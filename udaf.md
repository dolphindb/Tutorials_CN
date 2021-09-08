# 自定义聚合函数（UDAF）

分布式时序数据库DolphinDB具有很好的扩展性。用户可以使用内置的脚本语言或者C++插件来增加自定义函数（UDF），包括自定义聚合函数（UDAF）。本教程讲解如何使用脚本语言自定义聚合函数，以及聚合函数在分布式环境中的map reduce实现和在cgroup by中的running aggregate实现。

## 1. 使用defg定义一个聚合函数 

DolphinDB中使用关键词def定义一个函数，关键词defg定义一个聚合函数。下面的例子是几何平均数的实现。为了防止数据的溢出，我们使用对数的方法来求几何平均。
```
defg geometricMean(x){
    return x.log().avg().exp()
}

>geometricMean(2 4 8);
4
```

自定义的聚合函数除了单独使用外，也可以直接用于sql语句做分组计算。
```
t = table(1 1 1 2 2 2 as id, 2.0 4.0 8.0 1.0 3.0 9.0 as value)
select geometricMean(value) as gval from t group by id
```

## 2. 聚合函数的分布式实现

当一个自定义的聚合函数用于分布式表的sql语句做分组计算时，情况变得复杂。当分布式表的分区字段跟group by的字段一致时，我们只需要在每个分区上分别运行这个sql语句，然后合并每一个分区上的运行结果就可以了。当分区字段和分组字段不一致时，我们需要使用map reduce来重新实现聚合函数。还是以geometricMean为例，基本思路如下：（1）map：在每个分区上计算对数均值以及非空数据的个数，（2）计算这些对数均值的加权平均，并用exp还原几何平均。
```
defg geometricMean(x){
    return x.log().avg().exp()
}
def logAvg(x) : log(x).avg()
defg geometricMeanReduce(logAvgs, counts) : wavg(logAvgs, counts).exp()

mapr geometricMean(x){logAvg(x), count(x) -> geometricMeanReduce}
```
使用mapr语句将map reduce的实现与聚合函数关联。关键词mapr后面加空格，其后是自定义聚合函数的signature。map reduce部分用一对花括号括起来。`->`之前部分是map函数，之后部分是reduce函数。在此例中，有两个map函数（logAvg和count），多个map函数之间用逗号分隔。map函数的参数必须在前面的聚合函数signature中定义过。

把上面的代码黏贴到dolphindb.dos中，重启dolphindb后就可以在分布式sql中使用这个聚合函数了。下面我们用内存分区表来测试这个聚合函数。分区表用日期分区，sql按照股票sym分组，这样就能够触发聚合函数geometricMean的分布式实现了。
```
t = table(2020.09.01 + 0 0 1 1 3 3 as date, take(`IBM`MSFT, 6) as sym, 1.0 2.0 3.0 4.0 9.0 8.0 as value)
db = database("", RANGE, [2020.09.01, 2020.09.03, 2020.09.10])
stock = db.createPartitionedTable(t, "stock", "date").append!(t)
select geometricMean(value) as gval from stock group by sym

sym  gval
---- ----
IBM  3
MSFT 4
```
下面深入讲述一下DolphinDB的map reduce实现。DolphinDB中的map函数作用于一个数据分区。所以一个数据表有n个分区，就会产生n个map函数调用。在上面的例子中，按照日期将stock表分成了两个区，map函数logAvg(x)和count(x)分别会被调用两次。reduce函数的输入是map函数的结果。有几个map函数，reduce的参数就有几个。每一个reduce的参数都是一个vector，vector的长度正好是分区的个数。

## 3. 聚合函数的cgroup by实现

cgroup by的典型应用场景是按时间维度将数据分成几个组，然后累计计算每个组的统计值。具体来说，先计算第一个组的统计值，然后计算前两个组的数据合在一起的统计值，接着计算前三个组的数据合在一起的统计值，依此类推。若严格根据此定义计算，效率很低。一个改进的办法是分别计算每个组的一些统计值，然后根据这些统计值计算running aggregate。这个优化算法，与map reduce的思路非常类似。区别是在map reduce的场景下，我们只计算一个聚合值，在cgroup by下，我们计算多个组的running aggregate。

我们继续以geometricMean为例，演示聚合函数的cgroup by实现。增加了自定义函数geometricMeanRunning，并且扩展了mapr语句。mapr语句的第二部分是cgroup by的实现。map reduce和cgroup by的实现用分号分隔。cgroup by的map实现跟map reduce完全一致，所以我们直接使用了copy函数，也就是将map的结果直接传给geometricMeanRunning。
```
def geometricMeanRunning(logAvgs, counts) : cumwavg(logAvgs, counts).exp()
mapr geometricMean(x){logAvg(x), count(x) -> geometricMeanReduce; copy, copy->geometricMeanRunning}
```
上述变化更新到dolphindb.dos，重启后可以在分布式sql和cgroup by中使用聚合函数geometricMean。
```
t = table(2020.09.01 + 0 0 1 1 3 3 as date, take(`IBM`MSFT, 6) as sym, 1.0 2.0 3.0 4.0 9.0 8.0 as value)
select geometricMean(value) as gval from t cgroup by date order by date

date       gval
---------- -----------------
2020.09.01 1.414213562373095
2020.09.02 2.213363839400643
2020.09.04 3.464101615137754
```

## 4. 一个更为复杂的聚合函数例子

几何平均的实现相对简单。下面我们给出一个更为复杂的聚合函数的完整实现。这个聚合函数用于计算失衡的t-value，基本形式定义在函数tval中。
```
defg tval(x, w){
	wavgX = wavg(x, w)
	wavgX2 = wavg(x*x, w)
	return wavgX/sqrt(wavgX2 - wavgX.square())
}

def wsum2(x,w): wsum(x*x, w)

defg tvalReduce(wsumX, wsumX2, w){
	wavgX = wsumX.sum()\w.sum()
	wavgX2 = wsumX2.sum\w.sum()
	return wavgX/sqrt(wavgX2 - wavgX.square())
}

def tvalRunning(wsumX, wsumX2, w){
	wavgX = wsumX\w
	wavgX2 = wsumX2\w
	return wavgX/sqrt(wavgX2 - wavgX.square())
}

mapr tval(x, w){wsum(x, w), wsum2(x, w), contextSum(w, x)->tvalReduce; cumsum, cumsum, cumsum->tvalRunning}
```
分布式的实现，要计算三个部分：x的加权和wsum(x, w)，x的平方的加权和wsum2(x, w)，以及权重和conextSum(w, x)。注意计算权重和时没有使用sum(w)，而使用了contextSum(w, x)。这是考虑到数据中可能有空值。构建这三个map函数后，使用reduce函数tvalReduce即可完成tval的分布式实现。cgroup by的实现，需要对上面三个map函数的结果做一个cumsum的变换，然后用tvalRunning实现running aggregate。
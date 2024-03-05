# DolphinDB 教程：定义聚合函数

分布式时序数据库 DolphinDB 具有很好的扩展性。用户可以使用内置的脚本语言或者 C++ 插件来编写自定义函数（UDF）和自定义聚合函数（UDAF）。

本教程主要讲解:

* 如何使用脚本语言编写自定义聚合函数
* 聚合函数在分布式环境中的 map reduce 实现
* 聚合函数在 cgroup by 中的 running aggregate 实现。

- [DolphinDB 教程：定义聚合函数](#dolphindb-教程定义聚合函数)
	- [1. 使用 defg 定义一个聚合函数](#1-使用-defg-定义一个聚合函数)
	- [2. 聚合函数的分布式实现](#2-聚合函数的分布式实现)
	- [3. 聚合函数的 cgroup by 实现](#3-聚合函数的-cgroup-by-实现)
	- [4. 更为复杂的聚合函数例子](#4-更为复杂的聚合函数例子)

## 1. 使用 defg 定义一个聚合函数

DolphinDB 中使用关键词 def 定义一个函数，关键词 defg 定义一个聚合函数。

下面的例子是 DolphinDB 中几何平均数的实现方法。为了防止数据的溢出，这里使用对数的方法来求几何平均。
```c++
defg geometricMean(x){
    return x.log().avg().exp()
}

> geometricMean(2 4 8);
4
```

自定义聚合函数和内置聚合函数一样，除了单独作为函数调用外，也可以用于 SQL 语句。

下例为一个内存表的分组聚合计算：

```
t = table(1 1 1 2 2 2 as id, 2.0 4.0 8.0 1.0 3.0 9.0 as value)
select geometricMean(value) as gval from t group by id
```

## 2. 聚合函数的分布式实现

对于分布式表应用自定义的聚合函数进行 SQL 语句的分组聚合计算时，情况将变得复杂。

* 当分布式表的分区字段跟 group by 的字段一致时，只需要在每个分区上分别运行该 SQL 语句，然后合并各个分区的运行结果即可。

* 当分区字段和分组字段不一致时，则需要使用 map reduce 来重新实现聚合函数。

以上文定义 geometricMean 为例，基本思路如下：

1. map：在每个分区上计算对数均值以及非空数据的个数；

2. 计算这些对数均值的加权平均，并用 exp 还原几何平均。

示例：

```c++
// 普通的聚合函数声明
defg geometricMean(x){
    return x.log().avg().exp()
}

// 分布式实现
def logAvg(x) : log(x).avg()

defg geometricMeanReduce(logAvgs, counts) : wavg(logAvgs, counts).exp()

mapr geometricMean(x){logAvg(x), count(x) -> geometricMeanReduce}
```
使用 mapr 关键字将 map reduce 的实现与聚合函数关联。关键词 mapr 之后声明的是自定义聚合函数的 signature。map reduce 部分用一对花括号 `{}` 括起来。`->` 之前部分是 map 函数，之后部分是 reduce 函数。

在此例中，有两个 map 函数（logAvg 和 count），多个 map 函数之间用逗号分隔。注意，map 函数的参数必须在前面的聚合函数 signature 中定义过。

**注意**：把上面的代码粘贴到 DolphinDB 的初始化启动脚本 dolphindb.dos 中，重启 dolphindb server 后就可以在分布式 SQL 中使用这个聚合函数了。

下例用内存分区表来测试这个聚合函数。分区表用日期分区，SQL 按照股票 sym 分组，这样就能够触发聚合函数 geometricMean 的分布式实现了。

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
结合此例，此处来深入分析一下 DolphinDB 的 map reduce 实现。

* map 函数作用于一个数据分区。所以若一个数据表有 n 个分区，就会产生 n 个 map 函数调用。在上面的例子中，按照日期将 stock 表分成了 2 个区，map 函数 logAvg(x) 和 count(x) 分别会被调用两次。
* reduce 函数的输入是 map 函数的结果。有几个 map 函数，reduce 的参数就有几个。每一个 reduce 的参数都是一个 vector，vector 的长度正好是分区的个数。

## 3. 聚合函数的 cgroup by 实现

cgroup by 的典型应用场景是按时间维度将数据分成几个组，然后累计计算每个组的统计值。具体来说，先计算第一个组的统计值，然后计算前两个组的所有数据的统计值，接着计算前三个组的所有数据统计值，依此类推。若严格根据此定义计算，效率很低。

一个改进的办法是分别计算每个组的一些统计值，然后根据这些统计值计算 running aggregate。这个优化算法，与 map reduce 的思路非常类似。区别是在 map reduce 的场景下，只计算一个聚合值；在 cgroup by 场景下，需要计算多个组的 running aggregate。

继续以 geometricMean 为例，演示聚合函数的 cgroup by 实现。下例增加了自定义函数 geometricMeanRunning，并且扩展了 mapr 语句：

mapr 语句的第二部分 `copy, copy->geometricMeanRunning` 是 cgroup by 的实现。map reduce 和 cgroup by 的实现用分号分隔。cgroup by 的 map 实现跟 map reduce 完全一致，所以这里直接使用了 copy 函数，也就是将 map 的结果直接传给 geometricMeanRunning。

```c++
def geometricMeanRunning(logAvgs, counts) : cumwavg(logAvgs, counts).exp()

defg geometricMeanReduce(logAvgs, counts) : wavg(logAvgs, counts).exp()

mapr geometricMean(x){logAvg(x), count(x) -> geometricMeanReduce; copy, copy->geometricMeanRunning}
```

**注意**：上述变化更新到 dolphindb.dos，重启后可以在分布式 cgroup by 语句中调用聚合函数 geometricMean。

```
t = table(2020.09.01 + 0 0 1 1 3 3 as date, take(`IBM`MSFT, 6) as sym, 1.0 2.0 3.0 4.0 9.0 8.0 as value)
select geometricMean(value) as gval from t cgroup by date order by date

date       gval
---------- -----------------
2020.09.01 1.414213562373095
2020.09.02 2.213363839400643
2020.09.04 3.464101615137754
```

## 4. 更为复杂的聚合函数例子

几何平均的实现相对简单。下面我们给出一个更为复杂的聚合函数的完整实现。这个聚合函数用于计算失衡的 t-value，基本形式定义在函数 tval 中。
```c++
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
分布式的实现，要计算三个部分：x 的加权和 wsum(x, w)，x 的平方的加权和 wsum2(x, w)，以及权重和 conextSum(w, x)。注意计算权重和时没有使用 sum(w)，而使用了 contextSum(w, x)。这是考虑到数据中可能有空值。构建这三个 map 函数后，使用 reduce 函数 tvalReduce 即可完成 tval 的分布式实现。cgroup by 的实现，需要对上面三个 map 函数的结果做一个 cumsum 的变换，然后用 tvalRunning 实现 running aggregate。
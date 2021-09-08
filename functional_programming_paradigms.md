# 函数化编程案例

- [函数化编程案例](#函数化编程案例)
  - [1.CSV文件导入时预处理](#1csv文件导入时预处理)
    - [1.1 整型时间转化为TIME格式并导入](#11-整型时间转化为time格式并导入)
    - [1.2 有纳秒时间戳的文本导入](#12-有纳秒时间戳的文本导入)
  - [2. lambda函数](#2-lambda函数)
  - [3. 高阶函数使用示例](#3-高阶函数使用示例)
    - [3.1 cross使用示例](#31-cross使用示例)
    - [3.2 each使用示例](#32-each使用示例)
      - [3.2.1 获取表各个列的NULL值个数](#321-获取表各个列的null值个数)
      - [3.2.2 去除表中存在NULL值的行](#322-去除表中存在null值的行)
      - [3.2.3 判断两张表内容是否相同](#323-判断两张表内容是否相同)
    - [3.3 loop使用示例](#33-loop使用示例)
      - [3.3.1 loop跟each的区别](#331-loop跟each的区别)
      - [3.3.2 导入多个文件](#332-导入多个文件)
    - [3.4 moving使用示例](#34-moving使用示例)
    - [3.5 eachPre使用示例](#35-eachpre使用示例)
    - [3.6 byRow使用示例](#36-byrow使用示例)
  - [4. 部分应用示例](#4-部分应用示例)
    - [4.1 提交带有参数的作业](#41-提交带有参数的作业)
    - [4.2 获取集群其它节点作业信息](#42-获取集群其它节点作业信息)
    - [4.3 带“状态”的流计算消息处理函数](#43-带状态的流计算消息处理函数)
  - [5. 金融相关计算示例](#5-金融相关计算示例)
    - [5.1 计算股票两两之间的相关性](#51-计算股票两两之间的相关性)
    - [5.2 使用map reduce，对tick降精度](#52-使用map-reduce对tick降精度)
    - [5.3 基于字典的高频因子计算](#53-基于字典的高频因子计算)
  - [6. 数据处理相关示例](#6-数据处理相关示例)
    - [6.1 ols残差](#61-ols残差)
    - [6.2 拼接矩阵](#62-拼接矩阵)
    - [6.3 分组计算](#63-分组计算)
    - [6.4 比较两个字典元素是否相同](#64-比较两个字典元素是否相同)
    - [6.5 更新字典](#65-更新字典)

## 1.CSV文件导入时预处理

### 1.1 整型时间转化为TIME格式并导入

数据文件中表示时间的数据可能是整型或者长整型，而在进行数据分析时，往往又需要将这类数据强制转化为时间类型的格式导入并存储到数据库中。针对这种场景，可通过`loadTextEx`函数的`transform`参数为文本文件中的日期和时间列指定相应的数据类型。

> 关于文本导入的相关函数和案例，可以参考[数据导入教程](import_data.md)

首先，创建分布式数据库

``` sql
login(`admin,`123456)
dataFilePath="/home/data/candle_201801.csv"
dbPath="dfs://DolphinDBdatabase"
db=database(dbPath,VALUE,2018.01.02..2018.01.30)
```
[candle_201801.csv]((data/candle_201801.csv))的样本内容如下:

``` csv
symbol,exchange,cycle,tradingDay,date,time,open,high,low,close,volume,turnover,unixTime
000001,SZSE,1,20180102,20180102,93100000,13.35,13.39,13.35,13.38,2003635,26785576.72,1514856660000
000001,SZSE,1,20180102,20180102,93200000,13.37,13.38,13.33,13.33,867181
......
```

然后，我们通过`extractTextSchema`函数，来自动获取入数据文件的表的结构。导入数据的time字段，被识别为整数类型。而我们的表需要的是TIME类型，可以通过修改自动获取的表结构来修改定义。之后，就可以用这个表结构来创建分布式表了。如下：

``` shell
schemaTB=extractTextSchema(dataFilePath)
update schemaTB set type="TIME" where name="time"
tb=table(1:0,schemaTB.name,schemaTB.type)
tb=db.createPartitionedTable(tb,`tb1,`date);
```
>这里通过extractTextSchema来抽取生成表结构，只是为了方便，实际也可以直接定义表结构。然后使用时，要注意可能存在识别不符合预期的情况，这时候可以通过修改其定义来实现。

由于time字段的整数值需要转化为TIME类型， 我们通过自定义函数`i2t`，用于对数据进行预处理，并返回处理过后的数据表。

``` shell 
def i2t(mutable t){
    return t.replaceColumn!(`time,time(t.time/10))
}
```

>请注意：在自定义函数体内对数据进行处理时，请尽量使用本地的修改（以！结尾的函数）来提升性能。

最后，调用`loadTextEx`函数，并且指定`transform`参数为`i2t`函数，系统会对文本文件中的数据执行`i2t`函数，并将结果保存到数据库中。


``` sql
tmpTB=loadTextEx(dbHandle=db,tableName=`tb1,partitionColumns=`date,filename=dataFilePath,transform=i2t);
```

查看表内前5行数据。可见time列是以TIME类型存储，而不是文本文件中的INT类型：

``` sql
select top 5 * from loadTable(dbPath,`tb1);

symbol exchange cycle tradingDay date       time               open  high  low   close volume  turnover   unixTime
------ -------- ----- ---------- ---------- ------------------ ----- ----- ----- ----- ------- ---------- -------------
000001 SZSE     1     2018.01.02 2018.01.02 02:35:10.000000000 13.35 13.39 13.35 13.38 2003635 2.678558E7 1514856660000
000001 SZSE     1     2018.01.02 2018.01.02 02:35:20.000000000 13.37 13.38 13.33 13.33 867181  1.158757E7 1514856720000
```

完整代码如下:
``` shell
login(`admin,`123456)
dataFilePath="/home/data/candle_201801.csv"
dbPath="dfs://DolphinDBdatabase"
db=database(dbPath,VALUE,2018.01.02..2018.01.30)
schemaTB=extractTextSchema(dataFilePath)
update schemaTB set type="TIME" where name="time"
tb=table(1:0,schemaTB.name,schemaTB.type)
tb=db.createPartitionedTable(tb,`tb1,`date);

def i2t(mutable t){
    return t.replaceColumn!(`time,time(t.time/10))
}

tmpTB=loadTextEx(dbHandle=db,tableName=`tb1,partitionColumns=`date,filename=dataFilePath,transform=i2t);
```

### 1.2 有纳秒时间戳的文本导入

假设有一个文本文件nx.txt，样本内容如下所示

``` shell
SendingTimeInNano#securityID#origSendingTimeInNano#bidSize
1579510735948574000#27522#1575277200049000000#1
1579510735948606000#27522#1575277200049000000#2
...
```

文本的每一行通过字符'#'来拼接，其中SendingTimeInNano和origSendingTimeInNano是纳秒时间戳。

首先定义分布式数据库和表，如下:

>由于上个例子是使用`extractTextSchema`函数抽取文本结构生成表结构定义，这里我们就不用这个函数，直接定义表结构。

``` shell
dbSendingTimeInNano = database(, VALUE,  2020.01.11..2020.01.22);
dbSecurityIDRange = database(, RANGE, x);
db = database("dfs://testdb", COMPO, [dbSendingTimeInNano, dbSecurityIDRange]);

nameCol = `SendingTimeInNano`securityID`origSendingTimeInNano`bidSize;
typeCol = [`NANOTIMESTAMP,`INT,`NANOTIMESTAMP,`INT];
schemaTb = table(1:0,nameCol,typeCol);

db = database("dfs://testdb");
nx = db.createPartitionedTable(schemaTb, `nx, `SendingTimeInNano`securityID);
```

这里我们创建了一个[组合分区](database.md)的数据库，然后根据文本内容定义了表nx。

在导入数据的时候，我们也需要定义函数对纳秒时间戳的字段进行处理，通过函数`nanotimestamp`，将文本中的整型转化为纳秒时间戳。如下：

``` shell
def dataTransform(mutable t){
  return t.replaceColumn!(`SendingTimeInNano, nanotimestamp(t.SendingTimeInNano)).replaceColumn!(`origSendingTimeInNano, nanotimestamp(t.origSendingTimeInNano))
}
```

最终通过`loadTextEx`导入数据，完整代码如下：

``` shell
dbSendingTimeInNano = database(, VALUE,  2020.01.11..2020.01.22);
dbSecurityIDRange = database(, RANGE, x);
db = database("dfs://testdb", COMPO, [dbSendingTimeInNano, dbSecurityIDRange]);

nameCol = `SendingTimeInNano`securityID`origSendingTimeInNano`bidSize;
typeCol = [`NANOTIMESTAMP,`INT,`NANOTIMESTAMP,`INT];
schemaTb = table(1:0,nameCol,typeCol);

db = database("dfs://testdb");
nx = db.createPartitionedTable(schemaTb, `nx, `SendingTimeInNano`securityID);

def dataTransform(mutable t){
  return t.replaceColumn!(`SendingTimeInNano, nanotimestamp(t.SendingTimeInNano)).replaceColumn!(`origSendingTimeInNano, nanotimestamp(t.origSendingTimeInNano))
}

pt=loadTextEx(dbHandle=db,tableName=`nx , partitionColumns=`SendingTimeInNano`securityID,filename="nx.txt",delimiter='#',transform=dataTransform);
```


## 2. lambda函数

DolphinDB中可以创建自定义函数，函数可以有名称或者没有名称（通常为lambda函数）。

举个简单例子说明，如下计算每一个向量元素的平方:

``` shell
x = 1..10
each(x -> pow(x,2), x)
```

这里，用到了高阶函数`each`，然后里面定义了一个lambda函数: `x -> pow(x,2)`，来计算每一个元素的平方

接下去的例子中，也会有其它的lambda函数示例。

## 3. 高阶函数使用示例

### 3.1 cross使用示例

在实际应用场景中，我们可能遇到将两个向量或矩阵，两两组合作为参数来调用函数的场景。常见的伪代码如下：

``` shell
for(i:0~(size(X)-1)){
   for(j:0~(size(Y)-1)){
       result[i,j]=<function>(X[i], Y[j]);
   }
}
return result;
```

以计算[协方差矩阵](https://baike.baidu.com/item/%E5%8D%8F%E6%96%B9%E5%B7%AE%E7%9F%A9%E9%98%B5/9822183?fr=aladdin)为例。需要用两个for循环，去计算自身某一行和某一列的协方差。示例如下：

```shell
def matlab_cov(mutable matt){
  nullFill!(matt,0.0)
  rowss,colss=matt.shape()
  df=matrix(float,colss,colss)
  for (r in 0..(colss-1)){
    for (c in 0..(colss-1)){
      df[r,c]=covar(matt[:,r],matt[:,c])
    }
  }
  return df
}
```

可以看到，上面的代码虽然简单，但是代码行数多。在复杂的计算场景下，这样的写法容易出错。代码的表达能力也比较差。DolphinDB提供了一些高阶函数，这里 可以使用`cross`或`pcross`(并行的`cross`版本)，优化如下:

```shell
cross(covar, matt)
```

### 3.2 each使用示例

实际场景中，可能会遇到需要把函数应用到指定参数中的每个元素的情况。非函数化编程的例子里，我们需要用一个for循环取遍历指定参数的每个元素，然后调用函数。DolphinDB提供的高阶函数`each`,`peach`,`loop`,`ploop`可以简化这个写法。下面提供一些例子作为参考

#### 3.2.1 获取表各个列的NULL值个数
比如有一个表 t，想知道表各个列有多少个NULL值，可以使用each去处理每个列，求出NULL值的数量。

``` shell
each(x->x.size() - x.count(), t.values())
```
> 在DolphinDB中，对于向量或矩阵，size返回元素的个数，而count返回的是非null元素的个数。因此可以通过size和count返回值差获得null元素的个数。

其中，t.values()返回一个table `t`所有列

这里，我们也用到了DolphinDB的Lambda函数特性：`x -> x.size() - x.count()`

#### 3.2.2 去除表中存在NULL值的行

假如有一个表 t，我们想去除存在NULL值的行，样本表可以通过如下代码生成:

```shell
sym = take(`a`b`c, 110)
id = 1..100 join take(int(),10)
id2 =  take(int(),10) join 1..100
t = table(sym, id,id2)
```

有两种方法来实现,第一种是直接按行来处理，看看每一行是否存在NULL值，存在就去除。

这种方式实现代码如下:

``` shell
t[each(x -> !(x.id == NULL || x.id2 == NULL), t)]
```

需要注意的是，对表按行处理表时，表的每一行是一个字典对象，所以这里`each`函数里的函数，需要对每个列字段去判断是否为空。有一个为空，则不符合，为了筛选出符合的列，需要在最终条件前面加上逻辑取反操作。当列很多时，不方便列举每一个列名时，可以改进写法如下：

``` shell
t[each(x -> all(isValid(x.values)), t)]
```

上面代码中，`x.values`获取了该字典所有的值，然后通过`isValid`，生成一个向量，向量的每个值为0或1,表示是否为NULL值。因为只有每个值都不为0,才表示该行不存在NULL值，最后通过`all`将判断结果转化为标量，以说明该行是不是应该保留。

当数据量比较大时，上面的实现会比较慢。
>DolphinDB是列式存储，按列操作会比按行操作快很多很多。

因此我们先获取表的每一列，然后对每一列用`isValid`函数，获得一个结果向量，所有的结果向量又会组成一个矩阵。对于这个矩阵，我们可以判断矩阵的每一行是否为存在0值。在判断矩阵每一行是否存在0时，可以通过`rowAnd`来计算判断。如下：


```shell
t[each(isValid, t.values()).rowAnd()]
```

当数据量很大时，这样去处理可能会产生如下报错: 
```
The number of cells in a matrix can't exceed 2 billions.
```

出现这个错误，是因为上面的`each(isValid, t.values())`会生成一个过大的矩阵。为了避免生成过大的矩阵，我们可以迭代的计算，

这时候可以再使用`reduce`来迭代的计算,通过遍历每一列，去计算得到一个新列，每个元素表示该行是否存在NULL值。这样不用再是

```shell
t[reduce(def(x,y) -> x and isValid(y), t.values(), true)]
```


#### 3.2.3 判断两张表内容是否相同

比如说有两张表t1和t2,我们下判断这两张表的每条记录的数据是否都相等，可以使用`each`高阶函数，对表的每列进行比较。最后，只有每一列都相等，才能判断为相同，这里可以使用`all`函数，对每一列比较结果做运算。

>为了简化，这里假设表字段排序都一样，而且每行都已经按照某个字段排序

``` shell
all(each(eqObj, t1.values(), t2.values())）
```

### 3.3 loop使用示例

#### 3.3.1 loop跟each的区别

`loop` 模板与`each`模板很相似，区别在于函数返回值的格式和类型。

对于`each`模板来说，第一个函数调用的返回值数据格式和类型决定了所有函数的返回值数据格式和类型。

相反，`loop`没有这样的限制。它适用于函数返回值类型不同的情况。

``` shell
def parse_signals(mutable tbl_value, value){
    kvs = split(value, ',');
    d = dict(STRING, STRING);
    for(kv in kvs) {
        sp = split(kv, ':');
        d[sp[0]] = sp[1];
    }
    insert into tbl_value values(date(d[`tradingday]), d[`signal_id], d[`index], d[`underlying], d[`symbol], int(d[`volume]), int(d[`buysell]), int(d[`openclose]), temporalParse(d[`signal_time], "HHmmssSSS"));
}
tbl_value=table(100:0, [`tradingday,`signal_id,`index,`underlying,`symbol,`volume,`buysell,`openclose,`signal_time],[DATE,SYMBOL,SYMBOL,SYMBOL,SYMBOL,INT,INT,INT,TIME]);

v1="tradingday:2020.06.03,signal_id:1,index:000300,underlying:510300,symbol:10002985,volume:2,buysell:0,openclose:0,signal_time:093000120";
v2="tradingday:2020.06.04,signal_id:2,index:000500,underlying:510050,symbol:10002986,volume:3,buysell:1,openclose:1,signal_time:093100120"
parse_signals(tbl_value, v1);//It's OK.
each(parse_signals{tbl_value}, [v1, v2]);
```
上面示例中，最后使用`each`函数，会报错，报错如下:

``` shell
Not allowed to create void vector
```

原因在于，`each`是一个高阶函数，并行执行多个任务。以第一个任务的结果来决定整个函数的运行结果。如果单个任务返回的是一个scalar，那么`each`返回一个vector，单个任务返回vector，那么`each`返回matrix，单个任务返回字典，`each`返回table。

该问题中的parse_signals函数没有任何返回值（也就是返回一个NOTHING标量），所以`each`试图去创建一个类型为void的vector。这在DolphinDB中是不允许的。

改为`loop`。`loop`返回一个tuple，每个单独任务的返回值作为tuple的每一个元素。

``` shell
loop(parse_signals{tbl_value}, [v1, v2]);
```

#### 3.3.2 导入多个文件

假设在一个目录下，有多个csv文件，结构相同，需要导入到一个DolphinDB内存表中。
则可以使用高阶函数`loop`，如下:

``` shell
loop(loadText, fileDir + "/" + files(fileDir).filename).unionAll(false)
```


### 3.4 moving使用示例


本例中，我们演示一个滑动窗口的计算例子，需求如下：

计算某2列的当前值，与另一列的前面20个数做比较，然后算出是否在它的区间的百分比。数据如下：
![image](images/functional_programming/moving1.png)
比如6月17日这行数据的前面20行数据的close值（即图中标1这列），若其中有75%的数据是在upAvgPrice(图中标2）和upAvgPrice(图中标3）这两个值的区间中，那么signal（图中标4）的值设置为true，否则设为false。

解决办法：

我们使用高阶函数moving来解决问题。对于每一个窗口的处理，写一个自定义函数rangeTest来处理，返回true或false。

``` sql
def rangeTest(close, downlimit, uplimit){
    size = close.size() - 1
    return between(close.subarray(0, size), downlimit.last() : uplimit.last()).sum() >= size*0.75
}

update t set signal = moving(rangeTest, [close, downAvgPrice, upAvgPrice], 21)
```
>本例中，因为是计算前20行作为当期行的列数值，因而窗口需要包含前20条记录和本条记录，故值为21

>这里还用到了`between`函数，用来检查每个元素是否在a和b之间（两个边界都是包含在内的）。此处返回的是跟输入等长的包含0或者1的向量


### 3.5 eachPre使用示例


假设有一个表，包含sym和BidPrice两列。样本数据生成如下:

``` shell
t = table(take(`a`b`c`d`e ,100) as sym, rand(100.0,100) as bidPrice)
```

有如下的数据处理要求：

- 1.生成新的一列LN，值为：对当前行的BidPrice 除以前3行的平均值（不包括当前行），并取自然对数

- 2.对与上面的新列LN, 再生成新的一列Clean，值的取值逻辑：abs（LN） 如果值大于我们设定的波动范围F中的值，取前一个数的值，反之则认为当前报价正常保留当前报价

对于LN这一列的处理要求，跟上一个例子一样，是一个滑动窗口计算的问题。窗口的大小为3,计算函数是求均值。参考上面的`moving`使用示例，可以如下实现：

``` shell
t2 = select sym,bidPrice,log(bidPrice / moving(avg, bidPrice,3)) as ln from t
```

不过DolphinDB也提供了内置函数`msum`,`mcount`和`mavg`为各自的计算场景进行了优化，因此比`moving`模板有更好的性能。改写如下:

``` shell
t2 = select sym,bidPrice,log(bidPrice / mavg(bidPrice,3)) as ln from t
```

由于上面的计算结果`ln`字段是显示在第三行的当期行，我们可以对结果向下移动一行，更直观显示数据，可以通过`move`函数实现。改写如下:

``` shell
t2 = select sym,bidPrice,move(log(bidPrice / mavg(bidPrice,3)), 1) as ln from t
```

当然，向下移动一行，也就是取上一行结果，跟函数`prev`是等效的，因此上面的写法也等价于下面的写法：

``` shell
t2 = select sym,bidPrice,prev(log(bidPrice / mavg(bidPrice,3))) as ln from t
```

对于第二个数据处理要求，我们假设波动返回F 为0.02,然后实现一个自定义函数`cleanFun`来实现其取值逻辑，如下:

``` shell
F = 0.02
def cleanFun(F, x, y): iif(abs(x) > F, y, x)
```
其中，x表示当前值，y表示前一个值。然后使用`eachPre`函数来计算，`eachPre`模板等同于: F(X0], pre), F(X[1], X[0]), ..., F(X[n], X[n-1])。实现如下:

``` shell
t2[`clean] = eachPre(cleanFun{F}, t2[`ln])
```

完整代码如下:

``` shell
F = 0.02
t = table(take(`a`b`c`d`e ,100) as sym, rand(100.0,100) as bidPrice)
t2 = select sym,bidPrice,move(log(bidPrice / mavg(bidPrice,3)),1) as  ln from t 
def cleanFun(F,x,y) : iif(abs(x) > F, y,x)
t2[`clean] = eachPre(cleanFun{F}, t2[`ln])
```

### 3.6 byRow使用示例

假设有个场景，我们需要计算返回矩阵的每一行最大值的位置，示例矩阵如下：

``` shell
a1=2 3 4
a2=1 2 3
a3=1 4 5
a4=5 3 2
m = matrix(a1,a2,a3,a4)
``` 

一个直观的想法，就是对每一行调用计算的函数，DolphinDB有个`imax`函数，可以用来返回最大值的位置。
当`imax`的参数为矩阵，计算在每列内部进行，返回一个向量。因此，我们可以先对矩阵进行转置操作，然后使用
`imax`函数来求解。如下:

``` shell
imax(m.transpose())
```

当然，DolphinDB也提供了一个高阶函数`byRow`，把把列操作函数，应用到矩阵的行操作上。上面例子需求可以实现如下:

``` shell
byRow(imax, m)
```




## 4. 部分应用示例

在实际的场景中，我们可能会遇到一些高阶函数，它们接受函数作为参数。而这些作为参数的函数，我们在使用时，其中的一些参数其实是固定的。DolphinDB提供了部分应用来固定一个函数的部分参数，产生一个参数较少的函数。可以看下如下例子：

### 4.1 提交带有参数的作业

假设我们需要一个[定时任务](./scheduledJob.md),时间是每天的0点执行，任务是计算前一天某个设备温度指标的最大值。

假设设备的温度是存在分布式库 `dfs://dolphindb` 的表 `sensor`里，为了寻找前一天的设备温度，我们需要限定时间范围。假设时间字段为`ts`，类型为DATETIME,则可以实现如下:

``` shell
ts between (today()-1).datetime():(today().datetime()-1)
```

这里，函数`today`用来返回当期系统的时间，而`datetime`将其转化成DATETIME类型。`between`包含了左右区间的边界，因此对于DATETIME类型的数据，右边界需要减1。

在限定时间返回之后，我们就可以通过聚合函数`max`来获取最大值。我们可以定义一个`getMaxTemperature`来实现计算过程，因为我们函数返回的是数值，所以需要用`exec`而不是`select`。实现如下：

``` shell
def getMaxTemperature(deviceID){
    maxTemp=exec max(temperature) from loadTable("dfs://dolphindb","sensor")
            where ID=deviceID ,ts between (today()-1).datetime():(today().datetime()-1)
    return  maxTemp
}
```

定义好计算函数后，我们可以通过函数`scheduleJob`来提交一个定时任务。由于函数`scheduleJob`的任务函数是没有参数的。而上面的函数`getMaxTemperature`是以设备ID`deviceID`为参数的，这里，我们就可以通过部分应用来固定参数,来产生一个没有参数的函数。如下：

``` shell
scheduleJob(`testJob, "getMaxTemperature", getMaxTemperature{1}, 00:00m, today(), today()+30, 'D');
```
这里，我们固定参数为 1,即只查询设备号为1 的设备。

最终，完整代码如下:
``` shell
def getMaxTemperature(deviceID){
    maxTemp=exec max(temperature) from loadTable("dfs://dolphindb","sensor")
            where ID=deviceID ,ts between (today()-1).datetime():(today().datetime()-1)
    return  maxTemp
}

scheduleJob(`testJob, "getMaxTemperature", getMaxTemperature{1}, 00:00m, today(), today()+30, 'D');
``` 

### 4.2 获取集群其它节点作业信息

在DolphinDB中提交作业之后，可以通过函数`getRecentJobs`来取得本地节点上最近几个批处理作业的状态。比如说查看本地节点最近3个批处理作业状态，可以如下实现：

``` shell
getRecentJobs(3);
```

如果想获取集群上，其它节点作业信息，则可以通过函数`rpc`来在指定的远程节点上调用内置函数`getRecentJobs`来获取。假设我们需要获取节点 P1-node1的作业信息，可以如下实现：

``` shell
rpc("P1-node1",getRecentJobs)
```

进一步，我们只想获取节点 P1-node1上最近3个作业信息，如下实现会报错:

``` shell
rpc("P1-node1",getRecentJobs(3))
```

因为`rpc`函数第二个参数需要为函数（内置函数或用户自定义函数）。我们可以通过DolphinDB的部分应用，固定函数参数，来生成一个新的函数给`rpc`使用，如下：

``` shell
rpc("P1-node1",getRecentJobs{3})
```

### 4.3 带“状态”的流计算消息处理函数

在流计算中，用户通常需要给定一个消息处理函数，接受到消息后进行处理。这个处理函数是一元函数或数据表。若为函数，用于处理订阅数据，其唯一的参数是订阅的数据，即不能包含状态信息，是纯函数。假设希望处理函数计算的是迄今为止所有接收到的数据的平均值，则可以通过部分应用解决。

假设流表为 trades，包含了一个`price`字段，每次新接受一条消息，都计算一次迄今为止所有的`price`的平均值，并插入一个表 avgTable里。实现如下：

``` shell
share streamTable(10000:0,`time`symbol`price, [TIMESTAMP,SYMBOL,DOUBLE]) as trades
avgT=table(10000:0,[`avg_price],[DOUBLE])

def cumulativeAverage(mutable avgTable, mutable stat, trade){
   newVals = exec price from trade;
 
   for(val in newVals) {
        stat[0] = (stat[0] * stat[1] + val )/(stat[1] + 1)
	    stat[1] += 1
	    insert into avgTable values(stat[0])
   }
}

subscribeTable(tableName="trades", actionName="action30", handler=cumulativeAverage{avgT,0.0 0.0}, msgAsTable=true)
```

上面函数`cumulativeAverage`接受一个avgTable作为计算结果的存储表，`stat`是一个向量，包含了两个值。其中，`stat[0]`用来表示当前的所有数据的平均值，`stat[1]`表示数据个数。在函数内部计算时，每一条数据，都去更新`stat`的值，并将新的计算结果插入表。最后在订阅流表时，通过固定前面两个参数，实现了带“状态”的消息处理函数。

## 5. 金融相关计算示例


### 5.1 计算股票两两之间的相关性

本例中，我们使用金融大数据开放社区Tushare的沪深股票[日线行情](https://waditu.com/document/2?doc_id=27)数据，来计算股票的两两相关性。

首先我们定义一个数据库和表，来存储沪深股票日线行情数据。相关语句如下：

``` shell
login("admin","123456")
dbPath="dfs://tushare"
yearRange=date(2008.01M + 12*0..22)
if(existsDatabase(dbPath)){
	dropDatabase(dbPath)
}
columns1=`ts_code`trade_date`open`high`low`close`pre_close`change`pct_change`vol`amount
type1=`SYMBOL`NANOTIMESTAMP`DOUBLE`DOUBLE`DOUBLE`DOUBLE`DOUBLE`DOUBLE`DOUBLE`DOUBLE`DOUBLE
db=database(dbPath,RANGE,yearRange)
hushen_daily_line=db.createPartitionedTable(table(100000000:0,columns1,type1),`hushen_daily_line,`trade_date)
``` 
>上面的表结构定义，是按照[日线行情](https://waditu.com/document/2?doc_id=27)里的结构说明定义的。

定义好结构后，我们需要获取对应的数据。可以去[Tushare](https://tushare.pro/document/1?doc_id=39)平台注册账户，获取TOKEN，然后参考[示例脚本](./script/getTushareDailyLine.py)去获取数据并导入。这里的示例脚本使用了DolphinDB的[Python API](https://gitee.com/dolphindb/api_python3/blob/master/README_CN.md),也可以参考Tushare的说明文档使用其它语言或库来实现数据的获取。

为了演示，我们这里就只使用2008年到2017年的日线行情，而不是整个的数据。

在计算两辆相关性时，先计算生成股票回报率矩阵:

``` shell
retMatrix=exec pct_change/100 as ret from daily_line pivot by trade_date,ts_code
``` 

`exec`和`pivot by`是DolphinDB编程语言的特点之一。`exec`与`select`的用法相同，但是`select`语句生成的是表，`exec`语句生成的是向量。`pivot by`用于整理维度，与`exec`一起使用时会生成一个矩阵。


接着，生成股票相关性矩阵：

``` shell
corrMatrix=cross(corr,retMatrix)
```

这里的`cross`是DolphinDB中的高阶函数，可以参考[cross使用示例](#21-cross使用示例)。

然后，找到每只股票相关性最高的10只股票， 如下：

``` shell
syms=(exec count(*) from daily_line group by ts_code).ts_code
syms="C"+strReplace(syms, ".", "_")
mostCorrelated=select * from table(corrMatrix.columnNames() as ts_code, corrMatrix).rename!([`ts_code].append!(syms)).unpivot(`ts_code, syms).rename!(`ts_code`corr_ts_code`corr) context by ts_code having rank(corr,false) between 1:10
```

上面代码中，由于corrMatrix通过`table`函数来转化成表的时候，会丢失每行的股票代码信息，而且列名也改变了。所以这里，我们先从表daily_line 中抽取出所有的股票代码信息`syms`。然后由于表的列名不能以数字开头，我们又对`syms`做了字符串的处理，在前面拼接了字符"C"，然后把里面的字符'.转化成'_'。

在拼接上一列股票代码并生成表后`table(corrMatrix.columnNames() as ts_code, corrMatrix)`，我们重新命名每一列的名称，通过`rename!`函数来修改。由于新增了一列股票代码，所以这时候列名重命名时，还需要在列名里面拼接上`ts_code`这个字段，即:`.rename!(["ts_code"].append!(syms))`。

之后，对表做`unpivot`操作，把多列的数据转化成一列。这里是把原来的列名组成了结果中的valueType。为了说明中间过程，我们将上面代码拆解开如下一个中间步骤：

``` shell
select * from table(corrMatrix.columnNames() as ts_code, corrMatrix).rename!([`ts_code].append!(syms)).unpivot(`ts_code, syms)
```

这步生成结果为：

``` shell
ts_code   valueType  value            
--------- ---------- -----------------
000001.SZ C600539_SH 1                
000002.SZ C600539_SH 0.581235290880416
000004.SZ C600539_SH 0.277978963095669
000005.SZ C600539_SH 0.352580116619933
000006.SZ C600539_SH 0.5056164472398  
......
```

这样就得到了每只股票与其它股票的相关系数。之后又做了一次`rename!`来修改列名，然后通过`context by`来按照`ts_code`即股票代码分组计算，每组中，找到相关性最高的10只股票。

最终完整代码为:

``` shell
login("admin","123456")
daily_line= loadTable("dfs://tushare","hushen_daily_line")

retMatrix=exec pct_change/100 as ret from daily_line pivot by trade_date,ts_code
corrMatrix=cross(corr,retMatrix)

syms=(exec count(*) from daily_line group by ts_code).ts_code
syms="C"+strReplace(syms, ".", "_")
mostCorrelated=select * from table(corrMatrix.columnNames() as ts_code, corrMatrix).rename!([`ts_code].append!(syms)).unpivot(`ts_code, syms).rename!(`ts_code`corr_ts_code`corr) context by ts_code having rank(corr,false) between 1:10
```

### 5.2 使用map reduce，对tick降精度

以下例子，使用`mr`将TAQ的数据降精度为分钟级数据

在实际场景中，我可能遇到需要将tick数据降精度的场景。这里降精度，类似于上面的[moving使用示例](#24-moving使用示例)。可以通过滑动窗口计算，对数据进行处理，每个窗口计算保留均值作为这个窗口的数据。可以想到类似如下实现：

``` shell
minuteQuotes=select avg(bid) as bid, avg(ofr) as ofr from t group by symbol,date,minute(time) as minute
```

如果只是这样实现，当数据表很大的时候会很慢，这时候可以使用DolphinDB的分布式计算。
Map-Reduce函数`mr`是DolphinDB通用分布式计算框架的核心功能。

完整代码如下:

``` shell
login(`admin, `123456)
db = database("dfs://TAQ")
quotes = db.loadTable("quotes")

//create a new table quotes_minute
model=select  top 1 symbol,date, minute(time) as minute,bid,ofr from quotes where date=2007.08.01,symbol=`EBAY
if(existsTable("dfs://TAQ", "quotesMinute"))
db.dropTable("quotesMinute")
db.createPartitionedTable(model, "quotesMinute", `date`symbol)

//populate data for table quotes_minute
def saveMinuteQuote(t){
minuteQuotes=select avg(bid) as bid, avg(ofr) as ofr from t group by symbol,date,minute(time) as minute
loadTable("dfs://TAQ", "quotes_minute").append!(minuteQuotes)
return minuteQuotes.size()
}

ds = sqlDS(<select symbol,date,time,bid,ofr from quotes where date between 2007.08.01 : 2007.08.31>)
timer mr(ds, saveMinuteQuote, +)

```


### 5.3 基于字典的高频因子计算

有状态的因子，即因子的计算不仅用到当前数据，还会用到历史数据。实现状态因子的计算，一般包括这几个步骤：

- 1.保存本批次的消息数据到历史记录；
- 2.根据更新后的历史记录，计算因子
- 3.将因子计算结果写入输出表中。如有必要，删除未来不再需要的的历史记录。

由于DolphinDB的消息处理函数必须是单目函数，且唯一的参数就是当前的消息。要保存历史状态并且可以在消息处理函数中引用它，可以使用部分应用，定义一个多个参数的消息处理函数，其中一个参数用于接收消息，其它所有参数被固化，用于保存历史状态。这些固化参数只对消息处理函数可见，不受其他应用的影响。

历史状态可保存在内存表，字典或分区内存表中。本例将使用DolphinDB[流计算引擎](./streaming_tutorial.md)来对[报价数据](https://www.dolphindb.cn/downloads/tutorial/hfFactorsSampleData.zip)进行处理,基于字典保存历史状态并计算因子。关于基于内存表保存和分布式内存表保存历史状态的实现，可以参考[实时计算高频因子](./hf_factor_streaming.md)。


首先我们定义状态因子,为当前第一档卖价(askPrice1)与30个报价之前的第一档卖价的比值。因此，对于每只股票，至少需要保留30个历史报价。

对应的因子计算函数`factorAskPriceRatio`实现如下:

``` shell
defg factorAskPriceRatio(x){
	cnt = x.size()
	if(cnt < 31) return double()
	else return x[cnt - 1]/x[cnt - 31]
}
```

因为用到了DolphinDB[流计算引擎](./streaming_tutorial.md)，我们先导入数据，然后创建对应的流表，之后可以通过`replay`函数，进行数据回放和计算。

``` shell
quotesData = loadText("/data/ddb/data/sampleQuotes.csv")

x=quotesData.schema().colDefs
share streamTable(100:0, x.name, x.typeString) as quotes1
```
因为使用字典来保存历史状态，我们定义一个字典

``` shell
history = dict(STRING, ANY)
```

这里创建了一个键值为STRING类型，值为元组（tuple）类型的字典。该字典中，每只股票对应一个数组，以存储卖价的历史数据。使用`dictUpdate!`函数更新该字典，然后循环计算每只股票的因子。

对于因子的计算结果，也需要一个表来存放结果。然后通过订阅流表，数据回放时触发计算操作，计算中的历史数据来通过字典报错，最后结果数据到表。在触发流计算引擎触发计算时，我们需要定义计算函数，如下

``` shell
def factorHandler(mutable historyDict, mutable factors, msg){
	historyDict.dictUpdate!(function=append!, keys=msg.symbol, parameters=msg.askPrice1, initFunc=x->array(x.type(), 0, 512).append!(x))
	syms = msg.symbol.distinct()
	cnt = syms.size()
	v = array(DOUBLE, cnt)
	for(i in 0:cnt){
	    v[i] = factorAskPriceRatio(historyDict[syms[i]])
	}
	factors.tableInsert([take(now(), cnt), syms, v])
}
```

这里historyDict就是上面创建的字典，factors是计算结果保存的表。函数[`dictUpdate!`](https://www.dolphindb.cn/cn/help/index.html?dictUpdate.html)将新的数据通过`append`来更新插入原来的字典值里。

完整代码如下：

``` shell
quotesData = loadText("/data/ddb/data/sampleQuotes.csv")

defg factorAskPriceRatio(x){
	cnt = x.size()
	if(cnt < 31) return double()
	else return x[cnt - 1]/x[cnt - 31]
}
def factorHandler(mutable historyDict, mutable factors, msg){
	historyDict.dictUpdate!(function=append!, keys=msg.symbol, parameters=msg.askPrice1, initFunc=x->array(x.type(), 0, 512).append!(x))
	syms = msg.symbol.distinct()
	cnt = syms.size()
	v = array(DOUBLE, cnt)
	for(i in 0:cnt){
	    v[i] = factorAskPriceRatio(historyDict[syms[i]])
	}
	factors.tableInsert([take(now(), cnt), syms, v])
}

x=quotesData.schema().colDefs
share streamTable(100:0, x.name, x.typeString) as quotes1
history = dict(STRING, ANY)
share streamTable(100000:0, `timestamp`symbol`factor, [TIMESTAMP,SYMBOL,DOUBLE]) as factors
subscribeTable(tableName = "quotes1", offset=0, handler=factorHandler{history, factors}, msgAsTable=true, batchSize=3000, throttle=0.005)

replay(inputTables=quotesData, outputTables=quotes1, dateColumn=`date, timeColumn=`time)
```

查看结果

``` shell
select top 10 * from factors where isValid(factor)
```

## 6. 数据处理相关示例

### 6.1 ols残差

有一个表，样本如下:

``` shell
t=table(2020.11.01 2020.11.02 as date, `IBM`MSFT as ticker, 1.0 2 as past1, 2.0 2.5 as past3, 3.5 7 as past5, 4.2 2.4 as past10, 5.0 3.7 as past20, 5.5 6.2 as past30, 7.0 8.0 as past60)
```
对于这个表有一个计算需求：在原有的表创建一个新列，这列数据对应的是每行数据和一个固定的array进行ols回归得到的残差。

假设固定的array如下:

``` shell
benchX = 10 15 7 8 9 1 2.0
```

DolphinDB提供了函数`ols`，用来返回对 X 和 Y 计算普通最小二乘回归的结果。因为要对表的每一行数据进行处理，因此很容易想到可以使用高阶函数`each`。

我们把表中需要计算的字段数据转化成矩阵来进行处理。即:

``` shell
mt = matrix(t[`past1`past3`past5`past10`past20`past30`past60]).transpose()
``` 

之后，定义计算获取残差的函数，如下:

```
def(y, x) {
    return ols(y, x, true, 2).ANOVA.SS[1]
}
```

关于上面`ols`函数各个参数定义和使用，可以参考[ols函数说明](https://www.dolphindb.cn/cn/help/index.html?ols.html)

最后就是使用高阶函数，并使用部分应用固定参数，对每行数据应用上面的函数了，如下：

``` shell
t[`residual] = each(def(y, x){ return ols(y, x, true, 2).ANOVA.SS[1]}{,benchX}, mt)
```

完整代码如下：

``` shell
t=table(2020.11.01 2020.11.02 as date, `IBM`MSFT as ticker, 1.0 2 as past1, 2.0 2.5 as past3, 3.5 7 as past5, 4.2 2.4 as past10, 5.0 3.7 as past20, 5.5 6.2 as past30, 7.0 8.0 as past60)

mt = matrix(t[`past1`past3`past5`past10`past20`past30`past60]).transpose()
t[`residual] = each(def(y, x){ return ols(y, x, true, 2).ANOVA.SS[1]}{,benchX}, mt)
```

### 6.2 拼接矩阵

假设有两个矩阵a和b，如下

``` shell
a = 1..4$2:2
b = 1..4$2:2
```

横向拼接时，可以使用`join`函数

``` shell
a.join(b)
```

当有多个矩阵需要横向拼接时，可以使用高阶函数`reduce`:

``` shell
c = [a, b]
reduce(join, c)
```

纵向拼接时，可以先对矩阵进行转置操作，然后横向拼接，再转置

``` shell
a.transpose().join(b.transpose()).transpose()
```

当有多个矩阵时，则可以使用高阶函数`reduce`迭代的操作

``` shell
c = [a, b]
def transposeJoin(a, b) {
  return a.transpose().join(b.transpose()).transpose()
}
reduce(transposeJoin, c)
```

>表的拼接也类似


### 6.3 分组计算


``` shell
sym=`IBM`IBM`IBM`MS`MS`MS                                            
price=172.12 170.32 175.25 26.46 31.45 29.43
qty=5800 700 9000 6300 2100 5300
trade_date=2013.05.08 2013.05.06 2013.05.07 2013.05.08 2013.05.06 2013.05.07;     
contextby(avg, price, sym)
```

`contextby`模板可以在SQL查询中使用
``` shell
t1=table(trade_date,sym,qty,price);    
select trade_date, sym, qty, price from t1 where price > contextby(avg, price, sym);
```


### 6.4 比较两个字典元素是否相同

对于两个标量、数据对、向量或矩阵的比较，看它们是否相同时，DolphinDB提供了`eqObj`这个函数。对于字典元素的比较，我们可以通过函数来实现。

假设在DolphinDB中有下列2个字典：

``` shell
dict1 = {'a': 1, 'b': 2, 'c': '3'}
dict2 ={'a': 1, 'b': 2, 'c': 3}
```
实现一个函数`cmpDict`来做两个字典元素是否相同的比较
``` shell
def cmpDict(dict1, dict2) {
  if (dict1.keys().size()!=dict2.keys().size())
    return false;
  for(key in dict1.keys()) {
    if(dict1[key]!=dict2[key])
      return false;
  }
  return true;
}

cmpDict(dict1, dict2)
```


### 6.5 更新字典

假设我们有一个表orders，包含了一些简单的股票信息，如下:

``` shell
orders = table(`IBM`IBM`IBM`GOOG as SecID, 1 2 3 4 as Value, 4 5 6 7 as Vol) 
```

现在，我们希望能创建一个字典，每个键是股票代码，每个值是从上面orders表中筛选出来的只包含该股票信息的子表。

我们先定义一个字典，如下:

``` shell
historyDict = dict(STRING, ANY)
```

然后通过函数[`dictUpdate!`](http://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/d/dictUpdate!.html?highlight=dictupdate)，来更新每个键的值，实现如下:

``` shell
historyDict.dictUpdate!(function=def(x,y){tableInsert(x,y);return x}, keys=orders.SecID, parameters=orders, initFunc=def(x){t = table(100:0, x.keys(), each(type, x.values())); tableInsert(t, x); return t}) 
```

这里，我们使用orders.SecID作为keys，在更新的函数参数中，我们定义了一个将当期记录插入到之前存在的表中，如下:

``` shell
def(x,y){tableInsert(x,y);return x}
```
上面,`x`表示的是某个股票作为键其值（是一个表），然后把当前的记录`y`插入到其值中。

当原来的值不存在时，我们定一个一个initFunc，来进行初始化，即:

``` shell
def(x){
  t = table(100:0, x.keys(), each(type, x.values())); 
  tableInsert(t, x); 
  return t
}
```
这里，`x`输入参数是`orders`表的某一行记录，我们根据这行记录新建一个表，并最终返回。这里不是直接调用tableInsert，因为tableInsert返回的是插入的记录行数。在创表语句里，`x.keys()`获取的就是每一行数据的键（表中的每一行数据是一个dict）。`each(type, x.values())`之类通过高阶函数`each`，来获取每个参数的类型，从而实现根据表的一行记录(类型是dict)来定义一个表。


最终，完整代码如下:
``` shell
orders = table(`IBM`IBM`IBM`GOOG as SecID, 1 2 3 4 as Value, 4 5 6 7 as Vol) 
historyDict = dict(STRING, ANY) 
historyDict.dictUpdate!(function=def(x,y){tableInsert(x,y);return x}, keys=orders.SecID, parameters=orders, initFunc=def(x){t = table(100:0, x.keys(), each(type, x.values())); tableInsert(t, x); return t}) 
```


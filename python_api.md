# DolphinDB Python API

DolphinDB的Python API支持Python 2.7和Python 3.6及更高版本。

Python API本质上封装了DolphinDB的脚本语言。执行的时候，Python代码实际上被转换成DolphinDB脚本，当某些方法被触发时，DolphinDB服务器会执行这些方法，并且把执行结果保存到服务器会话中或者序列化到Python客户端。为此，Python API提供了两种方法。第一种方法不触发脚本的执行，只生成DolphinDB脚本。第二种方法触发脚本的执行。下表列出了所有生成DolphinDB脚本或触发脚本执行的方法。

| 方法名        | 详情          |
|:------------- |:-------------|
|connect(host, port, [username, password])|将会话连接到DolphinDB服务器|
|toDF()|把DolphinDB表对象转换成pandas的Dataframe对象|
|executeAs(tableName)|指定表名并把表保存到DolphinDB服务器中|
|execute()|与**update**和**delete**一起使用|
|database(dbPath, ......)|创建或加载数据库|
|dropDatabase(dbPath)|删除数据库|
|dropPartition(dbPath, partitionPaths)|删除数据库的某个分区|
|dropTable(dbPath, tableName)|删除数据库中的表|
|drop(colNameList)|删除表中的某列|
|ols(Y, X, intercept)|计算普通最小二乘回归，返回结果是一个字典|


本教程使用了一个csv文件：[example.csv](data/example.csv)。

### 1 连接DolphinDB

Python通过会话与DolphinDB进行交互。在下面的例子中，首先在Python中创建一个会话，然后使用指定的域名或IP地址和端口号把会话连接到DolphinDB服务器。在执行以下Python脚本前，需要先启动DolphinDB服务器。

```
import dolphindb ad ddb
s = ddb.session()
s.connect("localhost",8848)
```

如果需要使用用户名和密码连接DolphinDB，使用以下脚本：

```
s.connect("localhost",8848, YOUR_USER_NAME, YOUR_PASS_WORD)
```

DolphinDB默认的管理员用户名为“admin”，密码为“123456”。

### 2 把数据导入到DolphinDB服务器

DolphinDB数据库根据存储介质可以分为3种类型：分布式文件系统（DFS）中的数据库、本地文件系统的数据库和内存数据库。DolphinDB在DFS模式中性能达到最优。DFS能够自动管理数据存储和备份。因此，我们推荐用户使用分布式文件系统，部署方式请参考[多服务器集群部署](https://github.com/dolphindb/Tutorials_CN/blob/master/multi_machine_cluster_deploy.md)。为了能够让用户快速开始，我们在本教程中给出了本地文件系统和分布式文件系统的例子。DFS数据库的路径以“dfs://”开头。

#### 2.1 把数据导入到内存表中

我们可以使用**loadText**方法把文本文件导入到DolphinDB的内存表中。该方法会在Python中返回一个DolphinDB内存表对象。我们可以使用**toDF**方法把Python中的DolphinDB Table对象转换成pandas DataFrame。

```
WORK_DIR = "C:/DolphinDB/Data"

# return a DolphinDB table object in Python
trade=s.loadText(WORK_DIR+"/example.csv")

# convert the imported DolphinDB table object into a pandas DataFrame
df = trade.toDF()
print(df)

# output
TICKER        date       VOL        PRC        BID       ASK
0       AMZN  1997.05.16   6029815   23.50000   23.50000   23.6250
1       AMZN  1997.05.17   1232226   20.75000   20.50000   21.0000
2       AMZN  1997.05.20    512070   20.50000   20.50000   20.6250
3       AMZN  1997.05.21    456357   19.62500   19.62500   19.7500
4       AMZN  1997.05.22   1577414   17.12500   17.12500   17.2500
5       AMZN  1997.05.23    983855   16.75000   16.62500   16.7500
...
13134   NFLX  2016.12.29   3444729  125.33000  125.31000  125.3300
13135   NFLX  2016.12.30   4455012  123.80000  123.80000  123.8300

```

**loadText**函数导入文件时的默认分隔符是“,”。用户可以指定其他符号作为分隔符。例如，导入表格形式的文本文件：

```
t1=s.loadText(WORK_DIR+"/t1.tsv", '\t')
```

#### 2.2 把数据导入到分区数据库中

如果需要导入的文件比可用内存大，我们可以把数据导入到分区数据库中。


#### 2.2.1 创建分区数据库

创建了分区数据库后，我们不能改变它的分区方案。为了保证使用的不是已经存在的数据库，需要先检查数据库“valuedb”是否存在。如果存在，将其删除。

```
if s.existsDatabase(WORK_DIR+"/valuedb"):
    s.dropDatabase(WORK_DIR+"/valuedb")
```

使用**database**方法创建值分区（VALUE）的数据库。由于example.csv文件中只有3个股票代码，使用股票代码作为分区字段。参数**partitions**表示分区方案。

```
# 'db' indicates the database handle name on the DolphinDB server.
s.database('db', partitionType=ddb.VALUE, partitions=["AMZN","NFLX","NVDA"], dbPath=WORK_DIR+"/valuedb")
# this is equivalent to executing 'db=database(=WORK_DIR+"/valuedb", VALUE, ["AMZN","NFLX", "NVDA"])' on DolphinDB server.
```

在DFS（分布式文件系统）创建分区数据库，只需把数据库的路径改成以“dfs://”开头。下面的例子需要在集群中执行。请参考教程[多服务器集群部署](https://github.com/dolphindb/Tutorials_CN/blob/master/multi_machine_cluster_deploy.md)配置集群。

```
s.database('db', partitionType=VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath="dfs://valuedb")
```

除了值分区（VALUE），DolphinDB还支持顺序分区（SEQ）、哈希分区（HASH）、范围分区（RANGE）、组合分区（COMBO）和哈希分区（HASH）。

#### 2.2.2 创建分区表，并把数据追加到表中

创建数据库后，我们可以使用函数**loadTextEx**把文本文件导入到分区数据库的分区表中。如果分区表不存在，函数会自动生成该分区表并把数据追加到表中。如果分区表已经存在，则直接把数据追加到分区表中。

函数**loadTextEx**的各个参数如下：
**dbPath**表示数据库路径，**tableName**表示分区表的名称，**partitionColumns**表示分区列，**filePath**表示文本文件的绝对路径，**delimiter**表示文本文件的分隔符（默认分隔符是逗号）。

下面的例子使用函数**loadTextEx**创建了分区表**trade**，并把example.csv中的数据追加到表中。

```
if s.existsDatabase(WORK_DIR+"/valuedb"):
    s.dropDatabase(WORK_DIR+"/valuedb")
s.database('db', partitionType=ddb.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")
trade = s.loadTextEx("db",  tableName='trade',partitionColumns=["TICKER"], filePath=WORK_DIR + "/example.csv")
print(trade.toDF())

# output
TICKER        date       VOL        PRC        BID       ASK
0       AMZN  1997.05.16   6029815   23.50000   23.50000   23.6250
1       AMZN  1997.05.17   1232226   20.75000   20.50000   21.0000
2       AMZN  1997.05.20    512070   20.50000   20.50000   20.6250
3       AMZN  1997.05.21    456357   19.62500   19.62500   19.7500
4       AMZN  1997.05.22   1577414   17.12500   17.12500   17.2500
5       AMZN  1997.05.23    983855   16.75000   16.62500   16.7500
...
13134   NFLX  2016.12.29   3444729  125.33000  125.31000  125.3300
13135   NFLX  2016.12.30   4455012  123.80000  123.80000  123.8300

[13136 rows x 6 columns]

#返回表中的行数：
print(trade.rows)
13136

#返回表中的列数：
print(trade.cols)
6

#展示表的结构：
print(trade.schema)
     name typeString  typeInt
0  TICKER     SYMBOL       17
1    date       DATE        6
2     VOL        INT        4
3     PRC     DOUBLE       16
4     BID     DOUBLE       16
5     ASK     DOUBLE       16
```

访问表：

```
 trade = s.table(dbPath=WORK_DIR+"/valuedb", data="trade")
```



#### 2.3 把数据导入到内存的分区表中

#### 2.3.1 使用loadTextEx
我们可以把数据导入到内存的分区表中。由于内存分区表使用了并行计算，因此对它进行操作比对内存未分区进行操作要快。

同样地，使用**loadTextEx**函数创建内存分区数据库时，**dbPath**参数为空字符串。

```
s.database('db', partitionType=ddb.VALUE, partitions=["AMZN","NFLX","NVDA"], dbPath="")

# "dbPath='db'" means that the system uses database handle 'db' to import data into in-memory partitioned table trade
trade=s.loadTextEx(dbPath="db", partitionColumns=["TICKER"], tableName='trade', filePath=WORK_DIR + "/example.csv")

```

#### 2.3.2 使用ploadText

**ploadText**函数可以并行加载文本文件到内存分区表中。它的加载速度要比**loadText**函数快。
```
trade=s.ploadText(WORK_DIR+"/example.csv")
print(trade.rows)

# output
13136
```


#### 2.4 从Python上传数据到DolphinDB服务器

#### 2.4.1 使用upload函数

**upload**可以把Python对象上传到DolphinDB服务器。**upload**函数的输入是Python的字典对象，它的key对应的是DolphinDB中的变量名，value对应的是Python对象。

```
import pandas as pd
import numpy as np
df = pd.DataFrame({'id': np.int32([1, 2, 3, 4, 3]), 'value':  np.double([7.8, 4.6, 5.1, 9.6, 0.1]), 'x': np.int32([5, 4, 3, 2, 1])})
s.upload({'t1': df})
print(s.run("t1.value.avg()"))

# output
5.44
```

#### 2.4.2 使用table函数

我们可以在Python中使用**table**函数创建DolphinDB表对象。**table**函数的输入可以是字典、Dataframe或DolphinDB中的表名。

```
# save the table to DolphinDB server as table "test"
dt = s.table(data={'id': [1, 2, 2, 3],
                   'ticker': ['AAPL', 'AMZN', 'AMZN', 'A'],
                   'price': [22, 3.5, 21, 26]}).executeAs("test")

# load table "test" on DolphinDB server 
print(s.loadTable("test").toDF())

# output
   id  ticker   price
0   1   AAPL    22.0
1   2   AMZN     3.5
2   2   AMZN    21.0
3   3      A    26.0
```

#### 3 从DolphinDB数据库中加载数据

#### 3.1 使用loadTable函数

我们可以使用**loadTable**从数据库中加载数据。参数**tableName**表示分区表的名称，**dbPath**表示数据库的路径。如果没有指定**dbPath**，**loadTable**函数会加载内存中名为**tableName**的表。

对于分区表，如果参数**memoryMode**=true，把表中的所有数据加载到内存的分区表中（如果指定了**partition**参数，则加载指定的分区数据）；如果参数**memoryMode**=false，只把元数据加载到内存。

#### 3.1.1 加载整个表的数据

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
trade.toDF()

# output
TICKER        date       VOL        PRC        BID       ASK
0       AMZN  1997.05.16   6029815   23.50000   23.50000   23.6250
1       AMZN  1997.05.17   1232226   20.75000   20.50000   21.0000
2       AMZN  1997.05.20    512070   20.50000   20.50000   20.6250
3       AMZN  1997.05.21    456357   19.62500   19.62500   19.7500
4       AMZN  1997.05.22   1577414   17.12500   17.12500   17.2500
5       AMZN  1997.05.23    983855   16.75000   16.62500   16.7500
...
13134   NFLX  2016.12.29   3444729  125.33000  125.31000  125.3300
13135   NFLX  2016.12.30   4455012  123.80000  123.80000  123.8300

[13136 rows x 6 columns]
```

#### 3.1.2 加载指定分区的数据

只加载AMZN分区的数据：

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", partitions="AMZN")
print(trade.rows)

# output
4941
```

#### 3.1.3 把分区表加载到内存表中

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", partitions=["NFLX","NVDA"], memoryMode=True)
print(trade.rows)

# output
8195
```

#### 3.2 使用loadTableBySQL函数

**loadTableBySQL**函数通过SQL查询把磁盘上的分区表加载到内存的分区表中。

```
import os
if s.existsDatabase(WORK_DIR+"/valuedb"  or os.path.exists(WORK_DIR+"/valuedb")):
    s.dropDatabase(WORK_DIR+"/valuedb")
s.database(dbName='db', partitionType=ddb.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")
t = s.loadTextEx("db",  tableName='trade',partitionColumns=["TICKER"], filePath=WORK_DIR + "/example.csv")

trade = s.loadTableBySQL(tableName="trade", dbPath=WORK_DIR+"/valuedb", sql="select * from trade where date>2010.01.01")
print(trade.rows)

# output
5286
```


#### 4 操作数据库和表

#### 4.1 操作数据库

#### 4.1.1 创建数据库

使用**database**创建分区数据库。

```
s.database('db', partitionType=ddb.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")
```

#### 4.1.2 删除数据库

使用**dropDatabase**删除数据库。

```
if s.existsDatabase(WORK_DIR+"/valuedb"):
    s.dropDatabase(WORK_DIR+"/valuedb")
```

#### 4.1.3 删除DFS数据库的分区

使用**dropPartition**删除DFS数据库的分区。

```
if s.existsDatabase("dfs://valuedb"):
    s.dropDatabase("dfs://valuedb")
s.database('db', partitionType=ddb.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath="dfs://valuedb")
trade=s.loadTextEx(dbPath="dfs://valuedb", partitionColumns=["TICKER"], tableName='trade', filePath=WORK_DIR + "/example.csv")
print(trade.rows)

# output
13136

s.dropPartition("dfs://valuedb", partitionPaths=["/AMZN", "/NFLX"])
trade = s.loadTable(tableName="trade", dbPath="dfs://valuedb")
print(trade.rows)
# output
4516

print(trade.select("distinct TICKER").toDF())

  distinct_TICKER
0            NVDA
```

#### 4.2 操作表

#### 4.2.1 加载数据库中的表

见3.1节。

#### 4.2.2 把数据追加到表

下面的例子把数据追加到磁盘上的分区表。如果需要使用追加数据后的表，需要重新把它加载到内存中。

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.rows)

# output
13136

# take the top 10 rows of table "trade" on the DolphinDB server
t = trade.top(10).executeAs("top10")

trade.append(t)

# table "trade" needs to be reloaded in order to see the appended records
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print (trade.rows)

# output
13146
```

下面的例子把数据追加到内存表中。

```
trade=s.loadText(WORK_DIR+"/example.csv")
t = trade.top(10).executeAs("top10")
t1=trade.append(t)

print(t1.rows)

# output
13146
```

#### 4.3 更新表

**update**只能用于更新内存表，并且必须和**execute**一起使用。

```
trade = s.loadTable(tableName="trade", dbPath=WORK_DIR+"/valuedb", memoryMode=True)
trade = trade.update(["VOL"],["999999"]).where("TICKER=`AMZN").where(["date=2015.12.16"]).execute()
t1=trade.where("ticker=`AMZN").where("VOL=999999")
print(t1.toDF())

# output

  TICKER        date     VOL        PRC        BID        ASK
0      AMZN  1997.05.15  999999   23.50000   23.50000   23.62500
1      AMZN  1997.05.16  999999   20.75000   20.50000   21.00000
2      AMZN  1997.05.19  999999   20.50000   20.50000   20.62500
3      AMZN  1997.05.20  999999   19.62500   19.62500   19.75000
4      AMZN  1997.05.21  999999   17.12500   17.12500   17.25000
...
4948   AMZN  1997.05.27  999999   19.00000   19.00000   19.12500
4949   AMZN  1997.05.28  999999   18.37500   18.37500   18.62500
4950   AMZN  1997.05.29  999999   18.06250   18.00000   18.12500

[4951 rows x 6 columns]
```

#### 4.4 删除表中的记录

**delete**必须与**execute**一起使用来删除表中的记录。

```
trade = s.loadTable(tableName="trade", dbPath=WORK_DIR+"/valuedb", memoryMode=True)
trade.delete().where('date<2013.01.01').execute()
print(trade.rows)

# output
3024
```

#### 4.5 删除表中的列

```
trade = s.loadTable(tableName="trade", dbPath=WORK_DIR + "/valuedb", memoryMode=True)
t1=trade.drop(['ask', 'bid'])
print(t1.top(5).toDF())

  TICKER        date      VOL     PRC
0   AMZN  1997.05.15  6029815  23.500
1   AMZN  1997.05.16  1232226  20.750
2   AMZN  1997.05.19   512070  20.500
3   AMZN  1997.05.20   456357  19.625
4   AMZN  1997.05.21  1577414  17.125
```

#### 4.6 删除表

```
s.dropTable(WORK_DIR + "/valuedb", "trade")
```

#### 5 SQL 查询

DolphinDB提供了灵活的方法来生成SQL语句。

#### 5.1 **select**

#### 5.1.1 使用一系列的列名作为输入内容


```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", memoryMode=True)
print(trade.select(['ticker','date','bid','ask','prc','vol']).toDF())

# output
  TICKER        date      VOL     PRC     BID     ASK
0   AMZN  1997.05.15  6029815  23.500  23.500  23.625
1   AMZN  1997.05.16  1232226  20.750  20.500  21.000
2   AMZN  1997.05.19   512070  20.500  20.500  20.625
3   AMZN  1997.05.20   456357  19.625  19.625  19.750
4   AMZN  1997.05.21  1577414  17.125  17.125  17.250
...

```

我们可以使用**showSQL**来展示SQL语句。

```
print(trade.select(['ticker','date','bid','ask','prc','vol']).where("date=2012.09.06").where("vol<10000000").showSQL())

# output
select ticker,date,bid,ask,prc,vol from T64afd5a6 where date=2012.09.06 and vol<10000000

```

#### 5.1.2 使用字符串作为输入内容

```
print(trade.select("ticker,date,bid,ask,prc,vol").where("date=2012.09.06").where("vol<10000000").toDF())

# output
  ticker       date        bid     ask     prc      vol
0   AMZN 2012-09-06  251.42999  251.56  251.38  5657816
1   NFLX 2012-09-06   56.65000   56.66   56.65  5368963
...

```

#### 5.2 **top**

**top**用于取表中的前n条记录。

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
trade.top(5).toDF()

# output
      TICKER        date       VOL        PRC        BID       ASK
0       AMZN  1997.05.16   6029815   23.50000   23.50000   23.6250
1       AMZN  1997.05.17   1232226   20.75000   20.50000   21.0000
2       AMZN  1997.05.20    512070   20.50000   20.50000   20.6250
3       AMZN  1997.05.21    456357   19.62500   19.62500   19.7500
4       AMZN  1997.05.22   1577414   17.12500   17.12500   17.2500

```

#### 5.3 where

**where**用于过滤数据。

#### 5.3.1 多个条件过滤

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", memoryMode=True)

# use chaining WHERE conditions and save result to DolphinDB server variable "t1" through function "executeAs"
t1=trade.select(['date','bid','ask','prc','vol']).where('TICKER=`AMZN').where('bid!=NULL').where('ask!=NULL').where('vol>10000000').sort('vol desc').executeAs("t1")
print(t1.toDF())
# output

         date    bid      ask     prc        vol
0  2007.04.25  56.80  56.8100  56.810  104463043
1  1999.09.29  80.75  80.8125  80.750   80380734
2  2006.07.26  26.17  26.1800  26.260   76996899
3  2007.04.26  62.77  62.8300  62.781   62451660
4  2005.02.03  35.74  35.7300  35.750   60580703
...
print(t1.rows)

765
```

我们可以使用**showSQL**来查看SQL语句。

```
print(trade.select(['date','bid','ask','prc','vol']).where('TICKER=`AMZN').where('bid!=NULL').where('ask!=NULL').where('vol>10000000').sort('vol desc').showSQL())

# output
select date,bid,ask,prc,vol from Tff260d29 where TICKER=`AMZN and bid!=NULL and ask!=NULL and vol>10000000 order by vol desc
```

#### 5.3.2 使用字符串作为输入内容

**select**的输入内容可以是包含多个列名的字符串，**where**的输入内容可以是包含多个条件的字符串。

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.select("ticker, date, vol").where("bid!=NULL, ask!=NULL, vol>50000000").toDF())

# output
   ticker        date        vol
0    AMZN  1999.09.29   80380734
1    AMZN  2000.06.23   52221978
2    AMZN  2001.11.26   51543686
3    AMZN  2002.01.22   57235489
4    AMZN  2005.02.03   60580703
...
38   NVDA  2016.11.11   54384267
39   NVDA  2016.12.28   57384116
40   NVDA  2016.12.29   54384676
```

#### 5.4 **groupby**

**groupby**后面需要使用聚合函数，如**count**、**sum**、**agg**和**agg2**。

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.select('count(*)').groupby(['ticker']).sort(bys=['ticker desc']).toDF())

# output
  ticker  count_ticker
0   NVDA          4516
1   NFLX          3679
2   AMZN          4941

```

分别计算每个股票的vol总和和prc总和。

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.select(['vol','prc']).groupby(['ticker']).sum().toDF())

# output

   ticker      sum_vol       sum_prc
0   AMZN  33706396492  772503.81377
1   NFLX  14928048887  421568.81674
2   NVDA  46879603806  127139.51092
```


**groupby**与**having**一起使用：

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.select('count(ask)').groupby(['vol']).having('count(ask)>1').toDF())
# output

       vol  count_ask
0   579392          2
1  3683504          2
2  5732076          2
3  6299736          2
4  6438038          2
5  6946976          2
6  8160197          2
7  8924303          2
...

```

#### 5.5 **contextby**

**contextby**与**groupby**相似，区别在于**groupby**为每个组返回一个标量，但是**contextby**为每个组返回一个向量。返回的向量与每组之间的记录行数相同。

```
df= s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb").contextby('ticker').top(3).toDF()
print(df)

  TICKER       date      VOL      PRC      BID      ASK
0   AMZN 1997-05-15  6029815  23.5000  23.5000  23.6250
1   AMZN 1997-05-16  1232226  20.7500  20.5000  21.0000
2   AMZN 1997-05-19   512070  20.5000  20.5000  20.6250
3   NFLX 2002-05-23  7507079  16.7500  16.7500  16.8500
4   NFLX 2002-05-24   797783  16.9400  16.9400  16.9500
5   NFLX 2002-05-28   474866  16.2000  16.2000  16.3700
6   NVDA 1999-01-22  5702636  19.6875  19.6250  19.6875
7   NVDA 1999-01-25  1074571  21.7500  21.7500  21.8750
8   NVDA 1999-01-26   719199  20.0625  20.0625  20.1250

```

```
df= s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb").select("TICKER, month(date) as month, cumsum(VOL)").contextby("TICKER,month(date)").toDF()
print(df)

    TICKER     month  cumsum_VOL
0       AMZN  1997.05M     6029815
1       AMZN  1997.05M     7262041
2       AMZN  1997.05M     7774111
3       AMZN  1997.05M     8230468
4       AMZN  1997.05M     9807882
...
13133   NVDA  2016.12M   367356016
13134   NVDA  2016.12M   421740692
13135   NVDA  2016.12M   452063951
```

```
df= s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb").select("TICKER, month(date) as month, sum(VOL)").contextby("TICKER,month(date)").toDF()
print(df)

 TICKER     month    sum_VOL
0       AMZN  1997.05M   13736587
1       AMZN  1997.05M   13736587
2       AMZN  1997.05M   13736587
3       AMZN  1997.05M   13736587
4       AMZN  1997.05M   13736587
5       AMZN  1997.05M   13736587
...
13133   NVDA  2016.12M  452063951
13134   NVDA  2016.12M  452063951
13135   NVDA  2016.12M  452063951
```

```

df= s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade").contextby('ticker').having("sum(VOL)>40000000000").toDF()
print(df)

     TICKER        date       VOL       PRC       BID       ASK
0      NVDA  1999.01.22   5702636   19.6875   19.6250   19.6875
1      NVDA  1999.01.25   1074571   21.7500   21.7500   21.8750
2      NVDA  1999.01.26    719199   20.0625   20.0625   20.1250
3      NVDA  1999.01.27    510637   20.0000   19.8750   20.0000
4      NVDA  1999.01.28    476094   19.9375   19.8750   20.0000
5      NVDA  1999.01.29    509718   19.0000   19.0000   19.3125
...
4512   NVDA  2016.12.27  29857132  117.3200  117.3100  117.3200
4513   NVDA  2016.12.28  57384116  109.2500  109.2500  109.2900
4514   NVDA  2016.12.29  54384676  111.4300  111.2600  111.4200
4515   NVDA  2016.12.30  30323259  106.7400  106.7300  106.7500
```

#### 5.6 表连接

**merge**用于内部连接、左连接和外部连接，**merge_asof**用于asof join，**merge_window**用于窗口连接。

#### 5.6.1 **merge**

如果连接列名称相同，使用**on**参数指定连接列，如果连接列名称不同，使用**left_on**和**right_on**参数指定连接列。可选参数**how**表示表连接的类型。默认的连接类型时内部连接。

```
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")
t1 = s.table(data={'TICKER': ['AMZN', 'AMZN', 'AMZN'], 'date': ['2015.12.31', '2015.12.30', '2015.12.29'], 'open': [695, 685, 674]})
print(trade.merge(t1,on=["TICKER","date"]).toDF())

# output
  TICKER        date      VOL        PRC        BID        ASK  open
0   AMZN  2015.12.29  5734996  693.96997  693.96997  694.20001   674
1   AMZN  2015.12.30  3519303  689.07001  689.07001  689.09998   685
2   AMZN  2015.12.31  3749860  675.89001  675.85999  675.94000   695
```

当连接列名称不相同时，我们需要指定**left_on**参数和**right_on**参数。

```
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")
t1 = s.table(data={'TICKER1': ['AMZN', 'AMZN', 'AMZN'], 'date1': ['2015.12.31', '2015.12.30', '2015.12.29'], 'open': [695, 685, 674]})
print(trade.merge(t1,left_on=["TICKER","date"], right_on=["TICKER1","date1"]).toDF())

# output
  TICKER        date      VOL        PRC        BID        ASK  open
0   AMZN  2015.12.29  5734996  693.96997  693.96997  694.20001   674
1   AMZN  2015.12.30  3519303  689.07001  689.07001  689.09998   685
2   AMZN  2015.12.31  3749860  675.89001  675.85999  675.94000   695
```

左连接时，把**how**参数设置为“left”。

```
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")
t1 = s.table(data={'TICKER': ['AMZN', 'AMZN', 'AMZN'], 'date': ['2015.12.31', '2015.12.30', '2015.12.29'], 'open': [695, 685, 674]})
print(trade.merge(t1,how="left", on=["TICKER","date"]).where('TICKER=`AMZN').where('2015.12.23<=date<=2015.12.31').toDF())

# output
  TICKER       date      VOL        PRC        BID        ASK   open
0   AMZN 2015-12-23  2722922  663.70001  663.48999  663.71002    NaN
1   AMZN 2015-12-24  1092980  662.78998  662.56000  662.79999    NaN
2   AMZN 2015-12-28  3783555  675.20001  675.00000  675.21002    NaN
3   AMZN 2015-12-29  5734996  693.96997  693.96997  694.20001  674.0
4   AMZN 2015-12-30  3519303  689.07001  689.07001  689.09998  685.0
5   AMZN 2015-12-31  3749860  675.89001  675.85999  675.94000  695.0
```

外部连接时，把**how**参数设置为“outer”。分区表只能与分区表进行外部链接，内存表只能与内存表进行外部链接。

```
t1 = s.table(data={'TICKER': ['AMZN', 'AMZN', 'NFLX'], 'date': ['2015.12.29', '2015.12.30', '2015.12.31'], 'open': [674, 685, 942]})
t2 = s.table(data={'TICKER': ['AMZN', 'NFLX', 'NFLX'], 'date': ['2015.12.29', '2015.12.30', '2015.12.31'], 'close': [690, 936, 951]})
print(t1.merge(t2, how="outer", on=["TICKER","date"]).toDF())

# output
  TICKER        date   open TMP_TBL_ec03c3d2_TICKER TMP_TBL_ec03c3d2_date  \
0   AMZN  2015.12.29  674.0                    AMZN            2015.12.29   
1   AMZN  2015.12.30  685.0                                                 
2   NFLX  2015.12.31  942.0                    NFLX            2015.12.31   
3                       NaN                    NFLX            2015.12.30   

   close  
0  690.0  
1    NaN  
2  951.0  
3  936.0  
```

#### 5.6.2 **merge_asof**

**merge_asof**对应DolphinDB中的asof join（aj）。asof join用于非同步连接，它与left join非常相似，主要有以下区别：

1.asof join的最后一个连接列通常是时序类型。对于左表中某行的时间t，如果右表没有与t对应的时间，asof join会取右表中t之前的最近时间对应的记录。如果有多个相同的时间，它会取最后一个时间对应的记录。

2.如果只有一个连接列，右表必须按照连接列排好序。如果有多个连接列，右表必须在其他连接列定义的每个组内根据最后一个连接列排好序，右表不需要按照其他连接列排序，左表不需要排序。如果右表不满足这些条件，计算结果将会不符合预期。

下面的例子使用了[trades.csv](data/trades.csv)和[quotes.csv](data/quotes.csv)，它们包含了NYSE提供的APPL和FB的股票数据。

```
WORK_DIR = "C:/DolphinDB/Data"
if s.existsDatabase(WORK_DIR+"/tickDB"):
    s.dropDatabase(WORK_DIR+"/tickDB")
s.database('db', partitionType=ddb.VALUE, partitions=["AAPL","FB"], dbPath=WORK_DIR+"/tickDB")
trades = s.loadTextEx("db",  tableName='trades',partitionColumns=["Symbol"], filePath=WORK_DIR + "/trades.csv")
quotes = s.loadTextEx("db",  tableName='quotes',partitionColumns=["Symbol"], filePath=WORK_DIR + "/quotes.csv")

print(trades.top(5).toDF())

# output
                 Time Symbol  Trade_Volume  Trade_Price
0  09:30:00.087488712   AAPL        370466      117.100
1  09:30:00.087681843   AAPL        370466      117.100
2  09:30:00.103645440   AAPL           100      117.100
3  09:30:00.213850801   AAPL            20      117.100
4  09:30:00.264854448   AAPL            17      117.095

print(quotes.where("second(Time)>=09:29:59").top(5).toDF())

# output
                 Time Symbol  Bid_Price  Bid_Size  Offer_Price  Offer_Size
0  09:29:59.300399073   AAPL     117.07         1       117.09           1
1  09:29:59.300954263   AAPL     117.07         1       117.09           1
2  09:29:59.301594217   AAPL     117.05         1       117.19          10
3  09:30:00.499924044   AAPL     117.09        46       117.10           3
4  09:30:00.500005573   AAPL     116.86        53       117.37          64

print(trades.merge_asof(quotes,on=["Symbol","Time"]).select(["Symbol","Time","Trade_Volume","Trade_Price","Bid_Price", "Bid_Size","Offer_Price", "Offer_Size"]).top(5).toDF())

# output
  Symbol                Time  Trade_Volume  Trade_Price  Bid_Price  Bid_Size  \
0   AAPL  09:30:00.087488712        370466      117.100     117.05         1   
1   AAPL  09:30:00.087681843        370466      117.100     117.05         1   
2   AAPL  09:30:00.103645440           100      117.100     117.05         1   
3   AAPL  09:30:00.213850801            20      117.100     117.05         1   
4   AAPL  09:30:00.264854448            17      117.095     117.05         1   

   Offer_Price  Offer_Size  
0       117.19          10  
1       117.19          10  
2       117.19          10  
3       117.19          10  
4       117.19          10  
```

使用asof join计算交易成本：

```
print(trades.merge_asof(quotes, on=["Symbol","Time"]).select("sum(Trade_Volume*abs(Trade_Price-(Bid_Price+Offer_Price)/2))/sum(Trade_Volume*Trade_Price)*10000 as cost").groupby("Symbol").toDF())

# output
  Symbol      cost
0   AAPL  0.899823
1     FB  2.722923
```

#### 5.6.3 merge_window

**merge_window**对应DolphinDB中的window join，它是asof join的扩展。**leftBound**参数和**rightBound**参数用于指定窗口的边界w1和w2，左表中最后一个连接列对应的时间为t，在右表中选择(t+w1)到(t+w2)的时间并且其他连接列匹配的记录，然后对这些记录使用聚合函数。

window join和prevailing window join的唯一区别是，如果右表中没有与窗口左边界时间（即t+w1）匹配的值，prevailing window join会选择(t+w1)之前的最近时间。如果要使用prevailing window join，把**prevailing**参数设置为True。

```
print(trades.merge_window(quotes, -5000000000, 0, aggFunctions=["avg(Bid_Price)","avg(Offer_Price)"], on=["Symbol","Time"]).where("Time>=15:59:59").top(10).toDF())

# output
                 Time Symbol  Trade_Volume  Trade_Price  avg_Bid_Price  \
0  15:59:59.003095025   AAPL           250      117.620     117.603714   
1  15:59:59.003748103   AAPL           100      117.620     117.603714   
2  15:59:59.011092788   AAPL            95      117.620     117.603714   
3  15:59:59.011336471   AAPL           200      117.620     117.603714   
4  15:59:59.022841207   AAPL           144      117.610     117.603689   
5  15:59:59.028169703   AAPL           130      117.615     117.603544   
6  15:59:59.035357411   AAPL          1101      117.610     117.603544   
7  15:59:59.035360176   AAPL           799      117.610     117.603544   
8  15:59:59.035602676   AAPL           130      117.610     117.603544   
9  15:59:59.036929307   AAPL          2201      117.610     117.603544   

   avg_Offer_Price  
0       117.626816  
1       117.626816  
2       117.626816  
3       117.626816  
4       117.626803  
5       117.626962  
6       117.626962  
7       117.626962  
8       117.626962  
9       117.626962  

...
```

使用window join计算交易成本：

```
trades.merge_window(quotes,-1000000000, 0, aggFunctions="[wavg(Offer_Price, Offer_Size) as Offer_Price, wavg(Bid_Price, Bid_Size) as Bid_Price]", on=["Symbol","Time"], prevailing=True).select("sum(Trade_Volume*abs(Trade_Price-(Bid_Price+Offer_Price)/2))/sum(Trade_Volume*Trade_Price)*10000 as cost").groupby("Symbol").executeAs("tradingCost")

print(s.loadTable(tableName="tradingCost").toDF())

# output
  Symbol      cost
0   AAPL  0.953315
1     FB  1.077876
```

#### 5.7 executeAs

**executeAs**可以把结果保存为DolphinDB中的表对象。

```
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")
trade.select(['date','bid','ask','prc','vol']).where('TICKER=`AMZN').where('bid!=NULL').where('ask!=NULL').where('vol>10000000').sort('vol desc').executeAs("AMZN")
```

使用生成的表：
```
t1=s.loadTable(tableName="AMZN")
```

#### 6 回归运算

**ols**用于计算最小二乘回归系数。返回的是字典。

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR + "/valuedb", memoryMode=True)
z=trade.select(['bid','ask','prc']).ols('PRC', ['BID', 'ASK'])

print(z["ANOVA"])

# output
    Breakdown     DF            SS            MS             F  Significance
0  Regression      2  2.689281e+08  1.344640e+08  1.214740e+10           0.0
1    Residual  13133  1.453740e+02  1.106937e-02           NaN           NaN
2       Total  13135  2.689282e+08           NaN           NaN           NaN

print(z["RegressionStat"])

# output
         item    statistics
0            R2      0.999999
1    AdjustedR2      0.999999
2      StdError      0.105211
3  Observations  13136.000000


print(z["Coefficient"])

# output
      factor      beta  stdError      tstat    pvalue
0  intercept  0.003710  0.001155   3.213150  0.001316
1        BID  0.605307  0.010517  57.552527  0.000000
2        ASK  0.394712  0.010515  37.537919  0.000000

print(z["Coefficient"].beta[1])

# output
0.6053065019659698
```

下面的例子在分区数据库中执行回归运算。请注意，在DolphinDB中，两个整数整除的运算符为“/”，恰好是python的转移字符，因此在**select**中使用VOL\SHROUT。

```
result = s.loadTable(tableName="US",dbPath="dfs://US").select("select VOL\\SHROUT as turnover, abs(RET) as absRet, (ASK-BID)/(BID+ASK)*2 as spread, log(SHROUT*(BID+ASK)/2) as logMV").where("VOL>0").ols("turnover", ["absRet","logMV", "spread"], True)
print(result["ANOVA"])

   Breakdown        DF            SS            MS            F  Significance
0  Regression         3  2.814908e+09  9.383025e+08  30884.26453           0.0
1    Residual  46701483  1.418849e+12  3.038125e+04          NaN           NaN
2       Total  46701486  1.421674e+12           NaN          NaN           NaN
```

#### 7 **run**

**run**可用于执行任何DolphinDB脚本。如果脚本在DolphinDB中返回对象，**run**会把DolphinDB对象转换成Python中的对象。

```
# Load table
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")

# query the table and returns a pandas DataFrame
t = s.run("select bid, ask, prc from trade where bid!=NULL, ask!=NULL, vol>1000")
print(t)
```

#### 8 更多实例

#### 8.1 动量交易策略

下面的例子是使用动量交易策略进行回测。最常用的动量因素是过去一年扣除最近一个月的收益率。动量策略通常是一个月调整一次并且持有期也是一个月。本文的例子中，每天调整1/21的投资组合，并持有新的投资组合21天。为了简单起见，我们不考虑交易成本。

**Create server session**

```
import dolphindb as ddb
s=ddb.session()
s.connect("localhost",8921, "admin", "123456")
```

步骤1：加载股票交易数据，对数据进行清洗和过滤，然后为每只股票构建过去一年扣除最近一个月收益率的动量信号。注意，必须使用**executeAs**把中间结果保存到DolphinDB服务器上。数据集“US”包含了美国股票1990到2016年的交易数据。

```
US = s.loadTable(dbPath="dfs://US", tableName="US")
def loadPriceData(inData):
    s.loadTable(inData).select("PERMNO, date, abs(PRC) as PRC, VOL, RET, SHROUT*abs(PRC) as MV").where("weekday(date) between 1:5, isValid(PRC), isValid(VOL)").sort(bys=["PERMNO","date"]).executeAs("USstocks")
    s.loadTable("USstocks").select("PERMNO, date, PRC, VOL, RET, MV, cumprod(1+RET) as cumretIndex").contextby("PERMNO").executeAs("USstocks")
    return s.loadTable("USstocks").select("PERMNO, date, PRC, VOL, RET, MV, move(cumretIndex,21)/move(cumretIndex,252)-1 as signal").contextby("PERMNO").executeAs("priceData")

priceData = loadPriceData(US.tableName())
# US.tableName() returns the name of the table on the DolphinDB server that corresponds to the table object "US" in Python. 
```

步骤2：为动量策略生成投资组合

```
def genTradeTables(inData):
    return s.loadTable(inData).select(["date", "PERMNO", "MV", "signal"]).where("PRC>5, MV>100000, VOL>0, isValid(signal)").sort(bys=["date"]).executeAs("tradables")


def formPortfolio(startDate, endDate, tradables, holdingDays, groups, WtScheme):
    holdingDays = str(holdingDays)
    groups=str(groups)
    ports = tradables.select("date, PERMNO, MV, rank(signal,,"+groups+") as rank, count(PERMNO) as symCount, 0.0 as wt").where("date between "+startDate+":"+endDate).contextby("date").having("count(PERMNO)>=100").executeAs("ports")
    if WtScheme == 1:
        ports.where("rank=0").contextby("date").update(cols=["wt"], vals=["-1.0/count(PERMNO)/"+holdingDays]).execute()
        ports.where("rank="+groups+"-1").contextby("date").update(cols=["wt"], vals=["1.0/count(PERMNO)/"+holdingDays]).execute()
    elif WtScheme == 2:
        ports.where("rank=0").contextby("date").update(cols=["wt"], vals=["-MV/sum(MV)/"+holdingDays]).execute()
        ports.where("rank="+groups+"-1").contextby("date").update(cols=["wt"], vals=["MV/sum(MV)/"+holdingDays]).execute()
    else:
        raise Exception("Invalid WtScheme. valid values:1 or 2")
    return ports.select("PERMNO, date as tranche, wt").where("wt!=0").sort(bys=["PERMNO","date"]).executeAs("ports")

tradables=genTradeTables(priceData.tableName())
startDate="1996.01.01"
endDate="2017.01.01"
holdingDays=21
groups=10
ports=formPortfolio(startDate=startDate,endDate=endDate,tradables=tradables,holdingDays=holdingDays,groups=groups,WtScheme=2)
dailyRtn=priceData.select("date, PERMNO, RET as dailyRet").where("date between "+startDate+":"+endDate).executeAs("dailyRtn")
```

步骤3：计算投资组合中每只股票接下来21天的利润或损失。在投资组合形成后的21天关停投资组合。

```
def calcStockPnL(ports, dailyRtn, holdingDays, endDate):
    s.table(data={'age': list(range(1,holdingDays+1))}).executeAs("ages")
    ports.select("tranche").sort("tranche").executeAs("dates")
    s.run("dates = sort distinct dates.tranche")
    s.run("dictDateIndex=dict(dates,1..dates.size())")
    s.run("dictIndexDate=dict(1..dates.size(), dates)")
    ports.merge_cross(s.table(data="ages")).select("dictIndexDate[dictDateIndex[tranche]+age] as date, PERMNO, tranche, age, take(0.0,age.size()) as ret, wt as expr, take(0.0,age.size()) as pnl").where("isValid(dictIndexDate[dictDateIndex[tranche]+age]), dictIndexDate[dictDateIndex[tranche]+age]<=min(lastDays[PERMNO], "+endDate+")").executeAs("pos")
    t1= s.loadTable("pos")
    t1.merge(dailyRtn, on=["date","PERMNO"], merge_for_update=True).update(["ret"],["dailyRet"]).execute()
    t1.contextby(["PERMNO","tranche"]).update(["expr"], ["expr*cumprod(1+ret)"]).execute()
    t1.update(["pnl"],["expr*ret/(1+ret)"]).execute()
    return t1

lastDaysTable = priceData.select("max(date) as date").groupby("PERMNO").executeAs("lastDaysTable")
s.run("lastDays=dict(lastDaysTable.PERMNO,lastDaysTable.date)")
# undefine priceData to release memory
s.undef(priceData.tableName(), 'VAR')
stockPnL = calcStockPnL(ports=ports, dailyRtn=dailyRtn, holdingDays=holdingDays, endDate=endDate)
```

步骤4：计算投资组合的利润或损失。

```
portPnl = stockPnL.select("pnl").groupby("date").sum().sort(bys=["date"]).executeAs("portPnl")


print(portPnl.toDF())

      date   sum_pnl
0     1996.01.03 -0.001723
1     1996.01.04 -0.002033
2     1996.01.05 -0.000283
3     1996.01.08  0.000076
4     1996.01.09 -0.007517
5     1996.01.10  0.000964
...
5283  2016.12.27  0.005143
5284  2016.12.28 -0.001795
5285  2016.12.29  0.006746
5286  2016.12.30 -0.009754
```

#### 8.2 时间序列操作

下面的例子实现了WorldQuant 101 Alphas中的98号因子。

```
def alpha98(t):
    t1 = s.table(data=t)
    # add two calcualted columns through function update
    t1.contextby(["date"]).update(cols=["rank_open","rank_adv15"], vals=["rank(open)","rank(adv15)"]).execute()
    # add two more calculated columns
    t1.contextby(["PERMNO"]).update(["decay7", "decay8"], ["mavg(mcorr(vwap, msum(adv5, 26), 5), 1..7)","mavg(mrank(9 - mimin(mcorr(rank_open, rank_adv15, 21), 9), true, 7), 1..8)"]).execute()
    # return the final results with three columns: PERMNO, date, and A98
    return t1.select("PERMNO, date, rank(decay7)-rank(decay8) as A98").contextby(["date"]).executeAs("alpha98")

US = s.loadTable(tableName="US", dbPath="dfs://US").select("PERMNO, date, PRC as vwap, PRC+rand(1.0, PRC.size()) as open, mavg(VOL, 5) as adv5, mavg(VOL,15) as adv15").where("2007.01.01<=date<=2016.12.31").contextby("PERMNO").executeAs("US")
result=alpha98(US.tableName()).where('date>2007.03.12').executeAs("result")
print(result.top(10).toDF())
``` 

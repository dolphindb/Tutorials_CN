# 请修改Python API New。此版本为备份only
# 请修改Python API New。此版本为备份only
# 请修改Python API New。此版本为备份only
# 请修改Python API New。此版本为备份only
# 请修改Python API New。此版本为备份only
# 请修改Python API New。此版本为备份only
# 请修改Python API New。此版本为备份only
# 请修改Python API New。此版本为备份only
# 请修改Python API New。此版本为备份only
# 请修改Python API New。此版本为备份only
# 请修改Python API New。此版本为备份only
# 请修改Python API New。此版本为备份only
# 请修改Python API New。此版本为备份only
# 请修改Python API New。此版本为备份only
# 请修改Python API New。此版本为备份only
# 请修改Python API New。此版本为备份only





# DolphinDB Python API 

DolphinDB的Python API支持Python 2.7和Python 3.6及更高版本。

Python API本质上封装了DolphinDB的脚本语言。执行的时候，Python代码实际上被转换成DolphinDB脚本，当某些方法被触发时，DolphinDB服务器会执行这些方法，并且把执行结果保存到服务器会话中或者序列化到Python客户端。为此，Python API提供了两种方法。第一种方法不触发脚本的执行，只生成DolphinDB脚本。第二种方法触发脚本的执行。下表列出了所有生成DolphinDB脚本或触发脚本执行的方法。

| 方法名        | 详情          |是否执行脚本|
|:------------- |:-------------|:-------------|
|showSQL|   属于Table类| 否|
|ToDF()    | 属于Table类；把DolphinDB的Table对象转换成pandas DataFrame对象| 是 |
|execute()    | 属于Table类；与update和delete方法一起使用|是|





本教程使用了一个csv文件：[example.csv](data/example.csv)。使用该文件时，必须提供Linux格式的绝对路径，以便DolphinDB服务器定位文件。

### 1 连接DolphinDB

Python通过会话与DolphinDB进行交互。在下面的例子中，首先在Python中创建一个会话，然后使用指定的域名或IP地址和端口号把会话连接到DolphinDB服务器。在执行以下Python脚本前，需要先启动DolphinDB服务器。

```
import dolphindb ad ddb
s = ddb.session()
s.connect("localhost",8848)
from dolphindb import *
```

如果需要使用用户名和密码连接DolphinDB，使用以下脚本：

```
s.connect("localhost",8848, YOUR_USER_NAME, YOUR_PASS_WORD)
```

### 2 把数据导入到DolphinDB服务器

#### 2.1 把数据导入到内存表中

我们可以使用**loadText**方法把文本文件导入到DolphinDB中。该方法会在Python中返回一个DolphinDB Table对象，该对象是DolphinDB中的内存表。我们可以使用**toDF**方法把Python中的DolphinDB Table对象转换成pandas DataFrame。

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

使用**loadText**函数导入的数据规模必须小于可用内存。如果需要导入大数据文件，我们可以把数据导入到分区数据库中。


#### 2.2.1 创建分区数据库

创建了分区数据库后，我们不能改变它的分区方案。为了保证使用的不是预定义的数据库，需要先检查数据库“valuedb”是否存在。如果存在，将其删除。

```
if s.existsDatabase(WORK_DIR+"/valuedb"):
    s.dropDatabase(WORK_DIR+"/valuedb")
```

创建基于值分区（VALUE）的分区数据库。由于example.csv文件中只有3个股票代码，我们使用**VALUE**作为分区类型。参数**partitions**表示分区方案。

```
s.database('db', partitionType=VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")
```

在DFS（分布式文件系统）创建分区数据库，只需把数据库的路径改成以“dfs://”开头。下面的例子需要在集群中执行。请参考教程multi_machine_cluster_deploy.md配置集群。

```
s.database('db', partitionType=VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath="dfs://valuedb")
```

除了值分区（VALUE），DolphinDB还支持顺序分区（SEQ）、哈希分区（HASH）、范围分区（RANGE）和组合分区（COMBO）。

#### 2.2.2 创建分区表，并把数据追加到表中

创建数据库后，我们可以使用函数**loadTExtEx**把文本文件导入到分区数据库的分区表中。如果分区表不存在，函数会自动生成该分区表并把数据追加到表中。如果分区表已经存在，则直接把数据追加到分区表中。

**dbPath**表示数据库路径，**tableName**表示分区表的名称，**partitionColumns**表示分区列，**filePath**表示文本文件的绝对路径，**delimiter**表示文本文件的分隔符（默认分隔符是逗号）。

下面的例子使用函数**loadTextEx**创建了分区表**trade**，并把**example.csv**中的数据追加到表中。

```
trade = s.loadTextEx("db",  tableName='trade',partitionColumns=["TICKER"], filePath=WORK_DIR + "/example.csv")
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

访问表**trade**：

```
 trade = s.table(dbPath=WORK_DIR+"/valuedb", data="trade")
```



#### 2.3 把数据导入到内存的分区表中

#### 2.3.1 使用loadTextEx
我们可以把数据导入到内存的分区表中。由于内存分区表使用了并行计算，因此对它进行操作比对内存未分区进行操作要快。

同样地，使用**loadTextEx**函数创建内存分区数据库时，**dbPath**参数为空字符串。

```
s.database('db', partitionType=VALUE, partitions=["GFGC","EWST","EGAS"], dbPath="")
trade=s.loadTextEx(dbPath="db", partitionColumns=["sym"], tableName='trade', filePath=WORK_DIR + "/example.csv")
print(trade.toDF())

```

#### 2.3.2 使用loadTable

加载“NFLX”和“NVDA”两个分区的数据，并保存到内存分区表中：
```
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade", partitions=["NFLX","NVDA"], memoryMode=True)

print(trade.count())

# output

8195
```
#### 2.3.3 使用loadTableBySQL

**loadTableBySQL**可以把磁盘分区表的部分数据导入到内存的分区表。

```
if s.existsDatabase(WORK_DIR+"/valuedb"  or os.path.exists(WORK_DIR+"/valuedb")):
    s.dropDatabase(WORK_DIR+"/valuedb")
s.database(dbName='db', partitionType=VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")
t = s.loadTextEx("db",  tableName='trade',partitionColumns=["TICKER"], filePath=WORK_DIR + "/example.csv")

trade = s.loadTableBySQL(dbPath=WORK_DIR+"/valuedb", sql="select * from trade where date>2010.01.01")
print(trade.count())

# output 

5286

```

#### 2.3.4  使用ploadText

**ploadText**实际上是以并行模式执行**loadText**。使用**ploadText**加载文本文件，它会生成内存分区表。与未分区表相比，它的速度更快，但是占用更多内存。

```
trade=s.ploadText(WORK_DIR+"/example.csv")
print(trade.count())

# output

13136

````

#### 2.4 从Python上传数据到DolphinDB服务器

**upload**可以把Python对象上传到DolphinDB服务器。Python对象需要用Python dictionary表示，key表示上传的对象在DolphinDB中的变量名，value表示要上传的Python对象。这相当于在DolphinDB中执行**t1=table(1 2 3 4 3 as id, 7.8, 4.6, 5.1, 9.6, 0.1 as value,5, 4, 3, 2, 1 as x)**。

```
df = pd.DataFrame({'id': np.int32([1, 2, 3, 4, 3]), 'value':  np.double([7.8, 4.6, 5.1, 9.6, 0.1]), 'x': np.int32([5, 4, 3, 2, 1])})
s.upload({'t1': df})
print(s.run("t1.value.avg()"))

# output
5.44
```


#### 3 从DolphinDB数据库中加载数据

我们可以使用**loadTable**从数据库中加载数据。

```
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")


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

只加载“AMZN”分区：

```
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade", partitions="AMZN")
print(trade.count())

# output

4941

```

#### 4 操作数据库和表

Python中的DolphinDB Table对象作为DolphinDB table和pandas DataFrame之间的桥梁。使用**table**方法可以创建 DolphinDB Table对象，该方法的输入内容可以是dictionary，DataFrame或者DolphinDB中已经存在的表的名称。**table**方法会在DolphinDB中创建一个表，并分配一个随机的名称。我们可以使用**toDF**把Python中的DolphinDB Table对象转换成pandas DataFrame。

```
dt = s.table(data={'id': [1, 2, 2, 3],
                   'ticker': ['APPL', 'AMNZ', 'AMNZ', 'A'],
                   'price': [22, 3.5, 21, 26]})
print(dt.toDF())

# output
   id  price   sym
0   1   22.0  APPL
1   2    3.5  AMNZ
2   2   21.0  AMNZ
3   3   26.0     A

```

它会生成一个SQL查询，并把这个SQL查询发送到DolphinDB服务器，然后返回table对象。下面的例子计算了每个**id**的平均价格。

```
# average price for each id

print(dt['price'][dt.id < 3].groupby('id').avg().toDF())

# output
   id  avg_price
0   1       22.0
1   2       12.25

print(dt['price'][(dt.price > 10) & (dt.id < 3)].groupby('id').avg().toDF())

# output
   id  avg_price
0   1       22.0
1   2       21.0

print(  dt['price'][(dt.price > 10) & (dt.id < 3)].groupby('id').avg().showSQL())

# output
select avg(price) from T699daec5 where ((price > 10) and (id < 3)) group by id

```

#### 4.1 把数据追加到表中

使用**append**可以把数据追加到表中。

```
trade = s.table(dbPath=WORK_DIR+"/valuedb", data="trade", inMem=True)
c1 = trade.count()
print (c1)

 take the top 10 results from the table "trade" and assign it to variable "top10" on the server end
top10 = trade.top(10).executeAs("top10")

append table "top10" to table "trade"
c2 = trade.append(top10).count()
print (c2)
```


#### 4.2 更新表中数据

**update**后面必须使用**execute**才能更新表。

```
trade = s.table(dbPath=WORK_DIR+"/valuedb", data="trade", inMem=True)
trade = trade.update(["VOL"],["999999"]).where("TICKER=`AMZN").where(["date=2015.12.16"]).execute()
t1=trade.where("ticker=`AMZN").where("VOL=999999")
print(t1.toDF())


# output

  TICKER        date     VOL        PRC        BID        ASK
0   AMZN  2015.12.16  999999  675.77002  675.76001  675.83002

```

#### 4.3 删除表中数据

**delete**后面必须使用**execute**才能删除表中数据。

```
trade.delete().where('date<2013.01.01').execute()
print(trade.count())

# output

3024

```

#### 4.4 删除表中的列

```
trade = s.table(dbPath=WORK_DIR + "/valuedb", data="trade", inMem=True)
t1=trade.drop(['ask', 'bid'])
print(t1.top(5))

  TICKER        date      VOL     PRC
0   AMZN  1997.05.15  6029815  23.500
1   AMZN  1997.05.16  1232226  20.750
2   AMZN  1997.05.19   512070  20.500
3   AMZN  1997.05.20   456357  19.625
4   AMZN  1997.05.21  1577414  17.125

```

#### 4.5 删除表

表被删除之后，无法再使用。

```
s.dropTable(WORK_DIR + "/valuedb", "trade")
trade = s.table(dbPath=WORK_DIR + "/valuedb", data="trade", inMem=True)

Exception: ('Server Exception', 'table file does not exist: C:/Tutorials_EN/data/valuedb/trade.tbl')

```



#### 5 SQL 查询

DolphinDB Table类提供了灵活的方法来生成SQL语句。

#### 5.1 **select**

#### 5.1.1 使用list作为输入内容

我们可以在**select**中使用一系列的列名来选择列，也可以使用**where**来过滤数据。

```
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade", memoryMode=True)
print(trade.select(['date','bid','ask','prc','vol']).where('TICKER=`AMZN').where('bid!=NULL').where('ask!=NULL').where('vol>10000000').sort('vol desc').top(5).toDF())

# output

         date    bid      ask     prc        vol
0  2007.04.25  56.80  56.8100  56.810  104463043
1  1999.09.29  80.75  80.8125  80.750   80380734
2  2006.07.26  26.17  26.1800  26.260   76996899
3  2007.04.26  62.77  62.8300  62.781   62451660
4  2005.02.03  35.74  35.7300  35.750   60580703

```

我们可以使用**showSQL**来展示SQL语句。

```
print(trade.select(['date','bid','ask','prc','vol']).where('TICKER=`AMZN').where('bid!=NULL').where('ask!=NULL').where('vol>10000000').sort('vol desc').showSQL())

# output
select date,bid,ask,prc,vol from Tff260d29 where TICKER=`AMZN and bid!=NULL and ask!=NULL and vol>10000000 order by vol desc

```

#### 5.1.2 使用字符串作为输入内容

我们也可以在**select**中使用字符串来表示列名，**where**中的条件也可以用字符串表示。

```
trade.select("ticker, date, vol").where("bid!=NULL, ask!=NULL, vol>50000000").toDF()

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

#### 5.2 **top**

**top**用于取表中的前n条记录。

```
trade.top(5).toDF()



# output
      TICKER        date       VOL        PRC        BID       ASK
0       AMZN  1997.05.16   6029815   23.50000   23.50000   23.6250
1       AMZN  1997.05.17   1232226   20.75000   20.50000   21.0000
2       AMZN  1997.05.20    512070   20.50000   20.50000   20.6250
3       AMZN  1997.05.21    456357   19.62500   19.62500   19.7500
4       AMZN  1997.05.22   1577414   17.12500   17.12500   17.2500

```

#### 5.3 **selectAsVector**

把某个列输出为向量。

```
print(t.where('TICKER=`AMZN').where('date>2016.12.15').sort('date').selectAsVector('prc'))

#output
[757.77002 766.      771.21997 770.59998 766.34003 760.59003 771.40002
 772.13    765.15002 749.87   ]
```


#### 5.4 **groupby**

**groupby**后面需要使用聚合函数，如**count**、**sum**、**agg**和**agg2**。**agg2**有两个参数。

```
print(trade.select('ticker').groupby(['ticker']).count().sort(bys=['ticker desc']).toDF())

# output
  ticker  count_ticker
0   NVDA          4516
1   NFLX          3679
2   AMZN          4941

```

分别计算每个“ticker”的“vol”总和和“prc”总和。

```
print(trade.select(['vol','prc']).groupby(['ticker']).sum().toDF())

# output

   ticker      sum_vol       sum_prc
0   AMZN  33706396492  772503.81377
1   NFLX  14928048887  421568.81674
2   NVDA  46879603806  127139.51092
```


**groupby**与**having**一起使用：

```
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
df= s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade").select(["vol","prc"]).contextby('ticker').sum().top(10).toDF()
print(df)

# output
  ticker      sum_vol       sum_prc
0   AMZN  33706396492  772503.81377
1   AMZN  33706396492  772503.81377
2   AMZN  33706396492  772503.81377
3   AMZN  33706396492  772503.81377
4   AMZN  33706396492  772503.81377
5   AMZN  33706396492  772503.81377
6   AMZN  33706396492  772503.81377
7   AMZN  33706396492  772503.81377
8   AMZN  33706396492  772503.81377
9   AMZN  33706396492  772503.81377

```



#### 5.6 表连接

**merge**用于内部连接、左连接和外部连接，**merge_asof**用于asof join。

#### 5.6.1 **merge**

如果连接列名称相同，使用**on**参数指定连接列，如果连接列名称不同，使用**left_on**和**right_on**参数指定连接列。**how**参数表示表连接的类型。


内部连接分区表：

```
trade = s.table(dbPath=WORK_DIR+"/valuedb", data="trade")
t1 = s.table(data={'TICKER': ['AMZN', 'AMZN', 'AMZN'], 'date': ['2015.12.31', '2015.12.30', '2015.12.29'], 'open': [695, 685, 674]})
print(trade.merge(t1,on=["TICKER","date"]).select("*").toDF())

# outuput
  TICKER        date      VOL        PRC        BID        ASK  open
0   AMZN  2015.12.29  5734996  693.96997  693.96997  694.20001   674
1   AMZN  2015.12.30  3519303  689.07001  689.07001  689.09998   685
2   AMZN  2015.12.31  3749860  675.89001  675.85999  675.94000   695
```

#### 5.6.2 **merge_asof**
**merge_asof**对应DolphinDB中的asof join（aj）。**merge_asof**的连接列必须是整型或时序类型。如果只有1个连接列，**merge_asof**会假设右表已经根据连接列排好序。
如果有多个连接列，**merge_asof**会假设右表在其他连接列定义的每个组内根据最后一个连接列排好序。下面的例子中，虽然表t1中没有1997年的数据，但是它会使用1993年12月31日最后一个数据点。


```
from datetime import datetime
dates = [Date.from_date(x) for x in [datetime(1993,12,31), datetime(2015,12,30), datetime(2015,12,29)]]
t1 = s.table(data={'TICKER': ['AMZN', 'AMZN', 'AMZN'], 'date': dates, 'open': [695, 685, 674]})

print(trade.merge_asof(t1,on=["date"]).select(["date","prc","open"]).top(5).toDF())

         date     prc  open
0  1997.05.16  23.500   23
1  1997.05.17  20.750   23
2  1997.05.20  20.500   23
3  1997.05.21  19.625   23
4  1997.05.22  17.125   23


```



#### 6 计算

#### 6.1 回归运算

**ols**用于回归分析。返回的结果是一个具有方法分析、回归统计和系数的字典。

```
trade = s.loadTable(dbPath=WORK_DIR + "/valuedb", tableName="trade", memoryMode=True)
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

#### 6.2 **run**

**run**可用于执行任何DolphinDB脚本。如果脚本在DolphinDB中返回对象，**run**会把DolphinDB对象转换成Python中的对象。

```
# Load table
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")

# query the table and returns a pandas DataFrame
t = s.run("select bid, ask, prc from trade where bid!=NULL, ask!=NULL, vol>1000")
print(t)
```




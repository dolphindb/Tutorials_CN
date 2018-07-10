### DolphinDB 分区数据库教程



#### 1. 为什么对数据库进行分区
对数据库进行分区可以极大的降低系统响应延迟同时提高数据吞吐量。具体来说，分区有以下几个好处。
* 分区使得大型表更易于管理。对数据子集的维护操作也更加高效，因为这些操作只针对需要的数据而不是整个表。一个好的分区策略将通过只读取满足查询所需的相关数据来减少要扫描的数据量。当所有的数据都在同一个分区上，对数据库的查询，计算，以及其它操作都会被限制在磁盘访问IO这个瓶颈上。
* 分区使得系统可以充分利用所有资源。一个良好的分区方案搭配并行计算，分布式计算就可以充分利用所有节点来完成通常要在一个节点上完成的任务。 当一个任务可以拆分成几个分散的子任务，每个子任务访问不同的分区，就可以达到提升效率的目的。
* 分区增加了系统的可用性。由于分区的副本通常是存放在不同的物理节点的。所以一旦某个分区不可用，系统依然可以调用其它副本分区来保证作业的正常运转。


#### 2. DolphinDB分区和基于MPP架构的数据存储的区别

MPP(Mass Parallel Processing) 是目前主流的基于大规模并行处理技术的数据仓库普遍采用的一种方案。典型的采用该技术方案在PostgreSQ基础上的开源软件Greenplum，还有亚马逊的Reshift等。首先是MPP有一个主节点，每个客户都连接到这个主节点。DolphinDB在数据库层面不存在主节点，是点对点结构，每个客户端可以连接到任何一个数据节点，不会出现主节点瓶颈问题。

其次MPP一般通过哈希规则，将数据分布分到各个节点上。容易出现各个节点分布不均匀的问题。另外查询的时候有可能所有数据都落到一个节点上，不能充分利用所有节点的资源。DolphinDB将数据存储于分布式文件系统，有分布式文件系统全局性的统筹优化分区的存放，系统的扩容非常容易。还有一个我们在架构图上看不到的不同之处。MPP的一个表一般最多支持几万个分区，DolphinDB可以支持百万千万级别的分区数据，如果一百万个分区，每个分区1G的数据量，轻松就实现了PB级数据的存储和快速查询。

DolphinDB以最小分区为单位，将分区均匀地分配到所有节点，分区数目独立于节点数目。每一个存储数据的节点都兼顾了任务调度和计算的能力，所以我们对任意节点发起查询命令，都可以被分解给存储相关数据的节点去完成, 由于我们把数据和计算紧密结合，系统对内部的数据和资源信息有较强的感知能力，与开源集成系统相比，我们在资源调度上具有更高的效率。

![](images/distributed_mpp.JPG)



#### 3. 分区类型
分区类型是为了帮助用户根据业务进行均匀分割。DolphinDB支持多种分区方式： 顺序分区，区间分区，值分区，列表分区，复合分区。
  *  顺序分区适用于频繁快速的将数据库顺序读取到内存，比如将一个几十GB的csv文件转换成顺序分区数据库，读取到内存要比直接读取csv文件高效得多。顺序分区只能用在单节点。
  *  区间分区每个区间创建一个分区，是最常用的也是推荐的一种分区方式。通过区间，可以把数值在一个区间内的所有记录放置到一个分区。
  *  值分区每个值创建一个分区，例如股票交易日期，股票交易月。
  *  列表分区是根据用户枚举的列表来进行分区，分区更加灵活。
  *  复合分区适用于数据量大而且常用的查询经常涉及两个或以上的分区列。每层的分区可以采用区间，值或列表分区。比如按照股票交易日期进行第一层按值分区， 然后再按股票代码的值区间进行第二层按区间分区。

当这些表上的许多常用聚合函数利用分区列时，分区表特别高效。当我们创建一个新的分布式数据库时，我们需要指定数据库路径folderDirectory和分区类型partitionType以及分区模式partitionScheme。当我们重新打开现有的分布式数据库时，
我们只能指定数据库路径。不允许用不同的分区类型或分区方案覆盖现有的分布式数据库。

为了学习方便， 以下分区例子使用windows本地目录，用户可以改成数据库创建使用的路径改成linux和dfs目录。


#### 3.1. 顺序(SEQ)分区
在顺序域（SEQ）中，分区基于输入数据文件中行的顺序。**SEQ**只能在本地文件系统中使用，不能在分布式文件系统中使用。下面例子，在“C/DolphinDB/data/seqdb”文件夹下，创建了8个子文件夹。它们中的每一个对应于输入数据文件的分区。

```
n=1000000
ID=rand(100, n)
dates=2017.08.07..2017.08.11
date=rand(dates, n)
x=rand(10.0, n)
t=table(ID, date, x)
saveText(t, "C:/DolphinDB/Data/t.txt");

db = database("C:/DolphinDB/Data/seqdb", SEQ, 8)   //数字8指定多少个分区
pt = loadTextEx(db, `pt, , "C:/DolphinDB/Data/t.txt")
```
![](images/database/seq.png)

#### 3.2. 区间(RANGE)分区
分区由区间决定，区间由分区向量的任意两个相邻元素定义。起始值是包含的，结尾值是不包含的。

在下面的例子中，数据库db有两个分区：[0,5) 和[5,10]。使用函数savePartition，表t被保存为分区表pt，并在数据库db中使用ID作为分区列。

```
n=1000000
ID=rand(10, n)
x=rand(1.0, n)
t=table(ID, x)
db=database("C:/DolphinDB/Data/rangedb", RANGE,  0 5 10)

pt = db.createPartitionedTable(t, `pt, `ID)
pt.append!(t);

pt=loadTable(db,`pt)
select count(x) from pt
```

磁盘目录结构

![](images/database/range.png)


如果要创建DFS分区数据库，只需更改路径格式即可：把本地路径更改为dfs路径。系统会自动分配资源存储数据。

```
n=1000000
ID=rand(10, n)
x=rand(1.0, n)
t=table(ID, x)
db=database("dfs://rangedb", RANGE,  0 5 10)
pt = db.createPartitionedTable(t, `pt, `ID)
pt.append!(t);

pt=loadTable(db,`pt)
select count(x) from pt
```

#### 3.3.  值(VALUE)分区

在值域（VALUE）分区中，分区方案向量的每个元素都确定一个分区。

```
n=1000000
month=take(2000.01M..2016.12M, n)
x=rand(1.0, n)
t=table(month, x)

db=database("/DolphinDB/Data/valuedb", VALUE, 2000.01M..2016.12M)

// 在DFS分布式文件系统中只需把路径名改为
// db=database("dfs://valuedb", VALUE, 2000.01M..2016.12M)

pt = db.createPartitionedTable(t, `pt, `month)
pt.append!(t)

pt=loadTable(db,`pt)
select count(x) from pt
```

上面的例子定义了一个具有204个分区的数据库db。每个分区是2000年1月到2016年12月之间的一个月(如下图）。在数据库db中，表t被保存为分区表pt，分区列为month。

![](images/database/value.png)


#### 3.4 列表(LIST)分区

在列表域（LIST）中，分区方案向量的每个元素都确定一个分区。

```
n=1000000
ticker = rand(`MSFT`GOOG`FB`ORCL`IBM,n);
x=rand(1.0, n)
t=table(ticker, x)

db=database("C:/DolphinDB/Data/listdb", LIST, [`IBM`ORCL`MSFT, `GOOG`FB])
//在DFS分布式文件系统中只需把路径名改为
//db=database("dfs://listdb", LIST, [`IBM`ORCL`MSFT, `GOOG`FB])
pt = db.createPartitionedTable(t, `pt, `ticker)
pt.append!(t)

pt=loadTable(db,`pt)
select count(x) from pt
```

上面的数据库有2个分区。第一个分区包含3个股票代号，第二个分区包含2个股票代号。

![](images/database/list.png)

#### 3.5 复合(COMPO)分区

在复合（COMPO）中，可以定义2或3个分区列。每列可以是区间(RANGE)，值(VALUE)或列表(LIST)分区。

```
n=1000000
ID=rand(100, n)
dates=2017.08.07..2017.08.11
date=rand(dates, n)
x=rand(10.0, n)
t=table(ID, date, x)

dbDate = database(, VALUE, 2017.08.07..2017.08.11)
dbID=database(, RANGE, 0 50 100)
db = database("C:/DolphinDB/Data/compoDB", COMPO, [dbDate, dbID])
//在DFS分布式文件系统中只需把路径名改为
//db = database("dfs://compoDB", COMPO, [dbDate, dbID])
pt = db.createPartitionedTable(t, `pt, `date`ID)
pt.append!(t)

pt=loadTable(db,`pt)
select count(x) from pt
```

值域有5个分区：

![](images/database/hier1.png)

进入到，20170807这个分区，发现区间域(RANGE)有2个分区：

![](images/database/hier2.png)


#### 4. 分区的原则

分区的总原则是大部分查询语句可以与分区模式相匹配，只扫描部分分区数据即可实现，避免低效的全表扫描。下面详细介绍一下，分区的原则。

#### 4.1.选择合适的数据字段
在DolphinDB中，适合分区的数据类型包括整型(例如：CHAR, INT, SHORT)，日期类型(例如：DATE, MONTH)，以及可控数量的字符串(例如：SYMBOL)。

```
db=database("dfs://rangedb1", RANGE,  0.0 5.0 10.0)

//出错信息：DOUBLE数据类型的字段不能作为分区字段。

The data type DOUBLE can't be used for a partition column

```

下表显示哪些DolphinDB数据类型支持分区，哪些不支持。


| 数据类型        | 是否支持          |
| ------------- |:-------------:|
| VOID     | 否 |
| BOOL      | 否 |
| LONG| 否 |
| TIMESTAMP| 否 |
| NANOTIME| 否 |
| NANOTIMESTAMP| 否 |
| FLOAT| 否 |
| DOUBLE| 否 |
| STRING| 否 |
| CHAR | 是 |
| SHORT| 是 |
| INT| 是 |
| DATE| 是 |
| MONTH| 是 |
| TIME| 是 |
| MINUTE| 是 |
| SECOND| 是 |
| DATETIME| 是 |
| SYMBOL| 是 |


虽然DolphinDB支持对TIME, SECOND, DATETIME类型字段的分区， 但是在实际使用中要谨慎使用，避免采用值分区，以免分区粒度过细，将大量系统时间耗费在创建或查询几百上千万的只包含几条记录的文件目录。

例如下面这个例子就会产生过多的分区。
```
db=database("dfs://valuedb1",VALUE , 2012.06.01T09:30:00..2012.06.30T16:00:00);
```

因为序列：2012.06.01T09:30:00..2012.06.30T16:00:00包含2,529,001个元素。所以如果用这个序列做值分区，将会产生在磁盘上产生2,529,001分区，即产生2,529,001文件目录和相关文件。从而使得分区表创建、写入、查询都会变得缓慢。

```
>size(2012.06.01T09:30:00..2012.06.30T16:00:00);
2529001
```

避免使用STRING数据类型，因为STRING数据类型DolphinDB在后端无法通过转换成整型进行性能优化，所以无论写入还是查询效率都会降低。如果确定要采用字符串来进行分区，尽量使用SYMBOL,SYMBOL是将所有的字符串转换成整型，适用于字符串数目有限可控，例如：所有的股票代码。
如果该字段是任意字符串(STRING)就不适合用来进行分区。比如下面某论坛的留言字段。

```
我对产品很满意！
性能与我期望有差距。
...
```

##### 除了考虑数据类型之外，分区指端的值一般是不会变化的
例如， 股票代码可以作为分区字段，但股票价格不适合作为分区字段。因为股票的交易量不适合作为分区字段，因为同一股票的交易量每天都有变化，就会造成归属到不同的分区中。


#### 4.2.分区粒度的控制
分区粒度过大或过小都会造成系统效率降低。分区粒度过大会造成无法有效利用多节点多分区的优势，将本来可以并行计算的任务转化成了顺序计算任务。分区粒度过小又会造成过多并发子任务，过多磁盘访问，造成系统负荷过重。另外，当分区粒度过大，就需要频繁地在磁盘和工作内存之间进行切换，从而拖慢系统。

##### 单个分区不要过大
一般来说，合理的分区大小应该在几百兆到一个GB。由于分区列需要导入内存，如果单个分区过大，在多个用户同时使用的情况下，有可能会造成内存溢出。另外需要注意的是，DolphinDB单个分区支持最大记录条数是20亿。要对数据的大小的增长幅度有一个预估。

例如, 如果每天产生几亿条记录，按日期区间(RANGE)大粒度分区就不适合，而应该采用按值(VALUE)分区。

```
// 不适合
db=database("dfs://valuedb1", VALUE, 2017.07.01 2017.08.01 2017.09.01 2017.10.02)

// 适合
db=database("dfs://valuedb1", VALUE, 2017.07.01..2017.10.01)
```

更进一步，也可以采用复合分区(COMPO)。下面例子采用复合分区进行再度细分。

```
db1= database("", VALUE, 2017.07.01..2018.06.30)
db2 = database("", RANGE, `A...`ZZZZ)

//首先按日期进行第一层分区，然后再按字母分成26个子分区。
db = database("dfs://compodb1", COMPO, [db1, db2])

```

##### 单个分区不要过小

应该避免分区粒度过细，要确保每个分区内有足够多的数据。分区太小，会造成磁盘读取读效率太低。例如，读一个1MB和读一个1KB的文件时间是一样的。另外，所有的分区信息都会驻留在Name Node内存中，所以分区数过多太小， 可能会导致Name Node内存不足。

如果按下列这个**不恰当**的分区方案，一共只有100万条记录， 系统需要创建100万个文件目录，每个目录下面只存放一条记录。

```
n=1000000
t1=table(1..1000000 as id, rand(100.0, n) as v)
db=database("dfs://valuedb2", VALUE, 1..1000000)
db.createPartitionedTable(t1,`t1,`id).append!(t1)
```

#### 4.3.确保大部分查询语句与分区模式相符

当大部分查询语句与分区模式匹配时，就能确保我们的查询语句只是到需要的分区上查找数据，而无需对整表进行扫描，从而大幅度提高处理速度。例如，对一个股票交易的数据表，如果我们大部分语句都是按日期下载数据，并不涉及具体的股票代码，就不适合按股票代码进行分区。因为要取得一天的数据，就要涉及所有的股票代码的分区。所以合适的选择应该是按日期分区。
例如我们的数据列中包含日期date和股票代号symbol字段， 而我们大部分查询语句（如下）都是涉及date和symbol这两个字段。就可以考虑先按date,再按symbol来进行分层分区。

```
select * from mytable where date=2018.06.28, symbol='TLSA'

//或者
select * from mytable where date between 2018.06.24:2018.06.29, symbol in `FB`AMZN`TSLA`GOOG`AAPL


//或者
select sum(bidsiz) from mytable where date between 2018.06.24:2018.06.29, symbol in `FB`AMZN`TSLA`GOOG`AAPL group by date, symbol

```

那么这个分区数据库就可以这样配置。

```
db1= database("", VALUE, 2017.07.01..2018.06.30)
db2 = database("", RANGE, `A...`ZZZZ)
db = database("dfs://test", COMPO, [db1, db2])
```

#### 4.4.均匀分区

只有均匀分区才能最大程度的利用每个计算节点，否则会造成系统负荷不均衡，部分节点任务过重，而其它节点处于闲置等待状态。为了方便根据数据的分布进行分区，DolphinDB提供了一个非常有用的工具cutPoints(X, N, [freq]) 这里X是一个数组，**N**是需要产生多少个**buckets**, 而**freq**是**X**的等长数组，其中每个元素对应着**X**中元素出现的**频率**。
函数返回具有（N + 1）个元素的数组，使得**X**中的数据均匀地分布在由向量指示的**N**个**buckets**中。它可用于在分布式数据库中获取区间域的分区方案

假设大概100亿条关于8000个股票代码的记录，最好的方法就是用cutPoints根据数据分布产生均匀分区，而不是通过一个从字母A到Z的包含26个区间的简单序列。

```
db1= database("", VALUE, 2017.07.01..2018.06.30)

// **不是最优的分区方法**
db2 = database("", RANGE, `A...`ZZZZ)

// 首先按日期进行第一层分区，然后再按字母分成26个子分区。
db = database("dfs://test", COMPO, [db1, db2])
```

更合理的分区方法是，将一天或者一周数据做一个抽样统计。

```

// 将数据并行导入
t=ploadText(WORK_DIR+"/TAQ20070801.csv")

// 选择2007.08.1这天的数据来计算股票代码的分布
t=select count(*) as ct from t where date=2007.08.01 group by symbol

// 通过分布数据，以及cutPoints函数，按照股票代码按字母顺序产生128个均匀区间。每个区间内部的股票的报价记录数是相当的。
buckets = cutPoints(exec symbol from t, 128, exec ct from t)

// 将最后一个区间结束设置成不会出现的最大的数值。
buckets[size(buckets)-1]=`ZZZZZ

//这个对字符串操作产生的buckets的结果如下：
//["A",'ABA','ACEC','ADP','AFN','AII','ALTU','AMK',..., 'XEL','XLG','XLPRACL','XOMA','ZZZZZ']
//这样使得在每个子区间内的股票代码的数目相对均匀。

db1= database("", VALUE, 2017.07.01..2018.06.30)

 // **更贴近实际的分区方法**
db2 = database("", RANGE, buckets)

 // 首先按日期进行第一层分区，然后再按字母分成26个子分区。
db = database("dfs://test", COMPO, [db1, db2])
```

#### 4.5.时序类型分区

DolphinDB提供了更灵活的时序类型分区，只要保证分区的数据类型精度小于实际数据类型即可。比如说，如果数据库是按月份区，但数据库里面是date,datetime类型也是可以的。

```
// 数据库按月分区
db = database("dfs://valuedb_month", VALUE, 2018.01M 2018.02M 2018.03M)

// table column可以是date,datetime
2018.01.09

//  或者
2018.01.09 09:35：12

```

另外日期分区可以将将来时间作为分区区间。如下列把从1990年1月开始到2031年1月结束每个月作为一个分区。

```
partitions=1990.01M..2031.01M
```


#### 4.6. 多表共享一个分区数据库

当多个分区表存在于一个分区数据库内的时候，我们要保证多个分区表使用相同的分区。以下列子，三个分区表都使用同一个分区方案。

```
// 内存中创建三个表 t1,t2,t3
t1=table(1 2 5 20 50 as id, 1..5 as v)
t2=table(3 5 11 20 40 as id, 6..10 as v)
t3=table(1 2 11 20 35 as id3, 11..15 as v3)

// 创建RANGE分区数据库rangedb,分区区间为 1 10 20 30 51
// 分别以t1,t2,t3为模板创建并添加分区表pt1,pt2,pt3
db=database("dfs://rangedb",RANGE, 1 10 20 30 51)
db.createPartitionedTable(t1, `pt1, `id).append!(t1)
db.createPartitionedTable(t2, `pt2, `id).append!(t2)
db.createPartitionedTable(t3, `pt3, `id3).append!(t3)

//加载 pt1,pt2,pt3
pt1=db.loadTable("pt1")
pt2=db.loadTable("pt2")
pt3=db.loadTable("pt3")

// pt1, pt3 相同分区，相同字段名， inner join
select * from ej(pt1,pt2,`id)
>
id, v, pt2_v
5,  3, 7
20, 4, 9

// pt1, pt3 相同分区，不同字段名, inner join
select * from ej(pt1,pt3,`id, `id3)
>
id, v, v3
1,  1, 11
2, 2, 12
20, 4, 14

```


#### 5. 分区表的写入

#### 5.1 从文本文件导入

##### 5.1.1 在内存中产生数据，然后通过append!方法追加到数据库

以下例子，在内存中创建表t1, 在DFS中创建分区数据库testdb，然后以t1为模板，创建分区表pt1,最后将t1的数据追加到pt1中。注意：使用DFS存储，用户不用担心具体物理存储路，径系统会根据集群配置时指定的节点名，以及物理卷标，来自行分配。
```
t1 = table(1..10 as id)

// 按区间将数据分成两个区 1~5, 5~10, 区间不包含上界。
db = database("dfs://testdb",RANGE, 1 5 10)

// 以t1为schema模板，id为分区列名，创建名为pt1的分区表，并将内存表t1中的数据添加到分区数据库中。
db.createPartitionedTable(t1,`pt1, `id).append!(t1)
```

类似的我们也可以给出具体磁盘路径，创建一个本地分区数据库，并将t1添加到pt1中。

```
t1 = table(1..10 as id)
db = database("C:/DolphinDB/testdb",RANGE, 1 5 10)
db.createPartitionedTable(t1,`pt1, `id).append!(t1)
```

##### 5.1.2 通过loadText, ploadText将数据导入内存，然后通过append!方法追加到数据库

loadText适合于物理内存大于数据量的情况， 因为数据将被全部导入内存。

**首先通过如下代码产生数据，用于导入DolphinDB数据库**

```
// 产生数据
n=10000000
workDir = "C:/DolphinDB/Data"
if(!exists(workDir)) mkdir(workDir)
trades=table(rand(`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S,n) as sym, 2000.01.01+rand(365,n) as date, 10.0+rand(2.0,n) as price1, 100.0+rand(20.0,n) as price2, 1000.0+rand(200.0,n) as price3, 10000.0+rand(2000.0,n) as price4, 10000.0+rand(3000.0,n) as price5, 10000.0+rand(4000.0,n) as price6, rand(10,n) as qty1, rand(100,n) as qty2, rand(1000,n) as qty3, rand(10000,n) as qty4, rand(10000,n) as qty5, rand(10000,n) as qty6)
trades.saveText(workDir + "/trades.txt")

```

**通过loadText方法**

```
// 按值分区的内存数据库
db = database("dfs://valuedb", VALUE, `IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S)
pt1=db.createPartitionedTable(trades, `ptrades, `sym)
t1=loadText(workDir + "/trades.txt")
pt1.append!(t1)

```

**通过ploadText方法**
ploadText是通过多线程并行的方式将数据导入到内存，速度要比loadText有大幅度提升，但是内存占用大概是loadText的二倍。

```
t1=ploadText(workDir + "/trades.txt")
pt1.append!(t1)
```

##### 5.1.3 通过loadTextEx直接将数据添加到分区数据表（最高效模式）

通过oadTextEx可以直接将文本数据导入分区表。它的优点是：并行处理速度快,而且物理内存不必要大于数据占用内。,是DolphinDB推荐使用的加载文本数据的方法。 其实loadTextEx在内部帮助用户实现append!了方法。

```
loadTextEx(db, "pt1", "sym", workDir + "/trades.txt")
```

##### 5.1.4 通过loadTextEx并行写入数据

假设在每个数据节点的相同目录下，都有需要加载的相同格式的数据文件，但是数据没有重复，我们就可以通过以下方法将数据并行加载到数据库valuedb中。

```
def loadJob(){
    filedir='C:/DolphinDB/Data/'

    // 到路径下取出数据文件名
	filenames = exec filename from files(filedir)

	// 加载数据库
	db = database("dfs://valuedb")

	// 对每个文件，通过文件名产生jobId前缀。
	// 通过函数submitJob提交后台程序调用loadTextEx将数据加在到数据库valuedb中。
	for(fname in filenames){
		jobId = fname.strReplace(".txt", "")
		jobName = jobId

	    //注意到这里loadTextEx使用花括号的“{}”,这个是偏函数的方法，方便将该函数
	    //所需要的参数封装在一起，传递给调用函数。
		submitJob(jobId,jobName, loadTextEx{db, "pt1", `sym,filedir+'/'+fname})
	}
}

//通过pnodeRun将loadJob这个任务发送到集群的每个数据节点进行并行加载。
pnodeRun(loadJob)

//通过pnodeRun查看刚刚提交任务进展，该函数返回一个DolphinDB table，里面包含所有任务的开始时间，结束时间，状态，异常等信息。
pnodeRun(getRecentJobs)
```


#### 5.2 订阅一个流数据，批量写入

DolphinDB数据库支持流数据的处理。用户可以订阅一个流数据，系统会将订阅到的流数据批量写入到用户表中。详细内容，请参阅帮助文档关于流计算的部分。

#### 5.3 通过ODBC

用户也可以通过ODBC Plugin， 将其它数据源中的数据导入到DolphinDB中。下面例子通过ODCB将mysql中的employees表导入到DolphinDB。ODBC Plugin存放在server/plugins/odbc/。

```
loadPlugin("/DOLPHINDB_DIR/server/plugins/odbc/odbc.cfg")
use odbc
conn=connect("Driver=MySQL;Data Source = mysql-employees;server=127.0.0.1;uid=[username];pwd=[password]database=employees")
mysqlTable=query(conn,"select * from employees")
select * from mysqlTable
```

#### 5.4 通过API

DolhinDB提供了Python, Java, 以及C#API。用户在主页上下载，参照README来将数据通过这些API接口导入到DolphinDB。

#### 5.5 分区副本

在controller.cfg中，有两个非常重要的参数：dfsReplicationFactor和dfsReplicaReliabilityLevel。 dfsReplicationFactor用于决定每个表分区的副本数量。用途是某数据节点的数据损坏或者丢失，可以通过备份数据进行数据恢复。 dfsReplicaReliabilityLevel用于决定是否允许多个副本驻留在同一台服务器上。
在development阶段，允许在一个机器上配置多个节点，同时允许多个副本驻留在同一台物理服务器（dfsReplicaReliabilityLevel=0）， 但是production阶段需要设置成为1，否则起不到备份作用。

```

 // 每个表分区或文件块的副本数量。默认值是2。
dfsReplicationFactor=2

 // 多个副本是否可以驻留在同一台物理服务器上。 Level 0：允许; Level 1：不运行。默认值是0。
dfsReplicaReliabilityLevel=0
```

#### 5.6 分区事务
DolphinDB的分区支持事务管理，方便出现异常时候，事务回滚，恢复数据。但要注意两点：
1）一个事务只能包含写或者读，不能同时进行写和读。
2）多个用户的写入，对同一个分区写。


#### 6. 更多详细信息，请参阅帮助文档

中文

http://dolphindb.com/cn/help/Newtopic48.html

英文

http://dolphindb.com/help/DistributedDatabase.html

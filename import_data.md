# DolphinDB数据导入教程

企业在做大数据分析平台的选型时，避不开的一个问题就是，是否能支持将原有信息系统沉淀下来的海量数据导入到到新平台里。

根据用户数据的实际存储场景，DolphinDB提供了多种灵活的数据导入方法，来帮助用户方便的进行数据导入，具体有如下三种途径：

- 通过CSV文本文件导入。
- 通过HDF5文件导入。
- 通过ODBC接口导入。

### 1. 通过CSV文本文件导入

通过CSV文件进行数据中转是比较通用化的一种数据迁移方式，方式简单易操作。DolphinDB提供了 [loadText](http://www.dolphindb.com/cn/help/index.html?loadText.html)，
[ploadText](https://www.dolphindb.com/help/index.html?ploadText.html)，[loadTextEx](https://www.dolphindb.com/help/index.html?loadTextEx.html) 三个函数来载入CSV文本文件。

- loadText : 该函数将文本文件以 DolphinDB 数据表的形式读取到内存中。
- ploadText : 将数据文件作为分区表并行加载到内存中。与loadText函数相比，使用方式完全一样，但是ploadText速度更快。
- loadTextEx : 把数据文件转换为DolphinDB数据库中的分布式表，然后将表的元数据加载到内存中。

下面通过将 [candle_201801.csv](https://github.com/dolphindb/Tutorials_CN/blob/master/data/candle_201801.csv) 导入DolphinDB来演示loadText和loadTextEx的用法。

#### 1.1. loadText 

loadText函数有三个参数，第一个参数`filename`是文件名，第二个参数`delimiter`用于指定不同字段的分隔符，默认是","，第三个参数`schema`是用来指定导入后表的每个字段的数据类型，schema参数是table类型，具体格式如下：
name|type
---|---
timestamp|SECOND
ID|INT
qty|INT
price|DOUBLE

首先用最简单的缺省方式导入数据
```
tmpTB = loadText("<dataFilePath>/candle_201801.csv")
//可以尝试ploadText来导入并比较速度上的差异
//tmpTB = ploadText("<dataFilePath>/candle_201801.csv")
```
DolphinDB提供了字段类型自动识别功能，所以后面两个参数全部缺省也能导入大部分CSV文件，使用起来非常方便。

有时候系统自动识别的数据类型并不符合需求，比如导入数据的 volumn 字段被识别为INT类型, 而需要的 volume 类型是LONG类型，这时就需要使用schema参数，这里需要构造如下table作为schema参数：

name|type
---|---
symbol|SYMBOL
exchange|SYMBOL
cycle|INT
trdingDay|DATE
date|DATE
time|INT
open|DOUBLE
high|DOUBLE
low	|DOUBLE
close|DOUBLE
volume|INT
turnover|DOUBLE
unixTime|LONG

如果要创建这样的schema table要使用如下脚本：
```
nameCol = `symbol`exchange`cycle`trdingDay`date`time`open`high`low`close`volume`turnover`unixTime
typeCol = [SYMBOL,SYMBOL,INT,DATE,DATE,INT,DOUBLE,DOUBLE,DOUBLE,DOUBLE,INT,DOUBLE,LONG]
schemaTb = table(nameCol as name,typeCol as type)
```

当表字段非常多的时候，写这样一个脚本费时又费力，为了避免这种重复性工作，DolphinDB提供了[extractTextSchema](https://www.dolphindb.com/cn/help/index.html?extractTextSchema.html) 函数，可以从文本文件中提取表的结构生成schema table，通过对生成结果修改指定字段的数据类型，就可以得到想要的schema table。

最终导入脚本如下：
```
schema=extractTextSchema("<dataFilePath>/candle_201801.csv")
update schema set type=`LONG where name=`volume        
tt=loadText("<dataFilePath>/candle_201801.csv",,schema)
```

#### 1.2. loadTextEx

通过上述脚本，就可以将CSV文件导入到指定数据类型的内存表，而实际情况经常是数据文件体积庞大，导入时全量先载入内存，工作机的内存会成为瓶颈。DolphinDB提供的[loadTextEx](http://www.dolphindb.com/cn/help/index.html?loadText.html)函数可以较好的解决这个问题，它可以通过边载入边保存的方式，将静态CSV文件以较为平缓的数据流的方式"另存为"DolphinDB的分布式数据库表，而不是采用全量载入内存再另存分区表的方式，可以大大降低内存使用需求。

首先创建用于保存数据的分布式磁盘分区表
```
tb = loadText("<dataFilePath>/candle_201801.csv")
db=database("dfs://dataImportCSVDB",VALUE,2018.01.01..2018.01.31)  
db.createPartitionedTable(tb, "cycle", "trdingDay")
```
然后将文件直接导入分布式磁盘分区表
```
loadTextEx(db, "cycle", "trdingDay", "<dataFilePath>/candle_201801.csv")
```

当需要使用数据做分析的时候，通过loadTable函数将分区元数据先载入内存，在实际执行查询的时候，DolphinDB会按需加载数据到内存。
```
tb = database("dfs://dataImportCSVDB").loadTable("cycle");
```
### 2. 通过HDF5文件导入

HDF5是一种比CSV更标准更高效的数据文件格式，被各大数据库平台普遍支持。

#### 2.1. 使用HDF5插件
DolphinDB对HDF5文件格式是通过[HDF5插件](https://github.com/dolphindb/DolphinDBPlugin/blob/master/hdf5/README.md)来支持导入，插件提供了以下几个方法用于导入数据

- hdf5::loadHdf5 ：将h5文件导入内存表

- hdf5::loadHdf5Ex ：将h5文件导入分区磁盘表

- hdf5::extractHdf5Schema ：从h5文件中提取表结构

调用插件方法时需要在方法前面提供namespace，比如调用loadHdf5时`hdf5::loadHdf5`

要使用DolphinDB的插件，首先需要[下载HDF5插件](http://www.dolphindb.com/downloads/HDF5_V0.7.zip)，再将插件解压部署到节点的plugins目录下,在使用插件之前先使用下面的语句来加载插件

```
loadPlugin("plugins/hdf5/PluginHdf5.txt")
```

#### 2.2. 通过插件方法导入h5数据
HDF5文件的导入与CSV文件大同小异, 现在有一个candle_201801.h5文件内有一个dateset: candle_201801,那么导入过程如下：

##### 2.2.1. 通过`hdf5::loadHdf5` 将h5文件载入内存表
```
tmpTB = hdf5::loadHdf5("<dataFilePath>/candle_201801.h5","candle_201801")
```
需要指定数据类型可以使用`hdf5::extractHdf5Schema`，脚本如下
```
schema=hdf5::extractHdf5Schema("<dataFilePath>/candle_201801.h5","candle_201801")
update schema set type=`LONG where name=`volume        
tt=hdf5::loadHdf5("<dataFilePath>/candle_201801.csv","candle_201801",schema)
```
##### 2.2.2. h5文件载入到磁盘分区表

首先创建用于保存数据的分布式磁盘分区表
```
tb = hdf5::loadHdf5("<dataFilePath>/candle_201801.h5","candle_201801")
db=database("dfs://dataImportHDF5DB",VALUE,2018.01.01..2018.01.31)  
db.createPartitionedTable(tb, "cycle", "trdingDay")
```
然后将HDF5文件通过`hdf5::loadHdf5Ex`函数导入
```
hdf5::loadHdf5Ex(db, "cycle", "trdingDay", "<dataFilePath>/candle_201801.h5","candle_201801")
```

### 3. 通过ODBC接口导入

DolphinDB支持ODBC接口连接第三方数据库，从数据库中直接将表读取成DolphinDB的内存数据表。

#### 3.1. 使用ODBC插件
DolphinDB官方提供[ODBC插件](https://github.com/dolphindb/DolphinDBPlugin/blob/master/odbc/README.md)用于连接三方数据源，使用该插件可以方便的从ODBC支持的数据库中迁移数据至dolphinDB中。

ODBC插件提供了以下四个方法用于操作第三方数据源数据
odbc::connect : 开启连接
odbc::close : 关闭连接
odbc::query : 根据给定的SQL语句查询数据并返回到DolphinDB的内存表
odbc::execute : 在三方数据库内执行给定的SQL语句，不返回数据。

注意在使用ODBC插件之前，需要先给系统安装ODBC驱动,[请参考ODBC插件使用教程](https://github.com/dolphindb/DolphinDBPlugin/blob/master/odbc/README.md)

现在以连接MS SQL SERVER作为实例，现有数据库的具体配置为，
- server：172.18.0.15
- 默认端口：1433
- 连接用户名：sa
- 密码：123456
- 数据库名称： SZ_TAQ

数据库表选2016年1月1日的数据，表名candle_201801，字段与csv文件相同。

要使用ODBC插件连接SQL Server数据库，首先第一步是下载插件解压并拷贝plugins\odbc目录下所有文件到DolphinDB server的plugins/odbc目录下，通过下面的脚本完成插件初始化
```
//载入插件
loadPlugin("plugins/odbc/odbc.cfg")
//连接MS SQLSERVER
conn=odbc::connect("Driver=ODBC Driver 17 for SQL Server;Server=172.18.0.15;Database=SZ_TAQ;Uid=sa;
Pwd=123456;")
```

#### 3.2. 导入数据

首先创建分布式磁盘数据库用于保存导入的数据
```
//从sqlserver中取到表结构作为DolphinDB导入表的模板
tb = odbc::query(conn,"select top 1 * from candle_201801")
db=database("dfs://dataImportODBC",VALUE,2018.01.01..2018.01.31)
db.createPartitionedTable(tb, "cycle", "trdingDay")
```
从SQL SERVER中导入数据并保存成DolphinDB分区表
```
data = odbc::query(conn,"select * from candle_201801")
tb = database("dfs://dataImportODBC").loadTable("cycle")
tb.append!(data);
```

通过ODBC导入数据避免了文件导出导入的过程，而且通过DolphinDB的定时作业机制，它还可以作为时序数据定时同步的数据通道。

### 4. 金融数据导入案例

下面以国内深市的日K线图数据文件导入作为示例，数据以CSV文件格式保存在磁盘上，共有10年的数据，按产品分保存，一共大约100G的数据，保存路径是以<年份>-<产品编号>-K线图类型.csv这方式，路径示例如下：
```
2008
    ----A(Product)
        ---- candle_1.csv
        ---- candle_5.csv
        ---- candle_15.csv
        ---- ...
    ----B(Product)
    ----C(Product)
2009
...
2018
```
每个文件的结构都是一致的，如图所示：

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/csvfile.PNG?raw=true)

由于文件是保存在年度和产品子目录下，所以文件本身内容里并没有保存年度和产品信息，在导入到DolphinDB时，需要手工添加上product这列信息，年份信息在trdingDay列中已经包含，所以不需要添加。

最终计划导入数据表结构如下
`product,symbol,exchange,cycle,trdingDay,date,time,open,high,low,close,volume,turnover,unixTime`

#### 4.1. 分区规划

要导入数据之前，首先要做好数据的分区规划，这涉及到两个方面的考量：
- 如何选择分区字段
- 如何保证分区的大小均匀合理。

首先根据日常的查询语句执行频率，总结出最常使用的检索字段 tradeDate和product两个字段，通过对常用检索字端分区，可以极大的提升数据检索和分析的效率。

而数据划分的粒度,理论上每个数据块保持在100M-1G之间是比较合理的大小范围，所以总体100G的数据大概分成100到1000个这个数量范围比较合适。考虑到分区两个字段的特征，tradeDate可以通过范围(Range)方式按年度分成10个区，而product产品数量刚好在100左右，所以对product按值(Value)进行分区，最终的数据块大小在100M左右，在合理区间范围内。
这里product的数量比较凑巧，所以采用了按值分区，如果product产品数量较多，那么按值分区会使得每个分区体积太小，这时可以考虑使用范围(Range)方式分区，将多个product包含在一个范围分区内。

分区脚本如下
```
dbPath = "dfs://SAMPLE_TRDDB"
tableName = `CANDLE
rootDir="<fileRoot>/candle"
yearRange =date(2008.01M + 12*0..22)

//从文件系统中统计出所有不重复的products
products = array(SYMBOL, 0, 100)
yearDirs = files(rootDir)[`filename]
for(yearDir in yearDirs){
	path = rootDir + "/" + yearDir
	products.append!(files(path)[`filename].upper())
}
products = products.distinct().sort();
products

dbDate=database("", RANGE, yearRange)
dbID=database("", VALUE, products)

db = database(dbPath, COMPO, [dbDate, dbID])
pt=db.createPartitionedTable(table(1000000:0, `product`symbol`exchange`cycle`tradingDay`date`time`open`high`low`close`volume`turnover`oi`unixTime, [SYMBOL,SYMBOL,SYMBOL,INT,DATE,DATE,TIME,DOUBLE,DOUBLE,DOUBLE,DOUBLE,LONG,DOUBLE,LONG,LONG]), tableName, `tradingDay`product)

```

分区规划的时候需要注意的是，务必在分区范围上为后续数据留足余量，因为DolphinDB在保存数据时判断数据如果在分区范围之外，会识别为无效数据放弃保存，所以很多时候执行了新增数据的脚本，但是数据没有入库，往往是由于这个原因导致。

#### 4.2. 导入数据
数据导入脚本的主要思路很简单，就是通过循环目录树，将所有的csv文件逐个读取并写入到分布式数据库表`dfs://SAMPLE_TRDDB`中，但是具体导入过程中还是会有很多细节问题。

首先碰到的问题是，csv文件中保存的数据格式与DolphinDB内部的数据格式存在差异，比如time字段，文件里是以“9390100000”表示精确到毫秒的时间，如果直接读入会被识别成数值类型，而不是time类型，所以这里需要用到数据转换函数`datetimeParse`结合格式化函数`format`在数据导入时进行转换。

其次虽然通过循环导入实现起来非常简单，但是实际上100G的数据是由极多的5M左右的细碎文件组成，如果单线程操作会这个等待时间会很久。由于系统是通过多个并行线程来管理任务队列，为了保证充分利用集群的资源，这里按照年度把数据导入拆分成多个小任务，轮流发送到各节点的任务队列去执行，利用多节点并行，提高导入的效率。需要注意一个问题，当任务并行进行的时候，容易发生多任务同时写入同一个分区的问题，比如 2010年productId=A的分区，如果有两个任务写入的数据都属于这个分区，并且同时发生写入，这时任务会执行失败。为了避免这一问题，最有效的方式就是**让每个并行任务负责的数据都属于不同的分区**。

最终形成的导入脚本如下
```
dbPath = "dfs://SAMPLE_TRDDB"
tableName = `CANDLE
rootDir="<fileRoot>/candle"
//定义按年度导入任务函数用于提交线程池并行处理
def loadCsvFromYearPath(path, dbPath, tableName){
	products = files(path)[`filename]
	for(product in products){
		proPath = path + "/" + product
		fs = files(proPath)[`filename]
		for(j in fs){
			filePath = proPath + "/" + j
			t=loadText(filePath)
			database(dbPath).loadTable(tableName).append!(select product.upper(),symbol,exchange,cycle,trdingDay as tradingDay,date,datetimeParse(format(time,"000000000"),"HHmmssSSS"),open,high,low,close,long(volume),turnover,long(openInterest),unixTime from t )		
		}
	}
}
//定义节点别名数组，下面的循环会逐个向数组中的节点发任务
nodesAlias="NODE" + string(1..4)
years= files(rootDir)[`filename]

index = 0;
for(year in years){	
	yearPath = rootDir + "/" + year
	des = "loadCsv_" + year
	rpc(nodesAlias[index%nodesAlias.size()],submitJob,des,des,loadCsvFromYearPath,yearPath,dbPath,tableName)
	index=index+1
}
```

### 6. 附录
[candle_201801.csv](https://github.com/dolphindb/Tutorials_CN/blob/master/data/candle_201801.csv)

[candle_201801.h5](https://github.com/dolphindb/Tutorials_CN/blob/master/data/candle_201801.h5)
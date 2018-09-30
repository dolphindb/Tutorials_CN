# DolphinDB数据导入教程

企业在使用大数据分析平台时，第一步就是要把海量数据从多个数据源迁移到大数据平台中，这是一项重要但又往往费时费力的工作，DolphinDB在这个方面提供了很好的支持。

DolphinDB提供了多种灵活的数据导入方法，来帮助用户方便的进行数据导入，具体有如下三种途径：

- 通过CSV文本文件导入。
- 通过HDF5文件导入。
- 通过ODBC接口导入。

### 1. DolphinDB数据库基本概念

DolphinDB里数据以结构化数据表的方式保存。数据表按存储介质可以分为内存表，本地磁盘表，分布式表；按是否分区可以分为普通表和分区表。

在传统的数据库系统，数据库(Database)更多理解为数据对象的容器，而在DolphinDB里，Database是定义了数据分区方式和存储相关的元数据信息。最关键的区别是，传统的数据库里分区是针对Table定义的，而DolphinDB的分区是针对Database来定义的，也就是说同一个Database下的Table只能使用同一种分区机制。

### 2. 通过CSV文本文件导入

通过CSV文件进行数据中转是比较通用化的一种数据迁移方式，方式简单易操作。DolphinDB提供了 [loadText](http://www.dolphindb.com/cn/help/index.html?loadText.html)，
[ploadText](https://www.dolphindb.com/help/index.html?ploadText.html)，[loadTextEx](https://www.dolphindb.com/help/index.html?loadTextEx.html) 三个函数来载入CSV文本文件。

- loadText : 该函数将文本文件以 DolphinDB 数据表的形式读取到内存中。
- ploadText : 将数据文件作为分区表并行加载到内存中。与loadText函数相比，使用方式完全一样，但是ploadText速度更快。
- loadTextEx : 把数据文件转换为DolphinDB数据库中的分布式表，然后将表的元数据加载到内存中。

下面通过将 [candle_201801.csv](https://github.com/dolphindb/Tutorials_CN/blob/master/data/candle_201801.csv) 导入DolphinDB来演示loadText和loadTextEx的用法。

#### 2.1. loadText 

loadText函数有三个参数，第一个参数`filename`是文件名，第二个参数`delimiter`用于指定不同字段的分隔符，默认是","，第三个参数`schema`是用来指定导入后表的每个字段的数据类型，schema参数是table类型，格式示例如下：

name|type
---|---
timestamp|SECOND
ID|INT
qty|INT
price|DOUBLE

首先用最简单的缺省方式导入数据：
```
dataFilePath = "/home/data/candle_201801.csv"
tmpTB = loadText(dataFilePath)
```
DolphinDB提供了字段类型自动识别功能，所以后面两个参数全部缺省也能导入大部分CSV文件，使用起来非常方便。

有时候系统自动识别的数据类型并不符合需求，比如导入数据的 volume 字段被识别为INT类型, 而需要的 volume 类型是LONG类型，这时就需要使用schema参数，这里需要构造如下table作为schema参数：

name|type
---|---
symbol|SYMBOL
exchange|SYMBOL
cycle|INT
tradingDay|DATE
date|DATE
time|INT
open|DOUBLE
high|DOUBLE
low	|DOUBLE
close|DOUBLE
volume|INT
turnover|DOUBLE
unixTime|LONG

要创建这样的 schema table 要使用如下脚本：
```
nameCol = `symbol`exchange`cycle`tradingDay`date`time`open`high`low`close`volume`turnover`unixTime
typeCol = [SYMBOL,SYMBOL,INT,DATE,DATE,INT,DOUBLE,DOUBLE,DOUBLE,DOUBLE,INT,DOUBLE,LONG]
schemaTb = table(nameCol as name,typeCol as type)
```

当表字段非常多的时候，写这样一个脚本费时又费力，为了避免这种重复性工作，DolphinDB提供了[extractTextSchema](https://www.dolphindb.com/cn/help/index.html?extractTextSchema.html) 函数，可以从文本文件中提取表的结构生成schema 修改指定字段的数据类型，就可以得到想要的schema table。

整合上述方法，最终导入脚本如下：
```
dataFilePath = "/home/data/candle_201801.csv"
schemaTb=extractTextSchema(dataFilePath)
update schemaTb set type=`LONG where name=`volume        
tt=loadText(dataFilePath,,schemaTb)
```
#### 2.2. ploadText

ploadText函数的特点可以快速载入大文件，它在设计上充分利用了多个core来并行载入文件，并行程度取决于服务器本身core数量和节点的localExecutors配置。

下面通过实际载入对比来了解ploadText的特性。

首先通过脚本生成一个4G左右的CSV文件：
```
	filePath = "/home/data/testFile.csv"
	appendRows = 100000000
	dateRange = 2010.01.01..2018.12.30
	ints = rand(100, appendRows)
	symbols = take(string('A'..'Z'), appendRows)
	dates = take(dateRange, appendRows)
	floats = rand(float(100), appendRows)
	times = 00:00:00.000 + rand(86400000, appendRows)
	t = table(ints as int, symbols as symbol, dates as date, floats as float, times as time)
	t.saveText(filePath)
```
分别通过loadText和ploadText来载入文件，节点设置 `localExecutors=7`。
```
timer loadText(filePath);
```

> Time elapsed: `39728.393` ms

```
timer ploadText(filePath);
```

> Time elapsed: `10685.838` ms


#### 2.3. loadTextEx

当数据文件体积非常庞大，loadText函数总是把数据全量导入内存，工作机的内存很容易成为瓶颈。DolphinDB提供的[loadTextEx](http://www.dolphindb.com/cn/help/index.html?loadText.html)函数可以较好的解决这个问题，它可以通过边载入边保存的方式，将静态CSV文件以较为平缓的数据流的方式"另存为"DolphinDB的分布式表，而不是采用全量载入内存再另存分区表的方式，可以大大降低内存使用需求。

首先创建用于保存数据的分布式表：
```
dataFilePath = "/home/data/candle_201801.csv"
tb = loadText(dataFilePath)
db=database("dfs://dataImportCSVDB",VALUE,2018.01.01..2018.01.31)  
db.createPartitionedTable(tb, "cycle", "tradingDay")
```
然后将文件导入分布式表：
```
loadTextEx(db, "cycle", "tradingDay", dataFilePath)
```

当需要使用数据做分析的时候，通过loadTable函数将分区元数据先载入内存，在实际执行查询的时候，DolphinDB会按需加载数据到内存。
```
tb = database("dfs://dataImportCSVDB").loadTable("cycle")
```
### 3. 通过HDF5文件导入

HDF5是一种比CSV更高效的二进制数据文件格式，在数据分析领域广泛使用。DolphinDB也支持通过HDF5格式文件导入数据。

DolphinDB通过[HDF5插件](https://github.com/dolphindb/DolphinDBPlugin/blob/master/hdf5/README.md)来访问HDF5文件，插件提供了以下方法：

- hdf5::ls : 列出h5文件中所有 Group 和 Dataset 对象。

- hdf5::lsTable ：列出h5文件中所有 Dataset 对象。

- hdf5::hdf5DS ：返回h5文件中 Dataset 的元数据。

- hdf5::loadHdf5 ：将h5文件导入内存表。

- hdf5::loadHdf5Ex ：将h5文件导入分区表。

- hdf5::extractHdf5Schema ：从h5文件中提取表结构。

调用插件方法时需要在方法前面提供namespace，比如调用loadHdf5时`hdf5::loadHdf5`，如果不想每次调用都使用namespace，可以使用`use`关键字：
```
use hdf5
loadHdf5(filePath,tableName);
```

要使用DolphinDB的插件，首先需要[下载HDF5插件](http://www.dolphindb.com/downloads/HDF5_V0.7.zip)，再将插件部署到节点的plugins目录下，在使用插件之前需要先加载，使用下面的脚本：
```
loadPlugin("plugins/hdf5/PluginHdf5.txt")
```

HDF5文件的导入与CSV文件大同小异，比如我们要将candle_201801.h5文件导入，candle_201801.h5文件内包含一个Dataset: candle_201801，那么最简单的导入方式如下：
```
dataFilePath = "/home/data/candle_201801.h5"
datasetName = "candle_201801"
tmpTB = hdf5::loadHdf5(dataFilePath,datasetName)
```
如果需要指定数据类型导入可以使用`hdf5::extractHdf5Schema`，脚本如下：
```
dataFilePath = "/home/data/candle_201801.h5"
datasetName = "candle_201801"
schema=hdf5::extractHdf5Schema(dataFilePath,datasetName)
update schema set type=`LONG where name=`volume        
tt=hdf5::loadHdf5(dataFilePath,datasetName,schema)
```
如果h5文件非常庞大，工作机内存无法支持全量载入，可以使用`hdf5::loadHdf5Ex`方式来载入数据

首先创建用于保存数据的分布式表：
```
dataFilePath = "/home/data/candle_201801.h5"
datasetName = "candle_201801"
dfsPath = "dfs://dataImportHDF5DB"
tb = hdf5::loadHdf5(dataFilePath,datasetName)
db=database(dfsPath,VALUE,2018.01.01..2018.01.31)  
db.createPartitionedTable(tb, "cycle", "tradingDay")
```
然后将HDF5文件通过`hdf5::loadHdf5Ex`函数导入
```
hdf5::loadHdf5Ex(db, "cycle", "tradingDay", dataFilePath,datasetName)
```

### 4. 通过ODBC接口导入

DolphinDB支持ODBC接口连接第三方数据库，从数据库中直接将表读取成DolphinDB的内存数据表。

DolphinDB官方提供[ODBC插件](https://github.com/dolphindb/DolphinDBPlugin/blob/master/odbc/README.md)用于连接第三方数据源，使用该插件可以方便的从ODBC支持的数据库中迁移数据至DolphinDB中。

ODBC插件提供了以下四个方法用于操作第三方数据源数据：

- odbc::connect : 开启连接。

- odbc::close : 关闭连接。

- odbc::query : 根据给定的SQL语句查询数据并返回到DolphinDB的内存表。

- odbc::execute : 在第三方数据库内执行给定的SQL语句，不返回数据。

注意在使用ODBC插件之前，需要先给系统安装ODBC驱动，[请参考ODBC插件使用教程](https://github.com/dolphindb/DolphinDBPlugin/blob/master/odbc/README.md)。

现在以连接 SQL Server 作为实例，现有数据库的具体配置为：
- server：172.18.0.15
- 默认端口：1433
- 连接用户名：sa
- 密码：123456
- 数据库名称： SZ_TAQ

数据库表选2016年1月1日的数据，表名candle_201801，字段与CSV文件相同。

要使用ODBC插件连接SQL Server数据库，首先第一步是下载插件解压并拷贝plugins\odbc目录下所有文件到DolphinDB Server的plugins/odbc目录下，通过下面的脚本完成插件初始化：
```
//载入插件
loadPlugin("plugins/odbc/odbc.cfg")
//连接 SQL Server
conn=odbc::connect("Driver=ODBC Driver 17 for SQL Server;Server=172.18.0.15;Database=SZ_TAQ;Uid=sa;
Pwd=123456;")
```

在导入数据之前，先创建分布式磁盘数据库用于保存数据：
```
//从SQL Server中取到表结构作为DolphinDB导入表的模板
tb = odbc::query(conn,"select top 1 * from candle_201801")
db=database("dfs://dataImportODBC",VALUE,2018.01.01..2018.01.31)
db.createPartitionedTable(tb, "cycle", "tradingDay")
```
从SQL Server中导入数据并保存成DolphinDB分区表：
```
data = odbc::query(conn,"select * from candle_201801")
tb = database("dfs://dataImportODBC").loadTable("cycle")
tb.append!(data);
```
通过ODBC导入数据避免了文件导出导入的过程，而且通过DolphinDB的定时作业机制，它还可以作为时序数据定时同步的数据通道。

### 5. 金融数据导入案例

下面以证券市场日K线图数据文件导入作为示例，数据以CSV文件格式保存在磁盘上，共有10年的数据，按年度分目录保存，一共大约100G的数据，路径示例如下：
```
2008
    ---- 000001.csv
    ---- 000002.csv
    ---- 000003.csv
    ---- 000004.csv
	---- ...
2009
...
2018
```
每个文件的结构都是一致的，如图所示：

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/csvfile.PNG?raw=true)

#### 5.1. 分区规划

要导入数据之前，首先要做好数据的分区规划，这涉及到两个方面的考量：
- 确定分区字段。
- 确定分区的粒度。

首先根据日常的查询语句执行频率，我们采用trading和symbol两个字段进行组合范围(RANGE)分区，通过对常用检索字段分区，可以极大的提升数据检索和分析的效率。

接下来要做的是分别定义两个分区的粒度。

现有数据的时间跨度是从2008-2018年，所以这里按照年度对数据进行时间上的划分，在规划时间分区时要考虑为后续进入的数据留出足够的空间，所以这里把时间范围设置为2008-2030年。
```
yearRange =date(2008.01M + 12*0..22)
```

这里股票代码有几千个，如果按单个股票分区，那么每个分区只是几兆大小，而分区数量则很多。分布式系统在执行查询时，会将查询语句分成多个子任务分发到不同的分区执行，上面的分区方式会导致任务数量非常多，而任务执行时间极短，导致系统在管理任务上花费的时间反而大于任务本身的执行时间，这样的分区方式明显是不合理的，这里我们按照范围将股票代码均分成100个区间，每个区间作为一个分区，最终分区的大小约100M左右。 考虑到后期有新的股票数据进来，所以增加了一个虚拟的代码999999，跟最后一个股票代码组成一个分区，用来保存后续新增股票的数据。

通过下面的脚本得到 symbol 字段的分区范围 symRanges：
```
//遍历所有的年度目录，去重整理出股票代码清单，并通过cutPoint分成100个区间
symbols = array(SYMBOL, 0, 100)
yearDirs = files(rootDir)[`filename]
for(yearDir in yearDirs){
	path = rootDir + "/" + yearDir
	symbols.append!(files(path)[`filename].upper().strReplace(".CSV",""))
}
//去重并增加扩容空间：
symbols = symbols.distinct().sort!().append!("999999");
//均分成100份
symRanges = symbols.cutPoints(100)
```

通过下述脚本定义两个维度组合(COMPO)分区，创建Database和分区表：

```
columns=`symbol`exchange`cycle`tradingDay`date`time`open`high`low`close`volume`turnover`unixTime
types =  [SYMBOL,SYMBOL,INT,DATE,DATE,TIME,DOUBLE,DOUBLE,DOUBLE,DOUBLE,LONG,DOUBLE,LONG]

dbDate=database("", RANGE, yearRange)
dbID=database("", RANGE, symRanges)
db = database(dbPath, COMPO, [dbDate, dbID])

pt=db.createPartitionedTable(table(1000000:0,columns,types), tableName, `tradingDay`symbol)
```

#### 5.2. 导入数据
数据导入脚本的主要思路很简单，就是通过循环目录树，将所有的CSV文件逐个读取并写入到分布式数据库表`dfs://SAMPLE_TRDDB`中，但是具体导入过程中还是会有很多细节问题。

首先碰到的问题是，CSV文件中保存的数据格式与DolphinDB内部的数据格式存在差异，比如time字段，文件里是以“9390100000”表示精确到毫秒的时间，如果直接读入会被识别成数值类型，而不是time类型，所以这里需要用到数据转换函数`datetimeParse`结合格式化函数`format`在数据导入时进行转换。
关键脚本如下：
```
datetimeParse(format(time,"000000000"),"HHmmssSSS")
```
虽然通过循环导入实现起来非常简单，但是实际上100G的数据是由极多的5M左右的细碎文件组成，如果单线程操作会等待很久，为了充分利用集群的资源，所以我们按照年度把数据导入拆分成多个子任务，轮流发送到各节点的任务队列并行执行，提高导入的效率。这个过程分下面两步实现：

先定义一个自定义函数，函数的主要功能是导入指定年度目录下的所有文件：
```
//循环处理年度目录下的所有数据文件
def loadCsvFromYearPath(path, dbPath, tableName){
	symbols = files(path)[`filename]
	for(sym in symbols){
		filePath = path + "/" + sym
		t=loadText(filePath)
		database(dbPath).loadTable(tableName).append!(select symbol, exchange,cycle, tradingDay,date,datetimeParse(format(time,"000000000"),"HHmmssSSS"),open,high,low,close,volume,turnover,unixTime from t )			
	}
}
```
然后通过 [rpc](https://www.dolphindb.com/help/rpc.html) 函数结合 [submitJob](https://www.dolphindb.com/help/submitJob.html) 函数把上面定义的函数提交到各节点去执行：
```
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

需要注意的是，CHUNK(最底层分区数据块)是DolphinDB存储数据的最小单位，DolphinDB对CHUNK的写入操作是**独占式的**，当任务并行进行的时候，需要避免多任务同时向一个CHUNK写入数据。案例中我们设计每年的数据写入交给一个单独任务去做，各任务操作的数据边界没有重合，所以不可能发生多任务写入同一CHUNK的情况。

### 6. 附录
文中示例使用的CSV和HDF5格式提供下载，供脚本演练使用。

[candle_201801.csv](https://github.com/dolphindb/Tutorials_CN/blob/master/data/candle_201801.csv)

[candle_201801.h5](https://github.com/dolphindb/Tutorials_CN/blob/master/data/candle_201801.h5)
# 国内股票行情数据导入实例

DolphinDB提供了详细的[`文本数据加载教程`](./import_data.md)，以帮助用户导入数据。本文是以此为基础的一个实践案例，对每只股票每天一个csv文件的导入场景，提供了一个高性能的解决方案。

- [1. 应用需求](#1-应用需求)
- [2. 建库建表](#2-建库建表)
    - [2.1 DolphinDB的分区机制](#21-dolphindb的分区机制)
    - [2.2 数据库设计](#22-数据库设计)
    - [2.3 建库建表脚本](#23-建库建表脚本)
- [3. 新格式数据导入](#3-新格式数据导入)
- [4. 旧格式数据导入](#4-旧格式数据导入)

## 1. 应用需求

现有最近10年的历史行情数据。这些数据有以下特点：

* 数据源以CSV文件格式存储，每个股票每天的数据存为一个CSV文件；4000余只股票，每天生成4000余个文件，每个文件大小在60KB到2MB之间，每天总数据量在3到5GB。

* 需要导入的文件所在的的目录结构为~/yyyy/yyyyMMdd/，即按年月日存储，例如2020年1月2日的存储目录为~/2020/20200102。文件名为市场代码+证券代码+[yyyyMMdd].csv，例如SH501000.csv和SZ399985_20130104.csv等。

* 文件内容结构分2种。第一种是2015年至今的数据（下文简称新格式数据），示例如下：
```
Symbol,DateTime,Status,PreClose,Open,High,Low,Price,TotalVolume,TotalAmount,AskPrice1,AskPrice2,AskPrice3,AskPrice4,AskPrice5,AskPrice6,AskPrice7,AskPrice8,AskPrice9,AskPrice10,BidPrice1,BidPrice2,BidPrice3,BidPrice4,BidPrice5,BidPrice6,BidPrice7,BidPrice8,BidPrice9,BidPrice10,AskVolume1,AskVolume2,AskVolume3,AskVolume4,AskVolume5,AskVolume6,AskVolume7,AskVolume8,AskVolume9,AskVolume10,BidVolume1,BidVolume2,BidVolume3,BidVolume4,BidVolume5,BidVolume6,BidVolume7,BidVolume8,BidVolume9,BidVolume10,TickCount,BidOrderTotalVolume,AskOrderTotalVolume,AvgBidOrderPrice,AvgAskOrderPrice,LimitHighestPrice,LimitLowestPrice

SH501001,2020-01-02 09:25:01,2,1.133,0,0,0,0,0,0.0000,1.145,1.146,1.148,1.199,0,0,0,0,0,0,1.13,1.11,1.1,1.059,0,0,0,0,0,0,2900,100,16900,28300,0,0,0,0,0,0,66700,100,100,100,0,0,0,0,0,0,0,67000,48200,1.13,1.178,1.246,1.02
SH501001,2020-01-02 09:25:28,2,1.133,0,0,0,0,0,0.0000,1.145,1.146,1.148,1.199,0,0,0,0,0,0,1.13,1.11,1.1,1.059,0,0,0,0,0,0,2900,100,16900,28300,0,0,0,0,0,0,66700,100,100,100,0,0,0,0,0,0,0,67000,48200,1.13,1.178,1.246,1.02
SH501001,2020-01-02 09:26:28,2,1.133,0,0,0,0,0,0.0000,1.145,1.146,1.148,1.199,0,0,0,0,0,0,1.13,1.11,1.1,1.059,0,0,0,0,0,0,2900,100,16900,28300,0,0,0,0,0,0,66700,100,100,100,0,0,0,0,0,0,0,67000,48200,1.13,1.178,1.246,1.02
SH501001,2020-01-02 09:27:28,2,1.133,0,0,0,0,0,0.0000,1.145,1.146,1.148,1.199,0,0,0,0,0,0,1.13,1.11,1.1,1.059,0,0,0,0,0,0,2900,100,16900,28300,0,0,0,0,0,0,66700,100,100,100,0,0,0,0,0,0,0,67000,48200,1.13,1.178,1.246,1.02
SH501001,2020-01-02 09:28:28,2,1.133,0,0,0,0,0,0.0000,1.145,1.146,1.148,1.199,0,0,0,0,0,0,1.13,1.11,1.1,1.059,0,0,0,0,0,0,2900,100,16900,28300,0,0,0,0,0,0,66700,100,100,100,0,0,0,0,0,0,0,67000,48200,1.13,1.178,1.246,1.02
SH501001,2020-01-02 09:29:28,2,1.133,0,0,0,0,0,0.0000,1.145,1.146,1.148,1.199,0,0,0,0,0,0,1.13,1.11,1.1,1.059,0,0,0,0,0,0,2900,100,16900,28300,0,0,0,0,0,0,66700,100,100,100,0,0,0,0,0,0,0,67000,48200,1.13,1.178,1.246,1.02
```
另一种是2015年之前的数据（下文简称旧格式数据)，示例如下：
```
市场代码,证券代码,时间,最新,成交笔数,成交额,成交量,方向,买一价,买二价,买三价,买四价,买五价,卖一价,卖二价,卖三价,卖四价,卖五价,买一量,买二量,买三量,买四量,买五量,卖一量,卖二量,卖三量,卖四量,卖五量
sz,000001,2012-01-04 09:25:02,15.5900,111,3855407.0000,2473.0000,B,15.5800,15.5500,15.5400,15.5300,15.5100,15.5900,15.6000,15.6100,15.6200,15.6300,19,16,3,5,17,53,3028,2462,247,450
sz,000001,2012-01-04 09:30:06,15.5800,71,1596377.0000,1025.0000,S,15.5500,15.5300,15.5200,15.5100,15.5000,15.5600,15.5800,15.5900,15.6000,15.6100,11,10,16,109,1680,10,828,3917,2382,2462
sz,000001,2012-01-04 09:30:09,15.5300,4,30305.0000,19.0000,S,15.5300,15.5200,15.5100,15.5000,15.4900,15.5600,15.5800,15.5900,15.6000,15.6100,1,16,109,1680,15,10,838,3917,2382,2462
sz,000001,2012-01-04 09:30:11,15.5600,2,9335.0000,6.0000,B,15.5300,15.5200,15.5100,15.5000,15.4900,15.5600,15.5800,15.5900,15.6000,15.6100,1,16,109,1680,15,4,883,3917,2382,2462
sz,000001,2012-01-04 09:30:16,15.5800,5,173593.0000,112.0000,B,15.5200,15.5100,15.5000,15.4900,15.4800,15.5800,15.5900,15.6000,15.6100,15.6200,16,109,1680,15,1100,799,3923,2382,2462,143
sz,000001,2012-01-04 09:30:21,15.5200,3,10781.0000,6.0000,S,15.5200,15.5100,15.5000,15.4900,15.4800,15.5700,15.5800,15.5900,15.6000,15.6100,11,114,1680,15,1100,98,877,3913,2376,2462
```
其中字段名为中文，编码方式为GB2312。
* 新格式数据中的Symbol字段对应旧格式数据的市场代码+证券代码。
* 新格式数据中有TotalVolume（累计成交量）、TotalAmount（累计成交额）2列，没有成交量和成交额，旧格式数据相反，有成交量和成交额这2列，没有累计成交量、累计成交额。
* 新格式数据中买卖价和买卖量有10档，旧格式数据是5档。

现在需要导入这些行情到DolphinDB分布式库表中，以便用于量化分析计算。要求：

* 表结构以新格式数据的列为基准，但把Symbol字段分为Symbol(证券代码)+market（市场代码），TotalVolume（累计成交量）改成Volume（成交量），TotalAmount（累计成交额）改为Amount（成交额）。
* 旧格式数据各字段与表结构的对应关系如下:

|旧格式数据中的字段|表中字段| 旧格式数据中的字段|表中字段| 
|----|----|----|-----|
|证券代码|Symbol中数字| 卖一价|AskPrice1|
|市场代码|Symbol中字母|卖二价|AskPrice2|
|时间|DateTime|  卖三价|AskPrice3|
|最新价|Price| 卖四价|AskPrice4|
|成交笔数|TickCount| 卖五价|AskPrice5|
|成交额|Amount|买一量|BidVolume1|
|成交量*100|Volume| 买二量|BidVolume2| 
|买一价|BidPrice1| 买三量|BidVolume3|
|买二价|BidPrice2|  买四量|BidVolume4|
|买三价|BidPrice3| 买五量|BidVolume5|
|买四价|BidPrice4|  卖一量|AskVolume1|
|买五价|BidPrice5|卖二量|AskVolume2|
|  ||卖三量|AskVolume3| 
| | |卖四量|AskVolume4|
|  ||卖五量|AskVolume5|

新格式数据样本文件[下载](https://www.dolphindb.cn/downloads/tutorial/2020.zip)；旧格式数据样本文件[下载](https://www.dolphindb.cn/downloads/tutorial/2013.zip)。

## 2. 建库建表
### 2.1 DolphinDB的分区机制

DolphinDB利用分布式文件系统实现数据库的存储和基本事务机制。数据库以分区（chunk）为单位进行管理。分区的元数据（元数据指数据库的分区信息，每个分区的版本链，大小，存储位置等）存储在控制节点，副本数据存储在各数据节点，统一由分布式文件系统进行管理。一个数据库的数据可能存储在多个服务器上，系统内部通过事务机制和二阶段提交协议保证数据的强一致性和完整性，对于外部用户来说，这些机制是完全透明的。每个分区副本的数据采用列式增量压缩存储。压缩算法采用了LZ4方法，对金融数据平均能达到20%-25%的无损压缩比。

一个数据库最多可以支持三个维度的分区，支持百万甚至千万级的分区数。为尽可能保证每个分区的大小平衡，DolphinDB提供了值（VALUE）分区，范围（RANGE）分区，哈希（HASH）分区，列表（LIST）分区和复合（COMPO）分区等多种分区方式，用户可以灵活使用，合理规划分区。在查询时，加载数据的最小单位是一个分区的一个列。DolphinDB不提供行级的索引，而是将分区作为数据库的物理索引。一个分区字段相当于数据表的一个物理索引。如果查询时用到了该分区字段做数据过滤，SQL引擎就能快速定位需要的数据块，而无需对整表进行扫描。在量化金融领域，查询分析大多基于某一个时间段、某个产品标识进行，因此时间和产品标识是量化金融领域最常用的分区维度。有关分区的具体细节请参阅[分区数据库教程](./database.md)。

### 2.2 数据库设计

行情数据是量化金融中量级最大的数据类别。在中国证券市场，每日新增的数据在20-40G左右，累积的历史数据在20-40T左右。传统的关系型数据库处理这样的数据量级的性能非常低下。即使分库分表，效果也不理想。DolphinDB的分区机制可以轻松应对几百TB甚至PB级别的数据量。

为保证最佳性能，尽量将数据均匀分区，且将每个表的每个分区的数据量控制在压缩前100M左右。这是因为DolphinDB并不提供行级的索引，而是将分区作为数据库的物理索引，因此每个分区的数据量不宜过大。

行情数据通常可用时间和产品标识两个维度来进行分区：

(1) 时间维度大部分情况下可以选择按天进行值分区。如果时间跨度不是很长，而每天的数据量又非常大，也可以考虑按照小时进行分区，为此DolphinDB提供了DATEHOUR这种数据类型。设计分区机制时要考虑常用的应用场景。譬如说每次的请求都是对单一股票进行查询或聚合计算，而且跨越的时间比较长，可能几个月甚至一年，那么时间维度上按月分区不失为一种好的做法。

(2) 产品标识维度的分区可采用哈希、范围、值、列表等多种方法。如果每个产品在固定时间内的数据量比较均匀，可采用哈希或范围分区。例如中国的期货与股票市场以固定频率发布报价和交易的快照，因此每个市场内不同产品的数据量基本一致。美国金融市场的行情数据分布则完全不同，不同股票的tick级别数据量差异非常大。这种情境下，可选择范围分区，以一天或多天的数据为样本，将产品标识划分成多个范围，使得每一个范围内的产品的数据总量比较均衡。如果产品个数比较少，譬如期货的品种比较少，也可以考虑用值分区。

行情数据包括每日数据(end of day data)、Level 1、Level 2、Level 3等不同级别的数据。不同级别的数据，数据量差异比较大。所以建议采用不同分区机制的数据库来存储这些数据。

DolphinDB中的多个分区维度并不是层级关系，而是平级的组合关系。如果时间维度有n个分区，产品维度有m个分区，最多可能有n x m个分区。

K线数据或相关的signal数据都是基于高精度的行情数据降低时间精度产生的数据。通常，我们会生成不同频率的K线，譬如1分钟、5分钟、30分钟等等。这些不同频率的K线数据，因为数据量不是太大，建议存储在同一个分区表中，可以增加一个字段frequency来区分不同的时间窗口。K线表通常也按照日期和产品标识两个维度来分区，分区的粒度由数据量决定。以中国股票市场的分钟级K线为例，3000个股票每天产生约240个数据点，总共约72万个数据点。建议时间维度按月进行分区，产品的维度按范围或哈希分成15个分区。这样每个分区的数据量在100万行左右。这样的分区方法，既可在较长时间范围内（1个月或1年）快速查找某一个股票的数据，也可应对查找一天内全部股票的数据这样的任务。

### 2.3 建库建表脚本

遵循每个表每个分区中的常用数据压缩前为100MB左右的原则，可将数据库设计为复合分区，第一个维度按天（时间戳列）进行值分区，第二个维度按产品标识（证券代码列）分为40个HASH分区。

```
	dbDate = database("", VALUE, 2020.01.01..2020.01.03)
	dbSymbol=database("", HASH, [SYMBOL, 40])
	db = database(dbName, COMPO, [dbDate, dbSymbol])	
	
	columns = `Symbol`Market`DateTime`Status`PreClose`Open`High`Low`Price`Volume`Amount`AskPrice1`AskPrice2`AskPrice3`AskPrice4`AskPrice5`AskPrice6`AskPrice7`AskPrice8`AskPrice9`AskPrice10`BidPrice1`BidPrice2`BidPrice3`BidPrice4`BidPrice5`BidPrice6`BidPrice7`BidPrice8`BidPrice9`BidPrice10`AskVolume1`AskVolume2`AskVolume3`AskVolume4`AskVolume5`AskVolume6`AskVolume7`AskVolume8`AskVolume9`AskVolume10`BidVolume1`BidVolume2`BidVolume3`BidVolume4`BidVolume5`BidVolume6`BidVolume7`BidVolume8`BidVolume9`BidVolume10`TickCount`BidOrderTotalVolume`AskOrderTotalVolume`AvgBidOrderPrice`AvgAskOrderPrice`LimitHighestPrice`LimitLowestPrice
	type=[SYMBOL,SYMBOL,DATETIME,INT,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,INT,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,INT,INT,INT,INT,INT,INT,INT,INT,INT,INT,INT,INT,INT,INT,INT,INT,INT,INT,INT,INT,INT,INT,INT,DOUBLE,DOUBLE,DOUBLE,DOUBLE]
	orderData = table(1:0, columns,type)
	db.createPartitionedTable(orderData, tableName,`DateTime`Symbol)

```
建库脚本[下载](./script/csvImportDemo/createDB.txt)。

## 3. 新格式数据导入

导入脚本详见[importNewData](./script/csvImportDemo/importNewData.txt)。在脚本中，共定义了4个函数：`getSchema`，`loadOneFile`，`loadOneDayFiles`和`loopLoadOneYears`。

函数`getSchema`返回值为一个schema，用于指定导入CSV文件的schema。它先根据导入CSV文件自动判断其schema。修改TotalVolume（累计成交量）和TotalAmount（累计成交额）的列名为Volume和Amount。

函数`loadOneFile`加载一个文件到内存表并返回。其实现步骤如下：
* 加载一个csv文件的数据到内存表；
* 把内存表的Symbol列变成market(市场代码)和Symbol（证券代码）2列；
* 用[`eachPre`](https://www.dolphindb.cn/cn/help/Functionalprogramming/TemplateFunctions/eachPre.html)函数把TotalVolume（累计成交量）和TotalAmount（累计成交额）处理为成交量和成交额；

注意：下面2行代码都能把累计成交量变成成交量，但第一行即调用`eachPre`的方式效率较高，第二行在用`deltas`计算后，为了补第一个元素的空值，调用了`nullFill!`进行空值填充，效率较低。
```
	t["Volume"] = eachPre(-, t["volume"], 0)
	t["Volume"] = nullFill!(deltas(t["Volume"]),t["Volume"])
```

* 因为从csv加载并处理后的列顺序与分布式表不一致，所以最后用reorderColumns排成与分布式表一致。

函数`loadOneDayFiles`把一天的csv文件写入分布式表。其实现步骤如下：
* 先读取所有csv文件名，然后用`cut`函数分组，按每100个文件一组分成多组；
* 对每组文件，先定义一个容量为50万行的内存表bigTable，然后调用`loadOneFile`把100个文件分别加载并一一插入bigTable，最后把bigTable一批插入分布式表。

增大每批写入的数据量是提升导入性能的重要措施之一，但也不宜过大，一般几十MB比较合适。本案例每个CSV文件大小在60KB到2MB之间，平均约3-4千行记录，若每批写入一个文件，批量太小。在一台台式机上进行了比较测试，其配置为：win10操作系统，CPU为6 核 12 线程的Intel I7，内存32GB ，2TB 7200RPM HDD 。DolphinDB采用单节点部署，限制使用4G内存，4核CPU,其他都采用默认配置。测试结果为每批写入1个文件时，导入一天的数据需要约25分钟，每批写入100个文件约2分钟，写入性能差10余倍。

函数`loopLoadOneYears`输入年目录并把一年的数据并行导入分布式表。根据需求，源数据文件的目录结构为~/yyyy/yyyyMMdd/，这里输入~/yyyy，例如"/hdd/hdd9/data/quotes/2020"（这里2020表示2020年的数据）。函数获取年目录下的所有子目录，对每个子目录调用函数`loadOneDayFiles`并提交一个批处理作业，即每个任务导入一天的数据。使用多线程并行写入也能大幅提升导入性能。需要注意的是，这里提交了几百个批处理作业，但这些作业不一定会同时运行。在系统中，批处理作业工作线程数的上限是由配置参数maxBatchJobWorker设置的。如果批处理作业的数量超过了限制，新的批处理作业将会进入队列等待。批处理作业的具体介绍请参阅[作业管理](./job_management_tutorial.md#2-%E5%BC%82%E6%AD%A5%E4%BD%9C%E4%B8%9A)第2节。

## 4. 旧格式数据导入

导入脚本详见[importOldData](./script/csvImportDemo/importOldData.txt)。在脚本中，共定义了4个函数：`getSchema`，`loadOneFile`，`loadOneDayFiles`和`loopLoadOneYears`。函数功能与新格式数据的同名函数保持一致。其中`loadOneDayFiles`和`loopLoadOneYears`与新格式数据导入的`loadOneDayFiles`和`loopLoadOneYears`基本一致，区别主要在与`getSchema`和`loadOneFile`。`getSchema`的主要区别有：

* 旧格式数据的字段名为中文，编码为GB2312，因此用`extractTextSchema`函数得到的schema显示为乱码，需要用`convertEncode`函数转换为utf-8编码：
```
	update schema1 set name=convertEncode(name,"gbk","utf-8") 
```
* 旧格式数据中的“方向”这一列不需要导入分布式表，因此使用`rowNo`函数为各列生成列号，赋值给schema表中的col列，然后修改schema表，仅保留表示需要导入的字段的行。
```
	update schema1 set col = rowNo(name)
	delete from schema1 where name in [`方向]
```

`loadOneFile`的主要区别有：

* 旧格式数据有很多列的数据缺失，因此用`loadText`加载的内存表不能直接插入分布式表，因此预先用`addColumn`把这些列补上。
* 用`upper`把市场代码转换为大写。
* Volume*100以与新格式数据保持一致。







​	
​	




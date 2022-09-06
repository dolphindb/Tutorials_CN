# DolphinDB入门：量化金融范例

建议使用DolphinDB GUI编写DolphinDB脚本。请在DolphinDB官网下载[DolphinDB GUI](https://www.dolphindb.cn/downloads.html)。关于如何使用DolphinDB GUI，请参考[DolphinDB客户端教程](client_tool_tutorial.md)。

创建或访问分布式数据库和表需要用户权限。本教程使用默认用户名"admin"登录（默认密码是"123456"），后续例子中不再显示登录相关代码。DolphinDB与其他关系数据库、NoSQL、NewSQL数据库不同的是，数据库，编程语言和分布式计算三者融为一体。这种设计使得DolphinDB可以一站式轻量化的解决大数据问题。但是，引用数据库和表时，不能直接用数据库或表名称（因为与脚本中的变量名可能会冲突），必须使用`loadTable`函数加载数据表。下面的例子中，我们首先登录。然后加载数据库 dfs://futures 的一个表 quotes，并把这个表对象赋值给变量 quotes，之后就可以用变量 quotes 来访问这个数据表。
```
login("admin", "123456")
quotes = loadTable("dfs://futures", "quotes")
select count(*) from quotes
```

## 1. DolphinDB的存储机制

DolphinDB利用分布式文件系统实现数据库的存储和基本事务机制。数据库以分区（chunk）为单位进行管理。分区的元数据（元数据指数据库的分区信息，每个分区的版本链，大小，存储位置等）存储在控制节点，副本数据存储在各数据节点，统一由分布式文件系统进行管理。一个数据库的数据可能存储在多个服务器上，系统内部通过事务机制和二阶段提交协议保证数据的强一致性和完整性，对于外部用户来说，这些机制是完全透明的。每个分区副本的数据采用列式增量压缩存储。压缩算法采用了LZ4方法，对金融数据平均能达到20%-25%的无损压缩比。

一个数据库最多可以支持三个维度的分区，支持百万甚至千万级的分区数。为尽可能保证每个分区的大小平衡，DolphinDB提供了值（VALUE）分区，范围（RANGE）分区，哈希（HASH）分区，列表（LIST）分区和复合（COMPO）分区等多种分区方式，用户可以灵活使用，合理规划分区。在查询时，加载数据的最小单位是一个分区的一个列。DolphinDB不提供行级的索引，而是将分区作为数据库的物理索引。一个分区字段相当于数据表的一个物理索引。如果查询时用到了该分区字段做数据过滤，SQL引擎就能快速定位需要的数据块，而无需对整表进行扫描。在量化金融领域，查询分析大多基于某一个时间段、某个产品标识进行，因此时间和产品标识是量化金融领域最常用的分区维度。

下面展示一个期货tick实时行情数据库的存储目录和文件，其中数据库按照两个维度分区，第一个维度按天（tradingday列）进行值分区，第二个维度按照期货品种（instrument列）分为3个HASH分区,建库建表代码如下所示：

```
db1 = database("", VALUE, 2020.01.01..2020.12.31)
db2 = database("", HASH,[SYMBOL,3])
db = database("dfs://futures",COMPO, [db1,db2])
colNames=`instrument`tradingday`calendarday`time`lastp`volume`openinterest`turnover`ask1`asksz1`bid1`bidsz1
colTypes=[SYMBOL,DATE,DATE,TIME,DOUBLE,INT,DOUBLE,DOUBLE,DOUBLE,INT,DOUBLE,INT]
t=table(1:0,colNames,colTypes)
db.createPartitionedTable(t,`tick,`tradingday`instrument)
```
写入数据后，存储目录和数据文件如下所示，

```
[dolphindb@localhost futures]$ tree
.
├── 20200101
│   ├── Key0
│   │   ├── chunk.dict
│   │   └── tick
│   │       ├── ask1.col
│   │       ├── asksz1.col
│   │       ├── bid1.col
│   │       ├── bidsz1.col
│   │       ├── calendarday.col
│   │       ├── instrument.col
│   │       ├── lastp.col
│   │       ├── openinterest.col
│   │       ├── time.col
│   │       ├── tradingday.col
│   │       ├── turnover.col
│   │       └── volume.col
│   ├── Key1
│   │   ├── chunk.dict
│   │   └── tick
│   │       ├── ask1.col
│   │       ├── asksz1.col
│   │       ├── bid1.col
│   │       ├── bidsz1.col
│   │       ├── calendarday.col
│   │       ├── instrument.col
│   │       ├── lastp.col
│   │       ├── openinterest.col
│   │       ├── time.col
│   │       ├── tradingday.col
│   │       ├── turnover.col
│   │       └── volume.col
│   └── Key2
│       ├── chunk.dict
│       └── tick
│           ├── ask1.col
│           ├── asksz1.col
│           ├── bid1.col
│           ├── bidsz1.col
│           ├── calendarday.col
│           ├── instrument.col
│           ├── lastp.col
│           ├── openinterest.col
│           ├── time.col
│           ├── tradingday.col
│           ├── turnover.col
│           └── volume.col
├── 20200102
│   ├── Key0
...
├── dolphindb.lock
├── domain
└── tick.tbl

```
从中可以看到，一个分区维度对应一层子目录，譬如按天分区的子目录名是20200101，20200102等，按期货品种HASH分区的子目录名是Key0，Key1等，表中每一列保存为一个后缀名为col的文件，如ask1.col，bid1.col等。



## 2. 行情数据和K线数据的数据库设计

行情数据是量化金融中量级最大的数据类别。在中国证券市场，每日新增的数据在20-40G左右，累积的历史数据在20-40T左右。传统的关系型数据库处理这样的数据量级的性能非常低下。即使分库分表，效果也不理想。DolphinDB的分区机制可以轻松应对几百TB甚至PB级别的数据量。

为保证最佳性能，尽量将数据均匀分区，且将每个表的每个分区的数据量控制在压缩前100M左右。这是因为DolphinDB并不提供行级的索引，而是将分区作为数据库的物理索引，因此每个分区的数据量不宜过大。

行情数据通常可用时间和产品标识两个维度来进行分区：

(1) 时间维度大部分情况下可以选择按天进行值分区。如果时间跨度不是很长，而每天的数据量又非常大，也可以考虑按照小时进行分区，为此DolphinDB提供了DATEHOUR这种数据类型。设计分区机制时要考虑常用的应用场景。譬如说每次的请求都是对单一股票进行查询或聚合计算，而且跨越的时间比较长，可能几个月甚至一年，那么时间维度上按月分区不失为一种好的做法。

(2) 产品标识维度的分区可采用哈希、范围、值、列表等多种方法。如果每个产品在固定时间内的数据量比较均匀，可采用哈希或范围分区。例如中国的期货与股票市场以固定频率发布报价和交易的快照，因此每个市场内不同产品的数据量基本一致。美国金融市场的行情数据分布则完全不同，不同股票的tick级别数据量差异非常大。这种情境下，可选择范围分区，以一天或多天的数据为样本，将产品标识划分成多个范围，使得每一个范围内的产品的数据总量比较均衡。如果产品个数比较少，譬如期货的品种比较少，也可以考虑用值分区。

行情数据包括每日数据(end of day data)、Level 1、Level 2、Level 3等不同级别的数据。不同级别的数据，数据量差异比较大。所以建议采用不同分区机制的数据库来存储这些数据。

DolphinDB中的多个分区维度并不是层级关系，而是平级的组合关系。如果时间维度有n个分区，产品维度有m个分区，最多可能有n x m个分区。


K线数据或相关的signal数据都是基于高精度的行情数据降低时间精度产生的数据。通常，我们会生成不同频率的K线，譬如1分钟、5分钟、30分钟等等。这些不同频率的K线数据，因为数据量不是太大，建议存储在同一个分区表中，可以增加一个字段frequency来区分不同的时间窗口。K线表通常也按照日期和产品标识两个维度来分区，分区的粒度由数据量决定。以中国股票市场的分钟级K线为例，3000个股票每天产生约240个数据点，总共约72万个数据点。建议时间维度按月进行分区，产品的维度按范围或哈希分成15个分区。这样每个分区的数据量在100万行左右。这样的分区方法，既可在较长时间范围内（1个月或1年）快速查找某一个股票的数据，也可应对查找一天内全部股票的数据这样的任务。

## 3. 导入历史数据

### 3.1 从文本文件导入

中国股票市场每3秒更新一条 level 2 的行情数据，一般包括股票代码、日期、时间、交易量、交易价格、交易次数、买方与卖方的10档报价与量等常用信息，以及其它信息等数据。本例中所用数据为上海证券交易所A股股票2020年6月的 level 2 数据，每天的数据是一个约2.5GB的CSV文件，共68列数据。所有数据文件均存于同一个文件夹下。若其中一半的列为常用数据，遵循每个表每个分区中的常用数据压缩前为100MB左右的原则，可将数据库设计为复合分区。按天（date列）进行值分区，并按照股票代码（symbol列）分为10个HASH分区。

建库以及导入数据的脚本如下。使用[`loadTextEx`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/l/loadTextEx.html)导入分布式数据库，其详情请参阅[文本数据加载教程](./import_csv.md)。若您已有高频数据，可使用以下脚本建库，但请注意数据中列名与本例中列名一致。若您尚无高频数据，请见3.3节。
```
dbDate = database("", VALUE, 2020.01.01..2020.12.31)
dbSymbol=database("", HASH, [SYMBOL, 10])
db = database("dfs://level2", COMPO, [dbDate, dbSymbol])

//请注意更换目录dataDir
dataDir="/hdd/hdd1/data/Level2TextFiles/"

def importTxtFiles(dataDir, db){
    dataFiles = exec filename from files(dataDir) where isDir=false
    for(f in dataFiles){
        loadTextEx(db, `quotes, `date`symbol, dataDir + f)
    }
}
importTxtFiles(dataDir, db);
```

选择合适的数据库分区机制，对确保数据库最优性能非常重要。具体细节请参阅[分区数据库教程](database.md)。

### 3.2 从二进制文件导入

本例中导入的数据是上海证券交易所A股股票2020年6月1日的 level 2 数据。与csv导入时能自动生成分布式表的shema不同，二进制导入前需要显式定义分布式表，具体建库建表的脚本如下：
```
login("admin", "123456")
dbDate = database("", VALUE, 2020.01.01..2020.12.31)
dbSymbol=database("", HASH, [SYMBOL, 10])
db = database("dfs://level2", COMPO, [dbDate, dbSymbol])
schemaTable=table(	
	array(SYMBOL,0) as  symbol,
	array(SYMBOL,0) as  market,
	array(DATE,0) as  date,
	array(TIME,0) as  time,
	array(DOUBLE,0) as  preClose,
	array(DOUBLE,0) as  open,
	array(DOUBLE,0) as  high,
	array(DOUBLE,0) as  low,
	array(DOUBLE,0) as  last,
	array(INT,0) as  numTrades,
	array(INT,0) as  curNumTrades,
	array(INT,0) as  volume,
	array(INT,0) as  curVol,
	array(DOUBLE,0) as  turnover,
	array(INT,0) as  curTurnover,
	array(INT,0) as  peratio1,
	array(INT,0) as  peratio2,
	array(INT,0) as  totalAskVolume,
	array(DOUBLE,0) as  wavgAskPrice,
	array(INT,0) as  askLevel,
	array(INT,0) as  totalBidVolume,
	array(DOUBLE,0) as  wavgBidPrice,
	array(INT,0) as  bidLevel,
	array(DOUBLE,0) as  iopv,
	array(INT,0) as  ytm,
	array(DOUBLE,0) as  askPrice1,
	array(DOUBLE,0) as  askPrice2,
	array(DOUBLE,0) as  askPrice3,
	array(DOUBLE,0) as  askPrice4,
	array(DOUBLE,0) as  askPrice5,
	array(DOUBLE,0) as  askPrice6,
	array(DOUBLE,0) as  askPrice7,
	array(DOUBLE,0) as  askPrice8,
	array(DOUBLE,0) as  askPrice9,
	array(DOUBLE,0) as  askPrice10,
	array(DOUBLE,0) as  bidPrice1,
	array(DOUBLE,0) as  bidPrice2,
	array(DOUBLE,0) as  bidPrice3,
	array(DOUBLE,0) as  bidPrice4,
	array(DOUBLE,0) as  bidPrice5,
	array(DOUBLE,0) as  bidPrice6,
	array(DOUBLE,0) as  bidPrice7,
	array(DOUBLE,0) as  bidPrice8,
	array(DOUBLE,0) as  bidPrice9,
	array(DOUBLE,0) as  bidPrice10,
	array(INT,0) as  askVolume1,
	array(INT,0) as  askVolume2,
	array(INT,0) as  askVolume3,
	array(INT,0) as  askVolume4,
	array(INT,0) as  askVolume5,
	array(INT,0) as  askVolume6,
	array(INT,0) as  askVolume7,
	array(INT,0) as  askVolume8,
	array(INT,0) as  askVolume9,
	array(INT,0) as  askVolme10,
	array(INT,0) as  bidVolume1,
	array(INT,0) as  bidVolume2,
	array(INT,0) as  bidVolume3,
	array(INT,0) as  bidVolume4,
	array(INT,0) as  bidVolume5,
	array(INT,0) as  bidVolume6,
	array(INT,0) as  bidVolume7,
	array(INT,0) as  bidVolume8,
	array(INT,0) as  bidVolume9,
	array(INT,0) as  bidVolume10,
	array(LONG,0) as  unixTime,
	array(DOUBLE,0) as  upperLimit,
	array(DOUBLE,0) as  lowerLimit
)
db.createPartitionedTable(schemaTable,`quotes,`date`symbol)

```
对于二进制格式的文件，DolphinDB提供了2个函数用于导入：[`readRecord!`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/r/readRecord!.html)函数和[`loadRecord`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/l/loadRecord.html)函数。二者的区别是，前者不支持导入字符串类型的数据，后者支持。在二进制文件中，date列和time列的数据以数值形式存储，可以使用[`temporalParse`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/t/temporalParse.html)函数进行日期和时间类型数据的格式转换。再使用[`replaceColumn!`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/r/replaceColumn!.html)函数替换表中原有的列。symbol和market列在二进制文件中也是数值形式存储，处理的方式类似。具体代码如下所示：
```
schema = [
("symbol", INT), ("market", INT), ("date", INT), ("time", INT), ("preClose", DOUBLE),
("open", DOUBLE), ("high", DOUBLE), ("low", DOUBLE), ("last", DOUBLE), ("numTrades", INT),
("curNumTrades", INT), ("volume", INT), ("curVol", INT), ("turnover", DOUBLE), ("curTurnover", INT),
("peratio1", INT), ("peratio2", INT), ("totalAskVolume", INT), ("wavgAskPrice", DOUBLE), ("askLevel", INT),
("totalBidVolume", INT), ("wavgBidPrice", DOUBLE), ("bidLevel", INT), ("iopv", DOUBLE), ("ytm", INT),
("askPrice1", DOUBLE), ("askPrice2", DOUBLE), ("askPrice3", DOUBLE), ("askPrice4", DOUBLE), ("askPrice5", DOUBLE),
("askPrice6", DOUBLE), ("askPrice7", DOUBLE), ("askPrice8", DOUBLE), ("askPrice9", DOUBLE), ("askPrice10", DOUBLE),
("bidPrice1", DOUBLE), ("bidPrice2", DOUBLE), ("bidPrice3", DOUBLE), ("bidPrice4", DOUBLE), ("bidPrice5", DOUBLE),
("bidPrice6", DOUBLE), ("bidPrice7", DOUBLE), ("bidPrice8", DOUBLE), ("bidPrice9", DOUBLE), ("bidPrice10", DOUBLE),
("askVolume1", INT), ("askVolume2", INT), ("askVolume3", INT), ("askVolume4", INT), ("askVolume5", INT),
("askVolume6", INT), ("askVolume7", INT), ("askVolume8", INT), ("askVolume9", INT), ("askVolme10", INT),
("bidVolume1", INT), ("bidVolume2", INT), ("bidVolume3", INT), ("bidVolume4", INT), ("bidVolume5", INT),
("bidVolume6", INT), ("bidVolume7", INT), ("bidVolume8", INT), ("bidVolume9", INT),("bidVolume10", INT),
("unixTime", LONG), ("upperLimit", DOUBLE), ("lowerLimit", DOUBLE) ]

dataDir="/hdd/hdd1/data/Level2BinFiles/"

def importBinFiles(dataDir, schema){
    tick1 = loadTable("dfs://level2","quotes")
    dataFiles = exec filename from files(dataDir)
    for(f in dataFiles){
        t=loadRecord(dataDir + f, schema)
        t.replaceColumn!(`date, t.date.string().datetimeParse("yyyyMMdd"))
        t.replaceColumn!(`time, t.time.format("000000000").datetimeParse("HHmmssSSS"))
        t.replaceColumn!(`symbol, t.symbol.format("000000"))
        t.replaceColumn!(`market, iif(t.market==0,"SH","SZ"))
        tick1.append!(t)
    }
}
importBinFiles(dataDir, schema);
```

### 3.3 生成模拟数据

若您尚无高频数据，可下载[20200601.csv](http://www.dolphindb.cn/downloads/tutorial/20200601.zip)（或[20200601.bin](http://www.dolphindb.cn/downloads/tutorial/20200601_bin.zip)），采用3.1节（或3.2节）中的脚本，将这天数据载入数据库，然后通过修改日期，生成多天的高频数据以供测试。

下列代码通过[`sqlDS`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/s/sqlDS.html)函数将之前导入的2020.06.01这一天的数据，按分布式表一个分区生成一个数据源的方式，共分成10个数据源，然后通过[`mr`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/m/mr.html)函数将这10份数据先取到内存更新日期，再写入数据库。`mr`函数的parallel参数可设为true，即采用并行执行，以加块生成模拟数据的速度。若服务器内存不足容纳一天的数据，则需要设为false，即采用串行执行以尽量少占用内存。

```
def writeData(mutable t,dbName,tableName, days){
	pt = loadTable(dbName,tableName)
	for(day in days){
		update t set date = day
		pt.append!(t)		
	}
}
def main(dbName,tableName,days){
	rds = sqlDS(<select * from loadTable(dbName,tableName) where date=2020.06.01>)
	mr(ds=rds, mapFunc=writeData{,dbName,tableName,days}, parallel=true)
}
login(`admin,`123456)
days=2020.06.01..2020.06.30
days=days[weekday(days) between 1:5]
main("dfs://level2","quotes",days)
```

## 4. 基于历史数据库的量化计算

本章节所用数据均为第3章中所建之quotes表。

### 4.1 常用的SQL处理

将quotes表元数据载入内存：
```
db = database("dfs://level2")
quotes = loadTable(db, `quotes);
```

计算某只股票某天中，每分钟内的平均价差(bid-ask spread)，并将结果在GUI以图形展示：
```
avgSpread = select max((askPrice1-bidPrice1)/(askPrice1+bidPrice1)*2) as avgSpread from quotes where date=2020.06.01, symbol=`600600, time between 09:30:00.000 : 15:00:00.000, askPrice1>=bidPrice1 group by minute(time) as minute
plot(avgSpread.avgSpread, avgSpread.minute, "Average bid-ask spread per minute")
```

### 4.2 使用context by子句处理面板数据(panel data)

context by是DolphinDB独有的功能，是对标准SQL语句的拓展。使用context by子句可以简化对面板数据的操作。

context by与group by类似，都对数据进行分组。但是，用group by时，每一组返回一个标量值，而用context by时，每一组返回一个和组内元素数量相同的向量。group by只能配合聚合函数使用，而context by既可以配合聚合函数使用，也可以与移动窗口函数或累积函数等其它函数结合使用。

计算每只股票在2020.06.01中截止到当前时刻的每次数据更新（绝大部分情况下为3秒）中最大交易量：
```
t = select symbol, date, time, cummax(curVol) as volume_cummax from quotes where date=2020.06.01 context by symbol, date
```
context by子句亦可结合滑动窗口函数使用。下例计算每只股票在2020.06.01中过去20次数据更新中的平均价格（约为过去一分钟的平均价格）：
```
t = select symbol, date, time, mavg(last, 20) as price_mavg1min from quotes where date=2020.06.01 context by symbol, date
```
context by子句还可结合聚合函数使用，将聚合函数的分组计算结果赋予组内每一行：
```
t = select symbol, date, time, max(curVol) as volume_dailyMax from quotes where date=2020.06.01 context by symbol, date
```

使用某天数据，计算高频因子：
```
t=select symbol, date, time, (2*bidVolume1+bidVolume2-2*askVolume1-askVolume2)\(2*bidVolume1+bidVolume2+2*askVolume1+askVolume2) as factor1, (2*bidVolume1+bidVolume2-2*askVolume1-askVolume2)\mavg((2*bidVolume1+bidVolume2+2*askVolume1+askVolume2),100) as factor2 from quotes where date=2020.06.01, symbol>=`600000, time between 09:30:00.000 : 15:00:00.000 context by symbol order by symbol, date, time
```

移动窗口函数可嵌套使用。下例中，首先分别计算第一档买量与卖量100次数据更新（约为5分钟）的移动平均，再计算两者60次数据更新（约为3分钟）的移动相关性。仅用一行代码即可完成。
```
t=select symbol, date, time, mcorr(mavg(bidVolume1,100), mavg(askVolume1,100), 60) from quotes where date=2020.06.01, symbol>=`600000, time between 09:30:00.000 : 15:00:00.000 context by symbol order by symbol, date, time
```

### 4.3 pivot子句的应用

pivot by是DolphinDB的独有功能，是对标准SQL语句的拓展。它将表中某列的内容按照两个维度重新排列，亦可配合数据转换函数使用。

下例中的投资组合的股票代码为向量syms，其中各股票的持仓数量分别为100, 200, 400, 800, 600, 400, 300。本例的目标是计算某天中每个时刻的投资组合价值。请注意，两行DolphinDB代码即可实现目标，但为了读者理解方便，这里分为三步逐步介绍如何实现。

首先对数据使用pivot by子句进行重新排列：
```
db = database("dfs://level2")
quotes = loadTable(db, `quotes)
syms = `600000`600300`600400`600500`600600`600800`600900

pv = select last from quotes where date=2020.06.01, symbol in syms, time between 09:30:00.000 : 15:00:00.000 pivot by time, symbol
select top 10 * from pv;
```
结果为：
```
time         C600000 C600300 C600400 C600500 C600600 C600800 C600900
------------ ------- ------- ------- ------- ------- ------- -------
09:30:00.000 10.63   3.09    3.28    5.03    63.5    4.68    17.43
09:30:03.000 10.62   3.08    3.28    5.03    63.5    4.68    17.4
09:30:05.000 10.61                                   4.68    17.41
09:30:06.000         3.08    3.28    5.02    63.51
09:30:08.000 10.62                                   4.68    17.41
09:30:09.000         3.07    3.28    5.03    63.74
09:30:11.000 10.63                                   4.68    17.42
09:30:12.000         3.07    3.27    5.03    63.95
09:30:14.000 10.64                                   4.68    17.43
09:30:15.000         3.06            5.03    63.95
```

可见并不是所有股票均在同一时刻更新数据。若要计算每个时刻的投资组合价值，首先应在以上结果中使用`ffill`函数向前填充last列的空值：
```
tmp = select ffill(last) from quotes where date=2020.06.01, symbol in syms, time between 09:30:00.000 : 15:00:00.000 pivot by time, symbol
select top 10 * from tmp;
```
结果为：
```
time         C600000 C600300 C600400 C600500 C600600 C600800 C600900
------------ ------- ------- ------- ------- ------- ------- -------
09:30:00.000 10.63   3.09    3.28    5.03    63.5    4.68    17.43
09:30:03.000 10.62   3.08    3.28    5.03    63.5    4.68    17.4
09:30:05.000 10.61   3.08    3.28    5.03    63.5    4.68    17.41
09:30:06.000 10.61   3.08    3.28    5.02    63.51   4.68    17.41
09:30:08.000 10.62   3.08    3.28    5.02    63.51   4.68    17.41
09:30:09.000 10.62   3.07    3.28    5.03    63.74   4.68    17.41
09:30:11.000 10.63   3.07    3.28    5.03    63.74   4.68    17.42
09:30:12.000 10.63   3.07    3.27    5.03    63.95   4.68    17.42
09:30:14.000 10.64   3.07    3.27    5.03    63.95   4.68    17.43
09:30:15.000 10.64   3.06    3.27    5.03    63.95   4.68    17.43
```
最后计算每一时刻的投资组合价值：
```
select time, 100*C600000+200*C600300+400*C600400+800*C600500+600*C600600+400*C600800+300*C600900 from tmp;
```

### 4.4 生成分钟级数据

计算某天分钟级K线：
```
minuteBar = select first(last) as open, max(last) as high, min(last) as low, last(last) as last, sum(curVol) as volume from quotes where date=2020.06.01, symbol>=`600000 group by symbol, date, minute(time) as minute;
```

以上为仅计算一天数据的K线。若需使用全部数据计算分钟级K线，并将结果存入数据库，由于全部数据有可能超过内存，同时为了充分利用系统硬件资源进行并行计算，可使用MapReduce函数`mr`。
```
model=select top 1 symbol,date, minute(time) as minute, open, high, low, last, curVol as volume from quotes where date=2020.06.01,symbol=`600000
if(existsTable("dfs://level2", "minuteBar"))
	db.dropTable("minuteBar")
db.createPartitionedTable(model, "minuteBar", `date`symbol)

def saveMinuteBar(t){
	minuteBar=select first(last) as open, max(last) as high, min(last) as low, last(last) as last, sum(curVol) as volume from t where symbol>=`600000, time between 09:30:00.000 : 15:00:00.000 group by symbol, date, minute(time) as minute
	loadTable("dfs://level2", "minuteBar").append!(minuteBar)
	return minuteBar.size()
}

ds = sqlDS(<select symbol, date, time, last, curVol from quotes>)
mr(ds,saveMinuteBar,+)
```
有关K线计算的更多场景及范例，例如指定K线窗口的起始时刻、重叠K线窗口、使用交易量划分K线窗口等等，请参考[K线计算教程](OHLC.md)。

### 4.5 asof join 及 window join

DolphinDB提供性能极佳的非同时连接函数`aj`及`wj`。函数`aj`(asof join)为左表中每条记录，在右表中获取符合指定条件的组中该时刻之前（包括该时刻）的最后一条记录；函数`wj`(window join)为左表中每条记录，在右表中获取符合指定条件的组基于该时刻的指定时间范围的记录并进行计算。DolphinDB的asof join比pandas中的asof join速度快约200倍。

Asof join 在国际证券市场的最典型应用场景为，报价与交易信息处于不同的数据表中，使用asof join可以高效的寻找每一笔交易之前的最近一笔报价。在国内证券市场，asof join 亦有许多应用场景。

每天交易结束后，若要将交易价格与交易前的最新报价进行对比，可将交易记录与报价记录进行asof join。如下所示：
```
trades=table(`600000`600300`600800 as symbol, take(2020.06.01,3) as date, [14:35:18.000, 14:30:30.000, 14:31:09.000] as time, [10.63, 3.12, 4.72] as tradePrice)
quotesTmp=select symbol, date, time, bidPrice1, askPrice1 from quotes where symbol in `600000`600300`600800 and date=2020.06.01
select * from aj(trades, quotesTmp, `symbol`date`time)
```
结果为：
```
symbol date       time         tradePrice quotesTmp_time bidPrice1 askPrice1
------ ---------- ------------ ---------- -------------- --------- ---------
600000 2020.06.01 14:35:18.000 10.63      14:35:17.000   10.62     10.63
600300 2020.06.01 14:30:30.000 3.12       14:30:29.000   3.12      3.13
600800 2020.06.01 14:31:09.000 4.72       14:31:09.000   4.72      4.73
```
从4.3节中，可见不同的股票行情数据更新的时刻可能不同。若要为某只股票每一个数据更新的时刻，提供另外一只股票在此时刻的最新报价数据，可使用asof join。
```
t1 = select symbol, date, time, askPrice1, bidPrice1 from quotes where date=2020.06.01, symbol=`600000, time between 09:30:00.000 : 15:00:00.000 
C600300 = select date, time, askPrice1, bidPrice1 from quotes where date=2020.06.01, symbol=`600300, time between 09:30:00.000 : 15:00:00.000 
t = aj(t1, C600300, `date`time)
```

若要对某天中所有记录，计算之前一分钟之内的总交易量，可使用window join。以下脚本中，假设只保留原表中的symbol, date, time, curVol, askPrice1, bidPrice1这几列。
```
t=select symbol, date, time, curVol, askPrice1, bidPrice1 from quotes where date=2020.06.01, symbol>=`600000, time between 09:30:00.000 : 15:00:00.000 order by symbol, date, time
t1 = wj(t, t, -60000:-1, <sum(curVol) as sumVolumePrev1m>, `symbol`date`time)
```
若要对某天中所有记录，寻找一分钟之后第一笔第一档报价，可使用以下脚本。假设只保留原表中的symbol, date, time, askPrice1, bidPrice1这几列。
```
t=select symbol, date, time, askPrice1, bidPrice1 from quotes where date=2020.06.01, symbol>=`600000, time between 09:30:00.000 : 15:00:00.000 order by symbol, date, time
t1 = wj(t, t, 60000:70000, <[first(askPrice1) as firstAskPrice1In1m, first(bidPrice1) as firstBidPrice1In1m]>, `symbol`date`time)
```

### 4.6 高阶函数

高阶函数与其它函数的不同之处在于，高阶函数的变量之一为一个函数。输入的数据被分解成多个数据块（可能重叠），然后将函数应用于每个数据块，最后将所有的结果组合为一个对象返回。某些复杂的分析任务如果使用高阶函数，可大大减少代码量。

以下代码计算2020年6月1日交易量最大的100只股票的分钟级收益率的两两相关性。
```
minuteBar = select first(last) as open, max(last) as high, min(last) as low, last(last) as last, sum(curVol) as volume from quotes where date=2020.06.01, symbol>=`600000 group by symbol, date, minute(time) as minute;
syms = (exec sum(volume) from minuteBar group by symbol order by sum_volume desc).symbol[0:100]
priceMatrix = exec last from minuteBar where symbol in syms pivot by minute, symbol
retMatrix = each(def(x):ratios(x)-1, priceMatrix)
corrMatrix = pcross(corr, retMatrix);
```
首先计算分钟级K线，然后获取交易量最大的100只股票。将分钟级K线数据整理为每分钟价格矩阵（priceMatrix），其中每列为一只股票，每行为一分钟。然后对价格矩阵使用高阶函数`each`，对每列应用函数ratios(x)-1，将价格矩阵转化为收益率矩阵（retMatrix）。最后对收益率矩阵使用高阶函数`pcross`，对其每两列应用函数`corr`以计算其两两相关性。最终结果为100*100的相关性矩阵（corrMatrix）。

有关其它高阶函数以及更多细节，请参考用户手册中的[高阶函数](https://www.dolphindb.cn/cn/help/Functionalprogramming/TemplateFunctions/index.html)。

### 4.7 使用API读写数据

DolphinDB提供Python, C++, Java, C#, Go, JavaScript, Excel等常用系统的API。

Python是目前最流行的数据分析语言，pandas是Python在金融行业最常用的库。本小节讲述如何使用python API 写入分布式数据库以及从DolphinDB数据库中读取数据。

* 使用Python API将数据写入分布式数据库

```python
import dolphindb as ddb
import dolphindb.settings as keys
import pandas as pd
import numpy as np
dbPath = "dfs://level2API"
tableName = "quotes"
s = ddb.session()
s.connect("127.0.0.1",8848,"admin","123456")

if(s.existsDatabase(dbPath)):
    s.dropDatabase(dbPath)
s.database('dbDate',partitionType=keys.VALUE,partitions="2020.01.01..2020.12.31")
s.database('dbSymbol',partitionType=keys.HASH,partitions="[SYMBOL,10]")
s.database('db', partitionType=keys.COMPO, partitions="[dbDate, dbSymbol]", dbPath=dbPath)

data=pd.DataFrame({"symbol":['600007','600104'],"dt":[np.datetime64('2020-01-01T20:01:01'),np.datetime64('2020-01-01T20:01:02')],"last":[100.36,99.3],"askPrice1":[100.36,101.22], "bidPrice1":[100.35,100.45],"askVolume1":[4138,2],"bidVolume1":[20,39],"volume":[1,5]})
s.run("db.createPartitionedTable(table(1:0, `symbol`datetime`last`askPrice1`bidPrice1`askVolume1`bidVolume1`volume, [SYMBOL,DATETIME,DOUBLE,DOUBLE,DOUBLE,INT,INT,INT]),`quotes, `datetime`symbol)")
s.upload({"tmpdata":data})
s.run("data=select symbol, datetime(dt) as datetime, last, askPrice1, bidPrice1, askVolume1, bidVolume1, volume from tmpdata")
s.run("tableInsert(loadTable('{db}','{tb}'),data)".format(db=dbPath,tb=tableName))
```

* 使用Python API将从分布式数据库中读取数据

```python
import dolphindb as ddb
import pandas as pd
dbPath = "dfs://level2API"
tableName = "quotes"
s = ddb.session()
s.connect("127.0.0.1",8848,"admin","123456")
t = s.run("select * from loadTable('{db}','{tb}') where symbol=`600007".format(db=dbPath,tb=tableName))
print(t)
```
* orca 是基于Python API的完全实现pandas接口的库，下面的例子展示在 orca 中如何查询数据：

```python
import dolphindb.orca as orca
orca.connect("127.0.0.1", 8848, "admin", "123456")
odf = orca.read_table("dfs://level2API", "quotes")
t = odf[(odf["bidVolume1"]>5*odf["askVolume1"]) & (odf["askVolume1"]>1000000)].compute()
print(t)
```

更多信息与范例，请参考 [Python API教程](https://github.com/dolphindb/api_python3) 与 [orca教程](https://github.com/dolphindb/Orca/tree/master/tutorial_cn)。

## 5. 实时行情处理

实时的行情处理过程，首先是在DolphinDB中建立一个流数据表（level2），从API接收实时行情数据，然后通过订阅(subscribeTable)流数据表，将实时数据应用于K线计算、因子计算、实时截面数据更新、分布式表存储等场景中。

### 5.1 将数据写入流表

* DolphinDB中建立流数据表。以下为DolphinDB脚本：
```
share streamTable(100:0, `symbol`datetime`last`askPrice1`bidPrice1`askVolume1`bidVolume1`volume, [SYMBOL,DATETIME,DOUBLE,DOUBLE,DOUBLE,INT,INT,INT]) as level2
```

* 使用API将实时数据写入DolphinDB流数据表

在实际使用环境中，通常是先通过程序从数据提供商订阅实时数据，然后通过API写入到DolphinDB。本例使用Python API来展示这一过程，实际使用中用实时数据代替示例中的data变量。以下为Python代码。

```python
import dolphindb as ddb
import pandas as pd
import numpy as np
data = [['600007','600104'],[np.datetime64('2019-01-01T20:01:01'),np.datetime64('2019-01-01T20:01:02')],[100.36,99.3],[100.36,101.22], [100.35,100.45],[4138,2],[20,39],[1,5]]
s = ddb.session()
s.connect("127.0.0.1",8848,"admin","123456")
s.run("tableInsert{level2}",data)
```

* 使用数据回放功能将历史数据以指定速率写入流表

使用`replay`函数，可将历史数据以一定的速率注入到流数据表中，实现数据回放。结合流数据处理引擎或自定义函数使用，可实现基于历史数据的高频策略回测。具体回放函数的使用可参考[数据回放教程](historical_data_replay.md)。

在本例中的后续示例中，会使用历史数据回放来代替实时数据。即使在未实现三方数据源接口的情况下，也可以快速体验DolphinDB实时数据处理的功能。

在使用回放功能之前，首先需要准备好供回放的历史数据，本例中利用3.1导入的历史数据来生成回放的分布式表。
```
dbDate = database("", VALUE, 2020.01.01..2020.12.31)
dbSymbol=database("", HASH, [SYMBOL, 10])
db = database("dfs://level2Replay", COMPO, [dbDate, dbSymbol])
modal = table(1:0, `symbol`datetime`last`askPrice1`bidPrice1`askVolume1`bidVolume1`volume, [SYMBOL,DATETIME,DOUBLE,DOUBLE,DOUBLE,INT,INT,INT])
db.createPartitionedTable(modal,`quotes, `datetime`symbol)
data = select symbol, datetime(datetime(date(date))+second(time)) as datetime, last, askPrice1, bidPrice1, askVolume1, bidVolume1, curVol as volume from loadTable("dfs://level2","quotes")
loadTable("dfs://level2Replay","quotes").append!(data)
```

使用以下脚本，可以以10倍的速率将已保存到分布式表的报价数据回放到level2流数据表中：
```
quotes = loadTable("dfs://level2Replay","quotes")

//设置每次提取到内存数据量=1小时
repartitionSchema = time(cutPoints(08:00:00..18:00:00,10))
inputDS = replayDS(<select * from quotes>, `datetime, `datetime,  repartitionSchema)
submitJob("replay_quotes", "replay_quotes_stream",  replay,  [inputDS],  [`level2], `datetime, `datetime, 10, false, 2)
```

当回放函数被提交后，它在后台运行，可以通过`getRecentJobs()`函数查看已经提交的回放任务情况，通过`cancelJob(jobid)`取消回放任务。

[本示例脚本下载](script/quant5_1.dos)

### 5.2 用流计算生成K线

本小节介绍如何使用流数据时序聚合引擎`createTimeSeriesAggregator`函数实时计算K线。

时间窗口不重合，可将`createTimeSeriesAggregator`函数的windowSize参数和step参数设置为相同值。时间窗口部分重合，可将windowSize参数设为大于step参数。请注意，windowSize必须是step的整数倍。

场景一：每隔5分钟计算过去5分钟的K线数据
```
modal = table(100:0, `symbol`datetime`last`askPrice1`bidPrice1`askVolume1`bidVolume1`volume, [SYMBOL,DATETIME,DOUBLE,DOUBLE,DOUBLE,INT,INT,INT])
share streamTable(100:0, `datetime`symbol`open`high`low`close`volume,[DATETIME,SYMBOL,DOUBLE,DOUBLE,DOUBLE,DOUBLE,LONG]) as OHLC1
tsAggr1 = createTimeSeriesAggregator(name="tsAggr1", windowSize=300, step=300, metrics=<[first(last),max(last),min(last),last(last),sum(volume)]>, dummyTable=modal, outputTable=OHLC1, timeColumn=`datetime, keyColumn=`symbol)
subscribeTable(tableName="level2", actionName="act_tsAggr1", offset=0, handler=append!{tsAggr1}, msgAsTable=true);
```

场景二：每隔1分钟计算过去5分钟的K线数据
```
modal = table(100:0, `symbol`datetime`last`askPrice1`bidPrice1`askVolume1`bidVolume1`volume, [SYMBOL,DATETIME,DOUBLE,DOUBLE,DOUBLE,INT,INT,INT])
share streamTable(100:0, `datetime`symbol`open`high`low`close`volume,[DATETIME,SYMBOL,DOUBLE,DOUBLE,DOUBLE,DOUBLE,LONG]) as OHLC2
tsAggr2 = createTimeSeriesAggregator(name="tsAggr2", windowSize=300, step=60, metrics=<[first(last),max(last),min(last),last(last),sum(volume)]>, dummyTable=modal, outputTable=OHLC2, timeColumn=`datetime, keyColumn=`symbol)
subscribeTable(tableName="level2", actionName="act_tsAggr2", offset=0, handler=append!{tsAggr2}, msgAsTable=true);
```

[本示例脚本下载](script/quant5_2.dos)

### 5.3 用流计算生成实时高频因子

除了流数据聚合引擎，用户亦可使用自定义函数进行更复杂的实时计算。下面的例子是将实时数据与历史数据结合来计算因子。

本例中计算的因子定义为：前100笔记录与前200笔记录的资金净流入（net_amount）之比。计算流程为：订阅level2实时数据，调用因子计算函数`factorHandler`计算每只股票的因子值。在算法设计中，为了优化历史数据的存取性能，设计了一个字典（d）来存储每个symbol的历史资金净流入值（net_amount）。类似如下格式：
```
//字典定义 {key:symbol, value: [net_amount]}, 
600000->[-85,-69,-32,-57,80,-54,71,87,43,45,...]
600300->[-33,49,16,21,-82,-30,68,-44,-58,-66,...]
600400->[13,35,-67,-30,49,44,85,-10,-42,96,...]
600500->[-15,78,18,17,13,-70,67,-31,-19,-78,...]
600600->[65,-64,-90,-75,85,-99,15,83,-85,60,...]
600800->[14,-78,96,93,-89,92,99,-96,21,93,...]
```
当实时数据到达后，通过`dictUpdate!`将最新计算得到的net_amount更新到每个symbol的数据向量中，得到一个包含当天历史和最新net_amount数据的字典。针对这个字典通过循环调用自定义函数`calcNetAmountRatio`来计算每只股票的因子值。

* 核心计算脚本如下
```
//定义函数calcNetAmountRatio，对一个向量求前n个与前2n个元素之和的比值：
defg calcNetAmountRatio(x,n){
	size = x.size()
	return x.subarray((size - n):size).sum()\x.subarray((size - 2*n):size).sum()
}

//因子计算函数
def factorHandler(mutable factorTable,mutable d, facName,msg){
		codeList = msg.symbol.distinct()
		symbolCount = codeList.size()
		//资金净流入（net_amount）= volume * iif(bidPrice1>=askPrice1, 1, -1)
		t2 = select symbol, volume * iif(bidPrice1>=askPrice1, 1, -1) as net_amount from msg
		//将本次数据的计算net_amount追加更新字典
		dictUpdate!(d,append!, t2.symbol, t2.net_amount)
		//计算因子
	  	factorValue = array(DOUBLE,symbolCount)
		for(i in 0:symbolCount){
			factorValue[i] = calcNetAmountRatio(d[codeList[i]],100)
		}
		//添加时间戳，写入因子结果表
		factorTable.append!(table(take(now(),symbolCount) as timestamp, codeList as symbol,factorValue as value, take(facName,symbolCount) as factorName))
}
```

* 下列脚本完成数据的定义以及预处理

    * 定义保存因子的结果表
    ```
    share(streamTable(100:0, `timestamp`symbol`value`factorName,[TIMESTAMP,SYMBOL,DOUBLE,SYMBOL]),"FACTOR")
    ```
    * 预先构造历史的net_amount数据字典，此处利用了3.1的历史数据表。
    ```
	d = dict(STRING, ANY)
	his = select symbol,volume * iif(bidPrice1>=askPrice1, 1, -1) as net_amount from loadTable("dfs://level2","quotes") context by symbol limit -200
	for(id in his[`symbol].distinct())
		d[id]= exec net_amount from his where symbol == id
    ```

* 设置level2数据的订阅，建立实时数据和因子处理函数的关系。
```
subscribeTable(tableName="level2", actionName="act_factor", offset=0, handler=factorHandler{FACTOR,d,"factor1"}, msgAsTable=true, batchSize=4000, throttle=1)
```

订阅函数的调用需要注意以下几点：
* 部分应用的使用。因为订阅的handler必须是一个一元函数，仅接受一个msg参数(msg即订阅到的实时数据)，所以当因子处理函数需要多个参数时，需要将除msg之外的参数通过部分应用来固化，生成一个符合要求的一元函数。
* batchSize和throttle参数的使用。若消息的数量达到batchSize或者距离上次计算的时间间隔达到throttle这两个条件任意一个符合，都会触发handler。 

[本示例脚本下载](script/quant5_3.dos)

### 5.4 使用键值表缓存最新报价和交易价格

某些场景只需要每只股票最新的一条level 2数据。为了保证此类场景的最佳查询性能，可使用键值表订阅流数据表，并指定键值为股票代码。

```
newestLevel2 = keyedTable(`symbol, 100:0, `symbol`datetime`last`askPrice1`bidPrice1`askVolume1`bidVolume1`volume, [SYMBOL,DATETIME,DOUBLE,DOUBLE,DOUBLE,INT,INT,INT])
subscribeTable(tableName="level2", actionName="newestLevel2data", offset=0, handler=append!{newestLevel2}, msgAsTable=true)
```

键值表newestLevel2中，每只股票的数据仅为最新的一条level 2数据。 

[本示例脚本下载](script/quant5_4.dos)


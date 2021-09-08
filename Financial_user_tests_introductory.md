#  金融客户测试和入门教程

## 1. DolphinDB的存储机制

DolphinDB利用分布式文件系统实现数据库的存储和基本事务机制。数据库以分区（Chunk）为单位进行管理。分区的元数据（元数据指数据库的分区信息，每个分区的版本链，大小，存储位置等）存储在控制节点，副本数据存储在各数据节点，统一由分布式文件系统进行管理。一个数据库的数据可能分布存储在不同的服务器上，系统内部通过事务机制保证网络间数据的强一致性和完整性，对于外部用户来说，这些机制是完全透明的。每个分区副本的数据采用列式增量压缩存储。压缩算法采用了LZ4方式，平均能达到20%-25%的无损压缩比。

一个数据库最多可以支持三个维度的分区，支持百万甚至千万级的分区数。为尽可能保证每个分区的大小平衡，DolphinDB提供了值（VALUE）分区，范围（RANGE）分区，哈希（HASH）分区和列表（LIST）分区等多种分区方式，用户可以灵活的进行组合使用，合理规划分区。在查询时，加载数据的最小单位是分区列。DolphinDB不提供行级的索引，而是将分区作为数据库的物理索引。一个分区字段相当于给数据表建了一个物理索引。如果查询时用到了该字段做数据过滤，SQL引擎就能快速定位需要的数据块，而无需对整表进行扫描。在量化金融领域，查询分析大多基于某一个时间段、某个产品标识进行，因此时间和产品标识是量化金融领域最常用的分区维度。

下面展示一个期货tick实时行情数据库的存储目录和文件，其中数据库按照两个维度分区，第一个维度按天（tradingday列）进行值分区，第二个维度按照期货品种（instrument列）分为3个HASH分区,建库建表代码如下所示：

```
db1 = database("", VALUE, 2020.01.01..2020.12.31)
db2 = database("", HASH,[SYMBOL,3])
db = database("dfs://future",COMPO, [db1,db2])
colNames=`instrument`tradingday`calendarday`time`lastp`volume`openinterest`turnover`ask1`asksz1`bid1`bidsz1
colTypes=[SYMBOL,DATE,DATE,TIME,DOUBLE,INT,DOUBLE,DOUBLE,DOUBLE,INT,DOUBLE,INT]
t=table(1:0,colNames,colTypes)
db.createPartitionedTable(t,`tick,`tradingday`instrument)
```
写入数据后，存储目录和数据文件如下所示，

```
[dolphindb@localhost future]$ tree
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
从中可以看到，一个分区维度对应一层子目录，譬如按天分区的子目录名是20200101、20200102等，按HASH分区的子目录名是Key0，Key1等，表中每一列保存为一个后缀名为col的文件，如ask1.col,bid1.col等。



## 2. 行情数据和K线数据的数据库设计

行情数据是量化金融中量级最大的数据类别。在中国的证券市场，累积的历史数据在20~40T左右，每日新增的数据在20~40G左右。传统的关系型数据库处理这样的数据量级的性能非常低下。即使分库分表，效果也不理想。DolphinDB的分区机制可以轻松应对几百TB甚至PB级别的数据量。

为保证最佳性能，尽量将数据均匀分区，且将每个表的每个分区的数据量控制在压缩前100M左右。这是因为DolphinDB并不提供行级的索引，而是将分区作为数据库的物理索引，因此每个分区的数据量不宜过大。

行情数据通常可用时间和产品标识两个维度来进行分区：

(1) 时间维度大部分情况下可以选择按天进行值分区。如果时间跨度不是很长，而每天的数据量又非常大，也可以考虑按照小时进行分区，为此DolphinDB提供了DATEHOUR这种数据类型。设计分区机制时要考虑常用的应用场景。譬如说每次的请求都是对单一股票进行查询或聚合计算，而且跨越的时间比较长，可能几个月甚至一年，那么时间维度上按月分区不失为一种好的做法。

(2) 产品标识维度的分区可采用哈希、范围、值、列表等多种方法。如果每个产品在固定时间内的数据量比较均匀，可采用哈希或范围分区。例如中国的期货与股票市场以固定频率发布报价和交易的快照，因此每个市场内不同产品的数据量基本一致。美国金融市场的行情数据分布则完全不同，不同股票的tick级别数据量差异非常大。这种情境下，可选择范围分区，以一天或多天的数据为样本，将产品标识划分成多个范围，使得每一个范围内的产品的数据总量比较均衡。如果产品个数比较少，譬如期货的品种比较少，也可以考虑用值分区。

行情数据包括每日数据(end of day data)、Level 1、Level 2、Level 3等不同级别的数据。不同级别的数据，数据量差异比较大。所以建议采用不同分区机制的数据库来存储这些数据。

DolphinDB中的多个分区维度并不是层级关系，而是平级的组合关系。如果时间维度有n个分区，产品维度有m个分区，最多可能有n x m个分区。


K线数据或相关的signal数据都是基于高精度的行情数据降低时间精度产生的数据。通常，我们会生成不同频率的K线，譬如1分钟、5分钟、30分钟等等。这些不同频率的K线数据，因为数据量不是太大，建议存储在同一个分区表中，可以增加一个字段frequency来区分不同的时间窗口。K线表通常也按照日期和产品标识两个维度来分区，分区的粒度由数据量决定。以中国股票市场的分钟级K线为例，3000个股票每天产生约240个数据点，总共约72万个数据点。建议时间维度按月进行分区，产品的维度按范围或哈希分成15个分区。这样每个分区的数据量在100万行左右。这样的分区方法，既可在较长时间范围内（1个月或1年）快速查找某一个股票的数据，也可应对查找一天内全部股票的数据这样的任务。

## 3. 导入历史数据

### 3.1 从文本文件导入
中国股票市场每3秒更新一条 level 2 的行情数据，一般包括股票代码、日期、时间、交易量、交易价格、交易次数、买方与卖方的10档报价与量等常用信息，以及其它信息等数据。本例中所用数据为上海证券交易所A股股票2020年6月的 level 2 数据，每天的数据是一个约2.5GB的CSV文件，共68列数据。所有数据文件均存于同一个文件夹下("C:/DolphinDB/Data/Level2TextFiles/")。若其中一半的列为常用数据，遵循每个表每个分区中的常用数据压缩前为100MB左右的原则，可将数据库设计为复合分区。按天（date列）进行值分区，并按照股票代码（symbol列）分为10个HASH分区。

建库以及导入数据的脚本如下：
```
dbDate = database("", VALUE, 2020.01.01..2020.12.31)
dbSymbol=database("", HASH, [SYMBOL, 10])
db = database("dfs://level2", COMPO, [dbDate, dbSymbol])

dataDir="C:/DolphinDB/Data/Level2TextFiles/"

def importFiles(dataDir, db){
    dataFiles = exec filename from files(dataDir)
    for(f in dataFiles){
        loadTextEx(db, `quotes, `date`symbol, dataDir + f)
    }
}
importFiles(dataDir, db);
```

选择合适的数据库分区机制，对确保数据库最优性能非常重要。具体细节请参阅[分区数据库教程](https://github.com/dolphindb/Tutorials_CN/blob/master/database.md)。

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
对于二进制格式的文件，DolphinDB提供了2个函数用于导入：[readRecord!](https://www.dolphindb.cn/cn/help/readRecord.html)函数和[loadRecord](https://www.dolphindb.cn/cn/help/loadRecord.html)函数。二者的区别是，前者不支持导入字符串类型的数据，后者支持。在二进制文件中，date列和time列的数据以数值形式存储，可以使用[temporalParse](https://www.dolphindb.cn/cn/help/temporalParse.html)函数进行日期和时间类型数据的格式转换。再使用[replaceColumn!](https://www.dolphindb.cn/cn/help/replaceColumn.html)函数替换表中原有的列。symbol和market列在二进制文件中也是数值形式存储，处理的方式类似。具体代码如下所示：
```
schema = [
("symbol", INT),
("market", INT),
("date", INT),
("time", INT),
("preClose", DOUBLE),
("open", DOUBLE),
("high", DOUBLE),
("low", DOUBLE),
("last", DOUBLE),
("numTrades", INT),
("curNumTrades", INT),
("volume", INT),
("curVol", INT),
("turnover", DOUBLE),
("curTurnover", INT),
("peratio1", INT),
("peratio2", INT),
("totalAskVolume", INT),
("wavgAskPrice", DOUBLE),
("askLevel", INT),
("totalBidVolume", INT),
("wavgBidPrice", DOUBLE),
("bidLevel", INT),
("iopv", DOUBLE),
("ytm", INT),
("askPrice1", DOUBLE),
("askPrice2", DOUBLE),
("askPrice3", DOUBLE),
("askPrice4", DOUBLE),
("askPrice5", DOUBLE),
("askPrice6", DOUBLE),
("askPrice7", DOUBLE),
("askPrice8", DOUBLE),
("askPrice9", DOUBLE),
("askPrice10", DOUBLE),
("bidPrice1", DOUBLE),
("bidPrice2", DOUBLE),
("bidPrice3", DOUBLE),
("bidPrice4", DOUBLE),
("bidPrice5", DOUBLE),
("bidPrice6", DOUBLE),
("bidPrice7", DOUBLE),
("bidPrice8", DOUBLE),
("bidPrice9", DOUBLE),
("bidPrice10", DOUBLE),
("askVolume1", INT),
("askVolume2", INT),
("askVolume3", INT),
("askVolume4", INT),
("askVolume5", INT),
("askVolume6", INT),
("askVolume7", INT),
("askVolume8", INT),
("askVolume9", INT),
("askVolme10", INT),
("bidVolume1", INT),
("bidVolume2", INT),
("bidVolume3", INT),
("bidVolume4", INT),
("bidVolume5", INT),
("bidVolume6", INT),
("bidVolume7", INT),
("bidVolume8", INT),
("bidVolume9", INT),
("bidVolume10", INT),
("unixTime", LONG),
("upperLimit", DOUBLE),
("lowerLimit", DOUBLE)
]

dataDir="/hdd/hdd1/data/Level2BinFiles/"

def importFiles(dataDir, schema){
    tick1 = loadTable("dfs://level2","quotes")
    dataFiles = exec filename from files(dataDir)
    for(f in dataFiles){
        loadTextEx(db, `quotes, `date`symbol, dataDir + f)
        t=loadRecord(dataDir + f, schema)
        t.replaceColumn!(`date, t.date.string().datetimeParse("yyyyMMdd"))
        t.replaceColumn!(`time, t.time.format("000000000").datetimeParse("HHmmssSSS"))
        t.replaceColumn!(`symbol, t.symbol.format("000000"))
        t.replaceColumn!(`market, iif(t.market==0,"SH","SZ"))
        tick1.append!(t)
    }
}
importFiles(dataDir, schema);
```

### 3.3 生成模拟数据

测试需要的多天多月的数据，可通过前面导入的一天的真实数据，修改日期后复制生成。生成时考虑两种场景，一是服务器内存足够容纳一天的数据，二是内存不足以容纳一天的数据。

场景1，内存足够容纳一天的数据。例子代码如下，其中main函数中days为需要生成数据的起始日期，默认为2020年1月1日到2020年12月31日，threads为批处理作业数,这个数越大，对内存的要求越高，执行前须根据服务器内存实际情况进行修改。

```
def copyData(startDay,endDay){
	tick = loadTable("dfs://level2","quotes")
	t = select * from tick where date=2020.06.01
	
	for(i in 0:(endDay - startDay)){
		day = startDay + i
		if (weekday(day,false)>=5) 
                continue
		update t set date = day
		tick.append!(t)
	}
}
def main(days,threads){
	subdays=cutPoints(days,threads)
	for(i in 0:threads){
		submitJob("copyData"+i,"Simulated generated data", copyData, subdays[i],subdays[i+1]);
	}
}
login(`admin,`123456)
days=2020.01.01..2020.12.31
threads=12
main()
```
脚本从数据库中取出之前从文本文件导入的2020.06.01那天的数据，修改日期后写入数据库中。


场景2，内存不足容纳一天的数据。下列代码通过[repartitionDS](https://www.dolphindb.cn/cn/help/repartitionDS.html)函数将数据再分区。把一天的数据按照symbol字段切分为10份，然后通过[mr](https://www.dolphindb.cn/cn/help/distributedCalculation.html)函数将这10份数据更新日期后逐一写到数据库，mr函数的parallel参数设为false，不采用并行执行，以尽量少占用内存。

```
def writeData(mutable t,mutable pt, days){
	for(day in days){
		if (weekday(day,false)>=5)
            continue
		update t set date = day
		pt.append!(t)		
	}
}
def main(days){
	tick = loadTable("dfs://level2","quotes")
	ts = <select * from tick where date=2020.06.01>
	rds = repartitionDS(ts,`symbol,RANGE,10)
	mr(ds=rds, mapFunc=writeData{,tick,days},parallel=false)
}
login(`admin,`123456)
days=2020.07.01..2020.07.31
main(days)
```

## 4. 基于历史数据库的量化计算

4.1 常用的SQL处理

4.2 使用context子句处理面板数据

context by子句结合滑动窗口函数

4.3 asof join和window join的应用

4.4 pivot子句的应用

4.5 生成分钟级数据

4.5 机器学习的使用

4.6 使用API从数据库读取数据


5. 实时行情处理

5.1 使用API写数据到数据库

5.2 使用API写数据到流表再写入数据库

5.3 用流计算生成K线

5.4 用流计算生成实时高频因子

5.5 使用键值表缓存最新报价和交易价格

5.6 使用索引表重构Order Book

5.7 回放tick数据


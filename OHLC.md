# 在DolphinDB中计算K线 

DolphinDB提供了功能强大的内存计算引擎，内置时间序列函数，分布式计算以及流数据处理引擎，在众多场景下均可高效的计算K线。本教程将介绍DolphinDB如何通过批量处理和流式处理计算K线。

- 历史数据批量计算K线

其中可以指定K线窗口的起始时间；一天中可以存在多个交易时段，包括隔夜时段；K线窗口可重叠；使用交易量作为划分K线窗口的维度。需要读取的数据量特别大并且需要将结果写入数据库时，可使用DolphinDB内置的Map-Reduce函数并行计算。

- 流式计算K线

使用API实时接收市场数据，并使用DolphinDB内置的流数据时序计算引擎(TimeSeriesAggregator)进行实时计算得到K线数据。

## 1. 历史数据K线计算
使用历史数据计算K线，可使用DolphinDB的内置函数[`bar`](http://www.dolphindb.cn/cn/help/bar.html)，[`dailyAlignedBar`](http://www.dolphindb.cn/cn/help/dailyAlignedBar.html)，或[`wj`](http://www.dolphindb.cn/cn/help/windowjoin.html)。 

### 1.1 不指定K线窗口的起始时刻，根据数据自动生成K线结果
bar(X,Y)返回X减去X除以Y的余数，一般用于将数据分组。
```
date = 09:32m 09:33m 09:45m 09:49m 09:56m 09:56m;
bar(date, 5);
```
返回以下结果：
```
[09:30m,09:30m,09:45m,09:45m,09:55m,09:55m]
```

**例子1**：使用以下数据模拟美国股票市场：
```
n = 1000000
date = take(2019.11.07 2019.11.08, n)
time = (09:30:00.000 + rand(int(6.5*60*60*1000), n)).sort!()
timestamp = concatDateTime(date, time)
price = 100+cumsum(rand(0.02, n)-0.01)
volume = rand(1000, n)
symbol = rand(`AAPL`FB`AMZN`MSFT, n)
trade = table(symbol, date, time, timestamp, price, volume).sortBy!(`symbol`timestamp)
undef(`date`time`timestamp`price`volume`symbol)
```
计算5分钟K线：
```
barMinutes = 5
OHLC = select first(price) as open, max(price) as high, min(price) as low, last(price) as close, sum(volume) as volume from trade group by symbol, date, bar(time, barMinutes*60*1000) as barStart
```
请注意，以上数据中，time列的精度为毫秒。若time列精度不是毫秒，则应当将 barMinutes\*60*1000 中的数字做相应调整。


### 1.2 需要指定K线窗口的起始时刻

需要指定K线窗口的起始时刻，可使用`dailyAlignedBar`函数。该函数可处理每日多个交易时段，亦可处理隔夜时段。

请注意，使用`dailyAlignedBar`函数时，时间列必须含有日期信息，包括 DATETIME, TIMESTAMP 或 NANOTIMESTAMP 这三种类型的数据。指定每个交易时段窗口起始时刻的参数 timeOffset 必须使用相应的去除日期信息之后的 SECOND，TIME 或 NANOTIME 类型的数据。

**例子2**（每日一个交易时段）：计算美国股票市场7分钟K线。数据沿用例子1中的trade表。
```
barMinutes = 7
OHLC = select first(price) as open, max(price) as high, min(price) as low, last(price) as close, sum(volume) as volume from trade group by symbol, dailyAlignedBar(timestamp, 09:30:00.000, barMinutes*60*1000) as barStart
```

**例子3**（每日两个交易时段）：中国股票市场每日有两个交易时段，上午时段为9:30至11:30，下午时段为13:00至15:00。

使用以下数据模拟：
```
n = 1000000
date = take(2019.11.07 2019.11.08, n)
time = (09:30:00.000 + rand(2*60*60*1000, n/2)).sort!() join (13:00:00.000 + rand(2*60*60*1000, n/2)).sort!()
timestamp = concatDateTime(date, time)
price = 100+cumsum(rand(0.02, n)-0.01)
volume = rand(1000, n)
symbol = rand(`600519`000001`600000`601766, n)
trade = table(symbol, timestamp, price, volume).sortBy!(`symbol`timestamp)
undef(`date`time`timestamp`price`volume`symbol)
```

计算7分钟K线：
```
barMinutes = 7
sessionsStart=09:30:00.000 13:00:00.000
OHLC = select first(price) as open, max(price) as high, min(price) as low, last(price) as close, sum(volume) as volume from trade group by symbol, dailyAlignedBar(timestamp, sessionsStart, barMinutes*60*1000) as barStart
```

**例子4**（每日两个交易时段，包含隔夜时段）：某些期货每日有多个交易时段，且包括隔夜时段。本例中，第一个交易时段为8:45到下午13:45，另一个时段为隔夜时段，从下午15:00到第二天05:00。

使用以下数据模拟:
```
daySession =  08:45:00.000 : 13:45:00.000
nightSession = 15:00:00.000 : 05:00:00.000
n = 1000000
timestamp = rand(concatDateTime(2019.11.06, daySession[0]) .. concatDateTime(2019.11.08, nightSession[1]), n).sort!()
price = 100+cumsum(rand(0.02, n)-0.01)
volume = rand(1000, n)
symbol = rand(`A120001`A120002`A120003`A120004, n)
trade = select * from table(symbol, timestamp, price, volume) where timestamp.time() between daySession or timestamp.time()>=nightSession[0] or timestamp.time()<nightSession[1] order by symbol, timestamp
undef(`timestamp`price`volume`symbol)
```
计算7分钟K线：
```
barMinutes = 7
sessionsStart = [daySession[0], nightSession[0]]
OHLC = select first(price) as open, max(price) as high, min(price) as low, last(price) as close, sum(volume) as volume from trade group by symbol, dailyAlignedBar(timestamp, sessionsStart, barMinutes*60*1000) as barStart
```

### 1.3 重叠K线窗口：使用`wj`函数

以上例子中，K线窗口均不重叠。若要计算重叠K线窗口，可以使用`wj`函数。使用`wj`函数，可对左表中的时间列，指定相对时间范围，在右表中进行计算。

**例子5** （每日两个交易时段，重叠的K线窗口）：模拟中国股票市场数据，每5分钟计算30分钟K线。
```
n = 1000000
sampleDate = 2019.11.07
symbols = `600519`000001`600000`601766
trade = table(take(sampleDate, n) as date, 
	(09:30:00.000 + rand(7200000, n/2)).sort!() join (13:00:00.000 + rand(7200000, n/2)).sort!() as time, 
	rand(symbols, n) as symbol, 
	100+cumsum(rand(0.02, n)-0.01) as price, 
	rand(1000, n) as volume)
```
首先根据时间来生成窗口，并且用cross join来生成股票和交易窗口的组合。
```
barWindows = table(symbols as symbol).cj(table((09:30:00.000 + 0..23 * 300000).join(13:00:00.000 + 0..23 * 300000) as time))
```

然后使用`wj`函数计算重叠窗口的K线数据：
```
OHLC = wj(barWindows, trade, 0:(30*60*1000), 
		<[first(price) as open, max(price) as high, min(price) as low, last(price) as close, sum(volume) as volume]>, `symbol`time)
```

### 1.4 使用交易量划分K线窗口

上面的例子我们均使用时间作为划分K线窗口的维度。在实践中，也可以使用其他维度作为划分K线窗口的依据。譬如用累计的交易量来计算K线。

**例子6** （每日两个交易时段，使用累计的交易量计算K线）：模拟中国股票市场数据，交易量每增加10000计算K线。
```
n = 1000000
sampleDate = 2019.11.07
symbols = `600519`000001`600000`601766
trade = table(take(sampleDate, n) as date, 
	(09:30:00.000 + rand(7200000, n/2)).sort!() join (13:00:00.000 + rand(7200000, n/2)).sort!() as time, 
	rand(symbols, n) as symbol, 
	100+cumsum(rand(0.02, n)-0.01) as price, 
	rand(1000, n) as volume)
	
volThreshold = 10000
select first(time) as barStart, first(price) as open, max(price) as high, min(price) as low, last(price) as close 
from (select symbol, price, cumsum(volume) as cumvol from trade context by symbol)
group by symbol, bar(cumvol, volThreshold) as volBar
```
代码采用了嵌套查询的方法。子查询为每个股票生成累计的交易量cumvol，然后在主查询中根据累计的交易量用`bar`函数生成窗口。


#### 1.5 使用MapReduce函数加速

若需从数据库中提取较大量级的历史数据，计算K线，然后存入数据库，可使用DolphinDB内置的Map-Reduce函数[`mr`](http://www.dolphindb.cn/cn/help/mr.html)进行数据的并行读取与计算。这种方法可以显著提高速度。

本例使用美国股票市场精确到纳秒的交易数据。原始数据存于"dfs://TAQ"数据库的"trades"表中。"dfs://TAQ"数据库采用复合分区：基于交易日期Date的值分区与基于股票代码Symbol的范围分区。

(1) 将存于磁盘的原始数据表的元数据载入内存：
```
login(`admin, `123456)
db = database("dfs://TAQ")
trades = db.loadTable("trades")
```
(2) 在磁盘上创建一个空的数据表，以存放计算结果。以下代码建立一个模板表（model），并根据此模板表的schema在数据库"dfs://TAQ"中创建一个空的 OHLC 表以存放K线计算结果：
```
model=select top 1 Symbol, Date, Time.second() as bar, PRICE as open, PRICE as high, PRICE as low, PRICE as close, SIZE as volume from trades where Date=2007.08.01, Symbol=`EBAY
if(existsTable("dfs://TAQ", "OHLC"))
	db.dropTable("OHLC")
db.createPartitionedTable(model, `OHLC, `Date`Symbol)
```
(3) 使用`mr`函数计算K线数据，并将结果写入 OHLC 表中：
```
def calcOHLC(inputTable){
	tmp=select first(PRICE) as open, max(PRICE) as high, min(PRICE) as low, last(PRICE) as close, sum(SIZE) as volume from inputTable where Time.second() between 09:30:00 : 15:59:59 group by Symbol, Date, 09:30:00+bar(Time.second()-09:30:00, 5*60) as bar
	loadTable("dfs://TAQ", `OHLC).append!(tmp)
	return tmp.size()
}
ds = sqlDS(<select Symbol, Date, Time, PRICE, SIZE from trades where Date between 2007.08.01 : 2019.08.01>)
mr(ds, calcOHLC, +)
```
在以上代码中，ds是函数`sqlDS`生成的一系列数据源，每个数据源代表从一个数据分区中提取的数据；自定义函数`calcOHLC`为Map-Reduce算法中的map函数，对每个数据源计算K线数据，并将结果写入数据库，返回写入数据库的K线数据的行数；"+"是Map-Reduce算法中的reduce函数，将所有map函数的结果，亦即写入数据库的K线数据的行数相加，返回写入数据库的K线数据总数。

### 2. 实时K线计算

DolphinDB database 中计算实时K线的流程如下图所示：

![avatar](https://github.com/dolphindb/Tutorials_CN/raw/master/images/K-line.png)

实时数据供应商一般会提供基于Python、Java或其他常用语言的API的数据订阅服务。本例中使用Python来模拟接收市场数据，通过DolphinDB Python API写入流数据表中。DolphinDB的流数据时序聚合引擎(TimeSeriesAggregator)可以对实时数据按照指定的频率与移动窗口计算K线。

本例使用的模拟实时数据源为[文本文件trades.csv](https://github.com/dolphindb/Tutorials_CN/raw/master/data/k-line/trades.csv)。该文件包含以下4列（一同给出一行样本数据）：

Symbol| Datetime | Price| Volume
---|---|---|---
000001	|2018.09.03T09:30:06	|10.13	|4500


最终输出的K线数据表包含以下7列（一同给出一行样本数据）：

datetime| symbol | open | close | high | low | volume | 
---|---|---|---|---|---|---
2018.09.03T09:30:07|	000001	|10.13|	10.13	|10.12	|10.12	| 468060

以下三小节介绍实时K线计算的三个步骤：

#### 2.1 使用 Python 接收实时数据，并写入DolphinDB流数据表

* DolphinDB 中建立流数据表

```
share streamTable(100:0, `Symbol`Datetime`Price`Volume,[SYMBOL,DATETIME,DOUBLE,INT]) as Trade
```

* Python程序从数据源 trades.csv 文件中读取数据写入DolphinDB。

实时数据中Datetime的数据精度是秒，由于pandas DataFrame中仅能使用DateTime[64]即nanatimestamp类型，所以下列代码在写入前有一个数据类型转换的过程。这个过程也适用于大多数数据需要清洗和转换的场景。

```python
import dolphindb as ddb
import pandas as pd
import numpy as np
csv_file = "trades.csv"
csv_data = pd.read_csv(csv_file, dtype={'Symbol':str} )
csv_df = pd.DataFrame(csv_data)
s = ddb.session();
s.connect("127.0.0.1",8848,"admin","123456")
#上传DataFrame到DolphinDB，并对Datetime字段做类型转换
s.upload({"tmpData":csv_df})
s.run("data = select Symbol, datetime(Datetime) as Datetime, Price, Volume from tmpData")
s.run("tableInsert(Trade,data)")
```
#### 2.2 实时计算K线

本例中使用时序聚合引擎实时计算K线数据，并将计算结果输出到流数据表 OHLC 中。

计算K线数据，按照计算时间窗口是否存在重合分为两种计算场景：一是时间窗口不重合，比如每隔5分钟计算一次过去5分钟的K线数据；二是时间窗口部分重合，比如每隔1分钟计算过去5分钟的K线数据。

可通过设定 `createTimeSeriesAggregator` 函数的 windowSize 和 step 参数以实现这两个场景。场景一 windowSize 与 step 相等；场景二 windowSize 是 step 的倍数。

首先定义输出表:
```
share streamTable(100:0, `datetime`symbol`open`high`low`close`volume,[DATETIME, SYMBOL, DOUBLE,DOUBLE,DOUBLE,DOUBLE,LONG]) as OHLC
```
根据应用场景的不同，在以下两行代码中选择一行，以定义时序聚合引擎：

场景一：
```
tsAggrKline = createTimeSeriesAggregator(name="aggr_kline", windowSize=300, step=300, metrics=<[first(Price),max(Price),min(Price),last(Price),sum(volume)]>, dummyTable=Trade, outputTable=OHLC, timeColumn=`Datetime, keyColumn=`Symbol)
```
场景二：
```
tsAggrKline = createTimeSeriesAggregator(name="aggr_kline", windowSize=300, step=60, metrics=<[first(Price),max(Price),min(Price),last(Price),sum(volume)]>, dummyTable=Trade, outputTable=OHLC, timeColumn=`Datetime, keyColumn=`Symbol)
```
最后，定义流数据订阅。若此时流数据表Trade中已经有实时数据写入，那么实时数据会马上被订阅并注入聚合引擎：
```
subscribeTable(tableName="Trade", actionName="act_tsaggr", offset=0, handler=append!{tsAggrKline}, msgAsTable=true)
```

#### 2.3 在Python中展示K线数据

在本例中，聚合引擎的输出表也定义为流数据表，客户端可以通过Python API订阅输出表，并将计算结果展现到Python终端。

以下代码使用Python API订阅实时聚合计算的输出结果表OHLC，并将结果通过print函数打印出来。

```python
import dolphindb as ddb
import pandas as pd
import numpy as np
#设定本地端口20001用于订阅流数据
s.enableStreaming(20001)
def handler(lst):         
    print(lst)
# 订阅DolphinDB(本机8848端口)上的OHLC流数据表
s.subscribe("127.0.0.1", 8848, handler, "OHLC")
```

也可通过[Grafana](https://github.com/dolphindb/grafana-datasource/blob/master/README_CN.md)等可视化系统来连接DolphinDB database，对输出表进行查询并将结果以图表方式展现。
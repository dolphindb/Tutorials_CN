# DolphinDB教程：实时计算高频因子

DolphinDB是一款高性能分布式时序数据库。与传统的关系数据库和常见的时序数据库不同，DolphinDB不仅提供了高速存取时序数据的基本功能，而且内置了向量化的多范式编程语言与强大的计算引擎。DolphinDB的计算引擎不仅可以用于量化金融的回测和研发，也可以用于生产环境的实时计算，譬如高频因子的计算。请使用DolphinDB 1.20.0 或更高版本运行本教程中的例子。

运行本教程中的代码例子前，请先根据第8节“本教程中流数据配置”进行流数据系统的配置。

- [1. 概述](#1-概述)
- [2. 无状态因子计算](#2-无状态因子计算)
- [3. 滑动窗口因子计算](#3-滑动窗口因子计算)
- [4. 状态因子计算](#4-状态因子计算)
	- [4.1 使用内存表计算状态因子](#41-使用内存表计算状态因子)
	- [4.2 基于分区内存表的状态因子计算](#42-基于分区内存表的状态因子计算)
	- [4.3 基于字典的状态因子计算](#43-基于字典的状态因子计算)
- [5. 因子计算流水线](#5-因子计算流水线)
- [6. 提高计算效率的方法](#6-提高计算效率的方法)
	- [6.1 使用字典或分区内存表分组存储数据](#61-使用字典或分区内存表分组存储数据)
	- [6.2 平衡延时和吞吐量](#62-平衡延时和吞吐量)
	- [6.3 并行计算](#63-并行计算)
	- [6.4 即时编译](#64-即时编译)
- [7. 流计算调试](#7-流计算调试)
	- [7.1 调试消息处理函数](#71-调试消息处理函数)
	- [7.2 历史数据回测](#72-历史数据回测)
- [8. 本教程中流数据配置](#8-本教程中流数据配置)

## 1. 概述

与其它流计算处理框架类似，DolphinDB的流计算系统也包括消息发布、消息代理和消息订阅三个部分。消息发布端与消息订阅端均可为本地的数据节点、另一个数据节点，或第三方的API（例如Python,C++, Java, C#等API）。DolphinDB数据节点上的流数据表（stream table）充当消息代理的角色，发布端向流表插入记录即实现了消息发布的功能。

高频因子的计算，以交易和报价数据作为主要的流数据输入，亦可配合使用其它数据。高频因子的计算结果通常输出到一个流数据表或内存表。

DolphinDB流计算中使用的消息可以采用两种格式：表（table）和元组（tuple），由`subscribeTable`函数的msgAsTable参数指定。

本教程中所用的csv数据文件，可由[此处](https://www.dolphindb.cn/downloads/tutorial/hfFactorsSampleData.zip)下载，并存于文件夹 YOURDIR 中。

## 2. 无状态因子计算

所谓无状态因子计算，即因子的计算不需要回溯历史数据，仅根据最新的一条消息即可生成因子。无状态因子计算场景下，建议使用表作为消息的格式，并使用SQL语句计算因子。

假设消息数据表包含以下列：symbol, date, time, askPrice1..askPrice5, bidPrice1..bidPrice5, askVolume1..askVolume5, bidVolume1..bidVolume5。其中 askPrice1..askPrice5 以及 askVolume1..askVolume5 为前5档卖方出价以及对应的量；bidPrice1..bidPrice5 以及 bidVolume1..bidVolume5 为前5档买方出价以及对应的量。计算以下两个状态因子：
 
    * 因子1：根据每一条最新报价，计算因子 (askVolume1-bidVolume1)/(askVolume1+bidVolume1)。

    * 因子2：对买档与卖档，分别计算最新5挡成交量加权累计之和，然后计算两者之比例。
    
上述无状态因子，可分别使用以下脚本计算：

    * 因子1：
```
    select symbol,time(now()) as time, (askVolume1-bidVolume1)/(askVolume1+bidVolume1) as factorValue from msg
```
    * 因子2：
```
    w = exp(-1 * 0..4)
    select symbol, time(now()) as time, 0.5*log(rowSum([bidVolume1,bidVolume2,bidVolume3,bidVolume4,bidVolume5]*w)/rowSum([askVolume1,askVolume2,askVolume3,askVolume4,askVolume5]*w)) as factorValue from msg
```

要实时计算上述无状态因子，把上述脚本封装成函数并在`subscribeTable`函数中指定其为handler参数（消息处理函数）即可。消息处理函数必须是单目函数，且唯一的参数就是本批次订阅到的消息。以因子2为例:
```
quotesData = loadText(yourDIR + "sampleQuotes.csv")

def factorHandler(mutable factor1, msg){
    w = exp(-1 * 0..4)
    x=select symbol, datetime(now()) as datetime, 0.5*log(rowSum([bidVolume1,bidVolume2,bidVolume3,bidVolume4,bidVolume5]*w)/rowSum([askVolume1,askVolume2,askVolume3,askVolume4,askVolume5]*w)) as factorValue from msg
    factor1.tableInsert(x)
}
factor1=table(1000000:0, `symbol`datetime`factorValue, [SYMBOL,DATETIME,DOUBLE]) 
x=quotesData.schema().colDefs
share(streamTable(1000000:0, x.name, x.typeString), "quotes")

subscribeTable(tableName="quotes", actionName="hfFactor", handler=factorHandler{factor1}, msgAsTable=true)

```
然后使用`replay`函数将样本数据quotesData写入流数据表quotes触发计算。本教程的所有例子均使用`replay`函数将历史数据进行回放以模拟实时数据。
```
replay(inputTables=quotesData, outputTables=quotes, dateColumn=`date, timeColumn=`time)
```
最后在数据表factor1中查看计算结果。本例计算结果中的时间为计算发生时间，也可以根据业务要求调整为数据时间，即直接取消息中的date与time列。

## 3. 滑动窗口因子计算

流数据计算中，有一类典型的计算是根据滑动的时间窗口计算聚合值，连续的两个窗口可以重叠或不重叠。这类计算统称为滑动窗口计算。DolphinDB内置的时间序列聚合引擎用于解决滑动窗口计算。DolphinDB针对某些聚合函数在流数据时序引擎中的使用进行了优化，在计算每个窗口时充分利用上一个窗口的计算结果，尽可能避免重复计算，显著提高运行速度。已优化的聚合函数包括：`sum`, `sum2`, `min`, `max`, `first`, `last`, `avg`, `count`, `std`, `var`, `med`, `percentile`, `covar`, `corr`, `beta`, `wavg`, `wsum`。聚合引擎可以接受的指标除了单个聚合函数使用消息中的一个或两个列作为参数外，还可以进行两个方向的扩展：（1）多个聚合函数构成新的表达式；（2）聚合函数的参数可以是消息中多个字段的表达式。

下例使用时间序列聚合引擎计算分钟级K线。Trade表是一个流数据表，这里为了方便，假定Trade表与订阅端在同一个节点上。实际使用中，两者也可处于不同的节点。
```
tradesData = loadText(yourDIR + "sampleTrades1.csv")

//定义流数据表Trade
x=tradesData.schema().colDefs
share streamTable(100:0, x.name, x.typeString) as Trade

//定义OHLC输出表
share streamTable(100:0, `datetime`symbol`open`high`low`close`volume`updatetime,[TIMESTAMP,SYMBOL,DOUBLE,DOUBLE,DOUBLE,DOUBLE,LONG,TIMESTAMP]) as OHLC

//定义实时聚合引擎：每分钟计算过去5分钟K线
tsAggrOHLC = createTimeSeriesAggregator(name="aggr_ohlc", windowSize=300000, step=60000, metrics=<[first(Price),max(Price),min(Price),last(Price),sum(Volume),now()]>, dummyTable=Trade, outputTable=OHLC, timeColumn=`Datetime, keyColumn=`Symbol)

//订阅流数据写入聚合引擎
subscribeTable(tableName="Trade", actionName="minuteOHLC1", offset=0, handler=append!{tsAggrOHLC}, msgAsTable=true)

replay(inputTables=tradesData, outputTables=Trade, dateColumn=`Datetime)
```
查看结果：
```
select top 10 * from OHLC
```
上面的例子中，流数据表Trade的消息直接作为聚合引擎的输入。某些场景下，需要对流数据表中的数据进行预处理后再输入到聚合引擎。若Trade表中的Volume是从开盘到当前的累计交易量，下例中定义函数calcVolume作为数据订阅的消息处理函数（即handler参数），将累计交易量转化为当前交易量之后，再输入聚合引擎。使用字典dictVol保存每只股票上一条消息中的累计交易量，以计算当前交易量。由于若handler参数是函数时，必须仅有一个参数，即本批次订阅到的消息，所以calcVolume必须包括msg这样一个代表本批次订阅数据的参数，且在subscribeTable函数中使用时，使用“部分应用”将其它参数固化。
```
def calcVolume(mutable dictVolume, mutable tsAggrOHLC, msg){
	t = select Symbol, DateTime, Price, Volume from msg context by Symbol limit -1 
	update t set prevVolume = dictVolume[Symbol]
	dictVolume[t.Symbol] = t.Volume
	tsAggrOHLC.append!(t.update!("Volume", <Volume - prevVolume>).dropColumns!("prevVolume"))
}

tradesData = loadText(yourDIR + "sampleTrades2.csv")

//定义流数据表Trade
x=tradesData.schema().colDefs
share streamTable(100:0, x.name, x.typeString) as Trade

//定义OHLC输出表
share streamTable(100:0, `datetime`symbol`open`high`low`close`volume`updatetime,[TIMESTAMP,SYMBOL,DOUBLE,DOUBLE,DOUBLE,DOUBLE,LONG,TIMESTAMP]) as OHLC

//定义实时聚合引擎：每分钟计算过去5分钟K线
tsAggrOHLC = createTimeSeriesAggregator(name="aggr_ohlc", windowSize=300000, step=60000, metrics=<[first(Price),max(Price),min(Price),last(Price),sum(Volume),now()]>, dummyTable=Trade, outputTable=OHLC, timeColumn=`Datetime, keyColumn=`Symbol)

//订阅流数据写入聚合引擎
dictVol = dict(STRING, DOUBLE)
subscribeTable(tableName="Trade", actionName="minuteOHLC2", offset=0, handler=calcVolume{dictVol,tsAggrOHLC}, msgAsTable=true)

replay(inputTables=tradesData, outputTables=Trade, dateColumn=`Datetime)
```
最后查看结果：
```
select top 10 * from OHLC 
```
响应式状态引擎支持一部分优化过的序列处理函数，因此除了通过定义函数calcVolume来将累计交易量转化为当前交易量以外，可以通过响应式状态引擎和时间序列聚合引擎串联来实现同样的效果：

```
tradesData = loadText(yourDIR + "sampleTrades2.csv")

//定义流数据表Trade
x=tradesData.schema().colDefs
share streamTable(100:0, x.name, x.typeString) as Trade

//定义OHLC输出表
share streamTable(100:0, `datetime`symbol`open`high`low`close`volume`updatetime,[TIMESTAMP,SYMBOL,DOUBLE,DOUBLE,DOUBLE,DOUBLE,LONG,TIMESTAMP]) as OHLC

//定义实时聚合引擎：每分钟计算过去5分钟K线
tsAggrOHLC = createTimeSeriesAggregator(name="aggr_ohlc", windowSize=300000, step=60000, metrics=<[first(Price),max(Price),min(Price),last(Price),sum(Volume),now()]>, dummyTable=Trade, outputTable=OHLC, timeColumn=`Datetime, keyColumn=`Symbol)

//定义响应式状态引擎：预处理Volume数据
rsAggrOHLC = createReactiveStateEngine(name="calc_vol", metrics=<[Datetime, Price, deltas(Volume)]>, dummyTable=Trade, outputTable=tsAggrOHLC, keyColumn=`Symbol)

//订阅流数据写入聚合引擎
subscribeTable(tableName="Trade", actionName="minuteOHLC2", offset=0, handler=append!{rsAggrOHLC}, msgAsTable=true)

replay(inputTables=tradesData, outputTables=Trade, dateColumn=`Datetime)
```

最后查看结果：

```
select top 10 * from OHLC 
```

## 4. 状态因子计算

有状态的因子，即因子的计算不仅用到当前数据，还会用到历史数据。实现状态因子的计算，一般包括这几个步骤：（1）保存本批次的消息数据到历史记录；（2）根据更新后的历史记录，计算因子，（3）将因子计算结果写入输出表中。如有必要，删除未来不再需要的的历史记录。

由于DolphinDB的消息处理函数必须是单目函数，且唯一的参数就是当前的消息。要保存历史状态并且可以在消息处理函数中引用它，可以使用部分应用，定义一个多个参数的消息处理函数，其中一个参数用于接收消息，其它所有参数被固化，用于保存历史状态。这些固化参数只对消息处理函数可见，不受其他应用的影响。

历史状态可保存在内存表，字典或分区内存表中。本节的三个例子分别演示如何使用这三种方法来保存历史状态并计算因子。

### 4.1 使用内存表计算状态因子

本例中因子为当前第一档卖价与30个报价之前的第一档卖价的比值。因此，对于每只股票，至少需要保留30个历史报价。为此，可以定义一个内存表history用于保存所有股票的历史状态。

核心代码如下所示。其中，自定义聚合函数factorAskPriceRatio用于计算因子。消息处理函数factorHandler中：
- 第一行将本批次消息保存到内存表history中。 
- 第二行用于提取本批次消息的股票代码。每次计算仅针对本批次消息所包含的股票。
- 第三行计算每只股票的因子。
- 最后一行将生成的因子输出到factors表中。

消息订阅函数`subscribeTable`的核心参数handler是factorHandler的一个部分应用，其中两个固定的参数history和factors分别用于保存历史状态和输出生成的因子。
```
quotesData = loadText(yourDIR + "sampleQuotes.csv")

defg factorAskPriceRatio(x){
	cnt = x.size()
	if(cnt < 31) return double()
	else return x[cnt - 1]/x[cnt - 31]
}

def factorHandler(mutable history, mutable factors, msg){
	history.append!(select symbol, askPrice1 from msg)
	syms = msg.symbol
	t = select factorAskPriceRatio(askPrice1) as factor from history where symbol in syms group by symbol
	factors.append!(t.update!("timestamp", now()).reorderColumns!("timestamp"))
}

x=quotesData.schema().colDefs
share streamTable(100:0, x.name, x.typeString) as quotes1
history = table(1000000:0, `symbol`askPrice1, [SYMBOL,DOUBLE])
share streamTable(100000:0, `timestamp`symbol`factor, [TIMESTAMP,SYMBOL,DOUBLE]) as factors
subscribeTable(tableName = "quotes1", offset=0, handler=factorHandler{history, factors}, msgAsTable=true, batchSize = 3000, throttle=0.005)

replay(inputTables=quotesData, outputTables=quotes1, dateColumn=`date, timeColumn=`time)
```
查看结果：
```
select top 10 * from factors where isValid(factor)
```
### 4.2 基于分区内存表的状态因子计算

使用普通内存表计算因子，是单线程操作，不能并行计算。使用分区内存表计算因子，可以并行计算以提高效率。

对内存表执行SQL语句时，只有一个子任务。对分区内存表执行SQL语句时，会产生与分区数量一致的子任务，由当前的流数据执行线程和系统的执行线程池来完成。系统的线程池的大小由配置参数localExecutors决定。因此执行一个分区内存表的SQL语句，在分区数量大于localExecutors的情况下，最大的并行度是localExecutors + 1。

内存表与分区内存表在数据插入和SQL查询方面，大部分情况下没有语法上的区别。因此4.1节中的代码仍然适用于分区内存表。唯一需要修改的是history表的创建和初始化。
```
history_model = table(1000000:0, `symbol`askPrice1, [SYMBOL,DOUBLE])
syms = format(600000..601000, "000000")
db = database(partitionType=VALUE, partitionScheme=syms)
history = db.createPartitionedTable(table=history_model, tableName=`history, partitionColumns=`symbol)
```
> 请注意，syms仅包括样本数据中的1001个股票代码。实际使用时请根据具体情况进行调整。

当分区内存表的分区机制是值分区，而且因子比较简单时，除了使用SQL语句，亦可直接在每个分区中计算因子。在大量的小表上使用SQL的成本较高，直接在每个分区中进行计算可能提高效率。下面的代码中改写了factorHandler的定义。通过系统内置函数`getTablet`获取消息中所有股票对应的分区子表，然后循环计算每只股票的因子，最后把因子写入factors表中。该计算方案虽然实际上使用了单线程，但是耗时却只有SQL方案的三分之一左右。
```
def factorHandler(mutable history, mutable factors, msg){
	history.append!(select symbol, askPrice1 from msg)
	syms = msg.symbol
	tables = getTablet(history, syms)
	cnt = syms.size()
	v = array(DOUBLE, cnt)
	for(i in 0:cnt){
		v[i] = factorAskPriceRatio(tables[i].askPrice1)
	}
	factors.tableInsert([take(now(), cnt), syms, v])
}
```

### 4.3 基于字典的状态因子计算

创建一个键值为STRING类型，值为元组（tuple）类型的字典。该字典中，每只股票对应一个数组，以存储卖价的历史数据。使用`dictUpdate!`函数更新该字典，然后循环计算每只股票的因子。由于每只股票的历史数据分别存储，计算因子时不再需要对数据分组，因而有更高的效率。
```
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
查看结果：
```
select top 10 * from factors where isValid(factor)
```
这三种方法各有优缺点。
- 内存表简单易用，计算可以使用简单的SQL语句完成，缺点是计算性能较低，尤其是每只股票的消息单独处理时，性能尤为低下。
- 字典方法的数据结构最为简单，当因子较为简单时，无论大量股票批量处理，还是每只股票单独处理，效率均为最高。字典方法的缺点是如果因子计算较为复杂时，逐个处理的效率不高。
- 分区内存表方法居于两者之间。可以使用SQL语句来完成复杂或简单的因子计算，但与未分区的内存表相比，可以通过分区来实现并行计算，以提高效率。

## 5. 因子计算流水线

一些较为复杂的因子可能需要使用流水线处理（或者链式处理）。一种常见场景为：先根据输入的行情数据使用时间序列聚合引擎生成分钟级K线，然后根据分钟级K线生成状态因子。可将消息处理函数的输出指向另一个流数据表，以实现流水线处理。

下例演示因子计算的流水线处理。首先计算每只股票分钟级的K线，然后根据最近的10个K线记录计算前面5个时间段的资金净流入量与后面5个时间段的资金净流入量的比例。

```
tradesData = loadText(yourDIR + "sampleTrades1.csv")

defg factorMoneyFlowRatio(x){
	n = x.size()
	if(n < 9) return double()
	else return x.subarray((n-9):(n-5)).sum()\x.subarray((n-4):n).sum()
}

def factorHandler2(mutable historyDict, mutable factors, msg){
	netAmount = exec volume * iif(close>=open, 1, -1) from msg
	dictUpdate!(historyDict, append!, msg.symbol, netAmount, x->array(x.type(), 0, 500).append!(x))
	syms = msg.symbol.distinct()
	cnt = syms.size()
	v = array(DOUBLE, cnt)
	for(i in 0:cnt){
	    v[i] = factorMoneyFlowRatio(historyDict[syms[i]])
	}
	factors.tableInsert([take(now(), cnt), syms, v])
}

//定义流数据表Trade
x=tradesData.schema().colDefs
share streamTable(100:0, x.name, x.typeString) as Trade

//定义OHLC输出表
share streamTable(100:0, `datetime`symbol`open`high`low`close`volume`updatetime,[TIMESTAMP,SYMBOL,DOUBLE,DOUBLE,DOUBLE,DOUBLE,LONG,TIMESTAMP]) as OHLC

//定义实时聚合引擎：每分钟计算过去1分钟K线
tsAggrOHLC = createTimeSeriesAggregator(name="aggr_ohlc", windowSize=60000, step=60000, metrics=<[first(Price),max(Price),min(Price),last(Price),sum(Volume),now()]>, dummyTable=Trade, outputTable=OHLC, timeColumn=`Datetime, keyColumn=`Symbol)

//订阅流数据写入聚合引擎
subscribeTable(tableName="Trade", actionName="minuteOHLC3", offset=0, handler=append!{tsAggrOHLC}, msgAsTable=true)

//订阅流表OHLC，计算指标，并输出到流表factors
dictHistory = dict(STRING, ANY)
share streamTable(100000:0, `timestamp`symbol`factor, [TIMESTAMP,SYMBOL,DOUBLE]) as factors
subscribeTable(tableName="OHLC", actionName="calcMoneyFlowRatio", offset=0, handler=factorHandler2{dictHistory,factors}, msgAsTable=true)

replay(inputTables=tradesData, outputTables=Trade, dateColumn=`Datetime)
```
查看结果：
```
select top 10 * from factors where isValid(factor)
```
使用流水线计算因子时，需要合理安排消息的执行线程。最理想的情况是每一个环节由不同的线程来完成，以降低延迟。流数据消息的默认执行模式是为每一个线程分配一个消息队列，订阅的消息进入了不同的队列，就由相应的线程来执行。那如何为一个订阅指定执行线程或队列呢？可以使用函数`subscribeTable`的可选参数hash。如果订阅的执行线程总数为N，那么分配的线程序号（从0开始）为N除以hash的余数。订阅的执行线程总数可以通过配置变量subExecutors来设置，默认值为1。


## 6. 提高计算效率的方法

### 6.1 使用字典或分区内存表分组存储数据

实时计算时，通常需要对每只股票分别计算。如果事先按股票分组存储数据，可显著缩短计算耗时。分组存储可使用字典和分区内存表这两种方法。我们测试了第4节中提到的三种方法，假定4000个股票，每个股票有300条历史记录，4000条消息（每个股票1条）的批量处理时间（包括数据插入，因子计算和因子结果插入）分别为180毫秒（内存表），32毫秒（分区内存表）和20毫秒（字典）。可见字典和分区内存表可显著提升因子计算效率。

使用字典或分区内存表分组存储数据有可能遇到两个问题。第一个问题关于新股。初始化的时候没有考虑到后续出现的股票，但是日内流计算的时候出现了新的股票。若使用字典，只需在使用`dictUpdate!`函数时指定初始化函数参数initFunc即可。如4.3小节的factorHandler定义中，可使用字典值的初始化函数：
```
x->array(x.type(), 0, 512).append!(x)
```
这是一个单目的lambda函数，当输入为标量或向量时，创建一个新的向量，预先分配512个元素的内存，然后将当前值扩展到新创建的数组中，最后返回这个数组。如果使用值分区的内存表，创建之后不允许动态增加分区。如果出现新股票数据，这部分数据无法插入分区内存表，也不会报异常。这种情况下，若要处理当天开始交易的新股票，只能每天交易开始前初始化流数据系统。

第二个问题是根据多个字段分组。目前字典的键值和分区内存表的分区尚不支持组合字段，解决的办法是将多个字段拼接成单个字符串字段。


### 6.2 平衡延时和吞吐量

众所周知，在其它条件给定的情况下，延时和吞吐是一对矛盾。高频因子实时计算追求消息处理的低延迟，但是如果逐条处理消息，会降低整体的吞吐量。在实践中，可以找到一个延时和吞吐量之间的平衡点。`subscribeTable`函数提供了两个可选参数throttle和batchSize，用于调节延时和吞吐量。throttle为每个消息批次处理之前最长等待时间，单位为秒，最短可设为1毫秒，用0.001表示。batchSize为每个消息批次处理之前最多的消息条数。当throttle和batchSize两个条件中有一个满足时，系统就会把尚未处理的消息合并成一个表或元组（根据参数msgAsTable的设定），发送到任务队列，由`subscribeTable`函数指定的message handler来处理。

### 6.3 并行计算

并行计算可提升系统的吞吐量，单位时间内处理更多的消息。流计算使用并行计算可分为两种情况：使用订阅系统的线程和使用DolphinDB进程全局的执行线程。

#### 6.3.1 使用订阅系统的线程池

通过配置变量subExecutors，可以指定一定数量的线程来处理订阅的消息。默认的线程数量是1个，也即所有订阅的消息都是通过这个线程来处理。当订阅线程有多个时，如何并行处理消息又有两种方式。默认的方式是按订阅来分配线程，一个订阅分配给一个线程，一个线程可以处理多个订阅。如果需要精确指定哪个线程来处理哪个订阅，可以在`subscribeTable`中指定hash参数。这种方式的优点是一个订阅的消息处理函数只被一个线程执行，不存在线程安全的问题，也不存在线程同步的问题，有很高的效率。缺点是如果各个订阅的消息数量和处理复杂度极不平衡，那么某些订阅会成为瓶颈。

订阅线程的另一种使用模式是线程池模式。在线程池模式下，所有的消息处理任务都进入同一个队列，随机分配给空闲的线程去执行。因此，同一个订阅的消息处理函数可能同时被多个线程执行，必须确保：（1）消息处理函数是线程安全的，（2）各个消息的处理在业务上是独立的。DolphinDB的所有数据结构中，只有同步字典(synchronized dictionary)和共享表(shared table)是线程安全的。如果某个数据结构可能被多个线程并发读写，必须选择上述同步字典或共享表。要启用线程池模式，需将配置参数subExecutorPooling设置为true。

#### 6.3.2 使用全局的线程池

在消息处理函数内部，如果要处理的股票比较多或者要计算的因子比较多，通过任务分解和多线程并行可以缩短处理时间。多线程并行使用当前的订阅线程和DolphinDB进程全局的线程池。全局的线程池通过配置参数localExecutors设置。

下例对4.3中的factorHandler进行并行计算改造，将因子计算和写入factors表这两个步骤封装到了一个内嵌函数中，并按照要处理的股票来进行任务划分。如果股票数目小于400，在一个任务中完成，否则分成2个任务来完成。原先4000个股票计算一次耗时约20ms，两个任务并行后耗时13ms左右。使用`cut`函数将股票切割为多个部分，并用高阶函数`ploop`实现多任务的并行。
```
def factorHandler(mutable historyDict, mutable factors, msg){
	historyDict.dictUpdate!(append!, msg.symbol, msg.ap, x->array(x.type(), 0, 512).append!(x))
	syms = msg.symbol.distinct()
	cnt = syms.size()
	f = def(syms, d, mutable factors){
		cnt = syms.size()
		signals = array(DOUBLE, cnt)
		for(i in 0:cnt)	signals[i] = factorAskPriceRatio(d[syms[i]])
		factors.tableInsert([take(now(), cnt), syms, signals])
	}
	if(cnt < 400) f(syms, historyDict, factors)
	else ploop(f{,historyDict, factors}, syms.cut(ceil(cnt/2.0)))
}
```

### 6.4 即时编译

消息处理函数若逻辑较复杂，需要用到for循环，while循环和if-else等语句，无法使用向量化运算但又对运行速度有极高要求，可使用DolphinDB中的即时编译（JIT）功能，以显著提升性能。关于即时编译功能的更多介绍，请参考[DolphinDB即时编译教程](./jit.md)。

下例中的因子，在每行数据中，需要使用前5档的报价及对应的盘口数据进行计算，且根据设定条件进行更进一步的计算。这个过 程无法向量化运算，可使用即时编译以提升性能。

```
@jit
 def sum_diff(x, y){
     return 1.0 * (x-y)/(x+y) 
 }
 
 @jit
 def wbvol(bp, bv, price, jump) {
     return exp(0.6*(bp-price)/jump) * bv
 }
 
 @jit
 def wavol(ap, av, price, jump) {
     return exp(0.6 * (price - ap)/jump) * av
 }
 
 @jit
 def factor1(ap1, ap2, ap3, ap4, ap5, av1, av2, av3, av4, av5, bp1, bp2, bp3, bp4, bp5, bv1, bv2, bv3, bv4, bv5, mp, initMP, delta){
     n = ap1.size()
     re = array(DOUBLE, n)
     for(i in 0:n){
         jump = ceil(initMP[i] * 15.0 / 100.0) / 100.0
         w_av1 = 0.0  
         w_bv1 = 0.0  
         w_av1 = wavol(ap1[i], av1[i], mp[i], jump) + wavol(ap2[i], av2[i], mp[i], jump) + wavol(ap3[i], av3[i], mp[i], jump) + wavol(ap4[i], av4[i], mp[i], jump) + wavol(ap5[i], av5[i], mp[i], jump)
         w_bv1 = wbvol(bp1[i], bv1[i], mp[i], jump) + wbvol(bp2[i], bv2[i], mp[i], jump) + wbvol(bp3[i], bv3[i], mp[i], jump) + wbvol(bp4[i], bv4[i], mp[i],jump) + wbvol(bp5[i], bv5[i], mp[i], jump)
         if(delta[i]>0){
             re[i] = sum_diff(w_bv1*1.1, w_av1)
         }else{
             re[i] = sum_diff(w_bv1, w_av1 * 1.1)
         }		
     }
     return re
 }

 //---------------------------------------------------------订阅处理函数-----------------------------------------------------
def factor1_handler(mutable d, mutable factor, msg){
     start = now(true)
     n = msg.size()
     mp = (msg.bidPrice1+msg.askPrice1)/2
     dictUpdate!(d,append!, msg.symbol, mp)
     delta = array(DOUBLE, n)
     initMP = array(DOUBLE, n)
     sym = msg.symbol
     for(i in 0:n){
         &his_mp = d[sym[i]]
         initMP[i] = his_mp[0]
         delta[i] = nullFill(his_mp.tail()-his_mp.tail(5).avg(), 0)
     }
     factorValue = factor1(msg.askPrice1, msg.askPrice2, msg.askPrice3, msg.askPrice4, msg.askPrice5, msg.askVolume1, msg.askVolume2, msg.askVolume3, msg.askVolume4, msg.askVolume5, msg.bidPrice1, msg.bidPrice2, msg.bidPrice3, msg.bidPrice4, msg.bidPrice5, msg.bidVolume1, msg.bidVolume1, msg.bidVolume1, msg.bidVolume1, msg.bidVolume1, mp, initMP, delta)
     factor.tableInsert(take(start,n), take(now(true), n), sym, take("factor1", n), factorValue)
}

def clear(){
	try{
	unsubscribeTable(, `Trade, `act_factor)
	undef(`Trade, SHARED)
	undef(`factor_result, SHARED)
	}catch(ex){}
}

login("admin","123456")
clear()
go

quotesData = loadText(yourDIR + "sampleQuotes.csv")

x=quotesData.schema().colDefs
share(streamTable(1000000:0, x.name, x.typeString), "quotes")

d = dict(STRING, ANY)
for(id in quotesData[`symbol].distinct())
     d[id]= array(DOUBLE,0,0)
dictUpdate!(d,append!, quotesData.symbol, (quotesData.bidPrice1+quotesData.askPrice1)/2)
share streamTable(100:0,`starttime`endtime`symbol`factorName`orderbook_factor_15, [LONG,LONG,SYMBOL,SYMBOL,DOUBLE]) as factor_result
subscribeTable(tableName="quotes", actionName="act_factor", offset=-1, handler=factor1_handler{d, factor_result}, msgAsTable=true);

replay(inputTables=quotesData, outputTables=quotes, dateColumn=`date, timeColumn=`time)
```


## 7. 流计算调试

### 7.1 调试消息处理函数

消息处理函数是流计算的核心。调试消息处理函数通常有两种方法：（1）单独调试消息处理函数；（2）在函数中打印日志。

消息处理函数的核心输入是消息。消息在DolphinDB中的两种形式是table或tuple。只要构造消息，就可以调试消息处理函数。如果消息处理函数比较复杂，希望单行执行，一个推荐的做法是，构造与函数参数相同名称的变量，然后逐条运行消息处理函数体内的语句。以4.3中的factorHandler函数为例，可以构造三个变量historyDict，factors和msg。
```
k=4000
syms = string(1..k)
n = 1200000
min_history = table(take(syms, n) as symbol, rand(10.0, n) as ap)
msg = table(string(1..k) as symbol, rand(10.0, k) as ap)
historyDict = dict(STRING, ANY)
historyDict.dictUpdate!(append!, min_history.symbol, min_history.ap, x->array(x.type(), 0, 512).append!(x))
factors = streamTable(100000:0, `timestamp`symbol`factor, [TIMESTAMP,SYMBOL,DOUBLE])
```

另一个方法是在消息函数中打印日志，可通过函数`writeLog`实现。从DolphinDB server的系统日志中，能够看到writeLog输出的日志。

### 7.2 历史数据回测

本教程中使用了少量数据。在投入production前，建议使用大量真实的历史数据，来回测消息处理函数，这有助于发现程序逻辑，业务逻辑，以及系统性能方面的问题。DolphinDB提供了函数`replay`与`replayDS`以回放历史数据库中的tick数据。请参考用户手册以获取更多信息。

## 8. 本教程中流数据配置

本教程中使用了单机模式的DolphinDB Server。配置文件(dolphindb.cfg)的内容如下：
```
mode=single
maxPubConnections=8
subPort=20001
persistenceDir=dbCache
subThrottle=1
subExecutors=2
localExecutor=3
```

* 单机模式下，本节点既是发布端又是订阅端。作为发布端的必需参数是maxPubConnections；作为订阅端的必需参数是subPort，指定订阅线程监听的端口号。

* 通常情况下，流数据表的数据量会随时间不断增长。为了避免内存被耗尽，生产环境下建议设定配置参数persistenceDir以启用流数据表持久化。

* 鉴于第4.1节使用了毫秒级别的throttle，需要配置subThrottle=1。

* 鉴于第5节和第6.3节提到使用订阅系统的线程池和全局线程池，配置subExecutors 和 localExecutor。

* 更多关于流数据系统的详细配置信息请参考用户手册中[单实例配置](https://www.dolphindb.cn/cn/help/DatabaseandDistributedComputing/Configuration/StandaloneMode.html)部分中“流计算配置参数”章节。

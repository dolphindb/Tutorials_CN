# DolphinDB流数据回放教程

- [DolphinDB流数据回放教程](#dolphindb%E6%B5%81%E6%95%B0%E6%8D%AE%E5%9B%9E%E6%94%BE%E6%95%99%E7%A8%8B)
  - [DolphinDB流数据基本概念](#dolphindb%E6%B5%81%E6%95%B0%E6%8D%AE%E5%9F%BA%E6%9C%AC%E6%A6%82%E5%BF%B5)
  - [replay](#replay)
  - [replayDS](#replayds)
  - [如何使用回放数据](#%E5%A6%82%E4%BD%95%E4%BD%BF%E7%94%A8%E5%9B%9E%E6%94%BE%E6%95%B0%E6%8D%AE)
  - [示例](#%E7%A4%BA%E4%BE%8B)
    - [单个内存表回放](#%E5%8D%95%E4%B8%AA%E5%86%85%E5%AD%98%E8%A1%A8%E5%9B%9E%E6%94%BE)
    - [使用data source的单表回放](#%E4%BD%BF%E7%94%A8data-source%E7%9A%84%E5%8D%95%E8%A1%A8%E5%9B%9E%E6%94%BE)
    - [使用data source的多表回放](#%E4%BD%BF%E7%94%A8data-source%E7%9A%84%E5%A4%9A%E8%A1%A8%E5%9B%9E%E6%94%BE)
    - [取消回放](#%E5%8F%96%E6%B6%88%E5%9B%9E%E6%94%BE)
    - [ETF价值计算](#etf%E4%BB%B7%E5%80%BC%E8%AE%A1%E7%AE%97)
    - [回放TAQ一天的Level1数据](#%E5%9B%9E%E6%94%BEtaq%E4%B8%80%E5%A4%A9%E7%9A%84level1%E6%95%B0%E6%8D%AE)
      - [性能指标](#%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87)

一个量化策略在用于实际交易时，处理实时数据的程序通常为事件驱动。而研发量化策略时，需要使用历史数据进行回测，这时的程序通常不是事件驱动。因此同一个策略需要编写两套代码，不仅耗时而且容易出错。在DolphinDB中，用户可将历史数据按照时间顺序以“实时数据”的方式导入流数据表中，这样就可以使用同一套代码进行回测和实盘交易。

本文介绍`replay`和`replayDS`函数，然后使用一个例子展示数据回放的全过程。

## DolphinDB流数据基本概念

DolphinDB的流数据处理框架采用发布-订阅-消费的模式。数据生产者将实时数据继续地以流的形式发布给所有数据订阅者。订阅者收到消息以后，可使用自定义函数或者DolhpinDB内置的[聚合引擎](https://github.com/dolphindb/Tutorials_CN/blob/master/stream_aggregator.md)来处理消息。DolhpinDB流数据接口支持多种语言的API，包括C++, C#, Java, 和Python等。用户可以使用这些API来编写更加复杂的处理逻辑，更好地与实际生产环境相结合。详细情况请参考[DolphinDB流数据教程](https://github.com/dolphindb/Tutorials_CN/blob/master/streaming_tutorial.md)。

## replay

```
replay(inputTables, outputTables, [dateColumn], [timeColumn], [replayRate], [parallelLevel=1])
```

`replay`函数的作用是将若干表或数据源同时回放到相应的输出表中。用户需要指定输入的数据表或数据源、输出表、日期列、时间列、回放速度以及并行度。

- inputTables: 单个表或包含若干表或数据源（见`replayDS`介绍）的元组。
- outputTables: 单个表或包含若干个表的元组，这些表通常为流数据表。输入表和输出表的个数一致，且一一对应，每对输入|输出表的schema相同。
- dateColumn, timeColumn: string, 表示输入表的日期和时间列，若不指定则默认第一列为日期列。若输入表中时间列同时包含日期和时间，需要将dateColumn和timeColumn设为同一列。回放时，系统将根据dateColumn和timeColumn的设定，决定回放的最小时间精度。在此时间精度下，同一时刻的数据将在相同批次输出。比如一张表同时有日期列和时间列，但是`replay`函数只设置了dateColumn，那么同一天的所有数据会在一个批次输出。
- replayRate: int, 表示每秒钟回放的数据条数。由于回放时同一个时刻数据在同一批次输出，因此当replayRate小于一个批次的行数时，实际输出的速率会大于replayRate。
- parallelLevel: int, 表示读取数据的并行度。当源数据大小超过内存大小的时候，需要使用`replayDS`函数将源数据划分为若干个小的数据源，依次从磁盘中读取数据并回放。指定多个读取数据的线程数可提升数据读取速度。

## replayDS

```
replayDS(sqlObj, [dateColumn], [timeColumn], [timeRepartitionSchema])
```

`replayDS`函数可以将输入的SQL查询转化为数据源，结合`replay`函数使用。其作用是根据输入表的分区以及timeRepartitionSchema，将原始的SQL查询按照时间顺序拆分成若干小的SQL查询。

- sqlObj: SQL元代码，表示回放的数据，如<select * from sourceTable>。
- dateColumn: string, 表示日期列。若不指定，默认第一列为日期列。`replayDS`函数默认日期列是数据源的一个分区列，并根据分区信息将原始SQL查询拆分为多个查询。
- timeColumn: string, 表示时间列，配合timeRepartitionSchema使用。
- timeRepartitionSchema: 时间类型向量，如08:00:00 .. 18:00:00。若同时指定了timeColumn, 则对SQL查询在时间维度上进一步拆分。


## 如何使用回放数据

回放的数据以流数据形式存在，DolphinDB支持三种方法订阅使用这些数据：

1. 在DolphinDB中订阅，并用DolphinDB脚本写一个回调函数，方便但回调函数处理性能不高。
2. 在DolphinDB中订阅，并用内置的流计算引擎来处理，譬如时间序列聚合引擎，横截面聚合引擎，异常检测引擎等，方便高效但只能处理一些相对简单的及计算任务，详见[教程](https://github.com/dolphindb/Tutorials_CN/blob/master/stream_aggregator.md)。
3. 使用流数据API来开发，效率高，并可以处理非常复杂的逻辑，但是开发成本较高，适合于开发复杂的量化交易策略。

## 示例

### 单个内存表回放

单内存表回放只需要设置输入表、输出表、日期列、时间列和回放速度即可。
```
replay(inputTable, outputTable, `date, `time, 10)
```

### 使用data source的单表回放

当单表行数过多时，可以配合使用`replayDS`进行回放。首先使用`replayDS`生成data source，本例中指定了日期列和timeRepartitionColumn。回放调用与单个内存表回放相似，但是可以指定回放的并行度。`replay`内部实现使用了[pipeline](https://www.dolphindb.cn/cn/help/pipeline.html)框架，取数据和输出分开执行。当输入为data source时，多块数据可以并行读取，以避免输出线程等待的情况。此例中并行度设置为2，表示有两个线程同时执行取数据的操作。
```
inputDS = replayDS(<select * from inputTable>, `date, `time, 08:00:00.000 + (1..10) * 3600000)
replay(inputDS, outputTable, `date, `time, 1000, 2)
```

### 使用data source的多表回放
`replay`也支持多张表的同时回放，只需要将多张输入表以元组的方式传给`replay`,并且分别指定输出表即可。这里输出表和输入表应该一一对应，每一对都必须有相同的表结构。如果指定了日期列或时间列，那么所有表中都应当有存在相应的列。

```
ds1 = replayDS(<select * from input1>, `date, `time, 08:00:00.000 + (1..10) * 3600000)
ds2 = replayDS(<select * from input2>, `date, `time, 08:00:00.000 + (1..10) * 3600000)
ds3 = replayDS(<select * from input3>, `date, `time, 08:00:00.000 + (1..10) * 3600000)
replay([ds1, ds2, ds3], [out1, out2, out3], `date, `time, 1000, 2)
```

### 取消回放

回放过程中用户若要取消回放，可以使用以下两种方式。

1. 如果`replay`函数是通过`submitJob`调用，可以使用`getRecentJob`获取`jobId`，然后用`cancelJob`取消回放。
```
getRecentJobs()
cancelJob(jobid)
```

2. 如果是直接调用，可在另外一个GUI session中使用`getConsoleJobs`获取`jobId`，然后使用`cancelConsoleJob`取消回放任务。
```
getConsoleJobs()
cancelConsoleJob(jobId)
```

### ETF价值计算
使用DolphinDB的[流数据横截面引擎](https://www.dolphindb.cn/cn/help/createCrossSectionalAggregator.html)，我们可以方便地计算ETF的内在价值。首先，我们要将历史数据通过`replayDS`和`replay`导入流表中，同时我们定义股票权重字典weights以及聚合函数`etfVal`，并使用这个函数构建横截面引擎。然后再使用`subscribeTable`将回放部分与计算部分相连接，最后在outputTable中，我们可以得到不同时间点下我们选择的股票的etf价值。

```
quotes = database("dfs://TAQ").loadTable("quotes")
sch = select name,typeString as type from  quotes.schema().colDefs
trs = cutPoints(09:30:00.001..18:00:00.001, 60)
rds = replayDS(<select * from quotes>, `date, `time,  trs);
share streamTable(100:0, sch.name,sch.type) as outQuotes
setStreamTableFilterColumn(outQuotes, `symbol)
defg etfVal(weights,sym, price) {
    return wsum(price, weights[sym])
}
weights = dict(STRING, DOUBLE)
weights[`AAPL] = 0.1
weights[`IBM] = 0.1
weights[`MSFT] = 0.1
weights[`NTES] = 0.1
weights[`AMZN] = 0.1
weights[`GOOG] = 0.5
outputTable = table(1:0, `time`etf, [TIMESTAMP,DOUBLE])
tradesCrossAggregator=createCrossSectionalAggregator("etfvalue", <[etfVal{weights}(symbol, ofr)]>, quotes, outputTable, `symbol, `perBatch)
subscribeTable(,"outQuotes","tradesCrossAggregator",-1,append!{tradesCrossAggregator},true,,,,,`AAPL`IBM`MSFT`NTES`AMZN`GOOG)
submitJob("replay_quotes", "replay_quotes_stream",  replay,  [rds],  [`outQuotes], `date, `time,1000,4)
```

### 回放美国股市一天的level1交易数据

下例中使用美国股市2007年8月17日的level1交易数据，展示数据回放过程。

```
> quotes = database("dfs://TAQ").loadTable("quotes");
> quotes.schema().colDefs;
```
| name    | typeString | typeInt |
| ------- | ---------- | ------- |
| time    | SECOND     | 10      |
| symbol  | SYMBOL     | 17      |
| ofrsiz  | INT        | 4       |
| ofr     | DOUBLE     | 16      |
| mode    | INT        | 4       |
| mmid    | SYMBOL     | 17      |
| ex      | CHAR       | 2       |
| date    | DATE       | 6       |
| bidsize | INT        | 4       |
| bid     | DOUBLE     | 16      |

```
> select top 10 * from quotes
```
| symbol | date       | time     | bid   | ofr   | bidsiz | ofrsiz | mode | ex  | mmid |
| ------ | ---------- | -------- | ----- | ----- | ------ | ------ | ---- | --- | ---- |
| A      | 2007.08.17 | 04:15:06 | 0.01  | 0     | 10     | 0      | 12   | 80  |      |
| A      | 2007.08.17 | 06:21:16 | 1     | 0     | 1      | 0      | 12   | 80  |      |
| A      | 2007.08.17 | 06:21:44 | 0.01  | 0     | 10     | 0      | 12   | 80  |      |
| A      | 2007.08.17 | 06:49:02 | 32.03 | 0     | 1      | 0      | 12   | 80  |      |
| A      | 2007.08.17 | 06:49:02 | 32.03 | 32.78 | 1      | 1      | 12   | 80  |      |
| A      | 2007.08.17 | 07:02:01 | 18.5  | 0     | 1      | 0      | 12   | 84  |      |
| A      | 2007.08.17 | 07:02:01 | 18.5  | 45.25 | 1      | 1      | 12   | 84  |      |
| A      | 2007.08.17 | 07:54:55 | 31.9  | 45.25 | 3      | 1      | 12   | 84  |      |
| A      | 2007.08.17 | 08:00:00 | 31.9  | 40    | 3      | 2      | 12   | 84  |      |
| A      | 2007.08.17 | 08:00:00 | 31.9  | 35.5  | 3      | 2      | 12   | 84  |      |


1. 一天的数据共有336,305,414条，一次性导入内存再回放会有较长延迟，还有可能导致内存溢出。因此先使用`replayDS`函数并指定参数timeRepartitionSchema，将数据按照时间戳分为62个部分。
```

sch = select name,typeString as type from  quotes.schema().colDefs
trs = cutPoints(09:30:00.001..18:00:00.001,60)
rds = replayDS(<select * from quotes>, `date, `time,  trs);
```

2. 定义输出表，一般为流数据表。然后用户可以[订阅](https://www.dolphindb.com/help/subscribeTable.html)这张输出表，使用自定义的handler进行处理，或者使用[TimeSeriesAggregator](https://www.dolphindb.com/help/createTimeSeriesAggregator.html)或[CrossSectionalAggregator](https://www.dolphindb.com/help/createCrossSectionalAggregator.html)等聚合引擎对数据进行处理。

```
share streamTable(100:0, sch.name,sch.type) as outQuotes
```

3. 开始回放：直接调用`replay`函数，或者使用`submitJob`调用。由于`replay`函数是阻塞调用，因此一般建议结合`submitJob`使用。不指定replayRate，表示以最快速度回放。并行度设置为4，表示开启4个线程并行执行取数据操作。

```
jobid = submitJob("replay_quotes","replay_quotes_stream",  replay,  [rds],  [`outQuotes], `date, `time, , 4)
```

#### 性能指标

我们在以下硬件配置下进行回放，且输出表没有任何订阅，回放336,305,414条数据耗时仅需要90~110秒左右。

主机：DELL PowerEdge R730xd

CPU：Intel Xeon(R) CPU E5-2650 v4（24核 48线程 2.20GHz）

内存：512 GB （32GB × 16, 2666 MHz）

硬盘：17T HDD （1.7T × 10, 读取速度222 MB/s，写入速度210 MB/s）

网络：万兆以太网


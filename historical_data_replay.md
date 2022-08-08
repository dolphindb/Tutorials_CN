# DolphinDB教程：历史数据回放

一个量化策略在用于实际交易时，处理实时数据的程序通常为事件驱动。而研发量化策略时，需要使用历史数据进行回测，这时的程序通常不是事件驱动。因此同一个策略需要编写两套代码，不仅耗时而且容易出错。在DolphinDB中，用户可将历史数据按照时间顺序以“实时数据”的方式导入流数据表中，这样就可以使用同一套代码进行回测和实盘交易。

DolphinDB的流数据处理框架采用发布-订阅-消费的模式，数据持续地以流的形式发布给数据订阅者。订阅者收到消息以后，可使用自定义函数或者DolphinDB内置的[聚合引擎](./stream_aggregator.md)来处理消息。DolphinDB流数据接口支持多种语言的API，包括C++, C#, Java, 和Python等。用户可以使用这些API来编写更加复杂的处理逻辑，更好地与实际生产环境相结合。详细情况请参考[DolphinDB流数据教程](./streaming_tutorial.md)。

## 1. 函数介绍

### `replay`

```
replay(inputTables, outputTables, [dateColumn], [timeColumn], [replayRate], [absoluteRate=true], [parallelLevel=1])
```

`replay`函数的作用是将若干表或数据源同时回放到相应的输出表中。用户需要指定输入的数据表或数据源、输出表、日期列、时间列、回放速度以及并行度。

- inputTables: 单个表或包含若干表或数据源（见`replayDS`介绍）的元组。
- outputTables: 可以是单个表或包含若干个表的元组，表示共享的流数据表对象，也可以是字符或字符串，表示共享流数据表的名称。
- dateColumn 与 timeColumn: 字符串, 表示输入表的日期和时间列，若均不指定则默认第一列为dateColumn。若有dateColumn，则该列必须为分区列之一；若无dateColumn，则必须指定timeColumn，且其必须为分区列之一。若输入表中时间列同时包含日期和时间，需要将dateColumn和timeColumn设为同一列。回放时，系统将根据dateColumn和timeColumn的设定，决定回放的最小时间精度。在此时间精度下，同一时刻的数据将在相同批次输出。举例来说，若timeColumn最小时间精度为秒，则每一秒的数据在统一批次输出；若只设置了dateColumn，那么同一天的所有数据会在一个批次输出。
- replayRate: 整数，表示数据回放速度。若absoluteRate为true，replayRate表示每秒钟回放的数据条数。由于回放时同一个时刻数据在同一批次输出，因此当replayRate小于一个批次的行数时，实际输出的速率会大于replayRate。若absoluteRate为false，依照数据中的时间戳加速replayRate倍回放。若replayRate未指定或为负，以最大速度回放。
- absoluteRate是一个布尔值。默认值为true，表示replayRate为每秒回放的记录数。若为false，表示依照数据中的时间戳加速replayRate倍回放。
- parallelLevel: 整数, 表示读取数据的并行度。当源数据单个分区相对内存较大，或者超过内存时，需要使用`replayDS`函数将源数据划分为若干个小的数据源，依次从磁盘中读取数据并回放。参数parallelLevel指定同时读取这些经过划分之后的小数据源的线程数，可提升数据读取速度。

### `replayDS`

```
replayDS(sqlObj, [dateColumn], [timeColumn], [timeRepartitionSchema])
```
`replayDS`函数可以将输入的SQL查询转化为数据源，结合`replay`函数使用。其作用是根据输入表的分区以及timeRepartitionSchema，将原始的SQL查询按照时间顺序拆分成若干小的SQL查询。

- sqlObj: SQL查询元代码，表示回放的数据，如<select * from loadTable("dfs://source", "source")>。SQL查询的表对象是DFS表，且至少有一个分区列为DATE类型。
- dateColumn: 字符串, 表示日期列。若不指定，默认第一列为日期列。`replayDS`函数默认日期列是数据源的一个分区列，并根据分区信息将原始SQL查询拆分为多个查询。
- timeColumn: 字符串, 表示时间列，配合timeRepartitionSchema使用。
- timeRepartitionSchema: TIME或NANOTIME类型向量，如08:00:00 .. 18:00:00。对sqlObj在每一个dateColumn分区中，在timeColumn维度上进一步拆分。

### 单个内存表回放

单内存表回放只需要设置输入表、输出表、日期列、时间列和回放速度即可。
```
replay(inputTable, outputTable, `date, `time, 10)
```

### 使用data source的单表回放

若数据表的行数过多，可使用`replayDS`函数将其划分为若干个小的数据源，再使用`replay`函数从磁盘中读取数据并回放，`replayDS`函数的返回值是一个向量，记录了划分出的多个SQL查询语句。`replay`内部实现使用了[pipeline](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/p/pipeline.html)框架，取数据与输出分开执行。当`replayDS`函数的输出作为数据源时，多块数据可以并行读取，以避免输出线程等待的情况。此例中并行度设置为2，表示有两个线程同时执行取数据的操作。
```
inputTable = loadTable("dfs://source", "source")
inputDS = replayDS(<select * from inputTable>, `date, `time, 08:00:00.000 + (1..10) * 3600000)
replay(inputDS, outputTable, `date, `time, 1000, true, 2)
```

### 多表回放

#### N对N多表回放

`replay`也支持多张表的同时回放，只需将多张输入表以元组的方式传入`replay`，并且分别指定输出表即可。这里输出表和输入表应当一一对应，每一对都必须有相同的表结构。如果指定了日期列或时间列，那么所有表中都应当存在相应的列。

```
ds1 = replayDS(<select * from input1>, `date, `time, 08:00:00.000 + (1..10) * 3600000)
ds2 = replayDS(<select * from input2>, `date, `time, 08:00:00.000 + (1..10) * 3600000)
ds3 = replayDS(<select * from input3>, `date, `time, 08:00:00.000 + (1..10) * 3600000)
replay([ds1, ds2, ds3], [out1, out2, out3], `date, `time, 1000, true, 2)
```

#### N对一异构多表回放

1.30.17/2.00.5 及以上版本，`replay`增加了N对一异构模式的多表回放。它将多个具有不同表结构的数据源回放到同一个输出表中，这里的输出表必须为异构流数据表。N对一异构模式的多表回放能够保证多表之间严格按照时间顺序进行回放，且后续对输出表进行订阅和处理时，也能够保证多个表数据之间严格按照时间顺序被消费。更详细的异构多表回放的功能介绍与应用案例见[异构回放功能应用：股票行情回放](https://gitee.com/dolphindb/Tutorials_CN/blob/master/stock_market_replay.md)。

```
ds1 = replayDS(<select * from input1>, `date, `time, 08:00:00.000 + (1..10) * 3600000)
ds2 = replayDS(<select * from input2>, `date, `time, 08:00:00.000 + (1..10) * 3600000)
ds3 = replayDS(<select * from input3>, `date, `time, 08:00:00.000 + (1..10) * 3600000)
replay([ds1, ds2, ds3], outputTable, `date, `time, 1000, true, 2)
```

### 取消回放

如果`replay`函数是通过`submitJob`调用，可以使用`getRecentJobs`获取jobId，然后用`cancelJob`取消回放。
```
getRecentJobs()
cancelJob(jobid)
```

如果`replay`函数是直接调用，可在另外一个GUI session中使用`getConsoleJobs`获取jobId，然后使用`cancelConsoleJob`取消回放任务。
```
getConsoleJobs()
cancelConsoleJob(jobId)
```

## 2. 如何使用回放的数据

回放的数据以流数据形式存在，我们可以使用以下三种方式来订阅与消费这些数据：

- 在DolphinDB中订阅，使用DolphinDB脚本自定义回调函数来消费流数据。
- 在DolphinDB中订阅，使用内置的流计算引擎来处理流数据，譬如时间序列聚合引擎、横截面聚合引擎、异常检测引擎等。DolphinDB内置的聚合引擎可以对流数据进行实时聚合计算，使用简便且性能优异。在3.2中，我们使用横截面聚合引擎来处理回放的数据，并计算ETF的内在价值。横截面聚合引擎的具体用法参见[DolphinDB用户手册](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/c/createCrossSectionalAggregator.html)。
- 第三方客户端通过DolphinDB的流数据API来订阅和消费数据。

## 3. 金融示例

### 回放level1报价数据并计算ETF内在价值

本例中使用美国股市2007年8月17日的level1报价数据，执行`replayDS`函数进行数据回放，并通过DolphinDB内置的横截面聚合引擎计算ETF内在价值。数据存放在分布式数据库"dfs://TAQ"的quotes表，以下是quotes表的结构以及数据预览。

```
quotes = loadTable("dfs://TAQ", "quotes")
quotes.schema().colDefs;
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
select top 10 * from quotes where date=2007.08.17;
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

(1) 对要进行回放的数据进行划分。回放大量数据时，若将数据全部导入内存后再回放，可能导致内存不足。可先使用`replayDS`函数并指定参数timeRepartitionSchema，将数据按照时间戳分为60个部分。

```
trs = cutPoints(09:30:00.000..16:00:00.000, 60)
rds = replayDS(<select * from quotes where date=2007.08.17>, `date, `time,  trs);
```

(2) 定义输出表outQuotes为流数据表。

```
sch = quotes.schema().colDefs
share streamTable(100:0, sch.name, sch.typeString) as outQuotes
```

(3) 定义ETF成分股票权重字典weights以及聚合函数etfVal，用于计算ETF内在价值。为简化起见，本例使用了一个虚构的由AAPL、IBM、MSFT、NTES、AMZN、GOOG这6只股票组成的的ETF。

```
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
```

(4) 创建流聚合引擎，并订阅数据回放的输出表outQuotes。订阅outQuotes表时，我们指定过滤条件，只有symbol为AAPL、IBM、MSFT、NTES、AMZN、GOOG的数据才会发布到横截面聚合引擎，减少不必要的网络开销和数据传输。

```
setStreamTableFilterColumn(outQuotes, `symbol)
outputTable = table(1:0, `time`etf, [TIMESTAMP,DOUBLE])
tradesCrossAggregator=createCrossSectionalAggregator("etfvalue", <[etfVal{weights}(symbol, ofr)]>, outQuotes, outputTable, `symbol, `perBatch)
subscribeTable(tableName="outQuotes", actionName="tradesCrossAggregator", offset=-1, handler=append!{tradesCrossAggregator}, msgAsTable=true, filter=`AAPL`IBM`MSFT`NTES`AMZN`GOOG) 
```

(5) 开始回放，设定每秒回放10万条数据，聚合引擎则会实时地对回放的数据进行消费。

```
submitJob("replay_quotes", "replay_quotes_stream", replay, rds, outQuotes, `date, `time, 100000, true, 4)
```

(6) 查看ETF内在价值。

```
//查看outputTable表内前15行的数据,其中第一列时间为聚合计算发生的时间
select top 15 * from outputTable;
```

| time                     | etf     |
| ------------------------ | ------- |
| 2019.06.04T16:40:18.476  | 14.749  |
| 2019.06.04T16:40:19.476  | 14.749  |
| 2019.06.04T16:40:20.477  | 14.749  |
| 2019.06.04T16:40:21.477  | 22.059  |
| 2019.06.04T16:40:22.477  | 22.059  |
| 2019.06.04T16:40:23.477  | 34.049  |
| 2019.06.04T16:40:24.477  | 34.049  |
| 2019.06.04T16:40:25.477  | 284.214 |
| 2019.06.04T16:40:26.477  | 284.214 |
| 2019.06.04T16:40:27.477  | 285.68  |
| 2019.06.04T16:40:28.477  | 285.68  |
| 2019.06.04T16:40:29.478  | 285.51  |
| 2019.06.04T16:40:30.478  | 285.51  |
| 2019.06.04T16:40:31.478  | 285.51  |
| 2019.06.04T16:40:32.478  | 285.51  |

## 4. 性能测试

以下对 DolphinDB database 的数据回放功能进行性能测试。测试服务器配置如下：

- 主机：DELL PowerEdge R730xd
- CPU：Intel Xeon(R) CPU E5-2650 v4（24核 48线程 2.20GHz）
- 内存：512 GB （32GB × 16, 2666 MHz）
- 硬盘：17T HDD （1.7T × 10, 读取速度222 MB/s，写入速度210 MB/s）
- 网络：万兆以太网

测试脚本如下：
```
sch = quotes.schema().colDefs
trs = cutPoints(09:30:00.000..16:00:00.001,60)
rds = replayDS(<select * from quotes where date=2007.08.17>, `date, `time,  trs);
share streamTable(100:0, sch.name, sch.typeString) as outQuotes1
jobid = submitJob("replay_quotes", "replay_quotes_stream", replay, rds, outQuotes, `date, `time, 100000, true, 4)
```

在不设定回放速率（即以最快的速率回放），并且输出表没有任何订阅时，回放331,204,031条数据耗时仅需要90~110秒。

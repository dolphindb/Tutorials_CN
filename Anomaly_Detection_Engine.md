# 流数据异常检测引擎

物联网设备（如机床、锅炉、电梯、水表、气表等等）无时无刻不在产生海量的设备状态数据和业务消息数据，这些数据的在采集、计算、分析过程中又常常涉及异常数据的检测。

针对异常数据检测的需求，DolphinDB提供基于流数据框架的异常检测引擎函数，用户只需指定异常指标，异常检测引擎就可以实时地进行异常数据检测。

## 1. 异常检测引擎框架

DolphinDB的异常检测引擎建立在流数据的发布-订阅模型之上。下例中，通过`createAnomalyDetectionEngine`创建异常检测引擎，并通过`subscribeTable`函数订阅流数据，每次有新数据流入就会按指定规则触发`append!{engine}`，将流数据持续输入聚合引擎（指定的数据表中）。异常检测引擎实时检测数据是否符合用户自定义的警报指标temp>65，如发现异常数据，将它们输出到表outputTable中。

```
share streamTable(1000:0, `time`device`temp, [TIMESTAMP, SYMBOL, DOUBLE]) as sensor
share streamTable(1000:0, `time`device`anomalyType`anomalyString, [TIMESTAMP, SYMBOL, INT, SYMBOL]) as outputTable
engine = createAnomalyDetectionEngine("engine1", <[temp > 65]>, sensor, outputTable, `time, `device, 10, 1)
subscribeTable(, "sensor", "sensorAnomalyDetection", 0, append!{engine}, true)
```

这里对异常处理引擎涉及到的一些概念做简要介绍：

- 流数据表：DolphinDB 为流式数据提供的一种特定的表对象，提供流式数据的发布功能。通过`subscribeTable`函数，其他的节点或应用可以订阅和消费流数据。

- 异常处理引擎数据源：为异常处理引擎提供"原料"的通道。`createAnomalyDetectionEngine`函数返回一个抽象表，向这个抽象表写入数据，就意味着数据进入异常处理引擎进行计算。

- 异常指标：以元代码的格式提供一组处理流数据的布尔表达式。其中可以包含聚合函数，以支持复杂的场景。

- 数据窗口：每次计算时截取的流数据窗口长度。数据窗口仅在指标中包含聚合函数时有意义。

- 输出表：异常检测引擎的输出表第一列必须是时间类型，用于存放检测到异常的时间戳，如果有指定分组列，那么第二列为分组列，之后的两列分别为int类型和string或symbol类型，用于记录异常的类型（异常指标的表达式在metrics中的下标）和异常的内容。

## 2. 异常指标

异常检测引擎中的指标均要求返回布尔值。一般是一个函数或一个表达式。当指标中包含聚合函数，必须指定窗口长度和计算的时间间隔，每隔一段时间，在固定长度的移动窗口中计算指标。异常指标一般有以下三种类型：

- 只包含列名或非聚合函数，例如`qty>10`, `lt(qty, prev(qty))`。对于这类指标，异常检测引擎会对每一条收到的数据进行计算，判断是否符合指标并决定是否输出。
- 所有出现的列名都在聚合函数的参数中，例如`avg(qty-price)>10`, `percentile(qty, 90)<100`, `sum(qty)>prev(sum(qty))`。对于这类指标，异常检测引擎只会在窗口发生移动时对数据进行聚合计算，和时间序列聚合引擎（Time Series Aggregator）类似。
- 出现的列名中，既有作为聚合函数的参数的，又有不是聚合函数参数的，例如`avg(qty) > qty`, `le(med(qty), price)`。对于这类指标，异常检测引擎会在在窗口发生移动时进行聚合计算。每一条数据到达时，使用最近一个窗口的聚合函数的返回值与非聚合函数参数的列进行计算。

## 3. 数据窗口  

当异常指标中包含聚合函数时，用户必须指定数据窗口。流数据聚合计算是每隔一段时间，在固定长度的移动窗口中进行。窗口长度由参数 windowSize 设定；计算的时间间隔由参数 step 设定。

在有多组数据的情况下，若每组都根据各自第一条数据进入系统的时间来构造数据窗口的边界，则一般无法将各组的计算结果在相同数据窗口中进行对比。考虑到这一点，系统按照参数 step 值确定一个整型的规整尺度alignmentSize，以对各组第一个数据窗口的边界值进行规整处理。

（1）当数据时间类型为MONTH时，会以第一条数据对应年份的1月作为窗口的上边界。

（2）当数据的时间类型为DATE时，不对第一个数据窗口的边界值进行规整。

（3）当数据时间精度为秒或分钟时，如MINUTE, DATETIME或SECOND类型，alignmentSize取值规则如下表：

step | alignmentSize
---|---
0~2 |2
3~5 |5
6~10|10
11~15|15
16~20|20
21~30|30
31~60|60

如果 roundTime = false, 对于step > 60, alignmentSize 都为60。 如果 roundTime = true，则alignmentSize取值规则如下表：

| step      | alignmentSize  |
| --------- | -------------- |
| 61～120   | 120（2分钟）   |
| 121~180   | 180（3分钟）   |
| 181~300   | 300（5分钟）   |
| 301~600   | 600（10分钟）  |
| 601~900   | 900（15分钟）  |
| 901~1200  | 1200（20分钟） |
| 1201~1800 | 1800（30分钟） |
| >1800     | 3600（1小时）  |

（4）当数据时间精度为毫秒时，如TIMESTAMP或TIME类型，alignmentSize取值规则如下表：

| step        | alignmentSize  |
| ----------- | -------------- |
| 0~2         | 2              |
| 3~5         | 5              |
| 6~10        | 10             |
| 11~20       | 20             |
| 21~25       | 25             |
| 26~50       | 50             |
| 51~100      | 100            |
| 101~200     | 200            |
| 201~250     | 250            |
| 251~500     | 500            |
| 501~1000    | 1000（1秒）    |
| 1001~2000   | 2000（2秒）    |
| 2001~3000   | 3000（3秒）    |
| 3001~5000   | 5000（5秒）    |
| 5001~10000  | 10000（10秒）  |
| 10001~15000 | 15000（15秒）  |
| 15001~20000 | 20000（20秒）  |
| 20001~30000 | 30000（30秒）  |
| 30001~60000 | 60000（1分钟） |

如果 roundTime = false, 对于step > 60000, alignmentSize 都为60000。 如果 roundTime = true，则alignmentSize取值规则如下表：

| step            | alignmentSize     |
| --------------- | ----------------- |
| 60001~120000    | 120000（2分钟）   |
| 120001~180000   | 180000（3分钟）   |
| 120001~300000   | 300000（5分钟）   |
| 300001~600000   | 600000（10分钟）  |
| 600001~900000   | 900000（15分钟）  |
| 900001~1200000  | 1200000（20分钟） |
| 1200001~1800000 | 1800000（30分钟） |
| \>= 1800001     | 3600000（1小时）  |

假设第一条数据时间的最小精度值为x，那么第一个数据窗口的左边界最小精度经过规整后为`x/alignmentSize\*alignmentSize`，其中`/`代表相除后取整。举例来说，若第一条数据时间为 2018.10.08T01:01:01.365，则x=365。若step=100，根据上表，alignmentSize=100，可得出规整后的第一个数据窗口左边界最小精度为365\100*100=300，因此规整后的第一个数据窗口范围为2018.10.08T01:01:01.300至 2018.10.08T01:01:01.400。

## 4. 应用场景

现模拟传感器设备采集温度。假设窗口长度为4ms，每隔2ms移动一次窗口，每隔1ms采集一次温度，规定以下异常指标：

1. 单次采集的温度超过65；
2. 单次采集的温度超过上一个窗口中75%的值；

采集的数据存放到流数据表中，异常检测引擎通过订阅流数据表来获取实时数据，并进行异常检测，符合异常指标的数据输出到另外一个表中。

实现步骤如下：

(1) 定义流数据表sensor来存放采集的数据：

```
share streamTable(1000:0, `time`temp, [TIMESTAMP, DOUBLE]) as sensor
```

(2) 定义异常检测引擎和输出表outputTable，输出表也是流数据表：

```
share streamTable(1000:0, `time`anomalyType`anomalyString, [TIMESTAMP, INT, SYMBOL]) as outputTable
engine = createAnomalyDetectionEngine("engine1", <[temp > 65, temp > percentile(temp, 75)]>, sensor, outputTable, `time, , 6, 3)
```

(3) 异常检测引擎engine订阅流数据表sensor：

```
subscribeTable(, "sensor", "sensorAnomalyDetection", 0, append!{engine}, true)
```

(4) 向流数据表sensor中写入10次数据模拟采集温度：

```
timev = 2018.10.08T01:01:01.001 + 1..10
tempv = 59 66 57 60 63 51 53 52 56 55
insert into sensor values(timev, tempv)
```

查看流数据表 sensor 的内容：

time                    | temp
-----------------------|----
2018.10.08T01:01:01.002|59
2018.10.08T01:01:01.003|66
2018.10.08T01:01:01.004|57
2018.10.08T01:01:01.005|60
2018.10.08T01:01:01.006|63
2018.10.08T01:01:01.007|51
2018.10.08T01:01:01.008|53
2018.10.08T01:01:01.009|52
2018.10.08T01:01:01.010|56
2018.10.08T01:01:01.011|55


再查看结果表 outputTable ：

time                   |anomalyType|anomalyString
-----------------------|-----------|---------------------------------------------
2018.10.08T01:01:01.003|0          |temp > 65
2018.10.08T01:01:01.003|1          |temp > percentile(temp, 75)
2018.10.08T01:01:01.005|1          |temp > percentile(temp, 75)
2018.10.08T01:01:01.006|1          |temp > percentile(temp, 75)

下面详细解释异常检测引擎的计算过程。为方便阅读，对时间的描述中省略相同的2018.10.08T01:01:01部分，只列出毫秒部分。

（1）指标`temp > 65`只包含不作为函数参数的列temp，因此会在每条数据到达时计算。模拟数据中只有003时的温度满足检测异常的指标。

（2）指标`temp > percentile(temp, 75)`中，temp列既作为聚合函数`percentile`的参数，又单独出现，因此会在每条数据到达时，将其中的`temp`与上一个窗口计算得到的`percentile(temp, 75)`比较。第一个窗口基于第一行数据的时间002进行对齐，对齐后窗口起始边界为000，第一个窗口是从000到002，只包含002一条记录，计算`percentile(temp, 75)`的结果是59，数据003到005与这个值比较，满足条件的有003和005。第二个窗口是从002到005，计算`percentile(temp, 75)`的结果是60，数据006到008与这个值比较，满足条件的有006。第三个窗口是从003到008，计算`percentile(temp, 75)`的结果是63，数据009到011与这个值比较，其中没有满足条件的行。最后一条数据011到达后，尚未触发新的窗口计算。

监控异常检测引擎的状态

```
getAggregatorStat().AnomalyDetectionEngine
```
| name    | user  | status | lastErrMsg | numGroups | numRows | numMetrics                             | metrics | snapshotDir | snapshotInterval | snapshotMsgId | snapshotTimestamp | garbageSize | memoryUsed |   |
|---------|-------|--------|------------|-----------|---------|----------------------------------------|---------|-------------|------------------|---------------|-------------------|-------------|------------|---|
| engine1 | admin | OK     |     | 1        | 10      | 2     | temp > 65, temp > percentile(temp, 75) |     |       |      -1    |     |   2,000   |8,524 |

## 5. 快照机制

快照机制可以用于系统出现异常之后，对引擎进行恢复。通过以下这个例子，可以理解snapshotDir和snapshotIntervalInMsgCount的作用。如果启用snapshot，引擎订阅流表时，handler需是appendMsg函数，需指定handlerNeedMsgId=true，用来记录快照的消息位置。

```
WORK_DIR="/home/root/WORK_DIR"
mkdir(WORK_DIR+"/snapshotDir")
enableTableShareAndPersistence(table = streamTable(10000:0,`time`sym`price`qty, [TIMESTAMP,SYMBOL,DOUBLE,INT]) , tableName="trades", cacheSize=1000000)
enableTableShareAndPersistence(table = streamTable(10000:0, `time`sym`type`metric, [TIMESTAMP,STRING,INT,STRING]), tableName = "output", cacheSize=1000000)
go

adengine = createAnomalyDetectionEngine(name="test", metrics=<[avg(qty)>1]>, dummyTable=trades, outputTable=output, timeColumn=`time, keyColumn=`sym, windowSize=10, step=10, snapshotDir=WORK_DIR+"/snapshotDir", snapshotIntervalInMsgCount=100)
subscribeTable(server="", tableName="trades", actionName="adengine",offset= 0, handler=appendMsg{adengine}, msgAsTable=true, handlerNeedMsgId=true)

def writeData(mutable t){
do{
batch = 10
tmp = table(batch:batch, `time`sym`price`qty, [TIMESTAMP, SYMBOL, DOUBLE, DOUBLE])
tmp[`time] = take(now(), batch)
tmp[`sym] = "A"+string(1..batch)
tmp[`price] = round(rand(100.0, batch), 2)
tmp[`qty] = rand(10, batch)
t.append!(tmp)
sleep(1000)
}while(true)
}

job1=submitJob("write", "", writeData, trades)
//执行一段时间后重启server

enableTableShareAndPersistence(table = streamTable(10000:0,`time`sym`price`qty, [TIMESTAMP,SYMBOL,DOUBLE,INT]) , tableName="trades", cacheSize=1000000)
enableTableShareAndPersistence(table = streamTable(10000:0, `time`sym`type`metric, [TIMESTAMP,STRING,INT,STRING]), tableName = "output", cacheSize=1000000)

select last(time) from output
>2021.03.16T11:59:10.920

select last(time) from trades
>2021.03.16T11:59:13.916

WORK_DIR="/home/root/WORK_DIR"
adengine = createAnomalyDetectionEngine(name="test", metrics=<[avg(qty)>qty]>, dummyTable=trades, outputTable=output, timeColumn=`time, keyColumn=`sym, windowSize=10, step=10, snapshotDir=WORK_DIR+"/snapshotDir", snapshotIntervalInMsgCount=100)

ofst = getSnapshotMsgId(adengine)
print(ofst)
>299

select count(*) from trades
>390

//从第300条数据开始订阅
subscribeTable(server="", tableName="trades", actionName="adengine",offset=ofst+1, handler=appendMsg{adengine}, msgAsTable=true, handlerNeedMsgId=true) 
```

## 6. createAnomalyDetectionEngine函数介绍

详见 [DolphinDB 用户手册](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/c/createAnomalyDetectionEngine.html)

## 6.总结

DolphinDB database 提供的异常检测引擎是一个轻量、使用方便的流数据引擎，它通过与流数据表合作来完成流数据的实时检测任务，能够满足物联网实时监控和预警的需求。

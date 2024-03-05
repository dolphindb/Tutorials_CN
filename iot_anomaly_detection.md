# DolphinDB 流计算引擎实现传感器数据异常检测

DolphinDB 提供了流数据表 (stream table) 和流计算引擎用于实时数据处理，包括物联网中传感器数据的异常检测。内置的异常检测引擎 (Anomaly Detection Engine) 能满足大部分异常检测场景的需求。如果异常检测逻辑复杂且较为特殊，标准化的异常检测引擎不能满足要求，用户可以用自定义消息处理函数来实现。

- [1. 应用需求](#1-应用需求)
- [2. 设计思路](#2-设计思路)
- [3.详细实现步骤](#3详细实现步骤)
	- [3.1 定义输入输出流数据表](#31-定义输入输出流数据表)
	- [3.2 创建异常检测引擎，实现传感器温度异常报警的功能](#32-创建异常检测引擎实现传感器温度异常报警的功能)
	- [3.3 创建自定义消息处理函数，实现传感器离线报警的功能](#33-创建自定义消息处理函数实现传感器离线报警的功能)
- [4. 模拟写入与验证](#4-模拟写入与验证)
- [附录](#附录)


## 1. 应用需求
一个监控系统，一秒钟采集一次数据。现有以下 2 个异常检测需求：
* 每 3 分钟内，若传感器温度出现 2 次 40 摄氏度以上并且 3 次 30 摄氏度以上，系统报警。
* 若传感器网络断开，5 分钟内无数据，系统报警。

上述的报警是指若侦测到异常，向一个流数据表中写一条记录。

## 2. 设计思路

分布式时序数据库 DolphinDB 的流计算框架目前已支持[时序聚合引擎](./stream_aggregator.md)、[横截面聚合引擎](./streaming_crossSectionalAggregator.md)、[异常检测引擎](./Anomaly_Detection_Engine.md)和自定义流计算引擎：
* 时序聚合引擎 (Time-Series Aggregator)：能对设备状态进行纵向聚合计算（按时间序列聚合），或者将多个设备状态横向聚合后再按时间聚合。时序聚合支持滑动窗口的流式计算。DolphinDB 对内置的窗口聚合函数均进行了性能优化，单核 CPU 每秒可完成近百万状态的时序聚合。
* 横截面聚合引擎 (Cross Sectional Aggregator)：是快照引擎的扩展，能对设备状态进行横向聚合计算，比如计算一批设备的温度均值。
* 异常检测引擎 (Anomaly Detection Engine)：能实时检测数据是否符合用户自定义的警报指标，如发现异常数据，将它们输出到表中，满足物联网实时监控和预警的需求。
* 自定义流计算引擎：当以上三种引擎都不能满足需求时，用户也可以使用 DolphinDB 脚本或 API 语言自定义消息处理函数。

对于第一个需求即 3 分钟内传感器温度出现异常系统即报警，可使用异常检测引擎，只需用 DolphinDB 脚本定义一个表达式描述异常逻辑即可。但第 2 个需求无法使用前三种流计算引擎，因为这三种引擎的计算均是由流入的新数据触发。若没有产生新数据，则无法触发计算。对第二个需求，可以自定义一个消息处理函数（message handler）用于计算和检测。具体实现思路是：用一个键值内存表记录每个传感器的最新采集时间。消息以一定时间间隔（比如 1 秒）进入消息处理函数。消息处理函数首先更新键值内存表，然后检查这个表中每个设备记录的最新采集时间是否超过 5 分钟，若有即报警。


## 3.详细实现步骤

### 3.1 定义输入输出流数据表

首先定义一个流数据表用于接收实时采集的传感器数据，并用[`enableTableShareAndPersistence`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/e/enableTableShareAndPersistence.html)函数把流数据表共享和持久化到硬盘上。指定 cacheSize 参数以限制内存中保留的最大数据量是 100 万行。虽然传感器设备有很多指标，因为本例只涉及温度指标，所以本例对表结构进行了简化，表结构仅包含三列，即传感器编号 deviceID，时间 ts 和温度 temperature。代码如下：
```
st=streamTable(1000000:0,`deviceID`ts`temperature,[INT,DATETIME,FLOAT])
enableTableShareAndPersistence(table=st,tableName=`sensor,asynWrite=false,compress=true, cacheSize=1000000)
```
其次定义报警输出流数据表用于异常检测引擎的输出。按照 DolphinDB 用户手册中对创建异常检测引擎函数[`createAnomalyDetectionEngine`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/c/createAnomalyDetectionEngine.html)各参数的说明，异常引擎对输出表的格式有严格要求。它的第一列必须是时间类型，用于存放检测到异常的时间戳，并且该列的数据类型需与输入表的时间列一致。如果 keyColumn(分组列) 参数不为空，那么第二列为 keyColumn。在本例中，分组列为传感器编号 deviceID。之后的两列分别为 int 类型和 string/symbol 类型，用于记录异常的类型（在 metrics 中的下标）和异常的内容。建表代码如下：
```
share streamTable(1000:0, `time`deviceID`anomalyType`anomalyString, [DATETIME,INT,INT, SYMBOL]) as warningTable
```
### 3.2 创建异常检测引擎，实现传感器温度异常报警的功能

异常检测引擎中，设置异常指标为`sum(temperature > 40) > 2 && sum(temperature > 30) > 3 `，分组列（keyColumn）为传感器编号 deviceID，数据窗口 windowSize 为 180 秒，计算的时间间隔 step 为 30 秒。这些参数如何设置可参考[异常检测引擎](./Anomaly_Detection_Engine.md)。代码如下：
```
engine = createAnomalyDetectionEngine(name="engine1", metrics=<[sum(temperature > 40) > 2 && sum(temperature > 30) > 3  ]>, dummyTable=sensor, outputTable=warningTable, timeColumn=`ts, keyColumn=`deviceID, windowSize = 180, step = 30)
subscribeTable(tableName="sensor", actionName="sensorAnomalyDetection", offset=0, handler=append!{engine}, msgAsTable=true)
```
### 3.3 创建自定义消息处理函数，实现传感器离线报警的功能

第二个需求，需要保存每个传感器的最新数据采集时间，用于判断是否已有 5 分钟未采集数据。本例采用[键值内存表](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/k/keyedTable.html)保存每个设备的最新状态，并以传感器编号 deviceID 作为主键。键值表中，基于键值的查找和更新具有非常高的效率。收到传感器数据时，用[`append!`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/a/append!.html)函数更新键值表中的记录。如果新记录中的主键值不存在于表中，那么往表中添加新的记录；如果新记录的主键值与已有记录的主键值重复时，会更新表中该主键值对应的记录。

在输出异常信息到报警输出流数据表时，异常的类型 anomalyType 因为上节异常检测引擎已用 0，所以这里设为 1。异常的内容设为空。

配置函数[`subscribeTable`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/s/subscribeTable.html)的参数 throttle 和 batchSize，可以达到批量处理消息提升性能的目的。参数 throttle 决定 handler 间隔多久时间处理一次消息，本例中设定为每秒处理一次。这里要注意当消息的数量达到 batchSize 时，即便间隔时间没到也会处理进来的消息，所以需要将 batchSize 设置为一个比较大的数。示例代码如下，其中传感器数 deviceNum 假设为 3：

```
t=keyedTable(`deviceID,100:0,`deviceID`time,[INT,DATETIME])
deviceNum=3
insert into t values(1..deviceNum,take(now().datetime(),deviceNum))
def checkNoData (mutable keyedTable, mutable outputTable, msg) {
	keyedTable.append!(select deviceID, ts from msg)
	warning = select now().datetime(), deviceID, 1 as anomalyType, "" as anomalyString from keyedTable where time < datetimeAdd(now().datetime(), -5, "m")
	if(warning.size() > 0) outputTable.append!(warning)
}
subscribeTable(tableName="sensor", actionName="noData", offset=0,handler=checkNoData{t, warningTable}, msgAsTable=true, batchSize=1000000, throttle=1)

```
## 4. 模拟写入与验证

假设 3 个传感器，一秒钟采集一次数据，第一分钟所有设备都有数据，之后第 3 个设备无数据。产生数据的代码如下：
```
def writeData(){
	deviceNum = 3
	for (i in 0:60) {
		data = table(take(1..deviceNum, deviceNum) as deviceID, take(now().datetime(), deviceNum) as ts, rand(10..41, deviceNum) as temperature)
		sensor.append!(data)
		sleep(1000)
	}
	deviceNum = 2
	for (i in 0:600) {
		data = table(take(1..deviceNum, deviceNum) as deviceID ,take(now().datetime(), deviceNum) as ts, rand(10..45,deviceNum) as temperature)
		sensor.append!(data)
		sleep(1000)
	}	
}
submitJob("simulateData", "simulate sensor data", writeData)
```
运行后，查询报警输出表 warningTable，可看到结果如下：

time                   |deviceID |anomalyType|anomalyString
--------------------|-----------|-----------|---------------------------------------------
2020.08.20T11:42:30 |1          | 0   |sum(temperature > 40) > 2 && sum(temperature > 30) > 3
2020.08.20T11:42:30	|3          | 0   |sum(temperature > 40) > 2 && sum(temperature > 30) > 3
2020.08.20T11:43:30	|2	        | 0	  |sum(temperature > 40) > 2 && sum(temperature > 30) > 3
2020.08.20T11:47:26 |3          | 1   |

## 附录

[测试代码](./script/alarm.txt)
# DolphinDB 流计算在物联网的应用：实时检测传感器状态变化

工业物联网领域，能否对从传感器采集到的包括湿度、温度、压力、液位、流速等多方面的海量数据进行快速的实时处理，对各种工业智能制造应用至关重要。DolphinDB 提供了流数据表 (stream table) 和流计算引擎用于实时数据处理，助力智能制造。 [DolphinDB 流计算引擎实现传感器数据异常检测](https://gitee.com/dolphindb/Tutorials_CN/blob/master/iot_anomaly_detection.md)一文介绍了怎么用内置的异常检测引擎 (Anomaly Detection Engine) 和自定义计算引擎实现异常检测的需求。目前 DolphinDB 内置了更多的计算引擎，本文将介绍如何用响应式状态引擎和会话窗口引擎实现传感器状态变化的实时监测。

- [DolphinDB 流计算在物联网的应用：实时检测传感器状态变化](#dolphindb-流计算在物联网的应用实时检测传感器状态变化)
	- [1. 应用需求](#1-应用需求)
	- [2. 实验环境准备](#2-实验环境准备)
	- [3. 设计思路](#3-设计思路)
	- [4. 实现步骤](#4-实现步骤)
		- [4.1 定义输入输出流数据表](#41-定义输入输出流数据表)
		- [4.2 创建响应式状态引擎实现传感器状态变化实时监测](#42-创建响应式状态引擎实现传感器状态变化实时监测)
		- [4.3 创建会话窗口引擎实现传感器丢失数据实时报警](#43-创建会话窗口引擎实现传感器丢失数据实时报警)
		- [4.4 订阅流数据](#44-订阅流数据)
		- [4.5 从 MQTT 服务器接收数据](#45-从-mqtt-服务器接收数据)
	- [5. 模拟写入与验证](#5-模拟写入与验证)
	- [6. 总结](#6-总结)
	- [附录](#附录)

## 1. 应用需求

假定有一个监控系统，对所有传感器每 5 秒钟采集 1 次数据，并将采集后的数据以 json 格式写入 mqtt 服务器，典型样本数据如下所示：

```
tag	               ts	                    value
motor.C17156B.m1	2022.11.05T15:32:02.750	 1
motor.C17156C.m1	2022.11.05T15:32:05.265	 2
motor.C17156G.m146	2022.11.05T15:32:05.734	 0
motor.C17156B.m1	2022.11.05T15:32:07.750	 1
motor.C17156C.m1	2022.11.05T15:32:10.265	 2
motor.C17156G.m146	2022.11.05T15:32:10.734	 0
motor.C17156B.m1	2022.11.05T15:32:12.750	 1
motor.C17156C.m1	2022.11.05T15:32:15.265	 2
motor.C17156G.m146	2022.11.05T15:32:15.734	 0
motor.C17156B.m1	2022.11.05T15:32:17.750	 1
```

其中 tag 是传感器标签，ts 是采集时间戳，value 是设备测量值，取值范围是 0~4，分别表示设备的 5 种状态（0 表示待运行，1 表示运行，2 表示节能，3 表示阻塞，4 表示过载）。现有以下实时检测需求：

* 传感器状态变化监控：当监测到当前记录的传感器测量值与该传感器前一条记录的测量值不一样，即状态有变化时，输出这条记录，若不变就丢弃这条记录。
* 传感器数据丢失告警：若传感器数据丢失，即 30 秒钟内某个传感器没有采集到数据，系统告警。报警方式为，在侦测到传感器数据采集异常后，向一个流数据表中写一条记录。

## 2. 实验环境准备

实验环境配置如下：

* 服务器环境

    * CPU 类型：Intel(R) Core(TM) i7-6700HQ CPU @ 2.60GHz
    * 逻辑 CPU 总数：4
    * 内存：32 GB
    * OS：64 位 Ubuntu 20.04

* DolphinDB server 部署

    * server 版本：2.00.8 Linux 64 JIT，社区版
    * 部署模式：单节点模式

* DolphinDB GUI：1.30.14 版本

* MQTT 服务器：[mosquitto-2.0.15](https://mosquitto.org/download/)

## 3. 设计思路

DolphinDB 的流计算框架目前已提供时序聚合引擎、横截面聚合引擎、异常检测引擎、会话窗口引擎和响应式状态引擎等 10 余种计算引擎应对不同计算场景。本文主要介绍如何用响应式状态引擎和会话窗口引擎实现传感器状态变化的实时监测。

* 会话窗口引擎

会话窗口可以理解为一个活动阶段（数据产生阶段），其前后都是非活动阶段（无数据产生阶段）。会话窗口引擎与时间序列引擎极为相似，它们计算规则和触发计算的方式相同。不同之处在于时间序列引擎具有固定的窗口长度和滑动步长，但会话窗口引擎的窗口不是按照固定的频率产生的，其窗口长度也不是固定的。会话窗口引擎以引擎收到的第一条数据的时间戳作为第一个会话窗口的起始时间。会话窗口收到某条数据之后，若在指定的等待时间内仍未收到下一条新数据，则（该数据的时间戳 + 等待时间）是该窗口的结束时间。窗口结束后收到的第一条新数据的时间戳是新的会话窗口的起始时间。

* 响应式状态引擎

DolphinDB 流数据引擎所计算的因子可分为无状态因子与有状态因子。无状态因子仅根据最新一条数据即可完成计算，不需要之前的数据，亦不依赖之前的计算结果。有状态因子计算除需要最新的数据，还需要历史数据或之前计算得到的中间结果，统称为状态。因此有状态因子计算需要存储状态，以供后续因子计算使用，且每次计算都会更新状态。响应式状态引擎每输入一条数据都将触发一条结果输出，因此输入和输出数据量一致。响应式状态引擎的算子中只能包含向量函数，DolphinDB 针对生产业务中的常见状态算子（滑动窗口函数、累积函数、序列相关函数和 topN 相关函数等）进行了优化，大幅提升了这些算子在响应式状态引擎中的计算效率。

对于第一个需求即传感器状态变化，可使用响应式状态引擎。响应式状态引擎可以设置过滤条件，通过过滤条件判断当前记录的状态值与前一条记录相同，只有符合过滤条件的结果才被输出。

对于第二个需求即检测是否有数据丢失，可使用会话窗口引擎。对于每个传感器，会话窗口收到该传感器某条数据之后，若在 30 秒内仍未收到该传感器的下一条新数据，则认为该窗口结束，输出报警。

## 4. 实现步骤

### 4.1 定义输入输出流数据表

首先，定义一个流数据表用于接收实时采集的传感器数据，表结构包含三列，即标签 tag、时间 ts 和标签值 value。通过 [enableTableShareAndPersistence](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/e/enableTableShareAndPersistence.html) 函数共享流数据表并持久化到硬盘上。通过 cacheSize 参数将内存中可保存的最大数据量设定为 10 万行。代码如下：

```
stream01=streamTable(100000:0,`tag`ts`value,[SYMBOL,TIMESTAMP, INT])
enableTableShareAndPersistence(table=stream01,tableName=`inputSt,asynWrite=false,compress=true, cacheSize=100000)
```

其次，定义响应式状态引擎的输出表。引擎的输出表可以是内存表或分布式表。本文定义如下所示流数据表 outputSt1 为满足第一个需求的跟踪状态变化的输出表，并参考 DolphinDB 用户手册中 [createReactiveStateEngine](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/c/createReactiveStateEngine.html) 各参数的设置说明完成对输出表的定义。根据 keyColumn(分组列) 的设置，输出表的前几列必须和 keyColumn 设置的列及其顺序保持一致，后面是计算结果列。本例的 keyColumn 为 tag，计算结果列为 ts 和 value，与输入表一致。建表代码如下：

```
out1 =streamTable(10000:0,`tag`ts`value,[SYMBOL,TIMESTAMP, INT])
enableTableShareAndPersistence(table=out1,tableName=`outputSt1,asynWrite=false,compress=true, cacheSize=100000)
```

最后，定义用于告警信息输出的流数据表 outputSt2，以满足第二个场景需求。参考 DolphinDB 用户手册中 [createSessionWindowEngine](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/c/createSessionWindowEngine.html) 各参数的设置说明完成对输出表的定义。它的第一列必须是时间类型，其时间为各个窗口的起始时刻或者结束时刻。如果 keyColumn (分组列) 参数不为空，则其后几列和 _keyColumn_ 设置的列及其顺序保持一致。最后为计算结果列，可为多列，在本例中，仅记录丢失数据前最后一条记录的标签测量值。建表代码如下：

```
out2 =streamTable(10000:0,`ts`tag`lastValue,[TIMESTAMP,SYMBOL, INT])
enableTableShareAndPersistence(table=out2,tableName=`outputSt2,asynWrite=false,compress=true, cacheSize=100000)
```

### 4.2 创建响应式状态引擎实现传感器状态变化实时监测

响应式状态引擎中，设置分组列（keyColumn）为传感器标签 tag，2 个计算指标为 `ts 和 value`，表示原样输出。需要注意的是 filter 参数的设置：`<value!=prev(value) && prev(value)!=NULL>`，这里以元代码的形式表示过滤条件。只有符合过滤条件的结果，即 value 值与该分组的上一个 value 值不相同才会被输出到通过 outputTable 设置的输出表，其中 `prev(value)!=NULL` 表示不输出每个分组的第一条记录。参考 DolphinDB 用户手册中 createReactiveStateEngine 页面内容完成对其他参数的设置。代码如下：

```
reactivEngine = createReactiveStateEngine(name=`reactivEngine, metrics=<[ts, value]>, dummyTable=stream01,
      outputTable= outputSt2,keyColumn= "tag",filter=<value!=prev(value) && prev(value)!=NULL>)
```

### 4.3 创建会话窗口引擎实现传感器丢失数据实时报警

会话窗口引擎中，设置 keyColumn（分组列）为传感器标签 tag，timeColumn（时间列）为 ts。检测需求是 30 秒内无数据，所以 sessionGap 为 30000（单位为毫秒，同 ts 列），表示收到某条数据后经过该时间的等待仍无新数据到来，就终止当前窗口。设置 useSessionStartTime 为 false，表示输出表中的时刻为数据窗口结束时刻，即每个窗口中最后一条数据的时刻 + *sessionGap*。参考 DolphinDB 用户手册中 [createSessionWindowEngine](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/c/createSessionWindowEngine.html) 页面内容完成对其他参数的设置。代码如下：

```
swEngine = createSessionWindowEngine(name = "swEngine", sessionGap = 30000, metrics = < last(value)>,
	dummyTable = stream01, outputTable = outputSt1, timeColumn = `ts, keyColumn=`tag,useSessionStartTime=false)
```

### 4.4 订阅流数据

本例定义了 handler 处理函数 process，把收到的流数据分别写入上述会话窗口引擎和响应式状态引擎，代码如下：

```
def process(mutable  engine1,mutable  engine2,msg){
	engine1.append!(msg)
	engine2.append!(msg)
}
subscribeTable(tableName="inputSt", actionName="monitor", offset=0,
		handler=process{swEngine,reactivEngine}, msgAsTable=true)
```

注意：

1. 本例没启用快照（snapshot）机制。为了满足生产环境业务持续性的需要，DolphinDB 内置的流式计算引擎包括会话窗口引擎、响应式状态引擎均支持快照输出。若需要启用快照机制，则引擎创建时需要指定两个额外的参数 snapshotDir 和 snapshotIntervalInMsgCount。snapshotDir 用于指定存储快照的目录。snapshotIntervalInMsgCount 指定处理多少条消息后产生一个快照。此外，引擎启用快照机制，调用 [subscribeTable](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/FunctionReferences/s/subscribeTable.html) 函数订阅流数据也需相应的修改：

* 首先，必须指定消息的 offset。
* 其次，handler 必须使用 `appendMsg` 函数。`appendMsg` 函数接受两个参数，msgBody 和 msgId。
* 再次，参数 handlerNeedMsgId 必须指定为 true。
* 更详细的说明请参阅 [流数据教程](https://gitee.com/dolphindb/Tutorials_CN/blob/master/streaming_tutorial.md#43-%E5%BF%AB%E7%85%A7%E6%9C%BA%E5%88%B6) 第 4.3 节或用户手册中会话窗口引擎、响应式状态引擎的说明。

2. 若设备极多，数据采集频率很高，可能需要处理大量消息。这时可在 DolphinDB 消息订阅函数 [subscribeTable](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/FunctionReferences/s/subscribeTable.html) 中指定可选参数 filter 与 hash，让多个订阅客户端并行处理消息。相关详细说明请参阅 [流数据教程](https://gitee.com/dolphindb/Tutorials_CN/blob/master/streaming_tutorial.md#42-%E5%B9%B6%E8%A1%8C%E5%A4%84%E7%90%86) 第 4.2 节或用户手册中 [subscribeTable](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/FunctionReferences/s/subscribeTable.html) 和 [setStreamTableFilterColumn](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/CommandsReferences/s/setStreamTableFilterColumn.html) 的说明。

### 4.5 从 MQTT 服务器接收数据

DolphinDB 提供了 [MQTT](https://gitee.com/dolphindb/DolphinDBPlugin/tree/release200/mqtt) 插件用于订阅 MQTT 服务器的数据。DolphinDB server 2.00.8 linux 64 JIT 版本已包含 MQTT 插件在 server/plugins/mqtt 目录下，不用下载插件即可直接加载使用。用户可以使用 `mqtt::subscribe` 从 MQTT 服务器订阅数据，在订阅时需要数据格式解析函数，目前插件提供了 json 和 csv 格式的解析函数，本例使用 `mqtt::createJsonParser` 解析 json 格式数据。示例代码如下：

```
loadPlugin(getHomeDir()+"/plugins/mqtt/PluginMQTTClient.txt")// 也可用 preloadModules=plugins::mqtt 自动加载
go
sp = mqtt::createJsonParser([SYMBOL,TIMESTAMP, INT], `tag`ts`value)
mqtt::subscribe(host, port, topic, sp, inputSt)
```

## 5. 模拟写入与验证

附录中的样本文件包含了 46 个 tag 的约 18 分钟的数据，共 9985 条记录，下列代码可把样本文件中的数据推送并写入 MQTT 服务器：

```
	t=loadText(getHomeDir()+"/deviceState.csv")// 加载样本文件到内存，目录需根据实际情况修改
	f = createJsonFormatter()//json 格式打包函数
	batchsize=100 // 每批打包 100 行记录发往 MQTT 服务器
	submitJob("submit_pub1", "submit_p1", publishTableData{host,topic,f, batchsize,t})
```

运行后，outputSt1 产生 409 条记录，用下列代码可验证结果是否正确：

```
	t=loadText(getHomeDir()+"/deviceState.csv")
	t1=select tag,ts,value from t context by tag  having deltas(value)!=0 and prev(value)!=NULL
	t2=select * from outputSt1 order by tag
	assert eqObj(t1.values(),t2.values())==true
```

outputSt2 产生如下所示 2 条记录：

```
ts	tag	lastValue
2022.11.05T15:45:37.750	motor.C17156B.m1	2
2022.11.05T15:49:52.750	motor.C17156B.m1	0
```

通过下列示例代码可发现样本中有 2 次丢了 30 秒以上的数据：

```
	t=loadText(getHomeDir()+"/deviceState.csv")
	select tag,ts,prev(ts),deltas(ts) from t context by tag  having deltas(ts)>30000
```

执行后结果：

```
tag	ts	prev_ts	deltas_ts
motor.C17156B.m1	2022.11.05T15:45:47.750	2022.11.05T15:45:07.750	40,000
motor.C17156B.m1	2022.11.05T15:50:07.750	2022.11.05T15:49:22.750	45,000
```

告警都在 prev\_ts 30 秒后发生，符合预期。

注意：为简化调试，也可不经过 MQTT 服务器和插件，直接通过回放的方式写入流表，回放的示例代码如下供参考：

```
t=loadText(getHomeDir()+"/deviceState.csv")
replay(t, inputSt, `ts, `ts)
```

本文中使用的代码样例可见于附件中的 deviceState.txt。

## 6. 总结

DolphinDB 内置的流数据框架用于流数据的发布、订阅、预处理、实时内存计算、复杂指标的滚动窗口计算、滑动窗口计算、累计窗口计算等，运行高效、使用便捷。

本文基于 DolphinDB 流数据处理框架，提供了一种实时检测设备数据状态变化的低延时解决方案，在实现设备状态变化检测、数据丢失告警、MQTT 服务器数据订阅等需求的过程中，可发现 DolphinDB 能大大降低开发难度，提高开发效率。

## 附录

* 样本文件：[deviceState.csv](data/DolphinDB_streaming_application_in_IOT/deviceState.csv)
* 案例代码：[deviceState.txt](data/DolphinDB_streaming_application_in_IOT/deviceState.txt)




### 背景

随着物联网技术的发展，工业企业的传感器设备越来越完善，能够更准确更实时地为生产企业提供大量的设备运转数据。

企业可以利用这些数据做预警和数据分析，提高生产效率，降低残次品率和设备损耗。

但是这类设备产生的实时数据与管理信息系统产生的数据在量级上有极大差异，管理信息系统通常每天产生的数据多则上万，少则几十几百条记录，而物联网设备则是以毫秒级的速度产生数据，当大量的设备以毫秒级的速度不间断的上传数据，每天的数据量通常会以亿为单位来计算，在这种情况下，传统的OLTP的数据库，比如Sql Server,Oracle,Mysql根本无法同时响应数据写入和查询的请求。

而时下流行的Hadoop+Spark大数据处理系统，由于其初期的设计只是为了分布式的处理海量非结构化的静态数据，所以对于这种物联网的实时、结构化的高频流数据并不能很好的支持。

所以，现在这些海量的设备运转数据只能作为冷数据简单的备份在磁盘上，不仅无法达成实时预警指导生产的功能，甚至连事后分析也非常的困难。

**而DolphinDB时序数据库正是为实时分析和处理海量数据而设计的。**

### 案例

在工厂环境里，很多设备的运转对于温度是非常敏感的，每当设备的温度发生异常时，往往需要系统以秒级的速度来提供预警，使得管理者能够及时介入和调整，若预警时间太迟轻则产出残次品重则导致设备损坏，所以系统的运行指标要求是必须要达到秒级实时响应。

这里我们设计如下的场景：

- 企业的生产车间内有10000个传感设备，每个设备每10ms上传三个维度的温度数据，系统通过一个前端Grafana平台来展示实时的温度数据。

* 在实际运转中，为了避免一些异常数据导致错误的预警，我们需要对监测数据做移动平均运算，过滤掉一些异常数据。

* 因为设备的管理者需要在最快的时间内掌握温度变化，所以前端展示界面每秒查询一次实时运算的结果并刷新温度变化趋势图。

对于传统的信息系统来说，这里有几个难点需要突破
 
 * 数据吞吐量：按照上述场景，每个维度的数据占8Byte(Double)来计算，数据流入的速度是192mbps,这还只是单点三个维度的数据，当维度数据增长到几百乃至上千时，这个流入速度任何传统的单点系统是无法承载的。
 * 实时运算：高频流数据的实时运算，流行的应对流数据实时运算的做法需要采用内存消息队列结合第三方系统订阅来处理，而当流数据频率极高时，这样的方式会导致数据频繁的在系统间迁移，使得响应性能急剧下降。
 * 需要在高频流数据接收、实时运算和保存分布式数据的同时，实时响应前端展示平台的每秒轮询。对于传统数据库平台，在密集地往磁盘写入数据同时，根本无法满足再从磁盘load数据响应查询的需求。

而DolphinDB的架构设计阶段就已经考虑到了上述问题
* DolphinDB分布式数据库支持将流数据通过多结点多线程写入DFS系统,并且支持统一查询，这个特性使得系统数据吞吐量可以近乎无限的扩展；
* DolphinDB可以支持在内存中对数据做实时的本地化运算，无需将数据迁移到第三方，从而极大提升实时运算的响应性能；
* DolphinDB是内存数据库，前端的轮询指令直接可以在内存中执行，无需从磁盘加载数据，而内存的IO性能完全可以支持客户端秒级轮询。

### 实施步骤

1. 集群架设

我们首先要为上述的场景部署一个DolphinDB集群，单机多节点集群的部署参照: 
    https://github.com/dolphindb/Tutorials_CN/blob/master/single_machine_cluster_deploy.md

2. 系统配置

根据案例设计中提到的特性，我们需要在集群中启用以下配置：
* 启动 DFS 分布式文件系统 : enableDFS = 1
* 启用 流数据持久化 : 指定 persistenceDir 目录
* 启用 Streaming发布和订阅：指定maxPubConnections和subPort

3. 具体配置示例 

配置文件里启用node1的订阅功能，使用subPort = 8089做为订阅端口。
```
cluster.node
* node1.subPort = 8089
* maxPubConnections = 64
* persistenceDir = /home/persistenceDir/

controller.cfg

* enableDFS = 1
```
4. 表结构及脚本设计

数据上传过程中，DolphinDB将高频数据流接收到sensorInfoTable表中，并会每1秒钟对数据进行一次回溯1分钟求均值运算，将运算结果保存到一个新的数据流表aggregateResult中。

* 高频表字段定义如下

字段名称 | 字段说明
---|---
hardwareId | 设备编号
ts | 采集时间(timestamp)
temp1 | 1号温度传感器数据
temp2 | 2号温度传感器数据
temp3 | 3号温度传感器数据

* 低频表字段定义

字段名称 | 字段说明
---|---
time | 窗口最后一条记录时间(timestamp)
hardwareId | 设备编号
tempavg1 | 1号传感器均值

* 模拟数据生成脚本

```
login("admin","123456")

n = 1000000;
tableSchema = streamTable(n:0,`hardwareId`ts`temp1`temp2`temp3,[INT,TIMESTAMP,DOUBLE,DOUBLE,DOUBLE])
share tableSchema as sensorInfoTable
enableTablePersistence(sensorInfoTable, true, false, 1000000)

def writeData(){
	hardwareNumber = 10000
	for (i in 0:10000) {
		data = table(take(1..hardwareNumber,hardwareNumber) as hardwareId ,take(now(),hardwareNumber) as ts,rand(20..41,hardwareNumber) as temp1,rand(30..71,hardwareNumber) as temp2,rand(70..151,hardwareNumber) as temp3)
		sensorInfoTable.append!(data)
		sleep(10)
	}
}
```

* 监测指标实时运算
 
```
share streamTable(1000000:0, `time`hardwareId`tempavg1`tempavg2`tempavg3, [TIMESTAMP,INT,DOUBLE,DOUBLE,DOUBLE]) as aggregateResult
metrics = createStreamAggregator(60000,1000,<[avg(temp1),avg(temp2),avg(temp3)]>,sensorInfoTable,aggregateResult,`ts,`hardwareId,2000)
subscribeTable(, "sensorInfoTable", "metric_engine", -1, append!{metrics},true)
```

* 高频数据的保存
在对流数据进行实时运算的同时，DolphinDB通过订阅高频流数据，把原始数据保存到分布式数据库中。
```
if(exists("dfs://iotDemoDB")){
	dropDatabase("dfs://iotDemoDB")
}
db1 = database("",RANGE,0..10*100)
db2 = database("",VALUE,2018.08.14..2018.12.20) //请输入实际时间
db = database("dfs://iotDemoDB",COMPO,[db1,db2])
dfsTable = db.createPartitionedTable(tableSchema,"sensorInfoTable",`hardwareId`ts)
subscribeTable(, "sensorInfoTable", "save_to_db", -1, append!{dfsTable}, true, 1000000,10)
```

* 启动整个Demo

```
    submitJob("simulateData", "simulate sensor data", writeData)
```

5. 前端展示配置

- Grafana系统配置

要观察实时的数据，我们需要一个支持时序数据展示的前端平台，DolphinDB和Grafana做了数据对接。
 
具体配置grafana 请参考 :  
https://www.github.com/dolphindb/grafana-datasource/blob/master/README.md

* 轮询脚本配置
* 
  在参照教程添加好数据源之后，在 Metics Tab 脚本输入框中输入：
```
select gmtime(time) as time, tempavg1 from aggregateResult where hardwareId = 1
```
(这段脚本是选出1号传感器的过去一分钟的平均温度)

### 系统性能观测及调整

1. 集群的配置： 此案例里我们使用一台i7,16G内存的工作站，部署一个单机四节点的集群
2. 数据量：10000个设备，以每个点3个维度、10ms每次的频率生成数据，以每个维度8个Byte(Double类型)计算，数据流速是 10000 * 1000/10 *3 * 8 * 8 = 24Mbps,持续100秒，保存的总数据量是2.4G。
3. 运行结果：在运行完成后，记录CPU最高占用为17.3%, 内存最大占用6.04G

**由结果可以看出，DolphinDB面对物联网场景，即使在普通工作站上也可以胜任高频数据流的接收、实时分析计算、分布式存储等一系列并行任务。**

* 如何观察高频数据流是否被及时的处理？
```
select * from getStreamingStat().subWorkers:
```
观察当前streaming的发布队列和消费队列的数据，用于判断数据的消费速度是否跟得上流入速度。
当流入数据积压并且没有下降的趋势，但是cpu资源还有余力时，可以适当缩短聚合计算的时间间隔，加快数据消费的速度。

### FAQ
* 如何观察数据是否被保存到分布式数据库？
1. 可以通过集群管理web界面上的Dfs Explorer来观察
2. 可以通过dfsTable = database("dfs://iotDemoDB").loadTable("sensorInfoTable");select top 100 from dfsTable 来观察表内的实时记录

* 发现数据流并没有保存到分布式数据库？
请确认
```
db2 = database("",VALUE,2018.08.14..2018.12.20) //请输入实际时间
```
这句脚本里的开始结束时间是否包含了当前时间，如果没有，需要调整结束时间参数来包含当前时间。

# DolphinDB在工业物联网的应用

### 1. 工业物联网的数据特点和痛点

随着物联网技术的发展，工业企业的传感器设备越来越完善，能够更准确更实时地为生产企业提供大量的设备运转数据。

企业可以利用这些数据做预警和数据分析，提高生产效率，降低残次品率和设备损耗。

但是这类设备产生的实时数据与管理信息系统产生的数据在量级上有极大差异，管理信息系统通常每天产生的数据多则上万，少则几十几百条记录，而物联网设备则是以毫秒级的速度产生数据，当大量的设备以毫秒级的速度不间断的上传数据，每天的数据量通常会以亿为单位来计算，在这种情况下，传统的OLTP的数据库，比如Sql Server,Oracle,Mysql根本无法同时响应数据写入和查询的请求。

而时下流行的Hadoop+Spark大数据处理系统，由于其初期的设计只是为了分布式的处理海量非结构化的静态数据，所以对于这种物联网的实时、结构化的高频流数据并不能很好的支持。

对于传统的信息系统来说，这里有几个难点需要突破：
 
 * 数据吞吐量：物联网数据的流入速度轻易就能达到几百乃至上千的MBps，这是任何传统的单点系统无法承载的。
 * 实时运算：高频流数据的实时运算，当下流行的应对流数据实时运算的做法需要采用内存消息队列结合第三方系统订阅来处理，而当流数据频率极高时，这样的方式会导致数据频繁的在系统间迁移，使得响应性能急剧下降。
 * 需要在高频流数据接收、实时运算和保存分布式数据的同时，实时响应前端展示平台的每秒轮询。对于传统数据库平台，在密集地往磁盘写入数据同时，根本无法满足再从磁盘load数据响应查询的需求。

所以，现在这些海量的设备运转数据只能作为冷数据简单的备份在磁盘上，不仅无法达成实时预警指导生产的功能，甚至连事后分析也非常的困难。

**而DolphinDB时序数据库正是为实时分析和处理海量数据而设计的。**

### 2. DolphinDB的工业物联网解决方案

* DolphinDB分布式数据库支持将流数据通过多结点多线程写入DFS系统,并且支持统一查询，这个特性使得系统数据吞吐量可以近乎无限的扩展；
* DolphinDB可以支持在内存中对数据做实时的本地化运算，无需将数据迁移到第三方，从而极大提升实时运算的响应性能；
* DolphinDB是内存数据库，前端的轮询指令直接可以在内存中执行，无需从磁盘加载数据，而内存的IO性能完全可以支持客户端秒级轮询。

### 3. 案例综述

* 企业的生产车间内总共有1000个传感设备，每个设备每10ms采集一次数据，为简化demo脚本，假设采集的数据仅有三个维度，均为温度，系统通过前端Grafana平台来展示实时的温度数据。

* 在实际运转中，为了避免一些异常数据导致错误的预警，我们需要对监测数据做移动平均运算，过滤掉一些异常数据，这个运算每两秒钟要进行一次。

* 因为设备的管理者需要在最快的时间内掌握温度变化，所以前端展示界面每秒查询一次实时运算的结果并刷新温度变化趋势图。
在工厂环境里，很多设备的运转对于温度是非常敏感的，每当设备的温度发生异常时，往往需要系统以秒级的速度来提供预警，使得管理者能够及时介入和调整，若预警时间太迟轻则产出残次品重则导致设备损坏，所以系统必须要达到秒级实时响应。

### 4. 案例实施

4.1 系统的功能模块设计
	
针对上述的案例，我们首先要启用DolphinDB的分布式数据库，创建一个命名为iotDemoDB的分布式数据库用于保存实时数据，为了利于日后的过期数据清理，采用日期作为第一个维度分区，设备编号作为第二个维度分区；

启用流数据发布和订阅功能，可以订阅高频数据流做实时运算处理，也可以将实时运算结果再次发布出去；

为了避免高频数据流临时积压导致内存不足，我们对流数据启用持久化处理，每累计满100万行数据进行一次数据持久化，这样内存中保留的高频数据记录永远只保留100万以内，保证内存使用率稳定；

系统设计createStreamingAggregator函数对高频数据做实时运算，我们在案例里指定运算窗口是1分钟，每2秒钟运算一次过往1分钟的温度均值，然后将运算结果保存到低频数据表中供前端轮询；

部署前端Grafana平台展示运算结果的趋势图，设置每1秒钟轮询一次DolphinDB Server并刷新展示界面。

4.2 服务器部署

在本次demo里，为了使用分布式数据库，我们需要使用一个单机多节点集群，可以参考[单机多节点集群部署指南](https://github.com/dolphindb/Tutorials_CN/blob/master/single_machine_cluster_deploy.md)。这里我们配置了1个controller+1个agent+4个datanode的集群，下面列出主要的配置文件内容供参考：

cluster.nodes
```
localSite,mode
localhost:8701:agent1,agent
localhost:8081:node1,datanode
localhost:8083:node2,datanode
localhost:8082:node3,datanode
localhost:8084:node4,datanode
```
由于DolphinDB系统默认是不启用Streaming模块功能的，所以我们需要通过在cluster.cfg里做显式配置来启用它，因为本次demo里使用的数据量不大，为了避免demo复杂化，所以这里只启用了node1来做数据订阅

cluster.cfg
```
maxMemSize=2
workerNum=4
persistenceDir=dbcache
maxSubConnections=4
node1.subPort=8085
maxPubConnections=4
```
实际生产环境下，建议使用多物理机集群，可以参考 [多物理机集群部署指南](https://github.com/dolphindb/Tutorials_CN/blob/master/multi_machine_cluster_deploy.md)

4.3 实现步骤

首先我们定义一个sensorTemp流数据表用于接收实时采集的温度数据，我们使用enableTablePersistence函数对sensorTemp表做持久化，这里我们对流数据表设置100万条记录的阈值，每当记录数超出100万之后，系统会做一次持久化处理。
```
share streamTable(1000000:0,`hardwareId`ts`temp1`temp2`temp3,[INT,TIMESTAMP,DOUBLE,DOUBLE,DOUBLE]) as sensorTemp
enableTablePersistence(sensorTemp, true, false, 1000000)
```
在模拟产生的高频数据流开始进入系统之后，DolphinDB通过订阅高频流数据，把数据实时保存到分布式数据库中。我们这里将日期作为第一个分区维度，设备编号作为第二分区维度。
> *在物联网大数据场景下，经常要清除过时的数据，这样分区的模式可以简单的通过删除指定日期分区就可以快速的清理过期数据。*

```
db1 = database("",VALUE,2018.08.14..2018.12.20)
db2 = database("",RANGE,0..10*100)
db = database("dfs://iotDemoDB",COMPO,[db1,db2])
dfsTable = db.createPartitionedTable(tableSchema,"sensorTemp",`ts`hardwareId)
subscribeTable(, "sensorTemp", "save_to_db", -1, append!{dfsTable}, true, 1000000,10)
```

在对流数据做分布式保存数据库的同时，系统使用DolphinDB内置的 createStreamAggregator 实时运算函数来定义实时运算的过程。函数第一个参数指定了窗口大小为60秒，第二个参数指定每2秒钟做一次求均值运算，第三个参数是运算的元代码，可以由用户自己指定计算函数，任何系统支持的或用户自定义的聚合函数这里都能支持，通过指定分组字段hardwareId，函数会将流数据按设备分成1000个队列进行均值运算，每个设备都会按各自的窗口计算得到对应的平均温度。最后通过subscribeTable订阅高频流数据，在有新数据进来时触发实时计算，并将运算结果保存到一个新的数据流表sensorTempAvg中。
createStreamAggregator 参数说明：窗口时间，运算间隔时间，聚合运算元代码，原始数据输入表，运算结果输出表，时序字段，分组字段，触发GC记录数阈值。

```
share streamTable(1000000:0, `time`hardwareId`tempavg1`tempavg2`tempavg3, [TIMESTAMP,INT,DOUBLE,DOUBLE,DOUBLE]) as sensorTempAvg
metrics = createStreamAggregator(60000,2000,<[avg(temp1),avg(temp2),avg(temp3)]>,sensorTemp,sensorTempAvg,`ts,`hardwareId,2000)
subscribeTable(, "sensorTemp", "metric_engine", -1, append!{metrics},true)
```

在DolphinDB Server端在对高频数据流做保存、分析的时候，Grafana前端程序每秒钟会轮询实时运算的结果，并刷新平均温度的趋势图。DolphinDB提供了Grafana_DolphinDB的datasource插件，关于Grafana的安装以及DolphinDB的插件配置请参考[Grafana配置教程](https://www.github.com/dolphindb/grafana-datasource/blob/master/README.md)
。

在完成grafana的基本配置之后，新增一个Graph Panel, 在Metrics tab里输入

```
select gmtime(time) as time, tempavg1, tempavg2, tempavg3 from sensorTempAvg where hardwareId = 1
```
> *这段脚本是选出1号设备实时运算得到的平均温度表*

![image](images/datasource.PNG)


最后，启动数据模拟程序，生成高频数据并写入流数据表
 > *高频数据规模: 1000 个设备，以每个点3个维度、10ms的频率生成数据，以每个维度8个Byte ( Double类型 ) 计算，数据流速是 24Mbps，持续100秒。*
```
def writeData(){
	hardwareNumber = 1000
	for (i in 0:10000) {
		data = table(take(1..hardwareNumber,hardwareNumber) as hardwareId ,take(now(),hardwareNumber) as ts,rand(20..41,hardwareNumber) as temp1,rand(30..71,hardwareNumber) as temp2,rand(70..151,hardwareNumber) as temp3)
		sensorTemp.append!(data)
		sleep(10)
	}
}
submitJob("simulateData", "simulate sensor data", writeData)
```

[demo完整脚本](script/iot_demo_script.txt)
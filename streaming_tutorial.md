# DolphinDB流数据教程
实时流处理是指将业务系统产生的持续增长的动态数据进行实时的收集、清洗、统计、入库，并对结果进行实时的展示。在金融交易、物联网、互联网/移动互联网等应用场景中，复杂的业务需求对大数据处理的实时性提出了极高的要求。面向静态数据表的传统计算引擎无法胜任流数据领域的分析和计算任务。

DolphinDB内置的流数据框架支持流数据的发布、订阅、预处理、实时内存计算、复杂指标的滚动窗口计算等，是一个运行高效，使用便捷的流数据处理框架。

与其它流数据系统相比，DolphinDB流数据处理系统的优点在于：
- 吞吐量大，低延迟。
- 与时序数据库及数据仓库集成，一站式解决方案。
- 天然具备流表对偶性，支持使用SQL语句进行数据注入和查询分析。

本教程将讲述以下内容：
- 流数据框架及相关概念
- 使用流数据
- 使用Java API订阅流数据
- 监控流数据运行状态
- 流数据性能调优
- 与开源系统Grafana结合使用

### 1 流数据框架及相关概念

流数据框架对流数据的管理和应用是基于发布-订阅-消费的模式。流数据首先注入流数据表中，通过流数据表来发布数据，数据节点或者第三方的应用可以通过DolphinDB脚本或API来订阅及消费流数据。

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/stream_cn.png?raw=true)

上图展示了DolphinDB的流数据处理框架。把实时数据注入到发布节点流数据表后，发布的数据可同时供多方订阅消费：
- 可由数据仓库订阅并保存，作为分析系统与报表系统的数据源。
- 可由聚合引擎订阅，进行聚合计算，并将聚合结果输出到流数据表。聚合结果既可以由Grafana等平台进行实时展示，也可以作为数据源再次发布，供二次订阅做事件处理。
- 可由API订阅，例如第三方的Java应用程序可以通过Java API订阅流数据进行业务操作。

#### 1.1 流数据表
流数据表可以作为发布和订阅流数据的载体。发布一条消息等价于向流数据表插入一条记录。可使用SQL语句对流数据表进行查询和分析。

#### 1.2 发布和订阅
流数据框架使用了经典的订阅发布模式。每当有新的流数据写入时，发布方会通知所有的订阅方处理新的流数据。数据节点使用`subscribeTable`函数来订阅流数据。

#### 1.3 实时聚合引擎

实时聚合引擎指的是专门用于处理流数据实时计算和分析的模块。DolphinDB提供`createStreamAggregator`函数用于持续地对流数据做实时聚合计算，并且将计算结果持续输出到指定的数据表中。关于如何使用聚合引擎请参考[流数据聚合引擎](https://github.com/dolphindb/Tutorials_CN/blob/master/stream_aggregator.md)。

### 2 使用流数据

要开启支持流数据功能的模块，需要对数据节点增加配置项。

对于发布节点需要的配置项：
```
maxPubConnections：发布信息节点最多可连接几个节点。若maxPubConnections>0，则该节点可作为发布节点。默认值为0。
persisitenceDir：保存共享的流数据表的文件夹路径。若需要保存流数据表，必须指定该参数。
persistenceWorkerNum：负责以异步模式保存流数据表的工作线程数。默认值为0。
maxPersistenceQueueDepth：以异步模式保存流数据表时消息队列的最大深度（记录数）。默认值为10,000,000。
maxMsgNumPerBlock：当服务器发布或组合消息时，消息块中最多可容纳多少条记录。默认值为1024。
maxPubQueueDepthPerSite：发布节点消息队列的最大深度（记录数）。默认值为10,000,000。
```

对于订阅节点需要的配置项：
```
subPort：订阅线程监听的端口号。当节点作为订阅节点时，该参数必须指定。默认值为0。
subExecutors：订阅节点中消息处理线程的数量。默认值为0，表示解析消息线程也处理消息。
maxSubConnections：服务器能够接收的最大的订阅连接数。默认值是64。
subExecutorPooling: 表示执行流计算的线程是否处于pooling模式的布尔值。默认值是false。
maxSubQueueDepth：订阅节点消息队列的最大深度（记录数）。默认值为10,000,000。
```
#### 2.1 流数据发布

使用`streamTable`函数定义一个流数据表，向其写入数据即意味着发布数据。由于流数据表需要被不同的会话访问，所以必须使用命令`share`，将流数据表进行共享。不被共享的流数据表无法发布数据。

下面的例子中，定义并共享流数据表pubTable：
```
share streamTable(10000:0,`timestamp`temperature, [TIMESTAMP,DOUBLE]) as pubTable
```

#### 2.2 流数据订阅

订阅数据通过 [`subscribeTable`](https://www.dolphindb.cn/cn/help/subscribeTable.html)函数来实现。
```
subscribeTable([server], tableName, [actionName], [offset=-1], handler, [msgAsTable=false], [batchSize=0], [throttle=1], [hash=-1])
```
参数说明：
- 只有tableName和handler两个参数是必需的。其他所有参数都是可选参数。

- server：字符串，表示服务器的别名或流数据所在的xdb连接服务器。如果未指定或者为空字符串，表示服务器是本地实例。

实际情况中，发布者与订阅者的关系有三种可能。下面的例子解释这三种情况的server参数如何构造：

1. 发布者与订阅者是同一节点：
```
subscribeTable(, "pubTable", "actionName", 0, subTable, true)
```
2. 发布者与订阅者是同一集群内的不同节点。此处发布节点别名为"NODE2"：
```
subscribeTable("NODE2", "pubTable", "actionName", 0, subTable, true)
```
3. 发布者与订阅者不在同一个集群内。此处发布节点为 (host="192.168.1.13"，port=8891)。
```
pubNodeHandler=xdb("192.168.1.13",8891)
subscribeTable(pubNodeHandler, "pubTable", "actionName", 0, subTable, true)
```
- tableName：被订阅的数据表名。
```
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable
subscribeTable(, "pubTable", "actionName", 0, subTable, true)
```
- actionName：流数据可以针对各种场景分别订阅消费。同一份流数据，可用于实时聚合运算，同时亦可将其存储到数据仓库供第三方应用做批处理。`subscribeTable`函数提供了actionName参数以区分同一个流数据表被订阅用于不同场景的情况。
```
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable
topic1 = subscribeTable(, "pubTable", "actionName_realtimeAnalytics", 0, subTable, true)
topic2 = subscribeTable(, "pubTable", "actionName_saveToDataWarehouse", 0, subTable, true)
```
`subscribeTable`函数的返回值是订阅主题，它是订阅表所在节点的别名、流数据表名称和订阅任务名称（如果指定了actionName）的组合，使用"/"分隔。如果订阅主题已经存在，函数将会抛出异常。若当前节点别名为NODE1，上述例子返回的两个topic内容如下:

topic1:
```
NODE1/pubTable/actionName_realtimeAnalytics
```
topic2:
```
NODE1/pubTable/actionName_saveToDataWarehouse
```
- offset：订阅任务开始后的第一条消息所在的位置。消息是指流数据表中的行。如果没有指定，或为负数，或超过了流数据表的记录行数，订阅将会从流数据表的当前行开始。offset的值永远与流数据表创建时的第一行对应，如果某些行因为内存限制被删除，在决定订阅开始的位置时，这些行仍然考虑在内。
下面的示例说明offset的作用，向pubTable写入100行数据，建立三个订阅：
```
share streamTable(10000:0,`timestamp`temperature, [TIMESTAMP,DOUBLE]) as pubTable
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable1
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable2
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable3
vtimestamp = 1..100
vtemp = norm(2,0.4,100)
tableInsert(pubTable,vtimestamp,vtemp)
topic1 = subscribeTable(, "pubTable", "actionName1", 102,subTable1, true)
topic1 = subscribeTable(, "pubTable", "actionName2", -1, subTable2, true)
topic1 = subscribeTable(, "pubTable", "actionName3", 50,subTable3, true)
```
从结果可以看到，subTable1与subTable2都没有数据，而subTable3有50条数据。当`offset`为负或者超过数据集记录数时，订阅会从当前行开始，只有当新数据进入发布表时才能订阅到数据。

- handler：一元函数或表。它用于处理订阅数据。若它是函数，其唯一的参数是订阅到的数据。订阅数据可以是一个数据表或元组，订阅数据表的每个列是元组的一个元素。我们经常需要把订阅数据插入到数据表。为了方便使用，handler也可以是一个数据表，并且订阅数据可以直接插入到该表中。 下面的示例展示handler的两种用途，subTable1直接把订阅数据写入目标table，subTable2通过自定义函数myHandler将数据进行过滤后写入。
```
def myhandler(msg){
	t = select * from msg where temperature>0.2
	if(size(t)>0)
		subTable2.append!(t)
}
share streamTable(10000:0,`timestamp`temperature, [TIMESTAMP,DOUBLE]) as pubTable
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable1
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable2
topic1 = subscribeTable(, "pubTable", "actionName1", -1, subTable1, true)
topic1 = subscribeTable(, "pubTable", "actionName2", -1, myhandler, true)

vtimestamp = 1..10
vtemp = 2.0 2.2 2.3 2.4 2.5 2.6 2.7 0.13 0.23 2.9
tableInsert(pubTable,vtimestamp,vtemp)
```
从结果可以看到pubTable写入10条数据，subTable1全部接收了，而subTable2经过myhandler过滤掉了0.13，收到9条数据。

- msgAsTable：表示订阅的数据是否为表的布尔值。默认值是false，表示订阅数据是由列组成的元组。
下面的示例展示订阅数据格式的不同：
```

def myhandler1(table){
	subTable1.append!(table)
}
def myhandler2(tuple){
	tableInsert(subTable2,tuple[0],tuple[1])
}
share streamTable(10000:0,`timestamp`temperature, [TIMESTAMP,DOUBLE]) as pubTable
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable1
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable2
//msgAsTable = true
topic1 = subscribeTable(, "pubTable", "actionName1", -1, myhandler1, true)
//msgAsTable = false
topic2 = subscribeTable(, "pubTable", "actionName2", -1, myhandler2, false)

vtimestamp = 1..10
vtemp = 2.0 2.2 2.3 2.4 2.5 2.6 2.7 0.13 0.23 2.9
tableInsert(pubTable,vtimestamp,vtemp)
```
- batchSize：一个整数，表示批处理的消息的行数。如果它是正数，则直到消息的数量达到batchSize时，handler才会开始处理消息。如果它没有指定或者是非正数，只要有一条消息进入，handler就会马上开始处理消息。
下面示例展示当batchSize设置为11时，先向pubTable写入10条数据，观察订阅表，然后再写入1条数据，再观察订阅表。
```
share streamTable(10000:0,`timestamp`temperature, [TIMESTAMP,DOUBLE]) as pubTable
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable1
topic1 = subscribeTable(, "pubTable", "actionName1", -1, subTable1, true, 11)
vtimestamp = 1..10
vtemp = 2.0 2.2 2.3 2.4 2.5 2.6 2.7 0.13 0.23 2.9
tableInsert(pubTable,vtimestamp,vtemp)

print size(subTable1)
```
此时可看到结果为0。
```
insert into pubTable values(11,3.1)
print size(subTable1)
```
此时可看到结果为11。当发布数据累计到11条时，数据才进入到subTable1。

- throttle：一个整数，表示handler处理进来的消息之前等待的时间，以秒为单位。默认值为1。如果没有指定batchSize，throttle将不会起作用。

batchSize用于数据缓冲。当流数据的写入频率非常高，以致数据消费能力跟不上数据进入的速度时，需要进行流量控制，否者订阅端缓冲区很快会堆积数据并耗光内存。throttle设定一个时间，根据订阅端的消费速度定时放一批数据进来，保障订阅端的缓冲区数据量稳定。

- hash：一个非负整数，指定某个订阅线程处理进来的消息。如果没有指定该参数，系统会自动分配一个线程。如果需要使用一个线程来处理多个订阅任务的消息，把订阅任务的hash设置为相同的值。当需要在两个或多个订阅的处理过程中保持消息数据的同步，可以将多个订阅的hash值设置成相同，这样就能使用同一个线程来同步处理多个数据源，不会出现数据处理有先后导致结果误差。

#### 2.3 取消订阅

每一次订阅都由一个订阅主题topic作为唯一标识。如果订阅时topic已存在，那么会订阅失败。这时需要通过`unsubscribeTable`命令取消订阅才能再次订阅。取消订阅示例如下：

取消订阅一个本地表：
```
unsubscribeTable(,"pubTable","actionName1")
```
取消订阅一个远程表：
```
unsubscribeTable("NODE_1","pubTable","actionName1")
```
若要删除共享的流数据表，可以使用`undef`命令：
```
undef("pubStreamTable", SHARED)
```
#### 2.4 流数据持久化

默认情况下，流数据表把所有数据保存在内存中。基于以下两点考量，可将流数据持久化到磁盘。
1. 避免内存不足。
2. 流数据的备份和回复。当节点出现异常重启时，持久化的数据会在重启时自动载入到流数据表。

我们可事先设定一个界限值。若流数据表的行数达到设定的界限值，前面一半的记录行会从内存转移到磁盘。持久化的数据支持重订阅，当订阅指定数据下标时，下标的计算包含持久化的数据。

要启动流数据持久化，首先要在发布节点的配置文件中添加持久化路径：
```
persisitenceDir = /data/streamCache
```
在脚本中执行[`enableTablePersistence`](https://www.dolphindb.cn/cn/help/enableTablePersistence.html)命令设置针对某一个流数据表启用持久化。下面的示例针对pubTable表启用持久化，其中asyn = true, compress = true, cacheSize=1000000，即当流数据表达到100万行数据时启用持久化，将其中50%的数据采用异步方式压缩保存到磁盘。
```
enableTablePersistence(pubTable, true, true, 1000000)
```
若执行`enableTablePersistence`时，磁盘上已经存在pubTable表的持久化数据，那么系统会加载最新的cacheSize=1000000行记录到内存中。

对于持久化是否启用异步，需要在持久化数据一致性和性能之间作权衡。当流数据的一致性要求极高时，可以使用同步方式，这样可以保证持久化完成以后，数据才会进入发布队列；若对实时性要求极高，不希望磁盘IO影响到流数据的实时性，那么可以启用异步方式。只有启用异步方式时，持久化工作线程数persistenceWorkerNum配置项才会起作用。当有多个发布表需要持久化，增加persistenceWorkerNum的配置值可以提升异步保存的效率。

当不需要保存在磁盘上的流数据时，通过`clearTablePersistence`命令可以删除持久化数据。
```
clearTablePersistence(pubTable)
```
当整个流数据写入结束时，可以使用[`disableTablePersistence`](https://www.dolphindb.cn/cn/help/disableTablePersistence.html)命令关闭持久化。
```
disableTablePersistence(pubTable)
```

### 3 使用Java API来订阅DolphinDB中的流数据

流数据的消费者可能是DolphinDB本身的聚合引擎，也可能是第三方的消息队列或者第三方程序。DolphinDB提供了Streaming API供第三方程序来订阅流数据。当有新数据进入时，API的订阅者能够及时的接收到通知，这使得DolphinDB的流数据框架可与第三方的应用进行深入的整合。目前DolphinDB提供Java流数据API，后续会逐步支持C++、C#等流数据API。

Java API处理数据的方式有两种：轮询方式(Polling)和事件方式(EventHandler)。

- 轮询方式示例代码：
```
PollingClient client = new PollingClient(subscribePort);
TopicPoller poller1 = client.subscribe(serverIP, serverPort, tableName, offset);

while (true) {
   ArrayList<IMessage> msgs = poller1.poll(1000);
   if (msgs.size() > 0) {
         BasicInt value = msgs.get(0).getEntity(2);  //取数据中第一行第二个字段
   }
}
```
每次流数据表发布新数据时，poller1会拉取到新数据。无新数据发布时，程序会阻塞在poller1.poll方法这里等待。

Java API使用预先设定的MessageHandler获取及处理新数据。首先需要调用者定义数据处理器Handler，Handler需要实现com.xxdb.streaming.client.MessageHandler接口。

- 事件方式示例代码:
```
public class MyHandler implements MessageHandler {
       public void doEvent(IMessage msg) {
               BasicInt qty = msg.getValue(2);
               //..处理数据
       }
}
```

在启动订阅时，把handler实例作为参数传入订阅函数。
```
ThreadedClient client = new ThreadedClient(subscribePort);
client.subscribe(serverIP, serverPort, tableName, new MyHandler(), offsetInt);
```
当每次流数据表有新数据发布时，Java API会调用MyHandler方法，并将新数据通过msg参数传入。


### 4 监控流数据运行状态

当通过订阅方式对流数据进行实时处理时，所有的计算都在后台进行，用户无法直观的看到运行的情况。DolphinDB提供`getStreamingStat`函数，可以全方位监控流数据处理过程。

`getStreamingStat`函数返回的是一个tuple，其中包含了pubConns, subConns, persistWorkers, subWorkers四个表。

#### 4.1 pubConns表

pubConns表监控本节点流数据发布状态，每行代表此发布节点的一个订阅节点。

列名称|说明
---|---
client|订阅节点的IP和端口信息
queueDepthLimit|发布节点消息队列允许的最大深度（消息数）。每个发布节点只有一个发布消息队列。
queueDepth|发布节点消息队列深度（消息数）
tables|该节点上的所有共享的流数据表。若多表，彼此通过逗号分隔。

在GUI中运行getStreamingStat().pubConns查看表内容：

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/pubconn.png?raw=true)

pubConns表会列出该节点所有的订阅节点信息，发布队列情况，以及流数据表名称。


#### 4.2 subConns表

subConns表监控本节点流数据订阅状态，每个订阅的发布节点为表中一行。

列名称|说明
---|---
publisher|发布节点别名
cumMsgCount|累计接收消息数
cumMsgLatency|累计接收消息的平均延迟时间(毫秒)。延迟时间指的是消息从进入发布队列到进入订阅队列的耗时。
lastMsgLatency|最后一次接收数据延迟时间(毫秒)
lastUpdate|最后一次接收数据时刻

在GUI中运行getStreamingStat().subConns查看表内容：

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/subconn.png?raw=true)

这张表列出所有本节点订阅的所有发布节点的连接状态和有关接收消息的统计信息。

#### 4.3 persistWorkers表

persistWorkers表监控流数据表持久化工作线程，每个工作线程为一行。

列名称|说明
---|---
workerId|工作线程编号
queueDepthLimit|持久化消息队列深度限制
queueDepth|持久化消息队列深度
tables|持久化表名。若多表，彼此通过逗号分隔。

只有持久化启用后，才能通过`getStreamingStat`获取persistWorkers表。这张表记录了所有持久化的表信息，记录数等于persistenceWorkerNum配置数。以下例子在GUI中运行getStreamingStat().persistWorkers查看持久化两张数据表的线程。

当persistenceWorkerNum=1时：

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/persistworker.png?raw=true)

当persistenceWorkerNum=3时：

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/persisWorders_2.png?raw=true)

从图上可以直观的看出，调高persistenceWorkerNum参数可并行处理持久化数据表的任务。

#### 4.4 subWorkers表

subWorkers表监控流数据订阅工作线程，每条记录代表一个订阅工作线程。

列名称|说明
---|---
workerId|工作线程编号
queueDepthLimit|订阅消息队列最大限制
queueDepth|订阅消息队列深度
processedMsgCount|已进入handler的消息数量
failedMsgCount|handler处理异常的消息数量
lastErrMsg|上次handler处理异常的信息
topics|已订阅主题。若多个，彼此通过逗号分隔。

配置项subExecutors与subExecutorPooling这两个配置项的对流数据处理的影响，在这张表上可以得到充分的展现。在GUI中使用getStreamingStat().subWorkers查看。

当subExecutorPooling=false,subExecutors=1时，内容如下：

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/subworker_1.png?raw=true)
此时，所有表的订阅消息共用一个线程队列。

当subExecutorPooling=false,subExecutors=2时，内容如下：

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/subworker_2.png?raw=true)
此时，各个表订阅消息分配到两个线程队列独立处理。

当subExecutorPooling=true,subExecutors=2时，内容如下：

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/subworker_pool.png?raw=true)
此时，各个表的订阅消息共享由两个线程组成的线程池。

当有流数据进入时，可以通过这个表观察到已处理数据量等信息：

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/subworker_msg.png?raw=true)

#### 4.5 pubTables表
pubTables表监控流数据表被订阅情况，每条记录代表流数据表一个订阅连接。

列名称|说明
---|---
tableName|发布表名称
subscriber|订阅方的host和port
msgOffset|订阅线程当前订阅消息的offset
actions|订阅的action。若有多个action，此处用逗号分割

比如存流数据发布表名称为`pubTable1`，发布了100条记录。 有一个订阅从offset=0开始，action名称为"
act_getdata"。那么当订阅完成之后，用getStreamingStat().pubTables 查看内容为：

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/pubtables1.png?raw=true)

### 5 流数据性能调优

当数据流量极大而系统来不及处理时，系统监控中会看到订阅端subWorkers表的queueDepth数值极高，此时系统会按照从订阅端队列-发布端队列-数据注入端逐级反馈数据压力。当订阅端队列深度达到上限时开始阻止发布端数据进入，此时发布端的队列开始累积。当发布端的队列深度达到上限时，系统会阻止流数据注入端写入数据。

可以通过以下几种方式来优化系统对流数据的处理性能：

- 调整订阅参数中的batchSize和throttle参数，来调整数据的批处理和控制接收数据的流量，平衡发布端和订阅端的缓存，让流数据输入速度与数据处理速度达到一个动态的平衡。若要充分发挥数据批量处理的性能优势，可以设定batchSize等待流数据积累到一定量时才进行消费，但是这样会带来一定程度的内存占用；而当batchSize较大的时候，可能会发生数据量一直没有达到batchSize而长期滞留在缓冲区的情况。throttle参数值是一个时间间隔，它的作用是即使batchSize未满足，也能将缓冲区的数据消费掉。

- 通过调整subExecutors配置参数增加订阅端计算的并行度，以加快订阅端队列的消费速度。系统默认采用哈希算法为每一个订阅分配一个executor。在订阅处理过程中，如果需要确保两个订阅用同一个executor来处理，可以在订阅函数subscribeTable中指定参数hash的值。两个订阅使用相同的hash值，来指定用同一个线程来处理这两个订阅数据流，这样可以保证这两个流数据表的时序同步。当有多个executor存在时，如果不同订阅的数据流频率不均或者处理复杂度差异很大，容易导致低负载的executor资源闲置。通过设置subExecutorPooling=true，可以让所有executor作为一个共享线程池，共同处理所有订阅的消息。在这种共享池模式下，所有订阅的消息进入同一个队列，多个executor从队列中读取消息并行处理。共享线程池处理流数据的一个副作用是不能保证消息按到达的时间顺序处理。当实际场景对消息处理的时间顺序有严格要求时，不能开启此设置。

- 若流数据表启用同步持久化，那么磁盘的IO可能会成为瓶颈。一种处理方法是参考2.4采用异步方式持久化数据，同时设置一个合理的持久化队列(maxPersistenceQueueDepth，默认1000万条消息)。当然也可以通过更换硬件，使用SSD硬盘来提高写入性能。

- 如果数据发布端(publisher)成为系统的瓶颈，譬如订阅的客户端太多可能导致发布瓶颈，可以采用以下两种处理办法。首先可以通过多级级联降低每一个发布节点的订阅数量，对延迟不敏感的应用可以订阅二级甚至三级的发布节点。其次可以调整部分参数来平衡延迟和吞吐量两个指标。参数maxMsgNumPerBlock设置批量发送消息时批的大小，默认值是1024。一般情况下，较大的批量值能提升吞吐量，但会增加网络延迟。

- 若输入流数据的流量波动较大，高峰期导致消费队列积压至队列峰值(默认1000万)，那么可以修改配置项maxPubQueueDepthPerSite和maxSubQueueDepth以增加发布端和订阅端的最大队列深度，提高系统数据流大幅波动的能力。鉴于队列深度增加时内存消耗会增加，应估算内存的使用量以合理配置内存。


### 6 流数据的展示

流数据可视化可分为两种类型：
- 实时值监控：用滑动窗口固定一个时间区间，把流数据聚合为一个值，并定时刷新，通常用于指标的监控和预警。

- 趋势监控：把新产生的数据附加到原有的数据上并以可视化图表的方式渐进更新，通常用于做数据全局分析。

很多数据可视化的平台都能支持流数据的实时监控，比如当前流行的开源数据可视化框架Grafana，它可以设定固定时间间隔去请求流数据表，并把数据以动态更新的数字或图表方式展示出来。DolphinDB已经实现了Grafana的服务端和客户端的接口，具体配置可以参考教程：https://github.com/dolphindb/grafana-datasource/blob/master/README.md
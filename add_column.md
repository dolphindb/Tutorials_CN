# 动态增加字段和计算指标

工业物联网采集的数据和金融交易数据具有相同的特点：频率高、维度多、数据一旦生成就不会改变、数据量庞大，并且工业物联网数据采集的维度和实时计算的指标会随着业务扩展和设备增加而不断增加，金融领域的数据分析和监控需要不断增加风控监测指标。因此，工业物联网和金融领域的数据平台必须能够满足动态增加字段和计算指标的需求。

DolphinDB database 为工业物联网和金融提供了一站式解决方案。数据处理流程如下图所示：

![Image text](../images/stream_cn.png)

工业物联网采集的数据和金融交易的实时数据首先会以流数据的形式注入到DolphinDB的流数据表中，数据节点通过订阅流数据表，可以把实时流数据持久化到分布式数据库中，供将来深度数据分析使用；同时，流聚合引擎通过订阅流数据表，对流数据进行实时聚合运算，计算结果用于工业物联网的监控和预警以及互联网金融的风控监测。

在这一数据处理流程中，涉及到了3种表：分布式表（DFS table）、流数据表、流聚合引擎的输入表和输出表。如果数据采集的维度增加，那么这3种表都要做相应的处理。

## 1.给分布式表增加字段

如果计划给流数据表新增加字段，而订阅者分布式表没有做相应的调整，那么流数据将无法写入分布式表，这是由于流数据表和分布式表结构不一致造成的。因此，如果需要给流数据表增加字段，必须首先要给订阅者分布式表增加字段。DolphinDB提供了`addColumn`函数为分布式表增加字段。

### 语法

addColumn(table, colNames, colTypes)

### 参数

* table 是分布式表或流数据表。

* colNames 是字符串标量或向量，表示要增加的字段名。

* colType 是表示数据类型的标量或向量。

### 例子

创建一个分布式数据库，计划用于保存流数据表的数据。

```
if(existsDatabase("dfs://iotDemo")){
	dropDatabase("dfs://iotDemo")
	}
db=database("dfs://iotDemo",RANGE,`A`F`M`T`Z)
pt = db.createPartitionedTable(table(1000:0,`time`equipmentId`voltage`eletricity,[TIMESTAMP,SYMBOL,INT,DOUBLE]), `pt, `equipmentId)
```

计划给流数据表streamTb新增两个字段，因此分布式表pt需要先增加两个字段。分布式表增加字段后，需要使用`loadTable`函数重新加载，才会生效。

```
addColumn(pt,`temperature`humidity,[DOUBLE,DOUBLE])
pt=loadTable("dfs://iotDemo","pt")
```

## 2.给流数据表增加字段

流数据表通常是由`streamTable`函数生成，用于传输流数据。工业物联网采集的数据和金融交易的实时数据往往会先注入流数据表。如果数据采集维度增加，那么作为信息发布者的流数据表需要调整结构。DolphinDB的`addColumn`函数除了可以给分布式表增加字段，还可以给流数据表的字段。

假设目前数据采集的维度只有两个：电压和电流。创建流数据表的代码如下：

```
streamTb=streamTable(1000:0,`time`equipmentId`voltage`eletricity,[TIMESTAMP,SYMBOL,INT,DOUBLE])
```

现在需要新增两个采集维度：温度和湿度。流数据表需要新增两个字段：

```
addColumn(streamTb,`temperature`humidity,[DOUBLE,DOUBLE])
```

给流数据表增加字段是即时生效，下一次调用流数据表时，它已经包含了新增加的字段。

## 3.给流聚合引擎增加计算指标

用户在定义流聚合引擎时，需要使用元代码（metacode）来指定计算指标。随着需求的变化，计算指标往往也会做出响应的改变。DolphinDB提供了`addMetrics`函数来增加流聚合引擎的计算指标。

### 语法

addMetrics(StreamAggregator, newMetrics, newMetricsSchema)

### 参数

* StreamAggregator 是`createTimeSeriesAggregator`函数返回的抽象表。

* newMetrics 是元代码，用于表示增加的计算指标。

* newMetricsSchema 是表对象，用于指定新增的计算指标在输出表中的列名和数据类型。

### 例子

定义一个流数据引擎，每隔50毫秒计算一次每台设备的平均电压和平均电流。

```
//定义流聚合引擎以及订阅流数据表
streamTb=streamTable(1000:0,`time`equipmentId`voltage`eletricity,[TIMESTAMP,SYMBOL,INT,DOUBLE])
share streamTb as sharedStreamTb
outTb=table(1000:0,`time`equipmentId`avgvoltage`avgeletricity,[TIMESTAMP,SYMBOL,INT,DOUBLE])
aggregator = createTimeSeriesAggregator(100, 50, <[avg(voltage),avg(eletricity)]>, sharedStreamTb, outTb, `time , false,`equipmentId , 2000)
subscribeTable(, "sharedStreamTb", "aggregator", 0, append!{aggregator},true)

//往流数据表中插入数据
n=10
timev=temporalAdd(2019.01.20 12:30:10.000,rand(300,n),"ms")
equipmentIdv=rand(`A`F`M`T`Z,n)
voltagev=rand(250,n)
eletricityv=rand(16.0,n)
insert into sharedStreamTb values(timev, equipmentIdv, voltagev, eletricityv)

//查看流数据表
select * from sharedStreamTb

```
|time                   |equipmentId|voltage|electricity|
|----                   |-----------|-------|-----------|
|2019.01.20T12:30:10.056|T          |249    |14.607704  |
|2019.01.20T12:30:10.045|Z          |225    |9.68903    |
|2019.01.20T12:30:10.225|M          |226    |0.556784   |
|2019.01.20T12:30:10.221|A          |245    |2.244341   |
|2019.01.20T12:30:10.183|F          |223    |1.094678   |
|2019.01.20T12:30:10.229|M          |222    |2.614694   |
|2019.01.20T12:30:10.132|M          |238    |0.273434   |
|2019.01.20T12:30:10.122|F          |238    |10.345701  |
|2019.01.20T12:30:10.226|M          |240    |9.950607   |
|2019.01.20T12:30:10.126|M          |244    |1.210446   |

```
//查看输出表
select * from outTb
```

|time                   |equipmentId|avgvlotage|avgeletricity|
|----                   |-----------|----------|-------------|
|2019.01.20T12:30:10.100|T          |249       |14.607704    |
|2019.01.20T12:30:10.100|Z          |225       |9.68903      |

给流聚合引擎增加两个新的计算指标，每隔50毫秒取最后一个电压和电流值。没有新数据流入聚合引擎时，输出表中新增加的计算指标的值为空。

```
newMetricsSchema=table(1:0,`lastvoltage`lasteletricity,[INT,DOUBLE])
addMetrics(aggregator,<[last(voltage), last(eletricity)]>,newMetricsSchema)

//查看数据表

select * from outTb

```
|time                   |equipmentId|avgvlotage|avgeletricity|lastvoltage|lasteletricity|
|----                   |-----------|----------|-------------|---|---|
|2019.01.20T12:30:10.100|T          |249       |14.607704    |||
|2019.01.20T12:30:10.100|Z          |225       |9.68903      |||

写入新的数据。

```
n=10
timev=temporalAdd(2019.01.20 12:30:10.000,rand(300,n),"ms")
equipmentIdv=rand(`A`F`M`T`Z,n)
voltagev=rand(220..250,n)
eletricityv=rand(16.0,n)
insert into sharedStreamTb values(timev, equipmentIdv, voltagev, eletricityv)
select * from outTb
```

|time                   |equipmentId|avgvlotage|avgeletricity|lastvoltage|lasteletricity|
|----                   |-----------|----------|-------------|---|---|
|2019.01.20T12:30:10.100|T          |249       |14.607704    |||
|2019.01.20T12:30:10.100|Z          |225       |9.68903      |||
|2019.01.20T12:30:10.200|F          |235       |9.182104     |234|14.896723|
|2019.01.20T12:30:10.150|T          |243       |10.816871    |236|7.026039|
|2019.01.20T12:30:10.200|Z          |225       |5.893952     |225|2.098874|

## 4.总结

在流数据处理流程中，如果需要增加字段，必须按照以下顺序：订阅者—分布式表、发布者—流数据表、订阅者—流聚合引擎。如果不按照以上顺序增加字段，那么数据结构不一致会导致流数据无法持久化到分布式表。


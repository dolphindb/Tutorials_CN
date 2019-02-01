
### DolphinDB与Druid对比测试报告附录

#### 附录

#### 附录1. 环境配置

(1) DolphinDB配置

controller.cfg

```
localSite=localhost:9919:ctl9919
localExecutors=3
maxConnections=128
maxMemSize=4
webWorkerNum=4
workerNum=4
dfsReplicationFactor=1
dfsReplicaReliabilityLevel=0
enableDFS=1
enableHTTPS=0

```

cluster.nodes

```
localSite,mode
localhost:9910:agent,agent
localhost:9921:DFS_NODE1,datanode
localhost:9922:DFS_NODE2,datanode
localhost:9923:DFS_NODE3,datanode
localhost:9924:DFS_NODE4,datanode
```

cluster.cfg

```
maxConnection=128
workerNum=8
localExecutors=7
webWorkerNum=2
maxMemSize=0
```

agent.cfg

```
workerNum=3
localExecutors=2
maxMemSize=4
localSite=localhost:9910:agent
controllerSite=localhost:9919:ctl9919
```

(2) Druid配置

_common

```
# Zookeeper
druid.zk.service.host=zk.host.ip
druid.zk.paths.base=/druid
# Metadata storage
druid.metadata.storage.type=mysql
druid.metadata.storage.connector.connectURI=jdbc:mysql://db.example.com:3306/druid
# Deep storage
druid.storage.type=local
druid.storage.storageDirectory=var/druid/segments
# Indexing service logs
druid.indexer.logs.type=file
druid.indexer.logs.directory=var/druid/indexing-logs
```

broker:

```
Xms24g
Xmx24g
XX:MaxDirectMemorySize=4096m

# HTTP server threads
druid.broker.http.numConnections=5
druid.server.http.numThreads=25

# Processing threads and buffers
druid.processing.buffer.sizeBytes=2147483648
druid.processing.numThreads=7

# Query cache
druid.broker.cache.useCache=false
druid.broker.cache.populateCache=false

coordinator:
Xms3g
Xmx3g

historical:
Xms8g
Xmx8g

# HTTP server threads
druid.server.http.numThreads=25

# Processing threads and buffers
druid.processing.buffer.sizeBytes=2147483648
druid.processing.numThreads=7

# Segment storage
druid.segmentCache.locations=[{"path":"var/druid/segment-cache","maxSize":0}]
druid.server.maxSize=130000000000

druid.historical.cache.useCache=false
druid.historical.cache.populateCache=false

middleManager:
Xms64m
Xmx64m

# Number of tasks per middleManager
druid.worker.capacity=3

# HTTP server threads
druid.server.http.numThreads=25

# Processing threads and buffers on Peons
druid.indexer.fork.property.druid.processing.buffer.sizeBytes=4147483648
druid.indexer.fork.property.druid.processing.numThreads=2
```

overload:

```
Xms3g
Xmx3g
```

#### 附录2. 数据库查询性能测试用例

DolphinDB脚本：

```
//根据股票代码和日期查找并取前1000条
timer select top 1000 * from TAQ where symbol = 'IBM' , date = 2007.08.10;

//根据部分股票代码和时间、报价范围计数
timer select count(*) from TAQ where date = 2007.08.10, symbol in ('GOOG', 'THOO', 'IBM'), bid>0, ofr>bid;

//按股票代码分组并按照卖出与买入价格差排序
timer select sum(ofr-bid) as spread from TAQ where date = 2007.08.27 group by symbol order by spread;

//按时间和报价范围过滤，按小时分组并计算均值
timer select avg((ofr-bid)/(ofr+bid)) as spread from TAQ where date = 2007.08.01, bid > 0, ofr > bid group by hour(time);

//按股票代码分组并计算最大卖出与最小买入价之差
timer select max(ofr)-min(bid) as gap from TAQ where date = 2007.08.03, bid > 0, ofr > bid group by symbol;

//对最大买入价按股票代码、小时分组并排序
timer select max(bid) as mx from TAQ where date = 2007.08.27 group by symbol, date having sum(bidsiz)>0 order by symbol, date;

//对买入与卖出价均值的最大值按股票代码、小时分组
timer select max(ofr+bid)/2.0 as mx from TAQ where date = 2007.08.01, group by symbol, date;

```

Druid脚本：

```
//根据股票代码和日期查找并取前1000条
select * from TAQ where SYMBOL = 'IBM' and __time = TIMESTAMP'2007-08-10 00:00:00' limit 1000;

//根据部分股票代码和时间、报价范围计数
select count(*) from TAQ where __time = TIMESTAMP'2007-08-10 00:00:00' and SYMBOL in ('GOOG', 'THOO', 'IBM') and BID>0 and OFR>BID;

//按股票代码分组并按照卖出与买入价格差排序
select sum(OFR-BID) as spread from TAQ where __time = TIMESTAMP'2007-08-27 00:00:00' group by SYMBOL order by spread;

//按时间和报价范围过滤，按小时分组并计算均值
select avg((OFR-BID)/(OFR+BID)) as speard from TAQ where __time = TIMESTAMP'2007-08-01 00:00:00' and BID > 0 and OFR > BID group by hour(__time);

//按股票代码分组并计算最大卖出与最小买入价之差
select max(OFR) - min(BID) as gap from TAQ where __time = TIMESTAMP'2007-08-03 00:00:00' and BID > 0 and OFR > BID group by SYMBOL;

//对最大买入价按股票代码、小时分组并排序
select max(BID) as mx from TAQ where __time =TIMESTAMP'2007-08-27 00:00:00' group by SYMBOL, __time having sum(BIDSIZ)>0 order by SYMBOL, __time;

//对买入与卖出价均值的最大值按股票代码、小时分组
select max(OFR+BID)/2.0 as mx from TAQ where __time = TIMESTAMP'2007-08-01 00:00:00' group by SYMBOL, __time;

```

#### 附录3. 数据导入脚本

DolphinDB脚本：

```
if (existsDatabase("dfs://TAQ"))
dropDatabase("dfs://TAQ")

db = database("/Druid/table", SEQ, 4)
t=loadTextEx(db, 'table', ,"/data/data/TAQ/TAQ20070801.csv")
t=select count(*) as ct from t group by symbol
buckets = cutPoints(exec symbol from t, 128)
buckets[size(buckets)-1]=`ZZZZZ
t1=table(buckets as bucket)
t1.saveText("/data/data/TAQ/buckets.txt")

db1 = database("", VALUE, 2007.08.01..2007.09.01)
partition = loadText("/data/data/buckets.txt")
partitions = exec * from partition
db2 = database("", RANGE, partitions)
db = database("dfs://TAQ", HIER, [db1, db2])
db.createPartitionedTable(table(100:0, `symbol`date`time`bid`ofr`bidsiz`ofrsiz`mode`ex`mmid, [SYMBOL, DATE, SECOND, DOUBLE, DOUBLE, INT, INT, INT, CHAR, SYMBOL]), `quotes, `date`symbol)

def loadJob() {
filenames = exec filename from files('/data/data/TAQ')
db = database("dfs://TAQ")
filedir = '/data/data/TAQ'
for(fname in filenames){
jobId = fname.strReplace(".csv", "")
jobName = jobId 
submitJob(jobId,jobName, loadTextEx{db, "quotes", `date`symbol,filedir+'/'+fname})
}
}
loadJob()
select * from getRecentJobs()
TAQ = loadTable("dfs://TAQ","quotes");
```

Druid脚本：
```
{
"type" : "index",
"spec" : {
"dataSchema" : {
"dataSource" : "TAQ",
"parser" : {
"type" : "string",
"parseSpec" : {
"format" : "csv",
"dimensionsSpec" : {
"dimensions" : [
"TIME",
"SYMBOL",
{"name":"BID", "type" : "double"},
{"name":"OFR", "type" : "double"},
{"name":"BIDSIZ", "type" : "int"},
{"name":"OFRSIZ", "type" : "int"},
"MODE",
"EX",
"MMID"
]
},
"timestampSpec": {
"column": "DATE",
"format": "yyyyMMdd"
},
"columns" : ["SYMBOL",
"DATE",
"TIME",
"BID",
"OFR",
"BIDSIZ",
"OFRSIZ",
"MODE",
"EX",
"MMID"]
}
},
"metricsSpec" : [],
"granularitySpec" : {
"type" : "uniform",
"segmentGranularity" : "day",
"queryGranularity" : "none",
"intervals" : ["2007-08-01/2007-09-01"],
"rollup" : false
}
},
"ioConfig" : {
"type" : "index",
"firehose" : {
"type" : "local",
"baseDir" : "/data/data/",
"filter" : "TAQ.csv"
},
"appendToExisting" : false
},
"tuningConfig" : {
"type" : "index",
"targetPartitionSize" : 5000000,
"maxRowsInMemory" : 25000,
"forceExtendableShardSpecs" : true
}
}
}
```

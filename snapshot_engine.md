# DolphinDB教程：快照引擎

### 1. 概述

在股票市场，交易员需要随时掌握每支股票的最新行情。在物联网领域，运维人员需要监控所有设备的最新状态数据。为了满足用户快速查询最新实时数据的需求，DolphinDB为分布式表(DFS tables)提供了快照引擎功能。快照引擎对每个分组最新插入的记录保存快照，查询最新记录时只需返回快照即可，因此性能出色，而且性能不受表中记录总数的影响。
> 快照引擎目前仅支持单节点服务模式

### 2. 快照引擎的适用场景

若需快速查询各组最新记录，且数据是按时间顺序插入，系统内存资源充足，建议使用快照引擎查询最新记录。

若不能保证按时间顺序插入数据，则不适合使用快照引擎，否则得到的不能保证是最新数据。

因为快照引擎保存了各组的快照，当分组很多时，会占用较多内存。若系统内存资源紧张，也不建议使用快照引擎。

在数据节点启动后，需要注册快照引擎后，节点才会保存最新记录的快照。因此，若插入记录的时间间隔比较长，在重启后到新的数据写入之前，这段时间数据节点是没有保存快照的，所以这时若需要查询快照注册之前的最新记录，是不能用快照引擎查询到最新记录的。

### 3. 快照引擎的使用说明

#### 3.1 注册快照引擎

在查询之前，我们需要先为分布式表注册快照引擎，注册快照引擎的语法如下：
```
registerSnapshotEngine(dbName, tableName, keyColumnName)
```
其中参数dbName表示分布式数据库的名称，tableName表示分布式表的名称，keyColumnName表示分组列的名称。快照引擎将分布式表按照keyColumnName指定的列分组，获取每个组的最新记录。在实际使用时，这个分组列可以是设备的编号或IP地址、股票的股票代码等，这样用户就可以查到每个设备、每个股票的最新状态或行情数据。

下列代码创建分布式数据库compoDB和分布式表pt，然后注册快照引擎来获取分布式表pt中每个股票代码对应的最新记录。
```
db1=database("",VALUE,2018.09.01..2018.09.30)
db2=database("",VALUE,`AAPL`MSFT`MS`C)
db=database("dfs://compoDB",COMPO,[db1,db2])
t=table(1:0,`ts`sym`val,[DATETIME,SYMBOL,DOUBLE])
pt=db.createPartitionedTable(t,`pt,`ts`sym);
registerSnapshotEngine("dfs://compoDB","pt","sym")
```
需要注意的是，需要在集群中的每个节点都注册快照引擎（可以调用pnodeRun函数,例如pnodeRun(registerSnapshotEngine{dbName, tableName, keyColumnName})），而且数据节点重启后需要重新注册。

#### 3.2 查询快照

注册快照引擎后，要查询各组最新记录，只需在SQL语句中设置hint值为64。上述例子中要查询每个分组的最新记录，可以使用以下代码：
```
select [64] * from loadTable("dfs://compoDB","pt")
```
查询最近1分钟有行情数据更新的股票，可以使用以下代码：
```
select [64] sym from loadTable("dfs://compoDB","pt") where ts > datetimeAdd(now(),-1,`m) 
```

#### 3.3 取消快照引擎

快照引擎为每个分组的最新记录在内存中保存快照。当分组较多时，会占用较多内存，所以不再需要查询最新记录时，建议取消快照引擎以释放内存。可以通过unregisterSnapshotEngine取消快照引擎：
```
unregisterSnapshotEngine(dbName, tableName)
```
其中参数dbName与tableName分别表示分布式数据库和分布式表的名称，须与注册时保持一致。上述例子中注册的快照引擎，我们可以用下列代码取消：
```
unregisterSnapshotEngine("dfs://compoDB","pt")
```

### 4. 快照引擎的性能优势

在DolphinDB中，除了使用快照引擎，还有三种通过select语句获取最新记录的方法。当快照引擎不适用时，可以考虑使用这些方法替代：

（1）通过group by对表内记录分组，然后用last函数查找每个分组的最后一行记录。但它也与快照引擎一样，不适合插入的数据是乱序的情况。

（2）通过group by对表内记录分组，然后用atImax函数找出每个分组的时间戳这列的最大值（即最新时间）所在行，然后返回该行的其他列数据。这种方法可用于插入数据是乱序的情况。

（3）通过SQL扩展语句context by对表内记录进行分组，然后在组内按时间戳列进行csort降序排序，再和top一并使用，就可获取每个分组中的最新记录。这种方法也可用于插入数据是乱序的情况。

本节将快照引擎与上述方法进行性能比较测试。

首先，准备测试环境。部署三台物理服务器的6数据节点的DolphinDB集群后，在DolphinDB GUI中用下列代码创建分布式数据库testDB和分布式表trainInfoTable，表中除了ts时间字段、trainID分组字段，还有3个指标字段。在 DolphinDB database中的分区方案是将时间ts作为第一个维度，每天一个分区，再将trainID作为分区的第二个维度，产生30个范围分区。
```
def createDatabase(dbName){
	tableSchema = table(100:0,`trainID`ts`tag0001`tag0002`tag0003 ,[INT,TIMESTAMP, FLOAT,DOUBLE,LONG])
	
	if(exists(dbName))
		dropDatabase(dbName)
	db1 = database("",VALUE,today()..(today()+3))
	db2 = database("",RANGE,0..30*10+1)
	db = database(dbName,COMPO,[db1,db2])
	dfsTable = db.createPartitionedTable(tableSchema,"trainInfoTable",`ts`trainID)
}
login("admin","123456")
createDatabase("dfs://testDB")
```

用以下代码将300辆车的数据写入到分布式表中，每200毫秒写入一次。
```
//模拟数据产生
def simulateData(trainVector){
	num = size(trainVector)
	return table(take(trainVector,num) as trainID, take(now(),num) as ts, rand(20..41,num) as tag0001, rand(30..71,num) as tag0002, rand(70..151,num) as tag0003)
}
//将数据写入数据表。写入次数为batches。
def simulate(host,port,trainVector,batches){
	h = xdb(host,port,"admin","123456")
	for(i in 0:batches){
		t=simulateData(trainVector)
		h("append!{loadTable('dfs://testDB', 'trainInfoTable')}", t)
		sleep(200)
    }
}
```

然后，使用各种方法进行查询。

(1) 注册快照引擎，然后查询：
```
registerSnapshotEngine("dfs://testDB", "trainInfoTable", `trainID)
timer select [64] * from loadTable("dfs://testDB", "trainInfoTable")
```

(2) 通过group by对表内记录分组，然后用last函数查找每个分组的最后一行记录。为了减少查询范围，增加了一个查询条件，即限制ts为最近一小时。
```
timer select last(ts), last(tag0001), last(tag0002), last(tag0003)
from loadTable('dfs://testDB', 'trainInfoTable') where ts > datetimeAdd(now(),-1,`h) group by trainID
```

(3) 通过group by对表内记录分组，然后用atImax函数找出每个分组的时间戳这列的最大值（即最新时间）所在行，然后返回该行的其他列数据。atImax函数的语法是atImax(location, value)，其中location和value是相同长度的向量或相同维度的矩阵。找出location中最大值所在的位置，就可以返回value中该位置对应的值。在查询表的数据时，location取时间戳列，value取其他状态列，就能查到表的最新记录。为了减少查询范围，增加了一个查询条件，即限制ts为最近一小时。

```
timer select atImax(ts,tag0001 ) as tag0001, atImax(ts,tag0002 ) as tag0002, atImax(ts,tag0003 ) as tag0003
from loadTable('dfs://testDB', 'trainInfoTable') where ts >datetimeAdd(now(),-1,`h) group by trainID
```
(4) 通过SQL扩展语句context by对表内记录进行分组，然后在组内按时间戳列进行csort降序排序，再和top一起使用，就可以用于获取每个分组中的最新记录。为了减少查询范围，增加了一个查询条件，即限制ts为最近一小时。
```
timer select top 1 * from loadTable('dfs://testDB', 'trainInfoTable') where ts >datetimeAdd(now(),-1,`h) context by trainID csort ts desc 
```

进行2次测试。第一次是刚开始向数据库中写入数据时，测试时当天的分区中的数据记录大约有10万条。第二次是长时间写入后，测试时当天的分区中的数据记录已有约4千万条。

|方法	         |第一次测试（刚开始写入时，单位：毫秒）|第二次测试（长时间写入后，单位：毫秒）|
|------------    |---|---|
|Snapshot Engine | 53| 55 |
|last            | 70| 723|
|atImax          | 71| 743|
|context by      | 72| 781|

从测试结果可以发现，用快照引擎查询最新记录的性能是最优的。而且由于它是返回内存中的快照，不受分区中记录数的影响，每次查询的时间都变化不大。而另外三种方法在查询时，会先把分区中的数据加载到内存中，所以当分区中的数据比较多时，会影响查询性能。
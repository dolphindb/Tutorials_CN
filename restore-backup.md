# DolphinDB流数备份恢复教程

备份时以表的分区为单位，每个单位生成一个二进制文件，包含元数据、schema、以及表内容。

恢复时也是如此，需要指定恢复哪些分区。

## backup(backupDir, sqlObj, [force=false])

用来对某张表的某些分区进行备份

- `backupDir`: string, 备份的根目录
- `sqlObj`: metacode, 用于选取想要备份的表，以及备份的分区范围，如`<select * from tbl where date = 2019.01.01>`
- `force`: bool, 是否强制备份。如果为否，只有当前元数据和已有备份中只有不一致时才会备份。

返回Int，表示备份了几个chunk。
执行后将在`backupDir`目录`backupDir/dbName/tableName`下存储元数据`meta.bin`和数据文件`<chunkID>.bin`。

## restore(backupDir, dbURL, tableName, partitionStr, [force=false], [outputTable])

用来恢复某张表的某些分区

- `backupDir`: string, 备份的根目录
- `dbURL`: string, dfs数据库路径，如`dfs://demo`
- `tableName`: string, 表示要恢复的表的名称
- `partitionStr`:string, 表示想要恢复的分区的范围，这个字符串将与备份过的分区的路径进行匹配。如`%2019%GOOG%`，参考`like`函数，表示所有路径中包含2019和GOOG的备份都要恢复。
- `force`: bool， 表示是否强制恢复。
- `outputTable`: table object，一张外部表。如果指定，将会把所有有关的Tablet中的数据保存到`outputTable`，而原来数据库中的表保持不变。

## listBackupTablet(backupDir, dbURL, tableName)
用来查看某个库下，某张表的所有备份信息

- `backupDir`: string, 备份的根目录
- `dbURL`: string, dfs数据库路径，如`dfs://demo`
- `tableName`: string, 表示要查看的表的名称

## getBackupTabletMeta(backupDir, dfsPath, tableName)

用来查看某张表，某个分区下的备份的信息，包含schema，cid，path等信息

- `backupDir`: string, 备份的根目录
- `dfsPath`: string, 形如`"dfs://db1x/1/20190101/GOOG"`，包含库名信息，以及分区信息。表示想要查看的表，所在的库，以及想要查看的分区。可以通过`listBackupTablet`获得
- `tableName`: string, 表示要查看的表的名称

## loadBackupTablet(backupDir, dfsPath, tableName)

用来查看某张表，某个分区下的备份的表的实际数据

- `backupDir`: string, 备份的根目录
- `dfsPath`: string, 形如`"dfs://db1x/1/20190101/GOOG"`，包含库名信息，以及分区信息。表示想要查看的表，所在的库，以及想要查看的分区。
- `tableName`: string, 表示要查看的表的名称

## 示例

```
login(`admin,`123456)

def benchmark(dbName, tableName, nid, metricNum,nappend, batchsize) {
	ids= 1..nid
	days = 2019.01.01..2019.01.30
	foo = 1..10
	sym = `GOOG`IBM`AAPL

	colNames = [`foo,`date,`id,`sym]
	colTypes= [INT,DATE,INT,SYMBOL]
	for(i in 1..metricNum) {
		colNames.append!("p" + string(i))
		colTypes.append!(LONG)
	}
	db0=database("",VALUE,foo)
	db1=database("",VALUE,days)
	db2=database("",VALUE,sym)
	db = NULL
	//if(existsDatabase(dbName)) {
	//	dropDatabase(dbName)
	//}
	db=database(dbName,COMPO,[db0,db1,db2])
	t = table(1:0,colNames,colTypes)
	//createPartitionedTable(db,t,tableName,`id`date`sym)

	n = batchsize
	basicTable = table(n:n,colNames,colTypes)
	basicTable[`foo] = 1
	basicTable[`id] = 1
	basicTable[`date] = take(days, n)
	basicTable[`sym]=take(sym, n)
	for(i in 4..(colNames.size()-1)) {
		basicTable[colNames[i]] = i * i
	}

	tbl_ = database(dbName).loadTable(tableName)
	t0 = now()

	for(i in 1..nappend) {
    tbl_.append!(basicTable)
		//tx2 = now()
		//print(string(i) + " " + string(tx2 - tx1))
	}
	t1 = now()
	return (t1-t0, tbl_)
}
dbURL = "dfs://db1x"
tableName = "t"
dir = "/home/wenxing/backup/"

days = 2019.01.01..2019.01.30
benchmark(dbURL, tableName, 20,300,1,100000)

t = database(dbURL).loadTable(tableName)
exec count(*) from t
backup(dir, <select * from t>)

restore(dir, dbURL, tableName, "%", false)

dropPartition(database(dbURL), "/1/20190101/GOOG")

listBackupTablet(dir, dbURL, tableName)
getBackupTabletMeta(dir, "dfs://db1x/1/20190101/GOOG", tableName)
loadBackupTablet(dir, "dfs://db1x/1/20190101/GOOG", tableName)
```

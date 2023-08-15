# 数据备份恢复教程

DolphinDB database 提供了一系列函数，用于数据备份与恢复。数据备份和恢复时均以表的分区为单位。

## 1. 备份

DolphinDB提供了[`backup`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/b/backup.html)函数对分布式数据库进行备份。备份是以分区为单位进行的，可对指定数据表的部分或全部分区进行备份，支持全量备份或增量备份。

备份需要指定存放备份文件的路径 backupDir 与需要备份的数据（用 SQL 语句表示）。备份后，系统会在 `<backupDir>/<dbName>/<tbName>` 目录下生成元数据文件 _metaData.bin 和数据文件 <chunkID>.bin，每个分区备份为一个数据文件。


下例说明如何备份数据库。

* 数据库的建库建表的脚本如下所示。采用复合分区，按天进行值分区，按照风机编号进行值分区。共有10台风机：
```
m = "tag" + string(decimalFormat(1..523,'000'))
tableSchema = table(100:0,`wntId`insertDate join m, [INT,DATETIME] join take(FLOAT,523) )
db1 = database("",VALUE,2020.01.01..2020.12.30)
db2 = database("",VALUE,1..10)
db = database("dfs://ddb",COMPO,[db1,db2])
db.createPartitionedTable(tableSchema,"windTurbine",`insertDate`wntId)
```
* 写入2020.01.01~2020.01.03三天的数据后，备份前2天的数据，代码如下，其中 parallel 参数表示是否进行并行备份，是 DolphinDB 1.10.13/1.20.3 版本新增的功能：
```
backup(backupDir="/hdd/hdd1/backup/",sqlObj=<select * from loadTable("dfs://ddb","windTurbine") where insertDate<=2020.01.02T23:59:59 >,parallel=true)

```
执行后返回结果20，说明备份了20个分区的数据。登录服务器，用 tree 命令列出目录的内容如下：
```
[dolphindb@localhost backup]$ tree /hdd/hdd1/backup/ -L 3 -t
/hdd/hdd1/backup/
└── ddb
    └── windTurbine
        ├── 02ddcb20-8872-af9d-ca46-f42a42239c78
        ├── 237e6e64-d62e-13bf-0443-fa7a974f7c42
        ├── 4d04471d-fff8-2e9a-7742-a0228af21bad
        ├── 4e7e014f-1346-c4b0-264e-e9d15de494cb
        ├── 4f2aade8-97ce-bca9-934f-b0b10f0da1fe
        ├── 6256d8f2-cc53-7a87-5b43-6cce55b38933
        ├── 77a4ac82-739c-389b-994b-22f84cb11417
        ├── 8c27389b-4689-7697-d243-2b16dbca8354
        ├── 8dd539b3-f3fc-b39c-6842-039dbec1ceb1
        ├── 90a5af5f-1161-23af-ea42-877999866f44
        ├── fd6b658c-47eb-e69e-164e-601c5b51daed
        ├── _metaData
        ├── 167a9165-05ec-e093-b74a-c6121939ebf0
        ├── 3afb5932-a8fa-9e93-ff4c-120c1223dcf6
        ├── 62d47049-155d-83a7-af48-36c8969072a7
        ├── b20422a9-487d-8eb7-7143-3597a3b44796
        ├── 2ae9676f-dbe7-669a-7144-68a02572df3e
        ├── 4559d6db-bb7a-efb8-164e-3198127a7c3d
        ├── 72e15689-4bf7-44a9-b84e-16fb8e856a6d
        ├── 8652f2f0-9d60-40aa-4e44-9d77bd1309f6
        ├── dolphindb.lock
        └── e266ab82-6ef9-e289-d241-d9218be59dde

2 directories, 22 files
```
从中可以看到，备份目录下根据数据库名和表名生成了2层子目录 ddb/windTurbine，在其下还有20个分区数据文件和1个元数据文件 _metaData。

* 增量备份
```
backup(backupDir="/hdd/hdd1/backup/",sqlObj=<select *  from loadTable("dfs://ddb","windTurbine") >,force=false,parallel=true)

```
执行后返回结果10，说明备份了10个分区的数据。登录服务器，用 tree 命令列出目录的内容如下：
```
[xjqian@localhost windTurbine]$ tree /hdd/hdd1/backup/ -L 3 -t
/hdd/hdd1/backup/
└── ddb
    └── windTurbine
        ├── 04eceea9-53d7-1389-4044-d31538025361
        ├── 14ff1d37-2ea7-7596-d94d-12ecfd8be197
        ├── 81f7236f-83b3-ef81-f648-3b8db67c04fa
        ├── 846aaf74-6c51-9a91-6c44-fb1e2cf93036
        ├── bcb94ce8-0e06-2fad-b946-774fcedc978d
        ├── c38cb06c-fd7f-608a-b148-b0f6a9883c5c
        ├── e5993354-cd4d-3ab0-0e4b-ea331e68a2df
        ├── _metaData
        ├── 401136d4-1fcd-408c-b84b-20c2af7b3fe8
        ├── 54076219-0904-97a2-1a4a-d076f35f76fe
        ├── b51f4f36-be16-cfad-a440-d04ac36b6791
        ├── dolphindb.lock
        ├── 02ddcb20-8872-af9d-ca46-f42a42239c78
        ├── 237e6e64-d62e-13bf-0443-fa7a974f7c42
        ├── 4d04471d-fff8-2e9a-7742-a0228af21bad
        ├── 4e7e014f-1346-c4b0-264e-e9d15de494cb
        ├── 4f2aade8-97ce-bca9-934f-b0b10f0da1fe
        ├── 6256d8f2-cc53-7a87-5b43-6cce55b38933
        ├── 77a4ac82-739c-389b-994b-22f84cb11417
        ├── 8c27389b-4689-7697-d243-2b16dbca8354
        ├── 8dd539b3-f3fc-b39c-6842-039dbec1ceb1
        ├── 90a5af5f-1161-23af-ea42-877999866f44
        ├── fd6b658c-47eb-e69e-164e-601c5b51daed
        ├── 167a9165-05ec-e093-b74a-c6121939ebf0
        ├── 3afb5932-a8fa-9e93-ff4c-120c1223dcf6
        ├── 62d47049-155d-83a7-af48-36c8969072a7
        ├── b20422a9-487d-8eb7-7143-3597a3b44796
        ├── 2ae9676f-dbe7-669a-7144-68a02572df3e
        ├── 4559d6db-bb7a-efb8-164e-3198127a7c3d
        ├── 72e15689-4bf7-44a9-b84e-16fb8e856a6d
        ├── 8652f2f0-9d60-40aa-4e44-9d77bd1309f6
        └── e266ab82-6ef9-e289-d241-d9218be59dde

2 directories, 32 files

```
可以看到数据文件比之前多了10个，恰好是2020年1月3日的完整数据。

* 每天备份

可用定时作业来实现。下面例子在每天凌晨00:05:00开始备份前一天的数据：
```
scheduleJob(`backupJob, "backupDB", backup{"/hdd/hdd1/backup/"+(today()-1).format("yyyyMMdd"),<select * from loadTable("dfs://ddb","windTurbine") where tm between datetime(today()-1) : (today().datetime()-1) >,false,true}, 00:05m, today(), 2030.12.31, 'D');
```

## 2. 恢复

DolphinDB提供两种数据恢复的方法：
- 使用[`migrate`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/m/migrate.html)函数
- 使用[`restore`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/r/restore.html)函数

`migrate` 函数以表为单位恢复，可以批量恢复多个表的全部数据；而 `restore` 函数以分区为单位恢复，每次恢复一个表中部分或全部分区的数据。
使用 `migrate` 函数时，用户无需创建新数据库，系统会自动创建新数据库；而 `restore` 函数需要用户先建库建表，而且数据库名称必须与备份的分布式数据库的名称一致。

下面的例子恢复2020年1月份的数据到原表，其中备份文件是上一小节的定时作业按天生成：
```
day=2020.01.01
for(i in 1..31){
	path="/hdd/hdd1/backup/"+temporalFormat(day, "yyyyMMdd") + "/";
	day=datetimeAdd(day,1,`d)
	if(!exists(path)) continue;
	print "restoring " + path;
	restore(backupDir=path,dbPath="dfs://ddb",tableName="windTurbine",partition="%",force=true);
}
```

下面的例子把2020年1月份的数据恢复到一个新的数据库 dfs://db1 和表 equip，其中先用 `migrate` 恢复第一天的数据，然后用 `migrate` 把剩余备份数据恢复到临时表，再导入 equip：
```
migrate("/hdd/hdd1/backup/20200101/","dfs://ddb","windTurbine","dfs://db1","equip")
day=2020.01.02
newTable=loadTable("dfs://db1","equip")
for(i in 2:31){
	path="/hdd/hdd1/backup/"+temporalFormat(day, "yyyyMMdd") + "/";
	day=datetimeAdd(day,1,`d)
	if(!exists(path)) continue;
	print "restoring " + path;
	t=migrate(path,"dfs://ddb","windTurbine","dfs://db1","tmp") 
	if(t['success'][0]==false){
		print t['errorMsg'][0]
		continue
	}
	newTable.append!(select * from loadTable("dfs://db1","tmp") where tm between datetime(day-1) : (day.datetime()-1) > )
	database("dfs://db1").dropTable("tmp")
}

```

## 3. 备份与恢复管理

### 3.1 getBackupList

[`getBackupList`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getBackupList.html)函数用来查看某个分布式表的所有备份信息，返回一张表，每个分区对应一行记录。

比如对上节备份的数据，运行：
```
getBackupList("/hdd/hdd1/backup/", "dfs://ddb", "windTurbine")
```
得到如下结果：

|chunkID|	chunkPath|	cid|
---|---|---
|72e15689-4bf7-44a9-b84e-16fb8e856a6d|	dfs://ddb/20200101/1|	10,413
|8652f2f0-9d60-40aa-4e44-9d77bd1309f6|	dfs://ddb/20200101/2|	10,417
|4559d6db-bb7a-efb8-164e-3198127a7c3d|	dfs://ddb/20200101/3|	10,421
|2ae9676f-dbe7-669a-7144-68a02572df3e|	dfs://ddb/20200101/4|	10,425
|e266ab82-6ef9-e289-d241-d9218be59dde|	dfs://ddb/20200101/5|	10,429
|62d47049-155d-83a7-af48-36c8969072a7|	dfs://ddb/20200101/6|	10,414
|3afb5932-a8fa-9e93-ff4c-120c1223dcf6|	dfs://ddb/20200101/7|	10,418
|b20422a9-487d-8eb7-7143-3597a3b44796|	dfs://ddb/20200101/8|	10,422
|167a9165-05ec-e093-b74a-c6121939ebf0|	dfs://ddb/20200101/9|	10,426
|4d04471d-fff8-2e9a-7742-a0228af21bad|	dfs://ddb/20200101/10|	10,430
|02ddcb20-8872-af9d-ca46-f42a42239c78|	dfs://ddb/20200102/1|	10,415
|8dd539b3-f3fc-b39c-6842-039dbec1ceb1|	dfs://ddb/20200102/2|	10,419
|fd6b658c-47eb-e69e-164e-601c5b51daed|	dfs://ddb/20200102/3|	10,423
|90a5af5f-1161-23af-ea42-877999866f44|	dfs://ddb/20200102/5|	10,431
|237e6e64-d62e-13bf-0443-fa7a974f7c42|	dfs://ddb/20200102/6|	10,416
|8c27389b-4689-7697-d243-2b16dbca8354|	dfs://ddb/20200102/7|	10,420
|6256d8f2-cc53-7a87-5b43-6cce55b38933|	dfs://ddb/20200102/8|	10,424
|4e7e014f-1346-c4b0-264e-e9d15de494cb|	dfs://ddb/20200102/9|	10,428
|77a4ac82-739c-389b-994b-22f84cb11417|	dfs://ddb/20200102/10|	10,432
|54076219-0904-97a2-1a4a-d076f35f76fe|	dfs://ddb/20200103/1|	10,433
|b51f4f36-be16-cfad-a440-d04ac36b6791|	dfs://ddb/20200103/2|	10,436
|401136d4-1fcd-408c-b84b-20c2af7b3fe8|	dfs://ddb/20200103/3|	10,438
|14ff1d37-2ea7-7596-d94d-12ecfd8be197|	dfs://ddb/20200103/4|	10,439
|846aaf74-6c51-9a91-6c44-fb1e2cf93036|	dfs://ddb/20200103/5|	10,442
|c38cb06c-fd7f-608a-b148-b0f6a9883c5c|	dfs://ddb/20200103/6|	10,434
|e5993354-cd4d-3ab0-0e4b-ea331e68a2df|	dfs://ddb/20200103/7|	10,435
|04eceea9-53d7-1389-4044-d31538025361|	dfs://ddb/20200103/8|	10,437
|bcb94ce8-0e06-2fad-b946-774fcedc978d|	dfs://ddb/20200103/9|	10,440
|81f7236f-83b3-ef81-f648-3b8db67c04fa|	dfs://ddb/20200103/10|	10,441

### 3.2 getBackupMeta

[`getBackupMeta`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getBackupMeta.html)函数用来查看某张表中某个分区的备份的信息，返回一个字典，包含schema，cid，path等信息。

示例如下：
```
getBackupMeta("/hdd/hdd1/backup/","dfs://ddb","/20200103/10","windTurbine")
```
运行后结果如下：
```
schema->
name       typeString typeInt comment
---------- ---------- ------- -------
wntId      INT        4              
insertDate DATETIME   11             
tag001     FLOAT      15             
tag002     FLOAT      15             
tag003     FLOAT      15             
...

dfsPath->dfs://ddb/20200103/10
chunkID->81f7236f-83b3-ef81-f648-3b8db67c04fa
cid->10441
```
### 3.3 loadBackup

[`loadBackup`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/l/loadBackup.html)函数用于加载指定分布式表中某个分区的备份数据。

```
loadBackup("/hdd/hdd1/backup/","dfs://ddb","/20200103/10","windTurbine")
```
运行后结果如下：

|wntId|insertDate|	tag001|	tags	|tag523|
|---|---|---|---|---|
|10|2020.01.03T00:00:00|	90.3187|	...|1|
|10|2020.01.03T00:00:01|	95.3273|	...|1|
|...||||
|10|2020.01.03T23:59:59|	94.6378|	...|1|


## 4. 示例

下面的例子创建了一个组合分区的数据库 dfs://compoDB。

```
n=1000000
ID=rand(100, n)
dates=2017.08.07..2017.08.11
date=rand(dates, n)
x=rand(10.0, n)
t=table(ID, date, x);

dbDate = database(, VALUE, 2017.08.07..2017.08.11)
dbID=database(, RANGE, 0 50 100);
db = database("dfs://compoDB", COMPO, [dbDate, dbID]);
pt = db.createPartitionedTable(t, `pt, `date`ID)
pt.append!(t);
```

备份表 pt 的所有数据：
```
backup("/home/DolphinDB/backup",<select * from loadTable("dfs://compoDB","pt")>,true);
```

SQL 元代码中可以添加 where 条件。例如，备份 date>2017.08.10 的数据。
```
backup("/home/DolphinDB/backup",<select * from loadTable("dfs://compoDB","pt") where date>2017.08.10>,true);
```

查看表 pt 的备份信息：
```
getBackupList("/home/DolphinDB/backup","dfs://compoDB","pt");
```

查看 20120810/0_50 分区的备份信息：
```
getBackupMeta("/home/DolphinDB/backup","dfs://compoDB","/20170810/0_50","pt");
```

加载 20120810/0_50 分区的备份数据到内存：
```
loadBackup("/home/DolphinDB/backup","dfs://compoDB","/20170810/0_50","pt");
```
请注意，如用户使用1.30.16/2.00.4及以上版本创建数据库，可以使用以下代码在查看及加载备份数据时指定参数 partition。

```
list=getBackupList("/home/DolphinDB/backup","dfs://compoDB","pt").chunkPath;
path=list[0][regexFind(list[0],"/20170807/0_50"):]
getBackupMeta("/home/DolphinDB/backup","dfs://compoDB", path, "pt");
loadBackup("/home/DolphinDB/backup","dfs://compoDB", path, "pt");
```

把所有数据恢复到原表：
```
restore("/home/DolphinDB/backup","dfs://compoDB","pt","%",true);
```

在数据库 dfs://compoDB 中创建一个与pt结构相同的表 temp：
```
temp=db.createPartitionedTable(t, `temp, `date`ID);
```

把 pt 中2017.08.10的数据恢复到 temp 中：
```
restore("/home/DolphinDB/backup","dfs://compoDB","pt","%20170810%",true,temp);
```

把所有数据恢复到一个新的库 dfs://newCompoDB 和表 pt：
```
migrate("/home/DolphinDB/backup","dfs://compoDB","pt","dfs://newCompoDB","pt");

```
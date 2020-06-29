# 数据备份恢复教程

DolphinDB database 提供了一系列函数，用于数据备份与恢复。数据备份和回复时均以表的分区为单位

## 1. 备份

`backup`函数对指定数据表的某些或全部分区进行备份，返回一个整数，表示备份成功的分区数量。执行后将在backupDir目录backupDir/dbName/tableName下存储元数据meta.bin和数据文件<chunkID>.bin。

backup(backupDir, sqlObj, [force=false])

- backupDir: 字符串, 表示存放备份数据的目录。
- sqlObj: SQL元数据, 表示需要备份的数据，如<select * from tbl where date = 2019.01.01>。
- force: 布尔值, 表示是否强制备份。默认值为false，表示表示只对上一次备份之后发生改变的分区进行备份。

## 2. 恢复

`restore`函数用于恢复某张表的某些分区，返回一个字符串向量，表示恢复成功的分区路径。

restore(backupDir, dbPath, tableName, partitionStr, [force=false], [outputTable])

- backupDir: 字符串, 表示备份的根目录。
- dbPath: 字符串, 分布式数据库的路径，如dfs://demo。
- tableName: 字符串, 表示要恢复的表的名称。
- partitionStr: 字符串，表示想要恢复的分区的路径。分区路径可以包含通配符，%表示恢复已备份的所有分区，%2019%GOOG%表示所有路径中包含2019和GOOG的备份都要恢复。
- force: 布尔值，表示是否强制恢复。默认是为false，只有当前元数据与备份数据不一致时，才会恢复。
- outputTable: 分布式表，该表的结构必须与要恢复的表结构一致。如果没有指定outputTable，恢复后的数据会存放到原表；如果指定了outputTable，恢复后的数据会存放到该表中，而原数据表保持不变。

## 3. 备份与恢复管理

### 3.1 getBackupList

`getBackupList`函数用来查看某个分布式表的所有备份信息，返回的是一张表，每个分区对应一行记录。

getBackupList(backupDir, dbURL, tableName)

- backupDir: 字符串, 表示备份的根目录。
- dbURL: 字符串, 分布式数据库路径，如dfs://demo。
- tableName: 字符串, 表示要查看的表的名称。

### 3.2 getBackupMeta

`getBackupMeta`函数用来查看某张表，某个分区的备份的信息，返回的结果是一个字典，包含schema，cid，path等信息。

getBackupMeta(backupDir, dfsPath, tableName)

- backupDir: 字符串, 表示备份的根目录。
- dfsPath: 字符串，表示分区的完整路径，包含库名信息以及分区信息。例如 "dfs://db1/1/20190101/GOOG"。
- tableName: 字符串, 表示要查看的表的名称。

### 3.3 loadBackup

`loadBackup`函数用于加载指定分布式表中某个分区的备份数据。

loadBackup(backupDir, dfsPath, tableName)

- backupDir: 字符串, 表示备份的根目录。
- dfsPath: 字符串, 表示分区的完整路径，包含库名信息以及分区信息。例如 "dfs://db1/1/20190101/GOOG"。
- tableName: 字符串, 表示要查看的表的名称。

## 4. 示例

下面的例子创建了一个组合分区的数据库dfs://compoDB。

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

备份表pt的所有数据：

```
backup("/home/DolphinDB/backup",<select * from loadTable("dfs://compoDB","pt")>,true);
```

SQL元代码中可以添加where条件。例如，备份date>2017.08.10的数据。

```
backup("/home/DolphinDB/backup",<select * from loadTable("dfs://compoDB","pt") where date>2017.08.10>,true);
```

查看表pt的备份信息：

```
getBackupList("/home/DolphinDB/backup","dfs://compoDB","pt");
```

查看20120810/0_50分区的备份信息：

```
getBackupMeta("/home/DolphinDB/backup","dfs://compoDB/20170810/0_50","pt");
```

查看20120810/0_50分区的备份数据：

```
loadBackup("/home/DolphinDB/backup","dfs://compoDB/20170810/0_50","pt");
```

把所有数据恢复到原表：

```
restore("/home/DolphinDB/backup","dfs://compoDB","pt","%",true);
```

在数据库 dfs://compoDB 中创建一个与pt结构相同的表temp：

```
temp=db.createPartitionedTable(t, `pt, `date`ID);
```

把pt中2017.08.10的数据恢复到temp中：

```
restore("/home/DolphinDB/backup","dfs://compoDB","pt","%20170810%",true,temp);
```


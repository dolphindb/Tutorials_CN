# DolphinDB数据备份恢复教程

DolphinDB数据备份时以表的分区为单位，每个单位生成一个二进制文件，包含元数据、schema、以及表内容。恢复时也是如此，需要指定恢复哪些分区。

DolphinDB提供了一系列函数，用于数据备份与恢复。

## 1. 备份

`backup`函数对某张表的某些分区进行备份，返回一个整数，表示备份成功的分区数量。执行后将在`backupDir`目录`backupDir/dbName/tableName`下存储元数据`meta.bin`和数据文件`<chunkID>.bin`。

backup(backupDir, sqlObj, [force=false])

- `backupDir`: 字符串, 表示备份的根目录。
- `sqlObj`: SQL元数据, 表示要备份的数据，如`<select * from tbl where date = 2019.01.01>`。
- `force`: 布尔值, 是否强制备份。默认值为false，表示只有当前元数据和已有备份中不一致时才会备份。

## 2. 恢复

`restore`函数用于恢复某张表的某些分区，返回一个字符串向量，表示恢复成功的分区路径。

restore(backupDir, dbPath, tableName, partitionStr, [force=false], [outputTable])

- `backupDir`: 字符串, 表示备份的根目录。
- `dbPath`: 字符串, 分布式数据库的路径，如`dfs://demo`。
- `tableName`: 字符串, 表示要恢复的表的名称。
- `partitionStr`:字符串, 表示想要恢复的分区的路径。分区路径可以包含通配符，`%`表示恢复已备份的所有分区，`%2019%GOOG%`表示所有路径中包含2019和GOOG的备份都要恢复。
- `force`: 布尔值，表示是否强制恢复。默认是为false，只有当前元数据与备份数据不一致时，才会恢复。
- `outputTable`: 分布式表，该表的结构必须与要恢复的表结构一致。如果没有指定outputTable，恢复后的数据会存放到原表；如果指定了outputTable，恢复后的数据会存放到该表中，而原数据表保持不变。

## 3. 备份与恢复管理

### 3.1 getBackupList

`getBackupList`函数用来查看某个分布式表的所有备份信息，返回的是一张表，每个分区对应一行记录。

getBackupList(backupDir, dbURL, tableName)

- `backupDir`: 字符串, 表示备份的根目录。
- `dbURL`: 字符串, 分布式数据库路径，如`dfs://demo`。
- `tableName`: 字符串, 表示要查看的表的名称。

### 3.2 getBackupMeta

`getBackupMeta`函数用来查看某张表，某个分区的备份的信息，返回的结果是一个字典，包含schema，cid，path等信息。

getBackupMeta(backupDir, dfsPath, tableName)

- `backupDir`: 字符串, 表示备份的根目录。
- `dfsPath`: 字符串，表示分区的完整路径，例如`"dfs://db1/1/20190101/GOOG"`，包含库名信息，以及分区信息。
- `tableName`: 字符串, 表示要查看的表的名称

### 3.3 loadBackup

`loadBackup`函数用于加载指定分布式表中某个分区的备份数据。

loadBackup(backupDir, dfsPath, tableName)

- `backupDir`: 字符串, 表示备份的根目录。
- `dfsPath`: 字符串, 表示分区的完整路径，例如`"dfs://db1/1/20190101/GOOG"`，包含库名信息，以及分区信息。
- `tableName`: 字符串, 表示要查看的表的名称

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

备份表pt的所有数据。

```
backup("/home/DolphinDB/backup",<select * from loadTable("dfs://compoDB","pt")>,true);
```

SQL元代码中可以添加where条件。例如，备份date>2017.08.10的数据。

```
backup("/home/DolphinDB/backup",<select * from loadTable("dfs://compoDB","pt") where date>2017.08.10>,true);
```

查看表pt的备份信息。

```
getBackupList("/home/DolphinDB/backup","dfs://compoDB","pt");
```

查看20120810/0_50分区的备份信息。

```
getBackupMeta("/home/DolphinDB/backup","dfs://compoDB/20170810/0_50","pt");
```

查看20120810/0_50分区的备份数据。

```
loadBackup("/home/DolphinDB/backup","dfs://compoDB/20170810/0_50","pt");
```

把所有数据恢复到原表。

```
restore("/home/DolphinDB/backup","dfs://compoDB","pt","%",true);
```

在数据库dfs://compoDB中创建一个与pt结构相同的表temp。

```
temp=db.createPartitionedTable(t, `pt, `date`ID);
```

把pt中2017.08.10的数据恢复到temp中。

```
restore("/home/DolphinDB/backup","dfs://compoDB","pt","%20170810%",true,temp);
```


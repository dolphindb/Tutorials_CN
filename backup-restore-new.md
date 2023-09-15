- [DolphinDB教程：数据备份以及恢复](#dolphindb教程数据备份以及恢复)
  - [适用场景](#适用场景)
  - [特性](#特性)
  - [模拟数据](#模拟数据)
  - [1. 数据备份](#1-数据备份)
    - [1.1 备份单个数据库](#11-备份单个数据库)
    - [1.2 备份单张表](#12-备份单张表)
    - [1.3 备份分区](#13-备份分区)
  - [2. 备份文件检验函数](#2-备份文件检验函数)
    - [2.1 getBackupStatus](#21-getbackupstatus)
    - [2.2 getBackupList](#22-getbackuplist)
    - [2.3 getBackupMeta](#23-getbackupmeta)
    - [2.4 checkBackup](#24-checkbackup)
    - [2.5 备份文件检查最佳实践](#25-备份文件检查最佳实践)
      - [2.5.1 判断备份任务是否正常完成](#251-判断备份任务是否正常完成)
      - [2.5.2 判断备份文件是否损坏](#252-判断备份文件是否损坏)
  - [3. 数据恢复](#3-数据恢复)
    - [3.1 恢复单个数据库](#31-恢复单个数据库)
    - [3.2 恢复单张表](#32-恢复单张表)
    - [3.3 恢复单个分区](#33-恢复单个分区)
    - [3.4 恢复整个集群](#34-恢复整个集群)
    - [3.5 判断恢复任务是否正常完成](#35-判断恢复任务是否正常完成)
  - [4. 备份恢复的性能](#4-备份恢复的性能)
  - [5. FAQ](#5-faq)
    - [5.1 是否支持恢复到某个时间点？](#51-是否支持恢复到某个时间点)
    - [5.2 备份时所有分区的时间点是否一致？](#52-备份时所有分区的时间点是否一致)
    - [5.3 是否支持断点续备/恢复?](#53-是否支持断点续备恢复)
    - [5.4 是否支持增量备份/恢复？](#54-是否支持增量备份恢复)
    - [5.5 如何查看备份进度？](#55-如何查看备份进度)
    - [5.6 如何检查备份是否完成？](#56-如何检查备份是否完成)
    - [5.7 如何检查恢复是否完成？](#57-如何检查恢复是否完成)

# DolphinDB教程：数据备份以及恢复

本文适用于 DolphinDB 如下版本：
- 130系列：1.30.20及以后的版本
- 200系列：2.00.8及以后的版本。

## 适用场景

本教程适用于整个集群/数据库/表/分区的数据备份、恢复，以及大数据量的数据迁移。如果进行小规模的集群间数据同步，可以参考[DolphinDB 集群间数据库同步的第二章](https://gitee.com/dolphindb/Tutorials_CN/blob/master/data_synchronization_between_clusters.md#2-%E5%9C%A8%E7%BA%BF%E6%96%B9%E5%BC%8F)。

## 特性
同2.00.8/1.30.20以前的版本的备份恢复功能相比，有如下的改进：

1. DolphinDB提供了拷贝文件的备份和恢复分布式数据库的方法，大大增加了备份和恢复的性能；

2. DolphinDB利用底层的 `backup` 和 `restore` 函数封装了不同场景下的备份和恢复函数。用户可以根据需要选择函数进行备份以及恢复。这大大增加了备份恢复功能的易用性；

3. DolphinDB 提供了更强大的备份文件校验功能，你可以在备份文件之后立刻检验文件的正确性以及完整性。

## 模拟数据
本教程对应的数据生成脚本见[附件1](./script/backup_restore/buildData.txt)。数据库结构如下图：

![dbStructure](./images/backup_restore/dbStructure.png)

可以看到，我们构建了两个数据库，分别是OLAP和TSDB数据库。在OLAP数据库中有两张表，`quotes`和`quotes_2`。

本教程各章节中使用的脚本，集合在[附件2](./script/backup_restore/backup_restore.txt)。

> 1. 备份和恢复任务有两种提交方式，一种是直接在客户端运行函数启动任务，另一种是通过`submitJob`提交任务到后台执行。鉴于备份和恢复的使用场景通常是大数据量，所需时间较长，建议将备份和恢复任务提交到后台执行，之后的脚本也都将采用这种方式。
> 2. 后台任务的状态可以通过`getRecentJobs`查询
> 3. 数据生成脚本运行之后，将往磁盘上写150G左右的数据，所以运行此脚本，请确保有足够的磁盘容量。如果磁盘容量不够，可以调节脚本里的`smallDates`变量，以减小数据量


## 1. 数据备份
现在 DolphinDB 提供了3种备份数据的方式：

(1) 备份单个数据库的数据

(2) 备份单张表的数据

(3) 备份部分分区的数据

如果你还需要更灵活的备份方式，可以查看 [DolphinDB用户手册](https://www.dolphindb.cn/cn/help/DatabaseandDistributedComputing/DatabaseOperations/BackupandRestore.html#migrage-restore)，其中有更详细的介绍。

> 注意：
> 1. 到2.00.8版本，备份暂时只能将文件放在运行备份任务的数据节点所在的机器的目录下。
> 2. DolphinDB 的备份保证了备份的是在同一时间点的数据。为此，DolphinDB在备份时会给数据加锁（如果使用backupDB则对数据库加锁，如果使用backupTable则对整个表加锁）。加锁期间数据可读但是不可写入。为了避免数据写入失败，请尽量选择没有写入任务的时候进行数据备份

### 1.1 备份单个数据库
要备份单个数据库，可使用`backupDB`命令。

用例：将数据库`testdb`备份到`/home/$USER/backupDB`目录下（其中$USER为用户名称）
```
dbPath="dfs://testdb"
backupDir="/home/$USER/backupDB"
submitJob("backupDB","backup testdb",backupDB,backupDir,dbPath)
```

`backupDB` 有以下特性：
1. 支持断线续备：如果备份中断，再次运行`backupDB`即可从刚才中断时正在备份的分区开始备份，已备份好的分区无需重新备份一遍。
2. 支持分区级别的增量备份：对于在数据库和备份文件里同时存在的分区，
`backupDB`会检查数据库的分区和备份文件里对应的分区的更新时间。DolphinDB 只会对更新时间不一致的分区，用数据库里的数据覆盖备份文件里的。
3. 备份数据和数据库备份开始时的数据一致：备份文件中存在，而数据库中不存在的分区会被从备份文件中删除；备份文件中不存在，而数据库中存在的分区将会被备份；备份文件和数据库中都存在的分区，参见特性2

### 1.2 备份单张表
要备份一张表，可使用 `backupTable` 命令。

用例：将数据库 `testdb` 的 `quotes_2` 表备份到 `/home/$USER/backupTb` 目录下（其中$USER为用户名称）

```
dbPath="dfs://testdb"
tbName=`quotes_2
backupDir="/home/$USER/backupTb"
submitJob("backupTable","backup quotes_2 in testdb",backupTable,backupDir,dbPath,tbName)
```
`backupTable` 和`backupDB`有类似的特性，只不过`backupTable`是针对分布式表的，而`backupDB`是针对数据库的。

### 1.3 备份分区
要备份同一个表的部分或全部分区，可以将他们的分区路径放入一个向量，并将这个向量传入backup函数中

用例：将数据库 `testdb` 的 `quotes_2` 表的 `/Key3/tp/20120101` 和 `/Key4/tp/20120101` 分区备份到 `/home/$USER/backupPar` 目录下

```
dbPath="dfs://testdb"
tbName=`quotes_2
backupDir="/home/$USER/backupPar"
pars=["/Key3/tp/20120101","/Key4/tp/20120101"]
submitJob("backupPartitions","backup some partitions in quotes_2 in testdb",backup,backupDir,dbPath,false,true,true,tbName,pars)
```


## 2. 备份文件检验函数
运行备份任务之后，一个很重要的步骤是检查备份是否成功完成，以及备份文件的完整性。DolphinDB提供了多个函数，用以监控备份任务、检验备份文件：

- `getBackupStatus` 可以用来查看指定用户的backup/restore任务进度
- `getBackupList` 可以查看备份的所有分区的基本信息，
- `getBackupMeta` 可以查看备份文件的元数据信息，包括表的schema等信息
- `checkBackup` 可以用来检查备份文件的完整性


接下来我们将一一介绍他们，并且在最后给出检查备份文件的最佳实践。

> 注意：以上的操作需要在进行备份任务的数据节点运行。你可以通过`getNodeAlias`函数查看自己当前所在的数据节点别名。

### 2.1 getBackupStatus
getBackupStatus可以用来查看指定用户的backup/restore任务进度，同时可以预估任务完成时间。

用例：作为管理员使用 `getBackupStatus` 查看所有用户的 backup/restore 任务
```
login(`admin, `123456)
getBackupStatus()
```

> 管理员调用该函数时，若指定了 userName，则返回指定用户的 backup/restore 任务；否则返回所有用户的 backup/restore 任务
>
> 非管理员调用该函数时，只能返回当前用户的 backup/restore 任务。

返回如下：
![backupStatus](./images/backup_restore/getBackupStatus.png)

这张表里会返回每个任务涉及到的数据库和表名，涉及多少个分区，当前已完成了多少分区，和完成百分比。

如果任务还未完成，endTime会返回预估完成时间；如果任务已完成，endTime返回实际完成时间。

> 注意事项
> 1. 返回的表里对每张表的备份/恢复任务都有一行新纪录。例如上图的表里返回了两条记录，虽然只进行了一次备份。
> 
> 2. getBackupStatus只会返回这次数据节点启动之后的backup任务的进度。如果重启数据节点，之前的backup任务的进度将丢失

### 2.2 getBackupList
`getBackupList` 会返回一个分布式表的备份信息。返回为一张表，表里包含备份文件里这个表的所有的分区。每个分区对应表中的一行。表中会有chunkID、chunkPath、版本号、每个分区包含的行数和最后一次更新的时间戳。

用例：getBackupList获得`testdb`数据库中`quotes_2`的表的备份信息。
```
dbPath="dfs://testdb"
backupDir="/home/$USER/backupDB"
getBackupList(backupDir,dbPath,`quotes_2)
```
部分信息见下图：

![getBackupList](./images/backup_restore/getBackupList.png)

### 2.3 getBackupMeta
使用`getBackupMeta` 可以获得某一个分区的相关信息，比如所在的表的表结构，分区的完整路径，行数，ID，版本号等等。详情参见 [DolphinDB用户手册](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getBackupMeta.html)


### 2.4 checkBackup 

`checkBackup` 会检查备份文件中每个分区的 checksum。返回一张包含 checksum 检查不通过的分区的表。

用例：检查1.1节里的备份文件的完整性
```
dbPath="dfs://testdb"
backupDir="/home/$USER/backupDB"
checkBackup(backupDir,dbPath)
```
> checkBackup运行需要的时间和备份文件时所需的时间相近。

如果发现检查不通过的分区，需要通过backup，并设定force为true强制重新备份。如果设置force=false，只会检查分区的元数据信息，那么就有可能不会重新备份有问题的分区。

为了展示这个函数的用法，我们将做如下操作：
1. 运行 checkBackup
2. 将之前备份好的文件，选取一个移动到别的目录下，并建一个同名的空文件，再运行checkBackup
3. 将移除文件涉及的分区重新备份，并再次运行 checkBackup

为了更快返回结果，我们选择检查OLAP数据库中 quotes_2 的备份文件：
```
checkBackup(backupDir,dbPath,`quotes_2)
```
返回为空，说明校验通过。

然后将`086b0c1e-0386-95a4-4b4a-5038f4fd5d51`分区中volume.col文件移除，并添加一个同名的空文件。
再次运行checkBackukp，得到结果

![checkBackup](./images/backup_restore/checkBackup.png)

接下来我们将这个分区重新备份：
```
backup(backupDir=backupDir,dbPath=dbPath,force=true,parallel=true,snapshot=true,tableName=`quotes_2,partition="/Key4/tp/20120103")
```
再运行checkBackup，返回为空，说明校验通过。

所以checkBackup可以检查一个备份文件在备份完成之后是否损坏。

### 2.5 备份文件检查最佳实践
备份文件检查分为两个阶段，第一个阶段是备份任务结束之后，需要判断其是否正常完成。第二个阶段是在恢复之前，需要检查备份文件是否有损坏。以下的命令都需要在备份任务所在的节点执行。
#### 2.5.1 判断备份任务是否正常完成
1. 使用 `getBackupStatus`，返回备份任务信息。每一行代表一个表的备份。如果此次备份任务涉及的各行的completed列都为1，则说明任务成功。

2. 如果 `getBackupStatus` 查不到相关的表的备份信息，说明这个备份任务开始到查询期间，数据节点重启过，那么可以用`getBackupList`函数获取备份的各分区的行数，和数据库中对应的分区的行数进行比对。 
   
    >在2.00.9版本及之后，可以在log中查到backup成功或者失败的日志信息
    
3. 如果您提交的是后台备份任务，可以到您配置的`homeDir/<nodeAlias>/batchJobs`下寻找对应的任务。以1.2的任务为例，可以查询`backupTable.msg`，返回如下：
    ![1.4batchJobMsg](./images/backup_restore/1.4batchJobmsg.png)
  
    如果有"The job is done." 则说明任务已完成。

#### 2.5.2 判断备份文件是否损坏
使用 `checkBackup` 函数。具体方法见 [2.4节](#24-checkbackup)。

## 3. 数据恢复
现在 DolphinDB 提供了4种恢复数据的方式：

1. 恢复单个数据库
2. 恢复单张表
3. 恢复部分分区
4. 恢复整个集群

如果你还需要更灵活的恢复方式，可以查看 [DolphinDB用户手册](https://www.dolphindb.cn/cn/help/DatabaseandDistributedComputing/DatabaseOperations/BackupandRestore.html#migrage-restore)，其中介绍了更灵活的用法。

> 与备份不同，在数据恢复时，不会对涉及分区加锁。比如，在对一张表做恢复的同时，允许对这张表进行写入操作。不过我们建议在恢复的同时不要写入，否则会出现一些无法预测的行为，比如新的写入可能会留在数据库，也可能被恢复任务覆盖。

### 3.1 恢复单个数据库
要恢复单个数据库的数据，可使用 `restoreDB` 命令。

用例1：将1.1节中备份的数据恢复到新集群中
```
dbPath="dfs://testdb"
backupDir="/home/$USER/backupDB"
submitJob("restoreDB","restore testdb in new cluster",restoreDB,backupDir,dbPath)
```
> 注意：此处我们只是声明了备份文件的路径和需要恢复的数据库路径，而 `restoreDB` 函数会在新集群按照备份文件创建 `testdb` 数据库及库里所有的表，并将所有表的数据导入这个数据库

也可以将单个数据库的数据恢复到同一个集群的另一个数据库中，只需要指定数据库的路径即可：
```
# 将1.1节中备份的数据恢复到 restoredb 中
dbPath="dfs://testdb"
backupDir="/home/$USER/backupDB"
restoreDBPath="dfs://restoredb"
submitJob("restoreDB2","restore testdb to restoredb in the original cluster",restoreDB,backupDir,dbPath,restoreDBPath)
```

`restoreDB` 有以下特性：
1. 支持断线续恢复：如果恢复中断，再次运行 `restoreDB` 即可从刚才中断时正在恢复的分区开始恢复，已恢复好的分区无需重新恢复一遍。
2. 支持分区级别的增量恢复：对于在新数据库和备份文件里同时存在的分区，`restoreDB` 会检查新数据库的分区和备份文件里对应的分区的更新时间。DolphinDB 只会对更新时间不一致的分区，用备份文件里的数据覆盖新数据库里的。
3. 备份数据和新数据库恢复开始时的数据一致：备份文件中存在，而新数据库中不存在的分区会被恢复到新数据库中；备份文件中不存在，而数据库中存在的分区将会从新数据库中被删去；备份文件和数据库中都存在的分区，参见特性2

### 3.2 恢复单张表
要恢复单张表的数据，可使用 `restoreTable` 命令。
用例1：将1.2节中备份的数据恢复到新集群中
```
dbPath="dfs://testdb"
tbName=`quotes_2
backupDir="/home/$USER/backupTb"
submitJob("restoreTable","restore quotes_2 in testdb to new cluster",restoreTable,backupDir,dbPath,tbName)
```
> 注意：此处我们只是声明了备份文件的路径和需要恢复的表名，而 `restoreTable` 会在新集群按照备份文件创建 `testdb` 数据库和 `quotes` 表，并将数据恢复到这张表

也可以将单张表的数据恢复到同一个集群的另一个数据库中，只需要指定数据库的路径即可：
```
# 将1.2中备份的数据恢复到 restoredb2 的 quotes_2 表中
dbPath="dfs://testdb"
tbName=`quotes_2
backupDir="/home/$USER/backupTb"
restoreDBPath="dfs://restoredb2"
submitJob("restoreTable2","restore quotes_2 in testdb to quotes_2 in restoredb",restoreTable,backupDir,dbPath,tbName,restoreDBPath)
```

也可以将单张表的数据恢复到同一个数据库的另一张表中，只需要指定表名即可
```
# 将1.2中备份的数据恢复到 testdb 的 quotes_restore 表中。
dbPath="dfs://testdb"
tbName=`quotes_2
backupDir="/home/$USER/backupTb"
restoreTb="quotes_restore"
submitJob("restoreTable3","restore quotes_2 to quotes_restore in testdb",restoreTable,backupDir,dbPath,tbName,,restoreTb)
```
`restoreTable` 和`restoreDB`有类似的特性，只不过`restoreTable`是针对分布式表的，而`restoreDB`是针对数据库的。

### 3.3 恢复单个分区
要恢复同一个表的部分分区，可以使用 `restore` 函数。和backup备份分区时略有不同，restore中的partition参数只支持传入一个标量，这个标量中可以使用通配符，去匹配多个分区。比如，`%/Key4/tp/%` 可以匹配 `/Key4/tp/20120101`，`/Key4/tp/20120103`，`/Key4/tp/20120104`...等分区。

用例：将1.3节中备份的分区恢复到新数据库中

```
dbPath="dfs://testdb"
backupDir="/home/$USER/backupPar"
tbName=`quotes_2
pars=["/testdb/Key3/tp/20120101","/testdb/Key4/tp/20120101"]
for (par in pars){
	restore(backupDir,dbPath,tbName,par,false,,true,true)
}
```

### 3.4 恢复整个集群
如果需要将整个集群的数据进行迁移，可以先将各个数据库备份至同一个目录下，然后通过`migrate`函数进行恢复。

用例：备份两个数据库`testdb`和`testdb_tsdb`至目录下，然后使用migrate在新集群恢复
```
//旧集群备份testdb和testdb_tsdb
dbPath="dfs://testdb"
dbPath2="dfs://testdb_tsdb"
backupDir="/home/$USER/migrate"
submitJob("backupForMigrate","backup testdb for migrate",backupDB,backupDir,dbPath)
submitJob("backupForMigrate2","backup testdb_tsdb for migrate",backupDB,backupDir,dbPath2)

//备份完成后，在新集群恢复这两个数据库
backupDir="/home/$USER/migrate"
submitJob("migrate","migrate testdb and testdb_tsdb to new cluster",migrate,backupDir)
```
`migrate`和`restoreDB`类似，但是有如下两个区别：
1. migrate可以恢复多个数据库，而restoreDB只能恢复单个数据库。
2. 当恢复后的数据库名称、表名称与原数据库、原表一致时，migrate 要求原数据库、原表已经被删除，否则无法恢复，而 restoreDB 无此限制。所以migrate无法用于增量恢复和断点续恢复，而一般用于新的集群刚部署完成的时候的数据迁移。有关更多数据备份与还原的函数选择，可参考 [数据备份与恢复 — DolphinDB 2.0 文档](https://www.dolphindb.cn/cn/help/DatabaseandDistributedComputing/DatabaseOperations/BackupandRestore.html#migrage-restore)。

### 3.5 判断恢复任务是否正常完成
恢复的任务信息也可以通过`getBackupStatus`查询。若要判断恢复任务是否完成，可以参考 [2.5.1节](#251-判断备份任务是否正常完成)。

## 4. 备份恢复的性能
本次性能测试使用的机器 CPU 为Intel(R) Xeon(R) Silver 4314 CPU @ 2.40GHz

使用的DolphinDB集群为 DolphinDB 普通集群，1个 controller，3个 data node，每个 data node 挂载1个普通SSD盘，读写速度约为500MB/s。备份文件所在的磁盘也是SSD盘，读写速度也为500MB/s。

cluster.cfg配置如下：
```
maxMemSize=256
maxConnections=512
workerNum=8
chunkCacheEngineMemSize=16
newValuePartitionPolicy=add
maxPubConnections=64
subExecutors=4
subPort=8893
lanCluster=0
enableChunkGranularityConfig=true
diskIOConcurrencyLevel=0
```
运行备份时，落库为50G大小的数据，观察备份文件所在的磁盘IO，写入速度为490MB/s左右，基本达到了磁盘的性能瓶颈。

运行恢复时，因为是写入多个磁盘，我们用数据量/时间来估算写入速度。备份文件大小为50G，恢复花费了2分20秒，速度约为365MB/s，低于备份速度。


## 5. FAQ
### 5.1 是否支持恢复到某个时间点？
不支持，DolphinDB的增量备份并不是添加新的binlog，而是直接覆盖原文件。所以，增量备份功能只是跳过了不需要备份的分区，从而加速了备份，而不支持恢复到某个时间点。在 DolphinDB 中，如果你需要恢复到到一周前的任意一天，那么你需要在一周前的每一天都备份一份数据，并且放在不同的目录中。

### 5.2 备份时所有分区的时间点是否一致？    
一致。

### 5.3 是否支持断点续备/恢复?
支持。具体见[1.1节](#11-备份单个数据库)。

### 5.4 是否支持增量备份/恢复？
支持。具体见[1.1节](#11-备份单个数据库)。

### 5.5 如何查看备份进度？
使用 `getBackupStatus` 函数。具体见[2.1节](#21-getbackupstatus)

### 5.6 如何检查备份是否完成？
见[2.5.1节](#251-判断备份任务是否正常完成)。

### 5.7 如何检查恢复是否完成？
见[3.5节](#35-判断恢复任务是否正常完成)




# 分级存储教程
- [分级存储教程](#分级存储教程)
  - [1.简介](#1简介)
  - [2.使用介绍](#2使用介绍)
    - [2.1 参数配置](#21-参数配置)
    - [2.2 设置数据迁移范围](#22-设置数据迁移范围)
    - [2.3 触发数据迁移](#23-触发数据迁移)
  - [3 机制介绍](#3-机制介绍)
    - [3.1 自动数据迁移触发机制](#31-自动数据迁移触发机制)
    - [3.2 数据迁移机制](#32-数据迁移机制)
    - [3.3 数据读取机制](#33-数据读取机制)
  - [4. 总结](#4-总结)

## 1. 简介

在数据库领域，分级存储是一种常见的需求，即将一部分较旧的数据转存至本地其他磁盘卷（通常是更低速的磁盘卷）或对象存储方案中。较旧的数据（冷数据）通常不会被用户频繁查询或计算，但是存储在本地会占用大量磁盘资源，因此将不常用的数据存储在对象存储中，或将其从高速磁盘（如 SSD）转存至较低速的磁盘（如 HDD），可以有效节约资源开销。本文将介绍 DolphinDB 的分级存储功能的基本原理和如何使用。

## 2. 使用介绍

### 2.1 参数配置

在使用分级存储前，需要先配置相应的参数：

冷数据磁盘卷配置项 `coldVolumes`

```
coldVolumes=file:/{your_local_path},s3://{your_bucket_name}/{s3_path_prefix}
```

我们使用 `coldVolumes` 配置项来指定存储冷数据的文件目录。该参数支持配置为本地路径（以 *file:/* 开头）或者 s3 路径（以 *s3://* 开头）。也可指定多个路径，路径间用逗号隔开。

例如：

```
coldVolumes=file://home/mypath/hdd/<ALIAS>,s3://bucket1/data/<ALIAS>
```

:exclamation:**注意**：

不同数据节点需要配置不同的 `coldVolumes` 路径，否则可能会造成不同 `datanode` 间数据的相互覆盖。这里通过 `<ALIAS>` 宏定义，让每个 `datanode` 将数据放到 */home/mypath/hdd/* 目录下按照节点别名命名的目录中。

如果您配置了 S3 路径，那么还需要配置 AWS S3 插件，以及 S3 的 `AccessKeyId`, `SecretAccessKey`, `Region`, `EndPoint` 等信息：

```
pluginDir=plugins //指定节点的插件目录，需要将AWS S3插件放到plugins目录下
preloadModules=plugins::awss3 //系统启动后自动加载AWS S3插件
s3AccessKeyId={your_access_key_id}
s3SecretAccessKey={your_access_screet_key}
s3Region={your_s3_region}
s3Endpoint={your_s3_Endpoint}
```

- 有关配置的详情，参考：[分级存储](https://docs.dolphindb.cn/zh/db_distr_comp/cfg/cfg_para_ref.html#configparamref__tieredstoragesection)。
- 有关AWS S3插件的用法，参考：[aws插件](https://docs.dolphindb.cn/zh/plugins/aws/aws.html) 。



### 2.2 设置数据迁移范围

在 DolphinDB 中，您可以使用 [setRetentionPolicy](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/s/setRetentionPolicy.html) 函数的参数 *hoursToColdVolume* 来配置数据的保留时间。

假设在上文中，我们已经配置了 `coldVolumes`：

```
coldVolumes=file://home/dolphindb/tiered_store/<ALIAS>
```

DolphinDB 通过数据的时间列来确定需要迁移的数据，所以需要对应的数据库存在时间分区的分区方案。首先，我们先创建一个时间列 `VALUE` 分区的数据库，并写入最近十五天的数据：

```
db = database("dfs://db1", VALUE, (date(now()) - 14)..date(now())) //创建一个按照时间列VALUE分区的数据库
data = table((date(now()) - 14)..date(now()) as cdate, 1..15 as val) //创建一个table，时间列为最近15天
tbl = db.createPartitionedTable(data, "table1", `cdate)
tbl.append!(data)
```

接着，我们使用 [setRetentionPolicy](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/s/setRetentionPolicy.html) 函数做如下配置：

超过五天（120h）的数据将会被迁移至冷数据层，超过三十天（720h）的数据将会删除。因为 `database` 只有一层 `VALUE` 分区，所以时间列分区维度为0。

```
setRetentionPolicy(db, 720, 0, 120)
```



### 2.3 触发数据迁移

设置之后，DolphinDB 会在后台每隔1小时检查并迁移范围内的数据。这里为了演示方便，我们使用 [moveHotDataToColdVolume](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/m/moveHotDataToColdVolume.html) 函数来手动触发迁移。

```
pnodeRun(moveHotDataToColdVolume) //在每个datanode上执行函数，手动触发迁移
```

之后，DolphinDB 会发起最近15天到最近7天的分区的数据迁移任务。DolphinDB 使用原有的 recovery 机制实现数据的迁移，可以通过 [getRecoveryTaskStatus](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getRecoveryTaskStatus.html?highlight=recovery) 函数来查看 recovery 任务的执行状态：

```
rpc(getControllerAlias(), getRecoveryTaskStatus) //可以看到创建了最近15天到最近7天的数据迁移任务
```

可能的结果样式（省略某些列）：

| **TaskId**                           | **TaskType**  | **ChunkPath**   | **Source** | **Dest** | **Status** |
| :----------------------------------- | :------------ | :-------------- | :--------- | :------- | :--------- |
| 2059a13f-00d7-1c9e-a644-7a23ca7bbdc2 | LoadRebalance | /db1/20230209/4 | NODE0      | NODE0    | Finish     |
| …                                    | …             | …               | …          | …        | …          |


:bulb:
1. 如果配置了多个 `coldVolumes`，会随机将分区迁往不同的 `coldVolumes`。
2. 如果 `coldVolumes` 是本地路径，会使用文件拷贝的方式进行迁移。
3. 如果 `coldVolumes` 是 S3 路径，会使用 AWS S3 插件进行多线程的上传，速度相对于本地路径可能较慢。
4. 在迁移时，分区会暂时不可用。

当 recovery 任务结束之后，已经被迁移的分区权限变为 `READ_ONLY`，我们可以使用 `select` 语句进行查询，但是不能使用 `update`, `delete`, `append!` 等语句进行更新、删除或写入。

```
select * from tbl where cdate = date(now()) - 10 //查询迁移后的数据
update tbl set val = 0 where cdate = date(now()) - 10 //更新迁移后的数据。会报错 “Writing to chunk {ChunkID} is not allowed.”
```

特殊地，我们使用 `dropTable`，`dropParititon`，`dropDatabase` 等 drop DDL 操作来进行数据的整体删除时，对象存储上对应的分区数据也会被删除。这里不再赘述。

您可以使用 `getClusterChunksStatus` 函数查看对应分区的权限：

```
rpc(getControllerAlias(), getClusterChunksStatus)
```

可能的结果样式（省略了某些列）：

| **chunkId**                          | **file**        | **permission**                 |
| :----------------------------------- | :-------------- | :----------------------------- |
| ef23ce84-f455-06b7-6842-c85e46acdaac | /db1/20230216/4 | READ_ONLY（已经被迁移的分区）  |
| 260ab856-f796-4a87-3d4b-993632fb09d9 | /db1/20230223/4 | READ_WRITE（没有被迁移的分区） |



## 3 机制介绍

### 3.1 自动数据迁移触发机制

使用 [setRetentionPolicy](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/s/setRetentionPolicy.html) 函数设置好后，DolphinDB 会使用后台工作线程，每隔1小时按照数据库的时间分区检查在 [当前时间 - *hoursToColdVolume* - 10天，当前时间 - *hoursToColdVolume*) 范围内是否存在需要被迁移的数据，如果存在，则触发数据迁移，生成对应的 recovery 任务。在触发时，工作线程可能不会一次性将所有的符合条件的分区全部迁移，而是以 DB 为单位，每隔一小时迁移一个DB下所有待迁移的数据，从而减少 recovery 的压力，提高可用性。

举例来说，假设有两个DB：`dfs://db1`，`dfs://db2`。它们都按照时间分区。*hoursToColdVolume* 设置120h，即保留5天内的数据：

- 在2023.02.20 17:00时，工作线程可能会将 db1 下所有2023.02.05~2023.02.15（但不包含02.15）的分区进行迁移。
- 在2023.02.20 18:00时，可能会将 db2 下的所有2023.02.05~2023.02.15（但不包含02.15）的分区进行迁移。
- 如果工作线程的检查覆盖完整的一天，会保证在2023.02.20这一天结束前将所有 db 的2023.02.05~2023.02.15（但不包含02.15）的分区进行迁移。



### 3.2 数据迁移机制

分级存储依托于 DolphinDB 的 recovery 机制，以分区为单位，将每个节点的分区副本迁移到低速磁盘或者 S3 对象存储中。数据迁移内部的大致流程：

1. 用户使用 [setRetentionPolicy](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/s/setRetentionPolicy.html) 函数设置 *hoursToColdVolume* 来配置数据的保留时间。
2. DolphinDB 后台线程根据时间分区检查需要被迁移的数据，创建 recovery 任务。
3. 执行 recovery 任务，上传或拷贝对应的数据文件到对应的 *S3/* 本地路径。
4. 修改分区元数据，更新分区路径，修改分区权限为 `READ_ONLY`。

### 3.3 数据读取机制

当使用 `select` 语句读取数据时，如果对应的分区文件位于 S3 上，我们会使用 S3 插件的相关 API 来代替本地文件 API 来进行数据读取、获取文件长度、获取目录下的所有文件等文件操作，其余读取流程与正常的引擎读取流程一致。

因为 S3 的网络请求相比于本地磁盘读取过于慢，且保存到 S3 上的文件不会被修改。基于此，DolphinDB 将文件长度等部分元数据以及读取的文件数据存入缓存。如果读取的数据已经被缓存，则不需要再通过 S3 文件 API 创建网络请求，而是从缓存中读取返回，从而节省了昂贵的网络开销。

## 4. 总结

DolphinDB 的分级存储功能，能够将冷数据定期迁移至低速磁盘或云端，同时支持 `select` 语句进行正常的读取、计算，能够满足金融及物联网用户节省高速存储资源、降低无谓资源开销的需求。

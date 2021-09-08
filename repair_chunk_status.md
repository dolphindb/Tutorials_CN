# DolphinDB分区状态不一致如何解决

## 1. 概述

在DolphinDB日常运维时，可能由于误操作或意外情况，造成控制节点与数据节点的分区状态不一致，最终导致数据无法加载和写入。针对这种异常，本教程讲述如何解决DolphinDB分区状态不一致的问题，以恢复数据库正常加载数据功能。

## 2. 基本知识

​	DolphinDB利用分布式文件系统实现数据库的存储和基本事务机制。数据库以分区为单位进行管理。分区的元数据存储在控制节点(Controller)，副本数据存储在各数据节点(Datanode,又称ChunkNode)，统一由分布式文件系统(Dolphin File System，简称DFS)进行管理。DolphinDB采用多副本机制，相同数据块的副本存储在不同的数据节点上。数据库中的数据包括两个部分：元数据和分区数据。元数据指的是数据库的分区信息，每个分区的版本链，大小，存储位置等。分区数据指的是具体要存储的实际数据，包含多个副本。每一个数据块简称为chunk。下面分别介绍Controller以及Datanode中chunk保存内容：

**Controller**

- 1.文件命名空间：例如/ff_custom15/YANGXS_YINZI8/202104M_202105M

  每一级目录都有属性:{'Normal', 'Partiton', 'Seq'}.

     Normal:类似于普通的文件系统目录.
     Partition:数据库的分区目录，Range，List，Value.
     Seq: 将一张表按照Tablet chunk为单位进行顺序分割的目录。

     File Chunk: 普通文件的chunk.例如/ff_custom3/table_data_3.tbl是一个FileChunk

     Tablet Chunk:一种特殊的chunk，可以想象为结构化数据表的一小片，是一个目录，也就是Sequential分区下的Part概念，该目录下存放实际的数据，这种类型的目录必须作为最后一级分区，该目录同样受chunk大小限制.例如/ff_custom15/YANGXS_YINZI8/202104M_202105M是一个Tablet Chunk.

- 2.File Chunk和文件名的映射关系，一个大文件chunk对应多个小chunk存储.

- 3.chunk的位置信息，一般是由DataNode汇报到Controller合成，包括该chunk位于的位置信息，管理的分区、tablet Chunk信息，各分区、tablet Chunk的版本号，负载等信息。

**datanode**

- 1.主要处理File Chunk和Tablet Chunk两种类型。
  File Chunk可以是按照chunk id命名的一个binary文件.
  Tablet Chunk可以是按照chunk id命名的一个目录，里面存放Tablet数据。
  ChunkNode定时向Controller汇报本地存放的File Chunk和Tablet Chunk信息，负载信息。

一个数据库可以包含上百万个分区，分区的多副本之间使用二阶段提交协议实现分区副本的强一致性。下面简要介绍TID、CID以及二阶段提交协议流程：

- 事务编号（TID, unsigned long long, 递增）
  事务提交编号（CID，unsigned long long, 递增）
  版本号（unsigned int，可以循环利用）
- 1、协调人（提交任务的节点）首先向Controller取得一个事务编号（TID），并在Controller的内存中做元数据修改，然后把任务发给每一个Chunk Node。每一个Chunk Node去完成具体任务，如果有错抛出异常给协调人。
- 2、a) 协调人收到异常或者请求超时，认为任务没有完成，决定回滚事务。向各个Chunk Node和Controller发出回滚请求。 b)协调人如果没有收到异常，也没有任何超时，协调人决定准备提交事务（提交的第一阶段）。协调人向Controller获取一个（Commit Identifier，CID）协调人带着TID和CID，向相关的Chunk Node和Controller发送提交请求。
- 3、a) 协调人收到异常或者请求超时，决定回滚事务。向各个Chunk Node和Controller发出回滚请求。 b) 协调人如果没有收到异常，也没有任何超时，协调人决定准备提交事务（提交的第二阶段）。协调人向Controller和chunk node发出complete事务请求。
- 4、在第二阶段（回滚或确认），不管chunk node和Controller发生什么，协调人不作任何处理，都交由集群的版本恢复机制来处理。

### 2.1 Controller和Datanode上版本状态说明

DolphinDB上版本状态说明分布在Controller和Datanode上，正常情况都处于完成状态。所有chunk的version以Controller的version为标准，如果一个chunk node保存的某个chunk的version不等于Controller上保存的该chunk的version，那么认为不一致，需要通过Recovery机制恢复到最新的version。事务版本状态说明如下:

- 查看Controller上所有chunk的版本：

  ```sql
  select * from getClusterChunksStatus()
  ```

- 返回表中重要的列说明

  - `chunkId`：chunk的唯一标识

  - `file`：分区路径。

  - `size`：file chunk占用磁盘空间，单位为byte。对于tablet chunk, 返回0，需要使用getTabletsMeta来查看它们实际占用的磁盘空间。

  - `version`：版本号

  - `VCLength`: 版本链长度

  - `VersionChain`: 版本链。例如1028:0:1 -> 1028:0:0 -> 标识该CHUNK经历了两个版本，1028:0:1分别表示CHUNK的Cid、size以及version

  - `state`： chunk状态。COMPLETE表示数据已导入；CONSTRUCTING 表示正在导入数据；RECOVERING 表示正在恢复数据。

  - `replicas`：副本的分布信息。

  - `replicaCount`：副本数

Controller上版本有3个状态：CONSTRUCTING,  RECOVERING,  COMPLETE（对应字段state）

- `CONSTRUCTING` ： chunk正在构建中，比如openchunk后正在写入，正在删除等，一般是事务中的状态。
- `RECOVERING` ： chunk处于恢复中，当Controller刚启动，chunk都处在这个状态，然后等待Datanode汇报版本，如果版本和Controller上的版本一致，则状态由RECOVERING 变为COMPLETE状态。 其次如果Datanode汇报上来的版本不一致，那么Controller上的chunk会一直处在这种状态，直到recovery过程完成，然后版本变为一致，状态变为COMPLETE。 除了Controller刚启动，在正常运行中，也可能出现这种状态，比如在读数据的时候，检查到数据校验错误，Datanode 会向Controller发起recovery请求，Controller开始执行这个recovery的过程中，chunk的状态也是RECOVERING。
- `COMPLETE` : chunk 处于完成状态，事务正常完成，重启后版本一致，都将处在这个状态，这个状态是最终正确的状态。

当Controller重启后，所有文件的最后一个chunk被置为Recovering状态，随着chunk信息汇报上来后，如果副本chunk version和master chunk version一致且有效副本个数到达阈值，那么Recovering=> Complete，否则Controller将不一致的chunk加入待恢复chunk队列。对于等待恢复的chunk，选择一个一致的chunk副本作为primary chunk，执行这个副本过程，如果一个chunk的所有副本都和Controller chunk version不一致，无法进行恢复。对于正在进行恢复的chunk来说，限制该chunk无法进行写。对于每个chunk的recovery过程都分配一个唯一的recovery id，由master生成，用于去重复。所以本篇文章第四节针对无法重启自动恢复chunk的问题提出解决方案。如下图附Controller的chunk状态图：

![](./images/repair_chunk_status/repair_chunk_status2.1-1.png)

查询Controller上版本可能有问题的chunk：

```sql
select * from getClusterChunksStatus()  where  state != 'COMPLETE'
select * from rpc(getControllerAlias(), getClusterChunksStatus) where  state != 'COMPLETE'
```

- 查看Datanode上所有chunk的版本

  ```sql
  select * from pnodeRun(getAllChunks)
  ```

- 返回表中重要的列说明

  - `site` : chunk所属datanode
  - `chunkId`：chunk的唯一标识。
  - `path`：chunk物理路径。
  - `dfsPath`：分区路径。
  - `type`：分区类型。0表示file chunk；1表示tablet chunk。
  - `flag`：删除标志。若flag=1，此chunk数据不能被查询到，但尚未从磁盘删除。
  - `size`：file chunk占用磁盘空间。
  - `version`：版本号
  - `state`：chunk状态
  - `versionList`：版本列表，cid : 6,pt=>6:500338; # 表示该分区chunk的cid为6，所属为pt表，其总行数为500338

Datanode上的状态有5个状态：FIN, BCOMM, COMM, WRE, IRE分别对应state字段0，1，2，3，4：

- `FIN` ：chunk处于终态，包括事务最终正确完成，或者rollback。
- `BCOMM` : before committe, 往一个chunk上正在执行事务，在commit之前的阶段。比如正在写数据或者删除数据。
- `COMM` ： after committe，事务已经commit的状态。
- `WRE `： waiting for recoving，等待恢复的状态，比如版本不一致或者数据损坏，向Controller发起recovery请求后，等待Controller发起recovery之前，则会处于这种状态。
- `IRE `： in recoving状态，在recoving状态中，接受到Controller的recoving请求，开始启动recovery，则处于这个状态，recoving完成后变为FIN状态。

chunk的最终状态为FIN，其他状态都是临时状态，Datanode启动后，一般处于FIN状态，如果有异常需要恢复，则可能处于WRE状态。

如下图附上ChunkNode状态图：

![](./images/repair_chunk_status/repair_chunk_status2.1-2.png)

查看Datanode上所有非正常的chunk的状态：

```sql
select * from getAllChunks() where state != 0 
```

### 2.2 Controller和Datanode版本一致性校验

Controller和Datanode 启动后，正常情况下，所有chunk都处于终态，Controller上状态为COMPLETE，Datanode上状态为FIN。并且每个chunk上所有副本版本一致，并且和Controller要完全一致。下面有以下3个场景将触发chunk的恢复机制。
（1）Controller或Datanode重启，
（2）Controller或Datanode的事务处于committed的状态，但已经timeout
（3）在客户端读写的过程中发现Controller和Datanode的版本不一致。

正常触发恢复机制后，在半个小时左右都将使得Controller或Datanode的Chunk状态分别变成COMPLETE以及FIN。如果Chunk一直处于Recovering状态，下面第三节介绍常见场景以及解决方案。

## 3.分区状态不一致场景

典型的版本不一致的场景如下：

- (a) Datanode 两个副本一致，但是和Controller不一致；
- (b) Datanode 两个副本不一致，其中一个和Controller一致；
- (c) Datanode 两个副本不一致，并且都和Controller不一致；
- (d) Datanode 两个副本一致，但是Controller的chunk丢失；

造成这些版本不一致的原因可能是多方面，一是程序的bug，二是人为删除数据文件，三是配置不当，（比如不同数据节点的meta配置到一个目录下），四是当不正常的关机、重启时，集群没准备好写入等原因。

## 4. 分区状态不一致修复方法与案例

由于版本不一致的现象多种多样，按照公司数据库recovery的设计，如果有版本不一致的情况，datanode上报后，Controller会启动recovery来修复。自动recovery只能修复上面的(b)场景，也就是两个datanode的replica中有一个和Controller的版本相同，这种场景下，recovery会修复不一致的版本，并且最终，Controller和datanode的版本会达到一致。针对其他的场景，还是修复不了，要利用一些特殊的手段来修复。下面的方法包括修改元数据，发起recovering，指定修复到某个版本，删除/复制 replica，从datanode恢复出Controller等。

注意：在确认数据本身正确，只是版本或者元数据不正确的话，利用下列函数来强制修改datanode元数据。

### 4.1 利用函数forceCorrectVersionByReplica修复版本错乱问题

如下场景：

查询Controller上版本可能有问题的chunk：

```sql
select * from rpc(getControllerAlias(), getClusterChunksStatus) where  state != 'COMPLETE'
```

![](./images/repair_chunk_status/repair_chunk_status4.1-1.png)

如图所示其中version字段对应Controller上的Chunk版本信息为270，而replicas对应DataNode上的Chunk版本信息，可以发现符合（a）场景，Controller上版本信息明显低于DataNode上信息。可以使用下面函数修复

`forceCorrectVersionByReplica`函数定义如下

forceCorrectVersionByReplica(chunkID,nodealias)

- `chunkID`: chunk的唯一标识。
- `nodealias`: 节点别名。

该函数功能是，强制该chunk 以nodealias上的版本和数据为准，Controller 和其他的datanode必须无条件与其同步。该函数背后的实现原理是，找到nodealias上chunk，Controller先向datanode获取到chunk的版本信息，并且将nodealias上该版本的状态转为FIN。然后Controller自己的版本号按照datanode反馈的更新，然后发起recovery，强制其他的replica同步nodealias行该chunk的数据和版本信息。

该函数可以解决版本不一致的绝大多数问题，但可能会导致数据部分丢失，所以在选择nodealias的时候，尽量选择版本高的nodealias。示例脚本如下：

```python
for(chunkID in chunkIDs){          
    nodes = exec  top 1 node from pnodeRun(getAllChunks) where chunkId=chunkID order by version desc
    rpc(getControllerAlias(), forceCorrectVersionByReplica{chunkID, nodes[0]})
}
```

查看该Chunk的状态，如图所示，版本一致，状态变成COMPLETE。

![](./images/repair_chunk_status/repair_chunk_status4.1-2.png)

### 4.2 利用函数updateTabletVersionOnDataNode和updateChunkVersionOnMaster直接编辑chunk的元数据版本信息

`updateTabletVersionOnDataNode`函数定义如下

updateTabletVersionOnDataNode(chunkID,version,cid)

- `chunkID`: chunk的唯一标识。
- `version`: 版本号
- `cid`：chunk提交事务的编号

该函数的功能不提供分布式功能，只针对某个chunkNode上某个Chunk，直接修改并持久化改Chunk的元数据，使得版本恢复一致。

`updateChunkVersionOnMaster`函数定义如下

updateChunkVersionOnMaster(chunkId, version)

- `chunkID`: chunk的唯一标识。
- `version`: 版本号

该函数的功能，直接修改并持久化改chunk的元数据，使得版本恢复一致。

注意：只能在Controller上使用。

如图所示

![](./images/repair_chunk_status/repair_chunk_status4.1-1.png)

Controller上版本低于ChunkNode上版本，使用下列语句修复

```
updateChunkVersionOnMaster("deb91fa2-f05a-3096-5941-b80feda42562",270)
```

注意；这两个函数并不修改除版本号外的其他信息。与forceCorrectVersionByReplica函数区别是,forceCorrectVersionByReplica是强制Controller版本和datanode版本一致，适合于Datanode上chunk版本高于master版本。如果Datanode上chunk版本低于master版本，尽量选择高版本信息，可以使用本小节两个函数，将chunk信息修改为指定版本.

### 4.3 利用函数restoreControllerMetaFromChunkNode恢复Controller上的元数据

如下场景：

```sql
select * from rpc(getControllerAlias(), getClusterChunksStatus)
```

执行上述语句时查询到控制节点的元数据为0.且加载dfs分布式表报如图错误，可以使用restoreControllerMetaFromChunkNode函数

![](./images/repair_chunk_status/repair_chunk_status4.3-1.png)

`restoreControllerMetaFromChunkNode`函数主要功能是恢复元数据，必须控制节点（controller）上执行；该函数于1.20.9开始支持，该函数执行时，元数据存储目录下必须为空，所以需要在 controller.cfg 中配置元数据存储位置，参数“dfsMetaDir=元数据存储路径”，元数据存储路径必须为空。控制节点的元数据文件如下：

![](./images/repair_chunk_status/repair_chunk_status4.3-2.png)

元数据恢复过程如下：

1.关闭 DolphinDB 集群；

2.备份 data 目录下的 DFSM*元数据文件（为了元数据安全，必须备份）；

3.删除 data 目录下的 DFSM*元数据文件；

4.在 controller.cfg 中配置元数据存储位置，参数“dfsMetaDir=元数据存储路径”，

该存储路径下必须只有元数据文件，不能同时存储其它文件；

5.重启集群，启动 controller、agent、datanode；

6.连接控制节点，需要等 1 分钟左右（数据节点加载 chunk 信息）再执行

restoreControllerMetaFromDatanode()函数，chunk 信息未加载完毕前执行上述

函数，会报错：Invalid UUID string;

7.如果反复执行 restoreControllerMetaFromChunkNode() 函数，会报错： File 

[DFSMasterMetaCheckpoint.23553] is not zero-length, please check.

此时说明，元数据文件已经恢复成功；

8.执行完函数后，重启整个集群，就可以正常查询原有数据了。

### 4.4 利用函数dropPartition强制删除元数据

如果确实要删除某个chunk，但如果chunk的版本不一致，或者处在recovering状态，那么正常的删除会删除失败。这个函数第四个参数，可以制定是否强制删除，不考虑版本一致性的问题。这种情况下，可以使用该函数，并且将第四个参数设置为true。

示例脚本如下：

```sql
dbName="/stocks_orderbook"
fileCond=dbName + "%"
t=exec substr(file,strlen(dbName)) from rpc(getControllerAlias(),getClusterChunksStatus) where file like fileCond, state != "COMPLETE"
dropPartition(database("dfs:/"+dbName),t,,true)
```

注意：假设执行查询 能正常返回数据，然后dropPartition语句，报错：Failed to find physical table from Table_Name when delete tablet chunk。

可以使用chunkCheckPoint()函数，再重启所有数据节点即可。

## 5. 总结

分布式数据库如何保持多副本数据一致性十分复杂，发生元数据异常的情况各有不同，下面有几个场景可能会导致上述情况：

- 网络异常：当协调者向参与者发送commit请求之后，发生了网络异常，这将导致只有部分参与者收到了commit请求。这部分参与者接到commit请求之后就会执行commit操作，但是其他未接到commit请求的参与者则无法执行事务提交，于是整个分布式系统便出现了数据不一致的问题。
- 服务器宕机：协调者在发出commit消息之后宕机，而唯一接收到这条消息的参与者同时也宕机了。那么即使协调者通过选举协议产生了新的协调者，这条事务的状态也是不确定的，没人知道事务是否被已经提交。

建议使用过程中避免sever在写入数据时，重启机器等操作。
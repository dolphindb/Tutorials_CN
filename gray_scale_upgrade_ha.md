高可用集群的灰度升级
==========================

- [1. 概述](#1-概述)
- [2. 版本兼容性](#2-版本兼容性)
- [3. 升级步骤](#3-升级步骤)
  - [3.1 升级准备](#31-升级准备)
  - [3.2 节点升级](#32-节点升级)
  - [3.3 验证](#33-验证)


## 1. 概述

用传统方式升级集群版本，通常需要先把全部节点关闭，然后一次性把整个集群全部节点的版本升级为新版本。升级时，业务必须中断。灰度升级是指可以按节点逐一进行版本升级的方式，在单个节点升级为新版本，并确保其稳定运行后，再升级集群内的另一个节点，以此类推，直至整个集群内的所有节点完成升级。

升级过程中，系统一直保持在线，不会造成业务中断。这就要求集群部署方式必须是高可用的，即控制节点采用高可用部署，数据副本数至少为2，客户端采用高可用写入。

本教程讲述如何进行高可用集群的灰度升级（Gray Scale Upgrade），亦称为局部升级。

## 2. 版本兼容性

灰度升级，意味着内存中的数据格式，包括传输协议、序列化协议等需要完全兼容。

因此，对于版本跨度较大的升级，建议联系 DolphinDB 的技术支持工程师进行风险评估后再进行升级。

## 3. 升级步骤
> 注意：
>
> 当 server 升级到某个版本后，使用的插件也应升级到与此对应的版本。

本例中，需要将版本为 2.00.7.4 的高可用集群升级到 2.00.8.12 版本

`controller.cfg`

```
mode=controller
localSite=10.10.11.2:8920:HActl44
dfsHAMode=Raft
dfsReplicationFactor=2
dfsReplicaReliabilityLevel=1
dataSync=1
workerNum=4
maxConnections=512
maxMemSize=8
lanCluster=0
dfsRecoveryWaitTime=30000
```

`cluster.nodes`

```sh
localSite,mode
10.10.11.1:8920:HActl43,controller
10.10.11.2:8920:HActl44,controller
10.10.11.3:8920:HActl45,controller
10.10.11.1:8921:agent43,agent
10.10.11.2:8921:agent44,agent
10.10.11.3:8921:agent45,agent
10.10.11.1:8922:node43,datanode
10.10.11.2:8922:node44,datanode
10.10.11.3:8922:node45,datanode
```

`pnodeRun(version)`

```sh
	node	value
0	node43	2.00.7.4 2022.12.08
1	node44	2.00.7.4 2022.12.08
2	node45	2.00.7.4 2022.12.08
```

DolphinDB 中现有数据库 `dfs://stock`，库中有分布式表 `stock`

```python
db = database("dfs://stock",VALUE,2023.01.01..2023.01.10,,'TSDB')
tmp = table(1:0,[`time,`name,`id],[TIMESTAMP,SYMBOL,INT])
pt = db.createPartitionedTable(tmp,`stock,`time,,`name,ALL)
```

执行升级过程中，Python API 始终以高可用的方式向 DFS 表中写入数据

```python
import dolphindb as ddb
import pandas as pd
import datetime
import time
import random
s = ddb.session()
sites = ["192.168.100.43:8922","192.168.100.44:8922","192.168.100.45:8922"]
s.connect(host="192.168.100.43",port=8922,userid="admin",password="123456", highAvailability=True, highAvailabilitySites=sites)
appender = ddb.tableAppender(dbPath="dfs://stock",tableName='stock',ddbSession=s,action="fitColumnType")
x = ['Apple','Microsoft','Meta','Google','Amazon']
i = 1
while i<=10000000:
    now = datetime.datetime.now()
    name = random.sample(x,1)
    data = pd.DataFrame({'time':now,'name':name,'id':i})
    appender.append(data)
    print(i)
    i = i+1
    time.sleep(1)
```

如果升级后验证 DFS 表 `stock` 中的 `time` 字段延续至当前，且 `id` 字段是连续正整数，说明升级过程中写入未被中断；否则，说明受到了停机影响。

### 3.1 升级准备

第一步，执行以下脚本检查分区状态是否正常，返回为空，即所有副本状态正常。只有在分区状态不处于 RECOVERING 状态下才可进行后续步骤。

```
select * from rpc(getControllerAlias(), getClusterChunksStatus) where state != "COMPLETE" 
```

第二步，执行以下脚本获取元数据文件的存储目录

```
pnodeRun(getConfig{`chunkMetaDir})
```

```sh
	node	value
0	node44	/home/zjchen/HA/server/clusterDemo/data/node44/storage
1	node45	/home/zjchen/HA/server/clusterDemo/data/node45/storage
2	node43	/home/zjchen/HA/server/clusterDemo/data/node43/storage
```

```sh
rpc(getControllerAlias(),getConfig{`dfsMetaDir})
```

```
string('/home/zjchen/HA/server/clusterDemo/data/HActl44/dfsMeta')
```

### 3.2 节点升级

第一步，关闭 10.10.11.1 服务器上的所有节点，包括 controller、agent、datanode。

```sh
cd /home/zjchen/HA/server/clusterDemo/
sh stopAllNodes.sh
```

第二步，备份元数据。

- 备份控制节点元数据

```sh
cd /home/zjchen/HA/server/clusterDemo/data/node43/storage/
cp -r CHUNK_METADATA/ CHUNK_METADATA_BAK/
```

- 备份数据节点元数据

```sh
cd /home/zjchen/HA/server/clusterDemo/data/HActl44/
cp -r dfsMeta/ dfsMeta_bak/
```

第三步，进行DolphinDB 版本升级。

```sh
cd /home/zjchen/HA/server/clusterDemo/
sh upgrade.sh
```

预期结果：

```sh
DolphinDB package uploaded successfully!  UpLoadSuccess
DolphinDB package unzipped successfully!  UnzipSuccess
DolphinDB upgraded successfully!  UpgradeSuccess
```

第四步，重启 controller、agent、datanode，并验证 DFS 表 `stock` 的 `time` 和 `id` 字段是否符合预期。

先后对 10.10.11.2 和 10.10.11.3 两台机器上的节点执行 3.1 和 3.2 中的操作。

**注意**：当一台机器的节点升级结束并重启后，要确保分区状态没有处于 RECOVERING 状态才可以继续进行下一台机器节点的升级。

### 3.3 验证

使用以下命令进行升级后的验证：

`pnodeRun(version)`

```sh
	node	value
0	node44	2.00.8.12 2023.01.10
1	node45	2.00.8.12 2023.01.10
2	node43	2.00.8.12 2023.01.10
```

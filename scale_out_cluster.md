# DolphinDB集群如何扩展节点和存储

## 1. 概述
当系统准备上线前，我们会评估和规划硬件平台的容量，并且尽可能的留出余量。可是现实往往是不能预料的，随着业务的扩张，系统的数据容量和计算能力都会变得不堪重负，我们就不得不面对一个问题：如何为现有系统增加数据容量和计算能力？

由于DolphinDB的节点是集计算和存储于一体的，所以要增加计算能力和数据容量对DolphinDB的集群来讲就是一件事 : 增加节点。当然，DolphinDB也支持对原有的节点单独增加存储。

## 2. 扩展机制

DolphinDB的集群是由控制节点(Controller)，代理节点(Agent)，数据节点(Data Node)三个角色组成:
- Controller负责管理集群元数据，提供Web集群管理工具;
- Agent部署在每一台物理机上，负责本机节点的启动和停止；
- Data Node是计算和数据节点。

DolphinDB扩展节点需要修改节点配置文件，通过集群Controller重启来载入新的节点配置，若新节点部署在一台新的物理机上，那么需要部署一个新的Agent服务来负责新物理机上的节点启停。当新的节点启动后，节点的计算能力会即时纳入集群的计算资源来统筹；新增的节点默认会将[Home Dir]/[Data Node Alias]/storage作为数据存储区域，
> 注意此处 [Home Dir] 本例中通过在启动命令中增加 -home data，意思就是[Home Dir]指向可执行文件同级目录下的/data/目录，所以举例node3的数据存储默认目录就是 /data/node3/storage。

当新节点启动后，该目录会被自动创建并初始化用于存储集群的分布式数据。

若仅对存储空间进行扩展，只需要修改节点配置文件，为指定节点volumes属性增加路径。

## 3 方法

扩展节点需要做的工作，首先要让Controller知道需要新增的机器IP和Data Node，这份工作主要是由配置文件来实现，DolphinDB提供以下几个配置文件分别来配置集群信息
- [Controller] controller.cfg: 负责定义控制节点的相关配置，比如IP端口，控制节点连接数上限等
- [Controller] cluster.cfg: 负责集群内每一个节点的个性化配置，比如node3的volumes属性等
- [Controller] cluster.nodes: 定义集群内部的节点和代理清单，控制节点会通过这个文件来获取集群的节点信息
- [Agent] agent.cfg: 定义代理节点相关属性，比如代理节点IP和端口，所属集群控制节点等信息，和代理节点程序一起部署在各台物理机上

然后在新增加的物理机上部署Agent来负责启停本机器的Data Node，而剩下的详细配置工作和节点的启停都可以在Web集群管理界面上方便的完成。

而扩展存储空间的工作，因为volumes属性支持用逗号分隔指定多个存储目录，所以在原有的volumes属性后面追加存储目录即可。
## 4. 扩展节点

### 4.1 环境说明

因为具体的操作是在一个已有的集群上做扩容操作，所以这里先了解一下原集群的配置情况。

原有服务器4台，操作系统均为ubuntu 16.04，部署了 DolphinDB 0.7 版本
```
172.18.0.10 : controller
172.18.0.11 : datanode1
172.18.0.12 : datanode2
172.18.0.13 : datanode3
```
具体的配置如下：

controller.cfg
```
localSite=172.18.0.10:8990:ctl8990
```
cluster.nodes
```
localSite,mode
172.18.0.11:8701:agent1,agent
172.18.0.12:8701:agent2,agent
172.18.0.13:8701:agent3,agent
172.18.0.11:8801:node1,datanode
172.18.0.12:8802:node2,datanode
172.18.0.13:8803:node3,datanode
```
启动Controller脚本
```
nohup ./dolphindb -console 0 -mode controller -script dolphindb.dos -config config/controller.cfg -logFile log/controller.log -nodesFile config/cluster.nodes &
```
启动Agent脚本
```
./dolphindb -mode agent -home data -script dolphindb.dos -config config/agent.cfg -logFile log/agent.log
```


为了在扩展工作完成之后可以验证效果，我们在集群内创建一个分布式数据库，并写入初始数据
```
data = table(1..1000 as id,rand(`A`B`C,1000) as name)
//分区时预留了1000的余量，预备后续写入测试用
db = database("dfs://scaleout_test_db",RANGE,cutPoints(1..2000,10))
tb = db.createPartitionedTable(data,"scaleoutTB",`id)
tb.append!(data)
```
执行完后通过集群web界面 dfs explorer观察生成的数据分布情况

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/scaleout/scale_dfs_exp1.PNG?raw=true)

在后续完成节点和存储的扩展之后，我们会用同样的方式追加数据，来验证新节点和存储是否已经启用。


> 需要了解集群初始化配置可以参考 [多物理机上部署集群教程](https://github.com/dolphindb/Tutorials_CN/blob/master/multi_machine_cluster_deploy.md)

### 4.2 扩展目标

本次扩容目标是为了增加计算和存储能力，增加了一台新的服务器，将之加入原有的集群作为一个新的节点。

新增的物理机IP
```
172.18.0.14
```
新增的节点信息
```
172.18.0.14:8804:datanode4
```

### 4.3 扩展步骤

#### 4.3.1 在新机器上部署和配置Agent

拷贝原机器上的Agent部署包到新机器，并修改agent.cfg
```
#指定Agent本身的ip和端口
localSite=172.18.0.14:8701:agent4
#告诉Agent本集群的controller位置
controllerSite=172.18.0.10:8990:ctl8990
mode=agent
```

#### 4.3.2 配置controller

修改节点清单配置cluster.nodes,配置新增加的Data Node和Agent

```
localSite,mode
172.18.0.14:8704:agent4,agent
172.18.0.14:8804:node4,datanode
```
#### 4.3.3 重启集群

- 访问集群web管理界面，关闭所有的节点。
```
http://172.18.0.10:8990
```
- 关闭Controller，在172.18.0.10机器上执行
```
pkill dolphindb
```
- 等待半分钟之后(等待端口释放，可能根据操作系统这个时间有不同)，重新再启动Controller

- 回到web管理界面，可以看到已经新增了一个agent4并且是已启动状态，在web界面上启动所有节点

 ![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/scaleout/scale_controller_start.PNG?raw=true)

到此我们已经完成了新节点的增加。

### 4.4 验证

下面我们通过向集群写入一些数据来验证node4是否已经在集群中启用。
```
tb = database("dfs://scaleout_test_db").loadTable("scaleoutTB")
tb.append!(table(1001..1500 as id,rand(`A`B`C,500) as name))
```
观察dfs explorer，可以看到数据已经分布到新的 node4 节点上。

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/scaleout/scale_dfs_exp2.PNG?raw=true)

## 5. 扩展存储

由于node3所在服务器本身的磁盘空间不足，现扩展了一块磁盘，路径为/dev/disk2，将这块磁盘纳入node3的存储。

### 5.1 步骤

DolphinDB的节点存储可以通过配置文件中的volumes属性来配置，上述案例中没有配置，那么默认的存储路径[HomeDir]/[Data Node Alias]/Storage, 在本例中即 data/node3/storage 目录下

> 若从默认路径增加磁盘，那么在设置volumes属性时，必须要将原默认路径显式设置，否则会导致默认路径下元数据丢失

默认情况的volumes属性内容如下，如果没有这一行，需要手工加上

cluster.cfg
```
node3.volumes=data/node3/storage
```
新的磁盘路径 /dev/disk2/node3要增加到node3节点,只要在上述配置后面用逗号分隔新增路径即可

cluster.cfg
```
node3.volumes=data/node3/storage,/dev/disk2/node3
```

修改配置文件后，在controller上执行loadClusterNodesConfigs()使得Controller重新载入节点配置，如果上述步骤在集群管理web界面上完成，这个重载过程会自动完成，无需手工执行。
配置完成后无需重启controller，只要在web界面上重启node3节点即可使新配置生效。
> 如果希望node3暂不重启，但是新的存储马上生效，可以在node3上执行addVolumes("/dev/disk2/node3")函数动态添加volumes，此函数的效果并不会持久化，重启后会被新配置覆盖。

### 5.2 验证

配置完成后，通过下面的语句向集群写入新数据，查看数据是否被写入新的磁盘
```
tb = database("dfs://scaleout_test_db").loadTable("scaleoutTB")
tb.append!(table(1501..2000 as id,rand(`A`B`C,500) as name))
```
到磁盘下观察数据已被写入

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/scaleout/3.PNG?raw=true)

## 6 常见问题

- 在验证节点的数据写入分布情况时 , 从dfs explorer里经常会发现site信息有时候会发生变化，比如原来保存在node3的数据迁移到其他节点了?

这个问题涉及到DolphinDB的Recovery 机制: 
DolphinDB的集群支持数据自动Recovery机制，当侦测到集群内部分节点长时间没有心跳时(判定宕机)，将会从其他副本中自动恢复数据并且保持整个集群的副本数稳定, 这也是当某个节点长时间未启动，系统后台会发生数据迁移的原因。需要注意的是，这个数据稳定的前提是宕掉的节点数少于系统设置的数据副本数。这个机制涉及到的配置项及默认值如下

controller.cfg

```
//集群内每个数据副本数，默认2
dfsReplicationFactor=2
//副本安全策略，0 多个副本允许存在一个节点 1 多个副本必须分存到不同节点,默认0
dfsReplicaReliabilityLevel=1
//节点心跳停止多久开启Recovery,默认不启用，单位ms
dfsRecoveryWaitTime=30000
```
这3个参数对于系统的数据稳定性非常重要

dfsRecoveryWaitTime控制recovery的启动，默认不设置即关闭recovery功能。这个等待时间的设置主要是为了避免一些计划内的停机维护导致不必要的recovery，需要用户根据运维的实际情况来设置。

从稳定性上来讲，副本数越多数据越不容易因意外丢失，但是副本数过多也会导致系统保存数据时性能低下，所以dfsReplicationFactor的值不建议低于2，但是具体设置多高需要用户根据整体集群的节点数、数据稳定性需求、系统写入性能需求来综合考虑。

dfsReplicaReliabilityLevel这个设置在生产环境下建议设置为1，0只建议作为学习或者测试环境下使用。


# 如何水平扩展DolphinDB集群

## 1. 概述

本教程讲述如何为一个DolphinDB集群增加节点，以增强其数据容量及计算能力。

## 2. 基本知识

DolphinDB的集群是由控制节点(controller)，代理节点(agent)及数据节点(data node)三类节点组成:
- controller负责管理集群元数据，提供Web集群管理工具。controller上存有三个核心的配置文件：
    - controller.cfg : 负责定义控制节点的相关配置，比如IP端口，控制节点连接数上限等。
    - cluster.nodes : 定义集群内部的节点清单，控制节点会通过这个文件来获取集群的节点信息。
    - cluster.cfg : 负责集群内每一个节点的个性化配置，比如node3的volumes属性等。
- agent部署在每一台物理机上，负责本机节点的启动和停止。Agent上的配置文件为
    - agent.cfg: 定义代理节点相关属性，比如代理节点IP和端口，所属集群控制节点等信息，和代理节点部署包一起部署在各台物理机上。
- data node是计算和数据节点，负责分发处理计算任务和存储数据。

扩展数据节点的主要步骤如下：
- 在新服务器上部署agent，并且配置好agent.cfg
- 向controller注册新的data node信息和agent信息
- 重启集群内controller和所有data Node

若仅对某data node存储空间进行扩展，例如增加硬盘，只需要修改节点配置文件，为指定节点volumes属性增加路径。

## 3. 扩展数据节点

本次扩容目标是为原有集群增加一个新的数据节点，新的数据节点部署在一台独立物理服务器上。

需要新增的物理机IP：
```
172.18.0.14
```
新增的节点信息：
```
172.18.0.14:8804:datanode4
```
原集群的配置情况为：服务器4台，操作系统均为 ubuntu 16.04，部署了 DolphinDB 0.7 版本。

```
172.18.0.10 : controller
172.18.0.11 : datanode1
172.18.0.12 : datanode2
172.18.0.13 : datanode3
```

具体的配置文件如下：

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
启动controller脚本
```
nohup ./dolphindb -console 0 -mode controller -script dolphindb.dos -config config/controller.cfg -logFile log/controller.log -nodesFile config/cluster.nodes &
```
启动agent脚本
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
执行完后通过集群web界面dfs explorer观察生成的数据分布情况

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/scaleout/scale_dfs_exp1.PNG?raw=true)

在后续完成节点和存储的扩展之后，我们会用同样的方式追加数据，来验证新节点和存储是否已经启用。


> *需要了解集群初始化配置可以参考 [多物理机上部署集群教程](https://github.com/dolphindb/Tutorials_CN/blob/master/multi_machine_cluster_deploy.md)*

### 3.1 配置agent

原服务器上的agent部署在/home/<DolphinDBRoot>目录下，将该目录下文件拷贝到新机器的/home/<DolphinDBRoot>目录，并修改/home/<DolphinDBRoot>/config/agent.cfg。

```
#指定Agent本身的ip和端口
localSite=172.18.0.14:8701:agent4
#指定本集群的controller位置
controllerSite=172.18.0.10:8990:ctl8990
mode=agent
```

### 3.2 配置controller

修改节点清单配置cluster.nodes，配置新增加的data node和agent。

```
localSite,mode
172.18.0.11:8701:agent1,agent
172.18.0.12:8701:agent2,agent
172.18.0.13:8701:agent3,agent
172.18.0.11:8801:node1,datanode
172.18.0.12:8802:node2,datanode
172.18.0.13:8803:node3,datanode
#新增Agent和Data Node
172.18.0.14:8704:agent4,agent
172.18.0.14:8804:node4,datanode
```

#### 3.3 重启集群

集群扩展数据节点必须重启整个集群，包括集群controller和所有的data node。

- 访问集群web管理界面 ```http://172.18.0.10:8990``` ，关闭所有的数据节点。

 ![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/scaleout/controller_stopAll.PNG?raw=true)

- 在172.18.0.10服务器上执行 ```pkill dolphindb``` 关闭controller。
- 等待半分钟之后(等待端口释放，可能根据操作系统这个时间有不同)，重新再启动controller。

- 回到web管理界面，可以看到已经新增了一个agent4并且是已启动状态，在web界面上启动所有数据节点

 ![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/scaleout/Controller_StartAll.PNG?raw=true)

到此我们已经完成了新节点的增加。

### 3.4 验证

下面我们通过向集群写入一些数据来验证node4是否已经在集群中启用。
```
tb = database("dfs://scaleout_test_db").loadTable("scaleoutTB")
tb.append!(table(1001..1500 as id,rand(`A`B`C,500) as name))
```
观察 dfs explorer，可以看到数据已经分布到新的 node4 节点上。

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/scaleout/scale_dfs_exp2.PNG?raw=true)

### 3.5. 扩展数据节点后的数据分布机制

在流行的MPP架构的集群中，添加节点后必须要对一部分数据resharding，因为hash值变了，而通常对海量数据做resharding需要很长时间。
而DolphinDB的数据存储基于底层分布式文件系统，通过元数据进行数据副本的管理，所以扩展了节点之后，原有的数据不需要有resharding这个过程，而新增的数据会按照分布策略保存到新的数据节点去。
当然通过resharding可以让数据分布更加均匀，DolphinDB正在开发这样的工具。

## 4. 扩展存储

由于node3所在服务器本身的磁盘空间不足，现扩展了一块磁盘，路径为/dev/disk2，将这块磁盘纳入node3的存储。

### 4.1 步骤

DolphinDB的节点存储可以通过配置文件中的volumes属性来配置，上述案例中没有配置，那么默认的存储路径<HomeDir>/<Data Node Alias>/Storage, 在本例中即 /home/server/data/node3/storage 目录下

> 若从默认路径增加磁盘，那么在设置volumes属性时，必须要将原默认路径显式设置，否则会导致默认路径下元数据丢失

默认情况的volumes属性内容如下，如果没有这一行，需要手工加上

cluster.cfg
```
node3.volumes=/home/server/data/node3/storage 
```
新的磁盘路径 /dev/disk2/node3要增加到node3节点,只要在上述配置后面用逗号分隔新增路径即可

cluster.cfg
```
node3.volumes=/home/server/data/node3/storage,/dev/disk2/node3
```

修改配置文件后，在controller上执行loadClusterNodesConfigs()使得controller重新载入节点配置，如果上述步骤在集群管理web界面上完成，这个重载过程会自动完成，无需手工执行。
配置完成后无需重启controller，只要在web界面上重启node3节点即可使新配置生效。
> 如果希望node3暂不重启，但是新的存储马上生效，可以在node3上执行addVolumes("/dev/disk2/node3")函数动态添加volumes，此函数的效果并不会持久化，重启后会被新配置覆盖。

### 4.2 验证

配置完成后，通过下面的语句向集群写入新数据，查看数据是否被写入新的磁盘
```
tb = database("dfs://scaleout_test_db").loadTable("scaleoutTB")
tb.append!(table(1501..2000 as id,rand(`A`B`C,500) as name))
```
到磁盘下观察数据已被写入

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/scaleout/3.PNG?raw=true)




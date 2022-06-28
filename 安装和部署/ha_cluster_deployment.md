# DolphinDB高可用集群部署教程

- [DolphinDB高可用集群部署教程](#dolphindb高可用集群部署教程)
	- [1.概述](#1概述)
	- [2.数据高可用](#2数据高可用)
	- [3.元数据高可用](#3元数据高可用)
	- [4.客户端高可用](#4客户端高可用)
	- [5.动态增加数据节点](#5动态增加数据节点)
	- [6.总结](#6总结)


## 1.概述
DolphinDB提供数据、元数据以及客户端的高可用方案，使得数据库节点发生故障时，数据库依然可以正常运作，保证业务不会中断。

DolphinDB采用多副本机制，相同数据块的多个副本存储在不同的数据节点（data node）上。即使集群中某个或多个数据节点宕机，只要集群中还有至少1个副本可用，那么数据库就可以提供服务。多副本的数据一致性通过二阶段提交协议来实现。

元数据存储在控制节点（conroller）上。为了保证元数据的高可用，DolphinDB采用Raft协议，通过构建多个控制节点来组成一个Raft组，只要宕机的控制节点少于半数，集群仍然可提供服务。由于配置文件cluster.cfg和cluster.node由Raft组统一管理，建议通过web接口修改配置项，web端会自动同步到集群中的所有配置文件。

DolphinDB API提供了自动重连和切换机制，如果当前连接的数据节点宕机，API会尝试重连，若重连失败就会自动切换连接到其他数据节点执行任务。切换数据节点对用户是透明的，用户不会感知到当前连接的节点已经切换。

如果要使用高可用功能，请先部署DolphinDB集群。高可用功能仅在集群中支持，在单实例中不支持。集群部署请参考[多服务器集群部署教程](../安装和部署/multi_machine_cluster_deployment.md)。

![images](../images/ha_cluster/arc.png?raw=true)

<div align='center'>DolphinDB 高可用架构图 </div>

## 2.数据高可用

为了保证数据的安全和高可用，DolphinDB支持在不同的服务器上存储多个数据副本，并且采用二阶段提交协议实现数据副本之间以及数据和元数据之间的强一致性。即使一台机器上的数据损坏，也可以通过访问其他机器上的副本数据来保证数据服务不中断。DolphinDB之所以采用二阶段提交协议实现副本之间的一致性，基于三个因素的考量：（1）DolphinDB集群是为海量数据设计的，单个集群可以支持千万级以上分区数，使用Raft和Paxos等算法创建千万级的协议组，成本太高；（2）使用Raft和Paxos等算法，查询数据时只有一个副本可用，对于OLAP应用场景来说过于浪费资源；（3）写入的数据如果跨分区，即使采用了Raft和Paxos等算法，仍然需要二阶段提交协议保证事务的ACID。

副本的个数可由在controller.cfg中的dfsReplicationFactor参数来设定。例如，把副本数设置为2：

```
dfsReplicationFactor=2
```
默认情况下，DolphinDB允许相同数据块的副本分布在同一台机器上。为了保证数据高可用，需要把相同数据块的副本分布在不同的机器上。可在controller.cfg添加以下配置项：

```
dfsReplicaReliabilityLevel=1
```

下面通过一个例子直观地解释DolphinDB的数据高可用。首先，在集群的数据节点上执行以下脚本以创建数据库：

```
n=1000000
date=rand(2018.08.01..2018.08.03,n)
sym=rand(`AAPL`MS`C`YHOO,n)
qty=rand(1..1000,n)
price=rand(100.0,n)
t=table(date,sym,qty,price)
if(existsDatabase("dfs://db1")){
	dropDatabase("dfs://db1")
}
db=database("dfs://db1",VALUE,2018.08.01..2018.08.03)
trades=db.createPartitionedTable(t,`trades,`date).append!(t)
```

分布式表trades被分成3个分区，每个日期表示一个分区。DolphinDB的Web集群管理界面提供了DFS Explorer，可以方便地查看数据分布情况。trades表各个分区的分布情况如下图所示：

![images](../images/ha_cluster/chunk_location.jpg?raw=true)

以20180801这个分区为例，Sites列显示，date=2018.08.01的数据分布在18104datanode和18103datanode上。即使18104datanode宕机，只要18103datanode正常，用户仍然对date=2018.08.01的数据进行读写操作。

## 3.元数据高可用
数据存储时会产生元数据，例如每个数据块存储在哪些数据节点上的哪个位置等信息。如果元数据不能使用，即使数据块完整，系统也无法正常访问数据。

元数据存放在控制节点。我们可以在一个集群中部署多个控制节点，通过元数据冗余来保证元数据服务不中断。一个集群中的所有控制节点组成一个Raft组，Raft组中只有一个Leader，其他都是Follower，Leader和Follower上的元数据保持强一致性。数据节点只能和Leader进行交互。如果当前Leader不可用，系统会立即选举出新的Leader来提供元数据服务。Raft组能够容忍小于半数的控制节点宕机，例如包含三个控制节点的集群，可以容忍一个控制节点出现故障；包含五个控制节点的集群，可以容忍两个控制节点出现故障。要设置元数据高可用，控制节点的数量至少为3个，同时需要设置数据高可用，即副本数必须大于1。

通过以下例子来介绍如何要为一个已有的集群启动元数据高可用。假设已有集群的控制节点位于P1机器上，现在要增加两个控制节点，分别部署在P2、P3机器上。它们的内网地址如下：

```
P1: 10.1.1.1
P2: 10.1.1.3
P3: 10.1.1.5
```

(1) 修改已有控制节点的配置文件

在P1的controller.cfg文件添加下列参数：dfsReplicationFactor=2, dfsReplicaReliabilityLevel=1, dfsHAMode=Raft。修改后的controller.cfg如下：

```
localSite=10.1.1.1:8900:controller1
dfsReplicationFactor=2
dfsReplicaReliabilityLevel=1
dfsHAMode=Raft
```

(2) 部署两个新的控制节点

分别在P2、P3下载DolphinDB服务器程序包，并解压，例如解压到/DolphinDB目录。

在/DolphinDB/server目录下创建config目录。在config目录下创建controller.cfg文件，填写以下内容：

P2

```
localSite=10.1.1.3:8900:controller2
dfsReplicationFactor=2
dfsReplicaReliabilityLevel=1
dfsHAMode=Raft
```

P3

```
localSite=10.1.1.5:8900:controller3
dfsReplicationFactor=2
dfsReplicaReliabilityLevel=1
dfsHAMode=Raft
```

(3) 修改已有代理节点的配置文件

在已有的agent.cfg文件中添加sites参数，它表示本机器代理节点和所有控制节点的局域网信息，代理节点信息必须在所有控制节点信息之前。例如，P1的agent.cfg修改后的内容如下：

```
localSite=10.1.1.1:8901:agent1
controllerSite=10.1.1.1:8900:controller1
sites=10.1.1.1:8901:agent1:agent,10.1.1.1:8900:controller1:controller,10.1.1.3:8900:controller2:controller,10.1.1.5:8900:controller3:controller
```

如果有多个代理节点，每个代理节点的配置文件都需要修改。

(4) 修改已有控制节点的集群成员配置文件

在P1的cluster.nodes上增加控制节点的局域网信息。例如，P1的cluster.nodes修改后的内容如下：

```
localSite,mode
10.1.1.1:8900:controller1,controller
10.1.1.2:8900:controller2,controller
10.1.1.3:8900:controller3,controller
10.1.1.1:8901:agent1,agent
10.1.1.1:8911:datanode1,datanode
10.1.1.2:8912:datanode2,datanode
```

(5) 为新的控制节点添加集群成员配置文件和节点配置文件

控制节点的启动需要cluster.nodes和cluster.cfg。把P1上的cluster.nodes和cluster.cfg复制到P2和P3的config目录。

(6) 启动高可用集群

- 启动控制节点

分别在每个控制节点所在机器上执行以下命令：

```bash
nohup ./dolphindb -console 0 -mode controller -home data -config config/controller.cfg -clusterConfig config/cluster.cfg -logFile log/controller.log -nodesFile config/cluster.nodes &
```

- 启动代理节点

在部署了代理节点的机器上执行以下命令：

```bash
nohup ./dolphindb -console 0 -mode agent -home data -config config/agent.cfg -logFile log/agent.log &
```
> 启动、关闭数据节点以及修改节点配置只能在Leader的集群管理界面操作。

- 如何判断哪个控制节点为Leader

在浏览器地址栏中输入任意控制节点的IP地址和端口号打开集群管理界面，例如10.1.1.1:8900，点击Node列的控制节点别名controller1进入DolphinDB Notebook。

![images](../images/ha_cluster/ha_web.jpg?raw=true)

执行`getActiveMaster()`函数，该函数返回Leader的别名。

![images](../images/ha_cluster/ha_notebook.jpg?raw=true)

在浏览器地址栏中输入Leader的IP地址和端口号打开Leader的集群管理界面。

## 4.客户端高可用

使用API与DolphinDB server的数据节点进行交互时，如果连接的数据节点宕机，API会尝试重连，若重连失败会自动切换到其他可用的数据节点。这对用户是透明的。目前Java、C#、C++和Python API支持高可用.

API的connect方法如下：

```
connect(host,port,username,password,startup,highAvailability)
```

使用connect方法连接数据节点时，只需要指定highAvailability参数为true。

以下例子设置Java API高可用：

```java
import com.xxdb;
DBConnection conn = new DBConnection();
String[] sites = {"192.168.1.189:22207","192.168.1.224:22207","192.168.1.228:22207","192.168.1.189:22208","192.168.1.224:22208","192.168.1.228:22208"};
boolean success = conn.connect("192.168.1.228", 22207,"admin","123456","",true, sites);
```

如果数据节点192.168.1.228:22207宕机，API会自动连接到其他可用的数据节点。

## 5.动态增加数据节点

用户可以使用`addNode`命令在线增加数据节点，无需重启集群。

下例中说明如何在新的服务器P4（内网IP为10.1.1.7）上增加新的数据节点datanode3，端口号为8911。

在新的物理服务器上增加数据节点，需要先部署一个代理节点，用于启动该服务器上的数据节点。P4的代理节点的端口为8901，别名为agent2。

在P4上下载DolphinDB程序包，解压到指定目录，例如/DolphinDB。

进入到/DolphinDB/server目录，创建config目录。

在config目录下创建agent.cfg文件，填写如下内容：

```
localSite=10.1.1.7:8901:agent2
controllerSite=10.1.1.1:8900:controller1
sites=10.1.1.7:8901:agent2:agent,10.1.1.1:8900:controller1:controller,10.1.1.3:8900:controller2:controller,10.1.1.5:8900:controller3:controller
```

在config目录下创建cluster.nodes文件，填写如下内容：

```
localSite,mode
10.1.1.1:8900:controller1,controller
10.1.1.2:8900:controller2,controller
10.1.1.3:8900:controller3,controller
10.1.1.1:8901:agent1,agent
10.1.1.7:8901:agent2,agent
10.1.1.1:8911:datanode1,datanode
10.1.1.2:8912:datanode2,datanode
```

把P1, P2和P3上的cluster.nodes修改为与P4的cluster.nodes相同。

执行以下Linux命令启动P4上的代理节点：

```bash
nohup ./dolphindb -console 0 -mode agent -home data -config config/agent.cfg -logFile log/agent.log &
```

在任意一个数据节点上执行以下命令：

```
addNode("10.1.1.7",8911,"datanode3")
```

执行上面的脚本后，刷新Web集群管理界面，可以发现新增加的数据节点已经存在，但它处于关闭状态，需要手动启动新增的数据节点。

## 6.总结

通过保证数据、元数据服务以及API连接不中断，DolphinDB database 可以满足物联网、金融等领域24小时不中断提供服务的需求。

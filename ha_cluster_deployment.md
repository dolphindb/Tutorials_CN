# 高可用集群部署

高可用仅在集群中支持，在单实例中不支持。集群部署请参考[多服务器集群部署教程](https://github.com/dolphindb/Tutorials_CN/blob/master/multi_machine_cluster_deploy.md)。

## 1. 数据高可用

为了保证数据的安全性和提高数据的可用性，DolphinDB提供了数据冗余备份，并支持在不同的服务器上存储数据副本。这样，即使一台机器上的数据损坏，也可以通过访问其他机器上的副本数据来保证数据不丢失。DolphinDB集群中，数据节点是存储中心。我们可以通过在多台机器上部署多个数据节点，并且设置多个副本数来保证数据高可用。

在controller.cfg中设置dfsReplicationFactor参数来设置多副本。例如，把副本数设置为2。

```
dfsReplicationFactor=2
```

默认情况下，DolphinDB是允许相同数据片段的副本分布在用一台机器上的。为了保证数据高可用，要把相同数据片段的副本分布在不同的机器上。在controller.cfg加上以下配置项：

```
dfsReplicaReliabilityLevel=1
```

## 2. 元数据高可用
数据存储时会产生很多元数据，比如数据片段存储在哪些数据节点上的哪个位置。如果元数据损坏，即使磁盘的数据完整，那么系统也无法正常访问数据。要设置元数据高可用，必须先设置数据高可用，即副本数必须大于1。如果数据只有一个副本，数据损坏，这时候系统不可用的原因在于数据本身，而不是元数据。

元数据是由控制节点统一管理。我们可以在一个集群中部署多个控制节点，通过元数据冗余来保证元数据服务不中断。一个集群中的所有控制节点组成一个Raft集群，Raft集群中只有一个Leader，其他都是Follower，Leader和Follower上的元数据保持强一致性。如果当前Leader不可用，系统会立即选举出新的Leader来提供元数据服务。Raft集群能够容忍小于半数的控制节点宕机，例如包含三个控制节点的集群，可以容忍一个控制节点出现故障；包含五个控制节点的集群，可以容忍两个控制节点出现故障。数据节点只能和Leader进行交互。

假设要为一个已有的集群启动元数据高可用，已有集群的控制节点位于P1机器上，现在要增加两个控制节点，分别部署在P2、P3机器上。

它们的内网地址如下：

```
P1: 10.1.1.1
P2: 10.1.1.3
P3: 10.1.1.5
```

(1)修改已有控制节点的配置文件

在P1的controller.cfg文件添加dfsReplicationFactor=2, dfsReplicaReliabilityLevel=1, dfsHAMode=Raft参数。修改后的controller.cfg如下：

```
localSite=10.1.1.1:8900:controller1
dfsReplicationFactor=2
dfsReplicaReliabilityLevel=1
dfsHAMode=Raft
```

(2)部署两个新的控制节点

分别在P2、P3上下载DolphinDB服务器程序包，并解压，例如解压到/DolphinDB目录。

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

(2)修改已有代理节点的配置文件

在已有的agent.cfg文件中添加sites参数，它表示本机器代理节点和所有控制节点的局域网信息。例如，P1的agent.cfg修改后的内容如下：

```
localSite=10.1.1.1:8901:agent1
controllerSite=10.1.1.1:8900:controller1
sites=10.1.1.1:8901:agent1:agent,10.1.1.1:8900:controller1:controller,10.1.1.3:8900:controller2:controller,10.1.1.5:8900:controller3:controller
```

如果有多个代理节点，每个代理节点的配置文件都需要修改。sites的第一个值要与本机器的代理节点的局域网信息对应。

(3)修改集群成员配置文件

在P1的cluster.nodes上增加控制节点的局域网信息。例如，P1的cluster.nodes修改后的内容如下：

```
localSite,mode
10.1.1.1:8900:controller1,controller
10.1.1.2:8900:controller2,controller
10.1.1.3:8900:controller3,controller
10.1.1.1:8901:agent1,agent
10.1.1.1:8911:datanode1,datanode
10.1.1.1:8912:datanode2,datanode
```

(4)为新的控制节点添加集群成员配置文件和节点配置文件

控制节点的启动需要cluster.nodes和cluster.cfg。把P1上的cluste.nodes和cluster.cfg复制到P2和P3的config目录。

(5)启动高可用集群

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

- 如何判断哪个控制节点为Leader

在浏览器地址栏中输入任意控制节点的IP地址和端口号打开集群管理界面，例如10.1.1.1:8900，点击Node列的控制节点别名进入DolphinDB Notebook。

![images]()

执行`getActiveMaster()`函数，该函数返回Leader的别名。



在浏览器地址栏中输入Leader的IP地址和端口号打开Leader的集群管理界面。

> 启动、关闭数据节点以及修改节点配置只能在Leader的集群管理界面操作。

## 3. 客户端高可用

使用API与DolphinDB server的数据节点进行交互时，如果连接的数据节点宕机，API可以自动切换到其他可用的数据节点。这对用户是透明的。目前只有Java和Python API支持高可用。

API的connect方法如下：

```
connect(host,port,username,password,startup,highAvailability)
```

使用connect方法连接数据节点时，只需要指定highAvailability为true。

例如，设置Java API高可用。

```java
import com.xxdb;
DBConnection conn = new DBConnection();
boolean success = conn.connect("localhost", 8848,"admin","123456","",true);
```




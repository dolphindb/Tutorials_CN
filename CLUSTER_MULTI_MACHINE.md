### DolphinDB 多物理节点集群部署

DolphinDB Cluster包括三种类型节点：datanode节点，agent节点和controller节点。
  *  datanode节点用于数据存储，查询以及计算
  *  agent节点用于关闭开启datanode节点
  *  controller节点用于集群管理

本教程假设有五个物理节点: P1,P2,P3,P4,P5。
这五个物理节点的对应的内网地址为
```
P1: 10.1.1.1
P2: 10.1.1.3
P3: 10.1.1.5
P4: 10.1.1.7
P5: 10.1.1.9
```

我们将controller节点设置在P4节点上，在其它每个节点上设置一个agent和一个datanode。这里需要说明一下，每个物理节点必须要有一个agent节点，
用于实现该节点上datanode的启动和关闭。DolphinDB每个集群有且仅有一个controller。

#### 1. 在每个物理节点上，下载DolphinDB，并解压到一个指定目录

例如解压到如下目录

```
/DolphinDB
```

#### 2. 软件授权许可更新

如果用户拿到了企业版试用授权许可，只需要把如下文件替换成新的授权许可即可。每个物理节点的license文件都需要更新。

```
/DolphinDB/server/dolphindb.lic
```
##### 2.1. 企业版与社区版的区别

与社区版本相比，企业版支持更多的节点，CPU内核和内存。


#### 3. DolphinDB P4 集群初始配置

在配置集群的时候请核对授权文件规定的节点个数，每个节点最多内核和最大内存限制。如果配置超出授权文件规定，集群或节点将无法正常启动。这些异常信息都会在log文件中标注。
##### 3.1. 进入server目录

登录P4服务器，进入server子目录

```
cd /DolphinDB/server/
```

##### 3.2. 在server目录下，以Linux为例，创建config, data, log 子目录
```
mkdir /DolphinDB/server/config  //存储配置文件。
mkdir /DolphinDB/server/data    //存储所有数据文件。
mkdir /DolphinDB/server/log     //存储所有日志文件。
```

##### 3.3. 在config目录下，创建controller.cfg文件，并填写如下内容。用户可根据实际情况，调整参数

DolphinDBController节点的主要用途是管理集群节点。本教程controller.cfg里面定义了集群管理的常见参数。

```
localSite=10.1.1.7::master     //节点局域网信息,格式为 IP地址:端口号:节点别名，所有字段都是必选项。
localExecutors=3                   //本地执行者的数量。默认值是CPU的内核数量 - 1。
maxConnections=128                 //最大向内连接数。
maxMemSize=16                      //最大内存数量。
webWorkerNum=4                     //处理http请求的工作池的大小。默认值是1。
workerNum=4                        //常规交互式作业的工作池大小。默认值是CPU的内核数量。
dfsReplicationFactor=1             //每个表分区或文件块的副本数量。默认值是2。
dfsReplicaReliabilityLevel=0       //多个副本是否可以驻留在同一台物理服务器上。 0：是; 1：不。默认值是0。
```


##### 3.4. 在config目录下，创建cluster.nodes文件，并填写如下内容。用户可根据实际情况，调整参数
cluster.nodes用于存放集群数据和计算节点信息。本教程使用5个物理节点，用户可根据授权证书更改节点个数。该配置文件分为两列，第一例存放节点IP地址，端口号和节点别名。这三个信息由冒号“:”分隔。第二列是说明节点类型。比如agent节点，类型为agent,
而数据节点类型为datanode，这里是大小写敏感的。而且别名在集群内必须是唯一的。

在这里，我们把controller节点设置在**P4**，节点配置信息需要包含**P1,P2,P3,P5**的agent和datanode信息。

```
localSite,mode
10.1.1.1:8960:P1-agent,agent
10.1.1.1:8961:P1-NODE1,datanode
10.1.1.3:8960,P2-agent,agent
10.1.1.3:8961:P2-NODE1,datanode
10.1.1.5:8960:P3-agent,agent
10.1.1.5:8961:P3-NODE1,datanode
10.1.1.9:8960:P5-agent,agent
10.1.1.9:8961:P5-NODE1,datanode
```

##### 3.5. 在config目录下，创建cluster.cfg文件，并填写如下内容。用户可根据实际情况，调整参数
cluster.cfg用于存放集群数据和计算节点的配置参数。例如下面定义的参数说明集群上每个节点都使用相同的配置
```
maxConnections=128
maxMemSize=32
workerNum=8
localExecutors=7
webWorkerNum=2
```


#### 3.7. DolphinDB P1,P2,P3,P5 集群初始配置
由于controller节点配置在P4节点，所以P1,P2,P3,P5只需要agent节点的配置信息，log路径和数据存储目录(data)。


##### 3.7.1. 登录每个物理节点， 进入server目录
```
cd /DolphinDB/server/
```

##### 3.7.2. 在server目录下，创建config, data, log子目录
```
mkdir /DolphinDB/server/config  //存储配置文件。
mkdir /DolphinDB/server/data  //存储所有数据文件。
mkdir /DolphinDB/server/log //存储所有日志文件。
```

##### 3.7.3. 在config目录下，创建agent.cfg文件，并填写如下内容。用户可根据实际情况，调整参数

下面列出P1,P2,P3,P5每台服务器上的agent.cfg内容。请注意，节点别名在集群内部必须是唯一的。如果两个节点采用同一个别名，将会造成节点无法响应请求。

###### P1
```
workerNum=3
localExecutors=2
maxMemSize=4
localSite=10.1.1.1:8960:P1-agent
controllerSite=10.1.1.7:8990:master       //controller节点的信息：IP地址:端口号:节点别名。
```

###### P2
```
workerNum=3
localExecutors=2
maxMemSize=4
localSite=10.1.1.3:8960:P2-agent
controllerSite=10.1.1.7:8990:master
```

###### P3
```
workerNum=3
localExecutors=2
maxMemSize=4
localSite=10.1.1.5:8960:P3-agent
controllerSite=10.1.1.7:8990:master
```

###### P5
```
workerNum=3
localExecutors=2
maxMemSize=4
localSite=10.1.1.9:8960:P5-agent
controllerSite=10.1.1.7:8990:master
```



#### 3.8. DolphinDB集群启动

##### 3.8.1. 启动P1,P2,P3,P5的agent节点

进入P1,P2,P3,P5每台服务器，在server目录，即可执行文件所在目录运行以下命令行。agent.log文件存放在log子目录下，如果出现agent无法正常启动的情况，可以根据此日志文件来诊断错误原因。

##### Linux

建议通过linux命令**nohup**（头） 和 **&**（尾） 启动为后台运行模式，这样即使断开程序，也会照常运行。 console默认是开启的，如果要设置为后台运行，必须要设置为0，否者nohup的log文件会占用很大磁盘空间。“-mode”表示节点启动为agent模式，“-home”指定数据以及元数据存储路径，“-config”指定配置文件路径，“-logFile”指定log文件路径。

###### 启动为后台模式
```
nohup ./dolphindb -console 0 -mode agent -home data -config config/agent.cfg -logFile log/agent.log &
```

###### 启动为前端交互模式

```
./dolphindb -mode agent -home data -config config/agent.cfg -logFile log/agent.log
```

##### Windows
```
dolphindb.exe -mode agent -home data -config config/agent.cfg -logFile log/agent.log
```

##### 3.8.2. 启动P4上的controller节点

进入P4服务器，在server目录，即可执行文件所在目录运行以下命令行。注意controller.log文件存放在log子目录下，如果出现controller无法正常启动的情况，可以根据此日志文件来诊断错误原因。
“-clusterConfig”用于指定集群节点配置文件路径，“-nodesFile”用于指定集群节点成员，以及它们的节点类型、IP地址、端口号、别名信息。

##### Linux
```
nohup ./dolphindb -console 0 -mode controller -home data -config config/controller.cfg -clusterConfig config/cluster.cfg -logFile log/controller.log -nodesFile config/cluster.nodes &
```

##### Windows
```
dolphindb.exe -mode controller -home data -config config/controller.cfg -clusterConfig config/cluster.cfg -logFile log/controller.log -nodesFile config/cluster.nodes
```

##### 3.8.3. 如何关闭agent和controller节点

如果是启动为前端交互模式，可以在控制台中输入"quit"退出

```
quit
```

如果是启动为后台交互模式，需要用linux系统kill命令。假设运行命令的linux系统用户名为 "ec2-user"
```
ps aux | grep dolphindb  | grep -v grep | grep ec2-user|  awk '{print $2}' | xargs kill -TERM
```

##### 3.8.4. 启动和关闭datanode节点
在controller和agent节点都启动的前提下，数据节点的开启和关闭可以通过DolphinDB提供的集群和管理界面。下一节有详细介绍。


##### 4.进入集群Web管理界面

在集群的agent和controller节点都成功启动之后
```
在浏览器的地址栏中输入(目前支持浏览器为chrome, firefox)： localhost:8990 (8990为controller的端口号)
```
![](images/multi_web.JPG)

#### 4.1. 启动数据节点

选择所有数据节点，之后点击执行图标，并确定。然后，点击刷新图标来查看状态。在刚关闭完节点，然后重新启动，需要多执行几次才能启动成功。主要原因是操作系统还没有释放资源。
如果出现长时间无法正常启动，请查看log目录下对应的日志文件。如果节点别名是DFS_NODE1，那对应的日志文件在log/DFS_NODE1.log。
常见的节点无法正常启动原因包括:1)超出授权证书规定节点数、内存大小、以及内核的数目。如果出现这种情况，日志中会有明确说明；2)数据文件破坏。这种情况要依据日志文件错误信息，具体情况具体分析。

![](images/multi_start_nodes.JPG)


#### 4.2. DolphinDB集群已经部署成功
点击刷新按钮直到所有节点成功启动，成功启动后，State列会用绿色对号显示成功启动。

![](images/multi_started.JPG)

#### 4.3. DolphinDB集群配置和管理
经过上述步骤，我们已经成功部署DolphinDB集群。在实际使用中我们经常会遇到需要更改参数配置，增加数据节点等等。DolphinDB的Web界面提供配置DolphinDB集群的所有功能。
#### 4.3.1. controller配置

点击按钮Controller Config

![](images/multi_controller_config.JPG)
#### 4.3.2. 数据节点配置

点击按钮Nodes Setup,进行添加删除数据节点。注意，如果节点上已经存放数据，删除节点有可能会造成数据丢失。

![](images/multi_nodes_setup.JPG)

点击按钮Nodes Config, 进行数据节点配置。

![](images/multi_nodes_config.JPG)

#### 5. 当所有节点不在一个局域网内如何部署

DolphinDB默认所有节点在一个局域网内。当节点不在一个局域网内，需要在controller.cfg，agent.cfg和cluster.cfg填入如下参数。

```
lanCluster=0
```

#### 6. 如何设置外网访问

如果设置P1,P2,P3,P5上所有节点的外网地址，在cluster.cfg中填入如下信息。%是节点别名的通配符。用户需要根据自己的真实IP做修改。

```
P1-%.publicName=19.56.128.21
P2-%.publicName=19.56.128.22
P3-%.publicName=19.56.128.23
P5-%.publicName=19.56.128.25
```

每个agent.cfg以及controller.cfg也要加上相应的外网IP

例如
```
publicName=19.56.128.21
```


#### 7. 更多详细信息，请参考dolphindb帮助文档第10章

中文

http://dolphindb.com/cn/help/Newtopic47.html

英文

http://dolphindb.com/help/ClusterSetup.html


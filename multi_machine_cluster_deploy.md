# 多服务器集群部署

本教程详细介绍了多服务器集群部署的步骤，以及分析了节点启动失败的可能原因。本教程主要包含以下内容：

- [1 集群结构](#1-集群结构)
- [2 下载](#2-下载)
- [3 软件授权许可更新](#3-软件授权许可更新)
- [4 DolphinDB集群初始配置](#4-dolphindb集群初始配置)
    - [4.1 配置控制节点](#41-配置控制节点)
    - [4.2 配置代理节点](#42=配置代理节点)
    - [4.3 DolphinDB集群启动](#43-dolphindb集群启动)
- [5 节点启动失败可能原因分析](#5-节点启动失败可能原因分析)
- [6 基于Web的集群管理](#6-基于Web的集群管理)
    - [6.1 控制节点参数配置](#61-控制节点参数配置)
    - [6.2 增删数据节点](#62-增删数据节点)
    - [6.3 修改数据节点参数](#63-修改数据节点参数)
    - [6.4 如何设置外网访问](#64-如何设置外网访问)
    - [6.5 设置数据卷](#65-设置数据卷)
- [7 云部署](#7-云部署)

## 1. 集群结构

DolphinDB Cluster包括三种类型节点：数据节点（data node），代理节点（agent）和控制节点（controller）。

- 数据节点用于数据存储，查询以及计算
- 代理节点用于关闭或开启数据节点
- 控制节点用于集群管理

本教程假设有五个物理节点: **P1**, **P2**, **P3**, **P4**, **P5**。
这五个物理节点的对应的内网地址为

```txt
P1: 10.1.1.1
P2: 10.1.1.3
P3: 10.1.1.5
P4: 10.1.1.7
P5: 10.1.1.9
```

我们将控制节点设置在**P4**节点上，在其它每个节点上设置一个代理节点和一个数据节点。这里需要说明一下：

- **节点的IP地址需要使用内网IP**。

- 每个物理节点必须要有一个代理节点，用于启动和关闭该物理节点上的一个或多个数据节点。

- DolphinDB每个集群有且仅有一个控制节点。

## 2. 下载

在每个物理节点上，从DolphinDB网站下载DolphinDB，并解压到一个指定目录。例如解压到如下目录

```sh
/DolphinDB
```
>请注意：安装路径的目录名中不能含有空格字符，也不能含有中文字符，否则启动数据节点时会失败。

## 3. 软件授权许可更新

如果用户拿到了企业版试用授权许可，只需用其把替换如下授权许可文件即可。每个物理节点的授权许可文件都需要更新。与社区版本相比，企业版支持更多的节点，CPU内核和内存。

```sh
/DolphinDB/server/dolphindb.lic
```

## 4. DolphinDB集群初始配置

启动一个集群，必须配置控制节点和代理节点。数据节点可以在集群启动后通过web界面来配置，当然也可以在初始阶段手工配置。

## 4.1 配置控制节点

在配置集群的时候请核对授权文件规定的节点个数以及每个节点最多内核。如果配置超出授权文件规定，集群将无法正常启动。这些异常信息都会记录在log文件中。

登录**P4**服务器，进入"server"子目录。在server目录下，以Linux为例，创建config, data, log 子目录。 DolphinDB缺省情况下会将server所在目录作为home目录，所有的配置文件和log文件也都会放在home目录下面。为了便于管理，本教程创建了如下目录来分别存放这些内容，但是这不是必须的。

```sh
cd /DolphinDB/server/

mkdir /DolphinDB/server/config
mkdir /DolphinDB/server/data
mkdir /DolphinDB/server/log
```

### 4.1.1 配置控制节点的参数文件

在config目录下，创建controller.cfg文件，可填写以下集群管理的常用参数。用户可根据实际需要调整参数。controller.cfg文件中只有localSite是必需的。其它参数都是可选参数。

```txt
localSite=10.1.1.7:8990:master
localExecutors=3
maxConnections=128
maxMemSize=16
webWorkerNum=4
workerNum=4
dfsReplicationFactor=1
dfsReplicaReliabilityLevel=0
```

以下是对这些参数的解释

| 参数配置        | 解释          |
|:------------- |:-------------|
|localSite=10.1.1.7:8990:master|     节点局域网信息,格式为 IP地址:端口号:节点别名，所有字段都是必选项。|
|localExecutors=3          |         本地执行者的数量。默认值是CPU的内核数量 - 1。|
|maxConnections=128     |            最大向内连接数|
|maxMemSize=16          |            最大内存（GB）|
|webWorkerNum=4              |       处理http请求的工作池的大小。默认值是1。|
|workerNum=4        |                常规交互式作业的工作池大小。默认值是CPU的内核数量。|
|dfsReplicationFactor=1         |    每个表分区或文件块的副本数量。默认值是2。|
|dfsReplicaReliabilityLevel=0     |  多个副本是否可以保存在同一台物理服务器上。 0：是; 1：不。默认值是0。|

### 4.1.2 配置集群成员参数文件

在config目录下，创建cluster.nodes文件，可填写如下内容。用户可根据实际需要调整参数。cluster.nodes用于存放集群代理节点和数据节点信息。本教程使用5个物理节点。该配置文件分为两列，第一例存放节点IP地址，端口号和节点别名。这三个信息由冒号:分隔。第二列是说明节点类型。比如代理节点类型为agent,而数据节点类型为datanode。节点别名是大小写敏感的，而且在集群内必须是唯一的。

本例中集群的节点配置信息需要包含位于**P1**,**P2**,**P3**,**P5**的代理节点和数据节点信息。

```txt
localSite,mode
10.1.1.1:8960:P1-agent,agent
10.1.1.1:8961:P1-NODE1,datanode
10.1.1.3:8960:P2-agent,agent
10.1.1.3:8961:P2-NODE1,datanode
10.1.1.5:8960:P3-agent,agent
10.1.1.5:8961:P3-NODE1,datanode
10.1.1.9:8960:P5-agent,agent
10.1.1.9:8961:P5-NODE1,datanode
```

### 4.1.3 配置数据节点的参数文件

在config目录下，创建cluster.cfg文件，并填写如下内容。cluster.cfg用于存放对集群中每个数据节点都适用的配置参数，用户可根据实际情况调整参数。

```txt
maxConnections=128
maxMemSize=32
workerNum=8
localExecutors=7
webWorkerNum=2
```

## 4.2 配置代理节点

登录**P1**,**P2**,**P3**和**P5**，在每台服务器的server目录下，创建config, data, log子目录。用户也可选择其它位置来存放这三个目录。

```sh
cd /DolphinDB/server/
mkdir /DolphinDB/server/config
mkdir /DolphinDB/server/data
mkdir /DolphinDB/server/log
```

在config目录下，创建agent.cfg文件，并填写如下内容。用户可根据实际情况，调整参数。下面列出**P1**,**P2**,**P3**和**P5**每台服务器上的agent.cfg内容。这些参数中localSite和controllerSite是必需的，其它参数是可选的。

#### P1

```txt
workerNum=3
localExecutors=2
maxMemSize=4
localSite=10.1.1.1:8960:P1-agent
controllerSite=10.1.1.7:8990:master
```

#### P2

```txt
workerNum=3
localExecutors=2
maxMemSize=4
localSite=10.1.1.3:8960:P2-agent
controllerSite=10.1.1.7:8990:master
```

#### P3

```txt
workerNum=3
localExecutors=2
maxMemSize=4
localSite=10.1.1.5:8960:P3-agent
controllerSite=10.1.1.7:8990:master
```

#### P5

```txt
workerNum=3
localExecutors=2
maxMemSize=4
localSite=10.1.1.9:8960:P5-agent
controllerSite=10.1.1.7:8990:master
```

由于代理节点依照agent.cfg中的controllerSite参数值来寻找控制节点并与其通信，controller.cfg中的localSite参数值应与所有agent.cfg中的controllerSite参数值一致。 若改变controller.cfg中的localSite参数值，即使只是别名改变，所有agent.cfg中的controllerSite参数值都应做相应改变。

## 4.3 DolphinDB集群启动

### 4.3.1 启动代理节点

登录**P1**,**P2**,**P3**和**P5**，在每一台服务器的server目录，即可执行文件所在目录运行以下命令行。agent.log文件存放在log子目录下，如果出现agent无法正常启动的情况，可以根据此日志文件来诊断错误原因。

#### Linux后台模式启动

```sh
nohup ./dolphindb -console 0 -mode agent -home data -config config/agent.cfg -logFile log/agent.log &
```

建议通过Linux命令`nohup`（头） 和 `&`（尾）启动为后台运行模式，这样即使终端失去连接，DolphinDB也会持续运行。

“-console”默认是为 1，如果要设置为后台运行，必须要设置为0（"-console 0")，否则系统运行一段时间后会自动退出。。

“-mode”表示节点性质，“-home”指定数据以及元数据存储路径，“-config”指定配置文件路径，“-logFile”指定log文件路径。

#### Linux前端交互模式启动

```sh
./dolphindb -mode agent -home data -config config/agent.cfg -logFile log/agent.log
```

#### Windows下启动

```sh
dolphindb.exe -mode agent -home data -config config/agent.cfg -logFile log/agent.log
```

### 4.3.2 启动控制节点

进入**P4**服务器，在server目录，即可执行文件所在目录运行以下命令行。注意controller.log文件存放在log子目录下，如果出现controller无法正常启动的情况，可以根据此日志文件来诊断错误原因。

“-clusterConfig”用于指定集群节点配置文件路径，“-nodesFile”用于指定集群节点成员，以及它们的节点类型、IP地址、端口号、别名信息。

#### Linux

```sh
nohup ./dolphindb -console 0 -mode controller -home data -config config/controller.cfg -clusterConfig config/cluster.cfg -logFile log/controller.log -nodesFile config/cluster.nodes &
```

#### Windows

```sh
dolphindb.exe -mode controller -home data -config config/controller.cfg -clusterConfig config/cluster.cfg -logFile log/controller.log -nodesFile config/cluster.nodes
```

### 4.3.3 如何关闭代理和控制节点

如果是启动为前端交互模式，可以在控制台中输入"quit"退出

```sh
quit
```

如果是启动为后台交互模式，需要用linux系统kill命令。假设运行命令的linux系统用户名为 "ec2-user"

```sh
ps aux | grep dolphindb  | grep -v grep | grep ec2-user|  awk '{print $2}' | xargs kill -TERM
```

### 4.3.4 启动网络上的集群管理器

启动控制节点和代理节点之后，可以通过DolphinDB提供的集群管理界面来开启或关闭数据节点。在浏览器的地址栏中输入(目前支持Chrome与Firefox)：

```sh
10.1.1.7:8990
```

(8990为控制节点的端口号)

![集群管理](images/multi_web.JPG)

### 4.3.5 DolphinDB权限控制

DolphinDB database 提供了良好的安全机制。只有系统管理员才有权限做集群部署。在初次使用DolphinDB网络集群管理器时，需要用以下默认的系统管理员账号登录。

```txt
系统管理员帐号名: admin
默认密码: 123456
```

点击登录链接

![登录链接](images/login_logo.JPG)

输入管理员用户名和密码

![输入账号](images/login.JPG)

使用上述账号登录以后，可修改"admin"的密码，亦可添加用户或其他管理员账户。

### 4.3.6 启动数据节点

选择所有数据节点，点击执行图标，并确定。节点启动可能要耗时30秒到一分钟。点击刷新图标来查看状态。若看到State栏全部为绿色对勾，则整个集群已经成功启动。

![启动](images/multi_start_nodes.JPG)

![刷新](images/multi_started.JPG)

如果出现长时间无法正常启动，请查看log目录下该节点的logFile. 如果节点名字是DFS_NODE1，那对应的logFile应该在 log/DFS_NODE1.log。

log文件中有可能出现错误信息 Failed to bind the socket on XXXX。这里的XXXX是待启动的节点端口号。这可能是因为此端口号被其它程序占用，这种情况下将其他程序关闭再重新启动节点即可。也可能是因为刚刚关闭了使用此端口的数据节点，Linux kernel还没有释放此端口号。这种情况下稍等30秒，再启动节点即可。

也可在控制节点执行以下代码来启动数据节点：

```txt
startDataNode(["P1-NODE1", "P2-NODE1","P3-NODE1","P5-NODE1"])
```

### 5. 节点启动失败可能原因分析

如果节点长时间无法启动，可能有以下原因：

1. **端口号被占用**。查看log文件，如果log文件中出现错误信息"Failed to bind the socket on XXXX"，这里的XXXX是待启动的节点端口号。这可能是该端口号已经被其他程序占用，这种情况下将其他程序关闭或者重新给DolphinDB节点分配端口号在重新启动节点即可，也有可能是刚刚关闭了该节点，Linux kernel还没有释放此端口号。这种情况下稍等30秒，再启动节点即可。
2. **防火墙未开放端口**。防火墙会对一些端口进行限制，如果使用到这些端口，需要在防火墙中开放这些端口。
3. **配置文件中的IP地址、端口号或节点别名没有书写正确。**
4. 集群默认情况下是采用UDP发送心跳，** 若发现agent节点进程已经启动了，但是集群web界面上显示不在线**，那就应该是集群网络不支持UDP包，需要将心跳机制改为TCP方式发送: 在agent.cfg和cluster.cfg文件中加上配置项lanCluster=0。
5. **集群成员配置文件cluster.nodes第一行为空行**。查看log文件，如果log文件中出现错误信息"Failed to load the nodes file [XXXX/cluster.nodes] with error: The input file is empty."，表示cluster.nodes的第一行为空行，这种情况下只需将文件中的空行删除，再重新启动节点即可。
6. **宏变量\<ALIAS>在明确节点的情况下使用无效**。查看配置文件cluster.cfg，若在明确了节点的情况下使用宏变量\<ALIAS>，如： P1-NODE1.persistenceDir = /hdd/hdd1/streamCache/\<ALIAS>, 则会导致该节点无法正常启动。这种情况下只需要把\<ALIAS>删除，替换成特定节点即可，如：P1-NODE1.persistenceDir = /hdd/hdd1/streamCache/P1-NODE1; 
若想对所有节点使用宏变量, 则做如下修改：persistenceDir = /hdd/hdd1/streamCache/\<ALIAS>。 宏变量的具体使用可详情参照[DolphinDB用户手册](https://www.dolphindb.cn/cn/help/index.html?ClusterSetup1.html)

## 6. 基于Web的集群管理

经过上述步骤，我们已经成功部署DolphinDB集群。在实际使用中我们经常会需要改变集群配置。DolphinDB的网络界面提供更改集群配置的所有功能。

### 6.1 控制节点参数配置

点击"Controller Config"按钮会弹出一个控制界面，这里的localExectors, maxConnections, maxMemSize, webWorkerNum以及workerNum等参数是我们在3.1.1中创建controller.cfg时填写的。这些配置信息都可以在这个界面上更改，新的配置会在重启控制节点之后生效。注意如果改变控制节点的localSite参数值，一定要在所有agent.cfg中对controllerSite参数值应做相应修改，否则会造成集群无法正常运行。

![controller配置](images/multi_controller_config.JPG)

### 6.2 增删数据节点

点击"Nodes Setup"按钮，会进入集群节点配置界面。下图显示的配置信息是我们在3.1.2中创建的cluster.nodes中的信息。在此界面中可以添加或删除数据节点。新的配置会在整个集群重启之后生效。集群重启的具体步骤为：

1. 关闭所有数据节点
2. 关闭控制节点
3. 启动控制节点
4. 启动数据节点。

另外需要注意，如果节点上已经存放数据，删除节点有可能会造成数据丢失。

![nodes_setup](images/multi_nodes_setup.JPG)

若新的数据节点位于一个新的物理机器上，我们必须在此物理机器上根据3.2中的步骤配置并启动一个新的代理节点，在cluster.nodes中增添有关新的代理节点和数据节点的信息，并重新启动控制节点。

## 6.3 修改数据节点参数

点击"Nodes Config"按钮, 可进行数据节点配置。以下参数是我们在3.1.3中创建cluster.cfg中提供的。除了这些参数之外，用户还可以根据实际应用在这里添加配置其它参数。重启所有数据节点后即可生效。

![nodes_config](images/multi_nodes_config.JPG)

## 6.4 如何设置集群管理器通过外网访问
通常同属一个内网的集群节点我们会将site信息设置为内网地址，这样节点间的网络通信会更加高效。若同时需要通过外网地址访问集群管理器，需要配置publicName选项，作用是告诉集群管理器，在浏览器中用指定的外网地址来打开节点的Notebook。publicName可以设置为域名或者IP地址，如果要启动HTTPS,则必须是域名。举个例子，要设置**P1**, **P2**, **P3**和**P5**上所有节点的外网地址，需要在cluster.cfg中填入如下信息。%是节点别名的通配符。

```txt
P1-%.publicName=19.56.128.21
P2-%.publicName=19.56.128.22
P3-%.publicName=19.56.128.23
P5-%.publicName=19.56.128.25
```

另外controller.cfg也要加上相应的外网域名或IP, 例如

```txt
publicName=19.56.128.24
```

## 6.5 设置数据卷

数据卷是位于数据节点上的文件夹，用来保存分布式文件系统产生的的数据。一个节点可以有多个数据卷。要确保最优性能，每个数据卷应当对应不同的物理设备。如果多个数据卷对应同一个物理设备，会影响性能。

可在cluster.cfg中设置数据卷的路径。如果用户不设置数据卷的路径，系统会默认按数据节点别名来设置数据卷的路径。若节点别名为P5-NODE1，系统会自动在该节点的home目录下创建一个名为P5-NODE1的子目录来存储数据。注意：数据卷只支持绝对路径，不支持相对路径。

三种设置数据卷路径的方法：

### 对每个节点分别指定数据卷路径

```txt
P3-NODE1.volumes=/DFS/P3-NODE1
P5-NODE1.volumes=/DFS/P5-NODE1
```

### 通过%和?通配符

？代表单个字符; ％表示0,1或多个字符。

将所有以"-NODE1"为结尾的节点的数据存放到 /VOL1/：

```txt
%-NODE1.volumes=/VOL1/
```

等同于：

```txt
P1-NODE1.volumes=/VOL1/
P2-NODE1.volumes=/VOL1/
P3-NODE1.volumes=/VOL1/
P5-NODE1.volumes=/VOL1/
```

### 通过ALIAS通配符

若所有数据节点的数据卷路径都含有节点别名，可使用<ALIAS>来配置数据卷路径。可用以下代码为每台服务器配置两个物理卷/VOL1/和/VOL2/：

```txt
volumes=/VOL1/<ALIAS>,/VOL2/<ALIAS>
```

等同于：

```txt
P1-NODE1.volumes=/VOL1/P1-NODE1,/VOL2/P1-NODE1
P2-NODE1.volumes=/VOL1/P2-NODE1,/VOL2/P2-NODE1
P3-NODE1.volumes=/VOL1/P3-NODE1,/VOL2/P3-NODE1
P5-NODE1.volumes=/VOL1/P5-NODE1,/VOL2/P5-NODE1
```

## 7. 云部署

DolphinDB集群可以部署在局域网内，也可以部署在私有云或公有云上。DolphinDB默认集群的所有节点在一个局域网内(lanCluster=1)并通过UDP广播来监测节点心跳。但是在云平台上，所有节点不一定在一个局域网内，也有可能不支持UDP。在云平台上，需要在controller.cfg和agent.cfg填入`lanCluster=0`的参数配置来实现非UDP模式的节点之间的通讯。否则，由于可能无法正常检测到节点的心跳，集群可能无法正常工作。

更多详细信息，请参考DolphinDB帮助文档第10章

- [中文](https://www.dolphindb.cn/cn/help/ClusterSetup.html)
- [英文](http://www.dolphindb.com/help/ClusterSetup.html)
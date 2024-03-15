# 多服务器集群部署

  DolphinDB 集群包括四种类型节点：控制节点（controller）、代理节点（agent）、数据节点（data node）和计算节点（compute node）。

- **控制节点**：控制节点是 DolphinDB 集群的核心部分，负责收集代理节点和数据节点的心跳，监控每个节点的工作状态，管理分布式文件系统的元数据和事务日志。多服务器集群中只有一个控制节点。
- **代理节点**：代理节点负责执行控制节点发出的启动和关闭数据节点或计算节点的命令。在一个集群中，每台物理服务器有且仅有一个代理节点。
- **数据节点**：数据节点既可以存储数据，也可以用于数据的查询和计算。每台物理服务器可以配置多个数据节点。
- **计算节点**：计算节点主要用于数据的查询和计算，包括历史数据查询、分布式表关联查询、批计算、流计算和机器学习模型训练等。计算节点不存储数据，但可以通过 [loadTable](https://docs.dolphindb.cn/zh/funcs/l/loadTable.html) 函数加载数据进行计算。在计算节点上，可以执行创建数据库和分区表的语句，也可以调用数据写入接口往分区表写入数据，但是相比在数据节点执行写入任务，会增加一定的网络传输的开销，因为计算节点不存储数据，会把涉及存储的数据均匀地发送并存储到集群中的数据节点上。每台物理服务器可以配置多个计算节点。

  本教程用于在 Linux 操作系统上进行多服务器集群的部署、升级、过期 License 升级，并对常见问题做出解答，便于用户快速上手 DolphinDB。包含以下主题：

- [1. 部署 DolphinDB 多服务器集群](#1-部署-dolphindb-多服务器集群)
  - [第一步：下载](#第一步下载)
  - [第二步：更新软件授权许可](#第二步更新软件授权许可)
  - [第三步：集群配置](#第三步集群配置)
  - [第四步：启动集群](#第四步启动集群)
  - [第五步：连接数据节点创建数据库和分区表](#第五步连接数据节点创建数据库和分区表)
  - [第六步：连接计算节点查询和计算](#第六步连接计算节点查询和计算)
- [2. 基于 Web 的集群管理](#2-基于-web-的集群管理)
  - [2.1 控制节点参数配置](#21-控制节点参数配置)
  - [2.2 数据节点和计算节点参数配置](#22-数据节点和计算节点参数配置)
  - [2.3 设置集群管理器通过外网访问](#23-设置集群管理器通过外网访问)
- [3. 集群升级](#3-集群升级)
- [4. 授权许可文件过期更新](#4-授权许可文件过期更新)
- [5. 常见问题解答（FAQ）](#5-常见问题解答faq)
  - [5.1 节点启动失败的可能原因](#51-节点启动失败的可能原因)
  - [5.2 如何通过 systemd 命令启动 DolphinDB 集群？](#52-如何通过-systemd-命令启动-dolphindb-集群)
  - [5.3 Web 管理界面无法访问怎么办？](#53-web-管理界面无法访问怎么办)
  - [5.4 Linux 升级失败如何版本回退？](#54-linux-升级失败如何版本回退)
  - [5.5 为什么在线更新授权许可文件失败？](#55-为什么在线更新授权许可文件失败)
  - [5.6 为什么云部署节点无法启动？](#56-为什么云部署节点无法启动)
  - [5.7 如何进行配置参数调优？](#57-如何进行配置参数调优)
  - [5.8 如何设置数据卷？](#58-如何设置数据卷)
- [6. 参考](#6-参考)


## 1. 部署 DolphinDB 多服务器集群

  本教程示例集群的部署架构图如下：

  <img src="./images/multi_machine_cluster_deployment/1_1.png" width=60%>

  三台部署服务器（P1, P2, P3）对应的内网 IP 地址为：

  ```
  P1:10.0.0.80
  P2:10.0.0.81
  P3:10.0.0.82
  ```

  部署本教程示例多服务器集群前的要求和准备：

- 本教程示例集群超过了社区版试用授权许可节点数的限制，所以必须[申请企业版 License](https://dolphindb.cn/product#downloads)并按第一章第二步的方法进行更新。
- 建议节点的 IP 地址使用内网 IP，网络使用万兆以太网。如果使用外网地址，则不能保证节点间网络传输性能。
- DolphinDB 多机集群（非高可用集群）有且仅有一个控制节点。
- 部署数据节点或者计算节点的服务器必须部署一个代理节点，用于启动和关闭该服务器上的数据节点或计算节点。

### 第一步：下载

  在每台服务器上下载 DolphinDB 安装包并解压。

- 官方下载地址：<https://dolphindb.cn/product#downloads>
- 也可以通过 Shell 指令下载。下载方式如下：

  ```sh
  wget https://www.dolphindb.cn/downloads/DolphinDB_Linux64_V${release}.zip -O dolphindb.zip
  ```

  其中，`${release}` 代表版本。例如：下载 2.00.11.3 版本的 Linux64 server，使用以下指令：

  ```sh
  wget https://www.dolphindb.cn/downloads/DolphinDB_Linux64_V2.00.11.3.zip -O dolphindb.zip
  ```

  如需下载 ABI 或 JIT 版本 server，则需要在版本号后以下划线连接 ABI 或 JIT。例如：下载 2.00.11.3 版本的 Linux64 ABI server, 使用以下指令：

  ```sh
  wget https://www.dolphindb.cn/downloads/DolphinDB_Linux64_V2.00.11.3_ABI.zip -O dolphindb.zip
  ```

  下载 2.00.11.3 版本的 Linux64 JIT 版本 server，使用以下指令：

  ```sh
  wget https://www.dolphindb.cn/downloads/DolphinDB_Linux64_V2.00.11.3_JIT.zip -O dolphindb.zip
  ```

  以此类推。

- 执行以下 Shell 指令解压安装包至指定路径 (`/path/to/directory`)：

  ```sh
  unzip dolphindb.zip -d </path/to/directory>
  ```

  > 注意：安装路径的目录名中不能含有空格字符或中文字符，否则启动数据节点时会失败。
  
### 第二步：更新软件授权许可

  与社区版试用授权许可相比，企业版试用授权许可支持更多的节点、CPU 核数和内存。用户拿到企业版试用授权许可，只需用其替换如下文件即可。请注意：每台服务器上的授权许可文件都需要替换。

  ```
  /DolphinDB/server/dolphindb.lic
  ```

本教程示例集群超过了社区版 License 节点数的限制，可以点击此处申请企业版试用授权许：许：[申请企业版 License](https://dolphindb.cn/product#downloads)。

### 第三步：集群配置

#### （1）P1 需要配置的文件

  登录 **P1** 服务器，进入 */DolphinDB/server/clusterDemo/config* 目录

- **配置控制节点参数文件**

  执行以下 Shell 指令修改 *controller.cfg* 配置文件：

  ```
  vim ./controller.cfg
  ```

  ```
  mode=controller
  localSite=10.0.0.80:8900:controller8900
  dfsReplicationFactor=1
  dfsReplicaReliabilityLevel=2
  dataSync=1
  workerNum=4
  maxConnections=512
  maxMemSize=8
  lanCluster=0
  ```

  在这里必须配置的是 *localSite*，指定控制节点的 IP 地址、端口号和别名。其余参数用户应结合自身服务器硬件配置进行合理参数调优。

- **配置集群成员参数文件**

  *cluster.nodes* 用于存放集群代理节点、数据节点和计算节点的信息。本教程配置 3 个代理节点，2 个数据节点和 1 个计算节点，用户可以根据实际要求配置节点个数。该配置文件分为两列，第一例存放节点 IP 地址、端口号和节点别名。这三个信息由冒号分隔；第二列是说明节点类型，比如代理节点类型为 agent，数据节点类型为 datanode，计算节点为 computenode。

  > 注意：节点别名是大小写敏感的，而且在集群内必须是唯一的。
  >

  本例中集群的节点配置信息需要包含位于 **P1** ， **P2** ， **P3** 的代理节点、数据节点和计算节点信息。执行以下 Shell 指令修改 *cluster.nodes* 配置文件：

  ```
  vim ./cluster.nodes
  ```

  ```
  localSite,mode
  10.0.0.80:8901:P1-agent,agent
  10.0.0.80:8902:P1-datanode,datanode
  10.0.0.81:8901:P2-agent,agent
  10.0.0.81:8902:P2-datanode,datanode
  10.0.0.82:8901:P3-agent,agent
  10.0.0.82:8902:P3-computenode,computenode
  ```

- **配置数据节点和计算节点参数文件**

  执行以下 Shell 指令修改 *cluster.cfg* 配置文件：

  ```
  vim ./cluster.cfg
  ```

  ```
  maxMemSize=32
  maxConnections=512
  workerNum=4
  maxBatchJobWorker=4
  chunkCacheEngineMemSize=2
  TSDBCacheEngineSize=1
  newValuePartitionPolicy=add
  maxPubConnections=64
  subExecutors=4
  lanCluster=0
  enableChunkGranularityConfig=true
  ```

  *cluster.cfg* 的配置适用于集群中所有数据节点和计算节点，用户应结合自身服务器硬件配置进行合理参数调优。

- **配置代理节点参数文件**

  执行以下 Shell 指令修改 *agent.cfg* 配置文件：

  ```
  vim ./agent.cfg
  ```

  ```
  mode=agent
  localSite=10.0.0.80:8901:P1-agent
  controllerSite=10.0.0.80:8900:controller8900
  workerNum=4
  maxMemSize=4
  lanCluster=0
  ```

  在这里， *controllerSite* 需要与 P1 的 *controller.cfg* 中的 *localSite* 保持一致，因为代理节点使用 *agent.cfg* 中的参数 *controllerSite*来寻找集群中的控制节点。若若 *controller.cfg* 中的参数 *localSite* 有变化，即使只是节点别名有改变，所有代理节点的配置文件 *agent.cfg* 中的参数 *controllerSite* 都应当做相应的改变。此外，还必须配置的是 *localSite*，指定代理节点的 IP 地址、端口号和别名。其余参数用户可根据实际情况进行调整。

#### （2）P2 需要配置的文件

  登录 **P2** 服务器，进入 */DolphinDB/server/clusterDemo/config* 目录

- **配置代理节点参数文件**

  执行以下 Shell 指令修改 *agent.cfg* 配置文件：

  ```
  vim ./agent.cfg
  ```

  ```
  mode=agent
  localSite=10.0.0.81:8901:P2-agent
  controllerSite=10.0.0.80:8900:controller8900
  workerNum=4
  maxMemSize=4
  lanCluster=0
  ```

  在这里， *controllerSite* 需要与 P1 的 *controller.cfg* 中的 *localSite* 保持一致，因为代理节点使用 *agent.cfg* 中的参数 *controllerSite* 来寻找集群中的控制节点。若 *controller.cfg* 中的参数 *localSite* 有变化，即使只是节点别名有改变，所有代理节点的配置文件 *agent.cfg* 中的参数 *controllerSite* 都应当做相应的改变。此外，还必须配置的是 *localSite* ，指定代理节点的 IP 地址、端口号和别名。其余参数用户可根据实际情况进行调整。

#### （3）P3 需要配置的文件

  登录 **P3** 服务器，进入 */DolphinDB/server/clusterDemo/config* 目录

- **配置代理节点参数文件**

  执行以下 Shell 指令修改 *agent.cfg* 配置文件：

  ```
  vim ./agent.cfg
  ```

  ```
  mode=agent
  localSite=10.0.0.82:8901:P3-agent
  controllerSite=10.0.0.80:8900:controller8900
  workerNum=4
  maxMemSize=4
  lanCluster=0
  ```

  在这里， *controllerSite* 需要与 P1 的 *controller.cfg* 中的 *localSite* 保持一致，因为代理节点使用 *agent.cfg* 中的参数 *controllerSite* 来寻找集群中的控制节点。若 *controller.cfg* 中的参数 *localSite* 有变化，即使只是节点别名有改变，所有代理节点的配置文件 *agent.cfg* 中的参数 *controllerSite* 都应当做相应的改变。此外，还必须配置的是 *localSite* ，指定代理节点的 IP 地址、端口号和别名。其余参数用户可根据实际情况进行调整。

### 第四步：启动集群

  登录服务器 **P1, P2 和 P3**，进入 */DolphinDB/server* 目录，第一次启动时需要修改文件权限，执行以下 Shell 指令：

  ```
  chmod +x dolphindb
  ```

- **启动控制节点**

  在服务器 **P1** 的 */DolphinDB/server/clusterDemo* 目录执行以下 Shell 指令启动控制节点：

  ```
  sh startController.sh
  ```

  > 注意：本教程示例集群的控制节点部署在服务器 P1，所以只需要在服务器 P1 启动控制节点。
  >

  可以执行以下 Shell 指令，查看节点是否成功启动：

  ```
  ps aux|grep dolphindb
  ```

  返回如下信息说明控制节点启动成功：

  <img src="./images/multi_machine_cluster_deployment/1_2.png" width=80%>

- **启动代理节点**

  在服务器 **P1, P2 和 P3** 的 */DolphinDB/server/clusterDemo* 目录执行以下 Shell 指令启动代理节点：

  ```
  sh startagent.sh
  ```

  可以执行以下 Shell 指令，查看节点是否成功启动：

  ```
  ps aux|grep dolphindb
  ```

  返回如下信息说明代理节点启动成功：

  <img src="./images/multi_machine_cluster_deployment/1_3.png" width=80%>

- 启动数据节点和计算节点

  可以在 Web 管理界面启动或关闭数据节点和计算节点，以及修改集群的配置。在浏览器中输入控制节点的 IP 地址和端口号即可进入 Web 管理界面，教程中的部署控制节点的服务器 IP 地址为 10.0.0.80，部署端口为 8900，所以访问地址为 10.0.0.80:8900，打开后的 Web 管理界面如下。以管理员身份（默认账号：admin，默认密码：123456）登录 Web 管理界面后，用户可以通过勾选想要启动的数据节点和计算节点，再点击启动（关闭）按键即可启动（关闭）相应的数据节点和计算节点：

  刷新页面后可看到对应的数据节点和计算节点已启动，如下图所示：

  <img src="./images/multi_machine_cluster_deployment/1_4.png" width=80%>

### 第五步：连接数据节点创建数据库和分区表

  数据节点既可以存储数据，也可以用于数据的查询和计算。接下来通过一个例子介绍如何在 DolphinDB 集群数据节点创建数据库并写入数据。首先，打开控制节点的 Web 管理界面，点击对应的数据节点打开其 Web 交互编程界面，如下图所示（以 P1-datanode 为例）：

  <img src="./images/multi_machine_cluster_deployment/1_5.png" width=80%>

  <img src="./images/multi_machine_cluster_deployment/1_6.png" width=80%>

  也可以在浏览器直接输入数据节点的 IP 地址和端口号进入数据节点的 Web 交互编程界面。

  在数据节点的 Web 交互编程界面执行以下语句创建数据库和分区表：

  ```
  // 创建存储的数据库和分区表
  login("admin", "123456")
  dbName = "dfs://testDB"
  tbName = "testTB"
  if(existsDatabase(dbName)){
          dropDatabase(dbName)
  }
  db = database(dbName, VALUE, 2021.01.01..2021.12.31)
  colNames = `SecurityID`DateTime`PreClosePx`OpenPx`HighPx`LowPx`LastPx`Volume`Amount
  colTypes = [SYMBOL, DATETIME, DOUBLE, DOUBLE, DOUBLE, DOUBLE, DOUBLE, INT, DOUBLE]
  schemaTable = table(1:0, colNames, colTypes)
  db.createPartitionedTable(table=schemaTable, tableName=tbName, partitionColumns=`DateTime)
  ```

  然后，执行以下语句创建 5000 个股票 1 分钟 K 线数据并写入上面创建的分区表：

  ```
  // 模拟数据并写入分区表
  n = 1210000
  randPrice = round(10+rand(1.0, 100), 2)
  randVolume = 100+rand(100, 100)
  SecurityID = lpad(string(take(0..4999, 5000)), 6, `0)
  DateTime = (2023.01.08T09:30:00 + take(0..120, 121)*60).join(2023.01.08T13:00:00 + take(0..120, 121)*60)
  PreClosePx = rand(randPrice, n)
  OpenPx = rand(randPrice, n)
  HighPx = rand(randPrice, n)
  LowPx = rand(randPrice, n)
  LastPx = rand(randPrice, n)
  Volume = int(rand(randVolume, n))
  Amount = round(LastPx*Volume, 2)
  tmp = cj(table(SecurityID), table(DateTime))
  t = tmp.join!(table(PreClosePx, OpenPx, HighPx, LowPx, LastPx, Volume, Amount))
  dbName = "dfs://testDB"
  tbName = "testTB"
  loadTable(dbName, tbName).append!(t)
  ```

  以上函数语句的用法说明请参考[用户手册](https://docs.dolphindb.cn/zh/funcs/funcs_intro.html)，也可以在交互编程界面选中函数语句跳转至弹出的网页查看函数说明。

  <img src="./images/multi_machine_cluster_deployment/1_7.png" width=70%>

  语句执行成功后可在交互编程界面的左边，**数据库**一栏查看已创建的库表及字段信息。

  <img src="./images/multi_machine_cluster_deployment/1_8.png" width=50%>

  也可在**本地变量**一栏查看已创建的变量和表，展示了变量名、变量类型、变量维度大小、占用内存大小等信息，并且可以直接点击变量名进行变量预览。

  <img src="./images/multi_machine_cluster_deployment/1_9.png" width=80%>

  上述语句执行成功后，可回到控制节点的**文件系统**查看已创建的库表。

  <img src="./images/multi_machine_cluster_deployment/1_10.png" width=80%>

### 第六步：连接计算节点查询和计算

  计算节点主要用于数据的查询和计算。接下来通过一个例子介绍如何在计算节点对数据库内的分区表执行查询和计算。首先，打开控制节点的 Web 管理界面，点击对应的计算节点打开其 Web 交互编程界面，如下图所示：

  <img src="./images/multi_machine_cluster_deployment/1_11.png" width=80%>

  <img src="./images/multi_machine_cluster_deployment/1_12.png" width=80%>

  也可以在浏览器直接输入计算节点的 IP 地址和端口号进入计算节点的 Web 交互编程界面。

  在计算节点的 Web 交互编程界面执行以下语句加载分区表对象，此时只加载了分区表的元数据，并未加载分区表全量数据，所以响应时间非常快：

  ```
  // 加载分区表对象
  pt = loadTable("dfs://testDB", "testTB")
  ```

  然后，执行以下语句查询股票表中每天包含的数据条数：

  ```
  // SQL 返回数据量少的时候，可以直接取回客户端展示
  select count(*) from pt group by date(DateTime) as Date
  ```

  语句执行成功后，查询结果会在 Web 界面下方展示：

  <img src="./images/multi_machine_cluster_deployment/1_13.png" width=40%>

  执行以下语句计算每支股票每天的 OHLC 值：

  ```
  // SQL 返回数据量较大时，可以赋值给变量，占用 server 端内存，客户端分页取回展示
  result = select first(LastPx) as Open, max(LastPx) as High, min(LastPx) as Low, last(LastPx) as Close from pt group by date(DateTime) as Date, SecurityID
  ```

  在这里，将计算结果赋值给了 `result` 变量，这样就不会直接在客户端界面直接展示，减少客户端内存占用，用户可以通过点击**本地变量**栏目下的 `result` 变量进行分页展示查看：

  <img src="./images/multi_machine_cluster_deployment/1_14.png" width=70%>

## 2. 基于 Web 的集群管理

  完成部署后，我们可以通过控制节点的 Web 管理界面更改集群配置。

### 2.1 控制节点参数配置

  点击 **Controller Config** 按钮，可进行控制节点的参数配置。以下参数是在第一章中 *controller.cfg* 里配置的，用户可以根据实际应用在这里添加、删除、修改配置参数。这些配置信息都可以在这个界面上进行更改，修改的配置会在重启控制节点之后生效。

  > 注意：如果改变了控制节点的 *localSite* 参数值，一定要对所有 *agent.cfg* 中的 *controllerSite* 参数做相应修改，否则集群将无法正常运行。
  >

  <img src="./images/multi_machine_cluster_deployment/2_1.png" width=80%>

### 2.2 数据节点和计算节点参数配置

  点击 **Nodes Config** 按钮，可进行数据节点和计算节点的参数配置。以下参数是在第一章中 *cluster.cfg* 里配置的，用户可以根据实际应用在这里添加、删除、修改配置参数。修改的配置会在重启数据节点和计算节点之后生效。

  <img src="./images/multi_machine_cluster_deployment/2_2.png" width=80%>

### 2.3 设置集群管理器通过外网访问

  通常，集群所有节点同属一个内网时，将 *site* 信息设置为内网地址，使节点间的网络通信更加高效。若同时需要通过外网地址访问集群管理器，需要在 controller 上配置 *publicName* 选项，用来指定外网访问的地址。*publicName* 可以设置为域名或者 IP 地址，如果要启动 HTTPS，则必须是域名。举个例子，要设置服务器 **P1, P2, P3** 上所有节点的外网地址，需要在 *cluster.cfg* 中填入如下信息：

  ```
  P1-%.publicName=19.56.128.21
  P2-%.publicName=19.56.128.22
  P3-%.publicName=19.56.128.23
  ```

  `%`是节点别名的通配符。另外 *controller.cfg* 也要加上相应的外网域名或 IP, 例如

  ```
  publicName=19.56.128.21
  ```

## 3. 集群升级

  **第一步：正常关闭集群所有节点**

  登录服务器 **P1 , P2 和 P3**，进入 */DolphinDB/server/clusterDemo* 目录执行以下 Shell 指令：

  ```
  ./stopAllNode.sh
  ```

  **第二步：备份旧版本的元数据文件**

  多服务器集群只有写入过数据才会创建相应的元数据文件，如果集群没有数据写入行为则可直接跳过此步骤进行升级。

- 备份控制节点元数据

  控制节点元数据默认存储在控制节点服务器的 */DolphinDB/server/clusterDemo/dfsMeta* 目录下的 *DFSMetaLog.0* 文件，如果数据量超过一定的大小则还会生成 *DFSMasterMetaCheckpoint.0* 文件。控制节点元数据的默认存储目录：

  ```
  /DolphinDB/server/clusterDemo/dfsMeta
  ```

  登录控制节点所在的服务器 **P1** ，可进入上述目录执行以下 Shell 指令进行备份：

  ```
  mkdir backup
  cp -r DFSMetaLog.0 backup
  cp -r DFSMasterMetaCheckpoint.0 backup
  ```

- 备份数据节点元数据

  数据节点的元数据默认存储在控制节点服务器的 */DolphinDB/server/clusterDemo/data/ 数据节点别名 /stroage/ CHUNK_METADATA* 目录下，接下来以 **P1** 服务器为例演示如何备份数据节点元数据，数据节点元数据的默认存储目录：

  ```
  /DolphinDB/server/clusterDemo/data/P1-datanode/stroage/CHUNK_METADATA
  ```

  登录服务器 **P1** ，可进入上述目录执行以下 Shell 指令备份到上面创建的 *backup* 文件夹：

  ```
  cp -r CHUNK_METADATA ../../backup
  ```

  > 注意：元数据文件可能通过配置文件指定存储在其它目录，如果在默认路径没有找到上述文件，可以通过查询配置文件中的 *dfsMetaDir* 参数和 *chunkMetaDir* 参数确认元数据文件的存储目录。若配置中未指定 *dfsMetaDir* 参数和 *chunkMetaDir* 参数，但是配置了 *volumes* 参数，*CHUNK_METADATA* 目录在相应的 *volumes* 参数指定的目录下。
  >

  **第三步：升级**
  > 注意：
  >
  > 当 server 升级到某个版本后，使用的插件也应升级到与此对应的版本。
  
- 在线升级

  登录服务器 **P1、P2 和 P3**，进入 */DolphinDB/server/clusterDemo* 目录执行以下 Shell 指令：

  ```
  ./upgrade.sh
  ```

  运行后将会出现如下提示：

  <img src="./images/multi_machine_cluster_deployment/3_1.png" width=60%>

  输入 y 并点击回车后会出现如下提示：

  <img src="./images/multi_machine_cluster_deployment/3_2.png" width=80%>

  输入 1 选择在线更新，并点击回车后会出现如下提示：

  <img src="./images/multi_machine_cluster_deployment/3_3.png" width=80%>

  输入所需更新的版本号再点击回车即可，以更新至 2.00.9.1 版本为例，输入 2.00.9.1 后点击回车，出现如下界面则表示升级成功：

  <img src="./images/multi_machine_cluster_deployment/3_4.png" width=80%>

- 离线升级

  下载升级所需版本的安装包，官方下载地址：[http://www.dolphindb.cn/downloads.html](https://dolphindb.cn/product#downloads)

  将下载好的安装包上传至 **P1** 、 **P2** 和 **P3** 的 */DolphinDB/server/clusterDemo* 目录下，以更新至 2.00.9.1 版本为例：

  <img src="./images/multi_machine_cluster_deployment/3_5.png" width=50%>

  登录 **P1** 、 **P2** 和 **P3** ，进入 */DolphinDB/server/clusterDemo* 目录执行以下 Shell 指令：

  ```
  ./upgrade.sh
  ```

  运行后将会出现如下提示：

  <img src="./images/multi_machine_cluster_deployment/3_6.png" width=60%>

  输入 y 并点击回车后会出现如下提示：

  <img src="./images/multi_machine_cluster_deployment/3_7.png" width=80%>

  输入 2 选择离线更新，并点击回车后会出现如下提示：

  <img src="./images/multi_machine_cluster_deployment/3_8.png" width=80%>

  输入所需更新的版本号再点击回车即可，以更新至 2.00.9.1 版本为例，输入 2.00.9.1 后点击回车，出现如下界面则表示升级成功：

  <img src="./images/multi_machine_cluster_deployment/3_9.png" width=80%>

  **第四步：重新启动集群**

- 启动控制节点

  在服务器 **P1** 的 */DolphinDB/server/clusterDemo* 目录执行以下 Shell 指令启动控制节点：

  ```
  sh startController.sh
  ```

  > 注意：本教程示例集群的控制节点部署在服务器 P1，所以只需要在服务器 P1 启动控制节点。
  >

- 启动代理节点

  在服务器 **P1, P2 和 P3** 的 */DolphinDB/server/clusterDemo* 目录执行以下 Shell 指令启动代理节点：

  ```
  sh startagent.sh
  ```

- 启动数据节点和计算节点

  在浏览器中输入控制节点的 IP 地址和端口号即可进入 Web 管理界面，教程中的部署控制节点的服务器 IP 地址为 10.0.0.80，部署端口为 8900，所以访问地址为 10.0.0.80:8900，打开后的 Web 管理界面如下。以管理员身份（默认账号：admin，默认密码：123456）登录 Web 管理界面后，用户可以通过勾选想要启动的数据节点和计算节点，再点击启动（关闭）按键即可启动（关闭）相应的数据节点和计算节点：

  <img src="./images/multi_machine_cluster_deployment/3_10.png" width=80%>

  刷新页面后可看到对应的数据节点和计算节点已启动，如下图所示：

  <img src="./images/multi_machine_cluster_deployment/3_11.png" width=80%>

  成功启动后，打开 Web 管理界面，在交互编程界面执行以下代码，查看 DolphinDB 当前版本：

  ```
  version()
  ```

## 4. 授权许可文件过期更新

  在更新授权许可文件前，可以打开 Web 管理界面，在任一节点交互编程界面执行以下代码查看当前授权许可文件的到期时间：

  ```
  use ops
  getAllLicenses()
  ```

  <img src="./images/multi_machine_cluster_deployment/4_1.png" width=40%>

  在更新授权许可文件后，可通过对比更新前后授权许可文件的到期时间确认是否更新成功

  **第一步：替换授权许可文件**

  登录服务器 **P1、P2 和 P3** ，用新的授权许可文件 *dolphindb.lic* 替换老的授权许可文件。

  Linux 环境授权许可文件位置：

  ```
  /DolphinDB/server/dolphindb.lic
  ```

  **第二步：更新授权许可文件**

- 在线更新

  打开 Web 管理界面，在任一节点交互编程界面执行以下代码完成更新，代码成功运行会返回新授权许可证的到期时间：
  
  ```
  use ops
  updateAllLicenses()
  ```

  <img src="./images/multi_machine_cluster_deployment/4_2.png" width=40%>

  > 注意，在线更新有如下要求：
  >
  > （1）License 授权的客户名称必须与原来的 License 相同。
  >
  > （2）授权的节点个数，内存大小，CPU 核个数不能比原来的小。
  >
  > （3）该函数只在执行该函数的节点生效。因此在集群环境下，需要在所有控制节点，代理节点、计算节点和数据节点上运行该函数。
  >
  > （4）License 的类型必须是 commercial（付费）类型和 free 类型，如果是 trial（试用）类型不支持在线更新。
  >

- 离线更新

  关闭每台服务器上的 DolphinDB 节点，然后重新启动，即可完成更新。

## 5. 常见问题解答（FAQ）

### 5.1 节点启动失败的可能原因

- **端口号被占用**

  如果遇到无法启动 DolphinDB 节点的情况，建议打开 */DolphinDB/server/clusterDemo/log* 目录下相应节点的日志文件，若出现如下错误：

  ```
  <ERROR> :Failed to bind the socket on port 8900 with error code 98
  ```

  说明该节点选用的端口被其他程序占用，导致 DolphinDB 无法正常启动，修改配置文件中对应节点的端口为其它空闲端口后即可正常启动。

- **集群成员配置文件** ***cluster.nodes*** **第一行为空行**

  如果遇到无法启动 DolphinDB 节点的情况，建议打开 */DolphinDB/server/clusterDemo/log* 目录下相应节点的日志文件，若出现如下错误：

  ```
  <ERROR> :Failed to bind the socket on port 8900 with error code 98
  ```

  说明控制节点的 *cluster.nodes* 的第一行为空行，这种情况下只需将文件中的空行删除，再重新启动节点即可。

- **宏变量 `<ALIAS>` 在明确节点的情况下使用无效**

  查看控制节点下的配置文件 *cluster.cfg*，若在明确了节点的情况下使用宏变量 `<ALIAS>`，如：P1-datanode.persistenceDir = /hdd/hdd1/streamCache/\<ALIAS> ：

  ```
  P1-datanode.persistenceDir = /hdd/hdd1/streamCache/<ALIAS>
  ```

  则会导致该节点无法正常启动。这种情况下只需要把 `<ALIAS>` 删除，替换成特定节点即可，如：

  ```
  P1-datanode.persistenceDir = /hdd/hdd1/streamCache/P1-datanode
  ```

  若想对所有节点使用宏变量，则做如下修改：

  ```
  persistenceDir = /hdd/hdd1/streamCache/<ALIAS>
  ```

### 5.2 如何通过 systemd 命令启动 DolphinDB 集群？

  首先在每台服务器的 *DolphinDB/server/clusterDemo* 目录中创建脚本文件 *controller.sh* 以及 *agent.sh*，其 Shell 创建命令及写入内容如下：

  ```
  vim ./controller.sh
  ```

  ```java
  #!/bin/bash
  #controller.sh
  workDir=$PWD

  start(){
      cd ${workDir} && export LD_LIBRARY_PATH=$(dirname "$workDir"):$LD_LIBRARY_PATH
      nohup ./../dolphindb -console 0 -mode controller -home data -script dolphindb.dos -config config/controller.cfg -logFile log/controller.log -nodesFile config/cluster.nodes -clusterConfig config/cluster.cfg > controller.nohup 2>&1 &
  }

  stop(){
      ps -o ruser=userForLongName -e -o pid,ppid,c,time,cmd |grep dolphindb|grep -v grep|grep $USER|grep controller| awk '{print $2}'| xargs kill -TERM
  }

  case $1 in
      start)
          start
          ;;
      stop)
          stop
          ;;
      restart)
          stop
          start
          ;;
  esac
  ```

  ```
  vim ./agent.sh
  ```

  ```java
  #!/bin/bash
  #agent.sh


  workDir=$PWD

  start(){
      cd ${workDir} && export LD_LIBRARY_PATH=$(dirname "$workDir"):$LD_LIBRARY_PATH
      nohup ./../dolphindb -console 0 -mode agent -home data -script dolphindb.dos -config config/agent.cfg -logFile log/agent.log  > agent.nohup 2>&1 &
  }

  stop(){
      ps -o ruser=userForLongName -e -o pid,ppid,c,time,cmd |grep dolphindb|grep -v grep|grep $USER|grep agent| awk '{print $2}'| xargs kill -TERM
  }

  case $1 in
      start)
          start
          ;;
      stop)
          stop
          ;;
      restart)
          stop
          start
          ;;
  esac
  ```

  然后，执行以下 Shell 命令配置 controller 的守护进程：

  ```
  vim /usr/lib/systemd/system/ddbcontroller.service
  ```

  配置如下内容：

  ```java
  [Unit]
  Description=ddbcontroller
  Documentation=https://www.dolphindb.com/

  [Service]
  Type=forking
  WorkingDirectory=/home/DolphinDB/server/clusterDemo
  ExecStart=/bin/sh controller.sh start
  ExecStop=/bin/sh controller.sh stop
  ExecReload=/bin/sh controller.sh restart
  Restart=always
  RestartSec=10s
  LimitNOFILE=infinity
  LimitNPROC=infinity
  LimitCORE=infinity

  [Install]
  WantedBy=multi-user.target
  ```

  > 注意：
  >
  > 配置中 *WorkingDirectory* 需要修改为 */DolphinDB/server/clusterDemo*
  >

  执行以下 Shell 命令配置 agent 的守护进程：

  ```
  vim /usr/lib/systemd/system/ddbagent.service
  ```

  配置如下内容：

  ```java
  [Unit]
  Description=ddbagent
  Documentation=https://www.dolphindb.com/

  [Service]
  Type=forking
  WorkingDirectory=/home/DolphinDB/server/clusterDemo
  ExecStart=/bin/sh agent.sh start
  ExecStop=/bin/sh agent.sh stop
  ExecReload=/bin/sh agent.sh restart
  Restart=always
  RestartSec=10s
  LimitNOFILE=infinity
  LimitNPROC=infinity
  LimitCORE=infinity

  [Install]
  WantedBy=multi-user.target
  ```

  > 注意：
  >
  > 配置中 *WorkingDirectory* 需要修改为 */DolphinDB/server/clusterDemo*
  >

  最后，执行以下 Shell 命令启动 controller：

  ```
  systemctl enable ddbcontroller.service   #配置自启
  systemctl start ddbcontroller.service  #启动
  systemctl stop  ddbcontroller.service   #停止服务
  systemctl status  ddbcontroller.service  #检测状态
  ```

  执行以下 Shell 命令启动 agent：

  ```
  systemctl enable ddbagent.service   #配置自启
  systemctl start ddbagent.service  #启动
  systemctl stop  ddbagent.service   #停止服务
  systemctl status  ddbagent.service  #检测状态
  ```

### 5.3 Web 管理界面无法访问怎么办？

  DolphinDB 正常启动后，在浏览器输入控制节点正确的访问地址，但 Web 管理界面无法正常打开，如下图所示：

  <img src="./images/multi_machine_cluster_deployment/5_1.png" width=40%>

  出现上述问题的原因通常是由于浏览器与 DolphinDB 不是部署在同一台服务器，且部署 DolphinDB 的服务器开启了防火墙。可以通过关闭部署了 DolphinDB 的服务器的防火墙或者打开对应的部署端口，解决这个问题。

### 5.4 Linux 升级失败如何版本回退？

  如果升级以后，不能正常开启 DolphinDB 集群，可按以下方式回退到旧版本。

  **第一步：恢复旧版本元数据文件**

- 恢复控制节点元数据

  登录控制节点的服务器，在 */DolphinDB/server/clusterDemo/dfsMeta* 目录执行以下 Shell 指令恢复已备份的控制节点元数据：

  ```
  cp -r backup/DFSMetaLog.0 ./
  cp -r backup/DFSMasterMetaCheckpoint.0 ./
  ```

- 恢复数据节点元数据

  登录数据节点的服务器（以 **P1** 为例），在 */DolphinDB/server/clusterDemo/data* 目录执行以下 Shell 指令恢复已备份的数据节点元数据：

  ```
  cp -r backup/CHUNK_METADATA ./P1-datanode/storage
  ```

  **第二步：恢复旧版本程序文件**

  在官方下载旧版本程序包，把重新下载的旧版本 *server* 目录下除 *dolphindb.cfg*,  *clusterDemo* 以及 *dolphindb.lic* 外的所有文件覆盖替换升级失败的文件。

### 5.5 为什么在线更新授权许可文件失败？

  在线更新授权文件需要满足[更新授权许可文件](#4-授权许可文件过期更新)中在线更新的要求。如果不满足其中的要求，可以通过离线方式进行更新，或[申请企业版 License](https://dolphindb.cn/product#downloads)。

### 5.6 为什么云部署节点无法启动？

  DolphinDB 集群既可以部署在局域网内，也可以部署在私有云或公有云上。DolphinDB 默认集群的所有节点在一个局域网内（*lanCluster*=1）并通过 UDP 广播来监测节点心跳。但是在云平台上，所有节点不一定位于一个局域网，也有可能不支持 UDP。所以，在云平台上，需要在 *controller.cfg* 和 *agent.cfg* 填入 lanCluster=0 来实现非 UDP 模式的节点之间的通讯。否则，由于可能无法正常检测到节点的心跳，集群可能无法正常工作。

### 5.7 如何进行配置参数调优？

  可以参考 DolphinDB 官方参数配置说明进行配置参数调优：[参数配置](https://docs.dolphindb.cn/zh/db_distr_comp/cfg/para_cfg.html)

  如果遇到性能问题，请添加微信号 13306510479（仅用于添加微信）或扫描下面二维码，客服会邀您进群，由 DolphinDB 的技术支持工程师会解答您的问题。

  <img src="./images/multi_machine_cluster_deployment/5_2.png" width=40%>

### 5.8 如何设置数据卷？

  数据卷是位于数据节点上的文件夹，用来保存分布式文件系统的数据。一个数据节点可以有多个数据卷。要确保最优性能，每个数据卷应当对应不同的物理设备。如果多个数据卷对应同一个物理设备，会影响性能。

  可在 *cluster.cfg* 中设置数据卷的路径。如果用户不设置数据卷的路径，系统会默认按数据节点别名来设置数据卷的路径。若节点别名为 P1-datanode，系统会自动在该节点的 */DophinDB/server/clusterDemo/data* 目录下创建一个名为 *P1-datanode* 的子目录来存储数据。注意：数据卷只支持绝对路径，不支持相对路径。

  > 注意：在 linux 环境部署时，*volumes* 配置目录建议不要指定用 NAS 挂载服务器路径的远程磁盘，如果这样配置，数据库性能会因为磁盘 IO 瓶颈变差。如果非要这样配置，如果您的分区挂载用的是 NFS 协议，则该 datanode（数据节点）进程必须以 root 身份启动。因为普通用户启动的数据库进程无权限在 NAS 读写磁盘，如果用 sudo 用户启动，会造成文件夹权限混乱。
  >

  三种设置数据卷路径的方法：

- **对每个数据节点分别指定数据卷路径**

  ```
  P1-datanode.volumes=/DFS/P1-datanode
  P2-datanode.volumes=/DFS/P2-datanode
  ```

- **通过 % 和 ? 通配符**

  `？` 代表单个字符；`％` 表示 0，1 或多个字符。

  将所有以 "-datanode" 为结尾的节点的数据存放到 */VOL1*：

  ```
  %-datanode.volumes=/VOL1
  ```

  等同于：

  ```
  P1-datanode.volumes=/VOL1
  P2-datanode.volumes=/VOL1
  ```

- **通过 ALIAS 通配符**

  若所有数据节点的数据卷路径都含有节点别名，可使用 来配置数据卷路径。可用以下代码为每台服务器配置两个物理卷 */VOL1* 和 */VOL2*：

  ```
  volumes=/VOL1/<ALIAS>,/VOL2/<ALIAS>
  ```

  等同于：

  ```
  P1-datanode.volumes=/VOL1/P1-datanode,/VOL2/P1-datanode
  P2-datanode.volumes=/VOL1/P2-datanode,/VOL2/P2-datanode
  ```

## 6. 参考

更多详细信息，请参阅 DolphinDB 用户手册：

- [中文版 DolphinDB 用户手册](https://docs.dolphindb.cn/zh/index.html)
- [英文版 DolphinDB 用户手册](https://docs.dolphindb.com/en/index.html)
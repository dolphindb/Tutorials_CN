##  基于Docker的集群部署教程

Docker是一个开源的引擎，可以轻松的为任何应用创建一个轻量级的、可移植的、自给自足的容器。DolphinDB database提供了基于docker的分布式集群部署包，可以让用户方便快捷的部署DolphinDB分布式集群。DolphinDB服务器可部署在云端服务器上，云边端使用同一数据库，能更好地实现互相协同，云边端一体化。

本文的目标是通过4个centos容器搭建一个5节点的多机集群，最终搭建好的集群情况如下:

```
           => agent1 => 2 datanodes
controller => agent2 => 2 datanodes
           => agent3 => 1 datanode
```

由于免费社区版license文件无法支持5个数据节点和1个控制器节点，请申请支持6个以上节点的企业版license，并将企业版 license 文件 dolphindb.lic 放到 ./cfg 文件目录下。

部署分布式集群时，需要分别配置控制器节点(controller)，代理节点(agent)， 和数据节点(datanode)的网络IP和端口。在本文提供的部署包里，
通过docker容器间构建虚拟子网，为4个容器分别指定了从 10.5.0.2 到 10.5.0.5 4个固定IP地址。包含这些信息的配置文件已内置到部署包中，用户无需再手工一一配置。

内置的网络IP及端口分配情况如下:

controller的配置文件
```bash
$ cat controller.cfg
$ localSite=10.5.0.5:8888:master
...
```
agent配置文件，以agent1为例：
```bash
$ cat agent1.cfg
$ mode=agent
$ localSite=10.5.0.2:8710:P1-agent,agent
$ controllerSite=10.5.0.5:8888:master
```

节点配置文件

```bash
$ cat cluster.nodes
localSite,mode
10.5.0.2:8710:P1-agent,agent
10.5.0.2:8711:P1-node1,datanode
10.5.0.2:8712:P1-node2,datanode
10.5.0.3:8810:P2-agent,agent
10.5.0.3:8811:P2-node1,datanode
10.5.0.3:8812:P2-node2,datanode
10.5.0.4:8910:P3-agent,agent
10.5.0.4:8911:P3-node1,datanode
```

由于在docker虚拟网络环境中UDP协议无法正常工作，所以需要在agent.cfg和cluster.cfg文件中加上配置项lanCluster=0，此配置项在部署包内的配置文件中已默认添加。

在做部署集群之前，需要先搭建好docker环境，可以参考: [docker 安装教程](https://docs.docker.com/install/), [docker-compose 安装教程](https://docs.docker.com/compose/install/#install-compose) 搭建本文所需环境。

按照文档安装好docker后，在Linux命令行窗口执行以下命令可以返回docker版本号。

```bash
$ docker -v
$ docker-compose --version
```

准备好环境之后，下面我们可以开始部署分布式集群。

#### 1. 下载并编译 DophinDB docker集群部署包

(1) 下载DolphinDB docker集群部署包
  在Github可以[下载dolphindb docker部署包](../docker/DolphinDB-Docker-Compose.zip)

(2) 生成DophinDB server 镜像文件

解压后修改包中Dockerbuild/DockerFile文件中的dolphindb_version参数，可以在build时更新到指定的DophinDB server版本。现行发布版本请从 [Release Notes](../release) 查询

示例如下：
```
ARG dolphindb_version = "DolphinDB_Linux64_V1.00.10.zip" 
```

通过下述步骤我们可以得到内置 DophinDB server 的镜像文件。
```bash
cd ./DolphinDB-Docker-Compose/Dockerbuild
docker build -t ddb:latest ./
```

编译完成后，执行 docker images 命令：
```bash
$ docker images
REPOSITORY   TAG     IMAGE ID       CREATED         SIZE
ddb          latest  4268ac618977   5 seconds ago   420MB
```

#### 2. 通过如下脚本，创建controller和agent所需容器，并启动容器。

通过如下步骤我们可以启动容器中的默认启动脚本会自动启动控制器节点(controller)和代理节点(agent)。
```bash
cd ./DolphinDB-Docker-Compose
docker-compose up -d
```
执行后输出结果如下：

```bash
$ docker-compose up -d
Creating network "20190121-dolphindb-docker-compose_dbnet" with driver "bridge"
Creating ddbcontroller ... done
Creating ddbagent2     ... done
Creating ddbagent3     ... done
Creating ddbagent1     ... done

```

#### 3. 查看集群

  通过上述步骤，已经完成了分布式集群的创建，启动和初始化工作，这里包含了一个controller容器和三个agent容器。 访问地址 http://localhost:8888/ 就可以访问集群管理web页面, 在集群管理界面全选并启动数据节点，最终界面如下：

  ![image](../images/docker/cluster_web.png?raw=true)


#### 4. 自定义docker集群

如果需要对集群环境做一些自定义，请参考下表的信息修改对应的配置文件内容
* 修改docker网络端口及IP配置，需修改`docker-compose.yml`文件，这里包含集群所有docker容器的配置及其启动参数。
* 由于免费社区版license文件无法支持5个数据节点和1个控制器节点，请申请支持6个以上节点的企业版license，并将企业版 license 文件 dolphindb.lic 放到 ./cfg 文件目录下。
* 需要自定义dolphindb集群本身的配置，修改 ./cfg/目录下各配置文件，简要介绍如下表，具体信息请参考[集群配置](https://www.dolphindb.cn/cn/help/DatabaseandDistributedComputing/Configuration/ClusterMode.html)

文件名|简介|
  ---|---|
controller.cfg|集群控制器的配置参数|
cluster.nodes|配置所有代理节点和数据节点的位置|
cluster.cfg|集群数据节点的配置参数|
agent1.cfg|代理节点1配置参数|
agent2.cfg|代理节点2配置参数|
agent3.cfg|代理节点3配置参数|
dolphindb.lic | 集群所有节点的企业版授权文件

* 若需要新增容器及配置对应节点，需要修改如下几处
  * 参照 docker-compose.yml文件，增加容器ddbagentx, 容器配置信息可以参考其他agent的配置，在port和ip这里需要与其他容器错开，避免冲突。
  * 需要修改 ./cfg/cluster.nodes 增加新的agent和datanode信息
  * 增加一个./cfg/agentx.cfg与docker-compose.yml中volumes映射的代理节点配置文件相对应。

#### 5. 如何升级版本

* 下载最新的server安装包，解压后，将server目录下dolphindb.lic文件删除
* 用docker cp命令拷贝server目录覆盖每个docker容器的 /data/ddb/server目录。
* 重启docker容器。

#### 6. 常见问题
* 一些docker镜像中不包含tzdata包，比如ubuntu:latest，导致dolphindb启动报如下错误：
```
Can't find time zone database. Please use parameter tzdb to set the root directory of time zone database.
```
安装 tzdata包可以解决此问题，运行如下命令：
```
apt-get install tzdata
```

* docker中获取机器指纹失败
  

正式license需要校验服务器硬件信息，而docker中没有权限获取此信息，启动时日志中会报告异常：

```
<ERROR> : Failed to retrieve machine fingerprint
```
解决方法：映射宿主机/etc/到docker容器的/dolphindb/etc目录。docker run 添加如下启动参数：

```
-v /etc:/dolphindb/etc 
```

* docker启动后发现容器处于exit(1)状态，通过docker logs去查看容器信息报错
```
<ERROR> : standard_init_linux.go:219: exec user process caused: no such file or directory
```
解决方法：在Dockerbuild目录中的文件default_cmd 通过set ff查看，若得出fileformat=dos 请修改 set ff=unix

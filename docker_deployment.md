####  用 docker 部署 DolphinDB分布式集群

Docker是一个开源的引擎，可以轻松的为任何应用创建一个轻量级的、可移植的、自给自足的容器。DolphinDB提供了基于docker的分布式集群部署包，可以让用户方便快捷的部署DolphinDB分布式集群。

本文的目标是通过4个centos容器搭建一个5节点的多机集群，最终搭建好的集群情况如下

```
controller => agent1 => 2 datanodes
           => agent2 => 2 datanodes
           => agent3 => 1 datanode
```

部署分布式集群时，需要分别配置控制器节点(controller)，代理节点(agent)， 和数据节点(datanode)的网络IP和端口。在本文提供的部署包里，
通过docker容器间构建虚拟子网，为4个容器分别指定了从`10.5.0.2`到`10.5.0.5` 4个固定ip地址， 包含这些信息的配置文件已内置到部署包中，用户无需再手工一一配置。
内置的网络IP及端口分配情况如下

controller的配置文件
```bash
$ cat controller.cfg
localSite=10.5.0.5:8888:master
...
```
agent配置文件，以agent1为例：
```bash
$ cat agent1.cfg
mode=agent
localSite=10.5.0.2:8710:P1-agent,agent
controllerSite=10.5.0.5:8888:master
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

按照文档安装好docker，直到在linux命令行窗口执行`docker -v`命令能返回正确的docker版本号。

```bash
$ docker -v
$ docker-compose --version
```

准备好环境之后，下面我们可以开始部署分布式集群。

#### 一、 下载并编译 dolphindb docker集群部署包

  在github可以[下载dolphindb docker部署包](https://github.com/dolphindb/Tutorials_CN/blob/master/docker/DolphinDB-Docker-Compose.zip)
* 编译dophindb server 镜像文件

通过下述步骤我们可以得到一个包含最新 dolphindb server 的镜像文件。
```bash
cd ./DolphinDB-Docker-Compose/Dockerbuild
docker build -t ddb:latest ./
```
编译完成后，用docker images 查看如下
```console
$ docker images
REPOSITORY  TAG IMAGE ID  CREATED SIZE
ddb latest  4268ac618977  5 seconds ago 420MB
```

#### 2. 替换部署包license文件
公开的社区版license文件无法支持5个数据节点和1个控制器节点，所以需要申请支持6个以上节点的企业版license。
将企业版 license 文件` dolphindb.lic `放到 `./cfg` 文件目录下。

#### 3. 通过如下脚本，创建controller和agent所需容器，并启动容器。
容器中的默认启动脚本会自动启动控制器节点(Controller)和代理节点(Agent)。
```bash
cd ./DolphinDB-Docker-Compose
sudo apt install docker-compose
docker-compose up -d
```
执行后输出结果如下：

```console
$ docker-compose up -d
Creating network "20190121-dolphindb-docker-compose_dbnet" with driver "bridge"
Creating ddbcontroller ... done
Creating ddbagent2     ... done
Creating ddbagent3     ... done
Creating ddbagent1     ... done

```

#### 4. 查看集群

  通过上述步骤，已经完成了分布式集群的创建，启动和初始化工作，这里包含了一个controller容器和三个Agent容器。 访问地址 http://localhost:8888/ 就可以访问集群管理web页面, 在集群管理界面全选并启动数据节点，最终界面如下：

  ![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/docker/cluster_web.png?raw=true)
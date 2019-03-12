## DolphinDB安装使用指南

DolphinDB系统包括：服务器程序包、图形用户界面GUI、网络集群管理器、Java/Python/C# API以及各种插件。

### 一、安装系统

#### 1、下载地址: 

https://www.dolphindb.cn/alone/alone.php?id=10

#### 2、海豚大数据社区试用版（必须）

解压DolphinDB压缩包，里面包含了web集群管理工具、服务端程序以及license文件。解压完成后不需要进一步安装。如需安装企业试用版，点击“试用”申请license，若已收到我们提供的license文件，无需再申请。

#### 3、图形用户界面GUI（推荐）

GUI提供了DolphinDB的集成开发环境。支持关键字着色，自动提示，数据可视化，数据浏览等功能。GUI使用环境需要Java 8及以上版本。
* Windows下启动：双击gui.bat
* Linux下启动：sh gui.sh

#### 4、Python/Java/C# API（可选）

DolphinDB提供Java，Python和C#的开发接口。安装步骤及使用请参考用户手册https://www.dolphindb.cn/cn/help/Chapter12ProgrammingAPIs.html

### 二、配置集群

完成以上系统安装后，即可搭建单机集群或多机集群。

#### 1、独立服务器

作为一个独立的工作站或服务器使用，无需配置。详见教程
https://github.com/dolphindb/Tutorials_CN/blob/master/standalone_server.md 

#### 2、单机集群搭建

控制节点(controller)、代理节点（agent）、数据节点(data node)部署在同一个物理机器上。详见教程 
https://github.com/dolphindb/Tutorials_CN/blob/master/single_machine_cluster_deploy.md

#### 3、多机集群搭建
在多个物理机器上部署DolphinDB集群。详见教程
https://github.com/dolphindb/Tutorials_CN/blob/master/multi_machine_cluster_deploy.md

### 三、使用系统

1. 使用网络集群管理器可以配置集群、启动或关闭数据节点、查看集群各节点的性能指标、浏览分布式数据库数据分区情况及详细数据。详见上文中的单机和多机集群部署教程。

2. 客户端GUI提供了方便开发DolphinDB脚本的图形界面。详见GUI帮助文档http://www.dolphindb.com/cn/gui_help/

3. 在DolphinDB中创建分区数据库和表。DolphinDB支持顺序、值、列表、区间以及复合分区，可灵活应对各类企业实际业务场景。详见教程

https://github.com/dolphindb/Tutorials_CN/blob/master/database.md

### 四、用户权限设置

DolphinDB提供了完善、安全的权限管理机制，满足企业的各种应用需要，详见教程 
https://github.com/dolphindb/Tutorials_CN/blob/master/ACL_and_Security.md

### 五、常见错误原因
1. 节点启动后立即退出，在log文件中显示错误原因为"The license has expired"。

原因：license过期。

解决方案：联系智臾科技技术支持support@dolphindb.com，更新license文件dolphindb.lic。

2. 集群管理器上启动节点后，节点仍然显示未启动状态。

原因：需要手动刷新集群节点状态。

解决方案：点击集群管理器上刷新按钮。

在使用过程中遇到各种问题，可以查看log文件获取问题信息。每个数据节点和控制节点都有独立的log文件，有系统详细的运行日志，默认在home目录下。也可联系 support@dolphindb.com或致电0571-82853925。


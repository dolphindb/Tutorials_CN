# DolphinDB安装使用指南

DolphinDB系统包括：服务器程序 dolphindb、web 集群管理工具、图形化开发工具 GUI、Java/Python/C# API 以及各种插件。

DolphinDB 提供了全套的中英文使用手册及教程：
- 中文使用手册：https://dolphindb.cn/cn/help/index.html 
- 中文教程系列：https://github.com/dolphindb/Tutorials_CN 

    若无法打开，可使用国内镜像:https://gitee.com/dolphindb/Tutorials_CN 
- 英文使用手册：http://dolphindb.com/help/index.html
- 英文教程系列：https://github.com/dolphindb/Tutorials_EN

DolphinDB 技术问答社区：
- 思否SegmentFault: https://segmentfault.com/t/dolphindb
- StackOverflow: https://stackoverflow.com/questions/tagged/dolphindb
- DolphinDB问答社区：https://ask.dolphindb.net/

## 1. 安装系统

### 1.1 下载地址: 

https://www.dolphindb.cn/downloads.html

### 1.2 DolphinDB社区试用版（必须）

解压 DolphinDB 压缩包，其中含有 web 集群管理工具、服务端程序以及license 文件。解压完成后不需要进一步安装。如需企业试用版，点击“试用”申请 license。待我方与您联系后，您会收到企业试用版 license 文件，若license文件名不是dolphindb.lic，需要将其改名为dolphindb.lic，并将其替换社区版中的同名文件即可使用企业试用版。

### 1.3 图形用户界面GUI（推荐）

GUI是DolphinDB的集成开发环境。支持内置函数、语法高亮、自动提示、数据可视化与数据浏览等功能，推荐在数据开发或数据分析场景下使用。GUI使用环境需要Java 8及以上版本。
请从官网下载页面的`其它资源下载`列表第一个链接获取GUI的安装包。 GUI无需安装，解压即可。
* Windows下启动：双击gui.bat
* Linux下启动：sh gui.sh

DolphinDB也支持使用 VS Code 插件等客户端来连接DolphinDB、编辑脚本。关于GUI、VS Code 插件等客户端的更多细节，请参阅[DolphinDB客户端教程][DolphinDB客户端教程]。

### 1.4 Python/Java/C# API（可选）

DolphinDB提供Java，Python和C#的开发接口。安装步骤及使用请参考[用户手册][用户手册]。

## 2. 配置

完成以上系统安装后，即可搭建单机集群或多机集群。

### 2.1 独立服务器（单节点模式）

作为一个独立的工作站或服务器使用，下载后即可使用，无需配置。详见[单节点部署教程][单节点部署教程]。

单节点模式拥有与集群模式相同的功能，区别在于单节点模式不支持扩展节点和高可用，而集群模式可以方便地扩展到多个服务器节点以及支持高可用。

### 2.2 单机集群搭建

控制节点(controller)、代理节点（agent)、数据节点(data node)部署在同一个物理机器上。详见[单服务器集群部署][单服务器集群部署]。

### 2.3 多机集群搭建

在多个物理机器上部署DolphinDB集群。详见[多服务器集群部署][多服务器集群部署]。

## 3. 使用系统

- 使用 web 集群管理工具可以启动关闭数据节点、查看集群各节点的性能指标、浏览分布式数据库整体数据分区情况及详细数据，详见上文中的单机和多机集群部署教程。

- 客户端GUI提供了方便开发DolphinDB脚本的图形界面。详见[GUI帮助文档][GUI帮助文档]。

- 在DolphinDB中创建分区数据库和表。DolphinDB支持顺序、值、列表、区间、哈希以及复合分区，可灵活应对各类企业实际业务场景，详见[分区数据库教程][分区数据库教程]。

- 使用DolphinDB流数据引擎进行实时数据处理与分析。详见[流数据教程][流数据教程]与[流数据时序聚合引擎教程][流数据时序聚合引擎教程]。

> 使用系统前建议先阅读：[量化金融范例][量化金融范例]或[物联网范例][物联网范例]。

## 4. 用户权限设置

DolphinDB提供了完善、安全的权限管理机制，适用于企业级的不同应用场景，详见[权限管理和安全教程][权限管理和安全教程]。

## 5. 常见错误原因

- 节点启动后立即退出，在log文件中显示错误原因为"The license has expired"。

原因：license过期。

解决方案：联系智臾科技技术支持support@dolphindb.com，更新license文件dolphindb.lic。

- 集群管理器上启动节点后，节点仍然显示未启动状态。

原因：需要手动刷新集群节点状态。

解决方案：点击集群管理器上刷新按钮。

在使用过程中如果遇到各种问题，可以查看log文件获取问题信息。每个数据节点和控制节点都有独立的log文件，默认在 home 目录下（例如单节点部署是server/dolphindb.log,集群部署是server/log/*.log），里面有系统详细的运行日志；也可以联系 support@dolphindb.com 或致电 0571-82853925。

[DolphinDB客户端教程]: ./client_tool_tutorial.md
[用户手册]: https://www.dolphindb.cn/cn/help/ProgrammingAPIs/ProgrammingAPIs.html
[单节点部署教程]: ./standalone_server.md
[单服务器集群部署]: single_machine_cluster_deploy.md
[多服务器集群部署]: ./multi_machine_cluster_deployment.md
[GUI帮助文档]: https://www.dolphindb.cn/cn/gui/
[分区数据库教程]: ./database.md
[流数据教程]: streaming_tutorial.md
[量化金融范例]: ./quant_finance_examples.md
[物联网范例]: ./iot_examples.md
[权限管理和安全教程]: ./ACL_and_Security.md


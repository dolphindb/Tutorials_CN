# DolphinDB 安装使用指南

DolphinDB 系统包括：服务器程序 dolphindb, web 集群管理工具、图形化开发工具 GUI, C++/Java/Python/C# API 以及各种插件。

DolphinDB 提供了全套的中英文使用手册及教程：
- 中文使用手册：[https://dolphindb.cn/cn/help/index.html ](https://docs.dolphindb.cn/zh/index.html)
- 中文教程系列：[https://github.com/dolphindb/Tutorials_CN ](https://github.com/dolphindb/Tutorials_CN)

若无法打开，可使用国内镜像：[https://gitee.com/dolphindb/Tutorials_CN](https://gitee.com/dolphindb/Tutorials_CN)

- 英文使用手册：[https://docs.dolphindb.com/en/index.html](https://docs.dolphindb.com/en/index.html)
- 英文教程系列：[https://github.com/dolphindb/Tutorials_EN](https://github.com/dolphindb/Tutorials_EN)

DolphinDB 技术问答社区：
- 思否 SegmentFault: https://segmentfault.com/t/dolphindb
- StackOverflow: https://stackoverflow.com/questions/tagged/dolphindb
- DolphinDB 问答社区：https://ask.dolphindb.net/

## 1. 安装系统

### 1.1 下载地址：

[https://dolphindb.cn/product#downloads](https://dolphindb.cn/product#downloads)

### 1.2 DolphinDB 社区试用版（必须）

解压 DolphinDB 压缩包，其中含有 web 集群管理工具、服务端程序以及 license 文件。解压完成后不需要进一步安装。如需企业试用版，点击“试用”申请 license。待我方与您联系后，您会收到企业试用版 license 文件，若 license 文件名不是 dolphindb.lic，需要将其改名为 dolphindb.lic，并将其替换社区版中的同名文件即可使用企业试用版。

### 1.3 DolphinDB VSCode 插件（推荐）

DolphinDB 公司开发了支持 DolphinDB 数据库编程语言的 VSCode 插件，便于用户使用 VSCode 编写 DolphinDB 脚本并在 DolphinDB 服务器上运行。VS Code 使用者无需安装其它软件，直接下载插件即可使用，学习成本低，上手快。因此，推荐用户选择使用 VS Code。有关 VSCode 插件的安装和使用，参考：[DolphinDB VSCode 插件用户手册](./vscode_extension.md)。

DolphinDB 也支持使用 DolphinDB GUI 客户端来连接 DolphinDB、编辑脚本。有关 DolphinDB GUI 的安装和使用，参考：[DolphinDB 客户端软件教程](./client_tool_tutorial.md)。

### 1.4 Python/Java/C# API（可选）

DolphinDB 提供 Java, Python 和 C# 的开发接口。安装步骤及使用请参考[用户手册](https://docs.dolphindb.cn/zh/api/connapi_intro.html)。

## 2. 配置

完成以上系统安装后，即可搭建单机集群或多机集群。

### 2.1 独立服务器（单节点模式）

作为一个独立的工作站或服务器使用，下载后即可使用，无需配置。详见[单节点部署教程](./standalone_server.md)。DolphinDB 支持嵌入式 ARM 环境。详见[ARM 版本单节点部署教程](./ARM_standalone_deploy.md)。

单节点模式拥有与集群模式相同的功能，区别在于单节点模式不支持扩展节点和高可用，而集群模式可以方便地扩展到多个服务器节点以及支持高可用。

### 2.2 单机集群搭建

控制节点（controller）、代理节点（agent）、数据节点（data node）、计算节点（compute node）部署在同一个物理机器上。详见[单服务器集群部署](./single_machine_cluster_deploy.md)。

### 2.3 多机集群搭建

在多个物理机器上部署 DolphinDB 集群。详见[多服务器集群部署](./multi_machine_cluster_deployment.md)。

DolphinDB 提供数据、元数据以及客户端的高可用方案，使得数据库节点发生故障时，数据库依然可以正常运作，保证业务不会中断。详见[高可用集群部署](./ha_cluster_deployment.md)。

### 2.4 功能及应用场景

| **功能**                                       | **单节点** | **单机集群** | **多服务器集群** |
| :----------------------------------------: | :---------: | :--------: | :----------: |
| [多模存储引擎](https://docs.dolphindb.cn/zh/db_distr_comp/db/multimodal_storage.html) |:white_check_mark:  | :white_check_mark:|:white_check_mark:  |
| [支持事务](https://docs.dolphindb.cn/zh/db_distr_comp/db/transaction.html) | :white_check_mark: | :white_check_mark: |:white_check_mark:  |
| [分布式计算](https://docs.dolphindb.cn/zh/tutorials/general_computing.html) | :white_check_mark: | :white_check_mark:|:white_check_mark:  |
| [多范式编程](https://docs.dolphindb.cn/zh/tutorials/hybrid_programming_paradigms.html) | :white_check_mark: | :white_check_mark: |:white_check_mark:  |
| [实时流数据](https://docs.dolphindb.cn/zh/tutorials/streaming_tutorial.html) | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| 系统管理及接口                                  | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| 云上部署                                     | :white_check_mark:         | :white_check_mark: | :white_check_mark: |
| 扩展节点                                     | :x:         | :white_check_mark: | :white_check_mark:  |
| 数据高可用（多副本）                               | :x:         | :white_check_mark: | :white_check_mark: |
| 应用高可用                                    | :x:         | :x:        | :white_check_mark: |

| **应用场景**    | **单节点** | **单机集群** | **多服务器集群** |
| ------- | --------- | -------- | ---------- |
| 开发      | :white_check_mark:         | :white_check_mark:        | :white_check_mark:          |
| 研究      | :white_check_mark:         | :white_check_mark:        | :white_check_mark:          |
| 小规模生产环境 | :white_check_mark:         | :white_check_mark:        | :white_check_mark:          |
| 可扩展     | :x:         | :white_check_mark:        | :white_check_mark:          |
| 企业级生产环境 | :x:         | :x:        | :white_check_mark:          |

## 3. 使用系统

- 使用 web 集群管理工具可以启动关闭数据节点、查看集群各节点的性能指标、浏览分布式数据库整体数据分区情况及详细数据，详见上文中的单机和多机集群部署教程。

- 客户端 GUI 提供了方便开发 DolphinDB 脚本的图形界面。详见[GUI 帮助文档](https://docs.dolphindb.cn/zh/db_distr_comp/gui.html)。

- 在 DolphinDB 中创建分区数据库和表。DolphinDB 支持范围、哈希、值、列表、以及组合分区，可灵活应对各类企业实际业务场景，详见[分区数据库教程](./database.md)。

- 使用 DolphinDB 流数据引擎进行实时数据处理与分析。详见[流数据教程](streaming_tutorial.md)与[流数据时序聚合引擎教程](./stream_aggregator.md)。

> 使用系统前建议先阅读：[量化金融范例](./quant_finance_examples.md)或[物联网范例](./iot_examples.md)。

## 4. 用户权限设置

DolphinDB 提供了完善、安全的权限管理机制，适用于企业级的不同应用场景，详见[权限管理和安全教程](./ACL_and_Security.md)。

## 5. 常见错误原因

- 节点启动后立即退出，在 log 文件中显示错误原因为"The license has expired"。

    原因：license 过期。

    解决方案：联系智臾科技技术支持 support@dolphindb.com，更新 license 文件 dolphindb.lic。

- 集群管理器上启动节点后，节点仍然显示未启动状态。

    原因：需要手动刷新集群节点状态。

    解决方案：点击集群管理器上刷新按钮。

    在使用过程中如果遇到各种问题，可以查看 log 文件获取问题信息。每个数据节点和控制节点都有独立的 log 文件，默认在 home 目录下（例如单节点部署是 server/dolphindb.log，集群部署是 server/log/*.log），里面有系统详细的运行日志；也可以联系 support@dolphindb.com 或致电 0571-82853925。
- 错误码处理
  
  参考：[错误代码](https://docs.dolphindb.cn/zh/error_codes/err_codes.html)
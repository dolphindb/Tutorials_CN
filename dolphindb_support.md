# DolphinDB技术支持攻略

DolphinDB是新一代高性能分布式时序数据库，集成了功能强大的编程语言和流数据分析系统，为海量结构化数据的快速存储、检索、分析及计算提供一站式解决方案，在大规模时序数据处理与分析领域拥有世界领先的性能水平。

在使用DolphinDB的过程中碰到了问题，解决不了怎么办？DolphinDB提供了多种技术支持方式，包括用户手册、Github教程及提交问题、技术问答社区、电子邮件、微信技术交流群、知乎等渠道，帮您解决问题。

## 1. 用户手册

用户手册分中英文两个版本：
- [中文使用手册](https://dolphindb.cn/cn/help/index.html)
- [英文使用手册](http://dolphindb.com/help/index.html)

DolphinDB融编程语言、数据库和分布式计算三者为一体，用户手册对三者的基本概念和基本操作进行了详细介绍，以帮助用户了解系统和入门。其中第2-9章介绍编程语言，包括DolphinDB支持的数据类型与结构、运算符、控制语句、函数、SQL语句、文件IO等。第10章介绍数据库和分布式计算。数据库操作包括增删改查、函数视图等；计算包括分布式计算、内存计算和流计算。第11章介绍了系统管理，包括批处理作业、定时任务、性能监控、权限与安全管理等。第12章提供了API教程链接。

DolphinDB计算功能极其丰富，目前提供了近千个函数。用户手册第13章对这些函数按功能进行了分类并对每个函数进行了详细的说明。用户日常使用时，可随时检索这些函数的语法与例子。用户手册中也一一列举了各类命令，方便用户编程时查阅和参考。

## 2. Github

### 2.1 教程

教程也分中英文版：
- [中文教程系列](https://github.com/dolphindb/Tutorials_CN)  
    若无法打开，可使用[国内镜像](https://gitee.com/dolphindb/Tutorials_CN)。
- [英文教程系列](https://github.com/dolphindb/Tutorials_EN)

教程以专题的形式，对DolphinDB使用过程可能碰到的问题，进行了深入的描述和分析。对每个主题，一般包括设计原理、详细的操作步骤和注意事项等。教程分以下几类：
* 安装和部署：包括单节点和集群部署、docker部署、高可用集群部署、在线扩展集群节点和增加存储、客户端软件安装使用等。
* 数据库：包括分区数据库设计、数据导入、动态增加字段和计算指标、数据库备份与恢复等。
* 编程语言：包括脚本语言的混合范式编程、模块复用教程、通用计算教程、即时编译(JIT)、元编程等。
* 流计算：包括流数据、时序聚合引擎、横截面引擎、异常检测引擎、历史数据回放等。
* 系统管理：包括权限管理和安全、作业管理、定时作业、内存管理、启动脚本等。
* API：包括各语言API使用教程、第三方可视化系统对接教程等。
* 插件：包括插件开发教程、系统提供的MySQL、ODBC、OPC等插件的使用教程。
* 模块：技术分析(Technical Analysis)指标库的使用。
* 应用场景示例：包括K线计算、机器学习、加密货币逐笔交易数据回放等。

### 2.2 问题反馈与新需求

在Github上您也可以把需求与问题告诉我们，以帮助我们完善系统。有关各语言API、插件和Server都可以通过提交issues来反馈问题与提新需求。
- [Python API](https://github.com/dolphindb/api_python3/issues)
- [C++ API](https://github.com/dolphindb/api-cplusplus/issues)
- [Go API](https://github.com/dolphindb/api-go/issues)
- [Java API](https://github.com/dolphindb/api-java/issues)
- [C# API](https://github.com/dolphindb/api-csharp/issues)
- [Rust API](https://github.com/dolphindb/api-rust/issues)
- [R API](https://github.com/dolphindb/api-r/issues)
- [Web API](https://github.com/dolphindb/api-json/issues)
- [插件](https://github.com/dolphindb/DolphinDBPlugin/issues)
- [Server](https://github.com/dolphindb/DolphinDB/issues)

在反馈问题时，请按[附录](#附录)中提问模板的要求，尽量详细。提新需求时，请告诉我们您的应用场景，为什么现有功能不能满足需求，您想要DolphinDB提供什么样的功能。

## 3. 技术问答社区

社区分中文社区与英文社区：
- [DolphinDB问答社区](https://ask.dolphindb.net/)
- [思否SegmentFault](https://segmentfault.com/t/dolphindb)
- [StackOverflow](https://stackoverflow.com/questions/tagged/dolphindb)
 
我们尽力在1个工作日内回复问题。

提问之前建议先搜索一下DolphinDB相关问题帖子，有可能您的问题已经有过提问与解答。提问时请注意：
* 1. 请选择dolphindb标签，其他标签如database、sql、python、c++等请酌情选择，这样可以让您的问题更快的被关注，而且也更好地被搜索定位。
* 2. 提问内容按[附录](#附录)中提问模板的要求，越详细越好。

## 4. 电子邮件支持

邮箱地址：support@dolphindb.com

您的问题，我们尽力在1个工作日内回复。若问题复杂，可能需要更多的时间进行分析和答复。写邮件时请注意以下几点：
* 1. 提问内容按[附录](#附录)中提问模板要求，尽量详细。
* 2. 方便的话，请告知一下您的电话或微信，以便深入交流。

## 5. 微信技术交流群

添加微信号 13306510479（仅用于添加微信）或扫描下面二维码，客服会邀您进群。群里的其他DolphinDB用户和我们的工程师会解答您的问题。

![image](images/wecat.png?raw=true)


## 6. 知乎

请访问知乎上的[智臾科技公司主页](https://www.zhihu.com/org/zhe-jiang-zhi-yu-ke-ji-you-xian-gong-si)

知乎是DolphinDB的产品对外发布平台。与产品相关的技术和测评类文章，都可以在知乎上找到。目前DolphinDB在知乎上有4个专栏，分别是：
- [DolphinDB和量化金融](https://zhuanlan.zhihu.com/DolphinDBinQuantitativeFinance)
- [DolphinDB和物联网](https://zhuanlan.zhihu.com/DolphinDBinIoT)
- [DolphinDB和大数据](https://zhuanlan.zhihu.com/DolphinDBandBigData)
- [Orca — 分布式pandas接口](https://zhuanlan.zhihu.com/orcapandas)

如果您希望了解DolphinDB的产品特点、使用场景、与其他数据库和大数据产品的对比，可以在知乎上查找相关的文章。


## 7. 怎样优先获取技术支持

社区是DolphinDB生命力的源泉，我们十分重视对社区的建设和回馈。为了及时回答和解决未付费的社区用户在使用DolphinDB过程中遇到的问题，我们安排了专职的工程师提供技术支持。但是面对大量的社区用户，有时也难免捉襟见肘。做好以下几点，有助于优先获取DolphinDB工程师的支持。
* 1. 清楚的表述问题：提问内容按[附录](#附录)中提问模板的要求，越详细越好。
* 2. 标识社区身份。社区的建设需要大家的努力。社区建设的第一步便是标识社区身份，方便交流。如果您已经开始使用DolphinDB，建议您登录[Linkedin](https://www.linkedin.com)，在您的Linkedin帐号上将`DolphinDB Database`标注为您的技能。同等情况下，工程师会优先解决已经在Linkedin标识社区身份的用户。标识DolphinDB技能也有助于雇主寻找具有DolphinDB经验的工程师。
* 3. 在技术问答社区回答问题。帮助他人的过程，也是自己学习的过程，可以让自己的知识更系统化，提高自己解决问题的能力。经常回答问题的用户也会获得DolphinDB团队的关注。

## 8. 小结

如果您正在产品选型，希望进一步了解DolphinDB, 请阅读我们在知乎上发布的[相关文章](https://www.zhihu.com/org/zhe-jiang-zhi-yu-ke-ji-you-xian-gong-si/posts)，尤其是与其他产品的对比文章。如果您是新用户，希望了解基本的语法，数据结构，或者某一个函数的使用，请使用在线的[用户手册](https://www.dolphindb.cn/cn/help/index.html)。如果您了解了DolphinDB的基本用法，希望对某一个领域有深入了解，请参阅[Github](https://github.com/dolphindb/Tutorials_CN)或[Gitee](https://gitee.com/dolphindb/Tutorials_CN)上的相关教程。如果您遇到问题，自己无法独立解决，那就到[问答社区](https://segmentfault.com/t/dolphindb/questions)搜索答案、提问，或者发[邮件](mailto:support@dolphindb.com)给我们。我们鼓励您自己解决问题，但若以上方式还不能解决您的问题，请加入我们微信群寻求支持。帮您解决问题，我们将竭尽全力!

## 附录

### 提问要求

提问时，按下列提示和要求来提问，有助于快速高效地得到解答：
- 1. 描述您的运行环境：部署在本地还是云服务器上，集群还是单节点，linux还是windows，32位还是64位，版本号（可在DolphinDB GUI、web Notebook等客户端上执行version()得到）；若是龙芯或ARM版本，请注明硬件平台。
- 2. 尽量清楚地描述问题
    - 描述预期与实际结果。
    - 问题描述，尽可能提供问题所需的主要配置及程序源代码。
    - 明确描述错误提示信息。DolphinDB每个数据节点和控制节点都有独立的log文件，默认在home目录下，里面有系统详细的运行日志，提问时可把相关日志贴上。
    - 一图胜千言，如果有图片请贴上图片。

### 例子

我的DolphinDB部署在本地服务器上，单节点single mode，版本号1.20.1，服务器操作系统是64位Centos 7.6。

我写了一个定时作业，代码如下：
```
loadPlugin(loadPlugin(getHomeDir()+"/plugins/odbc/pluginOdbc.txt");
use odbcdef doJob(){
    connStr="Driver={MySQL ODBC 8.0 UNICODE Driver};Server=127.0.0.1;Database=ecimp_ver3;User=newuser;Password=dolphindb123;Option=3;" 
    conn1=odbc::connect(connStr)
}
scheduleJob("schedulejob1","init",doJob,15:00m, 2020.04.01, 2020.12.31, 'D')
```

现在碰到的问题是添加上述定时作业后，重新启动DolphinDB时，节点启动不了。查看dolphindb.log，错误日志信息如下：
```
<ERROR>:Failed to unmarshall the job [schedulejob1]. Failed to deserialize assign statement.. Invalid message format
```

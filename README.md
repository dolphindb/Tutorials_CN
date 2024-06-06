## DolphinDB 教程

> **注意：自 2.00.12/3.00.0 版本起（2024/4/1），该项目不再维护。用户可移步至 [DolphinDB 文档中心-教程](https://docs.dolphindb.cn/zh/tutorials/about_tutorials.html)。**

- 安装和部署

  - [安装使用指南](dolphindb_user_guide.md)
  - [单节点部署](standalone_server.md)
  - [单节点部署 (嵌入式 ARM 版本)](ARM_standalone_deploy.md)
  - [单服务器集群部署](single_machine_cluster_deploy.md)
  - [多服务器集群部署](multi_machine_cluster_deployment.md)
  - [高可用集群部署教程](ha_cluster_deployment.md)
  - [高可用服务部署与迁移](service_deployment_and_migration.md)
  - [如何扩展集群节点和存储](scale_out_cluster.md)
  - [DolphinDB 客户端软件教程](client_tool_tutorial.md)
  - [DolphinDB 技术支持攻略](dolphindb_support.md)
  - [用新服务器从零开始部署 DolphinDB](deploy_dolphindb_on_new_server.md)
  - [高可用集群灰度升级](gray_scale_upgrade_ha.md)
  - [HAProxy 在 DolphinDB 中的最佳实践](haProxy_best_practices.md)
  - [计算节点使用指南](Compute_Node.md)
  
- 云上部署 DolphinDB

  - [DolphinDB Docker 单机部署方案](../../../dolphindb-k8s/blob/master/docker_single_deployment.md)
  - [基于 Docker-Compose 的 DolphinDB 多容器集群部署](../../../dolphindb-k8s/blob/master/docker-compose_high_cluster.md)
  - [DolphinDB 套件简介](../../../dolphindb-k8s/blob/master/suite_brief_introduction.md)
  - [快速上手 DolphinDB MGR](../../../dolphindb-k8s/blob/master/deploy_k8s_quickly.md)
  - [自托管的 Kubernetes 部署 DolphinDB 集群](../../../dolphindb-k8s/blob/master/k8s_deployment.md)
  - [AWS Marketplace 上的 DolphinDB MGR 快速上手](../../../dolphindb-k8s/blob/master/k8s_deployment_in_AWS.md)
  - [基于阿里云 K8S 的 DolphinDB 套件部署教程](../../../dolphindb-k8s/blob/master/k8s_deployment_in_Aliyun.md)
  
- 数据库

  - [分区数据库设计和操作](database.md)
  - [数据导入教程](import_data.md)
  - [数据备份恢复教程 (1.30.20/2.00.8 及以后版本)](backup-restore-new.md)
  - [数据备份恢复教程 (1.30.20/2.00.8 以前版本)](restore-backup.md)
  - [内存表数据加载与操作](partitioned_in_memory_table.md)
  - [文本数据加载教程](import_csv.md)
  - [集群间数据库同步](data_synchronization_between_clusters.md)
  - [CacheEngine 与数据库日志教程](redoLog_cacheEngine.md)
  - [内存表详解](in_memory_table.md)
  - [DolphinDB 分布式表数据更新原理和性能介绍](dolphindb_update.md)
  - [DolphinDB TSDB 存储引擎介绍](tsdb_engine.md)
  - [DolphinDB TSDB 存储引擎详解](tsdb_explained.md)
  - [DECIMAL 使用教程](DECIMAL.md)
  - [DolphinDB 计算精度问题与 DECIMAL 类型](DECIMAL_Calculation_Characteristics.md)
  - [分级存储](hierarchical_storage.md)
  - [数据迁移与平衡](data_move_rebalance.md)
  - [快照引擎](snapshot_engine.md)
  - [DolphinDB 集群间的异步复制](Asynchronous_Replication.md)
  - [DolphinDB 中有关 array vector 的最佳实践指南](Array_Vector.md)
  - [Debezium + Kafka 实时同步 MySQL 数据到 DolphinDB](Debezium_and_Kafka_data_sync.md)
  - [使用 summary 函数生成大规模数据统计信息](generate_large_scale_statistics_with_summary.md)
  
  
- 编程语言

  - [脚本语言的混合范式编程](hybrid_programming_paradigms.md)
  - [函数化编程案例](functional_programming_cases.md)
  - [模块复用教程](module_tutorial.md)
  - [通用计算教程](general_computing.md)
  - [即时编译 (JIT) 教程](jit.md) 
  - [元编程教程](meta_programming.md)
  - [自定义聚合函数](udaf.md)
  - [矩阵计算](matrix.md)
  - [日期/时间类型](date_time.md)
  - [DolphinDB 窗口计算综述](window_cal.md)
  - [DolphinDB SQL 案例教程](DolphinDB_SQL_Case_Tutorial.md)
  - [DolphinDB SQL 执行计划教程](DolphinDB_Explain.md)
  - [DolphinDB SQL 标准化](Standard_SQL_in_DolphinDB.md)
  - [基于宏变量的元编程](macro_var_based_metaprogramming.md)
  
- 流计算

  - [流数据教程](streaming_tutorial.md)
  - [流数据时序聚合引擎](stream_aggregator.md)
  - [流数据横截面引擎](streaming_crossSectionalAggregator.md)
  - [流数据异常检测引擎](Anomaly_Detection_Engine.md)
  - [历史数据回放教程](historical_data_replay.md)
  - [流数据高可用](haStreamingTutorial.md)
  - [StreamEngineParser 解析原理介绍](StreamEngineParser.md)
  - [DolphinDB 流计算时延统计与性能优化](streaming_timer.md)
  <!-- - [流数据状态函数插件](PluginReactiveState.md)    -->
  
- 系统管理

  - [权限管理和安全](Permission_Management.md)
  - [作业管理](job_management_tutorial.md)
  - [内存管理](memory_management.md)
  - [启动脚本教程](Startup.md)
  - [定时作业](scheduledJob.md)
  - [使用 Prometheus 监控告警](DolphinDB_monitor.md)
  - [如何正确定位节点宕机的原因](how_to_handle_crash.md)
  - [线程简介](thread_intro.md)
  - [从一次 SQL 查询的全过程看 DolphinDB 的线程模型](thread_model_SQL.md)
  - [DolphinDB 集群运维监控教程](cluster_monitor.md)
  - [用户级别的资源跟踪详解](user_level_resource_tracking.md)
  - [OOM 应对指南](handling_oom.md)
  
- 连接器

  - [DolphinDB Python API 使用教程](../../../api_python3/blob/master/README_CN.md)
  - [DolphinDB Python API 离线安装](python_api_install_offline.md)
  - [Java API 使用教程](../../../api-java/blob/master/README_CN.md)

  <!--先隐藏，等教程更新完毕再暴露 - [Java API 使用实例](../../../api-java/blob/master/example/README_CN.md) -->

  - [JDBC 使用教程](../../../jdbc/blob/master/README_CN.md)
  - [C# API 使用教程](../../../api-csharp/blob/master/README_CN.md)
  - [C++ API 使用教程](../../../api-cplusplus/blob/main/README_CN.md)
  - [C++ API 数据写入使用指南](ddb_cpp_api_connector.md)
  - [C++ API 数据读写指南](c%2B%2Bapi.md)
  - [Go API 使用教程](../../../api-go/blob/master/README.md)
  - [R API 使用教程](../../../api-r/blob/master/README_CN.md)
  - [Json API 使用教程](../../../api-json/blob/master/README_CN.md)
  - [NodeJS API 使用教程](../../../api-nodejs/blob/master/README.md)
  - [JavaScript API 使用教程](../../../api-javascript/blob/master/README.zh.md)
  - [redash 连接 DolphinDB 数据源的教程](data_interface_for_redash.md)
  - [DolphinDB 整合前端 chart 组件展示数据教程](web_chart_integration.md)
  - [Grafana 连接 DolphinDB 数据源](../../../grafana-datasource/blob/master/README.zh.md)
  - [帆软报表软件连接 DolphinDB 数据源](FineReport_to_dolphindb.md)
  - [API 交互协议](api_protocol.md)
  
- 插件
  
  - 插件开发与使用
    - [插件开发教程（介绍插件开发的方法与流程）](plugin_development_tutorial.md "介绍插件开发的方法与流程")
    - [插件开发深度解析（介绍插件开发中的常见问题）](plugin_advance.md "介绍插件开发中的常见问题")
    - [DolphinDB VSCode 插件使用说明](https://gitee.com/dolphindb/vscode-extension/blob/main/README.zh.md "VSCode 插件使用说明")
  - 数据导入、交互与转换
    - [AWS S3 插件使用说明（如何编译、加载和使用该插件并实现 AWS S3 对象存储与 DolphinDB 之间的数据交互）](../../../DolphinDBPlugin/blob/release200/aws/README.md "如何编译、加载和使用该插件并实现 AWS S3 对象存储与 DolphinDB 之间的数据交互")
    - [Excel 插件（用于从 MS Excel 向 DolphinDB 数据库的数据导入，不含使用说明）](../../../excel-add-in "用于从 MS Excel 向 DolphinDB 数据库的数据导入，不含使用说明")
    - [Feather 插件使用说明（用于 Apache Arrow 协议下的数据列式存储、读取和转换）](../../../DolphinDBPlugin/blob/release200/feather/README.md "Apache Arrow 协议下的数据列式存储、读取和转换")
    - [Arrow 插件使用说明（用于在 server 与 API 交互时对列式数据进行数据类型转换）](../../../DolphinDBPlugin/blob/release200/Arrow/README_CN.md "用于在 server 与 API 交互时对列式数据进行数据类型转换")
    - [HBase 插件使用说明（介绍如何通过 Thrift 接口连接 HBase 数据源并读取数据）](../../../DolphinDBPlugin/blob/release200/hbase/README.md "如何通过 Thrift 接口连接 HBase 数据源并读取数据")
    - [HDF5 插件使用说明（介绍如何将 HDF5 文件导入 DolphinDB 并完成数据类型转换）](../../../DolphinDBPlugin/blob/release200/hdf5/README_CN.md "如何将 HDF5 文件导入 DolphinDB 并完成数据类型转换")
    - [HDFS 插件使用说明（介绍如何读取 Hadoop 分布式文件系统上的文件信息及传输 HDFS 上的文件至本地）](../../../DolphinDBPlugin/blob/release200/hdfs/README.md "介绍如何读取 Hadoop 分布式文件系统上的文件信息及传输 HDFS 上的文件至本地")
    - [kdb 插件使用说明（用于导入 kdb+ 数据表和 Q 语言数据类型到 DolphinDB 内存表）](../../../DolphinDBPlugin/blob/release200/kdb/README_CN.md "用于导入 kdb+ 数据表和 Q 语言数据类型到 DolphinDB 内存表")
    - [Matlab 插件使用说明（用于在 Matlab 文件与 DolphinDB server 之间的数据读写和类型转换）](../../../DolphinDBPlugin/blob/release200/mat/README.md "用于在 Matlab 文件与 DolphinDB server 之间的数据读写和类型转换")
    - [MongoDB 插件使用说明（用于将 MongoDB 数据源的数据导入 DolphinDB 内存表）](../../../DolphinDBPlugin/blob/release200/mongodb/README_CN.md "用于将 MongoDB 数据源的数据导入 DolphinDB 内存表")
    - [MSeed 插件使用说明（用于在 miniSEED 文件和 DolphinDB 内存表间的数据读取和写入）](../../../DolphinDBPlugin/blob/release200/mseed/README.md "用于在 miniSEED 文件和 DolphinDB 内存表间的数据读取和写入")
    - [MySQL 插件使用说明（用于将 MySQL 中的数据表或语句查询结果高速导入 DolphinDB）](../../../DolphinDBPlugin/blob/release200/mysql/README_CN.md "用于将 MySQL 中的数据表或语句查询结果高速导入 DolphinDB")
    - [ODBC 插件使用说明（介绍如何通过 ODBC 连接其它数据源，导入数据到 DolphinDB 数据库，或将 DolphinDB 内存表导出到其它数据库）](../../../DolphinDBPlugin/blob/release200/odbc/README_CN.md "介绍如何通过 ODBC 连接其它数据源，导入数据到 DolphinDB 数据库，或将 DolphinDB 内存表导出到其它数据库")
    - [ODBC 插件使用指南（介绍 ODBC 插件的一般使用方法和常见问题解决）](ODBC_plugin_user_guide.md "介绍 ODBC 插件的一般使用方法和常见问题解决")
    - [Parquet 插件使用说明（Apache Parquet 协议下的数据列式存储、读取和转换）](../../../DolphinDBPlugin/blob/release200/parquet/README_CN.md "Apache Parquet 协议下的数据列式存储、读取和转换")
    - [Kafka 插件说明（用于发布或订阅 Apache Kafka 流服务）](../../../DolphinDBPlugin/blob/release200/kafka/README_CN.md "用于发布或订阅 Apache Kafka 流服务")
  - 金融市场行情数据
    - [amdQuote 插件使用说明（如何在 Linux 下安装和使用该插件连接 AMD 行情服务器获取行情信息）](../../../DolphinDBPlugin/blob/release200.11/amdQuote/README.md "如何在 Linux 下安装和使用该插件连接 AMD 行情服务器获取行情信息")
    - [Insight 插件说明（介绍如何在 Linux 下通过该插件获取交易所行情数据）](../../../DolphinDBPlugin/blob/release200/insight/README.md "用于获取交易所行情数据，仅限 Linux 系统")
    - [Matching Engine 插件使用说明（用于为股票市场、商品市场或其他金融交易所匹配和执行买入和卖出订单）](../../../DolphinDBPlugin/blob/release200/MatchingEngine/README.md "用于为股票市场、商品市场或其他金融交易所匹配和执行买入和卖出订单")
    - [NSQ 插件使用说明（用于获取上海和深圳交易市场的行情数据）](../../../DolphinDBPlugin/blob/release200/nsq/README.md "用于获取上海和深圳交易市场的行情数据")
    <!-- - [流数据状态函数插件（用于有状态的高频因子流计算）](PluginReactiveState.md "用于有状态的高频因子流计算")  -->
  - 物联网数据处理与传输
    - [OPC 插件使用说明（用于访问并采集自动化行业 OPC 服务器的数据）](../../../DolphinDBPlugin/blob/release200/opc/README_CN.md "用于访问并采集自动化行业 OPC 服务器的数据")
    - [OPCUA 插件使用说明（用于与自动化行业 OPC UA 服务器之间的数据传输）](../../../DolphinDBPlugin/blob/release200/opcua/README_CN.md "用于与与自动化行业 OPC UA 服务器之间的数据传输")
    - [Signal 插件使用说明（用于信号处理）](../../../DolphinDBPlugin/blob/release200/signal/README_CN.md "用于信号处理")
  - 消息队列
    - [HttpClient 插件使用说明（介绍如何使用该插件整合外部消息平台的数据）](send_messages_external_systems.md "介绍如何使用该插件整合外部消息平台的数据")
    - [MQTT 插件使用说明（用于向 MQTT 服务器发布或订阅消息）](../../../DolphinDBPlugin/blob/release200/mqtt/README_CN.md "用于通过该插件向 MQTT 服务器发布或订阅消息")
    - [zmq 插件使用说明（用于 zmq 消息队列库的请求应答、发布、订阅和管道消息传输）](../../../DolphinDBPlugin/blob/release200/zmq/README.md "用于 zmq 消息队列库的请求应答、发布、订阅和管道消息传输")

  - 机器学习
    - [SVM 插件使用说明（用于在机器学习数据处理中对 DolphinDB 对象执行支持向量机模型的训练和预测）](../../../DolphinDBPlugin/blob/release200/svm/README.md "用于对 DolphinDB 对象执行 SVM 模型的训练和预测")
    - [XGBoost 插件使用说明（用于机器学习数据的训练、预测、模型保存和加载）](../../../DolphinDBPlugin/blob/release200/xgboost/README_CN.md "用于机器学习数据的训练、预测、模型保存和加载")
  - 其他工具
    - [Py 插件使用说明（介绍如何在 DolphinDB 内调用 Python 环境中的第三方库）](../../../DolphinDBPlugin/blob/release200/py/README_CN.md "介绍如何在 DolphinDB 内调用 Python 环境中的第三方库")
    - [ZLib 插件使用说明（用于文件到文件的 zlib 压缩与解压缩）](../../../DolphinDBPlugin/blob/release200/zlib/README.md "用于文件到文件的 zlib 压缩与解压缩")  
    - [GP 插件使用说明（用于利用 DolphinDB vector 和 table 中的数据绘图）](../../../DolphinDBPlugin/blob/release200/gp/README.md "用于利用DolphinDB vector 和 table 中的数据绘图") 

- 模块

  - [基于 DolphinDB 的 Barra 多因子风险模型实践](barra_multi_factor_risk_model_0.md)
  - [技术分析 (Technical Analysis) 指标库](../../../DolphinDBModules/blob/master/ta/README_CN.md)
  - [mytt (My 麦语言 T 通达信 T 同花顺) 指标库](../../../DolphinDBModules/blob/master/mytt/README.md)
  - [WorldQuant 101 Alpha 因子指标库](../../../DolphinDBModules/blob/master/wq101alpha/README_CN.md)
  - [ops 运维函数库](../../../DolphinDBModules/blob/master/ops/README.md)
  - [国泰君安 191 Alpha 因子库](../../../DolphinDBModules/blob/master/gtja191Alpha/README_CN.md)
  - [交易日历](../../../DolphinDBModules/blob/200.11/MarketHoliday/README.md)
  - [easyNSQ：实时行情数据接入功能模块使用教程](../../../DolphinDBModules/blob/master/easyNSQ/README.md)
  - [easyTLDataImport：通联历史数据自动化导入功能模块使用教程](../../../DolphinDBModules/blob/master/easyTLDataImport/README.md)

- 应用场景示例

  - [使用 DolphinDB 进行机器学习](machine_learning.md)
  - [深度学习遇到 DolphinDB AI DataLoader](DolphinDB_AI_DataLoader_for_Deep_Learning.md) 
  <!-- - [基于逐笔数据合成高频订单簿](orderBookSnapshotEngine.md)-->
  - [DolphinDB缓存表（CachedTable）快速实现MySQL跨数据库基础信息同步功能](cachedtable.md)
  - [DolphinDB中有关时间信息的最佳实践指南](timezone.md)
  - 金融：
    - [在 DolphinDB 中计算 K 线](OHLC.md)
    - [基于快照行情的股票和基金 K 线合成](K.md)
    - [实时计算高频因子](hf_factor_streaming.md) 
    - [DolphinDB 教程：面板数据的处理](panel_data.md)
    - [金融高频因子的流批统一计算：DolphinDB 响应式状态引擎](reactive_state_engine.md)
    - [股票行情数据导入实例](stockdata_csv_import_demo.md)
    - [节点启动时的流计算自动订阅教程](streaming_auto_sub.md)
    - [DolphinDB 机器学习在金融行业的应用：实时实际波动率预测](machine_learning_volatility.md)
    - [DolphinDB 流计算在金融行业的应用：实时计算分钟资金流](streaming_capital_flow_order_by_order.md)
    - [基于 DolphinDB 的因子计算最佳实践](best_practice_for_factor_calculation.md)
    - [SQL 优化案例：深度不平衡、买卖压力指标、波动率计算](sql_performance_optimization_wap_di_rv.md)
    - [SQL 优化案例：外汇掉期估值计算](FxSwapValuation.md)
    - [DolphinDB 流计算在金融行业的应用：实时计算日累计逐单资金流](streaming_capital_flow_daily.md)
    - [DolphinDB 历史数据回放功能应用：股票行情回放](stock_market_replay.md)
    - [DolphinDB 搭建行情回放服务的最佳实践](appendices_market_replay_bp.md)
    - [优化投资组合：DolphinDB 最优化求解系列函数应用指南](MVO.md)
    - [DolphinDB 流计算应用：基金份额参考价值 IOPV 计算](streaming_IOPV.md)
    - [DolphinDB 元编程：开发股票波动率预测模型的 676 个输入特征](metacode_derived_features.md)
    - [从 4.5 小时到 3.5 分钟，如何利用 DolphinDB 高效清洗数据](data_ETL.md)
    - [DolphinDB 流式计算中证 1000 指数主买/主卖交易量](CSI_1000.md)
    - [公募基金历史数据基础分析教程](public_fund_basic_analysis.md)
    - [平均性能超 Python10 倍：如何使用 DolphinDB 计算基金日频因子](fund_factor_contrasted_by_py.md)
    <!-- - [DolphinDB Kafka 插件最佳实践指南](kafka_plugin_guide.md) -->
    - [中高频多因子库存储最佳实践](best_practices_for_multi_factor.md)
    - [金融 PoC 用户历史数据导入指导手册之股票 level2 逐笔篇](LoadDataForPoc.md)
    - [DolphinDB NSQ 插件最佳实践指南](best_implementation_for_NSQ_Plugin.md)
    - [通过 DolphinDB JIT 功能加速计算 ETF 期权隐含波动率和希腊值](IV_Greeks_Calculation_for_ETF_Options_Using_JIT.md)
    - [DolphinDB 流数据连接引擎应用：多数据源流式实时关联处理](streaming-real-time-correlation-processing.md)
    - [基于 DolphinDB 与 Python Celery 框架的因子计算平台构建](Python_Celery.md)
    - [快速搭建 Level-2 快照数据流批一体因子计算平台最佳实践](Level2_Snapshot_Factor_Calculation.md)
    - [DolphinDB 处理 Level-2 行情数据实例](Level-2_stock_data_processing.md)
    - [DolphinDB 与 Python AirFlow 最佳实践](Best_Practices_for_DolphinDB_and_Python_AirFlow.md)
    - [金融因子流式实现](Streaming_computing_of_financial_quantifiers.md)
    - [Python + HDF5 因子计算与 DolphinDB 一体化因子计算方案对比](Python+HDF5_vs_DolphinDB.md)
    - [Python + 文件存储与 DolphinDB 因子计算性能比较](DolphinDB_VS_Python+File_Storage.md)
    - [DolphinDB 流计算在金融行业的应用：实时计算涨幅榜](Real-Time_Stock_Price_Increase_Calculation.md)
    - [DolphinDB TopN 系列函数教程](DolphinDB_TopN.md)
    - [DolphinDB AMD 插件最佳实践指南](best_implementation_for_AMD_Plugin.md)
    - [DolphinDB Python Parser 在金融量化分析场景的入门教程](DolphinDB_Python_Parser_Intro_for_Quantitative_Finance.md)
    - [模拟撮合引擎应用教程](matching_engine_simulator.md)
    - [DolphinDB 与任务调度器 DolphinScheduler 的集成](dolphinscheduler_integration.md)
    - [基于 DolphinDB 存储金融数据的分区方案最佳实践](best_practices_for_partitioned_storage.md)
    - [DolphinDB INSIGHT 行情插件最佳实践指南](insight_plugin.md)
  - 物联网：
    - [物联网应用范例](iot_examples.md)
    - [实时检测传感器状态变化](DolphinDB_streaming_application_in_IOT.md)
    - [DolphinDB 在工业物联网的应用](iot_demo.md)
    - [物联网时序数据查询案例](iot_query_case.md)
    - [DolphinDB 流计算引擎实现传感器数据异常检测](iot_anomaly_detection.md)
    - [DolphinDB 流计算在物联网的应用：实时检测传感器状态变化](DolphinDB_streaming_application_in_IOT.md)
    - [随机振动信号分析解决方案](Random_Vibration_Signal_Analysis_Solution.md)
    - [DolphinDB 通过 Telegraf 与 Grafana 实现设备指标的采集监控和展示](DolphinDB_Telegraf_Grafana.md)
    - [DolphinDB 机器学习在物联网行业的应用：实时数据异常预警](knn_iot.md)
    - [DolphinDB 流计算应用：引擎级联监测门禁异常状态](streaming_engine_anomaly_alerts.md)
    - [基于 DolphinDB 机器学习的出租车行程时间预测](Forecast_of_Taxi_Trip_Duration.md)
    - [地震波形数据存储解决方案](Seismic_waveform_data_storage.md)
    - [使用 DolphinDB 和机器学习对地震波形数据进行预测](Earthquake_Prediction_with_DolphinDB_and_Machine_Learning.md)
    - [PIP 降采样算法文章](PIP_in_DolphinDB.md)
    - [使用 Node-RED 构建 DolphinDB 低代码平台](node_red_tutorial_iot.md)
    - [动态增加字段和计算指标](add_column.md)
    - [DolphinDB 基于 Glibc 升级的性能优化实战案例](performance_optimization_based_on_glibc.md)
    - [工业试验平台高频数据的存储和处理分析](high_freq_data_storage_and_analysis.md)
    - [助力工业物联网实现智能运维](Iot_intelligent_O&M.md)
    - [DolphinDB 历史数据回放功能应用：物联网设备故障分析](faultAnalysis.md)
    - [云边协同：DolphinDB 构建一体化振动监控与故障诊断解决方案](Virbration_Monitor_Fault_Diagnose.md)

- 入门和测试

  - [DolphinDB 入门：量化金融范例](quant_finance_examples.md)
  - [DolphinDB 入门：物联网范例](iot_examples.md)

- 测试报告

  - [DolphinDB API 性能基准测试报告](api_performance.md)
  - [金融市场高频数据应当如何管理 - DolphinDB 与 pickle 的性能对比测试和分析](DolphinDB_pickle_comparison.md)
  - [DolphinDB 集群水平扩展性能测试](Cluster_scale_out_performance_test.md)

- 数据迁移

  - [Python 函数到 DolphinDB 函数的映射](function_mapping_py.md)
  - [从 Kdb+ 到 DolphinDB](kdb_to_dolphindb.md)
  - [从 SQL Server 迁移数据到 DolphinDB](SQLServer_to_DolphinDB.md)
  - [从 InfluxDB 迁移数据到 DolphinDB](Migrate_data_from_InfluxDB_to_DolphinDB.md)
  - [从 Redshift 迁移数据到 DolphinDB](Migrate_data_from_Redshift_to_DolphinDB.md)
  - [基于 DataX 的 DolphinDB 数据导入工具](../../../datax-writer)
  - [从 OceanBase 迁移到 DolphinDB](OceanBase_to_DolphinDB.md)
  - [从 Oracle 迁移到 DolphinDB](Oracle_to_DolphinDB.md)
  - [从 Postgre/Greenplum 迁移到 DolphinDB](migrate_data_from_Postgre_and_Greenplum_to_DolphinDB.md)
  - [从 ClickHouse 迁移到 DolphinDB](ClickHouse_to_DolphinDB.md)
 
- 开源项目

  - [开源项目贡献者指南](DolphinDB_Open_Source_Project_Contribution.md)

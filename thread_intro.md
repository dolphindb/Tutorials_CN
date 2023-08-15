# 线程简介

基于 DolphinDB server 最新版 2.00.X，从任务管理、存储引擎、流数据、集群管理、高可用几个方面简单介绍 DolphinDB 在运行中可能使用到的各种线程，及其相关的配置项和函数。

## 1.任务管理

工作线程（Worker）接收客户端请求，将任务分解为多个小任务，根据任务的粒度自己执行或者发送给执行线程 localExecutor 、交给下级线程执行或者由 remoteExecutor 发送到远端执行。

- Worker

  常规交互作业的工作线程。每个节点都存在 Worker 线程，可以分为以下几类。

  - ZeroWorker, FirstWorker, SecondWorker, ThirdWorker, ForthWorker, FifthWorker, SixthWorker

    客户端提交至节点的作业为0级，由 ZeroWorker 处理。根据作业所涉及到的分区，ZeroWorker 将其分解为多个子任务。其中本地节点上的子任务由 ZeroWorker 与 FirstWorker 并行执行；需要由远程节点执行的子任务则降低为1级，并通过 remoteExecutor 发送到对应节点上的 FirstWorker 处理。以此类推，若某个级别的子任务需要进一步拆解，则拆分出来的由远程节点执行的子任务降低一级，发送至远程节点上对应层级的 Worker 处理。

    ZeroWorker, FirstWorker, SecondWorker 的数量由 `workerNum` 决定，分别为workerNum, workerNum-1, workerNum*0.75，`workerNum` 默认值为机器上的 CPU 核数，最大值不超过 license 中的最大核数。其余层级的 Work 数量为上级的1/2，最小为1。

  - UrgentWorker

    处理紧急任务，只接收一些特殊的系统级任务，譬如登录，取消作业等。由 `urgentWorkerNum` 配置，默认值为1，最大值为 CPU 内核数。

  - WebWorker

    处理 HTTP 请求，由 webWorkerNum 配置。默认为1，最大值为 CPU 内核数。

  - InfraWorker

    开启高可用后，用于接收 raft 心跳汇报的线程，防止集群负载大时，心跳信息无法及时汇报。默认有2个该线程。

- RemoteExecutor

  将远程任务发送到远程节点的线程，在非 single 模式的节点上可以通过 `remoteExecutors` 配置线程个数。默认值为集群中节点个数和本地 Worker 的较小值。

- AsynchronousRemoteExecutor

  接收对其他节点发起的远程调用（Remote Procedure Call, RPC）任务的线程，并将收到的远程调用放到 RemoteExecutor 的任务队列中。每个非 single 模式的节点上有且仅有一个该线程。

- RemoteTaskDispatcher

  在远程调用出错需要重试时，或者一个被关闭的连接上仍有未完成的任务时，这些任务会先放到一个队列里，由 RemoteTaskDispatcher 从这个队列取任务并重新交由 AsynchronousRemoteExecutor 去发起远程调用。

- DynamicWorkerManager 和 DynamicWorker

  DynamicWorker 是动态工作线程，作为 Worker 的补充。DynamicWorkerManager 是创建 DynamicWorker 的线程，每个节点有且仅有一个该线程。如果所有的工作线程被占满，有新任务到来时，通过该线程创建 DynamicWorker 来执行新任务。根据系统并发任务的繁忙程度，总共可以创建三组动态工作线程，每一个级别可以创建 maxDynamicWorker 个动态工作线程。

  动态工作线程在任务执行完后若闲置60秒则会被系统自动回收，不再占用系统资源。maxDynamicWorker 的默认值为 workerNum。

- BlockIOWorker

  执行对硬盘读写任务的线程。通过 `diskIOConcurrencyLevel` 控制线程数量，默认值为1。

- BatchJobWorker

  执行批处理作业任务的工作线程。其上限通过 `maxBatchJobWorker` 设置，默认值是 workerNum。该线程在任务执行完后若闲置60秒会被系统自动回收，不再占用系统资源。

## 2.存储引擎

存储相关的线程在 server 启动过程中创建。其主要负责数据的写入与落盘，并在各种情况下（如节点宕机，磁盘损坏导致数据损坏）维护各节点间数据的完整与一致性。

### 2.1 预写日志

在数据节点上，OLAP 和 TSDB 都有两个写预写日志（WAL）的线程 RedoLogHeadWriter 和 RedoLogDataWriter，分别负责写 WAL 的元数据和数据。

存储 OLAP 和 TSDB WAL 日志的目录分别由 `redoLogDir`, `TSDBRedoLogDir` 配置。

- RedoLogHeadWriter

  事务发生时通过 RedoLogHeadWriter 同步写事务元数据信息到 redoLog 目录下的 header.log 中。

- RedoLogDataWriter

  事务的数据会通过 RedoLogDataWriter 异步写入 redoLog 目录下的 tid.log 中。

### 2.2 OLAP 引擎

在开启了 OLAP 的 cacheEngine 后，会创建一个 ChunkCacheEngineGCWorker 线程。

- ChunkCacheEngineGCWorker

  负责将 cacheEngine 中的数据写入磁盘的线程。用于清理 cacheEngine，并将磁盘的随机写变成顺序写的线程。BackgroundRoutineService 每隔60秒，或者写入时 cacheEngine 的占用量超过 OLAPCacheEngineSize 的30%，就会触发 ChunkCacheEngineGCWorker 将 cacheEngine 中的数据写入磁盘。cacheEngine 中一张表的一个分区数据称为一个 tabletCache，ChunkCacheEngineGCWorker 写入磁盘时会根据每个 tabletCache 的大小和在 cacheEngine 中存在时间决定写入磁盘优先级，tabletCache 的大小越大、存在时间越久写入磁盘优先级越高。

### 2.3 TSDB 引擎（1.30.X 版本 server 无此类线程）

除了将数据写入磁盘外，TSDB 引擎的线程还要负责 cacheEngine 中数据的排序与合并，并维护磁盘上的 levelFile，以提高读写性能。这些线程也仅在数据节点上存在。

- TableAsyncSortRunner

  异步地对 TSDB cacheEngine 中的表进行排序的线程。TSDB 在写入 cacheEngine 时，如果 cacheEngine 中的表太大，会影响查询性能，因此需要进行排序。但若同步进行排序，会影响写入性能。所以 DolphinDB 提供此线程异步地对表进行排序。可以通过 `TSDBAsyncSortingWorkerNum` 来控制排序线程的数量，默认值为1。也可以通过函数 `disableTSDBAsyncSorting` 和 `enableTSDBAsyncSorting`，来手动开启和关闭异步排序功能。

- CacheDumpTaskDispatcher

  分配 cacheEngine 写入磁盘任务的线程。线程数量固定为1。
  当 cacheEngine 的内存占用大于 TSDBCacheEngineSize 时，系统会对 cacheEngine 做一次快照，并将快照送到 CacheDumpTaskDispatcher 线程准备写入磁盘。CacheDumpTaskDispatcher 线程将任务分配给 ChunkCacheDumpRunner 线程，由该线程写入磁盘。若磁盘上存在需要合并的 levelFile，则交由 MergeRunner 线程进行合并。

- ChunkCacheDumpRunner

  将 cacheEngine 中的数据写入磁盘的线程。线程的个数等于 `volumes` 的配置值。

- MergeRunner

  对磁盘上 levelFile 进行合并的线程，线程的个数等于 `volumes` 的配置值。

- DelLevelFileRunner

  检查并删除无效的 levelFile（即已经被合并的较小 size 的文件）的线程。线程数量固定为1。每隔30秒会自动执行一次。

### 2.4 数据恢复

数据恢复（recovery）相关线程负责节点宕机，或者数据损坏时，数据副本间的数据恢复。

- RecoveryReportingService

  在数据节点上，任何一个 chunk 发生数据错误或者版本号不一致都通过该线程来向控制节点汇报。每个数据节点有且仅有一个该线程。

- RecoveryWorker

  发生 recovery 时，数据恢复的源节点将数据发送给目标节点的线程。该线程仅存在于数据节点，个数可由 `recoveryWorkers` 配置，默认值为1。可以通过 `resetRecoveryWorkerNum` 函数动态修改线程个数，通过 `getRecoveryWorkerNum` 函数获取实际 RecoveryWorker 线程数量。

- RecoverMetaLogWriter 和 RecoverRedoLogDataWriter

  在线恢复（onlineRecovery）过程中，为了避免节点宕机或离线影响恢复过程，会分别通过 RecoverMetaLogWriter 和 RecoverRedoLogDataWriter 写 recover redoLog 的元数据（Metadata）和数据（data）。与 redoLog 不同的是，recover redoLog 的 Metadata 和 data 需要进行写磁盘时才能开始 recovery。通过 `enableDfsRecoverRedo` 配置是否开启 recover redoLog，默认是开启。开启后，在每个数据节点上存在一个相应的线程。recover redoLog 的文件目录也可以通过 `recoverLogDir` 配置，默认在节点根目录下的 `log/recoverLog` 中。

- DFSChunkRecoveryWorker

  在控制节点上处理 recovery 任务的线程。同时进行 recovery 任务的数量默认为集群中数据节点个数的2倍，可由 `dfsRecoveryConcurrency` 配置。

### 2.5 事务相关

如果集群中的某个节点在处理事务的过程中宕机了，那么重启后仅依靠该节点有可能无法确定事务的最终状态，需要在集群中进行事务决议来确定。

- UnresolvedTransactionReporter

  在数据节点启动时，如果数据节点自己不能判断某些事务的状态，通过该线程来向控制节点汇报并发起事务决议，判断事务最终处于回滚还是完成状态。该线程只有一个，且在所有需要决议的事务决议后结束。

- DFSTransactionResolutionWorker

  该线程处理由数据节点发起的事务决议、控制节点启动时回放元数据后无法决定状态的事务或运行时超时未更新状态的事务。在控制节点上存在一个该线程。

- ChunkNodeLogWriter

  数据节点写元数据的线程。元数据默认在各个数据节点根目录下的 `storage/CHUNK_METADATA` 中，可以通过配置项 `chunkMetaDir` 修改。在数据节点上存在一个该线程。

- EditLogBatchWriter

  控制节点写元数据的线程。由于对控制节点上元数据的修改比较频繁，所以由该线程统一将写入缓冲区的数据写入磁盘并同步，同时还对写元数据失败的情况进行回滚处理。在控制节点上存在一个该线程。

### 2.6 其他

- SnapshotEngineWorker

  为减少开启快照引擎对写入的影响，而将分布式表数据异步写入快照引擎的线程。在数据节点上存在一个该线程。可以通过函数 `registerSnapshotEngine` 和 `unregisterSnapshotEngine` 对一个分布式表注册和取消注册快照引擎。

- DFSChunkRebalanceWorker

  节点间平衡数据或者多块磁盘间平衡数据的任务，均交由控制节点上的 DFSChunkRebalanceWorker 线程处理。在控制节点上存在一个该线程。同时发起的数据平衡任务数量默认为集群中数据节点个数的两倍。可由 `dfsRebalanceConcurrency` 配置。通过函数 `rebalanceChunksWithinDataNode` 和 `rebalanceChunksAmongDataNodes` 手动触发节点或磁盘间的数据平衡。

## 3.流数据

本节通过发布订阅、计算引擎和高可用三个模块介绍流数据相关线程。这些线程都仅在数据节点或单节点上存在。

### 3.1 发布订阅

以下为数据节点上普通流表的订阅发布流程中涉及到的线程。

- MessageThrottle

  实现流数据订阅 throttle 参数功能的线程，数量为1。系统每隔一段时间检查当前节点上是否存在经过  throttle 时间但仍未达到 batchSize 的订阅（[subscribeTable](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/s/subscribeTable.html) 函数中指定了 batchSize 和 throttle ）。如果存在，则触发一次订阅的消息处理。通过 `subThrottle` 配置触发检查的间隔时间，默认值为1000，单位为毫秒。

- AsynchronousPublisher

  在 AsynchronousPublisher 线程中检查每个发布节点对每个订阅节点建立的连接。如果这个连接对应的发布队列有更新，就将更新的数据发布到订阅端。通过 `maxPubConnections` 配置发布节点连接的订阅节点数量上限，默认值为0，表示不可以作为发布节点，即不会创建 AsynchronousPublisher 线程，大于0时会创建一个该线程。

- AsynchronousSubscriber

  监听所有的订阅连接，接收、解析连接上收到的数据，并发送到相应的订阅消息队列。配置了subPort之后，会创建一个该线程。 通过 `maxSubConnections` 配置一个订阅节点可以连接的发布节点数量上限，默认值为64。

- LocalSubscriberImp

  在 LocalSubscriberImp 线程中直接检查有数据更新的本地订阅，并将符合条件的本地订阅中的数据发送到订阅消息队列中。配置 subPort 后，会创建一个该线程。

- StreamExecutor

  StreamExecutor 线程从订阅消息队列中取出数据，写入相应订阅的 handler 中，同时维护订阅的偏移量、消息总数等信息。每个订阅消息队列对应一个 StreamExecutor 线程，数量由配置项 subExecutors 决定，默认值为1，最大不超过 CPU 核数。

- PersistenceWorker

  以异步方式持久化的流表会通过 PersistenceWorker 线程将数据写到磁盘上。`persistenceWorkerNum` 控制持久化线程的数量，默认为1。由 `persistenceDir` 配置开启持久化的流表的保存路径。

- AsynchronousReconnector

  针对所有设置参数 reconnect=true 的订阅，系统会在非正常中断后通过该线程尝试自动重连。在配置了`subPort` 之后，会创建一个该线程。

### 3.2 计算引擎

创建计算引擎时，若配置了如下参数，便会创建两个线程：CheckTimeExecutor 和 SystemTimeExecutor。

- CheckTimeExecutor

  包括 TimeSeriesCheckTimeExecutor, SessionCheckTimeExecutor, CSEngineCheckTimeExecutor, AsofJoinCheckTimeExecutor 和 LookupJoinCheckTimeExecutor。

  在创建 TimeSeriesEngine 时设置了 updateTime、创建 SessionWindowEngine 时设置了 forceTriggerTime、创建 CrossSectionalEngine 时设置了 triggeringPattern=“interval”、创建 AsofJoinEngine 时设置了 delayedTime、创建 LookupJoinEngine 时设置了 checkTimes，那么每个引擎就会创建一个 CheckTimeExecutor 线程，表示如果经过了参数设置的时间还未触发计算，则强制触发一次引擎的计算。

- SystemTimeExecutor

  包括 TimeSeriesSystemTimeExecutor, SessionSystemTimeExecutor, CrossSectionalEngineExecutor 和 WindowJoinSystemTimeExecutor。

  在创建 TimeSeriesEngine, SessionWindowEngine, CrossSectionalEngine 和 WindowJoinEngine 时，如果设置了 useSystemTime=true，那么每个引擎就会创建一个 SystemTimeExecutor 线程，表示每隔固定的时间触发一次引擎的计算。

### 3.3 流数据高可用

配置项 `streamingRaftGroups` 中每个 group 都会在 group 内的节点上生成下述的三个线程。

- StreamingDataFileWriter

  在 raft 的 leader 节点上向流表写数据时，要通过该线程应用 leader 上写数据的 entryLog，向流表写数据。

- StreamingRaftReplayWorker

  当一个节点成为某个 group 的 leader 时，就会通过该线程回放此 group 的 raftLog。

- StreamingHA::CkptWorker

  为节点上的 raftLog 做 checkpoint 以回收垃圾的线程。垃圾回收的间隔可由 `streamingHAPurgeInterval` 设置，默认值为300，单位是秒。

## 4.集群管理

在集群中控制节点通过心跳监控其他节点的存活状态。

- HeartBeatSender

  控制数据节点或计算节点向控制节点每隔0.5秒发送一次心跳的线程。心跳信息中同时还会汇报节点当前的一些信息（如 CPU、内存、磁盘占用）给控制节点。在数据节点或计算节点上存在一个该线程。
  通过 lanCluster 控制心跳采用 udp 或 tcp 协议，当为 true 时使用 udp，false 时使用 tcp，默认值为true。

- HeartBeatReceiver

  仅当 lanCluster=true 时，在控制节点和数据节点、计算节点上存在的接收 udp 心跳的线程。

- HeartBeatMonitor

  仅在控制节点存在的线程。每隔一秒检查一次是否收到集群中数据节点或计算节点的心跳信息。如果一个节点连续3次检查都没有心跳，就认为这个节点已经宕机了。
  如果数据节点配置了 datanodeRestartInterval（值大于0），那么当节点宕机时间超过设置值，就会通过 agent 重启该数据节点。该配置项默认值为0。

- ServiceMgmtCenter

  仅在控制节点存在的线程。当一个代理节点重新上线时，通过该线程将公钥信息保存到代理节点上。当一个数据节点重新上线时，会让其汇报节点的所有 chunk 信息，并且在数据节点上删除控制节点上不存在的chunk。

## 5.控制节点高可用

本节简述开启控制节点高可用之后，raft 相关的线程。对于每种线程，在 raft group 内的每个控制节点上都有且仅有一个。

- RaftTimer

  负责计时（心跳发送间隔和发起选举时间）的线程。leader 通过该线程每隔一段时间向 follower 发送心跳信息，follower 如果一段时间没有收到 leader 的心跳，将发起选举。
  通过 `raftElectionTick` 可以设置在 [raftElectionTick, 2*raftElectionTick] 之间的一个随机时间后未收到 leader 的心跳将发起选举，默认值为800，单位是10ms。

- RaftInputWorker

  从输入消息队列取出消息应用到当前节点的线程。

- RaftOutputWorker

  从输出消息队列取出消息并应用到相应节点的线程。

- RaftProposeWorker

  处理对 raftLog 读写请求的线程。

- SnapshotSender

  将 leader 当前状态的快照发送给其他节点的线程。

- RaftLeaderSwitchWorker

  执行 raft 节点角色切换的线程。

- DFSRaftReplayWorker

  将记录的 raftLog 应用到当前节点的线程。

## 6.其他

- ThreadPoolSocketGroup

  在 server 的端口上监听收到的消息请求，并交由相应的工作队列处理。每个节点有且仅有一个线程。

- BackgroundRoutineService

  server 的后台线程，每个节点会生成 4 个该线程。server 会在该线程中注册一些函数，这些函数会在BackgroundRoutineService 线程运行过程中每隔一段时间就被调用一次。

- LogWriter

  将节点运行过程中生成的 log 写入文件的线程。每个节点都有一个该线程。

- StdConsole

  启动 server 后在命令行窗口接收命令的线程。在 server 启动参数中如果设置 console=true，那么就会启动一个该线程。
# DolphinDB教程：高性能集群配置

DolphinDB提供了一系列配置选项，方便用户进行配置，以充分利用机器硬件资源（包括CPU、内存、磁盘、网络等）。合理的参数配置，可以使系统均衡合理的使用这些资源，最大化发挥硬件的性能。配置选项分为以下几类：
- 计算：workerNum, localExecutors, maxBatchJobWorker, maxDynamicWorker, webWorkerNum, persistenceWorkerNum, subExecutors, recoveryWorkerNum, secondaryWorkerNum, urgentWorkerNum
- 内存：maxMemSize, chunkCacheEngineMemSize, regularArrayMemoryLimit, maxPersistenceQueueDepth, maxPubQueueDepthPerSite, maxSubQueueDepth
- 磁盘：volumes, diskIOConcurrencyLevel, persistenceDir, streamingHADir, dfsMetaDir, chunkMetadir, redoLogDir, logFile, batchJobDir, jobLogFile
- 网络：maxConnections, maxConnectionPerSite, tcpNoDelay, maxFileHandles, enableHttps, maxPubConnections, maxSubConnections
- 数据安全：dfsReplicationFactor, dataSync, dfsReplicaReliabilityLevel, dfsHAMode, streamingHAMode

要熟悉系统的详细配置，首先需要了解集群搭建流程。DolphinDB集群的搭建请参考[单服务器集群部署](./single_machine_cluster_deploy.md)或[多服务器集群部署](./multi_machine_cluster_deployment.md)。

## 1. 概述

DolphinDB 是一个功能强大，支持多用户的分布式数据库系统，同时集成了流数据、作业处理、分布式文件系统等功能，支持海量数据的高并发读写与流式计算。整个系统采用多线程架构，数据库文件的存储支持多种类型的分区。DolphinDB提供了很多选项来合理化配置集群，以最大化发挥机器的性能。从硬件资源和数据安全角度，配置项分为以下几类：

__计算__  

计算能力是数据库性能关键指标，DolphinDB内置分布式计算框架，在多用户并行使用时性能优异，系统提供了设置各种任务（批处理任务、web请求、客户端请求、数据恢复任务）的配置选项。对流计算，还提供了对持久化数据以及订阅处理任务并发度设置。

__内存__  

为充分利用内存，DolphinDB使用自研的内存管理系统。可配置最大可用内存，并且提供对各种队列（cacheEngine、持久化队列、发布队列、订阅队列）的配置选项。

__磁盘__  

读写数据往往是整个系统的性能瓶颈。DolphinDB提供选项来配置系统可用的磁盘卷，利用多个磁盘的并行读写能力，保证最优的IO吞吐量。DolphinDB提供各种不同类型的日志包括元数据日志、redoLog日志、查询日志、系统运行日志、后台任务日志。不同类型的日志需要的数据安全级别也不同。元数据与redoLog日志需要确保持久化到磁盘上，因此建议存储在SSD或者高性能IO设备上，其他的监控类日志可以存储到HDD。

__网络__  

对于分布式系统，网络本身的时延和吞吐量对系统性能影响极大。网络性能主要是由基础硬件决定，如果有多台服务器，服务器间应使用万兆以太网连接。DolphinDB提供了一些对连接数控制的选项，来合理的控制系统资源消耗。

__数据安全__ 

DolphinDB提供数据、元数据以及客户端的高可用方案。DolphinDB采用多副本机制，当数据库节点发生故障时，数据库依然可以正常运作，保证业务不会中断。提供控制节点高可用模式，通过构建多个控制节点来组成一个Raft组，只要宕机的控制节点少于半数，集群仍然可提供服务。DolphinDB API提供了自动重连和切换机制，在节点宕机，用户不需要干预的情况下，自动进行重连或者切换。细节可参考[DolphinDB高可用集群部署教程](./ha_cluster_deployment.md)

DolphinDB的典型应用场景包括：作为分布式时序数据库，提供入库和查询功能；作为稳定的流数据发布中心，提供来自各种应用的订阅服务。下面分别介绍DolphinDB作为数据库和作为流数据发布中心的配置选项。

## 2. 数据库相关配置

作为时序数据库系统，是DolphinDB最典型的应用场景，数据库提供多用户并发读写能力，和数据库相关的配置选项如下。

### 2.1 计算配置选项

DolphinDB架构采用多线程技术，合理的并发度能极大提升系统性能。并发度太低，不能充分利用系统硬件的多线程能力，并发度太高，容易导致过多的线程切换，造成总体性能降低。影响并发度的主要参数如下:  

* workerNum: worker负责接收客户端请求，分解任务，根据任务粒度自己执行或者交给executor执行。该参数直接决定了系统的并发能力，根据主机的CPU核数，以及部署的DolphinDB节点个数来配置， 默认为主机的CPU核数。  

* localExecutors: localExecutor负责执行woker分解的任务。和workerNum类似，直接决定了系统的并发度，推荐默认为workerNum-1。  

* maxBatchJobWorker: batchJob Worker 执行批处理任务，这些任务是指通过submitJob函数提交的任务，通常耗时较长。该参数决定了执行批处理任务的并发度。根据系统执行批处理任务的多少来确定。 
注意：如果没有批处理任务，创建的线程会回收，所以并不会占用系统资源，默认为workerNum。  

* maxDynamicWorker: dynamic worker作为上面介绍的worker的补充，当所有的worker线程占满后，如果新的任务进来，则会创建dynamic worker来执行，并且任务完毕后会释放资源，默认为workerNum。  

* webWorkerNum: web worker处理http请求，该参数表示处理http请求的线程数目。web的连接可以通过集群管理器界面，连接到某个节点的notebook进行交互式操作，默认为1。  

* recoveryWorkerNum: 数据节点recovery任务执行的线程数，默认为1。如果系统需要进行recovery的任务较多，那么该参数可以适当设置的较大，比如4。默认为1。  

* secondaryWorkerNum: 二级worker线程数。引入该配置项是为了解决节点间的任务循环依赖而导致的死锁问题。比如节点A向节点B发送任务t，任务t产生的子任务可能会再发送到节点A,如果发送到A的worker上容易产生死锁，所以，这种情况下，会发送到A的secondary worker上执行，默认为workerNum。

* urgentWorkerNum: 紧急任务处理线程数，比如心跳任务等，确保系统任务重的情况下，心跳线程也不阻塞，默认为1。  

上面的选项配置系统的整体并发计算能力。同时，DolphinDB也提供了通过函数来设置某个用户执行任务的最大优先级和并行度，具有较高优先级的任务会有更多的机会和资源执行，从应用的层面来提高某些任务的计算并发度和优先级。

* setMaxJobPriority: 优先级范围是0-8，高优先级可以获取更多的执行时间和机会。任务的默认优先级为 4。

* setMaxJobParallelism: 并行度范围是0-64，高并行度可以更好地利用机器的多核资源，并发执行任务。任务的并行度默认为2。

### 2.2 内存配置选项

* maxMemSize: 节点使用的最大内存量，应该根据系统实际的物理内存，以及节点的个数来合理的设置该值。设置的越大，性能以及系统的处理能力越大，但如果设置值超出了系统提供的内存大小，则有可能会被操作系统杀掉。比如操作系统实际的物理内存是16G，该选项设置为32G，那么运行过程中，有可能被操作系统默默杀掉。 

* chunkCacheEngineMemSize: 指定cache engine的容量（单位为GB）。cache engine开启后，写入数据时，系统会先把数据写入缓存，当缓存中的数据量达到chunkCacheEngineMemSize的30%时，才会写入磁盘。默认值是0，即不开启cache engine。开启cache engine的同时，必须设置dataSync=1。

* regularArrayMemoryLimit: DolphinDB提供普通数组(array)和大数组(bigArray)两种数组类型，array要求连续内存，优点是性能稍高，缺点是如果要求的内存太大，系统可能由于无法提供连续的内存而分配失败；bigarray不要求连续内存，优点是可以利用碎片小内存提供大的内存请求，缺点是性能会稍差。该参数设置普通数组array的最大内存上限（以MB为单位），如果超过该限制，那么array定义的变量内部会采用bigArray方式分配内存。常用的使用场景中，该参数对性能影响非常有限，因此建议默认设置512。  

### 2.3 磁盘配置选项

* volumes: 分布式数据库存储分区数据的位置，如果系统有多个volume，建议每个节点配置成不同的volume，这样DolphinDB从系统读写数据，可以并行的利用多个磁盘的I/O接口，大大提升读写数据的速度。

* diskIOConcurrencyLevel: 磁盘I/O并行参数，该值可以设置为每个节点可以使用的磁盘volumes的数量。

DolphinDB 系统记录多种类型的日志，有节点运行情况的日志，数据库元数据日志，redoLog的日志，查询query的性能日志。为了确保系统在异常情况（比如断电等）下的数据安全，有些日志必须同步确保已经持久化到磁盘上。而监控类日志，则不需要严格同步。总体原则是建议需要同步写入磁盘的log采用ssd或者高性能IO设备，监控类log可以采用hdd设备。具体设置建议如下:  

* dfsMetaDir: 保存控制器节点上的分布式文件系统的元数据,默认值是由home参数指定的主目录，建议设置到SSD上。

* chunkMetaDir: 保存数据节点上元数据，默认目录是<HomeDir>/storage/CHUNK_METADATA。在集群模式中，应当为每个数据节点配置不同的chunkMetaDir，建议设置到SSD上。

* redoLogDir: redo log的存储目录，为了防止断电后数据丢失，在写数据库前，先写redo log。默认值是<HomeDir>/log/redoLog，建议设置到SSD上。

* logFile: 各个节点的运行日志，记录节点的运行状态、错误信息等，可以设置到HDD磁盘上。 

* batchJobDir: 批处理任务的日志目录，例如submiJob提交的任务日志，可以设置到HDD磁盘上。

* jobLogFile: 各个节点的query日志，记录各个query的执行情况，可以设置到HDD磁盘上。  


### 2.4 网络配置选项

* maxConnections: 可接受的最大连接数。DolphinDB每个实例收到用户请求后会建立一个连接，来完成用户任务。该选项越大，可以同时接受处理外部请求越多。该选项默认为 32 + maxConnectionPerSite * 节点数。

* maxConnectionPerSite: 对外某一个节点的最大连接数。DolphinDB数据是分布式存储的，每个节点需要和其他节点进行连接通信，该选项指明该节点和任一其他节点所能建立的最大连接数。默认是 localExecutors + workerNum + webWorkerNum，推荐使用默认设置。

* tcpNoDelay: 使能TCP的 TCP_NODELAY 选项，可以有效的降低请求的时延。推荐默认设置为true。  

* maxFileHandles: 系统打开文件（包括普通文件和socket连接）的最大个数，一般linux默认1024，当集群规模较大时，可对该参数进行配置。也可以直接对操作系统配置该参数。  

* enableHttps: 对于web连接是否启用https安全协议，默认为false。

### 2.5 数据安全配置选项

* dfsReplicationFactor: 分布式数据库的副本数，该值对系统性能和存储空间都有较大影响。推荐设置为2，一方面保证数据的高可用，另一方面两个副本，可以起到负载均衡的作用，读数据时从负载较低的节点读取，提高系统整体性能。如果磁盘存储空间非常有限，不能提供2副本的空间，可以设置为1。 

* dfsReplicaReliabilityLevel: 数据库不同的副本是否写到同一台物理机器上。若设置为1，表示不同的副本必须写入到不同的物理机器上，是真正的“分布式”；若设置为0，表示不同的副本可以写入到同一台服务物理机器上，是“伪分布式”。一般在测试调试环境或者对数据安全要求不高的环境，可以设置为0，而在生产环境中，对数据安全性高的场景下，建议设置为1。

* dataSync: 默认为0，数据库日志在事务提交前是否强制持久化到磁盘。若dataSync取值为1，每个事务提交前必须将数据库日志（包括redo log，undo log，数据节点的edit log，以及控制节点的edit log）写入磁盘，写入的数据在出现操作系统崩溃或系统掉电的情况下不会丢失。若dataSync取值为0，事务提交前只是保证将数据库日志写入操作系统缓存页面，由操作系统择时写入磁盘。在不可靠的环境中，存在数据丢失和数据库被破坏的风险。 

* dfsHAMode: 默认不启用Raft mode，控制节点的高可用模式。如果对控制节点高可用要求高，需要配置该选项，消除控制节点的单点故障。

* streamingHAMode: 默认不启用Raft mode，流节点的高可用模式。如果流数据节点有高可用要求，则需要配置该选项，启用高可用模式。

> __注意__: 数据库的分区设计对查询的性能影响很大。若分区过大，会造成并行加载容易出现内存不足，从而造成操作系统频繁对内存和磁盘进行数据交换，大大降低降低性能。若分区过小，会造成系统中存在大量的子任务，导致节点间产生大量的通信和调度，并且还会频繁的访问磁盘上的小文件，也会明显降低性能。请参考[分区数据库教程](./database.md)

## 3. 流计算模块高性能配置  

流数据作为一个较为独立的功能模块，有些配置选项专门为流计算设计，大部分场景默认配置能满足要求。如果用户对流数据的性能要求高，需要一些定制化配置，可以参考如下配置选项。

### 3.1 发布节点配置选项  

* persistenceWorkerNum: 异步持久化模式下，负责将数据发布表持久化到磁盘上的线程数。如果启用了持久化功能，则会将发布的数据同步或者异步的方式持久化到磁盘上。函数`enableTablePersistence`的第二个参数指定了是同步还是异步的方式持久化。同步保证消息不会丢失，而异步方式则会大大提升系统的吞吐量。因此，如果应用场景能容忍发布节点异常宕机时丢失最后几条消息，建议设置为异步持久化。

* persistenceDir: 流数据表持久化数据保存的目录。推荐设置为SSD或者独立的HDD磁盘卷作为持久化目录，以提高持久化的IO处理能力。

* maxPersistenceQueueDepth: 流表持久化队列的最大消息数。对于异步持久化的发布流表，先异步的将数据放到持久化队列中，然后负责持久化的线程（persistenceWorkerNum设置持久化线程数）不断的将队列中的消息持久化到磁盘上。该选项指明了，该流表持久化队列中的最大消息条数。默认值为10000000。

* maxPubQueueDepthPerSite: 最大消息发布队列深度。针对某个订阅节点，发布节点建立一个消息发布队列，该队列中的消息发送到订阅端。该选项设置该发布节点针对某个订阅节点的消息发布队列的最大深度。默认值为10000000。

* maxPubConnections: 最大的发布-订阅连接数。一个订阅节点和一个发布节点之间（可能订阅该节点的多张流表）建立1个发布-订阅连接。该选项指定能够订阅该发布节点上流表的最大订阅节点的个数。例如设置为8，则最多有8个订阅节点来订阅该发布节点上的流表。

* streamingHADir: 流数据Raft日志文件的存储目录。Raft日志包括注册表、删除表、append（追加）数据等信息。为保证断电后不丢失数据，DolphinDB会调用fsync把日志刷到磁盘上。建议这个目录配置在SSD上。默认值为<HomeDir>/log/streamLog。如果在同一个服务器上部署了多个数据节点，每个节点应当配置不同的streamingHADir。

> __注意__: 发布表的持久化函数`enableTablePersistence(table, [asynWrite=true], [compress=true], [cacheSize=-1])`中以下参数的设置，对性能影响很大。
> asynWrite: 流数据是否异步持久化。异步持久化会显著提升系统性能，代价是宕机的时候，可能会造成最后几条消息丢失。可容忍的场景下，建议设为true。  
> compress: 持久化到磁盘的数据是否压缩。如果压缩，数据量很降低很多，同时减少磁盘写入量，提升性能，但压缩解压有一定代价，建议设为true。  
> cacheSize: 流表中保存在内存中数据的最多条数。较大的该值会提升实时查询与订阅的性能。根据服务器内存总量合理分配，建议大于1000000。

### 3.2 订阅节点配置选项

* subExecutors: 订阅节点处理流数据的线程数。每个流数据表只能在1个executor上处理，所以根据该节点上订阅流表的多少，来设置该值。另外，一个订阅只能在一个线程上执行，一个线程也可以执行多个订阅。默认值为 1。

* maxSubQueueDepth: 订阅节点上每个订阅线程最大的可接收消息的队列深度。订阅的消息，会先放入订阅消息队列，该值指明该队列的大小。默认设置为10000000。

* maxSubConnections: 订阅节点的最大订阅连接数。如果一个节点订阅同一个发布节点上的多张流表，那么这些流表共享一个连接，默认为64。  

> __注意__: 订阅函数`subscribeTable([server], tableName, [actionName], [offset=-1], handler, [msgAsTable=false], [batchSize=0], [throttle=1], [hash=-1])`的以下参数对性能有很大影响：
> batchSize: 触发handler处理消息的累计消息量（行数）阈值。业务允许情况下，尽量调高该值，批量处理会显著提升系统吞吐量。    
> throttle: 触发handler处理消息的时间（秒）阈值。如果batchSize也设置，那么不管哪个先满足条件，都会触发handler计算。  
> handler: 处理流数据的函数。该函数应高度优化，尽量采用向量化编程。因为会多次调用，对性能影响很大。  


## 4. 典型服务器配置实例

### 4.1 数据库配置

一台物理服务配置：24CPU核，48线程；内存256G；SSD 480G，HDD 1.8T\*12。作为历史数据仓库，提供数据入库以及查询功能。可靠性方面，不要求7*24小时在线，允许偶尔宕机，几分钟能恢复并继续提供服务即可。

- 部署设计：由于只有一台物理机，显然可靠性方面没有非常严苛，因此从性能以及运维方便性角度，我们采用单机模式（singe mode），只包括1个DolphinDB实例。并且程序部署在SSD上，这样方便各种log的配置。
> __注意__: single mode 模式下，不能在后期增加机器（节点），而集群模式下，可以方便的增加机器（节点）。

- 内存设置：  
    - maxMemSize=200：操作系统以及其他进程保留50G左右。
    
- 线程设置：  
    - workerNum=32：workerNum加上localExecutors以及DolphinDB系统内的其他线程大于机器总线程48。因为实际中，很少有任务可以把所有线程占用，所以这样配置也是合理的。  
    - localExecutors=31：通常来说，localExecutors 设置为 workerNum-1 为最优。这是因为worker接受到任务，分配给executor，worker本身也可以执行该任务。

- 磁盘设置：   
    - volumes: /hdd/hdd1,/hdd/hdd2,..../hdd/hdd12, 12个volume都利用起来，可以最大化系统的吞吐量。  
    - diskIOConcurrencyLevel=12：与volumes的个数一致。  

- 网络设置：   
    - tcpNoDelay=true：采用默认设置true。  
    - maxConnections=64：该节点支持的接入的最多连接数，一般根据接入客户端的多少来设置，比如GUI, web, API等都是独立的连接，本例设置为64。 

- 启用cacheEngine：    
    - chunkCacheEngineMemSize=30：提升写入性能。

- 启用redoLog：
    - dataSync=1：保证数据库在断电或者操作系统崩溃的情况下的数据完整性。  

- log目录配置：   
    - dfsMeta=/ssd/dfsMetaDir：controller元数据目录，配置在SSD上。  
    - chunkMetadir=/ssd/chunkMetaDir：数据节点元数据目录，配置在SSD上。  
    - redoLogDir=/ssd/redoLogDir：redo log的数据目录，配置在SSD上。

下例是集群模式的服务器配置。3台物理服务器，每台12core，24线程，内存128G，SSD 480G，HDD 1.8T\*8。作为历史数据仓库，提供数据入库以及查询功能。 

- 部署设计：由于有3台物理机，采用集群模式，包括1个控制节点，3个代理节点（每个服务器1个），6个数据节点（每个服务器2个）。其中1台服务器部署1个控制节点与两个数据节点，另外两个服务器各配置2个数据节点。

- 内存设置：控制节点分配10G内存，每个数据节点分配45G内存；只部署数据节点的机器，数据节点可配置50G内存。

- 线程设置：  
    - workerNum=8  
    - localExecutors=7 

- 磁盘设置：每个数据节点设置4个volume。

- 网络设置：  
    - tcpNoDelay=true: 采用默认设置true。  
    - maxConnections=64: 该节点支持的最大接入进来的连接数，一般根据接入客户端的多少来设置，比如GUI, web, API等都是独立的连接，本例设置为64。 


- 启用cacheEngine：   
    - chunkCacheEngineMemSize=10：提升写入性能。   


- 启用redoLog：  
    - dataSync=1：保证数据库在断电或者操作系统崩溃的情况下的数据完整性。  


- log目录配置：
    - dfsMeta=/ssd/dfsMetaDir：controller元数据目录，配置在SSD上。  
    - chunkMetadir=/ssd/chunkMetaDir：数据节点元数据目录，配置在SSD上。  
    - redoLogDir=/ssd/redoLogDir：redo log的数据目录，配置在SSD上。


### 4.2 流计算配置

基于稳定性考虑，生产环境的流数据中心一般与历史数据库分开部署，部署到独立的物理机器上（集群或者单节点方式部署）。下面以金融领域为例，介绍一种典型的部署场景。

物理服务配置：8CPU核，16线程；内存64G；磁盘1.0T\*4；流数据表包括：期货、期权、股票指数、逐笔委托、股票、逐笔成交，前面三张数据量比较小，每秒几百条，后面三张每秒1万条左右。

- 发布节点部署设计：采用single mode，单节点处理上面的数据量没有问题。

- 参数配置：
    - maxMemSize=50：分配内存上限为50G。
    - workerNum=8   
    - localExecutors=7  
    - maxPubConnections=32：表示信息发布节点最多可连接的订阅节点数量。该节点发布表较多，可能有来自多个DlphinDB节点或其他客户端的订阅，因此设置为32。  
    - persistenceDir: 每个节点设置为一个单独的磁盘卷，这样持久化时可以并发写入。  
    发布队列深度、持久化线程数以及队列深度按照默认配置即可。  
> 注意定义每张发布流表的持久化参数，enableTablePersistence，对性能和内存影响极大，每个参数应根据数据量和性能需求仔细评估配置，可参考3.1节。流数据性能调优的更多细节请参考教程[流数据教程](./streaming_tutorial.md)

订阅端可以是各种API客户端，或者DolphinDB server。如果是DolphinDB server作为订阅客户端，性能相关的主要参数为subExecutors, maxSubQueueDepth 与 maxSubConnections。subExecutors根据订阅表数量配置，其他两个参数可以采用默认值。

## 5. 性能监控  

DolphinDB database提供了各种工具来监控集群的性能。包括控制节点和各个数据节点的资源占用、查询性能、流数据性能等指标。方便用户实时监控系统的资源和性能。

### 5.1 集群管理器

集群管理器可以监控到30多个性能指标。比较常用的包括各个节点的CPU利用率、平均负载、内存使用量、连接数、query查询统计、任务队列深度、磁盘写入速度、磁盘读取速度、网络接收速率、网络发送速率等。相关指标如下：

* CPU使用率：CpuUsage, AvgLoad

* 内存监控：MemUsed, MemAlloc, MemLimit

* 磁盘监控：DiskCapacity, DiskFreeSpaceRatio, DiskWriteRate, DiskReadRate, LastMinuteWriteVolume, LastMinuteReadVolume

* 网络监控：NetworkSendRate, NetworkRecvRate, LastMinuteNetworkSend, LastMinuteNetworkRecv

* 实时查询性能指标：MedLast10QueryTime, MaxLast10QueryTime, MedLast100QueryTime, MaxLast100QueryTime20, MaxRunningQueryTime, RunningJobs, QueuedJobs, RunningTasks, QueuedTasks, JobLoad

* 实时流数据性能指标：LastMsgLatency, CumMsgLatency

这些指标也可以通过函数`getClusterPerf()`以table的形式获取到。通过这些监控指标可以反映出整个集群的性能情况。比如CPU平均负载过大，说明CPU可能成为集群性能瓶颈；如果磁盘读取基本达到极限，说明IO限制了整体的性能；然后可以针对性能瓶颈进行配置调优。

### 5.2 流数据性能监控

使用`getStreamingStat()`函数可以获取到发布端和订阅端的流数据性能指标。该函数返回一个dictionary，包括发布和订阅端的性能指标。

#### 5.2.1 发布端性能指标

* pubTables: 该节点所有的发布连接，以及每个连接当前发布的msgOffset，每行代表一个topic(订阅节点，发布节点，订阅表名，订阅action名）。该msgOffset是指该发布表在这个topic的当前发布位置。

* pubConns: 与pubTables相似，区别是每行代表一个client端的所有订阅，即这个client在该发布节点订阅的所有表。通过queueDepth可以观察消息的积累程度，如果该值很大，说明发布的队列消息积累严重。可能网络传输慢，发送数据量太大，或者消息被订阅端消费的太慢。

#### 5.2.2 订阅端性能指标

* subConns: 统计发布端到订阅端消息的时延等信息。每行代表一个发布端，统计指标包括某个发布端向该订阅端，发布的消息总数，累计的时延，最后一条消息的时延。如果时延太长，有可能是不在同一台物理机器上，两个机器的时间有差异；还有可能是网络本身时延较高；

* subWorkers: 每个subWorker处理消息的统计信息。subWorker的个数由上面subExecutors指定，统计指标包括累积消息的队列深度，已经处理的消息个数等。如果queueDepth太大，或者达到queueDepthLimit值，说明该订阅消费消息太慢，导致消息积累。需要优化消息处理的handler，以更快的处理消息。

### 5.3 内存使用性能监控函数

* `getClusterPerf()`: 显示集群中各个节点或者single mode单节点内存占用情况，包括内存使用总量、内存分配总量、最大内存分配限制。  

* `getSessionMemoryStat()`: 返回该节点的不同用户的内存使用总量。如果碰到内存超限，可以使用该函数，排查哪个用户占用过多内存。   

* `mem()`: 可以显示整个节点的内存分配和占用情况。该函数输出4列，其中列blockSize表示分配的内存块大小，freeSize表示剩余的内存块大小，通过sum(mem().blockSize - mem().freeSize) 得到节点所使用的总的内存大小。

* `memSize()`: 查看某个对象占用内存量，单位为字节。  

* `getMemoryStat()`: 从系统级查看本节点的内存使用量概述，包括分配的页数，空闲页数，分配的内存总大小，空闲的内存大小。

更多细节请参考[内存管理教程](./memory_management.md)。



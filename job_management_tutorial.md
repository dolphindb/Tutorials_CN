# DolphinDB作业管理

作业（Job）是DolphinDB中最基本的执行单位，可以简单理解为一段DolphinDB脚本代码在DolphinDB系统中的一次执行。作业根据阻塞与否可分成同步作业和异步作业。

### 同步作业

也称为交互式作业（Interactive Job），同步任务的主要来源：

- Web notebook
- DolphinDB GUI
- DolphinDB命令行界面
- 通过DolphinDB提供的各个编程语言API接口

由于此类作业对实时性要求较高，DolphinDB在执行过程中会自动给予较高的优先级，使其更快得到计算资源。

### 异步作业

异步作业是在DolphinDB后台执行的作业，包括：

- 通过`submitJob`或`submitJobEx`函数提交的[**批处理作业**](https://www.dolphindb.cn/cn/help/BatchJobManagement.html)。
- 通过`scheduleJob`函数提交的[**定时作业**](https://www.dolphindb.cn/cn/help/ScheduleJobs.html)。
- Streaming作业。

这类任务一般对结果的实时反馈要求较低，且需要长期执行，DolphinDB一般会给予较低的优先级。

### 子任务

在DolphinDB中，若数据表数据量过大，一般都需要进行[分区处理](https://www.dolphindb.cn/cn/help/DistributedDatabase.html)。如果一个Job A里含有分区表的查询计算任务（如SQL查询），系统会将其分解成多个子任务并发送到不同的节点上并行执行，等待子任务执行完毕之后，再合并结果，继续Job A的执行。类似的，DolphinDB[分布式计算](https://www.dolphindb.cn/cn/help/DistributedComputing.html)也会产生子任务。因此，Job也可以理解成一系列的子任务。

### Worker与Executor

DolphinDB是一个P2P架构的系统，即每一个Data Node的角色都是相同的，它们都可以执行来自用户提交的Job，而因为一个Job可能产生子任务，每个Data Node需要有负责Job内部执行的调度者，我们称它为Worker，它负责处理用户提交的Job，简单计算任务的执行，并执行Job的任务分解以及任务分发，并汇集最终的执行结果。Job中分解出来的子任务将会被分发到集群中的Data Node上（也有可能是本地Data Node），并由Data Node上的Worker或Executor线程负责执行。

Worker与executor在执行Job的时候主要有以下几种情况：

1. 查询一个未分区表的Job会被Worker线程执行。

2. 查询一个单机上的分区表的Job可能会分解成多个子任务，并由该节点上的多个Executor线程并行执行。

3. 查询一个DFS分区表的Job可能会被分解成多个子任务，这些子任务会被分发给其它Node的Worker执行，进行分布式计算。

为了最优性能，DolphinDB database 会将子任务发送到数据所在的Data Node上执行，以减少网络传输开销。比如：

- 对于存储在DFS中的分区表，Worker将会根据分区模式以及分区当前所在Data Node来进行任务分解与分发。
- 对于分布式计算，Worker将会根据数据源信息，发送子任务到相应的数据源Data Node执行。

### Job调度

#### Job优先级

在DolphinDB中，Job是按照优先级进行调度的，优先级的取值范围为0-9，取值越高则优先级越高。对于优先级高的Job，系统会更优先的给与计算资源。每个Job一般会有一个取值为4的默认优先级，根据Job的类型又会有所调整。

#### Job调度策略

基于Job的优先级，DolphinDB设计了多级反馈队列来调度Job的执行。具体来说，系统维护了10个队列，分别对应10个优先级。系统总是分配线程资源给高优先级的Job，对于处于相同优先级的Job，系统会以round robin的方式分配线程资源给Job；当一个优先级队列为空的时候，才会处理低优先级的队列中的Job。

#### Job并行度

由于一个Job可能会分成多个并行子任务，DolphinDB的Job还拥有一个并行度parallelism，表示在一个Data Node上，将会最多同时用多少个线程来执行Job产生的并行任务，默认取值为2，可以认为是一种时间片单位。举个例子，若一个Job的并行度为2，Job产生了100个并行子任务，那么Job被调度的时候系统只会分配2个线程用于子任务的计算，因此需要50轮调度才能完成整个Job的执行。

#### Job优先级的动态变化

为了防止处于低优先级的Job被长时间饥饿，DolphinDB会适当降低Job的优先级。具体的做法是，当一个Job的时间片被执行完毕后，如果存在比其低优先级的Job，那么将会自动降低一级优先级。当优先级到达最低点后，又回到初始的优先级。因此低优先级的任务迟早会被调度到，解决了饥饿问题。

#### 设置Job的优先级

DolphinDB的Job的优先级可以通过以下方式来设置：

- 对于console、web notebook以及API提交上来的都属于interactive job，其优先级取值为min(4，一个可调节的用户最高优先级)，因此可以通过改变用户自身的优先级值来调整。
- 对于通过submitJob提交上的batch job，系统会给与默认优先级，即为4。用户也可以使用[submitJobEx](https://www.dolphindb.cn/cn/help/submitJobEx.html?search=submitJobEx)函数来指定优先级。
- 定时任务的优先级无法改变，默认为4。


### 计算容错

DolphinDB的分布式计算含有一定的容错性，这主要得益于分区副本冗余存储。当一个子任务被发送到一个分区副本节点上之后，若节点出现故障或者分区副本发生了数据校验错误(副本损坏），Job Scheduler(即某个Data Node的一个Worker线程)将会发现这个故障，并且选择该分区的另一个副本节点，重新执行子任务。你可以通过[设置dfsReplicationFactor](https://www.dolphindb.cn/cn/help/ClusterSetup.html?search=replication)来调整这种冗余度。


### 计算与存储耦合以及作业之间的数据共享

DolphinDB的计算尽量靠近存储。DolphinDB之所以不采用计算存储分离，主要有以下几个原因：

1. 计算与存储分离会出现数据冗余。考虑存储与计算分离的Spark+Hive架构，Spark应用程序之间是不共享存储的。若N个Spark应用程序从Hive读取某个表T的数据，那么首先T要加载到N个Spark应用程序的内存中，存在N份，这将造成机器内存的的浪费。在多用户场景下，同一份数据可能会被多个分析人员共享访问，如果采取Spark模式，会大大提高IT成本。

2. 拷贝带来的延迟问题。虽然现在有些数据中心逐渐配备了RDMA，NVMe等新硬件，显著改善了网络延迟和吞吐，但是这主要还是在数据中心。DolphinDB系统的部署环境可能没有这么好的网络环境以及硬件设施，数据在网络之间的传输会成为严重的性能瓶颈。

综上这些原因，DolphinDB采取了计算与存储耦合的架构。具体来说：

1. 对于内存浪费的问题，DolphinDB的解决方案是Job（对应Spark应用程序）之间共享数据。在数据经过分区存储到DolphinDB的DFS中之后，每个分区的副本都会有自己所属的节点，在一个节点上的分区副本将会在内存中只存在一份。当多个Job的子任务都涉及到同一个分区副本时，该分区副本在内存中可以被共享地读取，减少了内存的浪费。

2. 对于拷贝带来的延迟问题，DolphinDB的解决方案是将计算发送到数据所在的节点上。一个Job根据DFS的分区信息会被分解成多个子任务，发送到分区所在的节点上执行。因为发送计算到数据所在的节点上相当于只是发送一段代码，网络开销大大减少。
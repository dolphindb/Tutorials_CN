# DolphinDB 教程：金融市场高频数据的有效管理

- [DolphinDB 教程：金融市场高频数据的有效管理](#dolphindb-教程金融市场高频数据的有效管理)
  - [1. DolphinDB与pickle的性能对比测试和分析](#1-dolphindb与pickle的性能对比测试和分析)
  - [2. 测试场景和测试数据](#2-测试场景和测试数据)
  - [3. 测试环境](#3-测试环境)
  - [4. 测试方法](#4-测试方法)
    - [4.1. 测试DolphinDB](#41-测试dolphindb)
    - [4.2. 测试DolphinDB的Python API](#42-测试dolphindb的python-api)
    - [4.3. 测试pickle文件](#43-测试pickle文件)
  - [5. 测试结果分析](#5-测试结果分析)
    - [5.1. DolphinDB的性能优势来源](#51-dolphindb的性能优势来源)
    - [5.2. 字符串对性能的影响](#52-字符串对性能的影响)
    - [5.3. 多任务并发下的性能对比](#53-多任务并发下的性能对比)
  - [6. 库内分析的必要性](#6-库内分析的必要性)
  - [7. 结论和展望](#7-结论和展望)

## 1. DolphinDB与pickle的性能对比测试和分析

金融市场L1/L2的报价和交易数据是量化交易研究非常重要的数据。国内全市场L1/L2的历史数据约为20\~50T，每日新增的数据量约为20\~50G。传统的关系数据库如MS SQL Server或MySQL均无法支撑这样的数据量级，即便分库分表，查询性能也远远无法达到要求。例如Impala和Greenplum的数据仓库，以及例如HBase的NoSQL数据库，可以解决这个数据量级的存储，但是这类通用的存储引擎缺乏对时序数据的友好支持，在查询和计算方面都存在严重的不足，对量化金融普遍采用的Python的支持也极为有限。

数据库的局限性使得一部分用户转向文件存储。HDF5，Parquet和pickle是常用的二进制文件格式，其中pickle作为Python对象序列化/反序列的协议非常高效。由于Python是量化金融和数据分析的常用工具，因此许多用户使用pickle存储高频数据。但文件存储存在明显的缺陷，譬如大量的数据冗余，不同版本之间的管理困难，不提供权限控制，无法利用多个节点的资源，不同数据间的关联不便，数据管理粒度太粗，检索和查询不便等等。

目前，越来越多的券商和私募开始采用高性能时序数据库DolphinDB来处理高频数据。DolphinDB采用列式存储，并提供多种灵活的分区机制，可充分利用集群中每个节点的资源。DolphinDB的大量内置函数对时序数据的处理和计算非常友好，解决了传统关系数据库或NoSQL数据库处理时序数据方面的局限性。使用DolphinDB处理高频数据，既可以保证查询与计算的超高性能，又可以提供数据管理、权限控制、并行计算、数据关联等数据库的优势。

本文测试DolphinDB和pickle在数据读取方面的性能。与使用pickle文件存储相比，直接使用DolphinDB数据库，数据读取速度可最多可提升10倍以上；若为了考虑与现有Python系统的集成，使用DolphinDB提供的Python API读取数据，速度最多有2~3倍的提升。


## 2. 测试场景和测试数据

本次测试使用了以下两个数据集。
- 数据集1是美国股市一天(2007.08.23) Level 1的报价和交易数据。该数据共10列，其中2列是字符串类型，其余是整型或浮点数类型，存储在dolphindb中的表结构如下表，一天的数据约为2亿3000万行。csv文件大小为9.5G，转换为pickle文件后大小为11.8G。

  | 列名   | 类型   |
  | ------ | ------ |
  | symbol | SYMBOL |
  | date   | DATE   |
  | time   | SECOND |
  | bid    | DOUBLE |
  | ofr    | DOUBLE |
  | bidsiz | INT    |
  | ofrsiz | INT    |
  | mode   | INT    |
  | ex     | CHAR   |
  | mmid   | SYMBOL |

- 数据集2是中国股市3天(2019.09.10~2019.09.12)的Level 2报价数据。数据集总共78列，其中2列是字符串类型，存储在dolphindb中的表结构如下表，一天的数据约为2170万行。一天的csv文件大小为11.6G，转换为pickle文件后大小为12.1G。

  | 列名        | 类型   | 列名               | 类型   |
  | ----------- | ------ | ------------------ | ------ |
  | UpdateTime  | TIME   | TotalBidVol        | INT    |
  | TradeDate   | DATE   | WAvgBidPri         | DOUBLE |
  | Market      | SYMBOL | TotalAskVol        | INT    |
  | SecurityID  | SYMBOL | WAvgAskPri         | DOUBLE |
  | PreCloPrice | DOUBLE | IOPV               | DOUBLE |
  | OpenPrice   | DOUBLE | AskPrice1~10       | DOUBLE |
  | HighPrice   | DOUBLE | AskVolume1~10      | INT    |
  | LowPrice    | DOUBLE | BidPrice1~10       | DOUBLE |
  | LastPrice   | DOUBLE | BidVolume1~10      | INT    |
  | TradNumber  | INT    | NumOrdersB1~10     | INT    |
  | TradVolume  | INT    | NumOrdersS1~10     | INT    |
  | Turnover    | DOUBLE | LocalTime          | TIME   |
  
DolphinDB的数据副本数设为2。将这两个数据集写入DolphinDB后，磁盘占用空间为10.6G，单份数据仅占用5.3G，压缩比约为8:1。pickle文件没有采用压缩存储。测试发现pickle文件压缩后，加载时间大幅延长。

对比测试查询一天的数据。对DolphinDB Python API与pickle，记录从客户端发出查询到接收到数据并转换成Python pandas的DataFrame对象的耗时。
- 对于DolphinDB Python API，整个过程包括三个步骤：（1）从DolphinDB数据库查询数据耗时，即若不使用Python API而直接使用DolphinDB查询所需耗时；（2）把查询到的数据从DolphinDB数据节点发送到python API客户端需要的时间；(3) 在客户端将数据反序列化成pandas DataFrame需要的时间。
- 对于pickle，耗时为使用pickle模块加载pickle数据文件所需要的时间。

## 3. 测试环境

测试使用的三台服务器硬件配置如下：

- 主机：PowerEdge R730xd
- CPU：E5-2650  24cores 48线程
- 内存：512G
- 硬盘：HDD 1.8T * 12
- 网络：万兆以太网
- OS：CentOS Linux release 7.6.1810

本次测试使用的是DolphinDB多服务器集群模式，配置如下：

- 共使用3台服务器
- 每台服务器部署2个数据节点
- 每个节点分配2个10K RPM的HDD磁盘
- 内存使用限制为32G
- 线程数设置为16
- 数据库的副本数设置为2
- 测试的客户机安排在其中的一台服务器上。

本次测试的DolphinDB服务器版本是1.30.0，Python API for DolphinDB的版本是1.30.0.4。

## 4. 测试方法

读写文件之后，操作系统会缓存相应的文件。从缓存读取数据，相当于从内存读取数据，这会影响测试结果。因此每一次测试前，都会清除操作系统的缓存和DolphinDB
的缓存。为了对比，也测试有缓存时的性能，即不存在磁盘IO瓶颈时的性能。

### 4.1. 测试DolphinDB

测试代码如下：

```
＃读取Level 1数据集一天的数据
timer t1 = select * from loadTable("dfs://TAQ", "quotes") where TradeDate = 2007.08.23

＃读取Level 2数据集一天的数据
timer t2 = select * from loadTable("dfs://DataYesDB", "tick") where TradeDate = 2019.09.10
```

测试步骤如下：

（1）使用Linux命令`sudo sh -c "echo 1 > /proc/sys/vm/drop_caches"`清理操作系统缓存，可能需要在root用户下执行。

（2）执行`pnodeRun(clearAllCache)`清理DolphinDB的数据库缓存。

（3）执行查询脚本，此时为无操作系统缓存时的结果。

（4）再次执行`pnodeRun(clearAllCache)`清理DolphinDB的数据库缓存。

（5）再次执行查询脚本，此时为有操作系统缓存时的结果。

### 4.2. 测试DolphinDB的Python API

测试代码如下：

```python
import dolphindb as ddb
import pandas as pd
import time

s = ddb.session()
s.connect("192.168.1.13",22172, "admin", "123456")

＃读取Level 1数据集一天的数据
st1 = time.time()
quotes =s.run('''
select * from loadTable("dfs://TAQ", "quotes") where TradeDate = 2007.08.23
''')
et1 = time.time()
print(et1 - st1)

＃读取Level 2数据集一天的数据
st = time.time()
tick = s.run('''
select * from loadTable("dfs://DataYesDB", "tick") where TradeDate = 2019.09.10
''')
et = time.time()
print(et-st)
```

测试步骤如下：

（1）使用Linux命令`sudo sh -c "echo 1 > /proc/sys/vm/drop_caches"`清理操作系统缓存，可能需要在root用户下执行。

（2）执行`pnodeRun(clearAllCache)`清理DolphinDB的数据库缓存。

（3）执行查询脚本，此时为无操作系统缓存时的结果。

（4）再次执行`pnodeRun(clearAllCache)`清理DolphinDB的数据库缓存。

（5）再次执行查询脚本，此时为有操作系统缓存时的结果。

### 4.3. 测试pickle文件

pickle测试代码如下：

```
import dolphindb as ddb
import pandas as pd
import time
import pickle

s = ddb.session()
s.connect("192.168.1.13", 22172, "admin", "123456")
tick = s.run('''
select * from loadTable("dfs://DataYesDB", "tick") where TradeDate = 2019.09.10
''')
quotes =s.run('''
select * from loadTable("dfs://TAQ", "quotes")
''')

#将数据集1的Level 1的数据转换为pkl文件
quotes.to_pickle("taq.pkl")

#将数据集2的Level 2一天的数据转换为pkl文件
tick.to_pickle("level2.pkl")

#使用pickle模块读取数据集1的Level 1一天的数据
st1 = time.time()
f = open('taq.pkl', 'rb')
c = pickle.load(f)
et1 = time.time()
print(et1 - st1)
f.close()

#使用pickle模块读取数据集2的Level 2一天的数据
f = open('level2.pkl', 'rb')
st = time.time()
c = pickle.load(f)
et = time.time()
print(et - st)
f.close()
```

测试步骤：

（1）第一次执行测试代码，此为pickle无操作系统缓存时的结果。

（2）第二次执行pickle模块读取数据的脚本，此时为pickle有操作系统缓存时的结果。

## 5. 测试结果分析

以下是读取美国股市Level 1数据集的测试结果：

| 场景       | 无缓存　(秒) | 有缓存（秒） |
| ---------- | ------------ | ------------ |
| DolphinDB 数据库查询  | 6           | 6           |
| DolphinDB Python API  | 38           | 35           |
| pickle     | 72           | 34           |

以下读取中国股市Level 2数据集的测试结果：

| 场景       | 无缓存（秒） | 有缓存（秒） |
| ---------- | ------------ | ------------ |
| DolphinDB 数据库查询  | 5           | 5           |
| DolphinDB Python API  | 22           | 22           |
| pickle     | 70           | 20           |

### 5.1. DolphinDB的性能优势来源

从测试结果看，直接从DolphinDB数据库查询，速度最快，超过pickle查询的10倍以上。在没有操作系统缓存的情况下（大部分的实际场景），DolphinDB Python API的查询速度明显优于pickle。在有缓存的情况下，两者相差无几。有无缓存，对DolphinDB Python API没有显著的影响，但是对pickle却有显著的影响。这些结果从DolphinDB Python API和pickle的耗时构成，可以得到进一步的解释。

pickle文件存储在单个HDD裸盘上，读取性能的极限速度在每秒150MB~200MB之间。读取一个12G大小的pickle文件，需要70秒左右的时间。可见在当前配置下，pickle文件读取的瓶颈在磁盘IO。因此当有操作系统缓存时（等价于从内存读取数据），性能会有大幅提升，耗时主要是pickle文件的反序列化。要提高读取pickle文件的性能，关键在于提升存储介质的吞吐量，譬如改用SSD或者磁盘阵列。

DolphinDB数据库与Python API客户端之间采用了改良的pickle协议。如第1章中所述，使用DolphinDB Python API进行查询可分为3个步骤，其中步骤2和3是可以同时进行的，即一边传输一边反序列化。因此使用Python API从DolphinDB数据库查询的总耗时约等于第1个步骤查询耗时与第2和3个步骤的较大值之和。在两个数据集的测试中，无论是否有缓存，DolphinDB数据库查询部分的耗时均在5\~6秒左右。一天的数据量在DolphinDB数据库中约为8G，分三个节点存储，每个节点的数据量约为2.7G。从一个节点查询，需要传输的数据量约为5.4G（本地节点不需要网络传输），对万兆以太网而言，对应5\~6秒的传输时间。因此当前的配置下，DolphinDB数据库查询的瓶颈在于网络，而不是磁盘IO。一天的数据量压缩之后约1.4G，分布于12个磁盘中，按照每个磁盘100mb/s的吞吐量，加载一天数据的磁盘时间约在1.2秒，远远低于网络需要的5\~6秒。简而言之，DolphinDB时序数据库通过压缩技术和分布式技术，大大缩短了加载一天的金融市场数据的时间，使得磁盘IO不再成为数据查询的瓶颈。

如前所述，DolphinDB Python API的反序列化也采用了pickle协议，但是进行了改良，比原版的pickle协议节约了5\~6秒时间，正好抵消了数据库查询消耗的5\~6秒时间。所以在有缓存的情况下，pickle和DolphinDB Python API耗时几乎相等。如果要进一步提升DolphinDB Python API的查询性能，有两个方向：（1）采用更高速的网络，譬如从10G升级到100G，第一步查询的耗时可能从现在的5\~6秒缩减到2秒。（2）继续改良pickle协议。

### 5.2. 字符串对性能的影响

以数据集1为例，在没有缓存的情况下，DolphinDB Python API总共耗时38秒，但是数据库端的耗时仅5~6秒，80%的时间耗费在pickle反序列化上。通过进一步分析，我们发现字符串类型对pickle的反序列化有极大的影响。如果查询时，剔除两个字符串类型字段，数据集1的时间缩短到19秒，减少了一半。也就是说两个字符串字段，以20%的数据量，占了50%的耗时。数据集2总共78个字段，其中2个字段是字符串类型，如果不查询这两个字段，时间可从22秒缩减到20秒。

以下是读取美国股市Level 1（去除字符串字段）数据集的测试结果：

| 场景       | 无缓存　(秒) | 有缓存（秒） |
| ---------- | ------------ | ------------ |
| DolphinDB  | 19           | 18           |
| pickle     | 58           | 16           |

以下是读取中国股市Level 2（去除字符串字段）数据集的测试结果：

| 场景       | 无缓存（秒） | 有缓存（秒） |
| ---------- | ------------ | ------------ |
| DolphinDB  | 20           | 20           |
| pickle     | 66           | 18           |

剔除字符串字段，对提升pickle的查询也有帮助。在数据集1有缓存的情况下，耗时缩短一半。但是在没有缓存的情况下，提升有限，原因是瓶颈在磁盘IO。

这两个数据集中的字符串类型数据分别是股票ID和交易所名称。股票ID和交易所名称的个数极其有限，重复度非常高。DolphinDB数据库专门提供了一个数据类型SYMBOL用于优化存储此类数据。SYMBOL类型为一个具体的Vector或Table配备一个字典，存储全部不重复的字符串，Vector内部只存储字符串在字典中的索引。在前面的测试中，字符串类型数据已经启用了SYMBOL类型。如果改用STRING类型，DolphinDB的性能会降低。尽管通过SYMBOL类型的优化，为DolphinDB服务端的查询以及pickle的序列化节约了不少时间，但是pickle的反序列化这个步骤并没有充分利用SYMBOL带来的优势，存在大量的python对象多次copy，这是进一步优化的方向之一。

### 5.3. 多任务并发下的性能对比

在实际工作中，经常会多个用户同时提交多个查询。为此我们进一步测试了DolphinDB Python API和pickle在并发查询下的性能。测试采用了数据集2。对于DolphinDB Python API，我们分别测试了连接本地服务器的数据节点进行并发查询，以及连接不同服务器的数据节点进行并发查询的性能。对于pickle，我们并发查询了同一个节点同一个磁盘的不同文件。由于全局锁的限制，测试时，开启多个Python进程从pickle文件或DolphinDB数据库加载数据。下表是三个连接并发查询数据集2中不同日期的Level 2数据的耗时。

| 场景                                 | 连接1（秒） | 连接2（秒）  | 连接3（秒）  |
| ------------------------------------ | ------ | ------ | ------ |
| DolphinDB API 连接本地服务器数据节点 | 48    | 43    | 45    |
| DolphinDB API 连接不同服务器数据节点 | 28    | 35    | 31    |
| pickle                               | 220   | 222   | 219   |

pickle的耗时线性的从70秒增加了到了220秒。由于磁盘IO是pickle的瓶颈，在不增加磁盘吞吐量的情况下，读任务从1个增加到3个，耗时自然也增加到原先的3倍。当同一个客户端节点的三个连接连到不同的服务器数据节点时，耗时增加了50%（10s左右），主要原因是客户端节点的网络达到了瓶颈。当同一个客户端节点的三个连接接入到同一个服务器数据节点时，耗时增加了100%（22s左右），主要原因是客户端节点和接入的数据节点的网络同时达到了瓶颈。

如果要进一步提升DolphinDB并发的多任务查询性能，最直接的办法就是升级网络，譬如将万兆以太网升级成10万兆以太网。另一个方法是在数据节点之间以及数据节点和客户端之间传输数据时引入压缩技术，通过额外的CPU开销提升网络传输的效率，推迟瓶颈的到来。

## 6. 库内分析的必要性

从前面的测试我们可以看到，无论单任务还是多任务并发，DolphinDB数据库端的查询耗时占整个查询耗时的20%左右。因此，如果分析计算能够在数据库内直接完成，或者数据清洗工作在数据库内完成并降低需要传输的数据量，可以大大降低耗时。例如对数据集1的查询耗时38秒，而在DolphinDB数据库端的查询只需5\~6秒。即使这5\~6秒也是因为网络瓶颈造成的，在数据库集群的每一个节点上取数据的时间小于2秒。如果在每一个节点上完成相应的统计分析，只把最后少量的结果合并，总耗时约为2秒左右。但是使用Python API从DolphinDB数据库获取数据，然后再用pandas的单线程来完成数据分析，总耗时约为50秒左右。由此可见，面对海量的结构化数据，库内分析可以大幅提高系统的性能。

为支持时序数据的库内分析，DolphinDB内置了一门完整的多范式脚本语言，包括千余个内置函数，对时间序列、面板数据、矩阵的各种操作如聚合、滑动窗口分析、关联、Pivoting、机器学习等量化金融常用功能均可在DolphinDB数据库内直接完成。

## 7. 结论和展望

- 数据库在提供数据管理的便捷、安全、可靠等优势的同时，在性能上超越操作系统裸文件业已可行。这主要得益于分布式技术、压缩技术、列式存储技术的应用以及应用层协议的改进，使得磁盘IO可能不再成为一个数据库系统最先遇到的瓶颈。

- 金融市场高频数据的时序特性，使得时序数据库DolphinDB成为其最新最有前景的解决方案。DolphinDB相比pickle这样的文件解决方案，不仅为金融市场高频数据带来了管理上的便利和性能上的突破，其内置的强大的时间序列数据、面板数据处理能力更为金融的应用开发带来了极大的便利。

- 使用Python API进行数据查询的整个链路中，DolphinDB数据库查询的耗时只占了很小的一部分，大部分时间耗费在最后一公里，即客户端的网络传输和数据序列化/反序列化。要突破这个瓶颈，有几个发展思路：（1）采用数据库内分析技术，数据清洗和基本的数据分析功能选择在数据库内完成，使用分布式数据库的计算能力缩短数据处理时间，并且大幅降低网络传输的数据量。（2）启用类似Apache Arrow类似的通用内存数据格式，降低各应用之间序列化/反序列化的开销。

- 随着数据库技术的发展，尤其是分布式技术的推进，万兆（10G）网络会比预期更早成为数据库系统的瓶颈。在建设企业内网，尤其在部署高性能数据库集群时，可以开始考虑使用10万兆（100G）以太网。

- 数据压缩可以提升磁盘IO和网络IO的效率，无论在大数据的存储还是传输过程中都非常重要。

- 字符串类型对数据系统性能有非常大的负面影响。由于字符串类型长度不一致，在内存中不能连续存储（通常每个元素使用独立的对象存储），内存分配和释放的压力巨大，内存使用效率不高，CPU处理效率低下。长度不一致，也导致无法在磁盘存储中随机读取字符串元素。因此，数据系统的设计中尽可能避免使用字符串类型。如果字符串类型的重复度较高，建议使用类似DolphinDB中的SYMBOL类型替代。

# Orca与pandas的性能对比测试

## 1.概述
pandas是目前在数据科学和金融数据分析领域中广受欢迎的数据分析工具，但是当在进行大数据量的数据分析的时候，使用pandas就会力不从心。针对这个局限性，DolphinDB开发了orca项目，用户能够以pandas的编程风格，同时利用DolphinDB的性能优势，对海量数据进行高效分析，orca的优势在对于批量数据的读写和计算。
本文将进行orca和pandas的性能对比测试，具体包括以下场景：

- 加载本地数据和数据库数据
- 数据分析


## 2.测试环境
### 2.1硬件配置

主机：PRIME B250M-A

CPU：i7-7700 4cores 8线程

内存：15GB

硬盘：SSD 715.5GB

网络：千兆以太网

OS：ubuntu 16.04.7



### 2.2软件配置

pycharm：社区版2020.2

python：3.7

pandas：1.0.5

DolphinDB：0.1.15.20

## 3.测试场景

### 3.1 加载本地数据和数据库数据

pandas只支持单线程加载，速度会比较慢
Orca采用并行加载，还有智能加载，速度会很快

1、加载本地文件：使用read_csv加载对比时间

| 测试数据 |数据大小| orca | pandas |
| - | :-: | -: | -: |
| EQY_US_GOTC_IBF_20191007 | 65MB|0.3704| 1.0095 |
| EQY_US_ALL_BBO_ADMIN_20191008 |318MB| 1.340 | 4.228 |
| SPLITS_US_ALL_BBO_O_20191008 |1.27GB| 6.580 |21.838 |

2、加载DolphinDB数据库里的文件Orca可以直接连接DolphinDB数据库，使用read_table加载分区表，pandas需要使用pythonAPI加载然后再转成Datafram格式，二者对比时间

|测试数据 |数据大小| orca | pandas |
| - | :-: | :-: | :-: |
| EQY_US_GOTC_IBF_20191007 | 62.4MB|0.00423| 2.235 |
| EQY_US_ALL_BBO_ADMIN_20191008 |318MB| 0.0104 | 4.834 |
| SPLITS_US_ALL_BBO_O_20191008 |1.27GB| 0.0245 | out of memory |


### 3.2 数据分析


以下测试采用了SPLITS_US_ALL_BBO_O_20191008数据集


|方法|测试代码|pandas|orca（单线程）| orca（多线程）|
| - | :-: | :-: | :-: | :-: |
| 索引| `pdf.loc[:,['Offer_Price','Exchange','Symbol','Sequence_Number']]`|0.1786|0.000376| 0.00038 |
|过滤| `pdf[(pdf['Offer_Price']>30.8)&(pdf['Symbol']=='OILX')]`|0.64103|0.001650| 0.001529 |
|过滤| `pdf.loc[pdf.Offer_Price>30.08,['Offer_Price','Exchange','Symbol','Sequence_Number']]`|0.9697|0.00129| 0.00152 |
|分组| `pdf.groupby('Symbol')['Offer_Price'].count()`|0.534|0.0719| 0.0527 |
|分组|`pdf.groupby(['Symbol','Bid_Price'])['Offer_Price'].mean()`|0.780|0.4633|0.386 |
|分组|`pdf[pdf['Exchange']=='P'].groupby(['Symbol','Bid_Price'])['Offer_Price'].sum()`|0.2185|0.1212| 0.1200 |
|滑动窗口|`odf2.rolling(window=50)['Offer_Price','Bid_Price'].mean().compute()`|0.3691|0.3244|0.2387|
|高阶函数|`pdf['Offer_Price'].apply(np.sqrt)`|0.000217|0.000224|0.0167|

在每次操作前需要使用`sudo echo 1 > /proc/sys/vm/drop_caches`清理操作系统的缓存。

由于python采用全局锁，所以pandas只能单线程运行，Orca提供单线程和多线程运行。在单线程下因为DolphinDB中对一些数据分析的函数进行了性能优化，所以单线程下Orca已经会比pandas运算速度更快，而加上多线程同时进行的帮助，运算速度会更快。Orca单线程和多线程的配置可以在dolpindb.cfg文件里进行修改。
 
DolphinDB还支持分布式存储数据，直接对分布式数据库进行数据分析速度会更快。因为将数据数据进行分区后再进行数据分析的时候可以同时对多个分区进行操作，比如一个数据集按时间类型分成5个区，对这个数据集进行求和操作，DolphinDB会在每个分区同时使用sum函数，然后再将每个分区结果汇总起来再使用sum函数，这样操作会比不分区直接操作更快。但是有的操作不适用分区存储的数据，比如求中位数等 。






## 4.总结

从读取数据和数据分析两个角度看，Orca的性能都优于pandas。因为Orca在客户端生成DolphinDB脚本，然后再发送到DolphinDB服务器端解析执行，DolphinDB对于所有的内置函数都进行了性能优化，所以对于同样的操作，Orca的性能会由于pandas。Orca中也有一些操作与pandas存在差异，可以通过[Orca使用教程](http://https://gitee.com/dolphindb/Orca)了解。




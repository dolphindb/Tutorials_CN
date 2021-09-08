# orca和dask的对比报告
## 一、摘要
orca是基于Dolphindb实现的pandas API，orca中的Series与DataFrame在DolphinDB server端均以一个DolphinDB数据表的形式储存，
因此可以在dolphindb端以分布式表形式进行存储和计算。

Dask是一个并行计算库，能在集群中进行分布式计算.Dask Array使用分块算法实现NumPy ndarray接口的子集，将大数组切成许多小数组;Dataframe是基于Pandas Dataframe 改进的一个可以并行处理大数据量的数据结构。相比与Array,Dataframe可以处理大于内存的数据。 Bags 提供了 map, filter, fold, groupby等操作。

二者都能进行分布式计算，Dask更广泛地应用于商业智能应用程序以及许多科学和自定义情况。orca则更适用于金融和物联网领域。

## 二、分区方式

orca和dask都能实现按需求主动分区。dask可以通过自定义索引后根据索引值重新分区
```
df = dd.readcsv(...)
df = df.set_index(df.colname)
unique_col_list = list(df.index.unique().compute())
df = df.repartition(division=unique_col_list+[unique_col_list[-1]])
```
或根据时间频率重新分区`df = df.repartition(freq='1h')`，但开销极大。

orca在read_csv过程中就可以将dataframe存入dolphindb分布式数据表，在分布式表中进行计算，dolphindb同时支持值、范围以及联合分区等分区方式。比如要同时按日期范围和股票名称储存数据，orca就可以轻松实现。

## 三、性能对比
### （一）、测试环境
服务器型号：Dell  PowerEdge R730xd

CPU ：Intel(R) Xeon(R) CPU E5-2650 v4 @ 2.20GHz 12cores 48线程

内存 ：最大内存3T DDR4 2666 MT/s

硬盘 ：SSD   478.9 GB

操作系统：CentOS Linux release 7.7.1908 (Core)
### （二）、对比测试
本次实验将用到以下美国股票交易样本数据
| 数据集 |记录条数|单条记录字段数目|文件大小|
|-------|-------|-------|-------|
|EQY_US_ALL_TRADE_20171016|26,907,063|15|3.1G|
|EQY_US_ALL_NBBO_2017|235,748,387|30| 40G |

#### 1、数据加载性能
orca 和 dask 分别用read_csv导入数据集,利用`DataFrame.compute`将数据导入内存,比较总时间。
| 数据集 |文件大小|orca | dask |
|-------|-------|-----|-----|
| EQY_US_ALL_TRADE_20171016.csv |3.1GB|7.4|12|
| EQY_US_ALL_NBBO_2017.csv |40GB|28.7||


#### 2、函数计算性能
Orca和dask都采用惰性求值，orca会转换为一个中间表达式，dask会返回一个dask图，直到真正需要时才在硬件上发生计算。如果用户需要立即触发计算，可以调用compute函数。这对大数据量的计算场景有很大帮助。
##### 2.1单机
###### 2.1.1 分区计算
##### EQY_US_ALL_TRADE_20171016
|测试函数  |测试代码|orca|dask|
|--------------|------------|----|----|
|group by|df.groupby(['Symbol'])['Trade_Price'].sum()|0.06||
|filter|df[(df['Symbol']=='IBM')].count()|0.08||
|filter+group|df[df.Trade_Volume>=1000].groupby('Symbol')['Trade_Price'].count()|0.05||
##### EQY_US_ALL_NBBO_2017.csv
|测试函数  |测试代码|orca|dask|
|--------------|------------|----|----|
|group by|df.groupby(['Symbol'])['Bid_Size'].sum()|0.25||
|filter|df[(df['Symbol']=='IBM') ].count()|0.1||
|filter+group|df[df.Bid_Price>=37].groupby('Symbol')['Bid_Size'].count()|0.18||

###### 2.1.2 非分区计算
##### EQY_US_ALL_TRADE_20171016
|测试函数  |测试代码                |orca|dask|
|--------------|--------------------|----|----|
|var|df.groupby(['Symbol'])['Trade_Price'].var()|0.14||
|resample|df.resample('1h', on='Time')['Trade_Price'].mean()|0.15||
|rolling|rs=df.rolling(window=30)['Trade_Price'].sum()|0.18|
##### EQY_US_ALL_NBBO_2017.csv
|测试函数  |测试代码                |orca|dask|
|--------------|--------------------|----|----|
|var|df.groupby(['Symbol'])['Bid_Price'].var()|0.51||
|resample|df.resample('1h', on='Times')['Bid_Price'].mean()|0.8||
|rolling|df.rolling(window=30)['Bid_Price'].sum()|3.4|
#### 3、数据连接
采用自定义数据集 quotes.csv和 trades.csv
| 数据集 |记录条数|单条记录字段数目|文件大小|
|-------|-------|-------|-------|
|quotes|200000|4|12M|
|trades|10000000|4| 450M |

|测试函数  |测试代码                |orca|dask|
|--------------|--------------------|----|----|
|merge|trades.merge(right=quotes, left_on=['trade_time','sym'],right_on=['trade_time','sym'], how='inner')|3.5|15|

## 四、结论

















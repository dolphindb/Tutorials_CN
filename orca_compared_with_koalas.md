# orca与koalas性能对比测试

## 1.概述
orca (https://github.com/dolphindb/Orca) 是分布式时序数据库DolphinDB的pandas API。Orca的顶层是pandas API，底层是DolphinDB数据库，Python API for DolphinDB 实现orca客户端与DolphinDB服务端的通信。Orca的基本工作原理是，在客户端通过Python生成DolphinDB脚本，将脚本通过Python API发送到DolphinDB服务端解析执行。Orca的DataFrame中只存储对应的DolphinDB的表的元数据，存储和计算都发生在服务端。

Koalas是在Apache Spark之上实现了pandas API。Koalas的设计初衷和orca一致，即为通过pandas做数据分析的程序提供大数据解决方案。Apache Spark有完整基于hadoop的大数据处理生态，但是需要pandas的实现轻松上手大数据，从而开发了Koalas这个项目。Koalas为Apache Spark ETL+SQL方案之上，添加了Pandas API的接口。Koalas还在开发中，有很多功能还不完善，例如read_csv不能实现全部功能，无法实现resample等等。

## 2. 测试环境
### 2.1 硬件配置

主机：PowerEdge R730xd

CPU：48 Intel(R) Xeon(R) CPU E5-2650 v4 @ 2.20GHz 12core(24个物理核， 48个逻辑核)

内存：503GB

硬盘：17T

OS：CentOS Linux release 7.7.1908 (Core)

### 2.2 环境配置
koalas 和 orca 都最大使用24cores，最大内存128GB。具体配置方法如下。

#### 2.2.1 单节点配置

#### Orca
在dolphindb.cfg中做如下配置
```
mode=single
localExecutors=23
workerNum=24
maxMemSize=128
```

#### Koalas
```
conf = (conf.setMaster('local[*]').set('spark.executor.memory', '16G').set('spark.driver.memory', '128G').set(
    'spark.driver.maxResultSize', '128G')).set('spark.executor.instances', 12).set('spark.executor.cores', 2).set("spark.default.parallelism", 48)
```

### 2.3 软件配置

python：3.7

dolphindb：1.20.4.0

pyspark：3.0.1

koalas：1.2.0

## 3.测试场景

### 3.1 数据加载

### 导入功能实现
我们从字段的智能检测和加载速度两个方面来比较。 Orca支持智能检测类型，不需要指定parse_dates或者dtypes参数即可正确识别所有类型。Koalas必须要指定dtypes才能正确识别所有类型。Koalas没有实现Pandas函数read_csv的全部功能。 parse_dates参数只能设置为False，无法对指定dates字段做只能解析，所以只能在dtypes中将dates字段指定为numpy.datetime64。 其次，dtypes接受的数据格式必须是 Apache spark接受的数据格式， 例如koalas不接受object类型，必须指定为string类型才能正确导入数据。

### 导入性能比较
Orca read_csv 在不指定其他参数的情况下，默认将文件并行导入为DolphinDB server 里的顺序分区内存表， Koalas导入数据的时候，提供了多种index type, 后台会启用Apache Spark的map-reduce进程来并行导入，其中分布式distributed最快。
| 测试数据                     |数据大小 | orca  | koalas|
| ---------------------------- | ------ | ----- | ----- |
| SPLITS_US_ALL_BBO_O_20191008 | 1.27GB | 2.153  | 7.880 |
| EQY_US_ALL_NBBO_2017         | 38GB   | 31.149| 57.598|


#### SPLITS_US_ALL_BBO_O_20191008 表数据类型映射

| Columns                                | Data Type      |
|----------------------------------------|----------------|
|col0                                     |                int32|
|Time                                      |      datetime64[ns]|
|Exchange                                  |              object|
|Symbol                                   |               object|
|Bid_Price                                 |             float64|
|Bid_Size                                    |           float64|
|Offer_Price                               |             float64|
|Offer_Size                                   |          float64|
|Quote_Condition                              |           object|
|Sequence_Number                             |           float64|
|National_BBO_Ind                              |          object|
|FINRA_BBO_Indicator                          |           object|
|FINRA_ADF_MPID_Indicator                       |         object|
|Quote_Cancel_Correction                        |         object|
|Source_Of_Quote                                 |        object|
|Retail_Interest_Indicator                       |        object|
|Short_Sale_Restriction_Indicator                |       float64|
|LULD_BBO_Indicator                              |        object|
|SIP_Generated_Message_Identifier                |        object|
|National_BBO_LULD_Indicator                     |        object|
|Participant_Timestamp                           |datetime64[ns]|
|FINRA_ADF_Timestamp                              |       object|
|FINRA_ADF_Market_Participant_Quote_Indicator      |      object|
|Security_Status_Indicator                          |     object|

#### EQY_US_ALL_NBBO_2017 表数据类型映射

| Columns                                | Data Type      |
|----------------------------------------|----------------|
|Time                                |datetime64[ns]|
|Exchange                                    |object|
|Symbol                                      |object|
|Bid_Price                                 | float64|
|Bid_Size                                     |int32|
|Offer_Price                               | float64|
|Offer_Size                                  | int32|
|Quote_Condition                             |object|
|Sequence_Number                             | int64|
|National_BBO_Ind                          |  object|
|FINRA_BBO_Indicator                        | object|
|FINRA_ADF_MPID_Indicator                   | object|
|Quote_Cancel_Correction                   |  object|
|Source_Of_Quote                            |object|
|Best_Bid_Quote_Condition                  |  object|
|Best_Bid_Exchange                         |  object|
|Best_Bid_Price                            | float64|
|Best_Bid_Size                            |    int32|
|Best_Bid_FINRA_Market_Maker_ID           |   object|
|Best_Offer_Quote_Condition               |   object|
|Best_Offer_Exchange                       |  object|
|Best_Offer_Price                         |  float64|
|Best_Offer_Size                           |   int32|
|Best_Offer_FINRA_Market_Maker_ID           | object|
|LULD_Indicator                            |  object|
|LULD_NBBO_Indicator                    |     object|
|SIP_Generated_Message_Identifier        |    object|
|Participant_Timestamp              | datetime64[ns]|
|FINRA_ADF_Timestamp                      |   object|
|Security_Status_Indicator               |    object|

<!-- ### 3.2 数据存储
这里Orca 将数据保存为DolphinDB 分布式表，koalas 将数据保存为spark默认的格式parquet文件。 -->

### 3.2 基本计算功能
由于koalas采用惰性机制，所以以下测试均采用 print() + head() 的方式触发计算。Koalas 未实现resample功能，故在此不做性能比较。对于rolling，koalas 目前仅支持count、sum、min、max、mean，且不支持参数on，orca 目前支持count、sum、min、max、mean、median、var、std、skew、kurtosis、kurt、argmax、argmin、corr、cov，rolling仅测试'Bid_Price'这一列，即：df=df['Bid_Price']。

#### 数据集：SPLITS_US_ALL_BBO_O_20191008 大小：1.27G
|Category      |Statement                                                                        | orca |koalas |
|--------------|---------------------------------------------------------------------------------|------|-------|
|groupby       |print(df.groupby(['Symbol'])['Bid_Price'].count().head())                        |0.055 |3.358  |
|groupby       |print(df.groupby(['Symbol'])['Bid_Price'].mean().head())                         |0.049 |1.896  |
|groupby       |print(df.groupby(['Symbol'])['Bid_Price'].sum().head())                          |0.040 |1.827  |
|filter        |print(df[(df['Symbol']=='O')].head())                                            |0.196 |0.362  |
|filter+groupby|print(df[df.Sequence_Number>=1000].groupby('Symbol')['Bid_Price'].mean().head()) |0.066 |2.054  |
|rolling       |print(df.rolling(5).count().head())                                              |0.262 |8.438  |
|rolling       |print(df.rolling(5).sum().head())                                                |0.294 |8.155 |
|rolling       |print(df.rolling(5).mean().head())                                               |0.210 |8.010  |
|filter+groupby+rolling |print(df[df.Sequence_Number>=1000].groupby('Symbol').sum()['Bid_Price'].rolling(5).mean().head()|0.148|5.965|


#### 数据集：EQY_US_ALL_NBBO_2017 大小：38G
|Category      |Statement                                                                        | orca | koalas |
|--------------|---------------------------------------------------------------------------------|------|--------|
|groupby       |print(df.groupby(['Symbol'])['Bid_Price'].count().head())                        |0.227 |28.932  |
|groupby       |print(df.groupby(['Symbol'])['Bid_Price'].mean().head())                         |0.225 |29.241  |
|groupby       |print(df.groupby(['Symbol'])['Bid_Price'].sum().head())                          |0.181 |27.256  |
|filter        |print(df[(df['Symbol']=='O')].head())                                            |0.293 |39.568  |
|filter+groupby|print(df[df.Sequence_Number>=1000].groupby('Symbol')['Bid_Price'].mean().head()) |0.422 |28.356  |
|rolling       |print(df.rolling(5).count().head())                                              |1.708 |156.623 |
|rolling       |print(df.rolling(5).sum().head())                                                |2.873 |147.382 |
|rolling       |print(df.rolling(5).mean().head())                                               |2.236 |145.435 |
|filter+groupby+rolling |print(df[df.Sequence_Number>=1000].groupby('Symbol').sum()['Bid_Price'].rolling(5).mean().head()|1.486|27.791|

从表中可以看到，在小数据集上，orca比koalas快了50倍左右，对于大的数据集，orca的优势更加明显，领先50-150倍，可以看到koalas的rolling特别的慢，这是因为koalas当前实现是使用不指定分区的Spark Window，这会将所有数据移动到单台计算机的单个分区中，官方也不推荐在数据量较大时使用rolling函数。除此之外，koalas聚合的结果后并不保证排序，所以groupby得到的结果并不保证和orca或者pandas的一致，比如按天聚合，并按 30 天滑动窗口来计算平均值，`df.groupby('Date').mean()['Bid_Price'].rolling(30).mean()`, 计算得到的结果与pandas和orca的结果不一致，需要在rolling()之前sort_index()才能得到相同的结果。orca目前没有实现groupby与rolling一起使用,比如：`df[df.Sequence_Number>=1000].groupby('Symbol')['Bid_Price'].rolling(5).mean()`, koalas 可实现该功能。

### 3.3. 功能覆盖程度对比
Orca的接口限制：
- Orca的DataFrame中的每个列不能是混合类型，列名也必须是合法DolphinDB变量名。
- 如果DataFrame对应的DolphinDB表是一个分区表，数据存储并非连续，因此就没有RangeIndex的概念，且无法将一整个Series赋值给一个DataFrame的列。
- 对于DolphinDB分区表，一部分没有分布式版本实现的函数，例如median，Orca暂不支持。
- DolphinDB的空值机制和pandas不同，pandas用float类型的nan作为空值，而DolphinDB的空值是每个类型的最小值。
- DolphinDB是列式存储的数据库。对于pandas接口中，一些axis=columns参数还没有支持。
- 目前无法解析Python函数，因此，例如`DataFrame.apply`, `DataFrame.agg`等函数无法接受一个Python函数作为参数。

Koalas的接口限制：
- Koalas采用分区存储到spark表时，采用哈希分区，且不允许中间定义分区方式，只能定义分区列，Orca则可在存储到DolphinDB dfs表示自定义分区方式和分区列，包括顺序分区，值分区、哈希分区、列表分区和组合分区。
- Koalas DataFrame groupby之后的数据结果后并不保证排序。
- Koalas 一些函数还未实现和参数，比如，rolling之后的计算，koalas仅支持5个，orca支持15个，pandas支持19个，不支持resample等，read_csv 的parse_dates 参数，rolling 的 on 参数等。
- Koalas 一些函数的计算会将所有的数据移到一个分区中，导致计算速度较慢并影响之后的计算，比如：rolling、rank、cummax、cumprod、cumsum、bfill、sum、mean、diff等。

<!-- 主要分为一下几个部分进行对比：
- [1. I/O性能](#1-I/O性能) 
    - [2.1 read_csv](#21-read_csv)
    - [2.2 to_table和save_table](#22-to_spark和save_table)
    - [2.3 read_spark和read_table](#23-read_spark和read_table)
- [2. 数据运算(不同分区方式的影响，koalas不支持自定义分区方式)](#2-数据运算)
    - [2.1 groupby](#21-groupby)
    - [2.2 resample](#22-resample)
    - [2.3 rolling](#23-rolling)
    - [2.4 数据合并(join、merge等)](#24-数据合并)
    - [2.5 filter](#24-filter)
- [3. pandas api覆盖率](#3-pandas api覆盖率) -->

## 4.总结
从数据导入和数据计算性能来看，orca均优于koalas，尤其是计算性能方面，大部分都有50倍的差距，Orca的计算均在DolphinDB server上完成，Koalas 则通过spark的内置函数来实现pandas api。可以通过[DolphinDB与Spark的性能对比测试报告](https://blog.csdn.net/qq_41996852/article/details/90022043)了解更多Spark和DolphinDB的性能对比。
在pandas api覆盖上面，orca和koalas均有未实现的地方。koalas有较多的函数将数据移到一个分区中来完成计算，比如rolling、sum、max、min等都是比较常用的计算功能，对性能影响较大。





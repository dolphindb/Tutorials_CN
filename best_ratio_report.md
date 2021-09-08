# 最优报价比率计算场景

## 1. 前言

### 1.1 概述

一般来说，外汇报价为双向报价，分为买入价和卖出价。“买入”和“卖出”都是从银行的角度出发，即针对报价中的前一个币种而言，银行买入和卖出该币种的价格。报价机构会同时报出自己的买价和卖价，由客户自己决定买卖的方向。从投资者的角度来说，买入价和卖出价的价格差越小，成本也就相应地越小。因此，取最高买入价格和最低卖出价格，即为当天最优报价。

确定了当天最优外汇报价后，通过统计当天每家报价机构最优报价的次数以及全市场最优报价的次数，即可计算出各报价机构最优报价的比率。

本报告主要通过DolphinDB通用分布式计算框架的核心功能Map-Reduce，以及在服务器上模拟的公开报价数据，对计算外汇最优报价比率的性能进行测试。

### 1.2 名词解释

- 产品：2个，即期（FXSPT)、远期（FXFWD）
- 期限：17个，SPOT(即期只有个SPOT),1D,1W,2W,3W,1M，2M，3M，4M，5M，6M，9M，1Y，18M，2Y，3Y，10Y
- 货币对：
    结售汇30个：格式为：XXX/CNY或CNY/XXX.如：AUD/CNY,CAD/CNY,CHF/CNY,CNY/AED
    外币对11个：格式为XXX/YYY(XXX和YYY均不是CNY）。如：AUD/USD,EUR/GBP,EUR/JPY
- 报价机构：约40个，一般用四位字母表示：如ICBC

### 1.3 环境说明

服务器依赖的软硬件环境如下：

软件环境：

|  软件类型   | 软件名称  |
|  ----  | ----  |
| 时间序列数据库  | DolphinDB |
| DolphinDB客户端  | DolphinDB_Web_V1.10.10 |
| 操作系统  | CentOS Linux release 7.6.1810 |

硬件环境：

|  类型   | 说明  |
|  ----  | ----  |
| CPU型号  | Intel(R) Xeon(R) CPU E5-2678 v3 @ 2.50GHz |
| CPU核数  | 8 |
| 内存  | 32G |
| 硬盘  | 500G |

## 2. 最优报价比率计算场景测试报告

### 2.1 测试

### 2.1 函数定义

函数simuCurrencyQuotes用于模拟公开报价数据，在DolphinDB分布式数据库中创建一个以期限和外币对作为组合分区列的分区表quotes，包含的字段有品种product、报价机构agency、外币对currPair、报价时间time、期限expiration、卖价offer、买价bid、报价状态status，字段类型分别为SYMBOL、SYMBOL、SYMBOL、SECOND、SYMBOL、DOUBLE、DOUBLE、SYMBOL。并按照货币对、报价时间以及报价机构对数据进行分组和排序，每组货币对的最后一条记录中报价状态为J。

```
def simuCurrencyQuotes(dbName){
	if(existsDatabase(dbName)) dropDB(dbName)
	expiration = `SPOT`1D`1W`2W`3W`1M`2M`3M`4M`5M`6M`9M`1Y`18M`2Y`3Y`10Y
	currs =take(`USDCNY, 5) join (`CUR + string(1..40))
	agency=`AGY + string(1..40)
	time = 00:00:00 .. 23:59:59
	
	db1= database("", VALUE, expiration)
	db2= database("", VALUE, `USDCNY join (`CUR + string(1..40)))
	db = database(dbName, COMPO, [db1, db2])
	dummy = table(100:0, `product`agency`currPair`time`expiration`offer`bid`status, [SYMBOL,SYMBOL,SYMBOL,SECOND,SYMBOL,DOUBLE,DOUBLE,SYMBOL])
	quotes = db.createPartitionedTable(dummy, `quotes, `expiration`currPair)

	writeData = def(dbName, t){ loadTable(dbName, "quotes").append!(t)}
	
	exp =`SPOT
	n = 60000000
	product = `FXSPT
	t = table(take(product, n) as product, rand(agency, n) as agency, rand(currs, n) as currPair, rand(time, n) as time, take(exp, n) as expiration, rand(6000 .. 6010, n)/10000.0 as offer)
	t[`bid] = rand(1..15, n)/10000.0 + t[`offer]
	t[`status] = take(`valid, n)
	t = select top 1 * from t context by currPair, time, agency order by currPair, time, agency
	update t set status = `J where prev(currPair) != currPair
	submitJob("simuFXSpot", "simuFXSpot", writeData{dbName, t})

	exp =`1D
	n = 30000000
	product = `FXPWD
	t = table(take(product, n) as product, rand(agency, n) as agency, rand(currs, n) as currPair, rand(time, n) as time, take(exp, n) as exp, rand(6000 .. 6010, n)/10000.0 as offer)
	t[`bid] = rand(1..15, n)/10000.0 + t[`offer]
	t[`status] = take(`valid, n)
	t = select top 1 * from t context by currPair, time, agency order by currPair, time, agency
	update t set status = `J where prev(currPair) != currPair
	submitJob("simu1D", "simu1D", writeData{dbName, t})

	for(exp in expiration[2:]){
		expData = t.copy().update!(`exp, exp)
		submitJob("simu" + exp, "simu" + exp, writeData{dbName, expData})
	}
	return quotes
}
```

函数calcElapsedTime取下一比数据的报价时间作为当前报价的结束时间，计算结束时间-开始时间，即报价持续时间，结果精度到秒。此时的秒数就是按秒采样的次数。

```
def calcElapsedTime(tick){
	return (next(tick) - tick).replace!(0, int()).bfill!()
}
```

统计当天市场最优报价次数。

```
defg calcTotalQuoteTime(tick, elapsed){
	t = select top 1 elapsed from table(tick.copy() as tick, elapsed.copy() as elapsed) context by tick
	return t.elapsed.sum()
}
```

对同组报价分组后取买价最高价格和卖价最低价格，即为同组报价的最优价格，并对最优报价数据计算报价持续时间。统计当天每家报价机构最优报价的次数和全市场最优报价次数，之后按照品种、模式、报价机构、货币对、期限的维度，计算机构最优报价次数/全市场最优报价次数即为最优报价的比率。

```
def calcBestQuoteRatio(mutable quotes){
	update quotes set elapsed = calcElapsedTime(time) context by currPair
	update quotes set isBestBid = bid == max(bid), isBestOffer = offer == min(offer) context by currPair, time
	totalBestQuotes = select  calcTotalQuoteTime(time, elapsed) as totalQuotes from quotes group by currPair
	bestQuotes = select first(product) as product, first(expiration) as expiration, sum(isBestOffer*elapsed) as bestOfferQuotes, sum(isBestBid*elapsed) as bestBidQuotes from quotes group by currPair, agency
	return select product, agency, expiration, currPair, bestBidQuotes\totalQuotes as bestBidQuoteRatio, bestOfferQuotes\totalQuotes as bestOfferQuoteRatio from ej(bestQuotes, totalBestQuotes, `currPair)
}
```

### 2.2 测试脚本

登录并清理数据节点上的缓存。

```
login("admin", "123456")
pnodeRun(clearAllCache)
```

通过simuCurrencyQuotes函数，模拟公开报价数据并对数据进行分组。分区表quotes中共有390305133条记录。

```
quotes = simuCurrencyQuotes("dfs://cfets")
select count(*) from quotes
count
---------
390305133
```

函数sqlDS创建一个数据源列表。之后利用DolphinDB内置的分布式计算功能Map-Reduce函数，指定分布式数据源ds和map函数calcBestQuoteRatio以及final函数unionAll，进行分布式计算，统计出最优报价比率，返回一个内存表result。

```
ds = sqlDS(<select * from quotes where status != `J>)
result = mr(ds, mapFunc = calcBestQuoteRatio, finalFunc = unionAll{,false})
```

### 2.2 性能分析

运行时长：

```
>timer result = mr(ds, mapFunc = calcBestQuoteRatio, finalFunc = unionAll{,false})
Time elapsed: 23630.777 ms
```

在本测试中，数据库"dfs://cfets"包含两层分区，第一层按照字段期限expiration分区，共有17个分区，第二层按照字段外币对currPair分区，共有45个分区。因此数据库"dfs://cfets"一共有17*45个分区。
可以看出，采用DolphinDB分布式计算框架对近四亿条报价数据的各报价机构的最优报价比率进行计算，非常高效，用时仅有23秒。

计算结果：

```
select top 10 * from result
```

```
product  agency    expiration  currPair  bestBidQuoteRatio  bestOfferQuoteRatio
-------  ------    ----------  --------  -----------------  -------------------
FXPWD    AGY23     10Y		   CUR1      0.027072072593433  0.033380015972407
FXPWD    AGY29     10Y		   CUR1      0.027245685713955  0.033495758052755
FXPWD    AGY33     10Y		   CUR1      0.027778099283557  0.033461035428651
FXPWD    AGY40     10Y		   CUR1      0.027222537297885  0.033785113253626
FXPWD    AGY7      10Y		   CUR1      0.027222537297885	0.03348418384472
FXPWD    AGY1      10Y		   CUR1      0.02788226715587   0.0341091910786
FXPWD    AGY13     10Y		   CUR1      0.02756976353893   0.032627692450144
FXPWD    AGY15     10Y		   CUR1      0.028750332758481  0.034201784742879
FXPWD    AGY19     10Y		   CUR1      0.027766525075522  0.032974918691189
FXPWD    AGY2      10Y		   CUR1      0.027685505619278  0.034711049896411
```

```
select count(*) from result
count
-----
27880
```

result中共有27880条记录，之后在此基础上进行其他计算，比如按照期限天数、交易量等求加权平均等，速度将会非常快。

## 3. 附录

### 3.1 分布式时序数据库DolphinDB简介

DolphinDB是浙江智臾科技推出的国内第一款分布式时序数据库。目前广泛应用于物联网和金融量化交易领域。DolpinDB和其他数据库系统的不同之处在于DolphinDB 是一款集编程语言、数据库和分布式计算“三位一体”的时序数据库平台。

DolphinDB的技术优势如下：

|  序号   | 说明  |
|  ----  | ----  |
| 1  | 多范式编程语言 |
| 2  | 内存表、数组、矩阵、集合、字典等数据结构 |
| 3  | 自定义函数 |
| 4  | 基于map reduce的分布式计算 |
| 5  | 流表一体的流计算处理引擎 |
| 6  | 近千个内置函数 |
| 7  | 插件和模块拓展 |
| 8  | 即时编译（JIT） |
| 9  | orca项目，支持pandas接口 |


### 3.2 DolphinDB分布式计算框架

在DolphinDB分布式计算框架中，使用轻量级数据源对象，而不是将大数据实体传递到远程站点进行计算，大大减少了网络流量。数据源可以有0、1或多个位置，位置为0的数据源是本地数据源，在有多个位置的情况下，这些位置互为备份，系统会随机选择一个位置执行分布式计算。数据源作为一种特殊类型的数据对象，包含指示系统缓存数据或清除缓存的属性。此外，一个数据源对象还可以包含数据转换函数，用以进一步处理检索到的数据。

DolphinDB提供了mr和imr函数，用户只需要指定分布式数据源和核心函数即可编写自己的分布式应用。

DolphinDB分布式计算具有以下特点：

- 通过内存引擎、数据本地化、细粒度数据分区和并行计算实现高速的分布式计算。
- 内置流水线、map-reduce和迭代计算等多种计算框架。
- 为动态数据的分布式计算提供快照级别的隔离。
- 通过在内存中共享数据副本，大幅提升并发任务的吞吐量。
- 高效的分布式编程。在单个节点上编写脚本后，无需编译和部署即可在整个集群上执行。
- 使用内嵌的分布式文件系统自动管理分区数据及其副本，为分布式计算提供负载均衡和容错能力。
- 便捷的存储和计算能力水平扩展。



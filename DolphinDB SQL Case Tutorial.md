

# DolphinDB SQL案例教程

本教程介绍了一些SQL编写案例，通过优化前后性能对比，说明DolphinDB SQL脚本的一些使用技巧。包括以下内容：

- [0 测试环境说明](#0-测试环境说明)
- [1 条件过滤相关案例](#1-条件过滤相关案例)
  - [1.1 WHERE条件子句使用字典](#11-where条件子句使用字典)
  - [1.2 WHERE条件子句使用conditionalFilter函数](#12-where条件子句使用conditionalfilter函数)
- [2 分布式表相关案例](#2-分布式表相关案例)
  - [2.1 分区剪枝](#21-分区剪枝)
  - [2.2 GROUP BY并行查询](#22-group-by并行查询)
- [3 数据分组相关案例](#3-数据分组相关案例)
  - [3.1 分组求TOP N](#31-分组求top-n)
  - [3.2 分段统计股票价格变化率](#32-分段统计股票价格变化率)
  - [3.3 计算股票N shares的交易量加权平均价格](#33-计算股票n-shares的交易量加权平均价格)
  - [3.4 计算股票组合的价值](#34-计算股票组合的价值)
- [4 元编程相关案例](#4-元编程相关案例)
  - [4.1 动态生成SQL语句](#41-动态生成sql语句)

## 0 测试环境说明

处理器：Intel(R) Core(TM) i7-10700 CPU @ 2.90GHz   2.90 GHz

内存：16.0 GB

操作系统：Windows 10

DolphinDB Server版本：DolphinDB_Win64_V1.30.10，社区版License，单节点模式部署，限制使用4GB内存，2核CPU

GUI版本：DolphinDB_GUI_V1.30.7

案例中所用2020年06月的测试数据，数据库名为`dfs://level2`,分布式表名为 `quotes`,分区字段为date（日期）和symbol(股票代码)，数据来源与导入方法请参考 [DolphinDB入门：量化金融范例](./quant_finance_examples.md) 中第3.3节。

## 1 条件过滤相关案例

WHERE条件子句用来选择满足指定条件的记录，包含条件表达式。条件表达式中的函数可以是内置函数（聚合、序列或向量函数）或自定义函数。需要注意的是，DolphinDB不支持在分布式查询的where子句中使用聚合函数，如`sum`或`count`，这是因为执行聚合函数之前，分布式查询需要使用where子句来选择相关分区。如果聚合函数出现在where子句中，则分布式查询不能缩窄相关的分区范围。

### 1.1 WHERE条件子句使用字典

数据表t1含有股票的某些信息，数据表t2含有股票的行业信息，需要根据股票的行业信息进行过滤。

首先，载入2020年06月01日的行情数据，示例如下：

```
t1 = select * from loadTable("dfs://level2"，"quotes") where date = 2020.06.01
syms = exec distinct symbol from t1
t2 = table(syms as symbol, take(`Mul`IoT`Eco`Csm`Edu`Food, syms.size()) as industry)
```

**优化前写法**。将数据表t1与数据表t2根据symbol字段进行join，然后过滤，示例如下：

```
timer t = select * from lj(t1, t2, `symbol) where industry=`Edu
```
查询耗时547.578 ms。注意上面脚本中的`timer`函数用于计算一句或一段脚本的执行时间，是这个查询在服务器上运行耗费的时间，不包括返回查询结果集到客户端的耗时。若结果集数据量特别大，序列化/反序列化和网络传输的耗时可能会远远超过在服务器上运行的耗时。

**优化后写法一**。字典作为一种容器类型，包含唯一的键值对列表。 将数据表t2转换为一个字典，以symbol字段作为键，以industry字段作为值，然后在过滤条件中使用该字典，如下：

```
d = dict(t2.symbol, t2.industry)
timer t = select * from t1 where d[symbol]=`Edu
```

查询耗时340.082 ms。

**优化后写法二**。从数据表t2获取行业为Edu的股票代码向量，并使用in关键字，示例如下：

```
timer t = select * from t1 where symbol in (exec symbol from t2 where industry="Edu")
```

查询耗时194.51 ms。

与优化前写法相比，优化后第二种写法查询性能大大提升。如果t1是数据量非常大的分布式表时，会将t1所有数据载入内存进行join，会导致内存不足而无法得到结果。所以，能够使用字典或in关键字的情况下避免使用join。

### 1.2 WHERE条件子句使用conditionalFilter函数

**场景1**：从一天的全市场股票交易数据中，选择每只股票交易量最大的25%的记录。

首先，载入2020年06月01日的行情数据，如下：

```
trade = select * from database("dfs://level2").loadTable(`quotes) where date = 2020.06.01
```

**优化前写法**。使用context by对于股票分组，并根据volume字段降序排列，结合having子句过滤行号在前25%的记录，示例如下：

```
timer t = select * from trade context by symbol csort volume desc having rowNo(volume) < volume.size() * 0.25
```

查询耗时2417.82 ms。

**优化后写法**。使用group by对于股票分组，并根据volume字段锁定每只股票前25%的范围，以字典形式表示每只股票的查询范围，使用`conditionalFilter`进行条件过滤，示例如下：

```
filter = select percentile(volume, 75) as min, max(volume) as max from trade group by symbol
filterMap = dict(filter.symbol, each(pair, filter.min, double(filter.max)))

timer t = select * from trade where conditionalFilter(volume, symbol, filterMap)
```

查询耗时356.975 ms。

**场景2**：针对交易数据表，根据某个字段进行排序，计算每只股票前5%记录的均值、最小值和标准差。

首先，产生模拟数据，示例如下：

```
SecurityId = `APL`MS`MS`MS`IBM`IBM`APL`APL`APL$SYMBOL
date = 2012.06.01 2012.06.01 2012.06.02 2012.06.03 2012.06.01 2012.06.02 2012.06.02 2012.06.03 2012.06.04
tradeMoney = 49.6 29.46 29.52 30.02 174.97 175.23 50.76 50.32 51.29
trades = table(SecurityId, date, tradeMoney)
```

**优化前写法**。使用context by对于股票分组，并根据tradeMoney字段计算95%位置处的线性插值以及最大值，分别作为过滤条件的最小值与最大值。再根据group by对于股票分组，并使用统计函数分别计算每只股票的均值、最小值和标准差，示例如下：

```
timer(10000) t = select avg(tradeMoney), min(tradeMoney), std(tradeMoney) 
                 from ( select SecurityId, date, tradeMoney, percentile(tradeMoney, 95) as min, max(tradeMoney)  as max from trades context by SecurityId )
                 where tradeMoney >= min and tradeMoney <= max
                 group by SecurityId
```

查询1万次耗时920.563 ms。

**优化后写法**。使用group by对于股票分组，并根据tradeMoney字段锁定每只股票前5%的范围，以字典形式表示每只股票的查询范围，使用`conditionalFilter`进行条件过滤，并使用统计函数分别计算每只股票的均值、最小值和标准差，如下：

```
filter = select percentile(tradeMoney, 95) as min, max(tradeMoney)  as max from trades group by SecurityId
filterMap = dict(filter.SecurityId, each(pair, filter.min, filter.max))

timer(10000) t = select avg(tradeMoney), min(tradeMoney), std(tradeMoney) 
                 from trades 
                 where conditionalFilter(tradeMoney, SecurityId, filterMap) 
                 group by SecurityId
```

查询1万次耗时475.725 ms。

与优化前写法相比，使用`conditionalFilter`的写法查询性能提升一倍左右。

## 2 分布式表相关案例

分布式查询和普通查询的语法并无差异，理解分布式查询的工作原理有助于写出高效的查询。系统首先根据where子句确定需要的分区，然后重写查询，并把新的查询发送到相关分区所在的位置，最后整合所有分区的结果。

### 2.1 分区剪枝

查询每只股票在某个时间范围内的记录数目。

首先，加载测试数据库 `dfs://level2` 的表 `quotes`，并把这个表对象赋值给变量 quotes，之后就可以用变量 quotes ，示例如下：

```
quotes = loadTable("dfs://level2"，"quotes")
```

**优化前写法**。where条件子句根据日期过滤时，使用`temporalFormat`函数对于日期进行格式转换，如下：

```
timer t = select count(*) from quotes 
          where temporalFormat(date, "yyyy.MM.dd") >= '2020.06.01' and temporalFormat(date, "yyyy.MM.dd") <= '2020.06.02' 
          group by symbol
```

查询耗时2442.504 ms。

**优化后写法**。使用原始date进行分区过滤，如下：

```
timer t = select count(*) from quotes where date between 2020.06.01 : 2020.06.02 group by symbol
```

查询耗时106.746 ms。

与优化前写法相比，查询性能提升数十倍。DolphinDB在解决海量数据的存取时，并不提供行级的索引，而是将分区作为数据库的物理索引。系统在执行分布式查询时，首先根据where条件确定需要的分区。大多数分布式查询只涉及分布式表的部分分区，系统不必全表扫描，从而节省大量时间。但若不能根据where条件确定分区，就会全表扫描，影响查询性能。优化前写法中，分区字段套用了`temporalFormat`函数，系统无法做分区剪枝。

还有一些其它的导致系统无法做分区剪枝的反例，简单列举如下：

反例1：对分区字段进行运算

```
select count(*) from quotes where date+30 > 2020.06.27
```

反例2：使用链式比较

```
select count(*) from quotes where 2020.06.26 < date < 2020.06.27
```

反例3：过滤条件未使用分区字段

```
select count(*) from quotes where bidSize < 500
```

反例4：与分区字段比较时使用其它列

```
select count(*) from quotes where date < announcementDate-3
```

### 2.2 GROUP BY并行查询

针对某个时间范围内每只股票，区分涨跌，并计算第一档行情买卖双方报价之差、总交易量等指标。


**优化前写法**。首先，筛选2020年06月01日09: 30以后的数据，收盘价高于开盘价的记录，标志位设置为1；否则，标志位设置为0，结果赋给一个内存表。然后，使用group by根据symbol、date、flag三个字段分组，并统计计算askPrice1、volume，示例如下：

```
timer {
	tmpT = select *, iif(last > open, 1, 0) as flag from loadTable("dfs://level2"，"quotes") where date = 2020.06.01, time >= 09:30:00.000
	t = select iif(max(askPrice1) - min(bidPrice1) == 0, 0, 1) as price1Diff, count(askPrice1) as askPrice1Count, sum(volume) as volumes 
        from tmpT 
        group by symbol, date, flag
} 
```

查询耗时3538.867 ms。

**优化后写法**。不再有中间内存表，直接从分布式表查询，并使用group by分组、统计计算，示例如下：

```
timer t = select iif(max(askPrice1) - min(bidPrice1) == 0, 0, 1) as price1Diff, count(askPrice1) as askPrice1Count, sum(volume) as volumes 
          from loadTable("dfs://level2"，"quotes") 
          where date = 2020.06.01, time >= 09:30:00.000 
          group by symbol, date, iif(last > open, 1, 0) as flag
```

查询耗时485.734 ms。

与优化前写法相比，优化后写法查询性能提升约七倍多。对未分区内存表使用group by分组查询是串行计算各个分区，而对分布式表或分区内存表使用group by分组查询是并行对各个分区进行查询，因此后者的性能优于前者。

## 3 数据分组相关案例

### 3.1 分组求TOP N

获取每只股票最新的10条记录。

我们仅对于2020年06月01日的数据进行分组求TOP 10，数据行数670多万行。可以使用context by子句每组返回一个与组内记录数相同长度的向量，结合csort关键字，对于组内数据进行排序，最后top子句应用于每组，示例如下：

```
timer t = select top 10 * 
          from loadTable("dfs://level2"，"quotes")  
          where date = 2020.06.01 
          context by symbol csort date desc, time desc
```

查询耗时2172.224 ms。

context by是DolphinDB独有的创新，是对标准SQL语句的拓展。在关系型数据库管理系统中，一张表由行的集合组成，行之间没有顺序。我们可以使用如`min`, `max`, `avg`, `stdev`等聚合函数来对行进行分组，但是不能在分组内的行使用顺序敏感的聚合函数，比如`first`, `last`等，或者对顺序敏感的滑动窗口和累积计算函数，如`cumsum`, `cummax`, `ratios`, `deltas`等。DolphinDB支持时间序列数据处理，context by子句使组内处理时间序列数据更加方便。

### 3.2 分段统计股票价格变化率

根据表中某一列的值，分段统计并计算每只股票价格变化率。


我们对于2020年06月01日的数据，使用`segment`函数对于askLevel列连续相同的数据分组，并计算每只股票的第一档价格的变化率，示例如下：

```
timer t = select last(askPrice1) \ first(askPrice1) - 1 
          from loadTable("dfs://level2"，"quotes")  
          where date = 2020.06.01 
          group by symbol, segment(askLevel, false)
```

查询耗时286.26 ms。

### 3.3 计算股票N shares的交易量加权平均价格

计算每支股票最近1000 shares相关的所有trades的vwap。

1000 shares可能是100、300、600三个trades的，也可能是30000、100两个trades的。首先需要找到参与计算的trades，使得shares总和恰好超过1000，且减掉时间点最远的一个trade，则shares总和小于1000，然后计算一下它们的vwap。

首先，产生模拟数据，示例如下：

```
n = 500000
t = table(rand(string(1..4000), n) as sym, rand(10.0, n) as price, rand(500, n) as vol)
```

**优化前写法**。使用group by对于股票进行分组，针对每支股票分别调用自定义聚合函数`lastVolPx1`，针对所有trades采用循环计算，并判断shares是否恰好超过bound，最后计算vwag (交易量加权平均价，Volume Weighted Average Price)。如下：

```
defg lastVolPx1(price, vol, bound) {
	size = price.size()
	cumSum = 0
	for(i in 0:size) {
		cumSum = cumSum + vol[size - 1 - i]
		if(cumSum >= bound) {
			price_tmp = price.subarray(size - 1 - i :)
			vol_tmp = vol.subarray(size - 1 - i :)
			return wavg(price_tmp, vol_tmp)
		}
		if(i == size - 1 && cumSum < bound) {
			return wavg(price, vol)
		}
	}
}

timer lastVolPx_t1 = select lastVolPx1(price, vol, 1000) as lastVolPx from t group by sym
```

查询耗时160.606 ms。

**优化后写法**。使用group by对于股票进行分组，针对每支股票分别调用自定义聚合函数`lastVolPx2`，计算累积交易量向量，以及恰好满足shares大于bound的起始位置，最后计算vwag。如下：

```
defg lastVolPx2(price, vol, bound) {
	cumVol = vol.cumsum()
	if(cumVol.tail() <= bound)
		return wavg(price, vol)
	else {
		start = (cumVol <= cumVol.tail() - bound).sum()
		return wavg(price.subarray(start:), vol.subarray(start:))
	}
}

timer lastVolPx_t2 = select lastVolPx2(price, vol, 1000) as lastVolPx from t group by sym
```

查询耗时78.563 ms。与优化前相比，性能提升约1倍。

### 3.4 计算股票组合的价值

在进行指数套利交易回测时，需要计算给定股票组合的价值。当数据量极大时，回测时采用一般数据分析系统，对系统内存及速度的要求极高。本例可见，使用DolphinDB的编程语言可极为简洁的进行此类计算。

为了简化起见，假定某个指数仅由两只股票组成：AAPL与FB。模拟数据，如下：

```
syms = take(`AAPL, 6) join take(`FB, 5)
time = 2019.02.27T09:45:01.000000000 + [146, 278, 412, 445, 496, 789, 212, 556, 598, 712, 989]
prices = 173.27 173.26 173.24 173.25 173.26 173.27 161.51 161.50 161.49 161.50 161.51
quotes = table(take(syms, 100000) as Symbol, take(time, 100000) as Time, take(prices, 100000) as Price)
weights = dict(`AAPL`FB, 0.6 0.4)
ETF = select Symbol, Time, Price*weights[Symbol] as weightedPrice from quotes
```

**优化前写法**。首先，需要将原始数据表的3列（时间，股票代码，价格）转换为同等长度但是宽度为指数成分股数量+1的数据表，然后向前补充空值(forward fill NULLs)，进而计算每行的指数成分股对指数价格的贡献之和。示例如下：

```
colAAPL = array(DOUBLE, ETF.Time.size())
colFB = array(DOUBLE, ETF.Time.size())

for(i in 0:ETF.Time.size()) {
	if(ETF.Symbol[i] == `AAPL) {
		colAAPL[i] = ETF.weightedPrice[i]
		colFB[i] = NULL
	}
	if(ETF.Symbol[i] == `FB) {
		colAAPL[i] = NULL
		colFB[i] = ETF.weightedPrice[i]
	}
}

ETF_TMP1 = table(ETF.Time, colAAPL, colFB)
ETF_TMP2 = select * from ETF_TMP1 order by Time
ETF_TMP3 = ETF_TMP2.ffill()

t = select Time, rowSum(colAAPL, colFB) as rowSum from ETF_TMP3
```

以上代码块耗时594.969 ms。

**优化后写法**。pivot by是DolphinDB独有的功能，是对标准SQL语句的拓展，可以将表中一列或多列的内容按照两个维度重新排列，亦可配合数据转换函数使用。使用DolphinDB中的SQL pivot by语句，只需以下一行代码，即可实现上述所有步骤。不仅编程简洁，而且无需产生中间过程数据表，有效避免了内存不足的问题，同时极大提升计算速度。示例如下：

```
timer t = select rowSum(ffill(last(weightedPrice))) from ETF pivot by Time, Symbol
```

查询耗时6.982 ms。

## 4 元编程相关案例

### 4.1 动态生成SQL语句

执行一组查询，合并查询结果。

例如，每天需要执行一组查询，如下：

```
select * from t where vn=50982208,bc=25,cc=814,stt=11,vt=2, dsl=2020.02.05, mt<52355979 order by mt desc limit 1
select * from t where vn=50982208,bc=25,cc=814,stt=12,vt=2, dsl=2020.02.05, mt<52355979 order by mt desc limit 1
select * from t where vn=51180116,bc=25,cc=814,stt=12,vt=2, dsl=2020.02.05, mt<52354979 order by mt desc limit 1
select * from t where vn=41774759,bc=1180,cc=333,stt=3,vt=116, dsl=2020.02.05, mt<52355979 order by mt desc limit 1
```

通过元编程动态生成SQL语句可以解决这个问题。过滤条件包含的列和排序的列都相同，为此，可编写自定义函数bundleQuery：

```
def bundleQuery(tbl, dt, dtColName, mt, mtColName, filterColValues, filterColNames){
	cnt = filterColValues[0].size()
	filterColCnt = filterColValues.size()
	orderByCol = sqlCol(mtColName)
	selCol = sqlCol("*")
	filters = array(ANY, filterColCnt + 2)
	filters[filterColCnt] = expr(sqlCol(dtColName), ==, dt)
	filters[filterColCnt+1] = expr(sqlCol(mtColName), <, mt)
	
	queries = array(ANY, cnt)
	for(i in 0:cnt)	{
		for(j in 0:filterColCnt){
			filters[j] = expr(sqlCol(filterColNames[j]), ==, filterColValues[j][i])
		}
		queries.append!(sql(select=selCol, from=tbl, where=filters, orderBy=orderByCol, ascOrder=false, limit=1))
	}
	
	return loop(eval, queries).unionAll(false)
}
```

bundleQuery中各个参数的含义如下：tbl是数据表。dt是过滤条件中日期的值。dtColName是过滤条件中日期列的名称。mt是过滤条件中mt的值。mtColName是过滤条件中mt列的名称，以及排序列的名称。filterColValues是其他过滤条件中的值，用元组表示，其中的每个向量表示一个过滤条件，每个向量中的元素表示该过滤条件的值。filterColNames是其他过滤条件中的列名，用向量表示。

上面一组SQL语句，相当于执行以下代码：

```
dt = 2020.02.05
dtColName = "dls"
mt = 52355979
mtColName = "mt"
colNames = `vn`bc`cc`stt`vt
colValues = [50982208 50982208 51180116 41774759, 25 25 25 1180, 814 814 814 333, 11 12 12 3, 2 2 2 116]

bundleQuery(t, dt, dtColName, mt, mtColName, colValues, colNames)
```

可以以admin登录之后，执行以下脚本将`bundleQuery`函数定义为函数视图。在集群的任何节点重启系统之后，都可直接使用该函数。

```
addFunctionView(bundleQuery)
```

如果每次都手动编写全部SQL语句，工作量大，并且扩展性差，通过元编程动态生成SQL语句可以解决这个问题。
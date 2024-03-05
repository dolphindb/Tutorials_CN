# DolphinDB SQL 编写案例

本教程重点介绍了一些常见场景下的 SQL 编写案例。介绍如何正确编写 SQL 语句来提升脚本运行性能，通过优化前后性能对比，来说明DolphinDB SQL脚本的编写技巧。包括以下内容：

- [DolphinDB SQL 编写案例](#dolphindb-sql-编写案例)
	- [1. 测试环境说明](#1-测试环境说明)
	- [2. 条件过滤相关案例](#2-条件过滤相关案例)
		- [2.1. where 条件子句使用 in 关键字](#21-where-条件子句使用-in-关键字)
			- [2.1.1. 优化前](#211-优化前)
			- [2.1.2. 优化后](#212-优化后)
		- [2.2. 分组数据过滤](#22-分组数据过滤)
			- [2.2.1. 优化前](#221-优化前)
			- [2.2.2. 优化后](#222-优化后)
		- [2.3. where 条件子句使用逗号或 and](#23-where-条件子句使用逗号或-and)
			- [2.3.1. 过滤条件与序列无关](#231-过滤条件与序列无关)
			- [2.3.2. 过滤条件与序列有关](#232-过滤条件与序列有关)
	- [3. 分布式表相关案例](#3-分布式表相关案例)
		- [3.1. 分区剪枝](#31-分区剪枝)
			- [3.1.1. 优化前](#311-优化前)
			- [3.1.2. 优化后](#312-优化后)
		- [3.2. group by 并行查询](#32-group-by-并行查询)
			- [3.2.1. 优化前](#321-优化前)
			- [3.2.2. 优化后](#322-优化后)
		- [3.3. 分组查询使用 map 关键字](#33-分组查询使用-map-关键字)
			- [3.3.1. 优化前](#331-优化前)
			- [3.3.2. 优化后](#332-优化后)
	- [4. 分组计算相关案例](#4-分组计算相关案例)
		- [4.1. 查询最新的 N 条记录](#41-查询最新的-n-条记录)
		- [4.2. 计算滑动 VWAP](#42-计算滑动-vwap)
		- [4.3. 计算累积 VWAP](#43-计算累积-vwap)
		- [4.4. 计算 N 股 VWAP](#44-计算-n-股-vwap)
		- [4.5. 分段统计股票价格变化率](#45-分段统计股票价格变化率)
		- [4.6. 计算不同连续区间的最值](#46-计算不同连续区间的最值)
		- [4.7. 不同聚合方式计算指标](#47-不同聚合方式计算指标)
		- [4.8. 计算股票收益波动率](#48-计算股票收益波动率)
		- [4.9. 计算股票组合的价值](#49-计算股票组合的价值)
		- [4.10. 根据成交量切分时间窗口](#410-根据成交量切分时间窗口)
		- [4.11. 股票因子归整](#411-股票因子归整)
		- [4.12. 根据交易额统计单子类型](#412-根据交易额统计单子类型)
	- [5. 元编程相关案例](#5-元编程相关案例)
		- [5.1. 动态生成 SQL 语句案例 1](#51-动态生成-sql-语句案例-1)
		- [5.2. 动态生成 SQL 语句案例 2](#52-动态生成-sql-语句案例-2)

## 1. 测试环境说明

处理器：Intel(R) Xeon(R) Silver 4216 CPU @ 2.10GHz

核数：64

内存：512 GB

操作系统：CentOS Linux release 7.9

License：免费版License，CPU 2核，内存 8GB

DolphinDB Server 版本：DolphinDB_Linux64_V2.00.4，单节点模式部署

DolphinDB GUI 版本：DolphinDB_GUI_V1.30.15

以下章节案例中所用到的2020年06月测试数据为上交所 Level-1 快照数据，基于真实数据结构模拟2000只股票快照数据，基于 OLAP 与 TSDB 存储引擎的建库建表、数据模拟、数据插入脚本如下：

```
model = table(1:0, `SecurityID`DateTime`PreClosePx`OpenPx`HighPx`LowPx`LastPx`Volume`Amount`BidPrice1`BidPrice2`BidPrice3`BidPrice4`BidPrice5`BidOrderQty1`BidOrderQty2`BidOrderQty3`BidOrderQty4`BidOrderQty5`OfferPrice1`OfferPrice2`OfferPrice3`OfferPrice4`OfferPrice5`OfferQty1`OfferQty2`OfferQty3`OfferQty4`OfferQty5, [SYMBOL, DATETIME, DOUBLE, DOUBLE, DOUBLE, DOUBLE, DOUBLE, LONG, DOUBLE, DOUBLE, DOUBLE, DOUBLE, DOUBLE, DOUBLE, LONG, LONG, LONG, LONG, LONG, DOUBLE, DOUBLE, DOUBLE, DOUBLE, DOUBLE, LONG, LONG, LONG, LONG, LONG])

// OLAP 存储引擎建库建表
dbDate = database("", VALUE, 2020.06.01..2020.06.07)
dbSecurityID = database("", HASH, [SYMBOL, 10])
db = database("dfs://Level1", COMPO, [dbDate, dbSecurityID])
createPartitionedTable(db, model, `Snapshot, `DateTime`SecurityID)

// TSDB 存储引擎建库建表
dbDate = database("", VALUE, 2020.06.01..2020.06.07)
dbSymbol = database("", HASH, [SYMBOL, 10])
db = database("dfs://Level1_TSDB", COMPO, [dbDate, dbSymbol], engine="TSDB")
createPartitionedTable(db, model, `Snapshot, `DateTime`SecurityID, sortColumns=`SecurityID`DateTime)

def mockHalfDayData(Date, StartTime) {
	t_SecurityID = table(format(600001..602000, "000000") + ".SH" as SecurityID)
	t_DateTime = table(concatDateTime(Date, StartTime + 1..2400 * 3) as DateTime)
	t = cj(t_SecurityID, t_DateTime)
	size = t.size()
	return  table(t.SecurityID as SecurityID, t.DateTime as DateTime, rand(100.0, size) as PreClosePx, rand(100.0, size) as OpenPx, rand(100.0, size) as HighPx, rand(100.0, size) as LowPx, rand(100.0, size) as LastPx, rand(10000, size) as Volume, rand(100000.0, size) as Amount, rand(100.0, size) as BidPrice1, rand(100.0, size) as BidPrice2, rand(100.0, size) as BidPrice3, rand(100.0, size) as BidPrice4, rand(100.0, size) as BidPrice5, rand(100000, size) as BidOrderQty1, rand(100000, size) as BidOrderQty2, rand(100000, size) as BidOrderQty3, rand(100000, size) as BidOrderQty4, rand(100000, size) as BidOrderQty5, rand(100.0, size) as OfferPrice1, rand(100.0, size) as OfferPrice2, rand(100.0, size) as OfferPrice3, rand(100.0, size) as OfferPrice4, rand(100.0, size) as OfferPrice5, rand(100000, size) as OfferQty1, rand(100000, size) as OfferQty2, rand(100000, size) as OfferQty3, rand(100000, size) as OfferQty4, rand(100000, size) as OfferQty5)
}

def mockData(DateVector, StartTimeVector) {
	for(Date in DateVector) {
		for(StartTime in StartTimeVector) {
			data = mockHalfDayData(Date, StartTime)

			// OLAP 存储引擎分布式表插入模拟数据
			loadTable("dfs://Level1", "Snapshot").append!(data)

			// TSDB 存储引擎分布式表插入模拟数据
			loadTable("dfs://Level1_TSDB", "Snapshot").append!(data)
		}
	}
}

mockData(2020.06.01..2020.06.02, 09:30:00 13:00:00)
```

## 2. 条件过滤相关案例

where 条件子句包含一个或多个条件表达式，根据表达式指定的过滤条件，可以过滤出满足需求的记录。

条件表达式中可以使用 DolphinDB 内置函数，如聚合、序列、向量函数，也可以使用用户自定义函数。需要注意的是，DolphinDB 不支持在分布式查询的 where 子句中使用聚合函数，如 `sum`、`count`。因为执行聚合函数之前，分布式查询需要通过 where 子句来筛选相关分区的数据，达到分区剪枝的效果，减少查询耗时。如果聚合函数出现在 where 子句中，则分布式查询不能缩窄相关分区范围。

### 2.1. where 条件子句使用 in 关键字

**场景：数据表 t1 含有股票的某些信息，数据表 t2 含有股票的行业信息，需要根据股票的行业信息进行过滤。**

首先，载入测试数据库中的表 “Snapshot” 赋给变量 t1，并模拟构建行业信息数据表 t2，示例如下：

```
t1 = loadTable("dfs://Level1", "Snapshot")
SecurityIDs = exec distinct SecurityID from t1 where date(DateTime) = 2020.06.01
t2 = table(SecurityIDs as SecurityID, 
           take(`Mul`IoT`Eco`Csm`Edu`Food, SecurityIDs.size()) as Industry)
```



#### 2.1.1. 优化前

将数据表 t1 与数据表 t2 根据 SecurityID 字段进行 left join，然后指定 where 条件进行过滤，示例如下：

```
timer res1 = select SecurityID, DateTime 
			 from lj(t1, t2, `SecurityID) 
			 where date(DateTime) = 2020.06.01, Industry=`Edu
```

*查询耗时 336 ms。*

需要注意的是，以上脚本中的 `timer` 函数通常用于计算一行或一段脚本的执行时间，该时间指的是脚本在 DolphinDB Server 端的运行耗时，而不包括脚本运行结果集返回到客户端的耗时。若结果集数据量过大，序列化/反序列化以及网络传输的耗时可能会远远超过脚本在服务器上的运行耗时。



#### 2.1.2. 优化后

从数据表 t2 获取行业为 “Edu” 的股票代码向量，并使用 in 关键字指定条件范围，示例如下：

```
SecurityIDs = exec SecurityID from t2 where Industry="Edu"
timer res2 = select SecurityID, DateTime 
			 from t1 
			 where date(DateTime) = 2020.06.01, SecurityID in SecurityIDs
```

*查询耗时 72 ms。*

```
each(eqObj, res1.values(), res2.values()) // true
```

`each` 函数对表的每列分别通过 `eqObj` 比较，返回均为 true，说明优化前后返回的结果相同。但与优化前写法相比，优化后写法查询性能提升约4倍。这是因为，在 SQL 语句中，表连接的耗时远高于 where 子句中的过滤条件的耗时，因此在能够使用字典或 in 关键字的情况下应避免使用 join。

### 2.2. 分组数据过滤

场景：截取单日全市场股票交易快照数据，筛选出每只股票交易量最大的前 25% 的记录。

首先，载入测试数据库表并将该表对象赋值给变量 snapshot，之后可以直接引用变量 snapshot，示例如下：

```
snapshot = loadTable("dfs://Level1", "Snapshot")
```

使用 context by 对于股票分组，并根据 Volume 字段计算 75% 分位点的线性插值作为最小值，示例如下：

```
timer res1 = select * from snapshot 
			 where date(DateTime) = 2020.06.01 
			 context by SecurityID having Volume >= percentile(Volume, 75, "linear")
```

context by 是 DolphinDB SQL 引入的一个关键词，用于分组计算。与 group by 用于聚合不同，context by 只是对数据分组而不做聚合操作，因此不改变数据的记录数。

having 子句总是跟在 group by 或者 context by 后，用来将结果进行过滤，只返回满足指定条件的聚合函数值的组结果。having 与 group by 搭配使用时，表示是否输出某个组的结果。having 与 context by 搭配使用时，既可以表示是否输出这个组的结果，也可以表示输出组中的哪些行。



场景：承接以上场景，选出每只股票交易量最大的 25% 的记录后，计算 LastPx 的标准差。



#### 2.2.1. 优化前

使用 context by 对股票分组，并根据 Volume 字段计算 75% 位置处的线性插值作为过滤条件的最小值，再根据 group by 对股票分组，并计算标准差，最后使用 order by 对于股票排序，示例如下：

```
timer select std(LastPx) as std from (
      select SecurityID, LastPx from snapshot 
      where date(DateTime) = 2020.06.01 
      context by SecurityID 
      having Volume >= percentile(Volume, 75, "linear")) 
      group by SecurityID 
      order by SecurityID
```

*耗时 242 ms。*



#### 2.2.2. 优化后

使用 group by 对股票分组，aggrTopN 高阶函数选择交易量最大的 25% 的记录，并计算标准差。示例如下：

```
timer select aggrTopN(std, LastPx, Volume, 0.25, false) as std from snapshot 
	  where date(DateTime) = 2020.06.01 
	  group by SecurityID 
	  order by SecurityID
```

*耗时 124 ms。*

优化前先把数据分组并进行过滤，合并数据后再分组计算聚合值。优化后，在数据分组后，直接进行过滤和聚合，减少了中间步骤，从而提升了性能。

### 2.3. where 条件子句使用逗号或 and

where 子句中多条件如果使用 “,” 进行连接时，在查询时会按照顺序对 “,” 前的条件层层进行过滤；若使用 and 进行连接时，会对所有条件在原表内分别进行筛选后再将结果取交集。

下面将通过几个示例，比较使用 and 和逗号再不同场景下进行条件过滤的异同。

首先，产生模拟数据，示例如下：

```
N = 10000000
t = table(take(2019.01.01..2019.01.03, N) as date, 			  
          take(`C`MS`MS`MS`IBM`IBM`IBM`C`C$SYMBOL, N) as sym, 
          take(49.6 29.46 29.52 30.02 174.97 175.23 50.76 50.32 51.29, N) as price, 
          take(2200 1900 2100 3200 6800 5400 1300 2500 8800, N) as qty)
```

根据过滤条件是否使用序列相关函数，如 `deltas`, `ratios`, `ffill`, `move`, `prev`, `cumsum` 等，可以分为以下两种情况。

#### 2.3.1. 过滤条件与序列无关

示例代码如下：

```
timer(10) t1 = select * from t where qty > 2000, date = 2019.01.02, sym = `C
timer(10) t2 = select * from t where qty > 2000 and date = 2019.01.02 and sym = `C

each(eqObj, t1.values(), t2.values()) // true
```

*以上两个查询耗时分别为 902 ms、930 ms。* 此时，使用逗号与 and 的查询性能相差不大。



测试不同条件先后顺序对于查询性能与查询结果的影响，示例代码如下：

```
timer(10) t3 = select * from t where date = 2019.01.02, sym = `C, qty > 2000
timer(10) t4 = select * from t where date = 2019.01.02 and sym = `C and qty > 2000

each(eqObj, t1.values(), t3.values()) // true
each(eqObj, t2.values(), t4.values()) // true
```

*以上两个查询耗时分别为 669 ms、651 ms。* 此时，使用逗号与 and 的查询性能相差不大。

说明过滤条件与序列无关时，条件先后顺序对于查询结果无影响。但性能方面 t3(t4) 较 t1(t2) 提升约30%，这是因为 date 字段比 qty 字段筛选性更强。

#### 2.3.2. 过滤条件与序列有关

示例代码如下：

```
timer(10) t1 = select * from t where ratios(qty) > 1, date = 2019.01.02, sym = `C
timer(10) t2 = select * from t where ratios(qty) > 1 and date = 2019.01.02 and sym = `C

each(eqObj, t1.values(), t2.values()) // true
```

*以上两个查询耗时分别为 1503 ms、1465 ms。*

此时，使用逗号与 and 的查询性能相差无几。序列条件作为第一个条件，使用逗号连接时，首先按照原表中数据的顺序进行计算，后面条件与序列无关，所以查询结果与 and 连接时保持一致。

测试不同条件先后顺序对于查询性能与查询结果的影响，示例代码如下：

```
timer(10) t3 = select * from t where date = 2019.01.02, sym = `C, ratios(qty) > 1
timer(10) t4 = select * from t where date = 2019.01.02 and sym = `C and ratios(qty) > 1

each(eqObj, t2.values(), t4.values()) // true
each(eqObj, t1.values(), t3.values()) // false
```

*以上两个查询耗时分别为 507 ms、1433 ms。* 第一个 each 函数返回均为 true，即 t2 与 t4 查询结果相同；第二个 each 函数返回均为 false，即 t1 与 t3 查询结果不同。

说明过滤条件与序列相关时，对于使用 and 连接的查询语句，条件先后顺序对于查询结果无影响，性能方面亦无差别；对于使用逗号的查询语句，序列条件在后，性能虽有提升，但查询结果不同。

综合上述测试结果分析可知：

- 过滤条件与序列无关时，使用逗号或 and 均可，这是因为系统内部对于 and 做了优化，即将 and 转换为逗号，逗号会按照条件先后顺序层层过滤，因此条件先后顺序不同，执行查询时会有所差别，建议尽可能将过滤能力较强的条件放在前面，以减少后面过滤条件需要查询的数据量；
- 过滤条件与序列相关时，必须使用 and，会对所有过滤条件在原表内分别筛选，再将过滤结果取交集，因此条件先后顺序不影响查询结果与性能。

## 3. 分布式表相关案例

分布式查询和普通查询的语法并无差异，理解分布式查询的工作原理有助于编写高效的 SQL 查询语句。系统首先根据 where 条件子句确定查询涉及的分区，然后分解查询语句为多个子查询，并把子查询发送到相关分区所在的位置(map)，最后在发起节点汇总所有分区的查询结果(merge)，并进行进一步的查询(reduce)。

### 3.1. 分区剪枝

场景：查询每只股票在某个时间范围内的记录数目。

首先，载入测试数据库下的表 “Snapshot” 并将该表对象赋值给变量 snapshot，示例如下：

```
snapshot = loadTable("dfs://Level1", "Snapshot")
```



#### 3.1.1. 优化前

where 条件子句根据日期过滤时，使用 `temporalFormat` 函数对于日期进行格式转换，如下：

```
timer t1 = select count(*) from snapshot 
		   where temporalFormat(DateTime, "yyyy.MM.dd") >= "2020.06.01" and temporalFormat(DateTime, "yyyy.MM.dd") <= "2020.06.02" 
		   group by SecurityID 
```

*查询耗时 4145 ms。*



#### 3.1.2. 优化后

使用 `date` 函数将 DateTime 字段转换为 DATE 类型，如下：

```
timer t2 = select count(*) from snapshot 
		   where date(DateTime) between 2020.06.01 : 2020.06.02 group by SecurityID 
```

*查询耗时 92 ms。*

```
each(eqObj, t1.values(), t2.values()) // true
```

与优化前写法相比，查询性能提升数十倍。DolphinDB 在解决海量数据的存取时，并不提供行级的索引，而是将分区作为数据库的物理索引。系统在执行分布式查询时，首先根据 where 条件确定需要的分区。大多数分布式查询只涉及分布式表的部分分区，系统无需全表扫描，从而节省大量时间。但若不能根据 where 条件确定分区，进行全表扫描，就会大大降低查询性能。

可以看到以上优化前的脚本，分区字段套用了 temporalFormat 函数先对所有日期进行转换，因此系统无法做分区剪枝。

下面例举了部分其它导致系统 **无法做分区剪枝** 的案例：

例1：对分区字段进行运算。

```
select count(*) from snapshot where date(DateTime) + 1 > 2020.06.01
```

例2：使用链式比较。

```
select count(*) from snapshot where 2020.06.01 < date(DateTime) < 2020.06.03
```

例3：过滤条件未使用分区字段。

```
select count(*) from snapshot where Volume < 500
```

例4：与分区字段比较时使用其它列。AnnouncementDate 字段非 snapshot 表中字段，此处仅为举例说明。

```
select count(*) from snapshot where date(DateTime) < AnnouncementDate - 3
```

### 3.2. group by 并行查询

**场景：对在某个时间范围内所有股票，标记涨跌，并计算第一档行情买卖双方报价之差、总交易量等指标。**

首先，载入测试数据库中的表，示例如下：

```
snapshot = loadTable("dfs://Level1", "Snapshot")
```



#### 3.2.1. 优化前

首先，筛选2020年06月01日09:30:00以后的数据，收盘价高于开盘价的记录，标志位设置为1；否则，标志位设置为0，将结果赋给一个内存表。然后，使用 group by 子句根据 SecurityID, DateTime, Flag三个字段分组，并统计分组内 OfferPrice1 的记录数以及 Volume 的和，示例如下：

```
timer {
	tmp_t = select *, iif(LastPx > OpenPx, 1, 0) as Flag 
			from snapshot 
			where date(DateTime) = 2020.06.01, second(DateTime) >= 09:30:00
	t1 = select iif(max(OfferPrice1) - min(BidPrice1) == 0, 0, 1) as Price1Diff, count(OfferPrice1) as OfferPrice1Count, sum(Volume) as Volumes 
			from tmp_t 
			group by SecurityID, date(DateTime) as Date, Flag
}
```

*查询耗时 6249 ms。*



#### 3.2.2. 优化后

不再引入中间内存表，直接从分布式表进行查询计算。示例如下：

```
timer t2 = select iif(max(OfferPrice1) - min(BidPrice1) == 0, 0, 1) as Price1Diff, count(OfferPrice1) as OfferPrice1Count, sum(Volume) as Volumes 
			from snapshot 
			where date(DateTime) = 2020.06.01, second(DateTime) >= 09:30:00 
			group by SecurityID, date(DateTime) as Date, iif(LastPx > OpenPx, 1, 0) as Flag
```

*查询耗时 1112 ms。*

```
each(eqObj, t1.values(), (select * from t2 order by SecurityID, Date, Flag).values()) // true
```

*与优化前写法相比，优化后写法查询性能提升约 6 倍。*

性能的提升来自于两个方面：

（1）优化前的写法先把分区数据合并到一个内存表，然后再用 group by 分组计算，比优化后的写法多了合并与拆分的两个步骤。

（2）优化后的写法直接对分布式表进行分组计算，充分利用 CPU 多核并行计算。而优化前的写法合并成一个内存表后，只利用单核进行分组计算。

**作为一个通用规则，对于分布式表的查询和计算，尽可能不要生成中间结果，直接在原始的分布式表上做计算，性能最优。**

### 3.3. 分组查询使用 map 关键字

*场景：查询每只股票每分钟的记录数目。*

首先，载入测试数据库表：

```
snapshot = loadTable("dfs://Level1", "Snapshot")
```

#### 3.3.1. 优化前

```
timer result = select count(*) from snapshot group by SecurityID, bar(DateTime, 60)
```

*查询耗时 996 ms。*



#### 3.3.2. 优化后

使用 map 关键字。

```
timer result = select count(*) from snapshot group by SecurityID, bar(DateTime, 60) map
```

**查询耗时 864 ms。与优化前写法相比，查询性能提升约 10%~20%。**



优化前分组查询或计算时分为两个步骤：

- 每个分区内部计算；
- 所有分区的结果进行进一步计算，以确保最终结果的正确。

如果分区的粒度大于分组的粒度，那么第一步骤完全可以保证结果的正确。此场景中，一级分区为粒度为“天”，大于分组的粒度“分钟”，可以使用 `map` 关键字，避免第二步骤的计算开销，从而提升查询性能。

## 4. 分组计算相关案例

### 4.1. 查询最新的 N 条记录

**场景：获取每只股票最新的10条记录。**

仅对2020年06月01日的数据进行分组求 TOP 10。context by 子句对数据进行分组，返回结果中每一组的行数和组内元素数量相同，再结合 `csort` 和 `top` 关键字，可以获取每组数据的最新记录。以行数为960万行的数据为例：

**OLAP 存储引擎：**

```
timer t1 = select * from loadTable("dfs://Level1", "Snapshot") where date(DateTime) = 2020.06.01 context by SecurityID csort DateTime limit -10
```

**查询耗时 4289 ms。**



**TSDB 存储引擎：**

```
timer t2 = select * from loadTable("dfs://Level1_TSDB", "Snapshot") where date(DateTime) = 2020.06.01 context by SecurityID csort DateTime limit -10 
```

**查询耗时 1122 ms。**



```
each(eqObj, t1.values(), t2.values()) //true
```

TSDB 是 DolphinDB 2.0 版本推出的存储引擎，引入了排序列，相当于对分区内部建立了一个索引。因此对于时间相关、单点查询场景，性能较 OLAP 存储引擎会有进一步提升。

**此例中，TSDB 存储引擎的查询性能较 OLAP 存储引擎提升约 4 倍。**

context by 是 DolphinDB SQL 独有的创新，是对标准 SQL 语句的拓展。在关系型数据库管理系统中，一张表由行的集合组成，行之间没有顺序。可以使用如 `min`, `max`, `avg` 等聚合函数来对行进行分组，但是不能对分组内的行使用序列相关的聚合函数，比如 `first`, `last` 等，或者使用顺序敏感的滑动窗口函数和累积计算函数，如 `cumsum`, `cummax`, `ratios`, `deltas`等。

DolphinDB 使用列式存储引擎，因此能更好地支持对时间序列的数据进行处理，而其特有的 context by 子句使组内处理时间序列数据更加方便。

### 4.2. 计算滑动 VWAP

**场景：一个内存表包含3000只股票，每只股票10000条记录，使用循环与 context by 两种方法分别计算 mwavg (移动加权平均，Moving Weighted Average)，比较二者性能差异。**

首先，产生模拟数据，示例如下：

```
syms = format(1..3000, "SH000000")
N = 10000
t = cj(table(syms as symbol), table(rand(100.0, N) as price, rand(10000, N) as volume))
```



**优化前**：

使用循环，每一次取出某只股票相应的10000条记录的价格、交易量字段，计算 `mwavg`，共执行3000次，然后合并每一次的计算结果。

```
arr = array(ANY, syms.size())

timer {
	for(i in 0 : syms.size()) {
		price_vec = exec price from t where symbol = syms[i]
		volume_vec = exec volume from t where symbol = syms[i]
		arr[i] = mwavg(price_vec, volume_vec, 4)
	}
	res1 = reduce(join, arr)
}
```

**查询耗时 25 min。**



**优化后**：

使用 context by，根据股票分组，每个分组内部分别计算 mwavg。

```
timer res2 = select mwavg(price, volume, 4) from t 
			   context by symbol
```

**查询耗时 3176 ms。**



```
each(eqObj, res1, res2[`mwavg_price]) // true
```

**两种方法的性能相差约 400 多倍。**

原因是，context by 仅对全表数据扫描一次，并对所有股票分组，再对每组分别进行计算；而 for 循环每一次循环都要扫描全表以获取某只股票相应的10000记录，所以耗时较长。

### 4.3. 计算累积 VWAP

**场景：每分钟计算每只股票自开盘到现在的所有交易的 vwap (交易量加权平均价格，Volume Weighted Average Price)。**

首先，载入测试数据库表：

```
snapshot = loadTable("dfs://Level1", "Snapshot")
```

使用 group by 对股票分组，再对时间做分钟聚合并使用 cgroup by 分组，计算 vwap；然后使用 order by 子句对分组计算结果排序，最后对每只股票分别计算累计值。

```
timer result = select wavg(LastPx, Volume) as vwap 
			   from snapshot 
			   group by SecurityID 
			   cgroup by minute(DateTime) as Minute 
			   order by SecurityID, Minute
```

*查询耗时 1499 ms。*



cgroup by (cumulative group) 为 DolphinDB SQL 独有的功能，是对标准 SQL 语句的拓展，可以进行累计分组计算，第一次计算使用第一组记录，第二次计算使用前两组记录，第三次计算使用前三组记录，以此类推。

使用 cgroup by 时，必须同时使用 order by 对分组计算结果进行排序。cgroup by 的 SQL 语句仅支持以下聚合函数：`sum`, `sum2`, `sum3`, `sum4`, `prod`, `max`, `min`, `first`, `last`, `count`, `size`, `avg`, `std`, `var`, `skew`, `kurtosis`, `wsum`, `wavg`, `corr`, `covar`, `contextCount`, `contextSum`, `contextSum2`。

### 4.4. 计算 N 股 VWAP

**场景：计算每只股票最近 1000 shares 相关的所有 trades 的 vwap。**

筛选1000 shares 时可能出现以下情形，如 shares 为100、300、600的3个 trades 之和恰好为1000，或者shares 为900、300两个 trades 之和超过1000。首先需要找到参与计算的 trades，使得 shares 之和恰好超过1000，且保证减掉时间点最新的一个 trade 后，shares 之和小于1000，然后计算一下它们的 vwap。

首先，产生模拟数据，示例如下：

```
n = 500000
t = table(rand(string(1..4000), n) as sym, rand(10.0, n) as price, rand(500, n) as vol)
```



优化前:

使用 group by 对于股票进行分组，针对每只股票分别调用自定义聚合函数 lastVolPx1，针对所有 trades 采用循环计算，并判断 shares 是否恰好超过 bound，最后计算 vwag。如下：

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

**查询耗时 187 ms。**



优化后:

使用 group by 对股票进行分组，针对每支股票分别调用自定义聚合函数 lastVolPx2，计算累积交易量向量，以及恰好满足 shares 大于 bound 的起始位置，最后计算 vwag。如下：

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

*查询耗时 73 ms。*



```
each(eqObj, lastVolPx_t1.values(), lastVolPx_t2.values()) // true
```

与优化前写法相比，lastVolPx2 使用了向量化编程方法，性能提升一倍多。因此，编写 DolphinDB SQL 时，应当尽可能地使用向量化函数，避免使用循环。

### 4.5. 分段统计股票价格变化率

**场景：已知股票市场快照数据，根据其中某个字段，分段统计并计算每只股票价格变化率。**

仅对2020年06月01日的数据举例说明。首先，使用 group by 对股票以及 OfferPrice1 字段连续相同的数据分组，然后计算每只股票第一档价格的变化率，示例如下：

```
timer t = select last(OfferPrice1) \ first(OfferPrice1) - 1 
		  from loadTable("dfs://Level1", "Snapshot") 
		  where date(DateTime) = 2020.06.01 
		  group by SecurityID, segment(OfferPrice1, false) 
```

*查询耗时 511 ms。*



`segment` 函数用于向量分组，将连续相同的元素分为一组，返回与输入向量等长的向量。下一个案例中也使用了 segment 函数分组，以展示该函数在连续区间分组计算时的易用性。

### 4.6. 计算不同连续区间的最值

**场景：期望根据某个字段的值，获取大于或等于目标值的连续区间窗口，并在每个窗口内取该字段最大值的第一条记录。**

首先，产生模拟数据，示例如下：

```
t = table(2021.09.29 + 0..15 as date, 
          0 0 0.3 0.3 0 0.5 0.3 0.5 0 0 0.3 0 0.4 0.6 0.6 0 as value)
targetVal = 0.3
```



优化前：

自定义一个函数 generateGrp，如果当前值大于或等于目标值，记录下当前记录对应的分组 ID；如果下一条记录的值小于目标值，分组 ID 加 １，以保证不同的连续数据划分到不同的分组。

```
def generateGrp(targetVal, val) {
	arr = array(INT, val.size())
	n = 1
	for(i in 0 : val.size()) {
		if(val[i] >= targetVal) {
			arr[i] = n
			if(val[i + 1] < targetVal) n = n + 1
		}
	}
	return arr
}
```

使用 context by 根据分组 ID 分组，并结合 having 语句过滤最大值，limit 语句限制返回第一条记录。

```
timer(1000) {
	tmp = select date, value, generateGrp(targetVal, value) as grp from t
	res1 = select date, value from tmp where grp != 0 
		   context by grp 
		   having value = max(value) limit 1
}
```

*查询耗时 142 ms。*



优化后：

使用 `segment` 函数结合 context by 语句对大于或等于目标值的连续数据分组，并使用 having 语句过滤。

```
timer(1000) res2 = select * from t 
				   context by segment(value >= targetVal) 
				   having value >= targetVal and value = max(value) limit 1
```

*查询耗时 123 ms。*



```
each(eqObj, res1.values(), res2.values()) // true
```

**与优化前写法相比，优化后写法查询性能提升约 10%。**

`segment` 函数一般用于序列相关的分组，与循环相比，性能略有提升，可以化繁为简，使代码更为优雅。

### 4.7. 不同聚合方式计算指标

*场景：期望根据不同的标签对于某个字段采用不同的聚合方式。*

例如，标签为 code1 时，每10分钟取 max；标签为 code2 时，每10分钟取 min；标签为 code3 时，每10分钟取 avg。最后获得一个行转列宽表。

首先，产生模拟数据，示例如下：

```
N = 1000000
t = table("code" + string(take(1..3, N)) as tag, 
          sort(take([2021.06.28T00:00:00, 2021.06.28T00:10:00, 2021.06.28T00:20:00], N)) as time, 
          take([1.0, 2.0, 9.1, 2.0, 3.0, 9.1, 9.1, 2.0, 3.0], N) as value)
```

构建一个字典，标签为键，函数名称为值。使用 group by 对时间、标签分组，并调用自定义聚合函数，实现对不同标签的 value 进行不同的运算。

```
codes = dict(`code1`code2`code3, [max, min, avg])

defg func(tag, value, codes) : codes[tag.first()](value)
 
timer {
	t_tmp = select func(tag, value, codes) as value from t 
			group by tag, interval(time, 10m, "null") as time
	t_result = select value from t_tmp pivot by time, tag
}
```

*查询耗时 76 ms。*



上例中使用的 `interval` 函数只能在 group by 子句中使用，不能单独使用，缺失值的填充方式可以为："prev", "post", "linear", "null", 具体数值和 "none"。

### 4.8. 计算股票收益波动率

*场景：已知某只股票过去十年的日收益率，期望按月计算该股票的波动率。*

首先，产生模拟数据，示例如下：

```
N = 3653
t = table(2011.11.01..2021.10.31 as date, 
          take(`AAPL, N) as code, 
          rand([0.0573, -0.0231, 0.0765, 0.0174, -0.0025, 0.0267, 0.0304, -0.0143, -0.0256, 0.0412, 0.0810, -0.0159, 0.0058, -0.0107, -0.0090, 0.0209, -0.0053, 0.0317, -0.0117, 0.0123], N) as rate)
```

使用 `interval` 函数按日期分组，并计算标准差。其中，*fill* 类型为 "prev"，表示使用前一个值填充缺失值。

```
timer res = select std(rate) from t group by code, interval(date(date), 1, "prev")
```

*查询耗时 4.029 ms。*

### 4.9. 计算股票组合的价值

*场景：进行指数套利交易回测时，计算给定股票组合的价值。*

当数据量极大时，一般数据分析系统进行回测时，对系统内存及速度的要求极高。以下案例，展现了使用 DolphinDB SQL 语言可极为简洁地进行此类计算。

为了简化起见，假定某个指数仅由两只股票组成：AAPL 与 FB。模拟数据如下：

```
syms = take(`AAPL, 6) join take(`FB, 5)
time = 2019.02.27T09:45:01.000000000 + [146, 278, 412, 445, 496, 789, 212, 556, 598, 712, 989]
prices = 173.27 173.26 173.24 173.25 173.26 173.27 161.51 161.50 161.49 161.50 161.51
quotes = table(take(syms, 100000) as Symbol, 
               take(time, 100000) as Time, 
               take(prices, 100000) as Price)
weights = dict(`AAPL`FB, 0.6 0.4)
ETF = select Symbol, Time, Price*weights[Symbol] as weightedPrice from quotes
```



优化前：

首先，需要将原始数据表的3列（时间，股票代码，价格）转换为同等长度但是宽度为指数成分股数量加1的数据表，然后向前补充空值（forward fill NULLs），进而计算每行的指数成分股对指数价格的贡献之和。示例如下：

```
timer {
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
	
	ETF_TMP1 = table(ETF.Time, ETF.Symbol, colAAPL, colFB)
	ETF_TMP2 = select last(colAAPL) as colAAPL, last(colFB) as colFB from ETF_TMP1 group by time, Symbol
	ETF_TMP3 = ETF_TMP2.ffill()
	
	t1 = select Time, rowSum(colAAPL, colFB) as rowSum from ETF_TMP3
}
```

*以上代码块耗时 713 ms。*



优化后：

使用 pivot by 子句根据时间、股票代码对于数据表重新排序，将时间作为行，股票代码作为列，然后使用 `ffill` 函数填充 NULL 元素，使用 `avg` 函数计算均值，最后 `rowSum` 函数计算每个时间点的股票价值之和，仅需以下一行代码，即可实现上述所有步骤。示例如下：

```
timer t2 = select rowSum(ffill(last(weightedPrice))) from ETF pivot by Time, Symbol
```

**查询耗时 23 ms。**

```
each(eqObj, t1.values(), t2.values()) //true
```



**与优化前写法相比，优化后写法查询性能提升约 30 倍。**

此例中，仅以两只股票举例说明，当股票数量更多时，使用循环遍历的方式更为繁琐，而且性能极低。

pivot by 是 DolphinDB SQL 独有的功能，是对标准 SQL 语句的拓展，可以将表中两列或多列的内容按照两个维度重新排列，亦可配合数据转换函数使用。不仅编程简洁，而且无需产生中间过程数据表，有效避免了内存不足的问题，极大地提升了计算速度。



以下是与此场景类似的另外一个案例，属于物联网典型场景。

**场景：假设一个物联网场景中存在三个测点进行实时数据采集，期望针对每个测点分别计算一分钟均值，再对同一分钟的三个测点均值求和。**

首先，产生模拟数据，示例如下：

```
N = 10000
t = table(take(`id1`id2`id3, N) as id, 
          rand(2021.01.01T00:00:00.000 +  100000 * (1..10000), N) as time, 
          rand(10.0, N) as value)
```

使用 `bar` 函数对时间做一分钟聚合，并使用 pivot by 子句根据分钟、测点对数据表重新排序，将分钟作为行，测点作为列，然后使用 ffill 函数填充 NULL 元素，使用 avg 函数计算均值，然后再使用 rowSum 函数计算每个时间点的测点值之和。最后使用 group by 子句结合 interval 函数对于缺失值进行填充。

```
timePeriod = 2021.01.01T00:00:00.000 : 2021.01.01T01:00:00.000
timer result = select sum(rowSum) as v from (
    		   select rowSum(ffill(avg(value))) from t 
    		   where id in `id1`id2`id3, time between timePeriod 
    		   pivot by bar(time, 60000) as minute, id) 
    		   group by interval(minute, 1m, "prev") as minute
```

**查询耗时 12 ms。**

### 4.10. 根据成交量切分时间窗口

**场景：已知股票市场分钟线数据，期望根据成交量对股票在时间上进行切分，最终得到时间窗口不等的若干条数据，包含累计成交量，以及每个窗口的起止时间。**

具体切分规则为：假如期望对某只股票成交量约150万股便进行一次时间切分。切分时，如果当前组加上下一条数据的成交量与150万更接近，则下一条数据加入当前组；否则，从下一条数据开始一个新的组。

首先，产生模拟数据，示例如下：

```
N = 28
t = table(take(`600000.SH, N) as wind_code, 
          take(2015.02.11, N) as date, 
          take(13:03:00..13:30:00, N) as time, 
          take([288656, 234804, 182714, 371986, 265882, 174778, 153657, 201388, 175937, 138388, 169086, 203013, 261230, 398971, 692212, 494300, 581400, 348160, 250354, 220064, 218116, 458865, 673619, 477386, 454563, 622870, 458177, 880992], N) as volume)
```

根据切分规则，自定义一个累计函数 caclCumVol，如果当前组需要包含下一条数据的成交量，返回新的累计成交量；否则，返回下一条数据的成交量，即开始一个新的组。

```
def caclCumVol(target, cumVol, nextVol) {
	newVal = cumVol + nextVol
	if(newVal < target) return newVal
	else if(newVal - target > target - cumVol) return nextVol
	else return newVal
}
```

使用高阶函数 `accumulate`，迭代地应用 caclCumVol 函数到前一个累计成交量和下一个成交量上。如果累计成交量等于当前一条数据的成交量，则表示开始一个新的组，此时记录下当前这条数据的时间，作为一个窗口的起始时间，否则为空，通过 ffill 填充，使得同一组数据拥有相同的起始时间，最后根据起始时间分组并做聚合计算。

```
timer result = select first(wind_code) as wind_code, first(date) as date, sum(volume) as sum_volume, last(time) as endTime 
			   from t 
			   group by iif(accumulate(caclCumVol{1500000}, volume) == volume, time, NULL).ffill() as startTime
```

**查询耗时 0.9 ms。**

### 4.11. 股票因子归整

**场景：已知沪深两市某个10分钟因子，分别存储为一张分布式表，另有一张股票清单维度表存储股票代码相关信息。期望从沪市、深市分别取出部分股票代码相应因子，根据股票、日期对于因子做分组归整，并做行列转换。**

首先，自定义一个函数 createDBAndTable，用于创建分布式库表，如下：

```
def createDBAndTable(dbName, tableName) {
    if(existsTable(dbName, tableName)) return loadTable(dbName, tableName)
    dbDate = database(, VALUE, 2021.07.01..2021.07.31)
    dbSecurityID = database(, HASH, [SYMBOL, 10])
    db = database(dbName, COMPO, [dbDate, dbSecurityID])
    model = table(1:0, `SecurityID`Date`Time`FactorID`FactorValue, [SYMBOL, DATE, TIME, SYMBOL, DOUBLE])
    return createPartitionedTable(db, model, tableName, `Date`SecurityID)
}
```

执行以下代码，创建两个分布式表、一个维度表，并写入模拟数据，如下：

```
dates = 2020.01.01..2021.10.31
time = join(09:30:00 + 1..12 * 60 * 10, 13:00:00 + 1..12 * 60 * 10)

syms = format(1..2000, "000000") + ".SH"
tmp = cj(cj(table(dates), table(time)), table(syms))
t = table(tmp.syms as SecurityID, tmp.dates as Date, tmp.time as Time, take(["Factor01"], tmp.size()) as FactorID, rand(100.0, tmp.size()) as FactorValue)

createDBAndTable("dfs://Factor10MinSH", "Factor10MinSH").append!(t)

syms = format(2001..4000, "000000") + ".SZ"
tmp = cj(cj(table(dates), table(time)), table(syms))
t = table(tmp.syms as SecurityID, tmp.dates as Date, tmp.time as Time, take(["Factor01"], tmp.size()) as FactorID, rand(100.0, tmp.size()) as FactorValue)
createDBAndTable("dfs://Factor10MinSZ", "Factor10MinSZ").append!(t)

db = database("dfs://infodb", VALUE, 1 2 3)
model = table(1:0, `SecurityID`Info, [SYMBOL, STRING])
if(!existsTable("dfs://infodb", "MdSecurity")) createTable(db, model, "MdSecurity")
loadTable("dfs://infodb", "MdSecurity").append!(
    table(join(format(1..2000, "000000") + ".SH", format(2001..4000, "000000") + ".SZ") as SecurityID, 
          take(string(NULL), 4000) as Info))

setMaxMemSize(32)
```



**优化前**：

首先，分别从沪市、深市取出因子 Factor01 在某个时间范围的数据，合并后，再从股票代码维度表中取出需要归整的股票，通过表连接方式对合并结果进行过滤，最后使用 pivot by 子句根据时间、股票代码两个维度重新排列。

```
timer {
    nt1 = select concatDateTime(Date, Time) as TradeTime, SecurityID, FactorValue from loadTable("dfs://Factor10MinSH", "Factor10MinSH") where Date between 2019.01.01 : 2020.10.31, FactorID = "Factor01"
    nt2 = select concatDateTime(Date, Time) as TradeTime, SecurityID, FactorValue from loadTable("dfs://Factor10MinSZ", "Factor10MinSZ") where Date between 2019.01.01 : 2020.10.31, FactorID = "Factor01"
    unt = unionAll(nt1, nt2)
    
    sec = select SecurityID from loadTable("dfs://infodb", "MdSecurity") where substr(SecurityID, 0, 3) in ["001", "003", "005", "007"]
    res = select * from lj(sec, unt, `SecurityID)

    res1 = select FactorValue from res pivot by TradeTime, SecurityID
}
```

**查询耗时 6922 ms。**



**优化后**：

首先，从股票代码维度表中取出需要归整的股票列表，然后从沪深两市取出因子 Factor01。使用 in 关键字进行过滤，再使用 pivot by 根据时间、股票代码两个维度进行重新排列，最后合并结果。

```
timer {
    sec = exec SecurityID from loadTable("dfs://infodb", "MdSecurity") where substr(SecurityID, 0, 3) in ["001", "003", "005", "007"]
    schema(loadTable("dfs://Factor10MinSH", "Factor10MinSH"))
    nt1 = exec FactorValue from loadTable("dfs://Factor10MinSH", "Factor10MinSH") where Date between 2019.01.01 : 2020.10.31, SecurityID in sec, FactorID = "Factor01" pivot by concatDateTime(Date, Time), SecurityID
    nt2 = exec FactorValue from loadTable("dfs://Factor10MinSZ", "Factor10MinSZ") where Date between 2019.01.01 : 2020.10.31, SecurityID in sec, FactorID = "Factor01" pivot by concatDateTime(Date, Time), SecurityID

    res3 = merge(nt1.setIndexedMatrix!(), nt2.setIndexedMatrix!(), 'left')
}
```

**查询耗时 4210 ms。**

**与优化前相比，优化后查询性能提升约 40%。**

综合对比上述写法，概括出几个 SQL 编写技巧：

（1）尽量避免不必要的表连接；

（2）尽可能早地使用分区过滤；

（3）推迟数据的合并。

### 4.12. 根据交易额统计单子类型

**场景：对不同日期、不同股票、买单卖单，分别统计某个时间范围内的特大单、大单、中单、小单的累计交易量、交易额。**

具体规则为：交易额小于4万是小单，大于等于4万且小于20万是中单，大于等于20万且小于100万是大单，大于100万是特大单。

首先，产生模拟数据，示例如下：

```
N = 1000000
t = table(take(2021.11.01..2021.11.15, N) as date, 
          take([09:30:00, 09:35:00, 09:40:00, 09:45:00, 09:47:00, 09:49:00, 09:50:00, 09:55:00, 09:56:00, 10:00:00], N) as time, 
          take(`AAPL`FB`MSFT$SYMBOL, N) as symbol, 
          take([10000, 30000, 50000, 80000, 100000], N) as volume, 
          rand(100.0, N) as price, 
          take(`BUY`SELL$SYMBOL, N) as side)
```



**优化前**：

使用 group by 根据日期、股票、买卖方向分组，使用四个查询语句分别计算小单、中单、大单、特大单的累计交易量、交易额，再将结果合并。

```
timer {
	// 小单
	resS = select sum(volume) as volume_sum, sum(volume * price) as amount_sum, 0 as type 
			from t 
			where time <= 10:00:00, volume * price < 40000 
			group by date, symbol, side
	// 中单
	resM = select sum(volume) as volume_sum, sum(volume * price) as amount_sum, 1 as type 
			from t 
			where time <= 10:00:00, 40000 <= volume * price < 200000 
			group by date, symbol, side
	// 大单
	resB = select sum(volume) as volume_sum, sum(volume * price) as amount_sum, 2 as type 
			from t 
			where time <= 10:00:00, 200000 <= volume * price < 1000000 
			group by date, symbol, side
	// 特大单
	resX = select sum(volume) as volume_sum, sum(volume * price) as amount_sum, 3 as type 
			from t 
			where time <= 10:00:00, volume * price >= 1000000 
			group by date, symbol, side
	
	res1 = table(N:0, `date`symbol`side`volume_sum`amount_sum`type, [DATE, SYMBOL, SYMBOL, LONG, DOUBLE, INT])
	res1.append!(resS).append!(resM).append!(resB).append!(resX)
}
```

**查询耗时 135 ms。**



**第一种优化写法：**

自定义一个函数 getType，使用 `iif` 函数嵌套方式得到当前成交单子类型，然后使用 group by 对日期、股票、买卖方向、单子类型分组，并计算累计交易量、交易额。

```
def getType(amount) {
	return iif(amount < 40000, 0, iif(amount >= 40000 && amount < 200000, 1, iif(amount >= 200000 && amount < 1000000, 2, 3)))
}

timer res2 = select sum(volume) as volume_sum, sum(volume*price) as amount_sum 
				from t 
				where time <= 10:00:00
				group by date, symbol, side, getType(volume * price) as type 
```

**查询耗时 114 ms。**

**与优化前写法相比，优化后写法查询性能提升约 20%。** 虽然性能略有提升，但大大简化了代码编写。

需要注意的是，此处有个优化技巧，group by 后面字段类型为 INT、LONG、SHORT、SYMBOL 时，系统内部进行了优化，查询性能会有一定提升，所以本例中 getType 函数返回类型为 INT。

**第二种优化写法**：

```
range = [0.0, 40000.0, 200000.0, 1000000.0, 100000000.0]

timer res3 = select sum(volume) as volume_sum, sum(volume*price) as amount_sum 
				from t 
				where time <= 10:00:00 
				group by date, symbol, side, asof(range, volume*price) as type
```

**查询耗时 95 ms。**

与第一种优化写法区别在于，使用 `asof` 函数而非自定义函数，判断交易额落在哪个区间，然后以此分组并计算累计交易量、交易额。

```
each(eqObj, (select date, symbol, side, type, volume_sum, amount_sum 
             from res1 order by date, symbol, side, type).values(), res2.values()) // true
each(eqObj, res2.values(), res3.values()) // true
```



以下是 asof 函数在另外一个场景下的应用。

**场景：针对某个日期、某只股票，统计某一数值列落在不同的区间范围的记录数目。**

首先，产生模拟数据，示例如下：

```
N = 100000
t = table(take(2021.11.01, N) as date, 
          take(`AAPL, N) as code, 
          rand([-5, 5, 10, 15, 20, 25, 100], N) as value)
range = [-9999, 0, 10, 30, 9999]
```



**优化前**：

自定义一个函数 generateGrp，遍历不同的区间范围，判断数值列是否包含在当前的区间范围内，区间范围遵循左闭右开原则，并返回一个布尔型向量。如果为 true，表示数值包含在当前的区间范围内，则以下划线连接区间范围的左右边界作为分组 ID；如果为 false，表示数值不包含在当前的区间范围内，则将其置为空字符串。

然后使用高阶函数 `reduce` 将遍历结果合并，最后使用 group by 根据日期、股票、不同的区间范围分组，并聚合计算记录数目。

```
def generateGrp(range, val) {
	res = array(ANY, range.size()-1)
	for(i in 0 : (range.size()-1)) {
		cond = val >= range[i] && val < range[i+1]
		res[i] = iif(cond, strReplace(range[i] + "_" + range[i+1], "-", ""), string(NULL))
	}
	return reduce(add, res)
}

timer res1 = select count(*) from t group by date, code, generateGrp(range, value) as grp
```

**查询耗时 38 ms。**



**优化后**：

使用 asof 函数结合 group by 语句对于日期、股票、不同的区间范围分组，并聚合计算记录数目。

```
timer res2 = select count(*) from t 
			group by date, code, asof(range, value) as grp
```

**查询耗时 14 ms。**

**与优化前写法相比，优化后写法查询性能提升约 2 倍多。**

asof 函数一般用于分段统计，与循环相比，不仅性能大大提升，而且代码更为简洁。下一个案例也是使用了 asof 函数用于统计。

## 5. 元编程相关案例

### 5.1. 动态生成 SQL 语句案例 1

**场景：已知股票市场分钟线数据，使用元编程方式，根据股票、日期分组，每隔 10 分钟做一次聚合计算。**

首先，产生模拟数据，示例如下：

```
N = 10000000
t = table(take(format(1..4000, "000000") + ".SH", N) as SecurityID, 
          take(2021.10.01..2021.10.31, N) as TradeDate, 
          take(join(09:30:00 + 1..120 * 60, 13:00:00 + 1..120 * 60), N) as TradeTime, 
          rand(100.0, N) as Px)

barMinutes = 10
```



**优化前**：

查询语句拼接为一个字符串，使用 `parseExpr` 函数将字符串解析为元代码，再使用 `eval` 函数执行生成的元代码。

```
res = parseExpr("select " + avg + "(Px) as avgPx from t group by bar(TradeTime, " + barMinutes + "m) as minuteTradeTime, SecurityID, TradeDate").eval()
```

**查询耗时 219 ms。**



**优化后**：

DolphinDB 内置了 `sql` 函数用于动态生成 SQL 语句，然后使用 eval 函数执行生成的 SQL 语句。其中，`sqlCol` 函数将列名转化为表达式，`makeCall` 函数指定参数调用 `bar` 函数并生成脚本，`sqlColAlias` 函数使用元代码和别名定义一个列。

```
groupingCols = [sqlColAlias(makeCall(bar, sqlCol("TradeTime"), duration(barMinutes.string() + "m")), "minuteTradeTime"), sqlCol("SecurityID"), sqlCol("TradeDate")]
res = sql(select = sqlCol("Px", funcByName("avg"), "avgPx"), 
          from = t, groupBy = groupingCols, groupFlag = GROUPBY).eval()
```

**查询耗时 200 ms。**

类似地，`sqlUpdate` 函数用于动态生成 SQL update 语句的元代码，`sqlDelete` 函数用于动态生成 SQL delete 语句的元代码。

### 5.2. 动态生成 SQL 语句案例 2

**场景：每天需要执行一组查询，合并查询结果。**

首先，产生模拟数据，示例如下：

```
N = 100000
t = table(take(50982208 51180116 41774759, N) as vn, 
          rand(25 1180 50, N) as bc, 
          take(814 333 666, N) as cc, 
          take(11 12 3, N) as stt, 
          take(2 116 14, N) as vt, 
          take(2020.02.05..2020.02.05, N) as dsl, 
          take(52354079..52354979, N) as mt)
```

例如，每天需要执行一组查询，如下：

```
t1 = select * from t where vn=50982208, bc=25, cc=814, stt=11, vt=2, dsl=2020.02.05, mt < 52355979 order by mt desc limit 1
t2 = select * from t where vn=50982208, bc=25, cc=814, stt=12, vt=2, dsl=2020.02.05, mt < 52355979 order by mt desc limit 1
t3 = select * from t where vn=51180116, bc=25, cc=814, stt=12, vt=2, dsl=2020.02.05, mt < 52354979 order by mt desc limit 1
t4 = select * from t where vn=41774759, bc=1180, cc=333, stt=3, vt=116, dsl=2020.02.05, mt < 52355979 order by mt desc limit 1

reduce(unionAll, [t1, t2, t3, t4])
```

以下案例通过元编程动态生成 SQL 语句实现。过滤条件包含的列和排序的列相同，可编写如下自定义函数 bundleQuery 实现相关操作：

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

bundleQuery 中各个参数的含义如下：

- tbl 是数据表。
- dt 是过滤条件中日期的值。
- dtColName 是过滤条件中日期列的名称。
- mt 是过滤条件中 mt 的值。
- mtColName 是过滤条件中 mt 列的名称，以及排序列的名称。
- filterColValues 是其他过滤条件中的值，用元组表示，其中的每个向量表示一个过滤条件，每个向量中的元素表示该过滤条件的值。
- filterColNames 是其他过滤条件中的列名，用向量表示。

上面一组 SQL 语句，相当于执行以下代码：

```
dt = 2020.02.05
dtColName = "dsl"
mt = 52355979
mtColName = "mt"
colNames = `vn`bc`cc`stt`vt
colValues = [50982208 50982208 51180116 41774759, 25 25 25 1180, 814 814 814 333, 11 12 12 3, 2 2 2 116]

bundleQuery(t, dt, dtColName, mt, mtColName, colValues, colNames)
```

登录 admin 管理员用户后，执行以下脚本将 bundleQuery 函数定义为函数视图，以确保在集群的任何节点重启系统之后，都可直接调用该函数。

```
addFunctionView(bundleQuery)
```

如果每次都手动编写全部 SQL 语句，工作量大，并且扩展性差，通过元编程动态生成 SQL 语句可以解决这个问题。
# **DolphinDB SQL教程**

DolphinDB脚本语言的SQL语法与例如MYSQL、Oracle、SQL Server等常用关系型数据库的标准SQL语言十分相似。与标准SQL语言相比，DolphinDB SQL的优点在于：

（1）在DolphinDB中，脚本语言与SQL语言无缝融合。SQL语句中可引用DolphinDB中任何变量及函数。

（2）DolphinDB对标准SQL语法进行了多项扩展，方便用户使用。

在分布式数据库中使用SQL语句进行查询与计算时，SQL语句要遵循分区剪枝的原则，才可保证最优性能，否则有可能遍历所有分区，造成性能低下。请务必详细阅读第6.2节"分区剪枝"。

运行本教程代码示例前，请先使用`login`命令登录。

本教程中所用的csv数据文件，可由[此处](https://www.dolphindb.cn/downloads/tutorial/SQL.zip)下载，并存于文件夹 YOURDIR 中。

## 1. DolphinDB SQL基本语法

### 1.1 创建数据表

与标准SQL使用 CREATE TABLE ... 创建数据表的方法不同，在DolphinDB中使用以下函数创建各类数据表：
- 函数`table`创建普通内存表
- 函数`streamTable`创建流数据表
- 函数`indexedTable`创建索引内存表
- 函数`keyedTable`创建键值内存表
- 函数`keyedStreamTable`创建键值流数据表
- 函数`createPartitionedTable`创建分区表，包括分布式表、分区内存表、分区键值内存表、分区流数据表等。
- 函数`createTable`创建维度表

以`table`函数为例，若根据指定列名及相应的数据类型创建空表：
```
t1=table(200:0, `date`ticker`price, [DATE,SYMBOL,FLOAT]);
```
其中，200:0指的是预先为该表分配200行的内存，表的初始长度为0，即空表。

若根据已有数据创建内存表：
```
t2=table(2020.10.28 2020.10.28 2020.10.29 2020.10.29 as date, `600519`601857`600519`601857 as ticker, 12747.3 4.05 12701.81 4.07 as price);
```
### 1.2 插入数据

- 向内存表插入数据，可使用语法与标准SQL一致的 SQL insert into 语句，亦可使用`append!`或`tableInsert`函数。
```
t1=table(200:0, `date`ticker`price, [DATE,SYMBOL,FLOAT])
insert into t1 values (2020.10.28 2020.10.28, `600519`601857, 12747.3 4.05)

t2=table(2020.10.29 2020.10.29 as date, `600519`601857 as ticker, 12701.81 4.07 as price)
t1.append!(t2);
```
- 向非索引内存表或键值内存表的内存表中插入重复数据，内存表中会保存重复数据。

将上例中的```t1.append!(t2);```重复执行一遍，在结果中会发现，t2的数据出现了两次。

- 向索引内存表或键值内存表中插入重复索引或键值的数据，内存表中会保存最新的数据。
```
t1=indexedTable(`date`ticker, 2020.10.28 2020.10.28 as date, `600519`601857 as ticker, 12747.3 4.05 as price)
insert into t1 values (2020.10.28 2020.10.28, `600519`601857, 12747.3 4.05)

t2=table(2020.10.29 2020.10.29 as date, `600519`601857 as ticker, 12701.81 4.07 as price)
t1.append!(t2);
t1.append!(t2);
```
虽然t2的数据被插入两次，但是在结果中，只出现一次。

- 向分布式表中插入数据，不可使用 SQL insert into 子句，需使用`append!`或`tableInsert`函数。
```
db=database("dfs://db1", RANGE, 0 20 40 60 80 100)
n=100000
id=rand(99,n)
val=rand(100.0,n)
t=table(id,val)
pt=db.createPartitionedTable(t,`pt,`id).append!(t);

tmp=table(rand(100,10000) as id,take(200.0,10000) as val);
pt.append!(tmp)
```

### 1.3 select 与 exec

select子句可以使用原生字段、函数调用（聚合函数，向量函数，序列函数，或自定义函数）或复杂的表达式，也可以是复合字段，亦可引用SQL语句外的变量。
```
y=6
t=table(2020.11.01..2020.11.10 as date, 1 9 7 4 3 2 6 8 0 5 as x)
select date, cumsum(x>y) as z from t
```
传统的关系型数据库是基于行存储，在select读取部分属性的数据时需要读取全部数据；而DolphinDB是基于列式存储，在select读取部分列时无需读取其他列，因此读取速度更快，内存占用更少。使用select子句时，应只选择需要的列，尽量避免 select * 选择所有列，尤其是当表的列数较多时。

from之后的内容可以是表、一个表达式或函数调用，join或嵌套的join。常用的函数包括`objByName`与`loadTable`等。任何一个返回table对象的内置函数或者自定义函数都可以用在from子句中。
```
select count(*) from loadTable("dfs://db1", `pt)
```
select子句总是生成一张表，即使只选择一列亦是如此。若需要生成一个标量或者一个向量，可使用exec子句。

```
t=table(2020.11.01..2020.11.10 as date, 1 9 7 4 3 2 6 8 0 5 as x)
s = select x from t 
typestr s;
```
结果为：IN-MEMORY TABLE
```
s = exec x from t 
typestr s;
```
结果为：FAST INT VECTOR

### 1.4 where

where子句包含条件表达式。条件表达式中的函数可以是内置函数（聚合，序列或向量函数）或自定义函数。

可使用`sample`函数对分区进行抽样。例如，抽取分布式表中5%分区中的数据或5个分区中的数据：
```
//抽样10%分区
select * from pt where sample(date, 0.05)

//抽样10个分区
select * from pt where sample(date, 5)
```

DolphinDB不支持在分布式查询的where子句中使用聚合函数，如`sum`或`count`，这是因为执行聚合函数之前，分布式查询要使用where子句来选择相关分区。 如果聚合函数出现在where子句中，则分布式查询不能缩窄相关的分区范围。若需要在分布式查询的where子句中使用聚合函数，可以编写分布式查询来计算这些聚合函数的值，再将这些值分配给某些变量，并在原始分布式查询中引用这些变量。

### 1.5 group by 与 cgroup by

group by关键字可对记录进行分组，对每个组内的记录执行函数。分组列名会自动加入到结果集中，因此和标准SQL的区别在于DolphinDB中，用户不需要在select子句中指定该列。

分组列亦可为表达式：
```
t=table(2020.11.26+0..9 as date, 0..9 as x)
select avg(x) from t group by month(date) as month
```

对分布式表或分区内存表的查询中使用group by是并行对各个分区进行查询，而对未分区内存表使用group by是串行计算各个分区，因此前者的性能优于后者。

下例中，数据表t为未分区内存表，数据表pt为分区内存表。

```
n=10000000
id=take(1..1000,n).sort()
date=2019.12.31+take(1..365,n)
price=rand(50.0,n)
size=rand(1000,n)
t=table(id,date,price,size)
db=database("",RANGE,date(2020.01M..2021.01M))
pt=db.createPartitionedTable(t,`pt,`date)
pt.append!(t)

>timer(10) select avg(price) from t group by date
Time elapsed: 1050.695ms

>timer(10) select avg(price) from pt group by date
Time elapsed: 224.398ms
```
在pt上执行group by，耗时仅为在t上执行耗时的约20%。请注意，两者的差距与系统CPU核数有关。系统的CPU核数越多，平行计算的优势越大，两者耗时的差距也就越大。

使用cgroup by（cumulative group，为DolphinDB SQL独有功能，是对标准SQL语句的拓展）子句可进行累计分组计算，第一次计算使用第一个组的记录，第二次计算使用前两个组的记录，第三次计算使用前三个组的记录，以此类推。使用cgroup by时，必须同时使用order by对分组计算结果进行排序。使用cgroup by的SQL语句只支持以下聚合函数：sum, sum2, sum3, sum4, prod, max, min, first, last, count, size, avg, std, var, skew, kurtosis, wsum, wavg, corr, covar, contextCount, contextSum, contextSum2.

例：使用cgroup by计算日内累积交易量加权平均交易价格（volume weighted average price, 简称vwap）。每分钟计算自开盘到现在的所有交易的vwap。

```
t = table(`A`A`A`A`B`B`B`B as sym, 09:30:06 09:30:28 09:31:46 09:31:59 09:30:19 09:30:43 09:31:23 09:31:56 as time, 10 20 10 30 20 40 30 30 as volume, 10.05 10.06 10.07 10.05 20.12 20.13 20.14 20.15 as price);
select wavg(price, volume) as wvap from t group by sym cgroup by minute(time) as minute order by sym, minute;
```
结果为：
```
sym minute wvap
--- ------ ---------
A   09:30m 10.056667
A   09:31m 10.055714
B   09:30m 20.126667
B   09:31m 20.135833
```

### 1.6 pivot by

pivot by是DolphinDB SQL的独有功能，是对标准SQL语句的拓展。它将表中某列的数据按照两个维度重新排列，亦可配合数据转换函数使用。与select子句一同使用时返回一个表，而和exec语句一同使用时返回一个矩阵。pivot by支持多个分组字段，支持输出多个指标。

例１：对比同一时间段不同股票的平均价格：

```
sym = `A`B`B`B`C`C`A`A`A 				
price = 49.6 29.46 29.5 29.51 174.97 175.03 49.66 49.71 49.8							
timestamp = [09:34:07,09:35:42,09:36:51,09:36:59,09:35:47,09:36:26,09:34:16,09:35:26,09:36:12]
t = table(sym, timestamp, price)
select avg(price) from t pivot by timestamp.minute() as minute, sym;
```
结果为：
```
minute A     B      C
------ ----- ------ ------
09:34m 49.63
09:35m 49.71 29.46  174.97
09:36m 49.80 29.505 175.03
```

例２：计算每个时刻的投资组合价值。下例中的投资组合的股票代码由向量syms表示，各股票的持仓数量由向量holdings表示。

首先对数据使用pivot by进行重新排列：

```
trades = loadText(yourDIR+"trades.csv")
syms = `600000`600300`600400`600500`600600`600800`600900
tmp = select price from trades where date=2020.06.01, symbol in syms, time between 09:30:00.000 : 15:00:00.000 pivot by time, symbol
select top 10 * from tmp;
```

结果为：

```
time         C600000 C600300 C600400 C600500 C600600 C600800 C600900
------------ ------- ------- ------- ------- ------- ------- -------
09:30:00.000 10.63   3.09    3.28    5.03    63.5    4.68    17.43
09:30:03.000 10.62   3.08    3.28    5.03    63.5    4.68    17.4
09:30:05.000 10.61                                   4.68    17.41
09:30:06.000         3.08    3.28    5.02    63.51
09:30:08.000 10.62                                   4.68    17.41
09:30:09.000         3.07    3.28    5.03    63.74
09:30:11.000 10.63                                   4.68    17.42
09:30:12.000         3.07    3.27    5.03    63.95
09:30:14.000 10.64                                   4.68    17.43
09:30:15.000         3.06            5.03    63.95
```

可见并不是所有股票均在同一时刻更新数据。若要计算每个时刻的投资组合价值，首先将股票价格与持仓数量相乘，然后使用`ffill`函数向前填充空值，再将所有股票持仓价值相加：

```
holdings = 100 200 400 800 600 400 300
holdingsDict = dict(syms, holdings)
update trades set value=price*holdingsDict[symbol]

portfolioValue = select rowSum(ffill(last(value))) from trades where date=2020.06.01, symbol in syms, time between 09:30:00.000 : 15:00:00.000 pivot by time, symbol
```

### 1.7 context by 与 csort

context by是DolphinDB独有的功能，是对标准SQL语句的拓展。使用context by子句可以简化对面板数据(panel data)的操作。

传统的关系型数据库中，一张数据表的行之间没有顺序。可以使用如min, max, avg, stdev等与行的顺序无关的聚合函数，但不能使用DolphinDB中例如first, last等对行的顺序敏感的聚合函数，或例如cumsum, cummax, ratios, deltas等对行的顺序敏感的向量函数。

例１：计算每只股票过去20次数据更新（绝大部分情况下为1分钟）的移动平均价格：
```
trades = select * from loadText(yourDIR+"trades.csv") order by symbol, date, time
t = select symbol, mavg(price,20) as mavg_price from trades where date=2020.06.01 context by symbol
```

例２：计算每只股票在2020.06.01中截止到当前时刻的每次数据更新（绝大部分情况下为3秒）中最大交易量：

```
t = select symbol, date, time, cummax(volume) from trades where date=2020.06.01 context by symbol, date
```

例3：结合聚合函数使用，将聚合函数的分组计算结果赋予组内每一行：

```
t = select symbol, date, time, max(volume) from trades where date=2020.06.01 context by symbol, date
```

在context by语句后使用csort关键字排序。使用context by分组后，csort在select从句的表达式执行之前，对每个组内的数据进行排序。可对多个列（包括计算列）使用csort关键字，在组内进行升序或降序排序。csort关键字还可以和top关键字一起使用，用于获取每个分组中的最新记录。

例4：context by 与csort、top子句一起使用，获取每只股票的两条最新记录：

```
select top 2 * from trades context by symbol csort date desc, time desc
```

### 1.8 having

having子句总是跟在group by或者context by后，用来将select语句返回的结果再次进行过滤，只返回满足指定条件的聚合函数值的组结果。详细使用说明请参考用户手册http://www.dolphindb.cn/cn/help/index.html。

如果having用在group by后，having只可与聚合函数一起使用，为符合聚合函数条件的每组产生一条记录。
```
trades = select * from loadText(yourDIR+"trades.csv") order by symbol, date, time

t = select sum(volume) from trades where date=2020.06.01 group by symbol, minute(time) as minute having min(price)>50
select top 10 * from t
```
结果为：
```
symbol	minute	sum_volume
600600	09:25m	41,800
600600	09:30m	102,889
600600	09:31m	95,600
600600	09:32m	92,500
600600	09:33m	91,001
600600	09:34m	103,100
600600	09:35m	71,599
600600	09:36m	35,800
600600	09:37m	36,200
600600	09:38m	67,500
```

如果having用在context by后，并且只与聚合函数一起使用，结果是符合聚合函数条件的分组，每组记录数与输入数据中记录数一致。
```
t = select *, minute(time) as minute, sum(volume) from trades where date=2020.06.01 context by symbol, minute(time) as minute having min(price)>50
select top 10 * from t
```
结果为：
```
symbol	date	    time	        price	volume	minute	sum_volume
600600	2020.06.01	09:25:00.000	63.5	41,800	09:25m	41,800
600600	2020.06.01	09:25:03.000	63.5	0	    09:25m	41,800
600600	2020.06.01	09:30:00.000	63.5	400	    09:30m	102,889
600600	2020.06.01	09:30:03.000	63.5	48,991	09:30m	102,889
600600	2020.06.01	09:30:06.000	63.51	25,098	09:30m	102,889
600600	2020.06.01	09:30:09.000	63.74	6,500	09:30m	102,889
600600	2020.06.01	09:30:12.000	63.95	1,500	09:30m	102,889
600600	2020.06.01	09:30:15.000	63.95	500	    09:30m	102,889
600600	2020.06.01	09:30:18.000	63.95	1,800	09:30m	102,889
600600	2020.06.01	09:30:21.000	63.56	1,000	09:30m	102,889
```
如果having用在context by后，与非聚合函数一起使用，结果是符合指定条件的分组。
```
t = select *, cumsum(volume) from trades where date=2020.06.01, time>09:30:00.000 context by symbol having sum(volume)>5000000
select top 10 * from t
```
结果为：
```
symbol	date	    time	        price	volume	cumsum_volume
600000	2020.06.01	09:30:03.000	10.62	34,200	34,200
600000	2020.06.01	09:30:05.000	10.61	110,100	144,300
600000	2020.06.01	09:30:08.000	10.62	144,900	289,200
600000	2020.06.01	09:30:11.000	10.63	52,500	341,700
600000	2020.06.01	09:30:14.000	10.64	35,900	377,600
600000	2020.06.01	09:30:17.000	10.65	55,300	432,900
600000	2020.06.01	09:30:20.000	10.64	54,100	487,000
600000	2020.06.01	09:30:23.000	10.65	17,800	504,800
600000	2020.06.01	09:30:26.000	10.64	16,300	521,100
600000	2020.06.01	09:30:29.000	10.65	41,300	562,400
```
### 1.9 order by

order by 关键字用于对查询与计算结果进行排序，默认升序排序，可使用desc关键字进行降序排序。order by可与group by配合使用，order by的字段必须是group by结果表中的字段。
```
select count(*) from trades group by date order by date desc
```
结果为：
```
date	count
2020.06.05	29,994
2020.06.04	29,551
2020.06.03	31,420
2020.06.02	30,043
2020.06.01	30,625
```

### 1.10 top 与 limit

top 与 limit 均可限制返回记录的数量，亦可与context by子句一同使用，以限制结果中每组记录的数量。

top 与 limit 的区别在于：

- top子句只能使用非负整数，返回一个数据表最初的n行；limit子句在于context by子句同时使用时，亦可使用负整数返回每组最后的n行。

- 可使用limit子句从某行开始选择一定数量的行。

返回trades表的前2行：
```
select top 2 * from trades
```

返回每只股票的第1行：
```
select top 1 * from trades context by symbol
```

返回每只股票的最后1行：
```
select * from trades context by symbol limit -1
```

返回自第3行开始的5行：
```
select * from trades limit 2, 5
```

### 1.11 map

若使用map子句，SQL语句会在每个分区内分别执行，然后将结果合并。
```
t = table((1 2 1 2 1 2 1) as id, (1 1 2 5 1 2 1) as qty)
db=database("dfs://valuedb", VALUE, 1..10)
pt = db.createPartitionedTable(t, `pt, `id)
pt.append!(t);

select *, cumsum(qty) from pt map;
```
结果为
```
id qty cumsum_qty
-- --- ----------
1  1   1
1  2   3
1  1   4
1  1   5
2  1   1
2  5   6
2  2   8
```

涉及多个分区的where子句若使用结果与行次序有关的函数如isDuplicated，first，firstNot等，必须使用map关键字，以在每个分区内单独执行where条件。

```
select * from pt where isDuplicated(qty) = false map
```
结果为
```
id qty
-- ---
1  1
1  2
2  1
2  5
2  2
```
### 1.12 DolphinDB SQL语句各子句执行顺序

1. from子句

from子句中的表对象或者 lj，ej，aj 等表连接，会最先被执行。

2. where条件

不符合where过滤条件的行会被舍弃。请注意，这一步仅可处理from子句中的数据，不可使用select子句中不属于from子句对象的新列名，例如计算结果。

3. group by / context by / pivot by子句

经过where条件过滤的行会依据 group by / context by / pivot by子句进行分组。

4. csort关键字（仅为 context by 子句提供）

context by通常与时间序列函数一起使用，每个分组中行的顺序对结果有直接影响。在context by子句后使用csort关键字，对每个组内的数据进行排序。

5. having 条件（若使用了group by或context by子句）

若使用了group by或context by 子句，则对每组使用having条件过滤，不满足条件的组被舍弃。与where条件相同，having条件中亦不可使用select子句中不属于from子句对象的新列名，例如计算结果。

6. select子句

若select子句指定了计算，此时才执行。

7. limit/top子句 （若使用了context by子句）

若使用了context by子句，limit/top子句应用于每组。若有 n 组且 limit m 或 top m，则最多返回 n*m 行。

此情况下limit/top子句的执行顺序是在order by子句之前；其它情况下的limit/top子句的执行顺序是在order by子句之后。

8. order by子句

由于order by子句的执行顺序在select子句之后，order by子句可使用select子句中不属于from子句对象的新列名，例如计算结果。

9. limit / top子句 （若未使用context by子句）

若未使用context by子句，则 limit / top 子句应用于前一步的全体结果，其指定范围之外的行被丢弃。


特殊情况：cgroup by子句

若SQL语句使用cgroup by子句，其执行顺序如下：首先使用过滤条件（若有），然后根据cgroup by的列与group by的列（若有），对select子句中的项目进行分组计算，然后根据order by的列（必须使用，且必须属于group by列或cgroup by列）对分组计算结果进行排序，最后计算累计值。若使用group by，则在每个group by组内计算累计值。


## 2. DolphinDB SQL表关联语法解析

本节介绍DolphinDB SQL特有的表连接方法 aj, wj 与 pwj。其他常规连接方法 ej, lj, fj 请参考用户手册第八章中表连接相应章节。

### 2.1 aj

DolphinDB提供性能极佳的非同时连接函数`aj`(asof join)，为左表中每条记录，在右表中获取符合指定条件的组中该时刻之前（包括该时刻）的最后一条记录。DolphinDB的asof join比pandas中的asof join速度快约200倍。

Asof join在国际证券市场的最典型应用场景为：报价与交易信息存储于不同的数据表中，由于时间戳精确到纳秒，交易成交与买卖报价更新的时间戳绝大部分情况下不重合，因此不能使用常用的等值连接（equal join）来连接报价表与交易表。这种情况下，可使用asof join连接报价表与交易表，以寻找每只股票每一笔交易之前的最新一笔报价。

```
trades=loadText(YOURDIR+"UStrades.csv")
quotes=loadText(YOURDIR+"USquotes.csv")

t = select Exchange, Symbol, Date, Time, Trade_Volume, Trade_Price, Bid_Price, Offer_Price from aj(trades, quotes, `symbol`date`time) where trades.Time between 09:30:00.000000000 : 15:59:59.999999999
select top 10 * from t where Symbol=`AAPL, Time>=15:00:00 
```

结果为：
```
Exchange	Symbol	Date	Time	Trade_Volume	Trade_Price	Bid_Price	Offer_Price
68	AAPL	2017.10.16	15:00:00.317755829	1,000	159.7058	159.7	159.71
68	AAPL	2017.10.16	15:00:00.322306115	100	159.705	159.7	159.71
68	AAPL	2017.10.16	15:00:00.322920479	200	159.705	159.7	159.71
68	AAPL	2017.10.16	15:00:00.323709344	100	159.705	159.7	159.71
81	AAPL	2017.10.16	15:00:00.391594735	100	159.71	159.7	159.71
81	AAPL	2017.10.16	15:00:00.391598131	200	159.71	159.7	159.71
88	AAPL	2017.10.16	15:00:00.391598821	100	159.71	159.7	159.71
90	AAPL	2017.10.16	15:00:00.391995167	100	159.71	159.7	159.72
80	AAPL	2017.10.16	15:00:00.392245342	100	159.71	159.71	159.72
80	AAPL	2017.10.16	15:00:00.392255170	100	159.71	159.71	159.72
```

可使用以下脚本计算基于交易价格与交易之前的最新平均报价之比例，以交易量为权重的交易成本。`aj`函数的前两个参数是进行连接的数据表，第三个参数是连接的字段。首先按股票分组，每个组之内再按照时间列Time进行asof join。右表数据（quotes表）必须保证每个组（Symbol和Date分组）内的记录是按照最后一个连接字段（Time）升序排列的。
```
select sum(Trade_Volume*abs(Trade_Price-(Bid_Price+Offer_Price)/2))/sum(Trade_Volume*Trade_Price)*10000 as cost_aj from aj(trades,quotes,`Symbol`Date`Time) where Time between 09:30:00.000000000 : 15:59:59.999999999 group by symbol
```
结果如下，请注意在以上脚本中，计算结果被乘以10000，所以以下展示的结果的单位为basis point（万分之一）。
```
symbol	cost_aj
AAPL	1.0223
FB	2.5911
MSFT	2.5787
```

### 2.2 wj与pwj

DolphinDB提供性能极佳的非同时连接函数`wj`(window join)与`pwj`(prevailing window join)，为左表中每条记录，在右表中获取符合指定条件的且属于基于该时刻的指定时间范围内的记录，并进行计算。

`wj`和`pwj`的唯一区别是，如果右表没有在指定时间范围左边界相匹配的值，`pwj`会选择左边界前的最后一个值，将其并入指定时间范围。

2.1节中的例子使用了交易之前的最新报价以计算交易成本。下例中，使用交易前一段时间的报价的均值计算交易成本。pwj函数比aj函数增加了两个参数：-10000000:0 指定相对交易时刻的时间窗口。因为时间单位是纳秒，-10000000:0 表示从交易的发生时刻到前10毫秒的窗口；<[avg(Offer_Price) as Offer_Price, avg(Bid_Price) as Bid_Price]>是每个窗口中需要计算的一系列聚合函数。

```
select sum(Trade_Volume*abs(Trade_Price-(Bid_Price+Offer_Price)/2))/sum(Trade_Volume*Trade_Price)*10000 as cost_pwj from pwj(trades,quotes,-10000000:0,<[avg(Offer_Price) as Offer_Price, avg(Bid_Price) as Bid_Price]>,`Symbol`Time) where Time between 09:30:00.000000000 : 15:59:59.999999999 group by symbol
```
之所以使用`pwj`而不是`wj`，是因为如果某个10毫秒窗口内没有报价数据，会获取窗口之前的最新报价数据进行计算。

结果为：
```
symbol	cost_pwj
AAPL	1.0155
FB	2.5853
MSFT	2.4758
```

## 3. DolphinDB SQL与标准SQL的区别

| 标准SQL语法                                                  | DolphinDB语法                                                | 解释                                                         |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| where sym='IBM'                                              | where sym=\`IBM ("IBM")  where sym="IBM"   where sym='IBM'            | DolphinDB中，或使用双引号或者单引号，或者一个单词与反引号配合使用，均表示字符串。|
| where sym='IBM' and qty>2000                                 | where sym==\`IBM, qty>2000 where sym==\`IBM and qty>2000 where sym=`IBM && qty>2000 | DolphinDB中，不同过滤条件之间使用逗号(,)表示执行顺序，在前一个条件通过后才会继续验证下一个条件。 |
| where sym="IBM" or qty>2000                                  | where sym==\`IBM or qty>2000 where sym==\`IBM \|\| qty>2000    |                                                              |
| where x not in (1,2) and y not in (22,23)                    | where (not x in [1,2]) and (not y in (22,23))                | DolphinDB不支持 NOT IN 运算符。                              |
| select avg(price), sym from Dataset group by sym             | select avg(price) from Dataset group by sym                  | DolphinDB中，group by 的列名会自动添加到结果中，所以用户不需要在select子句中指定group by列。 |
| N/A                                                          | context by                                                   | context by 是DolphinDB的独有的创新，它使得在分组处理时间序列时非常方便。context by 与group by相似，但是group by 的结果为每一组返回一个标量值，而context by的结果为 每一组返回一个与组内记录数同样长度的向量。 |
| N/A                                                          | pivot by                                                     | pivot by 将数据转换成二维视图。                              |
| N/A                                                          | cgroup by                                                    | 累计分组计算                                                             |
| N/A                                                          | map                                                          | 将SQL语句在每个分区分别执行，然后将结果合并。                |
| case .... when ....                                          | [iif](http://www.dolphindb.cn/cn/help/iif.html)              |                                                              |
| select column_name(s) from table1 left join table 2 on table1.column_name=table2.column_name | select column_name(s) from lj(table1, table2, column_name)   | DolphinDB的语法更简洁。                                      |
| LEFT JOIN                                                    | lj,  slj                                                     | 左连接和有序左连接。返回左表中所有与右表匹配的行。左连接返回的行数与左表的行数相同。如果右表中有多个匹配的行，将会选择第一个匹配行。如果右表中没有匹配行，将返回NULL。左连接和有序左连接的唯一区别是有序左连接的结果会根据连接字段排序。 |
| INNER JOIN                                                   | ej, sej                                                      | 等值连接和有序等值连接。返回与匹配列相等的行。sej 和 ej 的区别sej 对连接结果的表根据连接字段进行排序。 |
| N/A                                                          | aj                                                           | asof 连接。它把左表中的每一条记录作为标准，并且检查右表中是否有匹配行。如果没有完全匹配的行，将会选择最近的行。如果有多个匹配行，将会选择最后一行。 |
| N/A                                                          | wj, pwj                                                      | 窗口连接和现行窗口连接。它们是asof连接的扩展。对于左表中的每一行，在右表中截取一个窗口，应用聚合函数。如果右表窗口左边界没有对应记录，现行窗口连接会选择滑动窗口左边界之前的最新记录，并将其并入窗口。|

## 4. SQL语句用于分布式表

本章讲述SQL语句用于分布式表（DFS table）与用于普通内存表的不同之处。为简单起见，本章中的例子均使用单节点下的分布式表。

### 4.1 数据的更改、增加与删除

由于分布式表不支持单行数据的更改、增加与删除，因而不支持SQL update, insert与delete子句。

若对分布式表进行单行数据的更改、增加与删除，目前必须以分区为单位。例如，若要更改某行记录，须将含有此行数据的分区使用`dropPartition`命令整体删除，然后重新写入此分区。

### 4.2 分区表的连接

分布式表连接时，需要遵循以下规则：

1. 如果左表和右表都是分布式表：
- 两个表必须位于同一个数据库中。
- 连接列必须包含所有分区列。连接列亦可包含非分区列。
- 不支持cross join。

2. 如果只有右表是分布式表，则只能使用equal join。

3. 如果左表是分布式表，右表是维度表或内存表，则不支持full join。当分布式表与维度表或内存表连接时，系统会将维度表或内存表复制到分布式表所在的各个节点上执行连接操作。如果本地表数据量非常庞大，表的传送将非常耗时。为了提高性能，系统在数据复制之前用where条件尽可能多地过滤内存表。如果右表数据量太大，会影响查询速度，所以在实际应用中，右表的数据量最好比较小。

4. 分布式表可以与任意数据库中的维度表进行连接。

### 4.3 某些聚合函数

当需要跨越分区进行计算时，一部分聚合函数如`max`，`sum`，`std`可以分解成map和reduce操作，另一部分聚合函数如`med`和`percentile`无法分解成map和reduce操作。目前SQL语句用于分区表时，不支持无法分解的聚合函数。
```
symbol=`600100`600200`600100`600200`600100`600200
date=2020.11.23 2020.11.23 2020.11.24 2020.11.24 2020.11.25 2020.11.25
volume = 1000 2000 1200 3600 2100 2800
t=table(symbol, date, volume)
db = database("dfs://valueDB1", VALUE, `600100`600200)
Trades = db.createPartitionedTable(t, "Trades", "symbol");
Trades.append!(t)
pt=loadTable("dfs://valueDB1", `Trades)
```
`med`和`percentile`目前均不可用于分区表。运行以下脚本会报错。

```
select med(volume) from pt;
select percentile(volume,25) from pt;
```
但这两个函数可用于普通内存表：
```
select med(volume) from t;
```
2050
```
select percentile(volume,25) from t;
```
1400

## 5. DolphinDB SQL元编程

DolphinDB支持使用元编程来动态创建表达式，包括函数调用的表达式、SQL查询表达式等。

以下为与SQL有关的常用的元编程函数：

- `sqlCol`: 转换列名为元代码。
- `sqlColAlias`：为某个计算列赋给别名。
- `sql`: 动态生成SQL语句。
- `eval`: 执行元代码。

例1：
```
symbol = take(`GE,6) join take(`MSFT,6) join take(`F,6)
date=take(take(2017.01.03,2) join take(2017.01.04,4), 18)
price=31.82 31.69 31.92 31.8  31.75 31.76 63.12 62.58 63.12 62.77 61.86 62.3 12.46 12.59 13.24 13.41 13.36 13.17
volume=2300 3500 3700 2100 1200 4600 1800 3800 6400 4200 2300 6800 4200 5600 8900 2300 6300 9600
t1 = table(symbol, date, price, volume);

x=5000
whereConditions = [<symbol=`MSFT>,<volume>x>]
havingCondition = <sum(volume)>200>;
```
```
sql(sqlCol("*"), t1, whereConditions);
```
结果为：
< select * from t1 where symbol == "MSFT",volume > x >
```
sql(select=sqlColAlias(<avg(price)>), from=t1, where=whereConditions, groupBy=sqlCol(`date));
```
结果为：
< select avg(price) as avg_price from t1 where symbol == "MSFT",volume > x group by date >
```
sql(select=sqlCol("*"), from=t1, groupBy=sqlCol(`symbol), groupFlag=0, limit=1);
```
结果为：
< select top 1 * from t1 context by symbol >
```
sql(select=sqlCol("*"), from=t1, groupBy=sqlCol(`symbol), groupFlag=0, limit=1).eval();
```
结果为：
```
symbol date       price volume
------ ---------- ----- ------
GE     2017.01.03 31.82 2300
MSFT   2017.01.03 63.12 1800
F      2017.01.03 12.46 4200
```

例2：执行一组查询，合并查询结果。

有时需要执行一组相同结构的查询，并将查询结果合并展示。如果每次都手动编写全部SQL语句，工作量大，并且扩展性差。通过元编程动态生成SQL语句可以解决这个问题。

本例使用的数据集结构如下（以第一行为例）：

| mt       | vn       | bc   | cc   | stt  | vt   | gn   | bk   | sc   | vas  | pm   | dls        | dt         | ts     | val   | vol   |
| -------- | -------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---------- | ---------- | ------ | ----- | ----- |
| 52354955 | 50982208 | 25   | 814  | 11   | 2    | 1    | 4194 | 0    | 0    | 0    | 2020.02.05 | 2020.02.05 | 153234 | 5.374 | 18600 |

每天都需要执行一组查询。例如：
```
select * from t where vn=50982208,bc=25,cc=814,stt=11,vt=2, dsl=2020.02.05, mt<52355979 order by mt desc limit 1
select * from t where vn=50982208,bc=25,cc=814,stt=12,vt=2, dsl=2020.02.05, mt<52355979 order by mt desc limit 1
select * from t where vn=51180116,bc=25,cc=814,stt=12,vt=2, dsl=2020.02.05, mt<52354979 order by mt desc limit 1
select * from t where vn=41774759,bc=1180,cc=333,stt=3,vt=116, dsl=2020.02.05, mt<52355979 order by mt desc limit 1
```

这一组查询中，过滤条件包含的列和排序列都相同。为此，可编写自定义函数bundleQuery：

```
def bundleQuery(tbl, dt, dtColName, mt, mtColName, filterColValues, filterColNames){
	cnt = filterColValues[0].size()
	filterColCnt =filterColValues.size()
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

bundleQuery中各个参数的含义如下：

- tbl是数据表
- dt是过滤条件中日期的值
- dtColName是过滤条件中日期列的名称
- mt是过滤条件中mt的值
- mtColName是过滤条件中mt列的名称，以及排序列的名称
- filterColValues是其他过滤条件中的值，用元组表示，其中的每个向量表示一个过滤条件，每个向量中的元素表示该过滤条件的值
- filterColNames是其他过滤条件中的列名，用向量表示

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

可以以admin登录后，执行以下脚本把bundleQuery函数定义为函数视图。在集群的任何节点重启系统之后，都可直接使用该函数。
```
addFunctionView(bundleQuery)
```

## 6. 性能优化

### 6.1 数据库分区

对数据库进行分区可以显著降低系统响应延迟，提高数据吞吐量。具体来说，分区有以下主要好处。

- 分区使得大型表更易于管理。对数据子集的维护操作也更加高效，因为这些操作只针对需要的数据而不是整个表。一个好的分区策略通过只读取查询所需的相关数据来减少要扫描的数据量。如果分区机制设计不合理，对数据库的查询、计算以及其它操作都可能受到磁盘访问I/O这个瓶颈的限制。

- 分区使得系统可以充分利用所有资源。选择一个良好的分区方案搭配并行计算，分布式计算可以充分利用所有节点来完成通常要在一个节点上完成的任务。若一个任务可以拆分成几个子任务，每个子任务访问不同的分区，可以显著提升效率。

- 分区增加了系统的可用性。由于分区的副本通常是存放在不同的物理节点的，所以一旦某个分区不可用，系统依然可以调用其它副本分区来保证作业的正常运转。

分布式查询（即查询分布式数据表）和普通查询的语法并无差异。理解分布式查询的工作原理有助于写出高效的查询。系统首先根据where子句确定需要的分区，然后把查询发送到相关分区所在的位置，最后整合所有分区的结果。

### 6.2 分区剪枝

绝大多数分布式查询只涉及分布式表的部分分区。若where子句中某个过滤条件仅包含分布式表的原始分区字段、关系运算符(<, <=, =, ==, >, >=, in, between)和逻辑运算符(or, and)，以及常量（包括常量与常量的运算），且非链式条件（例如100<x<200），且过滤逻辑可以缩窄相关分区范围，则系统只加载与查询相关的分区，以节省查询耗时。若where子句中的过滤条件无一满足以上要求，或过滤逻辑无法缩窄分区范围，则会遍历所有分区进行查询。数据量较大时，过滤条件的不同写法会造成查询耗时的巨大差异。

若分布式数据库 dfs://demo 中分布式表 pt 的分区列为 date，以下查询会显著缩小查询的分区范围：
```
pt = loadTable("dfs://demo", `pt)

x = select date, symbol, price from pt where date>2019.12.01-30;

x = select date, symbol, price from pt where date between 2019.12.01 : 2019.12.31;

x = select date, symbol, price from pt where date between 2019.12.01 : 2019.12.31 and price>5;

x = select date, symbol, price from pt where date>2019.12.01, date<2019.12.31, price>5;
```

但以下查询不能缩小查询的分区范围：

- 不可对分区字段进行运算
```
select date, symbol, price from pt where date+30>2019.12.01; 
```

- 不可使用链式比较：
```
select date, symbol, price from pt where 2019.12.01<date<2019.12.31;
```

- 不可对分区字段使用函数：
```
select date, symbol, price from pt where month(date)<=2019.12M;
```

- 至少有一个过滤条件需要使用分区字段：
```
select date, symbol, price from pt where price<5;
```

- 与分区字段比较时仅可使用常量，不可使用其他列：
```
select date, symbol, price from pt where date<announcementDate-3;
```

- 以下脚本由于必须执行 price<5，过滤逻辑无法缩窄相关分区范围：
```
select date, symbol, price from pt where price<5 or date between 2019.08.01:2019.08.31;
```


### 6.3 能够使用字典（dictionary）的情况下避免使用 join

若某些对分布式表进行的join操作可以使用字典完成，则尽量使用字典以避免join，可大大减少耗时。

例如，数据表t1含有股票的某些信息，数据表t2含有股票的行业信息。若要根据股票的行业信息进行过滤，可采用以下两种方式：

- 将t1与t2进行join，然后过滤：
```
t1=table(take(600001..600010,20) as symbol, take(2020.11.23 2020.11.24,20).sort!() as date, 1..20 as x);
t2=table(600001..600010 as symbol, `A`A`B`B`B`A`C`C`C`D as industry);
select * from lj(t1, t2, `symbol) where industry=`D
```
- 将t2转换为一个字典，然后在过滤条件中使用该字典，避免join：
```
d = dict(t2.symbol, t2.industry)
select * from t1 where d[symbol]=`D
```
若t1是数据量非常大的分布式表时，第一种方法会将t1所有数据载入内存进行join，会导致内存不足而无法得到结果；而第二种方法则会避免内存不足，较快得到结果。














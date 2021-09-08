# 数据透视(Pivoting)在高频数据处理与计算中的应用示例

## 1. 计算股票收益的两两相关性

在配对交易(pair trading)及风险对冲(hedging)时，经常需要计算给定一篮子股票之间的两两相关性。此种计算，一般数据库无法直接执行，而使用一般的统计软件不仅需要数据迁移，更需要繁琐的编程。本例展示如何在 DolphinDB database 中方便快捷的直接进行计算。

首先，载入美股股票高频交易数据库的元数据：

```txt
quotes = loadTable("dfs://TAQ", "quotes")
```

接下来，选择2009年8月4日中500只报价变动最频繁的股票：

```txt
dateValue=2009.08.04
num=500
syms = (exec count(*) from quotes where date = dateValue, time between 09:30:00 : 15:59:59, 0<bid, bid<ofr, ofr<bid*1.1 group by Symbol order by count desc).Symbol[0:num]
```

下面我们利用"pivot by"将高频数据降维成为分钟级数据，并且改变原始数据的结构，生成一个分钟级股票价格矩阵：每一列是一只股票；每一行是一分钟。

```txt
priceMatrix = exec avg(bid + ofr)/2.0 as price from quotes where date = dateValue, Symbol in syms, 0<bid, bid<ofr, ofr<bid*1.1, time between 09:30:00 : 15:59:59 pivot by time.minute() as minute, Symbol
```

DolphinDB的语言非常灵活。在这里，"pivot by"不仅将数据转换为透视表，同时也可以搭配函数使用，具有"group by"的功能。

利用高阶函数`each`将价格矩阵转换为收益率矩阵：

```txt
retMatrix = each(def(x):ratios(x)-1, priceMatrix)
```

利用高阶函数`cross`计算这500只股票之间收益的两两相关性：

```txt
corrMatrix = cross(corr, retMatrix, retMatrix)
```

选取与每只股票相关性最高的10只股票：

```txt
mostCorrelated = select * from table(corrMatrix).rename!(`sym`corrSym`corr) context by sym having rank(corr,false) between 1:10
```

选取与SPY相关性最高的10只股票：

```txt
select * from mostCorrelated where sym='SPY' order by corr desc
```

## 2. 使用高频数据计算股票组合的价值

在进行指数套利交易回测时，需要计算给定股票组合的价值。当数据量极大时，回测时采用一般数据分析系统，对系统内存及速度的要求极高。本例可见，使用DolphinDB的编程语言可极为简洁的进行此类计算。

在本例中，为了简化起见，假定某个指数只由两只股票组成：AAPL与FB。以下代码产生本例所用数据。时间戳精度为纳秒，指数成分权重存在weights这个dictionary里。

```txt
Symbol=take(`AAPL, 6) join take(`FB, 5)
Time=2019.02.27T09:45:01.000000000+[146, 278, 412, 445, 496, 789, 212, 556, 598, 712, 989]
Price=173.27 173.26 173.24 173.25 173.26 173.27 161.51 161.50 161.49 161.50 161.51
quotes=table(Symbol, Time, Price)
weights=dict(`AAPL`FB, 0.6 0.4)
ETF = select Symbol, Time, Price*weights[Symbol] as weightedPrice from quotes
select last(weightedPrice) from ETF pivot by Time, Symbol;
```

最后一行代码的结果为：

```txt
Time                          AAPL    FB
----------------------------- ------- ------
2019.02.27T09:45:01.000000146 103.962
2019.02.27T09:45:01.000000212         64.604
2019.02.27T09:45:01.000000278 103.956
2019.02.27T09:45:01.000000412 103.944
2019.02.27T09:45:01.000000445 103.95
2019.02.27T09:45:01.000000496 103.956
2019.02.27T09:45:01.000000556         64.6
2019.02.27T09:45:01.000000598         64.596
2019.02.27T09:45:01.000000712         64.6
2019.02.27T09:45:01.000000789 103.962
2019.02.27T09:45:01.000000989         64.604
```

由于时间戳精度为纳秒，基本上所有交易的时间戳均不一致。如果回测时的数据行数极多（几亿或几十亿行）且指数成分股数量也较多（如S&P500指数的500只成分股），使用传统分析系统，要计算任一时刻的指数价值，需要将原始数据表的3列（时间，股票代码，价格）转换为同等长度但是宽度为指数成分股数量+1的数据表，向前补充空值(forward fill NULLs)，进而计算每行的指数成分股对指数价格的贡献之和。这种做法，会产生比原始数据表大很多倍的中间过程数据表，很有可能会导致系统内存不足。同时，计算速度也很慢。

使用DolphinDB中的SQL "pivot by"语句，只需以下一行代码，即可实现上述所有步骤。不仅编程简洁，而且无需产生中间过程数据表，有效避免了内存不足的问题，同时极大提升计算速度。

```txt
select rowSum(ffill(last(weightedPrice))) from ETF pivot by Time, Symbol;
```

结果为：

```txt
Time                          rowSum
----------------------------- -------
2019.02.27T09:45:01.000000146 103.962
2019.02.27T09:45:01.000000212 168.566
2019.02.27T09:45:01.000000278 168.56
2019.02.27T09:45:01.000000412 168.548
2019.02.27T09:45:01.000000445 168.554
2019.02.27T09:45:01.000000496 168.56
2019.02.27T09:45:01.000000556 168.556
2019.02.27T09:45:01.000000598 168.552
2019.02.27T09:45:01.000000712 168.556
2019.02.27T09:45:01.000000789 168.562
2019.02.27T09:45:01.000000989 168.566
```
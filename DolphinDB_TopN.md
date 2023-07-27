# DolphinDB TopN 系列函数教程

DolphinDB 已经有非常多的窗口计算函数，例如 m 系列的滑动窗口计算，cum 系列累计窗口计算，tm 系列的的时间窗口滑动计算。但是所有这类函数都是对窗口内的所有记录进行指标计算，难免包含很多噪音。DolphinDB 的金融领域用户反馈，通过交易量信息等对窗口内的记录进行过滤，得到的计算指标具有更高的质量，以此为基础的交易策略能带来更多的 Alpha。同时用户也反馈，通过自定义函数来计算按额外信息过滤后的指标，消耗的时间过长。为此，DolphinDB 推出了 TopN 系列内置函数，涵盖 mTopN 系列、tmTopN 系列、cumTopN 系列，通过增量计算，大幅提升性能。DolphinDB 2.00.10 及 1.30.22 版本均支持本教程中涉及的功能。

本教程将从以下几个角度介绍 TopN 系列函数：
- [1. TopN 系列函数能解决的问题、计算规则及实现](#1-topn-系列函数能解决的问题计算规则及实现)
	- [1.1 TopN 系列函数解决的痛点问题](#11-topn-系列函数解决的痛点问题)
	- [1.2 TopN 系列函数的计算规则及实现](#12-topn-系列函数的计算规则及实现)
- [2. mTopN 、tmTopN 系列的应用场景](#2-mtopn-tmtopn-系列的应用场景)
	- [2.1 mTopN 应用场景](#21-mtopn-应用场景)
	- [2.2 tmTopN 应用场景](#22-tmtopn-应用场景)
- [3. cumTopN 系列的应用场景](#3-cumtopn-系列的应用场景)
- [4. 自定义 TopN 函数](#4-自定义-topn-函数)
	- [4.1 自定义 TopN 的实现方法](#41-自定义-topn-的实现方法)
	- [4.2 内置 TopN 与自定义 TopN 的性能对比](#42-内置-topn-与自定义-topn-的性能对比)
- [5. TopN 的批流一体场景](#5-topn-的批流一体场景)
- [6. DECIMAL 的使用](#6-decimal-的使用)
- [7. 总结](#7-总结)




## 1. TopN 系列函数能解决的问题、计算规则及实现

### 1.1 TopN 系列函数解决的痛点问题

在分组计算中，常常不需要对分组中的所有数据做计算，有时只需要对组中 topn 个元素做计算即可。举个例子，如想要统计每天每只股票 `Volume` 值小于第一四分位数的平均 `Volume` 值，是不可以用 `percentile` 函数直接求值的，因为 sql 语句是先整体进行条件过滤再分组计算，因此无法将每个分组的 top 元素取出。

假设存在表 *tb* 是两支股票的数据表，要按照股票和日期分组后用 `percentile` 筛选，统计每天每只股票因子位于前40%的 `value` 的平均值。

```
trade_date=sort(take(2017.01.11..2017.01.12,20))
secu_code=take(`600570`600000,20)
value=1..20
tb=table(trade_date,secu_code,value)   
```



常规的做法编写自定义聚合函数来实现：

```
defg percentile_40(x){
	ret = NULL
	y = percentile(x,40)
	cc = sum(x<y) 
	if (cc > 0){
		ret = sum(iif( x<y,x,0))\cc
	}
	return ret
}
select percentile_40(value) as factor_value from tb group by trade_date,secu_code

#output
trade_date secu_code factor_value
---------- --------- ------------
2017.01.11 600000    3           
2017.01.11 600570    2           
2017.01.12 600000    13          
2017.01.12 600570    12          
```

 

针对类似的情况，DolphinDB 推出了 topN 系列函数来解决这样的问题。topN 函数能够使得数据按照某个指标进行排序，并取排序后前 top 个元素或者前多少百分比的元素进行计算，能够显著提升脚本的可读性。

```
select aggrTopN(avg, funcArgs=value, sortingCol=value, top=0.4, ascending=true) as factor_value from tb group by trade_date,secu_code

#output
trade_date secu_code factor_value
---------- --------- ------------
2017.01.11 600000    3           
2017.01.11 600570    2           
2017.01.12 600000    13          
2017.01.12 600570    12
```

 

除了聚合函数 `aggrTopN` 之外，DolphinDB 还推出了 mTopN，cumTopN，tmTopN。对于 topN 的排序列，我们通常会将涨跌幅、交易量等指标作为排序键。在接下来的第2、3章中，将会具体举例 mTopN，cumTopN，tmTopN 的应用场景。



### 1.2 TopN 系列函数的计算规则及实现

TopN 系列函数基本上可以归纳为以下几种类型：mfuncTopN、tmfuncTopN 以及 cumfuncTopN。此外，还有与之对应的高阶函数 `aggrTopN`。

以 `mfuncTopN(X, S, window, top, [ascending=true], [tiesMethod])` 为例，其计算过程为：

1. 将 *X*  根据 *S* 进行稳定排序（排序方式由 *ascending* 指定，默认 true 为升序）
2. 取排序结果的前 top 个元素进行计算。如果有多个具有相同值的元素无法全部进入前 top，可通过 *tiesMethod* 参数设置对这些值的选取规则。简单的说，*tiesMethod* 为 latest 时，优先选取最新的数据，为 oldest 时，优先选取最老的数据，为 all 时，选取全部数据。具体的用法规则可参考 TopN 的用户手册 ([TopN 系列 — DolphinDB 2.0 documentation](https://www.dolphindb.cn/cn/help/FunctionsandCommands/SeriesOfFunctions/TopN.html) )。

目前支持 TopN 的计算函数共有36个：

| **基础函数** | **mTopN 系列** | **tmTopN系列** | **cumTopN系列** |
| :----------- | :------------- | :------------- | :-------------- |
| sum          | msumTopN       | tmsumTopN      | cumsumTopN      |
| avg          | mavgTopN       | tmavgTopN      | cumavgTopN      |
| std          | mstdTopN       | tmstdTopN      | cumstdTopN      |
| stdp         | mstdpTopN      | tmstdpTopN     | cumstdpTopN     |
| var          | mvarTopN       | tmvarTopN      | cumvarTopN      |
| varp         | mvarpTopN      | tmvarpTopN     | cumvarpTopN     |
| skew         | mskewTopN      | tmskewTopN     | cumskewTopN     |
| kurtosis     | mkurtosisTopN  | tmkurtosisTopN | cumkurtosisTopN |
| beta         | mbetaTopN      | tmbetaTopN     | cumbetaTopN     |
| corr         | mcorrTopN      | tmcorrTopN     | cumcorrTopN     |
| covar        | mcovarTopN     | tmcovarTopN    | cumcovarTopN    |
| wsum         | mwsumTopN      | tmwsumTopN     | cumwsumTopN     |

滑动窗口的 TopN 计算的场景很多，比如计算每只股票窗口内交易量最大的3条记录的平均价格，亦或是计算每种仪器的窗口内温度最高的5条记录的平均能耗等。具体的应用场景会在本教程的第二章 [mTopN 、tmTopN 系列的应用场景](#2-mtopn-tmtopn-系列的应用场景)中介绍。

累计窗口的 TopN 计算更多的涉及比如计算每只股票历史涨幅最大的几天的成交量之和等。具体的应用场景会在本教程的第三章 [cumTopN 系列的应用场景](#3-cumtopn-系列的应用场景)。

除此之外，如果用户想要自定义取出 TopN 之后的计算规则，DolphinDB 也开放了 `aggrTopN` 函数，用户可以在此函数搭配其他高阶函数如 `moving`， `tmoving` 等，实现自己的 `mfuncTopN` 函数。这一部分的场景和应用会在第四章[自定义 TopN 的实现方法](#4-自定义-topn-函数)中展开。

最后，TopN 系列函数都支持了批流一体，在第五章 [TopN 的批流一体场景](#5-topn-的批流一体场景)，会介绍如何将批计算中的 TopN 系列因子运用到实时计算流引擎中。



## 2. mTopN 、tmTopN 系列的应用场景 

滑动窗口的 TopN 计算，是基于窗口内的记录，通过先排序，取 TopN，再做聚合计算。本章节通过一些实际场景中会用到的例子加以说明。

本章节会用到的数据由以下脚本模拟：

```
n = 5*121
timeVector = 2023.04.30T09:30:00.000 + 0..120 * 60000
tradingTime = take(timeVector,n)
windCode = stretch(format(600001..600005, "000000") + ".SH", n)
open = (20.00+0.01*0..120) join (30.00-0.01*0..120) join (40.00+0.01*0..120) join (50.00-0.01*0..120) join (60.00+0.01*0..120)
high = (20.50+0.01*0..120) join (31.00-0.01*0..120) join (40.80+0.01*0..120) join (50.90-0.01*0..120) join (60.70+0.01*0..120)
low = (19.50+0.01*0..120) join (29.00-0.01*0..120) join (39.00+0.01*0..120) join (48.00-0.01*0..120) join (59.00+0.01*0..120)
close = (20.00+0.01*0..120) join (30.00-0.01*0..120) join (40.00+0.01*0..120) join (50.00-0.01*0..120) join (60.00+0.01*0..120)
volume= 10000+ take(-100..100,n)
t = table(tradingTime, windCode, open, high, low, close, volume)
```



### 2.1 mTopN 应用场景 

mTopN 可以按记录数滑动，窗口长度计算既可以按记录数，也可以按时间长度。具体滑动的规则可以参考窗口计算综述教程：[window_cal.md · 浙江智臾科技有限公司/Tutorials_CN - Gitee](https://gitee.com/dolphindb/Tutorials_CN/blob/master/window_cal.md) 

对于模拟数据中的分钟表 *t*，要得到每支股票每5条记录内交易量最大的3条记录的平均价格，可以用 `mavgTopN` 函数搭配 `context by` 解决：

```
select windCode, tradingTime, mavgTopN(close, volume, 5, 3, false) as mavgTop3Close from t context by windCode
//output
windCode  tradingTime             mavgTop3Close
--------- ----------------------- ------------------
600001.SH 2023.04.30T09:30:00.000 20                
600001.SH 2023.04.30T09:31:00.000 20.005
600001.SH 2023.04.30T09:32:00.000 20.01
600001.SH 2023.04.30T09:33:00.000 20.02
600001.SH 2023.04.30T09:34:00.000 20.03
...
```

 

一般来说，写因子的时候，计算的值不带单位，比如计算窗口大小为100分钟的交易量最大的十条记录的平均涨幅：

```
select windCode, tradingTime, mavgTopN(ratios(close), volume, 100, 10, false) as mavgTop10RatioClose from t context by windCode, date(tradingTime)
//output
windCode  tradingTime             mavgTop10RatioClose
--------- ----------------------- -----------------
600001.SH 2023.04.30T09:30:00.000                  
600001.SH 2023.04.30T09:31:00.000 1.0005           
600001.SH 2023.04.30T09:32:00.000 1.000499875
600001.SH 2023.04.30T09:33:00.000 1.000499750
600001.SH 2023.04.30T09:34:00.000 1.000499625
...
```

 

除了单目的 TopN 之外，DolphinDB 也支持了双目运算，如 `beta`、`corr`、`covar` 等的 TopN 算子。例如，计算每支股票每5条记录价格最高的3条记录的两个因子的相关性，可以用 `mcorrTopN` 函数搭配 `context by` 解决：

```
select windCode, tradingTime, mcorrTopN(low, close * volume,  log(ratios(close)), 5, 3, false) as mcorrTop3CloseVol from t context by windCode, date(tradingTime)
//output （由于是模拟数据，比较失真）
windCode  tradingTime             mcorrTop3CloseVol
--------- ----------------------- -----------------
600001.SH 2023.04.30T09:30:00.000                  
600001.SH 2023.04.30T09:31:00.000                  
600001.SH 2023.04.30T09:32:00.000 1.00000
600001.SH 2023.04.30T09:33:00.000 0.99999
600001.SH 2023.04.30T09:34:00.000 0.99999
```



### 2.2 tmTopN 应用场景

mTopN 的窗口计算是根据记录数取窗口大小。而 tmTopN 函数的窗口大小可以是一个时间间隔，既可以是5分钟，也可以为20秒，以此类推。tmTopN 系列函数中，top 可以是一个0和1之间的浮点数，表示百分比，譬如0.2，表示选择窗口内20%的记录。

例如对上述数据的处理中，计算时间窗口为3分钟，交易量最大的两条记录的平均涨幅：

```
select windCode, tradingTime, tmavgTopN(tradingTime, ratios(close), volume, 3m, 2, false) as tmavgTop2RatioClose from t context by windCode, date(tradingTime)
//output
windCode  tradingTime             tmavgTop2RatioClose
--------- ----------------------- -----------------
600001.SH 2023.04.30T09:30:00.000                  
600001.SH 2023.04.30T09:31:00.000 1.0005           
600001.SH 2023.04.30T09:32:00.000 1.000499875
600001.SH 2023.04.30T09:33:00.000 1.000499625
600001.SH 2023.04.30T09:34:00.000 1.0004993758
...
```

TopN 系列函数也实现了相关性函数的计算，因此可以计算例如5分钟窗口期内交易量最大的三条记录的 close 和 volume 相关性：

```
select windCode, tradingTime, tmcorrTopN(tradingTime, close, volume, volume, 5m, 3, false) as tmavgTop3CorrCloseVolume from t context by windCode, date(tradingTime)

//output
windCode  tradingTime             tmavgTop3CorrCloseVolume
--------- ----------------------- ------------------------
600001.SH 2023.04.30T09:30:00.000                         
600001.SH 2023.04.30T09:31:00.000 0.999999990552169       
600001.SH 2023.04.30T09:32:00.000 1.000000001625267       
600001.SH 2023.04.30T09:33:00.000 1.000000006877599       
600001.SH 2023.04.30T09:34:00.000 1.000000012129931       
...
```



## 3. cumTopN 系列的应用场景

与 mTopN 和 tmTopN 的滑动计算不同，cumTopN 系列计算的是累计窗口。例如，计算历史以来涨幅最大3条记录的交易量总和，可以通过 `cumsumTopN` 函数实现：

```
select windCode, tradingTime, cumsumTopN(volume, ratios(close), 3, false) as cumsumTop3Volume from t context by windCode

//output
windCode  tradingTime             cumsumTop3Volume
--------- ----------------------- ----------------
600001.SH 2023.04.30T09:30:00.000                 
600001.SH 2023.04.30T09:31:00.000 9901            
600001.SH 2023.04.30T09:32:00.000 19803           
600001.SH 2023.04.30T09:33:00.000 29706           
600001.SH 2023.04.30T09:34:00.000 29706
...
```

从上述脚本可以看到，函数内部的参数也可以是计算结果，并不一定是字段名，展现了TopN 函数用法的高度灵活性。



## 4. 自定义 TopN 函数

第一章列举了目前 DolphinDB 支持的内置的 TopN 系列函数。考虑到用户的多样化计算需求，DolphinDB 也开放了自定义的接口。用户可以根据实际需求，自定义 TopN 函数的聚合计算方式。

**注意**：经过优化的内置 TopN 系列函数性能优于自定义 TopN 函数。



### 4.1 自定义 TopN 的实现方法

TopN 系列对应的高阶函数是 `aggrTopN(func, funcArgs, sortingCol, top, [ascending=true])`，*func* 参数可以接受聚合函数。因此，如果用户希望用复杂的自定义聚合函数计算 TopN，例如计算交易量最大的前40%的记录中 OHLC 的平均值，可以这样实现：

```
//用 defg 自定义聚合函数 avgOHLC，定义取出 TopN 之后的聚合行为
defg avgOHLC(price){ 
	return avg(price)
}

select aggrTopN(avgOHLC, funcArgs =(open + high + low + close) , sortingCol=volume, top=0.4, ascending=true) as factor_value from t group by windCode

//output
windCode  factor_value       
--------- -------------------
600001.SH 80.94 
600002.SH 116.56583
600003.SH 160.74
600004.SH 196.40
600005.SH 240.76167
```

 

同样，mTopN 、tmTopN 系列的窗口函数也支持自定义。例如上述的 `avgOHLC` 函数，用户可以将其应用到 `moving`、`tmoving` 函数中：

```
select windCode, tradingTime, moving(aggrTopN{avgOHLC,,,0.4,true},(open + high + low + close, volume),10,1) as udfmTopN from t context by windCode

//output
windCode  tradingTime             udfmTopN          
--------- ----------------------- ------------------
600001.SH 2023.04.30T09:30:00.000 80 
...
600001.SH 2023.04.30T09:39:00.000 80.06
600001.SH 2023.04.30T09:40:00.000 80.10
600001.SH 2023.04.30T09:41:00.000 80.14
...
```



### 4.2 内置 TopN 与自定义 TopN 的性能对比

m 系列函数为各自的计算场景进行了优化，因此比 `moving` 高阶函数有更好的性能。上述的计算也可以用内置函数的 `mavgTopN` 完成：

```
select windCode, tradingTime, mavgTopN(open + high + low + close, volume,10,4) as udfmTopN from t context by windCode

//output
windCode  tradingTime             udfmTopN          
--------- ----------------------- ------------------
600001.SH 2023.04.30T09:30:00.000 80 
...
600001.SH 2023.04.30T09:39:00.000 80.06
600001.SH 2023.04.30T09:40:00.000 80.10
600001.SH 2023.04.30T09:41:00.000 80.14
...
```

 

性能上来说，内置 TopN 系列函数的计算效率远高于自定义 TopN 函数：

- 测试设备
  - CPU：Intel(R) Xeon(R) Silver 4216 CPU @ 2.10GHz
  - 操作系统： 64 位 CentOS Linux 7 (Core)
  - DolphinDB部署类型：2.00.10版本，单节点

```
//moving+aggrTopN+avgOHLC
timer(10000)select windCode, tradingTime, moving(aggrTopN{avgOHLC,,,0.4,true},(open + high + low + close, volume),10,1) as udfmTopN from t context by windCode
//8394 ms

//moving+aggrTopN+avg
timer(10000)select windCode, tradingTime, moving(aggrTopN{avg,,,0.4,true},(open + high + low + close, volume),10,1) as udfmTopN from t context by windCode
//6812 ms

//mavgTopN
timer(10000)select windCode, tradingTime, mavgTopN(open + high + low + close, volume,10,4) as udfmTopN from t context by windCode
//1394 ms
```

| **TopN函数**            | **运行10,000次耗时** |
| :---------------------- | :------------------- |
| moving+aggrTopN+avgOHLC | 8,394 ms             |
| moving+aggrTopN+avg     | 6,812 ms             |
| **mavgTopN**            | **1,394 ms**         |



## 5. TopN 的批流一体场景

在之前的章节中，介绍的均为离线计算的场景。TopN 系列函数目前也支持了流计算场景。例如计算窗口大小为100分钟的交易量最大的十条记录的平均涨幅：

```
//离线计算中的函数可以直接填入流引擎中
factor = <mavgTopN(ratios(close), volume, 100, 10, false)>

//定义输入输出表结构
share streamTable(1:0, `tradingTime`windCode`open`high`low`close`volume, [TIMESTAMP,STRING,DOUBLE,DOUBLE,DOUBLE,DOUBLE,INT]) as tickStream
result = table(1000:0, `windCode`tradingTime`mavgTop10RatioClose, [STRING,TIMESTAMP,DOUBLE])

//定义流计算引擎
rse = createReactiveStateEngine(name="streamTopN", metrics =[<tradingTime>, factor], dummyTable=t, outputTable=result, keyColumn="windCode")

//订阅流表、回放数据
subscribeTable(tableName=`tickStream, actionName="mTopN", handler=tableInsert{rse})
replay(inputTables=t.copy().sortBy!(`tradingTime), outputTables=tickStream, timeColumn=`tradingTime)

//查询流计算结果：
select * from result

//如若想要反复调用上述脚本，先运行以下三行脚本，清除流表订阅
unsubscribeTable(tableName=`tickStream, actionName="mTopN")
dropStreamEngine(`streamTopN)
undef(`tickStream, SHARED)
```



## 6. DECIMAL 的使用

2.00.10及后续的版本支持在 TopN 系列函数中使用 DECIMAL 类型（包括 DECIMAL32、64以及128类型）。不仅排序字段 S，而且计算字段 X 和 Y 均可使用 DECIMAL 类型。如果计算字段是 DECIMAL 类型，msumTopN、tmsumTopN 和 cumsumTopN 三个函数返回 DECIMAL 类型，其它函数的结果仍然返回 DOUBLE 类型。

虽然 `var`、`varp`、`std`、`stp`、`corr`、`covar`、`beta`、`wsum` 等8个基础函数对应的 TopN 系列函数最终结果位 DOUBLE 类型，但是当计算列 X 和 Y 为 DECIMAL 类型时，计算的中间结果用 DECIMAL128 表示，这样可以避免精度丢失。当然使用 DECIMAL 做计算的中间结果，也有不足的一面。首先计算耗时会更长，其次可能会出现 overflow。当前的版本，在计算出现 overflow 时，并不会抛出异常，这需要引起特别的注意。

DECIMAL128 的有效位数是38位（包括小数点前和后的位数）。例如要对价格数据算方差，18.2345这个数据总共6位有效数据，平方之后就是12位，如果有1亿个数（8位），总的有效位数是20位，远远低于38，不会出现 overflow。但如果小数位数特别多，例如小数点后从4位增加到了15位，这样价格数据的有效位数是17，平方之后就是34位，1万个数就可能超过 DECIMAL128 的有效数字38位。碰到小数位数特别多的数据，要么转成 DOUBLE 类型处理，要么用 decimal32、decimal64，decimal128 等函数先降低数据精度。

## 7. 总结

本教程介绍了 TopN 的计算规则，以及内置的36个 mTopN 、tmTopN、cumTopN 系列函数在离线计算和流计算等场景的应用，并针对性地介绍了自定义 TopN 的实现方法。

在未来版本中，DolphinDB 将支持更多的内置 TopN 计算函数。
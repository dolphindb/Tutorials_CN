# DolphinDB教程：面板数据的处理

时间序列数据、截面数据和面板数据是金融领域中常见的数据组织方式。面板数据包含了时间序列和横截面两个维度。在Python中，通常可以用pandas的DataFrame或numpy的二维数组来表示。在DolphinDB中面板数据也可以用表（table）或矩阵（matrix）来表示。

本教程主要介绍如何在DolphinDB中表示和分析面板数据。本文的所有例子都基于DolphinDB 1.30。

<!-- TOC -->
- [DolphinDB教程：面板数据的处理](#dolphindb教程面板数据的处理)
  - [1. 面板数据的表示方法和处理函数](#1-面板数据的表示方法和处理函数)
  - [2. SQL语句处理面板数据](#2-sql语句处理面板数据)
    - [2.1 context by](#21-context-by)
    - [2.2 pivot by](#22-pivot-by)
  - [3. 向量化函数处理面板数据](#3-向量化函数处理面板数据)
    - [3.1 矩阵操作示例](#31-矩阵操作示例)
    - [3.2 对齐矩阵的二次运算](#32-对齐矩阵的二次运算)
      - [3.2.1 indexedMatrix](#321-indexedmatrix)
      - [3.2.2 indexedSeries](#322-indexedseries)
    - [3.3 重采样和频度转换](#33-重采样和频度转换)
      - [3.3.1 resample（重采样）](#331-resample重采样)
      - [3.3.2 asfreq（频率转换）](#332-asfreq频率转换)
      - [3.3.3 NULL值的处理](#333-null值的处理)
  - [4. 面板数据处理方式的对比](#4-面板数据处理方式的对比)
    - [4.1 DolphinDB SQL 与 向量化函数处理面板数据的对比](#41-dolphindb-sql-与-向量化函数处理面板数据的对比)
    - [4.2 DolphinDB与pandas处理面板数据的性能对比：](#42-dolphindb与pandas处理面板数据的性能对比)

<!-- /TOC -->

## 1. 面板数据的表示方法和处理函数

DolphinDB提供了两种方法处理面板数据：

- 通过SQL和向量化函数来处理用二维表表示的面板数据
- 通过向量化函数来处理用矩阵表示的面板数据

DolphinDB中数据表和矩阵都采用了列式存储。以下是表和矩阵中的列常用的计算函数和二元运算符:

- 二元运算符：+, -, *, /, ratio, %, &&, ||, &, |, pow 
- 序列函数：ratios, deltas, prev, next, move
- 滑动窗口函数：mcount，mavg, msum, mmax, mimax, mimin, mmin, mprod, mstd, mvar, mmed，mpercentile, mrank, mwavg, mwsum, mbeta, mcorr, mcovar
- 累计窗口函数：cumcount, cumavg, cumsum, cummax, cummin, cumprod, cumstd, cumvar, cummed, cumpercentile, cumPositiveStreak, cumrank, cumwavg, cumwsum, cumbeta, cumcorr, cumcovar
- 聚合函数：count, avg, sum, sum2, first, firstNot, last, lastNot, max, min, std, var, med, mode, percentile, atImax, atImin, wavg, wsum, beta, corr, covar
- 聚合函数(针对面板数据的每一行进行计算): rowCount, rowAvg, rowSum, rowSum2, rowProd, rowMax, rowMin, rowStd, rowVar, rowAnd, rowOr, rowXor


我们会具体在下文中通过举例的方式让读者更能了解这些函数是如何进行面板数据操作。

## 2. SQL语句处理面板数据

当使用DolphinDB的二维数据表来表示SQL的面板数据时，通常一个列存储一个指标，譬如open，high，low，close，volume等，一行代表一个股票在一个时间点的数据。这样的好处是，多个指标进行处理时，不再需要对齐数据。缺点是分组计算（按股票分组的时间序列计算，或者按时间分组的横截面计算），需要先分组，SQL语句的group by/context by/pivot by子句均可用于分组。分组有一定的开销，通常尽可能把所有的计算在一次分组内全部计算完成。

DolphinDB的SQL不仅支持SQL的标准功能，还进行了扩展，包括面板数据处理，非同时连接，窗口连接，窗口函数等

```
sym = `C`C`C`C`MS`MS`MS`IBM`IBM
timestamp = [09:34:57,09:34:59,09:35:01,09:35:02,09:34:57,09:34:59,09:35:01,09:35:01,09:35:02]
price= 50.6 50.62 50.63 50.64 29.46 29.48 29.5 174.97 175.02			
volume = 2200 1900 2100 3200 6800 5400 1300 2500 8800		
t = table(sym, timestamp, price, volume);
t;

sym timestamp price  volume
--- --------- ------ ------
C   09:34:57  50.6   2200
C   09:34:59  50.62  1900
C   09:35:01  50.63  2100
C   09:35:02  50.64  3200
MS  09:34:57  29.46  6800
MS  09:34:59  29.48  5400
MS  09:35:01  29.5   1300
IBM 09:35:01  174.97 2500
IBM 09:35:02  175.02 8800
```
### 2.1 context by

context by 是Dolphin DB 独有的功能，是对标准SQL语句的拓展，我们可以通过context by子句实现的分组计算功能来简化对数据面板的操作。

SQL的group by子句将数据分成多组，每组产生一个值，也就是一行。因此使用group by子句后，行数一般会大大减少。

在对面板数据进行分组后，每一组数据通常是时间序列数据，譬如按股票分组，每一个组内的数据是一个股票的价格序列。处理面板数据时，有时候希望保持每个组的数据行数，也就是为组内的每一行数据生成一个值。例如，根据一个股票的价格序列生成回报序列，或者根据价格序列生成一个移动平均价格序列。其它数据库系统（例如SQL Server，PostGreSQL），用窗口函数(window function)来解决这个问题。DolpinDB引入了context by子句来处理面板数据。context by与窗口函数相比，除了语法更简洁，设计更系统化（与group by和pivot by一起组成对分组数据处理的三个子句）以外，表达能力上也更强大，具体表现在：


*  不仅能与select配合在查询中使用，也可以与update配合更新数据。

*  绝大多数数据库系统在窗口函数中只能使用表中现有的字段分组。context by子句可以使用任何现有字段和计算字段。

*  窗口函数仅限于少数几个函数。context by不仅不限制使用的函数，而且可以使用任意表达式，譬如多个函数的组合。

*  context by可以与having子句配合使用，以过滤每个组内部的行。



(1) 按股票代码进行分组，应用序列函数计算每一只股票的前后交易量比率，进行对比：

```
select timestamp, sym, price, ratios(volume) ,volume from t context by sym;

timestamp sym price  ratios_volume volume
--------- --- ------ ------------- ------
09:34:57  C   50.6                  2200  
09:34:59  C   50.62  0.86           1900  
09:35:01  C   50.63  1.106          2100  
09:35:02  C   50.64  1.52           3200  
09:35:01  IBM 174.97                2500  
09:35:02  IBM 175.02 3.52           8800  
09:34:57  MS  29.46                 6800  
09:34:59  MS  29.48  0.79           5400  
09:35:01  MS  29.5   0.24           1300  
```

(2) 结合滑动窗口函数，计算每只股票在3次数据更新中的平均价格：

```
select *, mavg(price,3) from t context by sym;

sym timestamp price  volume mavg_price        
--- --------- ------ ------ -----------
C   09:34:57  50.60  2200                     
C   09:34:59  50.62  1900                     
C   09:35:01  50.63  2100   50.62
C   09:35:02  50.64  3200   50.63
IBM 09:35:01  174.97 2500                     
IBM 09:35:02  175.02 8800                     
MS  09:34:57  29.46  6800                     
MS  09:34:59  29.48  5400                     
MS  09:35:01  29.50  1300   29.48        

```
(3) 结合累计窗口函数，计算每只股票在每一次的数据更新中最大交易量：

```
select timestamp, sym, price,volume, cummax(volume) from t context by sym;

timestamp sym price  volume cummax_volume
--------- --- ------ ------ -------------
09:34:57  C   50.6   2200   2200         
09:34:59  C   50.62  1900   2200         
09:35:01  C   50.63  2100   2200         
09:35:02  C   50.64  3200   3200         
09:35:01  IBM 174.97 2500   2500         
09:35:02  IBM 175.02 8800   8800         
09:34:57  MS  29.46  6800   6800         
09:34:59  MS  29.48  5400   6800   
09:35:01  MS  29.5   1300   6800   
```
(4) 应用聚合函数，计算每只股票在每分钟中的最大交易量：
```
select *, max(volume) from t context by sym, timestamp.minute();

sym timestamp price  volume max_volume
--- --------- ------ ------ ----------
C   09:34:57  50.61  2200   2200      
C   09:34:59  50.62  1900   2200      
C   09:35:01  50.63  2100   3200      
C   09:35:02  50.64  3200   3200      
IBM 09:35:01  174.97 2500   8800      
IBM 09:35:02  175.02 8800   8800      
MS  09:34:57  29.46  6800   6800      
MS  09:34:59  29.48  5400   6800      
MS  09:35:01  29.5   1300   1300      
```
### 2.2 pivot by

pivot by是DolphinDB的独有功能，是对标准SQL语句的拓展，可将数据表中某列的内容按照两个维度整理，产生数据表或矩阵。

通过应用pivot by子句，可以对于数据表t进行重新排列整理：每行为一秒钟，每列为一只股票，既能够了解单个股票每个时刻的变化，也可以了解各股票之间的差异。

如：对比同一时间段不同股票的交易价格：
```
select price from t pivot by timestamp, sym;

timestamp C     IBM    MS
--------- ----- ------ -----
09:34:57  50.6         29.46
09:34:59  50.62        29.48
09:35:01  50.63 174.97 29.5
09:35:02  50.64 175.02
```

pivot by还可以与聚合函数一起使用。比如，将数据中每分钟的平均收盘价转换为数据表：
```
select avg(price) from t where sym in `C`IBM pivot by minute(timestamp) as minute, sym;

minute C      IBM
------ ------ -------
09:34m 50.61
09:35m 50.635 174.995

```

## 3. 向量化函数处理面板数据

当使用DolphinDB的矩阵来表示面板数据时，数据按时间序列和横截面两个维度进行排列。

对矩阵表示的面板数据进行分析时，如：每行是按时间戳排序的时间点，每列是一只股票，我们既可以对某一只股票进行多个时间点的动态变化分析，也可以了解多个股票之间在某个时点的差异情况。

向量化函数panel可将一列或多列数据转换为矩阵。例如，将数据表t中的price列转换为一个矩阵：

```
price = panel(t.timestamp, t.sym, t.price);
price;

         C     IBM    MS
         ----- ------ -----
09:34:57|50.60        29.46
09:34:59|50.62        29.48
09:35:01|50.63 174.97 29.5
09:35:02|50.64 175.02
```
以下脚本将price与volume列分别转换为矩阵。返回的结果是一个元组，每个元素对应一列转换而来的矩阵。

```
price, volume = panel(t.timestamp, t.sym, [t.price, t.volume]);
```
使用panel函数时，可以指定结果矩阵的行与列的标签。这里需要注意，行与列的标签均需严格升序。例如：

```
rowLabel = 09:34:59..09:35:02;
colLabel = ["C", "MS"];
volume = panel(t.timestamp, t.sym, t.volume, rowLabel, colLabel);
volume;
         C    MS  
         ---- ----
09:34:59|1900 5400
09:35:00|         
09:35:01|2100 1300
09:35:02|3200     

```
使用rowNames和colNames函数可以获取panel函数返回的矩阵的行和列标签：
```
volume.rowNames();

volume.colNames();
```
如果后续要对面板数据做一步的计算和处理，推荐使用矩阵来表示面板数据。这是因为矩阵天然支持向量化操作和二元操作，计算效率会更高，代码会更简洁。


### 3.1 矩阵操作示例

下面举例一些处理用矩阵表示的面板数据时常用的操作。

(1) 通过序列函数,对每个股票的相邻价格进行比较。
```
price = panel(t.timestamp, t.sym, t.price);
deltas(price);

         C    IBM  MS  
         ---- ---- -----
09:34:57|                                        
09:34:59|0.02      0.02
09:35:01|0.01      0.02
09:35:02|0.01 0.05
```

(2) 结合滑动窗口函数，计算每只股票在每2次数据更新中的平均价格。

```
mavg(price,2);

         C      IBM      MS                
         ------ ------ -----------
09:34:57|                                                         
09:34:59|50.61         29.47
09:35:01|50.63  174.97 29.49
09:35:02|50.63  175.00 29.50
```

(3) 结合累计窗口函数，计算每只股票中价格的排序。
```
cumrank(price);

         C IBM MS
         - --- --
09:34:57|0     0 
09:34:59|1     1 
09:35:01|2 0   2 
09:35:02|3 1     
```
(4) 通过聚合函数,得到每只股票中的最低价格。
 
 ```
 min(price);
 
 [50.60,174.97,29.46]

```
(5) 通过聚合函数，得到每一个同时间段的最低股票价格。
```
rowMin(price);

[29.46,29.48,29.5,50.64]
```

### 3.2 对齐矩阵的二次运算

DolphinDB提供了两种扩展的数据结构来支持面板数据的对齐运算：indexedMatrix和indexedSeries。

普通矩阵进行二元运算时，按照对应元素分别进行计算，需要保持维度(shape)一致，而indexedMatrix和indexedSeries 帮助矩阵或向量进行二元运算时根据行列标签（index）自动对齐，对维度没有硬性要求。

indexedMatrix和indexedSeries支持的二元运算符和函数有：

（1）算术运算符和函数：+, -, *, /(整除), ratio, %(mod), pow

（2）逻辑运算符和函数：and, or, bitXor, &, |

（3）滑动窗口函数：mwavg, mwsum, mbeta, mcorr, mcovar

（4）累计窗口函数：cumwavg, cumwsum, cumbeta, cumcorr, cumcovar

（5）聚合函数：wavg, wsum, beta, corr, covar

#### 3.2.1 indexedMatrix

indexedMatrix是特殊的矩阵，它将矩阵的行与列标签作为索引。indexedMatrix进行二元运算时，系统对根据行与列标签将多个矩阵对齐，只对行列标签相同的数据进行计算。使用setIndexedMatrix!函数可以将普通矩阵设置为indexedMatrix。比如：

```
m=matrix(1..5, 6..10, 11..15);
m.rename!(2020.01.01..2020.01.05, `A`B`C);
m.setIndexedMatrix!();

           A B  C
           - -- --
2020.01.01|1 6  11
2020.01.02|2 7  12
2020.01.03|3 8  13
2020.01.04|4 9  14
2020.01.05|5 10 15

n=matrix(1..5, 6..10, 11..15);
n.rename!(2020.01.02..2020.01.06, `B`C`D);
n.setIndexedMatrix!();

           B C  D
           - -- --
2020.01.02|1 6  11
2020.01.03|2 7  12
2020.01.04|3 8  13
2020.01.05|4 9  14
2020.01.06|5 10 15

m+n;
           A B  C  D
           - -- -- -
2020.01.01|
2020.01.02|  8  18
2020.01.03|  10 20
2020.01.04|  12 22
2020.01.05|  14 24
2020.01.06|
```

#### 3.2.2 indexedSeries

可以使用indexedSeries函数生成带有索引的向量。例如：

```
index = 2008.01.02..2008.01.31;
value = 1..30;
indexedSeries(index, value);
```

（1）indexedSeries之间的对齐运算

两个indexedSeries进行二元操作，会根据index进行对齐再做计算。

```
index1 = 2020.11.01..2020.11.06;
value1 = 1..6;
s1 = indexedSeries(index1, value1);

index2 = 2020.11.04..2020.11.09;
value2 =4..9;
s2 = indexedSeries(index2, value2);

s1+s2;
           #0
           --
2020.11.01|
2020.11.02|
2020.11.03|
2020.11.04|8
2020.11.05|10
2020.11.06|12
2020.11.07|
2020.11.08|
2020.11.09|
```

（2）indexedSeries和indexedMatrix之间的对齐运算

indexedSeries与indexedMatrix进行二元操作，会根据行标签进行对齐，indexedSeries与indexedMatrix的每列进行计算。

```
m1=matrix(1..6, 11..16);
m1.rename!(2020.11.04..2020.11.09, `A`B);
m1.setIndexedMatrix!();
m1;
           A B
           - --
2020.11.04|1 11
2020.11.05|2 12
2020.11.06|3 13
2020.11.07|4 14
2020.11.08|5 15
2020.11.09|6 16

s1;
           #0
           --
2020.11.01|1
2020.11.02|2
2020.11.03|3
2020.11.04|4
2020.11.05|5
2020.11.06|6

m1 + s1;
           A B
           - --
2020.11.01|
2020.11.02|
2020.11.03|
2020.11.04|5 15
2020.11.05|7 17
2020.11.06|9 19
2020.11.07|
2020.11.08|
2020.11.09|
```

### 3.3 重采样和频度转换

DolphinDB提供了resample和asfreq函数，用于对有时间类型索引的indexedSeries或者indexedMatrix进行重采样和频度转换。

其实现目的是提供用户一个对常规时间序列数据重新采样和频率转换的便捷的方法。

#### 3.3.1 resample（重采样）

重采样是指将时间序列的频度转换为另一个频度。重采样时必须指定一个聚合函数对数据进行计算。

降低采样频率为月：
```
index=2020.01.01..2020.06.30;
s=indexedSeries(index, take(1,size(index)));
s.resample("M",sum);
           #0
           --
2020.01.31|31
2020.02.29|29
2020.03.31|31
2020.04.30|30
2020.05.31|31
2020.06.30|30
```

#### 3.3.2 asfreq（频率转换）

asfreq函数转换给定数据的时间频率。与resample函数不同，asfreq不能使用聚合函数对数据进行处理。

```
s.asfreq("M");
           #0
           --
2020.01.31|1
2020.02.29|1
2020.03.31|1
2020.04.30|1
2020.05.31|1
2020.06.30|1
```

#### 3.3.3 NULL值的处理

在重采样和频率转换中，可能需要对结果的NULL值进行处理。

（1）删除NULL值

DolphinDB提供dropna函数，用于删除向量中的NULL值，或矩阵中包含NULL值的行或列。

dropna的语法如下：
```
dropna(X, [byRow=true], [thresh])
```
- X是向量或矩阵。
- byRow是布尔值。byRow=true表示按行删除，byRow=false表示按列删除。
- thresh是整数。若一行（列）中非NULL元素少于该值，则删除该行（列）。

```
index=2020.01.01..2020.06.30;
m=matrix(take(3 4 5 NULL NULL 1 2, size(index)), take(1 2 3 4 5 NULL NULL, size(index)));
m.rename!(index, `A`B);
m.setIndexedMatrix!();
m.asfreq("M");
           A B
           - -
2020.01.31|5 3
2020.02.29|  4
2020.03.31|2
2020.04.30|4 2
2020.05.31|  5
2020.06.30|2

m.asfreq("M").dropna();
           A B
           - -
2020.01.31|5 3
2020.04.30|4 2
```

（2）填充NULL值

DolphinDB提供多种填充NULL值的函数：向前填充ffill，向后填充bfill，特定值填充nullFill和线性插值interpolate。例如：

```
m.asfreq("M").ffill();
           A B
           - -
2020.01.31|5 3
2020.02.29|5 4
2020.03.31|2 4
2020.04.30|4 2
2020.05.31|4 5
2020.06.30|2 5
```
（3）替换NULL值

DolphinDB提供高阶函数withNullFill，可以用特定值替换Null值参与计算。

withNullFill函数的语法如下：
```
withNullFill(func, x, y, fillValue) 
```
- func是一个DolphinDB内置函数，须为双目运算符，例如+, -, *, /, ratio, %, pow, and, or 等。
- x和y可以是向量或矩阵。
- fillValue是一个标量。

若x与y中相同位置的元素只有一个为NULL，使用fillValue替换NULL值参与计算。如果x和y相同位置的元素均为NULL，返回NULL。

```
s1=m.asfreq("M")[`A];
s2=m.asfreq("M")[`B];
s1+s2;
           #0
           --
2020.01.31|8
2020.02.29|
2020.03.31|
2020.04.30|6
2020.05.31|
2020.06.30|

withNullFill(add, s1, s2, 0);
           #0
           --
2020.01.31|8
2020.02.29|4
2020.03.31|2
2020.04.30|6
2020.05.31|5
2020.06.30|2
```



## 4. 面板数据处理方式的对比

下面我们会以一个更为复杂的实际例子演示如何高效的解决面板数据问题。著名论文[101 Formulaic Alphas](https://arxiv.org/ftp/arxiv/papers/1601/1601.00991.pdf)给出了世界顶级量化对冲基金WorldQuant所使用的101个因子公式，其中里面80%的因子仍然还行之有效并被运用在实盘项目中。

这里选取了WorldQuant公开的Alpha98因子的表达式。
```
alpha_098 = (rank(decay_linear(correlation(((high_0+low_0+open_0+close_0)*0.25), sum(mean(volume_0,5), 26.4719), 4.58418), 7.18088)) -rank(decay_linear(ts_rank(ts_argmin(correlation(rank(open_0), rank(mean(volume_0,15)), 20.8187), 8.62571),6.95668), 8.07206)))
```
为了更好的对比各个处理方式之间的差异，选择了一年的股票每日数据，涉及的原始数据量约为35万条。

以下是脚本测试所需要的数据, 输入数据为包含以下字段的table：

- ts_code：股票代码

- trade_date：日期

- amount：交易额

- vol：成交量

- vwap：成交量的加权平均价格

- open：开盘价格

- close：收盘价格

### 4.1 DolphinDB SQL 与 向量化函数处理面板数据的对比

我们会分别使用DolphinDB SQL语句和矩阵来实现计算Alpha98因子。


*  DolphinDB SQL语句实现Alpha98因子计算的脚本如下：
```
def alpha98(stock){
	t = select ts_code, trade_date, (stock.amount * 1000) /(stock.vol * 100 + 1) as vwap, open, mavg(vol, 5) as adv5, mavg(vol,15) as adv15 from stock context by ts_code
	update t set rank_open = rank(open), rank_adv15 = rank(adv15) context by trade_date
	update t set decay7 = mavg(mcorr(vwap, msum(adv5, 26), 5), 1..7), decay8 = mavg(mrank(9 - mimin(mcorr(rank_open, rank_adv15, 21), 9), true, 7), 1..8) context by ts_code
	return select ts_code, trade_date, rank(decay7)-rank(decay8) as A98 from t context by trade_date 
}

```

```
DIR="/home/llin/hzy/server1/support"
t=loadText(DIR+"/tushare_daily_data.csv")
timer alpha98(t)
```

*  以下是在DolphinDB中通过向量化函数来计算98号因子的脚本：

```
def myrank(x){
	return rowRank(x)\x.columns()
}

def alpha98(vwap, open, vol){
	return myrank(mavg(mcorr(vwap, msum(mavg(vol, 5), 26), 5), 1..7)) - myrank(mavg(mrank(9 - mimin(mcorr(myrank(open), myrank(mavg(vol, 15)), 21), 9), true, 7), 1..8))
}
```


```
DIR="/home/llin/hzy/server1/support"
t=loadText(DIR+"/tushare_daily_data.csv")
timer vwap, open, vol = panel(t.trade_date, t.ts_code, [(t.amount * 1000) /(t.vol * 100 + 1), t.open, t.vol])
timer res = alpha98(vwap, open, vol)
```
通过两个Alpha98因子脚本的对比，我们可以发现用向量化函数来实现Alpha98因子的脚本会更加简洁一点。
因为Alpha98因子在计算过程中用到了截面数据，也用到了大量时间序列的计算，即在计算某天股票某一天的因子中，既要用到该股票的历史数据，也要用到当天所有股票的信息，对信息量的要求很大，
而矩阵形式的面板数据是截面数据和时间序列数据综合起来的一种数据类型，可以支持股票数据按两个维度进行排列，
所以在实现Alpha98因子计算中，不需要多次对中间数据或输出数据进行多次维度转换，简化了计算逻辑。对比使用SQL语句执行计算，在实现Alpha98因子计算的过程中，进行函数嵌套的同时还需要多次进行分组计算来处理数据。用panel函数来处理面板数据，明显计算效率会更高，代码会更简洁。

在性能测试方面，我们使用单线程计算，SQL语句计算Alpha98因子耗时232ms。而panel函数生成面板数据耗时37ms，计算Alpha98因子耗时141ms。两者的耗时差异不大，矩阵方式可能略胜一筹。

但是向量化函数处理面板数据也有局限性, 矩阵的面板数据无法进行再次分组，单值模型格式不够直观，而SQL支持多列分组，可以联合查询多个字段的信息，适用于海量数据的并行计算。 

在处理面板数据时，客户可根据自身对数据的分析需求，来选择不同的方法处理面板数据。



### 4.2 DolphinDB与pandas处理面板数据的性能对比：



pandas实现alpha98因子的脚本如下：
 
```
vwap=conn.run("vwap1");
vwap.set_index("trade_date", inplace=True)
open=conn.run("open1");
vol=conn.run("vol1");
open.set_index("trade_date", inplace=True)
vol.set_index("trade_date", inplace=True)

def myrank(x):
    return ((x.rank(axis=1,method='min'))-1)/x.shape[1]

def wavg(x, weight):
    return (x*weight).sum()/weight.sum()

def imin(x):
    return np.where(x==min(x))[0][0]


def rank(x):
    s = pd.Series(x)
    return (s.rank(ascending=True, method="min")[len(s)-1])-1


def alpha98(vwap, open, vol):
    return myrank(vwap.rolling(5).corr(vol.rolling(5).mean().rolling(26).sum()).rolling(7).apply(wavg, args=[np.arange(1, 8)])) - myrank((9 - myrank(open).rolling(21).corr(myrank(vol.rolling(15).mean())).rolling(9).apply(imin)).rolling(7).apply(rank).rolling(8).apply(wavg, args=[np.arange(1, 9)]))


```
```
start_time = time.time()
re=alpha98(vwap, open, vol)
print("--- %s seconds ---" % (time.time() - start_time))

```
使用pandas计算，Alpha98耗时290s，而使用矩阵实现计算仅耗时141ms，性能相差千倍。

性能上的巨大差异，主要得益于DolphinDB内置了许多与时序数据相关的函数，并进行了优化，性能优于其它系统1~2个数量级, 比如上面使用到的mavg、mcorr、mrank、mimin、msum等计算滑动窗口函数。
尤其实在计算测试二元滑动窗口（mcorr）中，DolphinDB的计算耗时0.6秒，pandas耗时142秒，性能相差200倍以上。为了避免计算结果的偶然性，我们使用了十年的股市收盘价数据，涉及的原始数据量约为530万条，对比结果是连续运行十次的耗时ms。

就整体而言，在Alpha98因子的计算中，DolphinDB会出现性能上的断层式优势是有迹可循的。

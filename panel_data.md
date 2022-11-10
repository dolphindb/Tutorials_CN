# DolphinDB 教程：面板数据的处理

时间序列数据、截面数据和面板数据是金融领域中常见的数据组织方式。面板数据包含了时间序列和横截面两个维度。在 Python 中，通常可以用 pandas 的 DataFrame 或 numpy 的二维数组来表示。在 DolphinDB 中面板数据也可以用表（table）或矩阵（matrix）来表示。

本教程主要介绍如何在 DolphinDB 中表示和分析面板数据。本文的所有例子都基于 DolphinDB 1.30.16/2.00.4。

<!-- TOC -->
- [DolphinDB 教程：面板数据的处理](#dolphindb-教程面板数据的处理)
  - [1. 面板数据的表示方法和处理函数](#1-面板数据的表示方法和处理函数)
  - [2. SQL 语句处理面板数据](#2-sql-语句处理面板数据)
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
      - [3.3.3 NULL 值的处理](#333-null-值的处理)
  - [4. 面板数据处理方式的对比](#4-面板数据处理方式的对比)
    - [4.1 DolphinDB SQL 与向量化函数处理面板数据的对比](#41-dolphindb-sql-与向量化函数处理面板数据的对比)
    - [4.2 DolphinDB 与 pandas 处理面板数据的性能对比：](#42-dolphindb-与-pandas-处理面板数据的性能对比)
  - [5. 附录](#5-附录)

<!-- /TOC -->

## 1. 面板数据的表示方法和处理函数

DolphinDB 提供了两种方法处理面板数据：

- 通过 SQL 和向量化函数来处理用二维表表示的面板数据
- 通过向量化函数来处理用矩阵表示的面板数据

DolphinDB 中数据表和矩阵都采用了列式存储。以下是表和矩阵中的列常用的计算函数和二元运算符:

- 二元运算符：+, -, *, /, ratio, %, &&, ||, &, |, pow
- 序列函数：ratios, deltas, prev, next, move
- [滑动窗口函数](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/SeriesOfFunctions/mFunctions.html)：mcount，mavg, msum, mmax, mimax, mimin, mmin, mprod, mstd, mvar, mmed, mpercentile, mrank, mwavg, mwsum, mbeta, mcorr, mcovar
- [累计窗口函数](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/SeriesOfFunctions/cumFunctions.html)：cumcount, cumavg, cumsum, cummax, cummin, cumprod, cumstd, cumvar, cummed, cumpercentile, cumPositiveStreak, cumrank, cumwavg, cumwsum, cumbeta, cumcorr, cumcovar
- 聚合函数：count, avg, sum, sum2, first, firstNot, last, lastNot, max, min, std, var, med, mode, percentile, atImax, atImin, wavg, wsum, beta, corr, covar
- [row 系列函数](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/SeriesOfFunctions/rowFunctions.html)（针对面板数据的每一行进行计算）：rowCount, rowAvg, rowSum, rowSum2, rowProd, rowMax, rowMin, rowStd, rowVar, rowBeta, rowCorr, rowAnd, rowOr, rowXor

下文通过举例的方式让读者更能了解这些函数是如何进行面板数据操作。

## 2. SQL 语句处理面板数据

当使用 DolphinDB 的二维数据表来表示 SQL 的面板数据时，通常一个列存储一个指标，譬如 open, high, low, close, volume 等，一行代表一个股票在一个时间点的数据。这样的好处是，多个指标进行处理时，不再需要对齐数据。缺点是分组计算（按股票分组的时间序列计算，或者按时间分组的横截面计算），需要先分组。SQL 语句的 group by/context by/pivot by 子句均可用于分组。分组有一定的开销，通常尽可能把所有的计算在一次分组内全部计算完成。

DolphinDB 的 SQL 不仅支持 SQL 的标准功能，还进行了扩展，包括面板数据处理，非同时连接，窗口连接，窗口函数等。本章节中会分别展示如何用 SQL 语句处理面板数据。

首先，模拟一份含有 3 种股票代码的数据。这份数据在之后的例子中都会用到：

```
sym = `C`C`C`C`MS`MS`MS`IBM`IBM
timestamp = [09:34:57,09:34:59,09:35:01,09:35:02,09:34:57,09:34:59,09:35:01,09:35:01,09:35:02]
price= 50.6 50.62 50.63 50.64 29.46 29.48 29.5 174.97 175.02
volume = 2200 1900 2100 3200 6800 5400 1300 2500 8800
t = table(sym, timestamp, price, volume);
t;

# output
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

context by 是 DolphinDB 独有的功能，是对标准 SQL 语句的拓展，我们可以通过 context by 子句实现的分组计算功能来简化对数据面板的操作。

SQL 的 group by 子句将数据分成多组，每组产生一个值，也就是一行。因此使用 group by 子句后，行数一般会大大减少。

在对面板数据进行分组后，每一组数据通常是时间序列数据，譬如按股票分组，每一个组内的数据是一个股票的价格序列。处理面板数据时，有时候希望保持每个组的数据行数，也就是为组内的每一行数据生成一个值。例如，根据一个股票的价格序列生成回报序列，或者根据价格序列生成一个移动平均价格序列。其它数据库系统（例如 SQL Server, PostgreSQL），用窗口函数（window function）来解决这个问题。DolpinDB 引入了 context by 子句来处理面板数据。context by 与 group by, pivot by 一起组成了 DolphinDB 分组数据处理系统。它与窗口函数相比，除了语法更简洁以外，表达能力上也更强大，具体表现在：


*  不仅能与 select 配合查询数据，也可以与 update 配合更新数据。

*  绝大多数数据库系统在窗口函数中只能使用表中现有的字段分组。context by 子句可以使用任何现有字段和计算字段。

*   绝大多数数据库系统的窗口函数仅限于少数几个函数。context by 不仅不限制使用的函数，而且可以使用任意表达式，譬如多个函数的组合。

*  context by 可以与 having 子句配合使用，以过滤每个组内部的行。

例：

(1) 按股票代码进行分组，应用序列函数计算每一只股票的前后交易量比率，进行对比：

```
select timestamp, sym, price, ratios(volume) ,volume from t context by sym;

# output
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

(2) 结合滑动窗口函数，计算每只股票在 3 次数据更新中的平均价格：

```
select *, mavg(price,3) from t context by sym;

# output
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

# output
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

# output
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

pivot by 是 DolphinDB 的独有功能，是对标准 SQL 语句的拓展，可将数据表中某列的内容按照两个维度整理，产生数据表或矩阵。

通过应用 pivot by 子句，可以对于数据表 t 进行重新排列整理：每行为一秒钟，每列为一只股票，既能够了解单个股票每个时刻的变化，也可以了解各股票之间的差异。

如：对比同一时间段不同股票的交易价格：
```
select price from t pivot by timestamp, sym;

# output
timestamp C     IBM    MS
--------- ----- ------ -----
09:34:57  50.6         29.46
09:34:59  50.62        29.48
09:35:01  50.63 174.97 29.5
09:35:02  50.64 175.02
```

pivot by 还可以与聚合函数一起使用。比如，将数据中每分钟的平均收盘价转换为数据表：
```
select avg(price) from t where sym in `C`IBM pivot by minute(timestamp) as minute, sym;

# output
minute C      IBM
------ ------ -------
09:34m 50.61
09:35m 50.635 174.995

```

pivot by 与 select 子句一起使用时返回一个表，而和 exec 语句一起使用时返回一个矩阵：

```
resM = exec avg(price) from t where sym in `C`IBM pivot by minute(timestamp) as minute, sym;
resM

# output
       C      IBM
       ------ -------
09:34m|50.61
09:35m|50.635 174.995
```

```
typestr(resM)

# output
FAST DOUBLE MATRIX
```

## 3. 向量化函数处理面板数据

当使用 DolphinDB 的矩阵来表示面板数据时，数据按时间序列和横截面两个维度进行排列。

对矩阵表示的面板数据进行分析时，如：每行是按时间戳排序的时间点，每列是一只股票，我们既可以对某一只股票进行多个时间点的动态变化分析，也可以了解多个股票之间在某个时点的差异情况。

向量化函数 panel 可将一列或多列数据转换为矩阵。例如，将数据表 t 中的 price 列转换为一个矩阵：

```
price = panel(t.timestamp, t.sym, t.price);
price;

# output
         C     IBM    MS
         ----- ------ -----
09:34:57|50.60        29.46
09:34:59|50.62        29.48
09:35:01|50.63 174.97 29.5
09:35:02|50.64 175.02
```
以下脚本将 price 与 volume 列分别转换为矩阵。返回的结果是一个元组，每个元素对应一列转换而来的矩阵。

```
price, volume = panel(t.timestamp, t.sym, [t.price, t.volume]);
```
使用 panel 函数时，可以指定结果矩阵的行与列的标签。这里需要注意，行与列的标签均需严格升序。例如：

```
rowLabel = 09:34:59..09:35:02;
colLabel = ["C", "MS"];
volume = panel(t.timestamp, t.sym, t.volume, rowLabel, colLabel);
volume;

# output
         C    MS
         ---- ----
09:34:59|1900 5400
09:35:00|
09:35:01|2100 1300
09:35:02|3200

```

使用 rowNames 和 colNames 函数可以获取 panel 函数返回的矩阵的行和列标签：

```
volume.rowNames();
volume.colNames();
```

如果后续要对面板数据做一步的计算和处理，推荐使用矩阵来表示面板数据。这是因为矩阵天然支持向量化操作和二元操作，计算效率会更高，代码会更简洁。


### 3.1 矩阵操作示例

下文例举了矩阵形式面板数据的常用操作。

(1) 通过序列函数，对每个股票的相邻价格进行比较。
```
price = panel(t.timestamp, t.sym, t.price);
deltas(price);

# output
         C    IBM  MS
         ---- ---- -----
09:34:57|
09:34:59|0.02      0.02
09:35:01|0.01      0.02
09:35:02|0.01 0.05
```

(2) 结合滑动窗口函数，计算每只股票在每 2 次数据更新中的平均价格。

```
mavg(price,2);

# output
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

# output
         C IBM MS
         - --- --
09:34:57|0     0
09:34:59|1     1
09:35:01|2 0   2
09:35:02|3 1
```
(4) 通过聚合函数, 得到每只股票中的最低价格。

 ```
 min(price);

 # output
 [50.60,174.97,29.46]

```
(5) 通过聚合函数，得到每一个同时间段的最低股票价格。
```
rowMin(price);

 # output
[29.46,29.48,29.5,50.64]
```

### 3.2 对齐矩阵的二次运算

普通矩阵进行二元运算时，按照对应元素分别进行计算，需要保持维度 (shape) 一致，DolphinDB 提供了矩阵对齐的方法，使得矩阵计算不再受维度的限制。

在 1.30.20/2.00.8 版本前，用户需要通过 indexedMatrix 和 indexedSeries 来支持矩阵的对齐运算，其标签必须是严格递增的。

* indexedMatrix：以行列标签为索引的矩阵。
* indexedSeries：带索引标签的向量。

indexedMatrix 和 indexedSeries 在进行二元运算时，系统会自动以 "outer join" 的方式对齐，然后进行运算。

1.30.20/2.00.8 版本后，DolphinDB 提供了用于矩阵对齐的函数 [align](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/FunctionReferences/a/align.html)，拓展了标签矩阵的对齐功能，使矩阵对齐和运算更加灵活。

(1) indexedSeries 之间的对齐运算

两个 indexedSeries 进行二元操作，会根据 index 进行对齐再做计算。

```
index1 = 2020.11.01..2020.11.06;
value1 = 1..6;
s1 = indexedSeries(index1, value1);

index2 = 2020.11.04..2020.11.09;
value2 =4..9;
s2 = indexedSeries(index2, value2);

s1+s2;

 # output
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

(2) indexedMatrix 之间的对齐运算

两个 indexedMatrix 进行二元操作，其对齐的方法和 indexedSeries  一致。

```
id1 = 2020.11.01..2020.11.06;
m1 = matrix(1..6, 7..12, 13..18).rename!(id1, `a`b`d)
m1.setIndexedMatrix!()

id2 = 2020.11.04..2020.11.09;
m2 = matrix(4..9, 10..15, 16..21).rename!(id2, `a`b`c)
m2.setIndexedMatrix!()

m1+m2;

 # output
           a  b  c d
           -- -- - -
2020.11.01|         
2020.11.02|         
2020.11.03|         
2020.11.04|8  20    
2020.11.05|10 22    
2020.11.06|12 24    
2020.11.07|         
2020.11.08|         
2020.11.09|
```
(3) indexedSeries 和 indexedMatrix 之间的对齐运算

indexedSeries 与 indexedMatrix 进行二元操作，会根据行标签进行对齐，indexedSeries 与 indexedMatrix 的每列进行计算。

```
m1=matrix(1..6, 11..16);
m1.rename!(2020.11.04..2020.11.09, `A`B);
m1.setIndexedMatrix!();
m1;

 # output
           A B
           - --
2020.11.04|1 11
2020.11.05|2 12
2020.11.06|3 13
2020.11.07|4 14
2020.11.08|5 15
2020.11.09|6 16

s1;

 # output
           #0
           --
2020.11.01|1
2020.11.02|2
2020.11.03|3
2020.11.04|4
2020.11.05|5
2020.11.06|6

m1 + s1;

 # output
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

(4) 使用 align 函数进行对齐

```
x1 = [09:00:00, 09:00:01, 09:00:03]
x2 = [09:00:00, 09:00:03, 09:00:03, 09:00:04]
y1 = `a`a`b
y2 = `a`b`b
m1 = matrix(1 2 3, 2 3 4, 3 4 5).rename!(y1,x1)
m2 = matrix(11 12 13, 12 13 14, 13 14 15, 14 15 16).rename!(y2,x2)
a, b = align(m1, m2, 'ej,aj', false);
a;

# output
  09:00:00 09:00:01 09:00:03
  -------- -------- --------
a|1        2        3       
a|2        3        4       
b|3        4        5      

b;

# output
  09:00:00 09:00:01 09:00:03
  -------- -------- --------
a|11       11       13      
b|12       12       14      
b|13       13       15
```


### 3.3 重采样和频度转换

DolphinDB 提供了 [resample](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/FunctionReferences/r/resample.html) 和 [asfreq](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/FunctionReferences/a/asfreq.html) 函数，用于对有时间类型索引的 indexedSeries 或者 indexedMatrix 进行重采样和频度转换。

其实现目的是为用户提供一个对常规时间序列数据重新采样和频率转换的便捷的方法。

#### 3.3.1 resample（重采样）

重采样是指将时间序列的频度转换为另一个频度。重采样时必须指定一个聚合函数对数据进行计算。

降低采样频率为月：
```
index=2020.01.01..2020.06.30;
s=indexedSeries(index, take(1,size(index)));
s.resample("M",sum);

 # output
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

asfreq 函数转换给定数据的时间频率。与 resample 函数不同，asfreq 不能使用聚合函数对数据进行处理。asfreq 通常应用于将低频转时间换为高频时间的场景，且与各类 fill 函数配合使用。

提高采样频率为日：
```
index=2020.01.01 2020.01.05 2020.01.10
s=indexedSeries(index, take(1,size(index)));
s.asfreq("D").ffill()

 # output
            #0
           --
2020.01.01|1
2020.01.02|1
2020.01.03|1
2020.01.04|1
2020.01.05|1
2020.01.06|1
2020.01.07|1
2020.01.08|1
2020.01.09|1
2020.01.10|1
```

#### 3.3.3 NULL 值的处理

在重采样和频率转换中，可能需要对结果的 NULL 值进行处理。具体的处理方法请参考[矩阵运算教程](https://gitee.com/dolphindb/Tutorials_CN/blob/master/matrix.md)  2.6 节的介绍。

### 3.4 矩阵聚合

#### 3.4.1  列聚合

对矩阵应用内置的向量函数、聚合函数以及窗口函数，计算都是按列进行的。

以对某个矩阵应用求和 sum 为例：

```
m = rand(10, 20)$10:2
sum(m)

# output
[69, 38]
```
可以看出，矩阵每一列都被单独视为一个向量进行计算。

自定义函数，若要应用到矩阵每列单独计算，可以通过高阶函数 each 实现。

```
m = rand(10, 20)$10:2
m

# output
#0 #1
-- --
6  6 
9  2 
7  0 
5  5 
8  8 
8  1 
8  4 
7  8 
4  3 
7  0 

def mfunc(x, flag){if(flag==1) return sum(x); else return avg(x)}
each(mfunc, m, 0 1)

# output
[6.5, 38]
```

#### 3.4.2 行聚合

DolphinDB 提供了按行进行运算的高阶函数 byRow，以及一系列内置的 row 函数（参见 row 系列函数）。

以对某个矩阵应用 row 函数 [rowCount](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/FunctionReferences/r/rowCount.html) 为例：

```
m=matrix([4.5 NULL 1.5, 1.5 4.8 5.9, 4.9 2.0 NULL]);
rowCount(m);

# output
[3,2,2]
```

rowCount 统计每行非空的元素个数，返回一个长度和原矩阵行数相同的向量。

自定义函数，若要应用到矩阵每行单独计算，可以通过高阶函数 byRow 实现。复用 3.4.1 的自定义函数 mfunc 和矩阵 m：

```
byRow(mfunc{, 0}, m)

# output
[6,5.5,3.5,5,8,4.5,6,7.5,3.5,3.5]
```

#### 3.4.3 分组聚合

数据表的分组聚合可以通过 SQL 的 [group by](https://www.dolphindb.cn/cn/help/200/SQLStatements/groupby.html) 语句实现；而通过 [regroup](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/FunctionReferences/r/regroup.html) 函数，可以实现矩阵的分组聚合操作。

根据给出的时间标签将一个价格矩阵进行分组聚合：

```
timestamp = 09:00:00 + rand(10000, 1000).sort!()
id= rand(['st1', 'st2'], 1000)
price = (190 + rand(10.0, 2000))$1000:2
regroup(price, minute(timestamp), avg, true)
```

对于 [pivot by](https://www.dolphindb.cn/cn/help/200/SQLStatements/pivotBy.html) 产生的面板矩阵，按照 label 进行聚合，可以通过 [rowNames](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/FunctionReferences/r/rowNames.html) 或者 [colNames](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/FunctionReferences/c/columnNames.html) 获取标签：

```
n=1000
timestamp = 09:00:00 + rand(10000, n).sort!()
id = take(`st1`st2`st3, n)
vol = 100 + rand(10.0, n)
t = table(timestamp, id, vol)

m = exec vol from t pivot by timestamp, id
regroup(m,minute(m.rowNames()), avg)
```

## 4. 面板数据处理方式的对比

下面以一个更为复杂的实际例子演示如何高效的解决面板数据问题。著名论文 [101 Formulaic Alphas](https://arxiv.org/ftp/arxiv/papers/1601/1601.00991.pdf) 给出了世界顶级量化对冲基金 WorldQuant 所使用的 101 个因子公式，其中里面 80% 的因子仍然行之有效并被运用在实盘项目中。

这里选取了 WorldQuant 公开的 Alpha98 因子的表达式。
```
alpha_098 = (rank(decay_linear(correlation(((high_0+low_0+open_0+close_0)*0.25), sum(mean(volume_0,5), 26.4719), 4.58418), 7.18088)) -rank(decay_linear(ts_rank(ts_argmin(correlation(rank(open_0), rank(mean(volume_0,15)), 20.8187), 8.62571),6.95668), 8.07206)))
```
为了更好的对比各个处理方式之间的差异，我们选择了一年的股票每日数据，涉及的原始数据量约为 100 万条。如需数据请参考 [模拟数据脚本](script/panel_data/panelDataDailySimulate.dos)。

以下是脚本测试所需要的数据, 输入数据为包含以下字段的 table：

- securityid：股票代码

- tradetime：时间日期

- vol：成交量

- vwap：成交量的加权平均价格

- open：开盘价格

- close：收盘价格

### 4.1 DolphinDB SQL 与向量化函数处理面板数据的对比

下例分别使用 DolphinDB SQL 语句和矩阵来实现计算 Alpha98 因子。全部 DolphinDB 脚本请参考 [DolphinDB 实现 98 号因子脚本](script/panel_data/alpha98InDDB.dos)。


*  DolphinDB SQL 语句实现 Alpha98 因子计算的脚本如下：
```
def alpha98(stock){
	t = select securityid, tradetime, vwap, open, mavg(vol, 5) as adv5, mavg(vol,15) as adv15 from stock context by securityid
	update t set rank_open = rank(open), rank_adv15 = rank(adv15) context by tradetime
	update t set decay7 = mavg(mcorr(vwap, msum(adv5, 26), 5), 1..7), decay8 = mavg(mrank(9 - mimin(mcorr(rank_open, rank_adv15, 21), 9), true, 7), 1..8) context by securityid
	return select securityid, tradetime, rank(decay7)-rank(decay8) as A98 from t context by tradetime
}

```

```
t = loadTable("dfs://k_day_level","k_day")
timer alpha98(t)
```

*  以下是在 DolphinDB 中通过向量化函数来计算 98 号因子的脚本：

```
def myrank(x){
	return rowRank(x)\x.columns()
}

def alphaPanel98(vwap, open, vol){
	return myrank(mavg(mcorr(vwap, msum(mavg(vol, 5), 26), 5), 1..7)) - myrank(mavg(mrank(9 - mimin(mcorr(myrank(open), myrank(mavg(vol, 15)), 21), 9), true, 7), 1..8))
}
```


```
t = select * from loadTable("dfs://k_day_level","k_day")
timer vwap, open, vol = panel(t.tradetime, t.securityid, [t.vwap, t.open, t.vol])
timer res = alphaPanel98(vwap, open, vol)
```

通过两个 Alpha98 因子脚本的对比，可以发现用向量化函数来实现 Alpha98 因子的脚本会更加简洁一点。

因为 Alpha98 因子在计算过程中用到了截面数据，也用到了大量时间序列的计算结果。所以在计算某支股票某一天的因子中，既要用到该股票的历史数据，也要用到当天所有股票的信息，对信息量的要求很大。而矩阵形式的面板数据是截面数据和时间序列数据综合起来的一种数据类型，可以支持股票数据按两个维度进行排列，在实现 Alpha98 因子计算中，不需要多次对中间数据或输出数据进行维度转换，简化了计算逻辑。在实现 Alpha98 因子计算的过程中，进行函数嵌套的同时还需要多次进行分组计算来处理数据。对比使用 SQL 语句执行计算，用 panel 函数来处理面板数据，明显计算效率会更高，代码会更简洁。

在性能测试方面，使用单线程计算，SQL 语句计算 Alpha98 因子耗时 610ms。而 panel 函数生成面板数据耗时 70ms，计算 Alpha98 因子耗时 440ms。两者的耗时差异不大，矩阵方式可能略胜一筹。

但是向量化函数处理面板数据也有局限性, 矩阵的面板数据无法进行再次分组，单值模型格式不够直观，而 SQL 支持多列分组，可以联合查询多个字段的信息，适用于海量数据的并行计算。

在处理面板数据时，客户可根据自身对数据的分析需求，来选择不同的方法处理面板数据。


### 4.2 DolphinDB 与 pandas 处理面板数据的性能对比：

pandas 实现 alpha98 因子的部分脚本如下，完整脚本请参考 [python 中实现 98 号因子脚本](script/panel_data/alpha98InPython.py)：

```
def myrank(x):
    return ((x.rank(axis=1,method='min'))-1)/x.shape[1]

def imin(x):
    return np.where(x==min(x))[0][0]


def rank(x):
    s = pd.Series(x)
    return (s.rank(ascending=True, method="min")[len(s)-1])-1


def alpha98(vwap, open, vol):
    return myrank(vwap.rolling(5).corr(vol.rolling(5).mean().rolling(26).sum()).rolling(7).apply(lambda x: np.sum(np.arange(1, 8)*x)/np.sum(np.arange(1, 8)))) - myrank((9 - myrank(open).rolling(21).corr(myrank(vol.rolling(15).mean())).rolling(9).apply(imin)).rolling(7).apply(rank).rolling(8).apply(lambda x: np.sum(np.arange(1, 9)*x)/np.sum(np.arange(1, 9))))
```

```
start_time = time.time()
re=alpha98(vwap, open, vol)
print("--- %s seconds ---" % (time.time() - start_time))
```

使用 pandas 计算 Alpha98 的耗时为 520s，而使用矩阵实现计算仅耗时 440ms，性能相差千倍。

DolphinDB 内置了许多与时序数据相关的函数，并进行了优化，性能优于其它系统 1~2 个数量级。例如上面例子中使用到的 mavg, mcorr, mrank, mimin, msum 等计算滑动窗口函数。
尤其在计算测试二元滑动窗口（mcorr）中，DolphinDB 的计算耗时 0.6 秒，pandas 耗时 142 秒，性能相差 200 倍以上。为了避免计算结果的偶然性，我们使用了十年的股市收盘价数据，涉及的原始数据量约为 530 万条，对比结果是连续运行十次的耗时。

整体而言，在 Alpha98 因子的计算中，DolphinDB 出现性能上的断层式优势是有迹可循的。

## 5. 附录

[模拟数据脚本](script/panel_data/panelDataDailySimulate.dos)

[DolphinDB 实现 98 号因子脚本](script/panel_data/alpha98InDDB.dos)

[Python 实现 98 号因子脚本](script/panel_data/alpha98InPython.py)
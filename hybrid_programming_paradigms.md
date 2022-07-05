# DolphinDB教程：编程语言介绍

开发大数据应用，不仅需要一个能支撑海量数据的分布式数据库，一个能高效利用多核多节点的分布式计算框架，更需要一门能与分布式数据库和分布式计算有机融合，高性能易扩展，表达能力强，满足快速开发和建模需要的编程语言。DolphinDB从流行的SQL和Python语言汲取了灵感，设计了大数据处理脚本语言。本教程讲解如何通过混合范式编程，快速开发大数据分析的应用。从中你也可以了解DolphinDB的编程语言（以下简称DolphinDB）如何与数据库和分布式计算融合。

- [1. 向量化编程(Vector Programming)](#1-向量化编程vector-programming)
- [2. SQL编程(SQL Programming)](#2-sql编程sql-programming)
    - [2.1 SQL与编程语言的融合](#21-sql与编程语言的融合)
    - [2.2 对面板数据(Panel Data)的友好支持](#22-对面板数据panel-data的友好支持)
    - [2.3 对时间序列数据的友好支持](#23-对时间序列数据的友好支持)
    - [2.4 SQL的其它扩展](#24-sql的其它扩展)
- [3. 命令式编程(Imperative Programming)](#3-命令式编程imperative-programming)
- [4. 函数化编程(Functional Programming)](#4-函数化编程functional-programming)
    - [4.1 自定义函数和lambda函数](#41-自定义函数和lambda函数)
    - [4.2 高阶函数(Higher Order Function)](#42-高阶函数higher-order-function)
    - [4.3 部分应用(Partial Application)](#43-部分应用partial-application)
- [5. 远程过程调用编程(RPC Programming)](#5-远程过程调用编程rpc-programming)
    - [5.1 使用remoteRun执行远程函数](#51-使用remoterun执行远程函数)
    - [5.2 使用rpc执行远程函数](#52-使用rpc执行远程函数)
    - [5.3 使用其它函数间接执行远程函数](#53-使用其它函数间接执行远程函数)
    - [5.4 分布式计算](#54-分布式计算)
- [6. 元编程(Metaprogramming)](#6-元编程metaprogramming)
- [7. 小结](#7-小结)

## 1. 向量化编程(Vector Programming)

向量化编程是DolphinDB中最基本的编程范式。DolphinDB中绝大部分函数支持向量作为函数的输入参数。根据函数的返回值的不同，函数可分为两种：一种是聚合函数（aggregate function），返回标量（scalar）；另一种是向量函数，返回与输入向量等长的向量。

向量化操作有三个主要优点：
- 代码简洁
- 大幅降低脚本语言的解释成本
- 可对很多算法进行优化

时间序列数据通常可以用一个向量来表示，用于数据分析的列式数据库的每一个列也都可以用向量来表示。DolphinDB作为一个内存计算引擎或者作为一个分析型的数据仓库，在进行时间序列数据分析时，特别适合使用向量化编程。

以两个长度为一千万的向量相加作为一个简单例子。用命令式编程的for语句，不仅语句冗长，而且耗时是向量化编程的百倍以上。

```
n = 10000000
a = rand(1.0, n)
b = rand(1.0, n)

//采用for语句编程：
c = array(DOUBLE, n)
for(i in 0 : n)
    c[i] = a[i] + b[i]
    
//采用向量化编程：
c = a + b
```

向量化编程实际上是对一组同质数据的批处理，不仅在编译阶段可以利用vectorization对指令进行优化，在很多算法上也可以优化。以经常使用的时间序列数据滑动窗口（sliding window）指标之一的移动平均（moving average）为例。假设总的数据量是n，窗口大小为k，如果不采用批量计算，时间复杂度是O(nk)。但是因为计算完一个窗口的移动平均后，计算下一个窗口时，只有一个数据点发生了变化，所以只要调整这一个点的值，就可以算出新窗口的移动平均，所以批量计算的时间复杂度是O(n)。DolphinDB中，大部分计算滑动窗口指标的函数都经过了优化，性能近似于O(n)。这些函数包括`mmax`, `mmin`, `mimax`, `mimin`, `mavg`, `msum`, `mcount`, `mstd`, `mvar`, `mrank`, `mcorr`, `mcovar`, `mbeta` 和 `mmed`。在下例中，经过优化的`mavg`函数的性能超过对每一个窗口使用`avg`函数300倍。

```
n = 10000000
a = rand(1.0, n)
window = 60

//对每一个窗口分别使用avg计算：
timer moving(avg, a, window);

Time elapsed: 4039.23 ms

//采用mavg函数批量计算：
timer mavg(a, window);

Time elapsed: 12.968 ms
```

向量化编程也有其局限性。首先，不是所有的操作都可以用向量化计算来完成。在机器学习和统计分析中，在某些场景下，只能对逐行数据进行迭代处理，无法向量化计算。对于这种场景，可使用DolphinDB的JIT（即时编译）版本（参见[DolphinDB JIT教程](./jit.md))，将用for语句编写的逐行处理代码在运行时动态编译成机器码执行，从而显著提升性能。

其次，向量化计算通常要将整个向量全部加载到一段连续内存中，Matlab和R都有这样的要求。有时候因为内存碎片原因，无法找到大段的连续内存。DolphinDB针对内存碎片，特别引入了big array，可以将物理上不连续的内存块组成一个逻辑上连续的向量。系统是否采用big array是动态决定的，对用户透明。通常，对big array进行扫描，性能损耗对于连续内存而言，在1%~5%之间；对big array进行随机访问，性能损耗在20%~30%左右。在此方面，DolphinDB是以可以接受的少量性能损失来换取系统的更高可用性。

## 2. SQL编程(SQL Programming)

SQL是一个面向问题的语言。用户只需要给出问题的描述，SQL引擎会产生结果。通常SQL引擎属于数据库的一部分，其它系统通过JDBC，ODBC或Native API 与数据库交流。DolphinDB脚本语言的SQL语句不仅支持SQL的标准功能，而且为大数据的分析，尤其是时间序列大数据的分析做了很多扩展，可极大简化代码，方便用户使用。

### 2.1 SQL与编程语言的融合

在DolphinDB中，脚本语言与SQL语言是无缝融合在一起的。这种融合主要体现在几个方面：
- SQL语句是DolphinDB语言的一个子集，一种表达式。SQL语句可以直接赋给一个变量或作为一个函数的参数。
- SQL语句中可以使用上下文中的创建的变量和函数。如果SQL语句涉及到分布式表，这些变量和函数会自动序列化到相应的节点。
- SQL语句不再是一个简单的字符串，而是可以动态生成的代码。
- SQL语句不仅可以对数据表（table）进行操作，也可对其它数据结构如scalar，vector，matrix，set，dictionary进行操作。数据表可以与其它数据结构进行转换。

请注意，DolphinDB编程语言区分大小写。在DolphinDB中所有的SQL关键词均必须使用小写。

下面例子中，首先生成一个员工工资表：

```
empWages = table(take(1..10, 100) as id, take(2017.10M + 1..10, 100).sort() as month, take(5000 5500 6000 6500, 100) as wage); 
```

然后计算给定的一组员工的平均工资。员工列表存储在一个本地变量empIds中。

```
empIds = 3 4 6 7 9
select avg(wage) from empWages where id in empIds group by id;
id avg_wage
-- --------
3  5500
4  6000
6  6000
7  5500
9  5500
```

除计算平均工资外，同时显示员工的姓名。员工姓名使用一个字典empName来获取。

```
empNames = dict(1..10, `Alice`Bob`Jerry`Jessica`Mike`Tim`Henry`Anna`Kevin`Jones)
select empNames[first(id)] as name, avg(wage) from empWages where id in empIds group by id;
id name    avg_wage
-- ------- --------
3  Jerry   5500
4  Jessica 6000
6  Tim     6000
7  Henry   5500
9  Kevin   5500
```

上面的两个例子中，SQL语句的where子句和select子句分别用到了上下文中定义的数组和字典，使得本来需要通过子查询和多表联结来解决的问题，通过简单的hash table就解决了。如果SQL涉及到分布式数据库，这些上下文变量会自动序列化到相应的节点。这不仅让代码看上去更简洁，有更好的可读性，而且提升了性能。

SQL的select语句返回的数据表可以直接赋给一个本地变量，做进一步的处理分析。DolphinDB还引入了exec关键词，与select相比，EXEC语句返回的结果可以是一个matrix，vector或scalar，更便于数据分析。下面的例子中，exec与pivot by配合使用，直接返回一个矩阵。

```
exec first(wage) from empWages pivot by month, id;

         1    2    3    4    5    6    7    8    9    10
         ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
2017.11M|5000 5500 6000 6500 5000 5500 6000 6500 5000 5500
2017.12M|6000 6500 5000 5500 6000 6500 5000 5500 6000 6500
2018.01M|5000 5500 6000 6500 5000 5500 6000 6500 5000 5500
2018.02M|6000 6500 5000 5500 6000 6500 5000 5500 6000 6500
2018.03M|5000 5500 6000 6500 5000 5500 6000 6500 5000 5500
2018.04M|6000 6500 5000 5500 6000 6500 5000 5500 6000 6500
2018.05M|5000 5500 6000 6500 5000 5500 6000 6500 5000 5500
2018.06M|6000 6500 5000 5500 6000 6500 5000 5500 6000 6500
2018.07M|5000 5500 6000 6500 5000 5500 6000 6500 5000 5500
2018.08M|6000 6500 5000 5500 6000 6500 5000 5500 6000 6500
```

### 2.2 对面板数据(Panel Data)的友好支持

SQL的group by子句将数据分成多组，每组产生一个值，也就是一行。因此使用group by子句后，行数一般会大大减少。

在对面板数据进行分组后，每一组数据通常是时间序列数据，譬如按股票分组，每一个组内的数据是一个股票的价格序列。处理面板数据时，有时候希望保持每个组的数据行数，也就是为组内的每一行数据生成一个值。例如，根据一个股票的价格序列生成回报序列，或者根据价格序列生成一个移动平均价格序列。其它数据库系统（例如SQL Server，PostGreSQL），用窗口函数(window function)来解决这个问题。DolphinDB引入了context by子句来处理面板数据。context by与窗口函数相比，除了语法更简洁，设计更系统化（与group by和pivot by一起组成对分组数据处理的三个子句）以外，表达能力上也更强大，具体表现在下面三个方面：

- 不仅能与select配合在查询中使用，也可以与update配合更新数据。
- 绝大多数数据库系统在窗口函数中只能使用表中现有的字段分组。context by子句可以使用任何现有字段和计算字段。
- 窗口函数仅限于少数几个函数。context by不仅不限制使用的函数，而且可以使用任意表达式，譬如多个函数的组合。
- context by可以与having子句配合使用，以过滤每个组内部的行。

假定trades数据表记录了每个股票每天的日终价格，可以使用context by子句方便的计算每个股票每天的回报以及每天的排名。首先按股票代码进行分组，计算每个股票每天的回报。这里假设每个股票的数据是时间顺序排列的。

```
update trades set ret = ratios(price) - 1.0 context by symbol;
```

按日期进行分组，计算每天每个股票的回报降序排名：

```
select date, symbol,  ret, rank(ret, false) + 1 as rank from trades where isValid(ret) context by date;
```

选择每天回报排名前10的股票：

```
select date, symbol, ret from trades where isValid(ret) context by date having rank(ret, false) < 10;
```

下面我们以一个更为复杂的实际例子演示context by子句如何高效的解决面板数据问题。一篇论文 [101 Formulaic Alphas](https://arxiv.org/ftp/arxiv/papers/1601/1601.00991.pdf)介绍了华尔街的顶级量化对冲基金WorldQuant所使用的101个量化Alpha因子。某基金公司用C#来计算这些因子，其中代表性的98号因子既用到了纵向时间序列数据的多个指标的嵌套，又用到了横向截面数据的排序信息，实现使用了几百行代码。使用中国股市3000多个股票10年近9百万行的历史数据，计算98号Alpha因子耗时约30分钟。而改用DolphinDB实现，如下图所示只用了4行核心代码，耗时仅2秒钟，达到了接近三个数量级的性能提升。

```
def alpha98(stock){
	t = select code, valueDate, adv5, adv15, open, vwap from stock order by valueDate
	update t set rank_open = rank(open), rank_adv15 = rank(adv15) context by valueDate
	update t set decay7 = mavg(mcorr(vwap, msum(adv5, 26), 5), 1..7), decay8 = mavg(mrank(9 - mimin(mcorr(rank_open, rank_adv15, 21), 9), true, 7), 1..8) context by code
	return select code, valueDate, rank(decay7)-rank(decay8) as A98 from t context by valueDate 
}
```

### 2.3 对时间序列数据的友好支持

DolphinDB的数据库采用列式数据存储，计算的时候又采用向量化的编程，对时间序列数据天然友好。

- DolphinDB支持不同精度的时间类型。可以通过SQL语句方便的将高频数据转换成不同精度的低频数据，例如秒级、分钟级、小时级, 也可以通过`bar`函数和group by子句的配合使用，转换成任意时间间隔的数据。
- DolphinDB支持对时间序列数据的序列关系进行建模，包括领先（lead），滞后（lag），滑动窗口（sliding window），累积窗口（cumulative window）等。更重要的是在这类建模中用到的常用指标和函数，DolphinDB都做了优化，性能优于其它系统1~2个数量级。
- DolphinDB提供了专门为时间序列设计的高效而常用的表联结方式：asof join和window join。

我们以一个简单的例子来解释window join。譬如要统计一组人员在某些时间点前三个月的平均工资。我们可以简单的用window join（`wj`）来实现。window join函数的具体解释请参考[用户手册](https://www.dolphindb.cn/cn/help/SQLStatements/TableJoiners/windowjoin.html)

```
p = table(1 2 3 as id, 2018.06M 2018.07M 2018.07M as month)
s = table(1 2 1 2 1 2 as id, 2018.04M + 0 0 1 1 2 2 as month, 4500 5000 6000 5000 6000 4500 as wage)
select * from wj(p, s, -3:-1,<avg(wage)>,`id`month)

id month    avg_wage
-- -------- -----------
1  2018.06M 5250
2  2018.07M 4833.333333
3  2018.07M

```

上面的问题，在其它数据库系统中，可以使用equal join（id字段）和 non-equal join（month字段），以及group by子句来解决。但除了写法更为复杂外，与DolphinDB的window join相比，其它系统性能落后两个数量级以上。

window join在金融领分析领域有着广泛的应用。一个经典的应用就是将交易（trades）表和报价（quotes）表进行关联，计算交易成本。

以下为交易表（trades），不分区或者按日期和股票代码分区：

```
sym  date       time         price  qty
---- ---------- ------------ ------ ---
IBM  2018.06.01 10:01:01.005 143.19 100
MSFT 2018.06.01 10:01:04.006 107.94 200
```

以下为报价表（quotes），不分区或者按日期和股票代码分区：

```
sym  date       time         bid    ask    bidSize askSize
---- ---------- ------------ ------ ------ ------- -------
IBM  2018.06.01 10:01:01.006 143.18 143.21 400     200
MSFT 2018.06.01 10:01:04.010 107.92 107.97 800     100
```

使用asof join为每一个交易找到最近的一个报价，并利用报价的中间价作为交易成本的基准：

```
dateRange = 2018.05.01 : 2018.08.01
select sum(abs(price - (bid+ask)/2.0)*qty)/sum(price*qty) as cost from aj(trades, quotes, `date`sym`time) where date between dateRange group by sym;
```

使用window join为每一个交易找到前10毫秒的报价，计算平均中间价作为交易成本的基准：

```
select sum(abs(price - mid)*qty)/sum(price*qty) as cost from pwj(trades, quotes, -10:0, <avg((bid + ask)/2.0) as mid>,`date`sym`time) where date between dateRange group by sym;
```

### 2.4 SQL的其它扩展

为满足大数据分析的要求，DolphinDB对SQL还做了很多其他扩展。这儿我们例举一些常用功能。
- 用户自定义的函数无需编译、打包和部署，即可在本节点或分布式环境的SQL中使用此函数。
- 如5.4节所示，DolphinDB中的SQL与分布式计算框架紧密集成，实现库内计算（in-database analytics）变得更加便捷和高效。
- DolphinDB支持组合字段（composite column），可将复杂分析函数的多个返回值输出到数据表的一行。

如果要在SQL语句中使用组合字段，函数的输出结果必须是简单的键值对（key-value pair)或者数组。如果不是这两种类型，可以用自定义函数进行转换。组合字段的详细用法请参考[用户手册](https://www.dolphindb.cn/cn/help/SQLStatements/groupby.html)。

```
factor1=3.2 1.2 5.9 6.9 11.1 9.6 1.4 7.3 2.0 0.1 6.1 2.9 6.3 8.4 5.6
factor2=1.7 1.3 4.2 6.8 9.2 1.3 1.4 7.8 7.9 9.9 9.3 4.6 7.8 2.4 8.7
t=table(take(1 2 3, 15).sort() as id, 1..15 as y, factor1, factor2);
```

为每个id运行ols，y = alpha + beta1 * factor1 + beta2 * factor2, 输出参数alpha, beta1, beta2。

```
select ols(y, [factor1,factor2], true, 0) as `alpha`beta1`beta2 from t group by id;

id alpha     beta1     beta2
-- --------- --------- ---------
1  1.063991  -0.258685 0.732795
2  6.886877  -0.148325 0.303584
3  11.833867 0.272352  -0.065526
```

在输出参数的同时，输出R2。使用自定义函数包装输出结果。

```
def myols(y,x){
    r=ols(y,x,true,2)
    return r.Coefficient.beta join r.RegressionStat.statistics[0]
}
select myols(y,[factor1,factor2]) as `alpha`beta1`beta2`R2 from t group by id;

id alpha     beta1     beta2     R2
-- --------- --------- --------- --------
1  1.063991  -0.258685 0.732795  0.946056
2  6.886877  -0.148325 0.303584  0.992413
3  11.833867 0.272352  -0.065526 0.144837
```

## 3. 命令式编程(Imperative Programming)

DolphinDB与主流的脚本语言（Python和JavaScript等）和编译型强类型语言（C++，C和Java）一样，支持命令式编程，即一步一步告诉计算机先做什么再做什么。DolphinDB目前支持18种语句（详细参考[用户手册第五章](https://www.dolphindb.cn/cn/help/ProgrammingStatements/index.html)），包括最常用的赋值语句，分支语句if..else，以及循环语句for和do..while等。

DolphinDB支持对单变量和多变量进行赋值。

```
x = 1 2 3
y = 4 5
y += 2
x, y = y, x //swap the value of x and y
x, y =1 2 3, 4 5
```

DolphinDB目前支持的循环语句包括for语句和do..while语句。for语句的循环体可以包括数据对（pair）（左闭右开区间）、数组（vector）、矩阵（matrix）和表（table）。

1到100累加求和：

```
s = 0
for(x in 1:101) s += x
print s
```

数组中的元素求和：

```
s = 0;
for(x in 1 3 5 9 15) s += x
print s
```

打印矩阵每一列的均值：

```
m = matrix(1 2 3, 4 5 6, 7 8 9)
for(c in m) print c.avg()
```

计算数据表中每一个行两列之乘积：

```
t= table(["TV set", "Phone", "PC"] as productId, 1200 600 800 as price, 10 20 7 as qty)
for(row in t) print row.productId + ": " + row.price * row.qty
```

DolphinDB的分支语句if..else与其它语言一致。
```
if(condition){
    <true statements>
}
else{
     <false statements>
}
```

对处理海量数据时，不推荐利用控制语句（for语句，if..else语句）对数据逐行处理。这些控制语句一般用于上层模块的处理和调度，比较底层的数据处理模块建议使用向量编程，函数编程，SQL编程等方式来处理。

## 4. 函数化编程(Functional Programming)

DolphinDB支持函数式编程的大部分功能，包括：
- 纯函数（pure function）
- 自定义函数（user-defined function，或简称udf）
- lambda函数
- 高阶函数（higher order function）
- 部分应用（partial application）

详细请参考[用户手册第七章](https://www.dolphindb.cn/cn/help/Functionalprogramming/index.html)。

### 4.1 自定义函数和lambda函数

DolphinDB中可以创建自定义函数，函数可以有名称或者没有名称（通常是lambda函数）。创建的函数符合纯函数的要求，也就是说只有函数的输入参数可以影响函数的输出结果。DolphinDB与Python不同，函数体内只能引用函数参数和函数内的局部变量，不能使用函数体外定义的变量。从软件工程的角度看，这牺牲了一部分语法糖的灵活性，但对提高软件质量大有裨益。

```
def getWeekDays(dates){
    return dates[def(x):weekday(x) between 1:5]
}

getWeekDays(2018.07.01 2018.08.01 2018.09.01 2018.10.01)

[2018.08.01, 2018.10.01] 
```
上面的例子中，我们定义了一个函数`getWeekDays`，该函数接受一组日期，返回其在周一和周五之间的日期。函数的实现采用了向量的过滤功能，也就是接受一个布尔型单目函数用于数据的过滤。我们定义了一个lambda函数用于数据过滤。

### 4.2 高阶函数(Higher Order Function)

高阶函数是指可以接受另一个函数作为参数的函数。在DolphinDB中，高阶函数主要用作数据处理的模板函数，通常第一个参数是另外一个函数，用于具体的数据处理。譬如说，A对象有m个元素，B对象有n个元素，一种常见的处理模式是，A中的任意一个元素和B中的任意一个元素两两计算，最后产生一个m*n的矩阵。DolphinDB将这种数据处理模式抽象成一个高阶函数`cross`。DolphinDB提供了很多类似的高阶函数，包括`all`，`any`，`each`，`loop`，`eachLeft`，`eachRight`，`eachPre`，`eachPost`，`accumulate`，`reduce`，`groupby`，`contextby`，`pivot`，`cross`，`moving`，`rolling`等。

下面的一个例子我们使用三个高阶函数，只用三行代码，根据股票日内tick级别的交易数据，计算出每两只股票之间的相关性。

模拟生成10000000个数据点（股票代码，交易时间和价格）：

```
n=10000000
syms = rand(`FB`GOOG`MSFT`AMZN`IBM, n)
time = 09:30:00.000 + rand(21600000, n)
price = 500.0 + rand(500.0, n)
```

利用`pivot`函数生成股价透视矩阵，每列为一支股票，每行为一分钟：

```
priceMatrix = pivot(avg, price, time.minute(), syms)
```

`each`和`ratios`函数配合使用，对股价矩阵每列进行操作，将股价转为收益率：

```
retMatrix = each(ratios, priceMatrix) - 1
```

`cross`和`corr`函数配合使用，计算每两支股票收益率的相关性：

```
corrMatrix = cross(corr, retMatrix, retMatrix)
```

结果为：
```
     AMZN      FB        GOOG      IBM       MSFT
     --------- --------- --------- --------- ---------
AMZN|1         0.015181  -0.056245 0.005822  0.084104
FB  |0.015181  1         -0.028113 0.034159  -0.117279
GOOG|-0.056245 -0.028113 1         -0.039278 -0.025165
IBM |0.005822  0.034159  -0.039278 1         -0.049922
MSFT|0.084104  -0.117279 -0.025165 -0.049922 1
```

### 4.3 部分应用(Partial Application)

部分应用指当一个函数的一部分或全部参数给定后生成一个新的函数。在DolphinDB中，函数调用使用圆括号()，部分应用使用{}。3.2节中的例子用到的`ratios`函数的具体实现就是高阶函数`eachPre`的一个部分应用 eachPre{ratio}。

以下两行代码同构：

```
retMatrix = each(ratios, priceMatrix) - 1
retMatrix = each(eachPre{ratio}, priceMatrix) - 1
```

部分应用经常用于高阶函数。使用高阶函数时，通常对某些参数有特定要求，通过部分应用，可以确保所有参数符合要求。例如，计算一个向量a与一个矩阵m中的每一列的相关性，可以将函数`corr`与高阶函数`each`配合使用。但是若直接将向量与矩阵在`each`中列为`corr`的参数，系统将会试图计算向量的某个元素与矩阵的某个列的相关性，导致产生错误。这时，可利用部分应用把函数`corr`与向量a组成一个新的函数`corr{a}`，再与高阶函数`each`配合使用于矩阵的每一列，如下例所示。我们也可以利用for语句来解决这个问题，但代码冗长且增加耗时。

```
a = 12 14 18
m = matrix(5 6 7, 1 3 2, 8 7 11)
```

使用each和部分应用计算向量a与矩阵中的每一列的相关性：

```
each(corr{a}, m)
```

使用for语句解决上述问题：

```
cols = m.columns()
c = array(DOUBLE, cols)
for(i in 0:cols)
    c[i] = corr(a, m[i])
```

部分应用的另一个妙用是使函数保持状态。通常我们希望函数是无状态的，即函数的输出结果完全是由输入参数决定的。但有时候我们希望函数是有“状态”的。譬如说，在流计算中，用户通常需要给定一个消息处理函数（message handler），接受一条新的信息后返回一个结果。如果我们希望消息处理函数返回的是迄今为止所有接收到的数据的平均数，可以通过部分应用来解决。

```
def cumulativeAverage(mutable stat, newNum){
    stat[0] = (stat[0] * stat[1] + newNum)/(stat[1] + 1)
    stat[1] += 1
    return stat[0]
}

msgHandler = cumulativeAverage{0.0 0.0}
each(msgHandler, 1 2 3 4 5)

[1,1.5,2,2.5,3]
```

## 5. 远程过程调用编程(RPC Programming)

远程过程调用（Remote Procedure Call）是分布式系统最常用的基础设施之一。DolphinDB的分布式文件系统实现，分布式数据库实现，分布式计算框架实现都采用了`DolphinDB自己设计`的RPC系统。DolphinDB的脚本语言通过RPC可以在远程机器上执行代码。DolphinDB在使用RPC时有以下特点：
- 不仅可以执行在远程机器上已经注册的函数，也可以将本地自定义的函数序列化到远程节点执行。在远程机器运行代码时的权限等同于当前登录用户在本地的权限。
- 函数的参数既可以是常规的scalar，vector，matrix，set，dictionary和table，也可以是函数包括自定义的函数。
- 既可以使用两个节点之间的独占连接，也可以使用集群数据节点之间的共享连接。

### 5.1 使用remoteRun执行远程函数

DolphinDB使用`xdb`创建一个到远程节点的连接。远程节点可以是任何运行DolphinDB的节点，不必属于当前集群的一部分。创建连接之后可以在远程节点上执行远程节点上注册的函数或本地自定义的函数。

```
h = xdb("localhost", 8081);
```
在远程节点上执行一段脚本：

```
remoteRun(h, "sum(1 3 5 7)");
16
```
上述远程调用也可以简写成：

```
h("sum(1 3 5 7)");
16
```

在远程节点上执行一个在远程节点注册的函数：

```
h("sum", 1 3 5 7);
16
```

在远程系节点上执行本地的自定义函数：

```
def mysum(x) : reduce(+, x)
h(mysum, 1 3 5 7);
16
```

在远程节点（localhost:8081）上创建一个共享表sales：

```
h("share table(2018.07.02 2018.07.02 2018.07.03 as date, 1 2 3 as qty, 10 15 7 as price) as sales");
```

如果本地的自定义函数有依赖，所依赖的自定义函数会自动序列化到远程节点：
```
defg salesSum(tableName, d): select mysum(price*qty) from objByName(tableName) where date=d
h(salesSum, "sales", 2018.07.02);
40
```

### 5.2 使用rpc执行远程函数

DolphinDB使用远程过程调用功能的另一个途径是`rpc`函数。`rpc`函数接受远程节点的名称，需要执行的函数定义以及需要的参数。`rpc`只能在同一个集群内的控制节点及数据节点之间使用，但是不需要创建一个新的连接，而是复用已经存在的网络连接。这样做的好处是可以节约网络资源和免去创建新连接带来的延迟。当节点的用户很多时，这一点非常有意义。`rpc`函数只能在远程节点执行一个函数。如果要运行脚本，请把脚本封装在一个自定义函数内。
下面的例子必须在一个DolphinDB集群内使用。nodeB是远程节点的别名，nodeB上已经有共享表sales。

```
rpc("nodeB", salesSum, "sales",2018.07.02);
40
```

在使用`rpc`时，为增加代码的可读性，建议使用部分应用，将函数参数和函数定义写在一起，形成一个新的零参数的函数定义。

```
rpc("nodeB", salesSum{"sales", 2018.07.02});
40
```
master是控制节点的别名。DolphinDB只能在控制节点上创建用户：

```
rpc("master", createUser{"jerry", "123456"});
```

`rpc`函数需要的参数也可以是另外一个函数包括内置函数和自定义函数：

```
rpc("nodeB", reduce{+, 1 2 3 4 5});
15
```

### 5.3 使用其它函数间接执行远程函数

`remoteRun`和`rpc`都可以在一个远程节点上执行用户在本地自定义的函数。这是DolphinDB的RPC子系统与其它RPC系统最大的不同之处。在其它系统中，通常RPC的客户端只能被动调用远程节点已经暴露的注册函数。在大数据分析领域，数据科学家根据新的研发项目经常会提出新的接口需求。如果等待IT部门发布新的API接口，通常需要很长的周期，这会严重影响研发的效率和周期。如果要在远程节点执行自定义的函数，自定义的函数目前必须使用DolphinDB的脚本来开发。另外，对数据的安全性也提出了更高的要求，必须仔细规划和设置用户的访问权限。如果限制用户只能使用注册的函数，用户的访问权限管理可以十分的简单，只要拒绝外部用户访问一切数据，授权外部用户访问注册的视图函数就可以了。

除了直接使用`remoteRun`和`rpc`函数外，DolphinDB也提供了很多函数间接的使用远程过程调用。例如，在分布式数据库的线性回归就用到了`rpc`与`olsEx`。另外，`pnodeRun`用于在集群的多个节点上并行运行同一个函数，并将返回的结果合并。这在集群的管理中十分有用。

每个数据节点返回最近的10个正在运行或已经完成的批处理作业：

```
pnodeRun(getRecentJobs{10});
```

返回节点nodeA和nodeB的最近10个SQL query：

```
pnodeRun(getCompletedQueries{10}, `nodeA`nodeB);
```

清除所有数据节点上的缓存：

```
pnodeRun(clearAllCache);
```

### 5.4 分布式计算

`mr`用于开发基于MapReduce的分布式计算；`imr`用于开发基于迭代的MapReduce的分布式计算。用户只需要指定分布式数据源和核心函数，譬如map函数，reduce函数，final函数等。下面我们演示使用分布式数据计算中位数和线性回归的例子。

```
n=10000000
x1 = pow(rand(1.0,n), 2)
x2 = norm(3.0, 1.0, n)
y = 0.5 + 3 * x1 - 0.5*x2 + norm(0.0, 1.0, n)
t=table(rand(10, n) as id, y, x1, x2)

login(`admin,"123456")
db = database("dfs://testdb", VALUE, 0..9)
db.createPartitionedTable(t, "sample", "id").append!(t)
```

利用自定义的map函数`myOLSMap`，内置的reduce函数（+），自定义的final函数`myOLSFinal`，以及内置的map-reduce框架函数`mr`，构建一个在分布式数据源上运行线性回归的函数`myOLSEx`。

```
def myOLSMap(table, yColName, xColNames){
    x = matrix(take(1.0, table.rows()), table[xColNames])
    xt = x.transpose();
    return xt.dot(x), xt.dot(table[yColName])
}

def myOLSFinal(result){
    xtx = result[0]
    xty = result[1]
    return xtx.inv().dot(xty)[0]
}

def myOLSEx(ds, yColName, xColNames){
  return mr(ds, myOLSMap{, yColName, xColNames}, +, myOLSFinal)
}
```

使用用户自定义的分布式算法和分布式数据源计算线性回归系数：

```
sample = loadTable("dfs://testdb", "sample")
myOLSEx(sqlDS(<select * from sample>), `y, `x1`x2);
[0.4991, 3.0001, -0.4996]
```

使用内置的函数ols和未分的数据计算线性回归的系数，得到相同的结果：

```
ols(y, [x1,x2],true);
[0.4991, 3.0001, -0.4996]
```
下面这个例子中，我们构造一个算法，在分布式数据源上计算一组数据的近似中位数。算法的基本原理是利用`bucketCount`函数，在每一个节点上分别计算一组内的数据个数，然后把各个节点上的数据累加。这样我们可以找到中位数应该落在哪个区间内。如果这个区间不够小，进一步细分这个区间，直到小于给定的精度要求。中位数的算法需要多次迭代，我们因此使用了迭代计算框架`imr`。

```
def medMap(data, range, colName): bucketCount(data[colName], double(range), 1024, true)

def medFinal(range, result){
    x= result.cumsum()
    index = x.asof(x[1025]/2.0)
    ranges = range[1] - range[0]
    if(index == -1)
        return (range[0] - ranges*32):range[1]
    else if(index == 1024)
        return range[0]:(range[1] + ranges*32)
    else{
        interval = ranges / 1024.0
        startValue = range[0] + (index - 1) * interval
        return startValue : (startValue + interval)
    }
}

def medEx(ds, colName, range, precision){
    termFunc = def(prev, cur): cur[1] - cur[0] <= precision
    return imr(ds, range, medMap{,,colName}, +, medFinal, termFunc).avg()
}
```

使用以上近似中位数算法，计算分布式数据的中位数：

```
sample = loadTable("dfs://testdb", "sample")
medEx(sqlDS(<select y from sample>), `y, 0.0 : 1.0, 0.001);
-0.052973
```

使用内置的med函数计算未分区的数据的中位数：

```
med(y);
-0.052947
```

## 6. 元编程(Metaprogramming)

元编程指使用程序代码来创建可以动态运行的程序代码。元编程的目的一般是延迟执行代码或动态创建代码。

DolphinDB支持使用元编程来动态创建表达式，譬如函数调用的表达式，SQL查询表达式。很多业务细节无法在编码阶段确定。譬如说客户定制报表，只有运行时，客户选择了表格，字段和字段格式，才可以确定一个完整的SQL查询表达式。

延迟执行代码一般分为这几种情况：
- 提供一个回调函数
- 延迟执行为整体优化创造条件
- 问题描述在程序编码阶段完成，但是问题实现在程序运行阶段完成

DolphinDB实现元编程的途径有两个，一是使用一对尖括号<>来表示需要延后执行的动态代码，二是使用函数来创建各种表达式。常用的用于元编程的函数包括`objByName`, `sqlCol`, `sqlColAlias`, `sql`, `expr`, `eval`, `partial`, `makeCall`。

使用<>来生成延后执行的动态表达式：

```
a = <1 + 2 * 3>
a.typestr();
CODE

a.eval();
7
```

使用函数来生成延后执行的动态表达式：

```
a = expr(1, +, 2, *, 3)
a.typestr();
CODE

a.eval();
7
```

可使用元编程来定制报表。用户的输入包括数据表，字段名称和字段相应的格式字符串。下例中，根据输入的数据表，字段名称和格式，以及过滤条件，动态生成SQL表达式并执行。

```
def generateReport(tbl, colNames, colFormat, filter){
	colCount = colNames.size()
	colDefs = array(ANY, colCount)
	for(i in 0:colCount){
		if(colFormat[i] == "") 
			colDefs[i] = sqlCol(colNames[i])
		else
			colDefs[i] = sqlCol(colNames[i], format{,colFormat[i]})
	}
	return sql(colDefs, tbl, filter).eval()
}
```

模拟生成一个100行的数据表：
```
t = table(1..100 as id, (1..100 + 2018.01.01) as date, rand(100.0, 100) as price, rand(10000, 100) as qty);
```

输入过滤条件，字段和格式，定制报表。过滤条件使用了元编程。
```
generateReport(t, ["id","date","price","qty"], ["000","MM/dd/yyyy", "00.00", "#,###"], < id<5 or id>95 >);

id  date       price qty
--- ---------- ----- -----
001 01/02/2018 50.27 2,886
002 01/03/2018 30.85 1,331
003 01/04/2018 17.89 18
004 01/05/2018 51.00 6,439
096 04/07/2018 57.73 8,339
097 04/08/2018 47.16 2,425
098 04/09/2018 27.90 4,621
099 04/10/2018 31.55 7,644
100 04/11/2018 46.63 8,383
```

DolphinDB的一些内置函数的参数需要使用元编程。`窗口连接（window join）`中，需要为右表的窗口数据集指定一个或多个聚合函数以及这些函数运行时需要的参数。由于问题的描述和执行在两个不同的阶段，我们采用元编程来实现延后执行。

```
t = table(take(`ibm, 3) as sym, 10:01:01 10:01:04 10:01:07 as time, 100 101 105 as price)
q = table(take(`ibm, 8) as sym, 10:01:01+ 0..7 as time, 101 103 103 104 104 107 108 107 as ask, 98 99 102 103 103 104 106 106 as bid)
wj(t, q, -2 : 1, < [max(ask), min(bid), avg((bid+ask)*0.5) as avg_mid]>, `time);

sym time     price max_ask min_bid avg_mid
--- -------- ----- ------- ------- -------
ibm 10:01:01 100   103     98      100.25
ibm 10:01:04 101   104     99      102.625
ibm 10:01:07 105   108     103     105.625
```

DolphinDB中另一个使用元编程的内置功能是更新内存分区表。当然内存分区表的更新，删除，排序等功能也可以通过SQL语句来完成。

创建一个以日期为分区的内存分区数据库，并模拟生成trades表：

```
db = database("", VALUE, 2018.01.02 2018.01.03)
date = 2018.01.02 2018.01.02 2018.01.02 2018.01.03 2018.01.03 2018.01.03
t = table(`IBM`MSFT`GOOG`FB`IBM`MSFT as sym, date, 101 103 103 104 104 107 as price, 0 99 102 103 103 104 as qty)
trades = db.createPartitionedTable(t, "trades", "date").append!(t);
```

删除qty为0的记录，并在每个分区中按交易量进行升序排序：

```
trades.erase!(<qty=0>).sortBy!(<price*qty>);
```

增加一个新的字段logPrice：

```
trades[`logPrice]=<log(price)>;
```

更新股票IBM的交易数量：

```
trades[`qty, <sym=`IBM>]=<qty+100>;
```

## 7. 小结

DolphinDB是一门为数据分析而生的编程语言。DolphinDB支持向量化计算和分布式计算，具有极快的运行速度。与其它数据分析语言Matlab，SAS，pandas等不同，DolphinDB与分布式数据库和分布式计算紧密集成，天生具备处理海量数据的能力。DolphinDB支持SQL编程，函数化编程和元编程，语言简洁灵活，表达能力强，大大提高了数据科学家的开发效率。
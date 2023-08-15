# DolphinDB文本数据加载教程

DolphinDB提供以下4个函数，将文本数据导入内存或数据库：

- [`loadText`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/l/loadText.html): 将文本文件导入为内存表。
- [`ploadText`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/p/ploadText.html): 将文本文件并行导入为分区内存表。与`loadText`函数相比，速度更快。
- [`loadTextEx`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/l/loadTextEx.html): 将文本文件导入数据库中，包括分布式数据库或内存数据库。
- [`textChunkDS`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/t/textChunkDS.html)：将文本文件划分为多个小数据源，再通过[`mr`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/m/mr.html)函数进行灵活的数据处理。

DolphinDB的文本数据导入不仅灵活，而且速度非常快。DolphinDB与Clickhouse, MemSQL, Druid, Pandas等业界流行的系统相比，单线程导入的速度优势，最多可达一个数量级；多线程并行导入的情况下，速度优势更加明显。

本教程介绍文本数据导入时的常见问题，相应的解决方案以及注意事项。

- [DolphinDB文本数据加载教程](#dolphindb文本数据加载教程)
  - [1. 自动识别数据格式](#1-自动识别数据格式)
  - [2. 指定数据导入格式](#2-指定数据导入格式)
    - [2.1 提取文本文件的schema](#21-提取文本文件的schema)
    - [2.2 指定字段名称和类型](#22-指定字段名称和类型)
    - [2.3 指定日期和时间类型的格式](#23-指定日期和时间类型的格式)
    - [2.4 导入指定列](#24-导入指定列)
    - [2.5 跳过文本数据的前若干行](#25-跳过文本数据的前若干行)
  - [3. 并行导入数据](#3-并行导入数据)
    - [3.1 单个文件多线程载入内存](#31-单个文件多线程载入内存)
    - [3.2 多文件并行导入](#32-多文件并行导入)
  - [4. 导入数据库前的预处理](#4-导入数据库前的预处理)
    - [4.1 指定日期和时间数据的数据类型](#41-指定日期和时间数据的数据类型)
      - [4.1.1 将数值类型表示的日期和时间转化为指定类型](#411-将数值类型表示的日期和时间转化为指定类型)
      - [4.1.2 日期或时间数据类型之间转换](#412-日期或时间数据类型之间转换)
    - [4.2 填充空值](#42-填充空值)
  - [5. 导入数组向量类型的数据](#5-导入数组向量类型的数据)
    - [5.1 直接导入符合条件的文本文件 （2.00.4及以上版本）](#51-直接导入符合条件的文本文件-2004及以上版本)
    - [5.2 文本文件导入内存后，将多列合并成一列数组向量，再导入分布式数据库](#52-文本文件导入内存后将多列合并成一列数组向量再导入分布式数据库)
    - [5.3 使用 loadTextEx 函数时指定 transform 参数，将文本文件导入分布式数据库](#53-使用-loadtextex-函数时指定-transform-参数将文本文件导入分布式数据库)
  - [6. 使用Map-Reduce自定义数据导入](#6-使用map-reduce自定义数据导入)
    - [6.1 将文件中的股票和期货数据存储到两个不同的数据表](#61-将文件中的股票和期货数据存储到两个不同的数据表)
    - [6.2 快速加载大文件首尾部分数据](#62-快速加载大文件首尾部分数据)
  - [7. 其它注意事项](#7-其它注意事项)
    - [7.1 不同编码的数据的处理](#71-不同编码的数据的处理)
    - [7.2 数值类型的解析](#72-数值类型的解析)
    - [7.3 自动去除双引号](#73-自动去除双引号)
  - [附录](#附录)

## 1. 自动识别数据格式

大多数其它系统中，导入文本数据时，需要由用户指定数据的格式。DolphinDB在导入数据时，能够自动识别数据格式，为用户提供了方便。

自动识别数据格式包括两部分：字段名称识别和数据类型识别。如果文件的第一行没有任何一列以数字开头，那么系统认为第一行是文件头，包含了字段名称。DolphinDB会抽取少量部分数据作为样本，并自动推断各列的数据类型。因为是基于部分数据，某些列的数据类型可能识别错误。但是对于大多数文本文件，无须手动指定各列的字段名称和数据类型，就能正确地导入到DolphinDB中。

> 请注意：1.20.0之前的版本不支持导入INT128, UUID和IPADDR这三种数据类型。如果在csv文件中包含这三种数据类型，请确保所用版本不低于1.20.0。

[`loadText`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/l/loadText.html)函数用于将数据导入DolphinDB内存表。下例调用`loadText`函数导入数据，并查看生成的数据表的结构。例子中涉及到的数据文件请参考[附录](#附录)。

```
dataFilePath="/home/data/candle_201801.csv"
tmpTB=loadText(filename=dataFilePath);
```

查看数据表前5行数据：

```
select top 5 * from tmpTB;

symbol exchange cycle tradingDay date       time     open  high  low   close volume  turnover   unixTime
------ -------- ----- ---------- ---------- -------- ----- ----- ----- ----- ------- ---------- -------------
000001 SZSE     1     2018.01.02 2018.01.02 93100000 13.35 13.39 13.35 13.38 2003635 2.678558E7 1514856660000
000001 SZSE     1     2018.01.02 2018.01.02 93200000 13.37 13.38 13.33 13.33 867181  1.158757E7 1514856720000
000001 SZSE     1     2018.01.02 2018.01.02 93300000 13.32 13.35 13.32 13.35 903894  1.204971E7 1514856780000
000001 SZSE     1     2018.01.02 2018.01.02 93400000 13.35 13.38 13.35 13.35 1012000 1.352286E7 1514856840000
000001 SZSE     1     2018.01.02 2018.01.02 93500000 13.35 13.37 13.35 13.37 1601939 2.140652E7 1514856900000
```

调用[`schema`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/s/schema.html)函数查看表结构（字段名称、数据类型等信息）：

```
tmpTB.schema().colDefs;

name       typeString typeInt comment
---------- ---------- ------- -------
symbol     SYMBOL     17
exchange   SYMBOL     17
cycle      INT        4
tradingDay DATE       6
date       DATE       6
time       INT        4
open       DOUBLE     16
high       DOUBLE     16
low        DOUBLE     16
close      DOUBLE     16
volume     INT        4
turnover   DOUBLE     16
unixTime   LONG       5
```

## 2. 指定数据导入格式

本教程讲述的4个数据加载函数中，均可用schema参数指定一个表，内含各字段的名称、类型、格式、需要导入的列等信息。该表可包含以下4列：

列名 | 含义
--- | ---
name | 字符串，表示列名
type | 字符串，表示每列的数据类型
format | 字符串，表示日期或时间列的格式
col | 整型，表示要加载的列的下标。该列的值必须是升序。

其中，name和type这两列是必需的，而且必须是前两列。format和col这两列是可选的，且没有先后顺序的要求。

例如，我们可以使用以下的数据表作为schema参数：

name|type
---|---
timestamp|SECOND
ID|INT
qty|INT
price|DOUBLE

### 2.1 提取文本文件的schema

[`extractTextSchema`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/e/extractTextSchema.html)函数用于获取文本文件的schema，包括字段名称和数据类型等信息。

例如，使用`extractTextSchema`函数得到本教程中示例文件的表结构：

```
dataFilePath="/home/data/candle_201801.csv"
schemaTB=extractTextSchema(dataFilePath)
schemaTB;

name       type
---------- ------
symbol     SYMBOL
exchange   SYMBOL
cycle      INT
tradingDay DATE
date       DATE
time       INT
open       DOUBLE
high       DOUBLE
low        DOUBLE
close      DOUBLE
volume     INT
turnover   DOUBLE
unixTime   LONG
```

### 2.2 指定字段名称和类型

当系统自动识别的字段名称或者数据类型不符合预期时，可以通过修改`extractTextSchema`生成的schema表或直接创建schema表为文本文件中的每列指定字段名称和数据类型。

例如，若导入数据的volume列被自动识别为INT类型，而需要的volume类型是LONG类型，就需要修改schema表，指定volumn列类型为LONG。
```
dataFilePath="/home/data/candle_201801.csv"
schemaTB=extractTextSchema(dataFilePath)
update schemaTB set type="LONG" where name="volume";
```

使用`loadText`函数导入文本文件，将数据按照schemaTB所规定的字段数据类型导入到数据库中。
```
tmpTB=loadText(filename=dataFilePath,schema=schemaTB);
```

上例介绍了修改数据类型的情况，若要修改表中的字段名称，也可以通过同样的方法实现。

> 请注意，若对日期和时间相关数据类型的自动解析不符合预期，需要通过本教程[第2.3小节](#23-指定日期和时间类型的格式)的方式解决。

### 2.3 指定日期和时间类型的格式

对于日期列或时间列的数据，如果自动识别的数据类型不符合预期，不仅需要在schema的type列指定数据类型，还需要在format列中指定格式（用字符串表示），如"MM/dd/yyyy"。如何表示日期和时间格式请参考[日期和时间的调整及格式](https://www.dolphindb.cn/cn/help/DataManipulation/TemporalObjects/ParsingandFormatofTemporalVariables.html)。

下面结合例子具体说明对日期和时间列指定数据类型的方法。

在DolphinDB中执行以下脚本，生成本例所需的数据文件。

```
dataFilePath="/home/data/timeData.csv"
t=table(["20190623 14:54:57","20190623 15:54:23","20190623 16:30:25"] as time,`AAPL`MS`IBM as sym,2200 5400 8670 as qty,54.78 59.64 65.23 as price)
saveText(t,dataFilePath);
```

加载数据前，使用`extractTextSchema`函数获取该数据文件的schema:

```
schemaTB=extractTextSchema(dataFilePath)
schemaTB;

name  type
----- ------
time  SECOND
sym   SYMBOL
qty   INT
price DOUBLE
```

显然，系统识别time列的数据类型不符合预期。如果直接加载该文件，time列的数据将为空。为了能够正确加载该文件time列的数据，需要指定time列的数据类型为DATETIME，并且指定该列的格式为"yyyyMMdd HH:mm:ss"。

```
update schemaTB set type="DATETIME" where name="time"
schemaTB[`format]=["yyyyMMdd HH:mm:ss",,,];
```

导入数据并查看，数据显示正确：
```
tmpTB=loadText(dataFilePath,,schemaTB)
tmpTB;

time                sym  qty  price
------------------- ---- ---- -----
2019.06.23T14:54:57 AAPL 2200 54.78
2019.06.23T15:54:23 MS   5400 59.64
2019.06.23T16:30:25 IBM  8670 65.23
```

### 2.4 导入指定列

在导入数据时，可以通过schema参数指定只导入文本文件中的某几列。

下例中，只需加载文本文件中symbol, date, open, high, close, volume, turnover这7列。

首先，调用`extractTextSchema`函数得到目标文本文件的表结构。

```
dataFilePath="/home/data/candle_201801.csv"
schemaTB=extractTextSchema(dataFilePath);
```

使用`rowNo`函数为各列生成列号，赋值给schema表中的col列，然后修改schema表，仅保留表示需要导入的字段的行。
```
update schemaTB set col = rowNo(name)
schemaTB=select * from schemaTB where name in `symbol`date`open`high`close`volume`turnover;
```

>请注意：
>1. 列号从0开始。上例中第一列symbol列对应的列号是0。  
>2. 导入数据时不能改变各列的先后顺序。如果需要调整列的顺序，可以将数据文件加载后，再使用[`reorderColumns!`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/r/reorderColumns.html)函数。

最后，使用`loadText`函数，并配置schema参数，导入文本文件中指定的列。

```
tmpTB=loadText(filename=dataFilePath,schema=schemaTB);
```

查看表中前5行，只导入了所需的列：

```
select top 5 * from tmpTB

symbol date       open   high  close volume turnover
------ ---------- ------ ----- ----- ------ ----------
000001 2018.01.02 9.31E7 13.35 13.35 13     2.003635E6
000001 2018.01.02 9.32E7 13.37 13.33 13     867181
000001 2018.01.02 9.33E7 13.32 13.32 13     903894
000001 2018.01.02 9.34E7 13.35 13.35 13     1.012E6
000001 2018.01.02 9.35E7 13.35 13.35 13     1.601939E6
```

### 2.5 跳过文本数据的前若干行

在数据导入时，若需跳过文件前n行（可能为文件说明），可指定skipRows参数为n。由于描述文件的说明通常不会非常冗长，因此这个参数的取值最大为1024。本教程讲述的4个数据加载函数均支持skipRows参数。

下例中，通过`loadText`函数导入数据文件，并且查看该文件导入以后表的总行数，以及前5行的内容。

```
dataFilePath="/home/data/candle_201801.csv"
tmpTB=loadText(filename=dataFilePath)
select count(*) from tmpTB;

count
-----
5040

select top 5 * from tmpTB;

symbol exchange cycle tradingDay date       time     open  high  low   close volume  turnover   unixTime
------ -------- ----- ---------- ---------- -------- ----- ----- ----- ----- ------- ---------- -------------
000001 SZSE     1     2018.01.02 2018.01.02 93100000 13.35 13.39 13.35 13.38 2003635 2.678558E7 1514856660000
000001 SZSE     1     2018.01.02 2018.01.02 93200000 13.37 13.38 13.33 13.33 867181  1.158757E7 1514856720000
000001 SZSE     1     2018.01.02 2018.01.02 93300000 13.32 13.35 13.32 13.35 903894  1.204971E7 1514856780000
000001 SZSE     1     2018.01.02 2018.01.02 93400000 13.35 13.38 13.35 13.35 1012000 1.352286E7 1514856840000
000001 SZSE     1     2018.01.02 2018.01.02 93500000 13.35 13.37 13.35 13.37 1601939 2.140652E7 1514856900000
```

指定skipRows参数取值为1000，跳过文本文件的前1000行导入文件：

```
tmpTB=loadText(filename=dataFilePath,skipRows=1000)
select count(*) from tmpTB;

count
-----
4041

select top 5 * from tmpTB;

col0   col1 col2 col3       col4       col5      col6  col7  col8  col9  col10  col11      col12
------ ---- ---- ---------- ---------- --------- ----- ----- ----- ----- ------ ---------- -------------
000001 SZSE 1    2018.01.08 2018.01.08 101000000 13.13 13.14 13.12 13.14 646912 8.48962E6  1515377400000
000001 SZSE 1    2018.01.08 2018.01.08 101100000 13.13 13.14 13.13 13.14 453647 5.958462E6 1515377460000
000001 SZSE 1    2018.01.08 2018.01.08 101200000 13.13 13.14 13.12 13.13 700853 9.200605E6 1515377520000
000001 SZSE 1    2018.01.08 2018.01.08 101300000 13.13 13.14 13.12 13.12 738920 9.697166E6 1515377580000
000001 SZSE 1    2018.01.08 2018.01.08 101400000 13.13 13.14 13.12 13.13 469800 6.168286E6 1515377640000
```

> 请注意：如上例所示，在跳过前n行进行导入时，若数据文件的第一行是列名，该行会作为第一行被略过。

在上面的例子中，文本文件指定skipRows参数导入以后，由于表示列名的第一行被跳过，列名变成了默认列名：col0, col1, col2, 等等。若需要保留列名而又指定跳过前n行，可先通过`extractTextSchema`函数得到文本文件的schema，在导入时指定schema参数：

```
schema=extractTextSchema(dataFilePath)
tmpTB=loadText(filename=dataFilePath,schema=schema,skipRows=1000)
select count(*) from tmpTB;

count
-----
4041

select top 5 * from tmpTB;

symbol exchange cycle tradingDay date       time      open  high  low   close volume turnover   unixTime
------ -------- ----- ---------- ---------- --------- ----- ----- ----- ----- ------ ---------- -------------
000001 SZSE     1     2018.01.08 2018.01.08 101000000 13.13 13.14 13.12 13.14 646912 8.48962E6  1515377400000
000001 SZSE     1     2018.01.08 2018.01.08 101100000 13.13 13.14 13.13 13.14 453647 5.958462E6 1515377460000
000001 SZSE     1     2018.01.08 2018.01.08 101200000 13.13 13.14 13.12 13.13 700853 9.200605E6 1515377520000
000001 SZSE     1     2018.01.08 2018.01.08 101300000 13.13 13.14 13.12 13.12 738920 9.697166E6 1515377580000
000001 SZSE     1     2018.01.08 2018.01.08 101400000 13.13 13.14 13.12 13.13 469800 6.168286E6 1515377640000
```

## 3. 并行导入数据

### 3.1 单个文件多线程载入内存

[`ploadText`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/p/ploadText.html)函数可将一个文本文件以多线程的方式载入内存。该函数与[`loadText`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/l/loadText.html)函数的语法是一致的，区别在于，`ploadText`函数可以快速载入大型文件（至少16MB），并且生成内存分区表。它充分利用了多核CPU来并行载入文件，并行程度取决于服务器本身CPU核数量和节点的workerNum配置。

下面比较`loadText`函数与`ploadText`函数导入同一个文件的性能。

首先通过脚本生成一个4GB左右的文本文件：

```txt
filePath="/home/data/testFile.csv"
appendRows=100000000
t=table(rand(100,appendRows) as int,take(string('A'..'Z'),appendRows) as symbol,take(2010.01.01..2018.12.30,appendRows) as date,rand(float(100),appendRows) as float,00:00:00.000 + rand(86400000,appendRows) as time)
t.saveText(filePath);
```

分别通过`loadText`和`ploadText`来载入文件。本例所用节点是6核12超线程的CPU。

```txt
timer loadText(filePath);
Time elapsed: 12629.492 ms

timer ploadText(filePath);
Time elapsed: 2669.702 ms
```

结果显示在此配置下，`ploadText`的性能是`loadText`的4.5倍左右。

### 3.2 多文件并行导入

在大数据应用领域，数据导入往往不只是一个或两个文件的导入，而是数十个甚至数百个大型文件的批量导入。为了达到更好的导入性能，建议尽量以并行方式导入批量的数据文件。

[`loadTextEx`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/l/loadTextEx.html)函数可将文本文件导入指定的数据库中，包括分布式数据库或内存数据库。由于DolphinDB的分区表支持并发读写，因此可以支持多线程导入数据。

使用`loadTextEx`将文本数据导入到分布式数据库，具体实现为将数据先导入到内存，再由内存写入到数据库，这两个步骤由同一个函数完成，以保证高效率。

下例展示如何将磁盘上的多个文件批量写入到DolphinDB分区表中。首先，在DolphinDB中执行以下脚本，生成100个文件，共约778MB，包括1千万条记录。

```
n=100000
dataFilePath="/home/data/multi/multiImport_"+string(1..100)+".csv"
for (i in 0..99){
    trades=table(sort(take(100*i+1..100,n)) as id,rand(`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S,n) as sym,take(2000.01.01..2000.06.30,n) as date,10.0+rand(2.0,n) as price1,100.0+rand(20.0,n) as price2,1000.0+rand(200.0,n) as price3,10000.0+rand(2000.0,n) as price4,10000.0+rand(3000.0,n) as price5)
    trades.saveText(dataFilePath[i])
};
```

创建数据库和表：

```
login(`admin,`123456)
dbPath="dfs://DolphinDBdatabase"
db=database(dbPath,VALUE,1..10000)
tb=db.createPartitionedTable(trades,`tb,`id);
```

DolphinDB的[`cut`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/c/cut.html)函数可将一个向量中的元素分组。下面调用`cut`函数将待导入的文件路径进行分组，再调用[`submitJob`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/s/submitJob.html)函数，为每个线程分配写入任务，批量导入数据。

```
def writeData(db,file){
   loop(loadTextEx{db,`tb,`id,},file)
}
parallelLevel=10
for(x in dataFilePath.cut(100/parallelLevel)){
    submitJob("loadData"+parallelLevel,"loadData",writeData{db,x})
};
```

通过[`getRecentJobs`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getRecentJobs.html)函数可以取得当前本地节点上最近n个批处理作业的状态。使用select语句计算并行导入批量文件所需时间，得到在6核12超线程的CPU上耗时约1.59秒。

```
select max(endTime) - min(startTime) from getRecentJobs() where jobId like ("loadData"+string(parallelLevel)+"%");

max_endTime_sub
---------------
1590
```

执行以下脚本，将100个文件单线程顺序导入数据库，记录所需时间，耗时约8.65秒。

```
timer writeData(db, dataFilePath);
Time elapsed: 8647.645 ms
```

结果显示在此配置下，并行开启10个线程导入速度是单线程导入的5.5倍左右。

查看数据表中的记录条数：

```
select count(*) from loadTable("dfs://DolphinDBdatabase", `tb);

count
------
10000000
```

## 4. 导入数据库前的预处理

在将数据导入数据库之前，若需要对数据进行预处理，例如转换日期和时间数据类型，填充空值等，可以在调用[`loadTextEx`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/l/loadTextEx.html)函数时指定transform参数。tansform参数接受一个函数作为参数，并且要求该函数只能接受一个参数。函数的输入是一个未分区的内存表，输出也是一个未分区的内存表。需要注意的是，只有`loadTextEx`函数提供transform参数。

### 4.1 指定日期和时间数据的数据类型

#### 4.1.1 将数值类型表示的日期和时间转化为指定类型 

数据文件中表示时间的数据可能是整型或者长整型，而在进行数据分析时，往往又需要将这类数据强制转化为时间类型的格式导入并存储到数据库中。针对这种场景，可通过`loadTextEx`函数的transform参数为文本文件中的日期和时间列指定相应的数据类型。

首先，创建分布式数据库和表。

```
login(`admin,`123456)
dataFilePath="/home/data/candle_201801.csv"
dbPath="dfs://DolphinDBdatabase"
db=database(dbPath,VALUE,2018.01.02..2018.01.30)
schemaTB=extractTextSchema(dataFilePath)
update schemaTB set type="TIME" where name="time"
tb=table(1:0,schemaTB.name,schemaTB.type)
tb=db.createPartitionedTable(tb,`tb1,`date);
```

自定义函数`i2t`，用于对数据进行预处理，并返回处理过后的数据表。

```
def i2t(mutable t){
    return t.replaceColumn!(`time,time(t.time/10))
}
```

> 请注意：在自定义函数体内对数据进行处理时，请尽量使用本地的修改（以!结尾的函数）来提升性能。

调用`loadTextEx`函数，并且指定transform参数为`i2t`函数，系统会对文本文件中的数据执行`i2t`函数，并将结果保存到数据库中。

```
tmpTB=loadTextEx(dbHandle=db,tableName=`tb1,partitionColumns=`date,filename=dataFilePath,transform=i2t);
```

查看表内前5行数据。可见time列是以TIME类型存储，而不是文本文件中的INT类型：

```
select top 5 * from loadTable(dbPath,`tb1);

symbol exchange cycle tradingDay date       time               open  high  low   close volume  turnover   unixTime
------ -------- ----- ---------- ---------- ------------------ ----- ----- ----- ----- ------- ---------- -------------
000001 SZSE     1     2018.01.02 2018.01.02 02:35:10.000000000 13.35 13.39 13.35 13.38 2003635 2.678558E7 1514856660000
000001 SZSE     1     2018.01.02 2018.01.02 02:35:20.000000000 13.37 13.38 13.33 13.33 867181  1.158757E7 1514856720000
000001 SZSE     1     2018.01.02 2018.01.02 02:35:30.000000000 13.32 13.35 13.32 13.35 903894  1.204971E7 1514856780000
000001 SZSE     1     2018.01.02 2018.01.02 02:35:40.000000000 13.35 13.38 13.35 13.35 1012000 1.352286E7 1514856840000
000001 SZSE     1     2018.01.02 2018.01.02 02:35:50.000000000 13.35 13.37 13.35 13.37 1601939 2.140652E7 1514856900000
```

#### 4.1.2 日期或时间数据类型之间转换

若文本文件中日期以DATE类型存储，在导入数据库时希望以MONTH的形式存储，这种情况也可通过`loadTextEx`函数的transform参数转换该日期列的数据类型，步骤与上一小节一致。

```
login(`admin,`123456)
dbPath="dfs://DolphinDBdatabase"
db=database(dbPath,VALUE,2018.01.02..2018.01.30)
schemaTB=extractTextSchema(dataFilePath)
update schemaTB set type="MONTH" where name="tradingDay"
tb=table(1:0,schemaTB.name,schemaTB.type)
tb=db.createPartitionedTable(tb,`tb1,`date)
def d2m(mutable t){
    return t.replaceColumn!(`tradingDay,month(t.tradingDay))
}
tmpTB=loadTextEx(dbHandle=db,tableName=`tb1,partitionColumns=`date,filename=dataFilePath,transform=d2m);
```

查看表内前5行数据。可见tradingDay列是以MONTH类型存储，而不是文本文件中的DATE类型：

```
select top 5 * from loadTable(dbPath,`tb1);

symbol exchange cycle tradingDay date       time     open  high  low   close volume  turnover   unixTime
------ -------- ----- ---------- ---------- -------- ----- ----- ----- ----- ------- ---------- -------------
000001 SZSE     1     2018.01M   2018.01.02 93100000 13.35 13.39 13.35 13.38 2003635 2.678558E7 1514856660000
000001 SZSE     1     2018.01M   2018.01.02 93200000 13.37 13.38 13.33 13.33 867181  1.158757E7 1514856720000
000001 SZSE     1     2018.01M   2018.01.02 93300000 13.32 13.35 13.32 13.35 903894  1.204971E7 1514856780000
000001 SZSE     1     2018.01M   2018.01.02 93400000 13.35 13.38 13.35 13.35 1012000 1.352286E7 1514856840000
000001 SZSE     1     2018.01M   2018.01.02 93500000 13.35 13.37 13.35 13.37 1601939 2.140652E7 1514856900000
```

### 4.2 填充空值 

transform参数可调用DolphinDB的内置函数。当内置函数要求多个参数时，我们可以使用[部分应用](https://www.dolphindb.cn/cn/help/Functionalprogramming/PartialApplication.html)将多参数函数转换为一个参数的函数。例如，调用[`nullFill!`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/n/nullFill!.html)函数对文本文件中的空值进行填充。

```
db=database(dbPath,VALUE,2018.01.02..2018.01.30)
tb=db.createPartitionedTable(tb,`tb1,`date)
tmpTB=loadTextEx(dbHandle=db,tableName=`tb1,partitionColumns=`date,filename=dataFilePath,transform=nullFill!{,0});
```

## 5. 导入数组向量类型的数据
DolphinDB 中的数组向量 (array vector) 是一种特殊的向量，用于存储可变长度的二维数组。数组向量应用于数据表时，可将数据类型相同且含义相近的多列存为一列，例如股票的多档报价数据存为一个数组向量。

数据表中使用数组向量具有以下优势：
1. 显著简化某些常用的查询和计算
2. 若不同列中含有大量重复数据，使用数组向量存储可提高数据压缩比，提升查询速度

DolphinDB 提供3种方法，以导入数组向量类型的数据：
1. 直接导入符合条件的文本文件
2. 将文本文件导入内存后，将多列合并成一个数组向量，再导入分布式数据库
3. 使用 loadTextEx 函数时指定 transform 参数，将文本文件导入分布式数据库

### 5.1 直接导入符合条件的文本文件 （2.00.4及以上版本）

在导入文本文件时，暂不支持将多列数据合并导入 DolphinDB 数据表的一列（数组向量类型）。如需将数据导入为数组向量，需经过以下两步：

1. 将文本文件的多列数据合并存储到一列中，并通过标识符进行分隔。
2. 导入数据时，通过 loadText (ploadText) 与 loadTextEx 的 arrayDelimiter 参数指定分隔符，系统会将包含指定分隔符的列解析为数组向量。

构建包含数组向量的表，并将其存入1个 csv 文件

```
bid = array(DOUBLE[], 0, 20).append!([1.4799 1.479 1.4787, 1.4796 1.479 1.4784, 1.4791 1.479 1.4784])
ask = array(DOUBLE[], 0, 20).append!([1.4821 1.4825 1.4828, 1.4818 1.482 1.4821, 1.4814 1.4818 1.482])
TradeDate = 2022.01.01 + 1..3
SecurityID = rand(`APPL`AMZN`IBM, 3)
t = table(SecurityID as `sid, TradeDate as `date, bid as `bid, ask as `ask)
saveText(t,filename="/home/data/t.csv",delimiter=',',append=true)
```

导入数据前需要修改 schema 中对应列的类型为数组向量。

```
path = "/home/data/t.csv"
schema=extractTextSchema(path);
update schema set type = "DOUBLE[]" where name="bid" or name ="ask"
```

使用 loadText (ploadText) 与 loadTextEx 导入数据时，通过参数 arrayDelimiter 指定分隔符（本例中的分隔符为“,"）。

```
//用 loadText 将文本文件导入内存表
t = loadText(path, schema=schema, arrayDelimiter=",")

//用 loadTextEx 将文本文件导入分布式数据库
//创建 TSDB 引擎下的数据库表
db = database(directory="dfs://testTSDB", partitionType=VALUE, partitionScheme=`APPL`AMZN`IBM, engine="TSDB" )
name = `sid`date`bid`ask
type = ["SYMBOL","DATE","DOUBLE[]","DOUBLE[]"]
tbTemp = table(1:0, name, type)
db.createPartitionedTable(tbTemp, `pt, `sid, sortColumns=`date)
pt = loadTextEx(dbHandle=db, tableName=`pt, partitionColumns=`sid, filename=path, schema=schema, arrayDelimiter=",")
```


### 5.2 文本文件导入内存后，将多列合并成一列数组向量，再导入分布式数据库

如果不能方便地对文本文件进行修改，也可以先将数据导入内存后，将多列数据合并成一个数组向量，再导入分布式数据库。  
下例展示如何将国内A股行情快照数据的买10档或卖10档作为1个 vector 存入单个 cell 中。

建库建表及模拟数据生成语句参见[建库建表及模拟数据生成脚本](script/csvImportDemo/tsdbDatabaseTableGenerationAndDataSimulationForWritingArrayVector.dos)。

在本例中，我们首先使用 loadText 函数将模拟数据导入内存，再使用 fixedLengthArrayVector 函数将买10档和卖10档的各项数据分别整合为1列，最后将处理后的数据写入数据库。

```
snapFile="/home/data/snapshot.csv"
dbpath="dfs://LEVEL2_Snapshot_ArrayVector"
tbName="Snap"

schemas=extractTextSchema(snapFile)
update schemas set type = `SYMBOL where name = `InstrumentStatus

//使用 loadText 加载文本，耗时约1分30秒
rawTb = loadText(snapFile,schema=schemas)
//合并10档数据为1列，耗时约15秒
arrayVectorTb = select SecurityID,TradeTime,PreClosePx,OpenPx,HighPx,LowPx,LastPx,TotalVolumeTrade,TotalValueTrade,InstrumentStatus,fixedLengthArrayVector(BidPrice0,BidPrice1,BidPrice2,BidPrice3,BidPrice4,BidPrice5,BidPrice6,BidPrice7,BidPrice8,BidPrice9) as BidPrice,fixedLengthArrayVector(BidOrderQty0,BidOrderQty1,BidOrderQty2,BidOrderQty3,BidOrderQty4,BidOrderQty5,BidOrderQty6,BidOrderQty7,BidOrderQty8,BidOrderQty9) as BidOrderQty,fixedLengthArrayVector(BidOrders0,BidOrders1,BidOrders2,BidOrders3,BidOrders4,BidOrders5,BidOrders6,BidOrders7,BidOrders8,BidOrders9) as BidOrders ,fixedLengthArrayVector(OfferPrice0,OfferPrice1,OfferPrice2,OfferPrice3,OfferPrice4,OfferPrice5,OfferPrice6,OfferPrice7,OfferPrice8,OfferPrice9) as OfferPrice,fixedLengthArrayVector(OfferOrderQty0,OfferOrderQty1,OfferOrderQty2,OfferOrderQty3,OfferOrderQty4,OfferOrderQty5,OfferOrderQty6,OfferOrderQty7,OfferOrderQty8,OfferOrderQty9) as OfferOrderQty,fixedLengthArrayVector(OfferOrders0,OfferOrders1,OfferOrders2,OfferOrders3,OfferOrders4,OfferOrders5,OfferOrders6,OfferOrders7,OfferOrders8,OfferOrders9) as OfferOrders,NumTrades,IOPV,TotalBidQty,TotalOfferQty,WeightedAvgBidPx,WeightedAvgOfferPx,TotalBidNumber,TotalOfferNumber,BidTradeMaxDuration,OfferTradeMaxDuration,NumBidOrders,NumOfferOrders,WithdrawBuyNumber,WithdrawBuyAmount,WithdrawBuyMoney,WithdrawSellNumber,WithdrawSellAmount,WithdrawSellMoney,ETFBuyNumber,ETFBuyAmount,ETFBuyMoney,ETFSellNumber,ETFSellAmount,ETFSellMoney from rawTb
//载入数据库，耗时约60秒
loadTable(dbpath, tbName).append!(arrayVectorTb)
```
由上述代码可以看出，数据导入到分布式数据表，共耗时约2分45秒。

### 5.3 使用 loadTextEx 函数时指定 transform 参数，将文本文件导入分布式数据库

使用上文第4章中提到的通过为 loadTextEx 指定 transform 参数的方式，一步到位地将数据导入分布式数据库。

自定义函数`toArrayVector`，将10档数据合并为1列，重新排序列，并返回处理后的数据表。

```
def toArrayVector(mutable tmp){
  //将10档数据合并为1列，添加到tmp表中。也可以使用update!方法添加。
	tmp[`BidPrice]=fixedLengthArrayVector(tmp.BidPrice0,tmp.BidPrice1,tmp.BidPrice2,tmp.BidPrice3,tmp.BidPrice4,tmp.BidPrice5,tmp.BidPrice6,tmp.BidPrice7,tmp.BidPrice8,tmp.BidPrice9)
	tmp[`BidOrderQty]=fixedLengthArrayVector(tmp.BidOrderQty0,tmp.BidOrderQty1,tmp.BidOrderQty2,tmp.BidOrderQty3,tmp.BidOrderQty4,tmp.BidOrderQty5,tmp.BidOrderQty6,tmp.BidOrderQty7,tmp.BidOrderQty8,tmp.BidOrderQty9)
	tmp[`BidOrders]=fixedLengthArrayVector(tmp.BidOrders0,tmp.BidOrders1,tmp.BidOrders2,tmp.BidOrders3,tmp.BidOrders4,tmp.BidOrders5,tmp.BidOrders6,tmp.BidOrders7,tmp.BidOrders8,tmp.BidOrders9)
	tmp[`OfferPrice]=fixedLengthArrayVector(tmp.OfferPrice0,tmp.OfferPrice1,tmp.OfferPrice2,tmp.OfferPrice3,tmp.OfferPrice4,tmp.OfferPrice5,tmp.OfferPrice6,tmp.OfferPrice7,tmp.OfferPrice8,tmp.OfferPrice9)
	tmp[`OfferOrderQty]=fixedLengthArrayVector(tmp.OfferOrderQty0,tmp.OfferOrderQty1,tmp.OfferOrderQty2,tmp.OfferOrderQty3,tmp.OfferOrderQty4,tmp.OfferOrderQty5,tmp.OfferOrderQty6,tmp.OfferOrderQty7,tmp.OfferOrderQty8,tmp.OfferOrderQty9)
	tmp[`OfferOrders]=fixedLengthArrayVector(tmp.OfferOrders0,tmp.OfferOrders1,tmp.OfferOrders2,tmp.OfferOrders3,tmp.OfferOrders4,tmp.OfferOrders5,tmp.OfferOrders6,tmp.OfferOrders7,tmp.OfferOrders8,tmp.OfferOrders9)
  //删除合并前的列
	tmp.dropColumns!(`BidPrice0`BidPrice1`BidPrice2`BidPrice3`BidPrice4`BidPrice5`BidPrice6`BidPrice7`BidPrice8`BidPrice9`BidOrderQty0`BidOrderQty1`BidOrderQty2`BidOrderQty3`BidOrderQty4`BidOrderQty5`BidOrderQty6`BidOrderQty7`BidOrderQty8`BidOrderQty9`BidOrders0`BidOrders1`BidOrders2`BidOrders3`BidOrders4`BidOrders5`BidOrders6`BidOrders7`BidOrders8`BidOrders9`OfferPrice0`OfferPrice1`OfferPrice2`OfferPrice3`OfferPrice4`OfferPrice5`OfferPrice6`OfferPrice7`OfferPrice8`OfferPrice9`OfferOrderQty0`OfferOrderQty1`OfferOrderQty2`OfferOrderQty3`OfferOrderQty4`OfferOrderQty5`OfferOrderQty6`OfferOrderQty7`OfferOrderQty8`OfferOrderQty9`OfferOrders0`OfferOrders1`OfferOrders2`OfferOrders3`OfferOrders4`OfferOrders5`OfferOrders6`OfferOrders7`OfferOrders8`OfferOrders9)
  //对列重新排序
	tmp.reorderColumns!(`SecurityID`TradeTime`PreClosePx`OpenPx`HighPx`LowPx`LastPx`TotalVolumeTrade`TotalValueTrade`InstrumentStatus`BidPrice`BidOrderQty`BidOrders`OfferPrice`OfferOrderQty`OfferOrders`NumTrades`IOPV`TotalBidQty`TotalOfferQty`WeightedAvgBidPx`WeightedAvgOfferPx`TotalBidNumber`TotalOfferNumber`BidTradeMaxDuration`OfferTradeMaxDuration`NumBidOrders`NumOfferOrders`WithdrawBuyNumber`WithdrawBuyAmount`WithdrawBuyMoney`WithdrawSellNumber`WithdrawSellAmount`WithdrawSellMoney`ETFBuyNumber`ETFBuyAmount`ETFBuyMoney`ETFSellNumber`ETFSellAmount`ETFSellMoney)
	return tmp 
}
```

调用 `loadTextEx` 函数，并且指定 transform 参数为 `toArrayVector` 函数，系统会对文本文件中的数据执行`toArrayVector` 函数，并将结果保存到数据库中。

```
db=database(dbpath)
db.loadTextEx(tbName, `Tradetime`SecurityID, snapFile, schema=schemas, transform=toArrayVector)
```

数据导入分布式表耗时约1分40秒，比5.2章节的方法快了65秒。

## 6. 使用Map-Reduce自定义数据导入

DolphinDB支持使用Map-Reduce自定义数据导入，将数据按行进行划分，并将划分后的数据通过Map-Reduce导入到DolphinDB。

可使用[`textChunkDS`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/t/textChunkDS.html)函数将文件划分为多个小文件数据源，再通过[`mr`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/m/mr.html)函数写入到数据库中。在调用`mr`将数据存入数据库前，用户还可进行灵活的数据处理，从而实现更复杂的导入需求。

### 6.1 将文件中的股票和期货数据存储到两个不同的数据表

在DolphinDB中执行以下脚本，生成一个大小约为1.6GB的数据文件，其中包括股票数据和期货数据。
```
n=10000000
dataFilePath="/home/data/chunkText.csv"
trades=table(rand(`stock`futures,n) as type, rand(`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S,n) as sym,take(2000.01.01..2000.06.30,n) as date,10.0+rand(2.0,n) as price1,100.0+rand(20.0,n) as price2,1000.0+rand(200.0,n) as price3,10000.0+rand(2000.0,n) as price4,10000.0+rand(3000.0,n) as price5,10000.0+rand(4000.0,n) as price6,rand(10,n) as qty1,rand(100,n) as qty2,rand(1000,n) as qty3,rand(10000,n) as qty4,rand(10000,n) as qty5,rand(10000,n) as qty6)
trades.saveText(dataFilePath);
```

分别创建用于存放股票数据和期货数据的分布式数据库和表:
```
login(`admin,`123456)
dbPath1="dfs://stocksDatabase"
dbPath2="dfs://futuresDatabase"
db1=database(dbPath1,VALUE,`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S)
db2=database(dbPath2,VALUE,2000.01.01..2000.06.30)
tb1=db1.createPartitionedTable(trades,`stock,`sym)
tb2=db2.createPartitionedTable(trades,`futures,`date);
```

定义以下函数，用于划分数据，并将数据写入到不同的数据库。
```
def divideImport(tb, mutable stockTB, mutable futuresTB)
{
	tdata1=select * from tb where type="stock"
	tdata2=select * from tb where type="futures"
	append!(stockTB, tdata1)
	append!(futuresTB, tdata2)
}
```

再通过`textChunkDS`函数划分文本文件，以300MB为单位进行划分，文件被划分成了6部分。
```
ds=textChunkDS(dataFilePath,300)
ds;

(DataSource<readTableFromFileSegment, DataSource<readTableFromFileSegment, DataSource<readTableFromFileSegment, DataSource<readTableFromFileSegment)
```

调用`mr`函数，指定`textChunkDS`函数结果为数据源，将文件导入到数据库中。由于map函数（由mapFunc参数指定）只接受一个表作为参数，这里我们使用[部分应用](https://www.dolphindb.cn/cn/help/Functionalprogramming/PartialApplication.html)将多参数函数转换为一个参数的函数。

```
mr(ds=ds, mapFunc=divideImport{,tb1,tb2}, parallel=false);
```

> 请注意，这里不同的小文件数据源可能包含相同分区的数据。DolphinDB不允许多个线程同时对相同分区进行写入，因此要将`mr`函数的parallel参数设置为false，否则会抛出异常。

查看2个数据库中表的前5行，股票数据库中均为股票数据，期货数据库中均为期货数据。

stock表：

```
select top 5 * from loadTable(dbPath1, `stock);

type  sym  date       price1    price2     price3      price4       price5       price6       qty1 qty2 qty3 qty4 qty5 qty6
----- ---- ---------- --------- ---------- ----------- ------------ ------------ ------------ ---- ---- ---- ---- ---- ----
stock AMZN 2000.02.14 11.224234 112.26763  1160.926836 11661.418403 11902.403305 11636.093467 4    53   450  2072 9116 12
stock AMZN 2000.03.29 10.119057 111.132165 1031.171855 10655.048121 12682.656303 11182.317321 6    21   651  2078 7971 6207
stock AMZN 2000.06.16 11.61637  101.943971 1019.122963 10768.996906 11091.395164 11239.242307 0    91   857  3129 3829 811
stock AMZN 2000.02.20 11.69517  114.607763 1005.724332 10548.273754 12548.185724 12750.524002 1    39   270  4216 8607 6578
stock AMZN 2000.02.23 11.534805 106.040664 1085.913295 11461.783565 12496.932604 12995.461331 4    35   488  4042 6500 4826
```

futures表：

```
select top 5 * from loadTable(dbPath2, `futures);

type    sym  date       price1    price2     price3      price4       price5       price6       qty1 qty2 qty3 qty4 qty5 ...
------- ---- ---------- --------- ---------- ----------- ------------ ------------ ------------ ---- ---- ---- ---- ---- ---
futures MSFT 2000.01.01 11.894442 106.494131 1000.600933 10927.639217 10648.298313 11680.875797 9    10   241  524  8325 ...
futures S    2000.01.01 10.13728  115.907379 1140.10161  11222.057315 10909.352983 13535.931446 3    69   461  4560 2583 ...
futures GM   2000.01.01 10.339581 112.602729 1097.198543 10938.208083 10761.688725 11121.888288 1    1    714  6701 9203 ...
futures IBM  2000.01.01 10.45422  112.229537 1087.366764 10356.28124  11829.206165 11724.680443 0    47   741  7794 5529 ...
futures TSLA 2000.01.01 11.901426 106.127109 1144.022732 10465.529256 12831.721586 10621.111858 4    43   136  9858 8487 ...
```

### 6.2 快速加载大文件首尾部分数据

可使用`textChunkDS`将大文件划分成多个小的数据源(chunk)，然后加载首尾两个数据源。在DolphinDB中执行以下脚本生成数据文件：

```
n=10000000
dataFilePath="/home/data/chunkText.csv"
trades=table(rand(`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S,n) as sym,sort(take(2000.01.01..2000.06.30,n)) as date,10.0+rand(2.0,n) as price1,100.0+rand(20.0,n) as price2,1000.0+rand(200.0,n) as price3,10000.0+rand(2000.0,n) as price4,10000.0+rand(3000.0,n) as price5,10000.0+rand(4000.0,n) as price6,rand(10,n) as qty1,rand(100,n) as qty2,rand(1000,n) as qty3,rand(10000,n) as qty4, rand(10000,n) as qty5, rand(1000,n) as qty6)
trades.saveText(dataFilePath);
```
再通过`textChunkDS`函数划分文本文件，以10MB为单位进行划分。

```
ds=textChunkDS(dataFilePath, 10);
```

调用`mr`函数，加载首尾两个chunk的数据。因为这两个chunk的数据非常小，加载速度非常快。

```
head_tail_tb = mr(ds=[ds.head(), ds.tail()], mapFunc=x->x, finalFunc=unionAll{,false});
```

查看head_tail_tb表中的记录数：

```
select count(*) from head_tail_tb;

count
------
192262
```

## 7. 其它注意事项

### 7.1 不同编码的数据的处理

由于DolphinDB的字符串采用UTF-8编码，若加载的文件不是UTF-8编码，需在导入后进行转化。DolphinDB提供了[`convertEncode`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/c/convertEncode.html)、[`fromUTF8`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/f/fromUTF8.html)和[`toUTF8`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/t/toUTF8.html)函数，用于导入数据后对字符串编码进行转换。

例如，使用`convertEncode`函数转换表tmpTB中的exchange列的编码：

```
dataFilePath="/home/data/candle_201801.csv"
tmpTB=loadText(filename=dataFilePath, skipRows=0)
tmpTB.replaceColumn!(`exchange, convertEncode(tmpTB.exchange,"gbk","utf-8"));
```

### 7.2 数值类型的解析

本教程[第1节](#1-自动识别数据格式)介绍了DolphinDB在导入数据时的数据类型自动解析机制，本节讲解数值类型（包括CHAR，SHORT，INT，LONG，FLOAT和DOUBLE）数据的解析。系统能够识别以下几种形式的数值数据：

- 数字表示的数值，例如：123
- 含有千位分隔符的数值，例如：100,000
- 含有小数点的数值，即浮点数，例如：1.231
- 科学计数法表示的数值，例如：1.23E5

若指定数据类型为数值类型，DolphinDB在导入时会自动忽略数字前后的字母及其他符号，如果没有出现任何数字，则解析为NULL值。下面结合例子具体说明。

首先，执行以下脚本，创建一个文本文件。

```
dataFilePath="/home/data/testSym.csv"
prices1=["2131","$2,131", "N/A"]
prices2=["213.1","$213.1", "N/A"]
totals=["2.658E7","-2.658e7","2.658e-7"]
tt=table(1..3 as id, prices1 as price1, prices2 as price2, totals as total)
saveText(tt,dataFilePath);
```

创建的文本文件中，price1和price2列中既有数字，又有字符。若导入数据时不指定schema参数，系统会将这两列均识别为SYMBOL类型：

```
tmpTB=loadText(dataFilePath)
tmpTB;

id price1 price2 total
-- ------ ------ --------
1  2131   213.1  2.658E7
2  $2,131 $213.1 -2.658E7
3  N/A    N/A    2.658E-7

tmpTB.schema().colDefs;

name   typeString typeInt comment
------ ---------- ------- -------
id     INT        4
price1 SYMBOL     17
price2 SYMBOL     17
total  DOUBLE     16
```

若指定price1列为INT类型，指定price2列为DOUBLE类型，导入时系统会忽略数字前后的字母及其他符号。如果没有出现任何数字，则解析为NULL值。

```
schemaTB=table(`id`price1`price2`total as name, `INT`INT`DOUBLE`DOUBLE as type) 
tmpTB=loadText(dataFilePath,,schemaTB)
tmpTB;

id price1 price2 total
-- ------ ------ --------
1  2131   213.1  2.658E7
2  2131   213.1  -2.658E7
3                2.658E-7
```

### 7.3 自动去除双引号

在CSV文件中，有时候会用双引号来处理数值中含有的特殊字符（譬如千位分隔符）的字段。DolphinDB处理这样的数据时，会自动去除文本外的双引号。下面结合例子具体说明。

在下例所用的数据文件中，num列为使用千位分节法表示的数值。

```
dataFilePath="/home/data/test.csv"
tt=table(1..3 as id,  ["\"500\"","\"3,500\"","\"9,000,000\""] as num)
saveText(tt,dataFilePath);
```

导入数据并查看表内数据，DolphinDB自动脱去了文本外的双引号。

```
tmpTB=loadText(dataFilePath)
tmpTB;

id num
-- -------
1  500
2  3500
3  9000000
```


附录
--

本教程的例子中使用的数据文件： [candle_201801.csv](./data/candle_201801.csv)。

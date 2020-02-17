# DolphinDB文本数据加载教程

DolphinDB提供了多个函数（`loadText`，`ploadText`，`loadTextEx`和`textChunkDS`）将文本数据导入到内存表和分布式数据库。文本数据导入到分布式数据库，实际上也是将数据导入到内存，再从内存写入到数据库，只不过两个步骤在一个函数中完成了，效率更高。导入文本数据需要知道数据的格式，通常由用户指定。但为了方便用户，DolphinDB默认会自动分析数据格式。为了提升数据加载的效率，DolphinDB也支持多文件多线程并行加载。本教程介绍文本数据导入时的常见问题，相应的解决方案以及注意事项。

- [1.自动识别数据格式](#1自动识别数据格式)
- [2.指定数据导入格式](#2指定数据导入格式)
    - [2.1 `extractTextSchema`](#21-extracttextschema)
    - [2.2 导入文本文件中的指定列](#22-导入文本文件中的指定列)
    - [2.3 指定字段名称和类型](#23-指定字段名称和类型)
    - [2.4 指定日期和时间类型的格式](#24-指定日期和时间类型的格式)
    - [2.5 跳过文本数据的前若干行](#25-跳过文本数据的前若干行)
- [3.导入数据库前的预处理](#3导入数据库前的预处理)
- [4.使用Map-Reduce自定义数据导入](#4使用map-reduce自定义数据导入)
- [5.并行导入数据](#5并行导入数据)
    - [5.1 单个文件多线程加载](#51-单个文件多线程加载)
    - [5.2 多文件并行导入](#52-多文件并行导入)
- [6.数据导入的注意事项](#6数据导入的注意事项)
    - [6.1 不同编码的数据的处理](#61-不同编码的数据的处理)
    - [6.2 数值类型的解析](#62-数值类型的解析)
    - [6.3 自动脱去文本外的双引号](#63-自动脱去文本外的双引号)
- [7.小结](#7小结)

## 1.自动识别数据格式

DolphinDB在导入数据的同时，能够自动识别数据格式。自动识别数据格式包括两部分：字段名称识别和数据类型识别。如果文件的第一行不存在任何一列以数字开头，系统认为第一行是文件头，包含了字段名称。DolphinDB会抽取部分数据作为样本，并基于规则来确定文件中各列的数据类型。因为是基于很少一部分样本数据，数据类型的识别可能有误。但是对于大多数文本文件，无须手动指定各列的字段名称和数据类型，就能正确地导入到DolphinDB中。

> 请注意：DolphinDB支持识别大部分[DolphinDB提供的数据类型](https://www.dolphindb.cn/cn/help/DataType.html)，但是目前暂不支持识别UUID和IPADDR类型，该功能在后续版本中会支持。

DolphinDB提供[loadText](https://www.dolphindb.cn/cn/help/loadText.html)函数，用于将数据导入到DolphinDB内存表。下面直接调用`loadText`函数导入数据，并查看导入以后表的结构。例子中涉及到的数据文件请参考[附录](#附录)。

```
dataFilePath="/home/data/candle_201801.csv"
tmpTB=loadText(filename=dataFilePath)
```

查看表内前5行数据：

```
select top 5 * from tmpTB

symbol exchange cycle tradingDay date       time     open  high  low   close volume  turnover   unixTime
------ -------- ----- ---------- ---------- -------- ----- ----- ----- ----- ------- ---------- -------------
000001 SZSE     1     2018.01.02 2018.01.02 93100000 13.35 13.39 13.35 13.38 2003635 2.678558E7 1514856660000
000001 SZSE     1     2018.01.02 2018.01.02 93200000 13.37 13.38 13.33 13.33 867181  1.158757E7 1514856720000
000001 SZSE     1     2018.01.02 2018.01.02 93300000 13.32 13.35 13.32 13.35 903894  1.204971E7 1514856780000
000001 SZSE     1     2018.01.02 2018.01.02 93400000 13.35 13.38 13.35 13.35 1012000 1.352286E7 1514856840000
000001 SZSE     1     2018.01.02 2018.01.02 93500000 13.35 13.37 13.35 13.37 1601939 2.140652E7 1514856900000
```

调用[schema](https://www.dolphindb.cn/cn/help/schema.html)函数查看表结构（表的字段名称、数据类型等）：

```
tmpTB.schema().colDefs

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

## 2.指定数据导入格式

在导入时，通过指定schema参数可以指定数据导入格式，例如指定需要导入的列，指定表中字段的数据类型等。schema参数是一个表，用于指定各字段的名称、类型、格式等。该表可以包含以下4列：

列名 | 含义
--- | ---
name | 字符串，表示列名
type | 字符串，表示数各列的数据类型
format | 字符串，表示数据文件中日期或时间列的格式
col | 整型，表示要加载的列的下标。该列的值必须是升序。

其中，name和type这两列是必需的，而且必须是前两列。col和format这两列是可选的，不要求有严格的顺序关系。

具体来说，schema参数可以是这样一个表：

name|type
---|---
timestamp|SECOND
ID|INT
qty|INT
price|DOUBLE

### 2.1 extractTextSchema

DolphinDB提供[extractTextSchema](https://www.dolphindb.cn/cn/help/extractTextSchema.html)函数，获取文本文件的schema，包括字段名称和数据类型。

例如，使用`extractTextSchema`函数得到本教程中示例文件的表结构：

```
dataFilePath="/home/data/candle_201801.csv"
schemaTB=extractTextSchema(dataFilePath)
schemaTB

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

通过`extractTextSchema`函数得到数据文件的表结构schmeaTB以后，若表中自动解析的数据类型不符合预期，可以使用SQL语句对该表进行修改，从而得到满足要求的表结构。

### 2.2 导入文本文件中的指定列

在导入时，通过指定schema参数可以指定导入文本文件中的某几列。支持schema参数的函数有：[loadText](https://www.dolphindb.cn/cn/help/loadText.html)、[ploadText](https://www.dolphindb.cn/cn/help/ploadText.html)、[loadTextEx](https://www.dolphindb.cn/cn/help/loadTextEx.html)和[textChunkDS](https://www.dolphindb.cn/cn/help/textChunkDS.html)。下面使用`loadText`函数举例说明。

例如，我们只需加载文本文件中symbol，date，open，high，close，volume，turnover这7列。

首先，调用`extractTextSchema`函数得到目标文本文件的表结构。

```
dataFilePath="/home/data/candle_201801.csv"
schemaTB=extractTextSchema(dataFilePath)
```

使用SQL语句选出需要的字段。

```
update schemaTB set col = rowNo(name)
schemaTB=select * from schemaTB where name in `symbol`date`open`high`close`volume`turnover
```

>在指定需要导入的列时，请注意以下2点：
>1. 列号要从0开始编码。例如上例中第一列symbol列对应的列号是0。
>2. 不能改变各列的先后顺序。如果需要调整列的顺序，可以将数据文件加载后，再使用[reorderColumns!](https://www.dolphindb.cn/cn/help/reorderColumns.html)函数。

最后，使用`loadText`函数，并配置schema参数，导入文本文件中指定的列。

```
tmpTB=loadText(filename=dataFilePath,schema=schemaTB)
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

### 2.3 指定字段名称和类型

当系统自动识别的字段名称或者数据类型不符合预期或需求时，可以通过设置schema参数为文本文件中的每列指定字段名称和数据类型。

例如，导入数据的volume列被识别为INT类型，而需要的volume类型是LONG类型，这时就需要通过schema参数指定volumne列类型为LONG。下面的例子中，首先调用`extractTextSchema`函数得到文本文件的表结构，再根据需求修改表中列的数据类型。

```
dataFilePath="/home/data/candle_201801.csv"
schemaTB=extractTextSchema(dataFilePath)
update schemaTB set type="LONG" where name="volume"
```

使用`loadText`函数导入文本文件，将数据按照schemaTB所规定的字段数据类型导入到数据库中。

```
tmpTB=loadText(filename=dataFilePath,schema=schemaTB)
```

查看表中前五行的数据，volume列数据以长整型的形式正常显示：

```
select top 5 * from tmpTB

symbol exchange cycle tradingDay date       time     open  high  low   close volume  turnover   unixTime
------ -------- ----- ---------- ---------- -------- ----- ----- ----- ----- ------- ---------- -------------
000001 SZSE     1     2018.01.02 2018.01.02 93100000 13.35 13.39 13.35 13.38 2003635 2.678558E7 1514856660000
000001 SZSE     1     2018.01.02 2018.01.02 93200000 13.37 13.38 13.33 13.33 867181  1.158757E7 1514856720000
000001 SZSE     1     2018.01.02 2018.01.02 93300000 13.32 13.35 13.32 13.35 903894  1.204971E7 1514856780000
000001 SZSE     1     2018.01.02 2018.01.02 93400000 13.35 13.38 13.35 13.35 1012000 1.352286E7 1514856840000
000001 SZSE     1     2018.01.02 2018.01.02 93500000 13.35 13.37 13.35 13.37 1601939 2.140652E7 1514856900000
```

上例中只是介绍了修改数据类型的情况，若要修改表中的字段名称，也可以通过同样的方法实现。

> 请注意，若DolphinDB对日期和时间相关数据类型的解析不符合预期，需要通过本教程[第2.4小节](#24-指定日期和时间类型的格式)的方式解决。

### 2.4 指定日期和时间类型的格式

对于日期列或时间列的数据，如果DolphinDB识别的数据类型不符合预期，不仅需要在schema的type列指定时间类型，还需要在format列中指定数据文件中日期或时间的格式（用字符串表示），如"MM/dd/yyyy"。如何表示日期和时间格式请参考[日期和时间的调整及格式](https://www.dolphindb.cn/cn/help/DataTimeParsingandFormat.html)。

下面结合例子具体说明对日期和时间相关列指定数据类型的方法。

在DolphinDB中执行以下脚本，生成本例所需的数据文件。

```
dataFilePath="/home/data/timeData.csv"
t=table(["20190623 14:54:57","20190623 15:54:23","20190623 16:30:25"] as time,`AAPL`MS`IBM as sym,2200 5400 8670 as qty,54.78 59.64 65.23 as price)
saveText(t,dataFilePath)
```

加载数据前，使用`extractTextSchema`函数获取该数据文件的结构:

```
schemaTB=extractTextSchema(dataFilePath)
schemaTB

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
schemaTB[`format]=["yyyyMMdd HH:mm:ss",,,]
```

导入数据并查看，数据显示正确：
```
tmpTB=loadText(dataFilePath,,schemaTB)
tmpTB

time                sym  qty  price
------------------- ---- ---- -----
2019.06.23T14:54:57 AAPL 2200 54.78
2019.06.23T15:54:23 MS   5400 59.64
2019.06.23T16:30:25 IBM  8670 65.23
```

### 2.5 跳过文本数据的前若干行

在数据导入时，为了去掉文件前几行的文件说明，可以通过指定skipRows参数为n，来选择跳过文本文件前n行导入文件。由于描述文件的说明通常不会非常冗长，因此这个参数的取值最大为1024。支持skipRows参数的函数有：[loadText](https://www.dolphindb.cn/cn/help/loadText.html)、[ploadText](https://www.dolphindb.cn/cn/help/ploadText.html)、[loadTextEx](https://www.dolphindb.cn/cn/help/loadTextEx.html)和[textChunkDS](https://www.dolphindb.cn/cn/help/textChunkDS.html)。下面使用`loadText`函数举例说明。

下面的例子中，通过`loadText`函数导入数据文件，并且查看该文件导入以后表的总行数，以及前5行的内容。

```
dataFilePath="/home/data/candle_201801.csv"
tmpTB=loadText(filename=dataFilePath)
select count(*) from tmpTB

count
-----
5040

select top 5 * from tmpTB

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
select count(*) from tmpTB

count
-----
4041

select top 5 * from tmpTB

col0   col1 col2 col3       col4       col5      col6  col7  col8  col9  col10  col11      col12
------ ---- ---- ---------- ---------- --------- ----- ----- ----- ----- ------ ---------- -------------
000001 SZSE 1    2018.01.08 2018.01.08 101000000 13.13 13.14 13.12 13.14 646912 8.48962E6  1515377400000
000001 SZSE 1    2018.01.08 2018.01.08 101100000 13.13 13.14 13.13 13.14 453647 5.958462E6 1515377460000
000001 SZSE 1    2018.01.08 2018.01.08 101200000 13.13 13.14 13.12 13.13 700853 9.200605E6 1515377520000
000001 SZSE 1    2018.01.08 2018.01.08 101300000 13.13 13.14 13.12 13.12 738920 9.697166E6 1515377580000
000001 SZSE 1    2018.01.08 2018.01.08 101400000 13.13 13.14 13.12 13.13 469800 6.168286E6 1515377640000
```

> 请注意：数据在跳过前n行进行导入时，不会因为数据文件的第一行是列名而保留该行。

在上面的例子中，文本文件指定skipRows参数导入以后，由于表示列名的第一行被跳过，列名变成了DolphinDB的默认列名：col1，col2等等。若需要保留列名而又指定跳过前n行，也可以先通过`extractTextSchema`函数得到文本文件的表结构，在导入时同时指定schema参数：

```
schema=extractTextSchema(dataFilePath)
tmpTB=loadText(filename=dataFilePath,schema=schema,skipRows=1000)
select count(*) from tmpTB

count
-----
4041

select top 5 * from tmpTB

symbol exchange cycle tradingDay date       time      open  high  low   close volume turnover   unixTime
------ -------- ----- ---------- ---------- --------- ----- ----- ----- ----- ------ ---------- -------------
000001 SZSE     1     2018.01.08 2018.01.08 101000000 13.13 13.14 13.12 13.14 646912 8.48962E6  1515377400000
000001 SZSE     1     2018.01.08 2018.01.08 101100000 13.13 13.14 13.13 13.14 453647 5.958462E6 1515377460000
000001 SZSE     1     2018.01.08 2018.01.08 101200000 13.13 13.14 13.12 13.13 700853 9.200605E6 1515377520000
000001 SZSE     1     2018.01.08 2018.01.08 101300000 13.13 13.14 13.12 13.12 738920 9.697166E6 1515377580000
000001 SZSE     1     2018.01.08 2018.01.08 101400000 13.13 13.14 13.12 13.13 469800 6.168286E6 1515377640000
```

## 3.导入数据库前的预处理

在将数据导入数据库之前，若需要对数据进行复杂的处理，例如日期和时间数据类型的强制转换，填充空值等，可以在调用函数时指定transform参数。tansform参数接受一个函数作为参数，并且要求该函数只能接受一个参数，函数的输入是一个未分区的内存表，输出也是一个未分区的内存表。需要注意的是，只有[loadTextEx](https://www.dolphindb.cn/cn/help/loadTextEx.html)函数提供transform参数，下面重点讲解transform参数的适用场景。

### 3.1 指定日期和时间数据的数据类型

#### 3.1.1 将数值类型表示的日期和时间转化为指定类型 

在导入数据时会遇到的一种场景是，数据文件中存储的表示时间数据是整型或者长整型，而在进行数据分析时，往往又需要将数据强制转化为时间类型的格式导入并存储到数据库中。针对这种场景，通过指定transeform参数，可以为文本文件中的日期和时间列指定相应的数据类型。

首先，创建分布式数据库和表。

```
login(`admin,`123456)
dataFilePath="/home/data/candle_201801.csv"
dbPath="dfs://DolphinDBdatabase"
db=database(dbPath,VALUE,2018.01.02..2018.01.30)
schemaTB=extractTextSchema(dataFilePath)
update schemaTB set type="TIME" where name="time"
tb=table(1:0,schemaTB.name,schemaTB.type)
tb=db.createPartitionedTable(tb,`tb1,`date)
```

自定义函数foo，用于对数据进行预处理，返回处理过后的数据表。

```
def foo(mutable t){
    return t.replaceColumn!(`time,time(t.time/10))
}
```

> 请注意：在自定义函数体内对数据进行处理时，请尽量使用本地的修改来提升性能。

调用`loadTextEx`函数，并且指定transform参数，系统会对文本文件中的数据执行transform参数指定的函数，即foo函数，再将得到的结果保存到数据库中。

```
tmpTB=loadTextEx(dbHandle=db,tableName=`tb1,partitionColumns=`date,filename=dataFilePath,transform=foo)
```

查看表内前5行数据，系统中time列的数据是以TIME类型存储，而不是文本文件中的INT类型：

```
select top 5* from loadTable(dbPath,`tb1)

symbol exchange cycle tradingDay date       time               open  high  low   close volume  turnover   unixTime
------ -------- ----- ---------- ---------- ------------------ ----- ----- ----- ----- ------- ---------- -------------
000001 SZSE     1     2018.01.02 2018.01.02 02:35:10.000000000 13.35 13.39 13.35 13.38 2003635 2.678558E7 1514856660000
000001 SZSE     1     2018.01.02 2018.01.02 02:35:20.000000000 13.37 13.38 13.33 13.33 867181  1.158757E7 1514856720000
000001 SZSE     1     2018.01.02 2018.01.02 02:35:30.000000000 13.32 13.35 13.32 13.35 903894  1.204971E7 1514856780000
000001 SZSE     1     2018.01.02 2018.01.02 02:35:40.000000000 13.35 13.38 13.35 13.35 1012000 1.352286E7 1514856840000
000001 SZSE     1     2018.01.02 2018.01.02 02:35:50.000000000 13.35 13.37 13.35 13.37 1601939 2.140652E7 1514856900000
```

#### 3.1.2 为文本文件中的日期和时间相关列指定数据类型

另一种与日期和时间列相关的处理是，文本文件中日期以DATE类型存储，在导入数据库时有希望以MONTH的形式存储，这时候也可以通过transform参数转换该日期列的数据类型。步骤与上述过程一致。

```
login(`admin,`123456)
dbPath="dfs://DolphinDBdatabase"
db=database(dbPath,VALUE,2018.01.02..2018.01.30)
schemaTB=extractTextSchema(dataFilePath)
update schemaTB set type="MONTH" where name="tradingDay"
tb=table(1:0,schemaTB.name,schemaTB.type)
tb=db.createPartitionedTable(tb,`tb1,`date)
def fee(mutable t){
    return t.replaceColumn!(`tradingDay,month(t.tradingDay))
}
tmpTB=loadTextEx(dbHandle=db,tableName=`tb1,partitionColumns=`date,filename=dataFilePath,transform=fee)
```

查看表内前5行数据，系统中tradingDay列的数据是以MONTH类型存储，而不是文本文件中的DATE类型：

```
select top 5* from loadTable(dbPath,`tb1)

symbol exchange cycle tradingDay date       time     open  high  low   close volume  turnover   unixTime
------ -------- ----- ---------- ---------- -------- ----- ----- ----- ----- ------- ---------- -------------
000001 SZSE     1     2018.01M   2018.01.02 93100000 13.35 13.39 13.35 13.38 2003635 2.678558E7 1514856660000
000001 SZSE     1     2018.01M   2018.01.02 93200000 13.37 13.38 13.33 13.33 867181  1.158757E7 1514856720000
000001 SZSE     1     2018.01M   2018.01.02 93300000 13.32 13.35 13.32 13.35 903894  1.204971E7 1514856780000
000001 SZSE     1     2018.01M   2018.01.02 93400000 13.35 13.38 13.35 13.35 1012000 1.352286E7 1514856840000
000001 SZSE     1     2018.01M   2018.01.02 93500000 13.35 13.37 13.35 13.37 1601939 2.140652E7 1514856900000
```

### 3.2 对表内数据填充空值 

transform参数支持直接调用DolphinDB的内置函数，当内置函数要求多个参数时，我们可以使用[部分应用](https://www.dolphindb.cn/cn/help/PartialApplication.html)将多参数函数转换为一个参数的函数。例如，直接调用[nullFill!](https://www.dolphindb.cn/cn/help/nullFill1.html)函数对文本文件中的空值进行填充。

```
db=database(dbPath,VALUE,2018.01.02..2018.01.30)
tb=db.createPartitionedTable(tb,`tb1,`date)
tmpTB=loadTextEx(dbHandle=db,tableName=`pt,partitionColumns=`date,filename=dataFilePath,transform=nullFill!{,0})
```

## 4.使用Map-Reduce自定义数据导入

DolphinDB支持自定义数据导入，即数据可以在导入数据库之前按行进行划分，并将划分后的数据通过Map-Reduce导入到DolphinDB。

DolphinDB提供[textChunkDS](https://www.dolphindb.cn/cn/help/textChunkDS.html)函数，该函数可以将文件划分为多个小文件数据源，每个数据源的大小为chunkSize，再通过[mr](https://www.dolphindb.cn/cn/help/mr.html)函数写入到数据库中。在调用`mr`时，用户还能指定自定义的划分依据，从而实现更复杂的导入需求。

下面展示使用`textChunkDS`函数划分数据并导入到DolphinDB的2个例子。

### 4.1 将文件中的股票和期货数据存储到两个不同的数据表

由于`textChunkDS`按照MB为单位划分数据，因此本节的例子生成一个大小约为1GB的数据文件作为示例数据。

在DolphinDB中执行以下脚本生成数据文件：

```
n=10000000
dataFilePath="/home/data/chunkText.csv"
trades=table(rand(`stock`futures,n) as type, rand(`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S,n) as sym,take(2000.01.01..2000.06.30,n) as date,10.0+rand(2.0,n) as price1,100.0+rand(20.0,n) as price2,1000.0+rand(200.0,n) as price3,10000.0+rand(2000.0,n) as price4,10000.0+rand(3000.0,n) as price5,10000.0+rand(4000.0,n) as price6,rand(10,n) as qty1,rand(100,n) as qty2,rand(1000,n) as qty3,rand(10000,n) as qty4,rand(10000,n) as qty5,rand(10000,n) as qty6)
trades.saveText(dataFilePath)
```

分别创建用于存放股票数据和期货数据的分布式数据库和表:

```
login(`admin,`123456)
dbPath1="dfs://DolphinDBTickDatabase"
dbPath2="dfs://DolphinDBFuturesDatabase"
db1=database(dbPath1,VALUE,`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S)
db2=database(dbPath2,VALUE,2000.01.01..2000.06.30)
tb1=db1.createPartitionedTable(trades,`stock,`sym)
tb2=db2.createPartitionedTable(trades,`futures,`date)
```

定义函数，用于划分数据，并将数据写入到不同的数据库。

```
def divideImport(tb,mutable stockTB,mutable futuresTB)
{
	tdata1=select * from tb where type="stock"
	tdata2=select * from tb where type="futures"
	append!(stockTB, tdata1)
	append!(futuresTB, tdata2)
}
```

再通过`textChunkDS`函数划分文本文件，以300MB为单位进行划分，文件被划分成了4部分。

```
ds=textChunkDS(dataFilePath,300)
ds

(DataSource< readTableFromFileSegment ,DataSource< readTableFromFileSegment ,DataSource< readTableFromFileSegment ,DataSource< readTableFromFileSegment )
```

调用`mr`函数，指定数据源将文件导入到数据库中。由于mapFunc函数只接受一个表作为参数，这里我们使用[部分应用](https://www.dolphindb.cn/cn/help/PartialApplication.html)将多参数函数转换为一个参数的函数。

```
mr(ds=ds,mapFunc=divideImport{,tb1,tb2},parallel=false)
```

> 请注意，这里每个小文件数据源可能包含相同分区的数据。DolphinDB不允许多个线程同时对相同分区进行写入，因此要将`mr`函数parallel参数设置为false，否则会抛出异常。

查看2个数据库中表的前5行，股票数据库中均为股票数据，期货数据库中均为期货数据。

stock表：

```
select top 5 * from loadTable("dfs://DolphinDBTickDatabase", `stock)

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
select top 5 * from loadTable("dfs://DolphinDBFuturesDatabase", `futures)

type    sym  date       price1    price2     price3      price4       price5       price6       qty1 qty2 qty3 qty4 qty5 ...
------- ---- ---------- --------- ---------- ----------- ------------ ------------ ------------ ---- ---- ---- ---- ---- ---
futures MSFT 2000.01.01 11.894442 106.494131 1000.600933 10927.639217 10648.298313 11680.875797 9    10   241  524  8325 ...
futures S    2000.01.01 10.13728  115.907379 1140.10161  11222.057315 10909.352983 13535.931446 3    69   461  4560 2583 ...
futures GM   2000.01.01 10.339581 112.602729 1097.198543 10938.208083 10761.688725 11121.888288 1    1    714  6701 9203 ...
futures IBM  2000.01.01 10.45422  112.229537 1087.366764 10356.28124  11829.206165 11724.680443 0    47   741  7794 5529 ...
futures TSLA 2000.01.01 11.901426 106.127109 1144.022732 10465.529256 12831.721586 10621.111858 4    43   136  9858 8487 ...
```

### 4.2 快速加载大文件首尾部分数据

我们使用textChunkDS将大文件划分成多个小的chunk，也就是数据源。然后加载首尾两个数据源。在DolphinDB中执行以下脚本生成数据文件。

```
n=10000000
dataFilePath="/home/data/chunkText.csv"
trades=table(rand(`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S,n) as sym,sort(take(2000.01.01..2000.06.30,n)) as date,10.0+rand(2.0,n) as price1,100.0+rand(20.0,n) as price2,1000.0+rand(200.0,n) as price3,10000.0+rand(2000.0,n) as price4,10000.0+rand(3000.0,n) as price5,10000.0+rand(4000.0,n) as price6,rand(10,n) as qty1,rand(100,n) as qty2,rand(1000,n) as qty3,rand(10000,n) as qty4, rand(10000,n) as qty5, rand(1000,n) as qty6)
trades.saveText(dataFilePath)
```
再通过`textChunkDS`函数划分文本文件，以10MB为单位进行划分。

```
ds=textChunkDS(dataFilePath, 10)
```

调用`mr`函数，加载首尾两个chunk的数据。因为这两个chunk的数据非常小，加载速度非常快。

```
head_tail_tb = mr(ds=[ds.head(), ds.tail()], mapFunc=x->x, finalFunc=unionAll{,false})
```

查看head_tail_tb表中的记录数以及前5条记录。因为数据是随机生成，记录数可能每次会略有不同，前5行的数据也会跟下面显示的不同。

```
select count(*) from head_tail_tb

count
------
192262
```

查看表的前5行数据：

```
select top 5 * from head_tail_tb

sym  date       price1    price2     price3      price4       price5       price6       qty1 qty2 qty3 qty4 qty5 qty6
---- ---------- --------- ---------- ----------- ------------ ------------ ------------ ---- ---- ---- ---- ---- ----
IBM  2000.01.01 10.978551 114.535418 1163.425635 11827.976468 11028.01038  10810.987825 2    51   396  6636 9403 937
MSFT 2000.01.01 11.776656 106.472172 1138.718459 10720.778545 10164.638399 11348.744314 9    79   691  533  5669 72
FB   2000.01.01 11.515097 118.674854 1153.305462 10478.6335   12160.662041 13874.09572  3    29   592  2097 4103 113
MSFT 2000.01.01 11.72034  105.760547 1139.238066 10669.293733 11314.226676 12560.093619 1    99   166  2282 9167 483
TSLA 2000.01.01 10.272615 114.748639 1043.019437 11508.695323 11825.865846 10495.364306 6    43   95   9433 6641 490
```

## 5.并行导入数据

在大数据应用领域，数据导入往往不只是涉及一个或两个文件的导入，而是数十个甚至数百个大型文件的批量导入，因此，为了达到更好的导入性能，建议尽量以并行方式导入批量的数据。下面介绍并行导入的例子以及相关注意事项。

### 5.1 单个文件多线程加载

DolphinDB提供[ploadText](https://www.dolphindb.cn/cn/help/ploadText.html)函数，用于将一个文本文件以多线程的方式加载到DolphinDB中。该函数与[loadText](https://www.dolphindb.cn/cn/help/loadText.html)函数功能与参数均一致，唯一的区别是`ploadText`函数可以快速载入大文件。它在设计中充分利用了多核CPU来并行载入文件，并行程度取决于服务器本身CPU核数量和节点的localExecutors配置。

下面比较`loadText`函数与`ploadText`函数导入同一个文件的性能。

首先通过脚本生成一个4G左右的文本文件：

```txt
filePath="/home/data/testFile.csv"
appendRows=100000000
t=table(rand(100,appendRows) as int,take(string('A'..'Z'),appendRows) as symbol,take(2010.01.01..2018.12.30,appendRows) as date,rand(float(100),appendRows) as float,00:00:00.000 + rand(86400000,appendRows) as time)
t.saveText(filePath)
```

分别通过`loadText`和`ploadText`来载入文件。本例所用节点是6核12超线程的CPU。

```txt
timer loadText(filePath)
Time elapsed: 12629.492 ms

timer ploadText(filePath)
Time elapsed: 2669.702 ms
```

结果显示在此配置下，`ploadText`的性能是`loadText`的4.5倍左右。

需要注意的是，`ploadText`和`loadText`函数只能将文本文件导入到普通的内存非分区表中。DolphinDB的非分区表不支持多个线程并发读写多个文件，因此这里所说的`ploadText`的多线程加载仅仅是提高单个文件的写入速度。

### 5.2 多文件并行导入

DolphinDB提供[loadTextEx](https://www.dolphindb.cn/cn/help/loadTextEx.html)函数，用于将数据导入到DolphinDB的分区表中。由于DolphinDB的分区表支持并发读写，因此可以支持多线程导入数据。下面展示如何将磁盘上的多个文件批量写入到DolphinDB分区表中。

首先，在DolphinDB中执行以下脚本，生成100个文件，生成的文件大小约为778MB，共包括1千万条记录。

```
n=100000
dataFilePath="/home/data/multi/multiImport_"+string(1..100)+".csv"
for (i in 0..99){
    trades=table(sort(take(100*i+1..100,n)) as id,rand(`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S,n) as sym,take(2000.01.01..2000.06.30,n) as date,10.0+rand(2.0,n) as price1,100.0+rand(20.0,n) as price2,1000.0+rand(200.0,n) as price3,10000.0+rand(2000.0,n) as price4,10000.0+rand(3000.0,n) as price5)
    trades.saveText(dataFilePath[i])
}
```

创建数据库和表：

```
login(`admin,`123456)
dbPath="dfs://DolphinDBdatabase"
db=database(dbPath,VALUE,1..10000)
tb=db.createPartitionedTable(trades,`tb,`id)
```

DolphinDB的[cut](https://www.dolphindb.cn/cn/help/cut.html)函数可以划分一个向量，下面调用`cut`函数将待导入的文件路径进行分组，再调用[submitJob](https://www.dolphindb.cn/cn/help/submitJob.html)函数，为每个线程分配写入任务，批量导入数据。

```
def writeData(db,file){
   loop(loadTextEx{db,`tb,`id,},file)
}
parallelLevel=10
for(x in dataFilePath.cut(100/parallelLevel)){
    submitJob("loadData"+parallelLevel,"loadData",writeData{db,x})
}
```

> 请注意：DolphinDB的分区表不允许多个线程同时向一个分区写数据。上面的例子中，每个文件中的分区列（id列）取值互相不一致，因此不会造成多个线程写同一个分区的情况。在设计分区表的并发读写时，请确保每个线程同时将数据写到不同的分区。

通过[getRecentJobs](https://www.dolphindb.cn/cn/help/getRecentJobs.html)函数可以取得当前本地节点上最近N个批处理作业的状态，该函数返回一个表。使用select语句计算并行导入批量文件所需时间，得到在6核12超线程的CPU上耗时约1.59秒。

```
select max(endTime) - min(startTime) from getRecentJobs() where jobId like "loadData"+string(parallelLevel)+"%"

max_endTime_sub
---------------
1590
```

执行以下脚本，将100个文件单线程顺序导入数据库，记录所需时间，耗时约8.65秒。

```
timer writeData(db, dataFilePath)
Time elapsed: 8647.645 ms
```

结果显示在此配置下，并行开启10个线程导入速度是单线程导入的5.5倍左右。

查看数据表中的记录条数：

```
select count(*) from loadTable("dfs://DolphinDBdatabase", `tb)

count
------
10000000
```

## 6.数据导入的注意事项

### 6.1 不同编码的数据的处理

由于DolphinDB的字符串采用UTF-8编码，加载的文件必须是UTF-8编码。若为其它形式的编码，可以在导入以后进行转化。DolphinDB提供了[convertEncode](https://www.dolphindb.cn/cn/help/convertEncode.html)、[fromUTF8](https://www.dolphindb.cn/cn/help/fromUTF8.html)和[toUTF8](https://www.dolphindb.cn/cn/help/toUTF8.html)函数，用于对字符串编码进行转换，方便用户将文件导入到DolphinDB数据库中以后，将数据转换成合适的编码再进行处理。

例如，使用`convertEncode`函数转换表tmpTB中的exchange列的编码：

```
dataFilePath="/home/data/candle_201801.csv"
tmpTB=loadText(filename=dataFilePath, skipRows=0)
tmpTB.replaceColumn!(`exchange, convertEncode(tmpTB.exchange,"gbk","utf-8"))
```

### 6.2 数值类型的解析

本教程[第1节](#1-自动识别数据格式)曾经提及，DolphinDB在导入数据的时的数据类型自动解析机制。DolphinDB能够识别的对于数值类型的数据，若指定该列为数值型，DolphinDB在导入时会自动忽略该列中的文本数据，以NULL值存储。下面结合例子具体说明。

首先，执行以下脚本，创建一个文本文件。

```
dataFilePath="/home/data/testSym.csv"
n=1000
syms=take(["112","123","fyfy"],n)
tt=table(1..n as id, syms as sym)
saveText(tt,dataFilePath)
```

创建的文本文件中，syms列既有数字，又有字符。首先不指定schema参数导入数据，DolphinDB会将sym列识别为SYMBOL类型：

```
tmpTB=loadText(dataFilePath)
tmpTB

id sym
-- ----
1  112
2  123
3  fyfy

tmpTB.schema().colDefs

name typeString typeInt comment
---- ---------- ------- -------
id   INT        4
sym  SYMBOL     17
```

指定syms列为INT类型，DolphinDB会跳过字母等非数值的数据，以NULL值存储：

```
schemaTB=table(`id`sym as name, `INT`INT as type)
tmpTB=loadText(dataFilePath,,schemaTB)
tmpTB

id sym
-- ---
1  112
2  123
3
```

### 6.3 自动脱去文本外的双引号

在CSV文件中，有时候会用双引号来处理文本和数值中含的特殊字符（譬如分隔符）的字段。DolphinDB处理这样的数据时，会自动脱去文本外的双引号。下面结合例子具体说明。

首先生成示例数据。

```
dataFilePath="/home/data/testSym.csv"
tt=table(1..3 as id,  ["\"321\"", "\"s\"", "\"21\""] as sym)
saveText(tt,dataFilePath)
```

导入数据并查看表内数据：

```
schemaTB=table(`id`sym as name, `INT`INT as type)
tmpTB=loadText(dataFilePath,,schemaTB)
tmpTB

id sym
-- ---
1  321
2
3  21
```

## 7.小结

DolphinDB通过以下4个函数，提供了丰富而强大的文本文件导入功能：

- [loadText](https://www.dolphindb.cn/cn/help/loadText.html): 将文本文件以 DolphinDB 数据表的形式读取到内存中。
- [ploadText](https://www.dolphindb.cn/cn/help/ploadText.html): 将文本文件切割并行导入为分区内存表。与`loadText`函数相比，速度更快。
- [loadTextEx](https://www.dolphindb.cn/cn/help/loadTextEx.html): 把文本文件导入到指定的数据库中，包括内存数据库，磁盘数据库和分布式数据库。
- [textChunkDS](https://www.dolphindb.cn/cn/help/textChunkDS.html)：将文本文件划分为多个小数据源，再通过[mr](https://www.dolphindb.cn/cn/help/mr.html)函数进行灵活的数据处理。

DolphinDB的文本数据导入不仅功能丰富，灵活，而且导入速度非常快。在单线程导入的情况下，DolphinDB与Clickhouse、MemSQL、Druid、Pandas等业界流行的系统相比，速度更快，最多达一个数量级的优势。多线程并行导入的情况下，优势更明显。

附录
--

本教程的例子中使用的数据文件： [candle_201801.csv](https://github.com/dolphindb/Tutorials_CN/blob/master/data/candle_201801.csv)。

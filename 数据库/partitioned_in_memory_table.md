# DolphinDB教程：内存数据表

DolphinDB的内存数据表可以是非分区的，也可以是分区的。除了组合分区以外的所有分区方式都适用于内存数据表。使用分区内存表进行运算能充分发挥多核CPU并行计算的优势。

本教程主要介绍以下内容：

- [DolphinDB教程：内存数据表](#dolphindb教程内存数据表)
  - [1. 创建内存数据表](#1-创建内存数据表)
    - [1.1 创建非分区内存表](#11-创建非分区内存表)
    - [1.2 创建分区内存表](#12-创建分区内存表)
  - [2. 加载数据到内存表](#2-加载数据到内存表)
    - [2.1 加载数据到未分区内存表](#21-加载数据到未分区内存表)
  - [2.2 加载数据到分区内存表](#22-加载数据到分区内存表)
    - [2.2.1 使用`ploadText`函数将文本文件导入为顺序分区的内存表](#221-使用ploadtext函数将文本文件导入为顺序分区的内存表)
    - [2.2.3 使用`loadTextEx`函数将文本文件导入为指定分区方式的表](#223-使用loadtextex函数将文本文件导入为指定分区方式的表)
    - [2.2.3 使用`loadTable`函数导入磁盘分区表的全部或部分分区](#223-使用loadtable函数导入磁盘分区表的全部或部分分区)
    - [2.2.4 使用`loadTableBySQL`函数导入磁盘分区表指定的行/列](#224-使用loadtablebysql函数导入磁盘分区表指定的行列)
  - [3. 内存表的数据处理](#3-内存表的数据处理)
    - [3.1 插入数据](#31-插入数据)
    - [3.2 增加列](#32-增加列)
    - [3.3 更新已存在的列](#33-更新已存在的列)
    - [3.4 删除行](#34-删除行)
    - [3.5 删除列](#35-删除列)
    - [3.6 重命名列](#36-重命名列)
    - [3.7 查看表结构](#37-查看表结构)
    - [3.8 删除内存表](#38-删除内存表)
    - [3.9 修改列的数据类型](#39-修改列的数据类型)
    - [3.10 修改列的顺序](#310-修改列的顺序)

## 1. 创建内存数据表

### 1.1 创建非分区内存表

使用`table`函数可以创建非分区内存表。`table`函数的用法非常灵活：

- 第一种用法：table(X, [X1], [X2], .....)

这里的X, X1, X2可以是向量、矩阵或元组，其中每个向量、矩阵和元组中每个元素的长度必须相同。

例1. 如果X是向量，那么每个向量对应表中一列。

```
id=`XOM`GS`AAPL
x=102.1 33.4 73.6
table(id, x)

id   x
---- -----
XOM  102.1
GS   33.4
AAPL 73.6

table(`XOM`GS`AAPL as id, 102.1 33.4 73.6 as x)

id   x
---- -----
XOM  102.1
GS   33.4
AAPL 73.6
```

例2. 如果X是矩阵，`table`函数将矩阵转换为表。

```
m1=1..6$3:2
table(m1)

C0 C1
-- --
1  4 
2  5 
3  6 

m2=7..12$3:2
table(m1,m2)

C0 C1 C2 C3
-- -- -- --
1  4  7  10
2  5  8  11
3  6  9  12

```

例3. 如果X是元组，那么元组中的每个元素对应表中的一列。

```
x=(["a","b","c"],[4,5,6])
table(x)

C0 C1
-- --
a  4 
b  5 
c  6 
```

例4. `table`函数的输入是向量、矩阵和元组。

```
x=1..6
y=11..22$6:2
z=(101..106, 201..206)
table(x,y,z)

x C1 C2 C3  C4 
- -- -- --- ---
1 11 17 101 201
2 12 18 102 202
3 13 19 103 203
4 14 20 104 204
5 15 21 105 205
6 16 22 106 206
```

- 第二种用法：table(capacity:size, colNames, colTypes)

我们可以通过指定表的容量和初始大小、列名以及每列的数据类型来创建内存表。如果表中实际的记录行数超出的capacity，它会自动扩展。如果要创建一个空的表，可以把size设置为0，如果size>0，创建表时会使用默认值填充。例如：

```
table(200:0, `name`id`value, [STRING,INT,DOUBLE])

name id value
---- -- -----


table(200:10, `name`id`value, [STRING,INT,DOUBLE])

name id value
---- -- -----
     0  0
     0  0
     0  0
     0  0
     0  0
     0  0
     0  0
     0  0
     0  0
     0  0

```

### 1.2 创建分区内存表

通过`createPartitionedTable`函数可以创建分区内存表。在创建分区内存表之前，需要创建内存的分区数据库，其路径为空字符串。

```
n=10000
t=table(rand(1..10,n) as id,rand(10.0,n) as val)
db=database("",VALUE,1..10)
pt=db.createPartitionedTable(t,`pt,`id).append!(t)
typestr(pt)

SEGMENTED IN-MEMORY TABLE
```

对于内存分区表，不能直接访问，需要使用SQL语句访问。

```
select * from pt
```

## 2. 加载数据到内存表

通过以下脚本，生成一个模拟数据集，用于后续例子。
```
n=30000000
workDir = "C:/DolphinDB/Data"
if(!exists(workDir)) mkdir(workDir)
trades=table(rand(`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S,n) as sym, 2000.01.01+rand(365,n) as date, 10.0+rand(2.0,n) as price1, 100.0+rand(20.0,n) as price2, 1000.0+rand(200.0,n) as price3, 10000.0+rand(2000.0,n) as price4, 10000.0+rand(3000.0,n) as price5, 10000.0+rand(4000.0,n) as price6, rand(10,n) as qty1, rand(100,n) as qty2, rand(1000,n) as qty3, rand(10000,n) as qty4, rand(10000,n) as qty5, rand(10000,n) as qty6)
trades.saveText(workDir + "/trades.txt");
```

### 2.1 加载数据到未分区内存表

使用`loadText`函数将文本文件数据导入到未分区内存表：
```
trades=loadText(workDir + "/trades.txt")
```

## 2.2 加载数据到分区内存表

### 2.2.1 使用`ploadText`函数将文本文件导入为顺序分区的内存表

这是最简单的将数据导入到内存分区表的方法，但缺乏其它导入方法的某些优点及灵活性。例如，需要导入的文本文件必须小于可用内存；无法使用函数`sortBy!`进行有意义的排序，等等。
```
trades = ploadText(workDir + "/trades.txt");
```

### 2.2.3 使用`loadTextEx`函数将文本文件导入为指定分区方式的表

这种方法适合下列情况：
* 经常需要在各个分区内部进行排序
* 经常需要根据分区字段进行group by与context by的计算

使用这种方法时，`database`函数的directory参数以及`loadTextEx`函数的tableName参数需使用空字符串("")。
```
db = database("", VALUE, `IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S)
trades = db.loadTextEx("", `sym, workDir + "/trades.txt");

trades.sortBy!(`qty1);

trades.sortBy!(`date`qty1, false true);

trades.sortBy!(<qty1 * price1>, false);
```

请注意，对内存分区表使用函数`sortBy!`时，是在每个分区内部进行排序，并不是对全表进行排序。

我们分别对未分区内存表、顺序分区内存表以及本节中的VALUE分区内存表，进行相同的分组聚合运算。SQL语句如下：

```
timer(10) select std(qty1) from trades group by sym;
```

这里的 "timer(10)" 指的是此语句被连续执行10次的总耗时。

结果如下表所致。可以看到，当分组列和分区列相同时，分组计算性能最优。

| 数据表        | 产生时所用函数  | 计算耗时  |
|:-------------|:------------|:-------|
| 未分区内存表    | `loadText` | 3.69 秒 |
| 顺序分区内存表 | `ploadText` | 2.51 秒 |
| 以sym值分区的内存表 | `loadTextEx` |  0.17 秒 |

### 2.2.3 使用`loadTable`函数导入磁盘分区表的全部或部分分区

这种方法适合下列情况：

* 文本文件比服务器可用内存更大，并且每次只需要用到其中的一部分数据。
* 需要重复使用数据。加载一个数据库表比导入一个文本文件要快得多。

使用`loadTextEx`在磁盘上建立一个分区表：（亦可使用`createPartitionedTable`和`append!`函数）
```
db = database(workDir+"/tradeDB", RANGE, ["A","G","M","S","ZZZZ"])
db.loadTextEx(`trades, `sym, workDir + "/trades.txt");
```

若只需要加载两个分区(["A","G")与["M","S"))到内存时：
```
db = database(workDir+"/tradeDB")
trades=loadTable(db, `trades, ["A", "M"], 1);
```

请注意，这里需要将函数`loadTable`的可选参数memoryMode设为1，否则将只会加载表的元数据。

### 2.2.4 使用`loadTableBySQL`函数导入磁盘分区表指定的行/列

这是最灵活的产生内存分区表的方法，可以使用SQL语句选择磁盘分区表中指定的行/列以载入内存分区表。需与函数`loadTable`结合使用。

```
db = database(workDir+"/tradeDB")
trades=loadTable(db, `trades);

sample=loadTableBySQL(<select * from trades where date between 2000.03.01 : 2000.05.01>);

sample=loadTableBySQL(<select sym, date, price1, qty1 from trades where date between 2000.03.01 : 2000.05.01>);

dates = 2000.01.16 2000.02.14 2000.08.01
st = sql(<select sym, date, price1, qty1>, trades, expr(<date>, in, dates))
sample = loadTableBySQL(st);

colNames =`sym`date`qty2`price2
st= sql(sqlCol(colNames), trades)
sample = loadTableBySQL(st);
```

## 3. 内存表的数据处理

以2.2.3中的分区内存表trades为例，介绍内存表的用法。
```
trades = ploadText(workDir + "/trades.txt");
```

### 3.1 插入数据

可以通过以下方法往内存表中插入数据：

1. SQL insert 语句

```
//往指定列插入数据，其他列为空
insert into trades(sym,date) values(`S,2000.12.31)

//往所有列插入数据
insert into trades values(`S`IBM,[2000.12.31,2000.12.30],[10.0,20.0],[10.0,20.0],[10.0,20.0],[10.0,20.0],[10.0,20.0],[10.0,20.0],[10,20],[10,20],[10,20],[10,20],[10,20],[10,20])

```

2. `append!`函数

如果使用`append!`函数往表中插入数据，新数据必须是以表的形式表示。例如：
```
tmp=table(`S`IBM as col1,[2000.12.31,2000.12.30] as col2,[10.0,20.0] as col3,[10.0,20.0] as col4,[10.0,20.0] as col5,[10.0,20.0] as col6,[10.0,20.0] as col7,[10.0,20.0] as col8,[10,20] as col9,[10,20] as col10,[10,20] as col11,[10,20] as col12,[10,20] as col13,[10,20] as col14)
trades.append!(tmp)
```

3. `tableInsert`函数

`tableInsert`函数会返回插入的行数。

对于分区表，如果使用`tableInsert`函数往表中插入数据，新数据必须是以表的形式表示。
```
tmp=table(`S`IBM as col1,[2000.12.31,2000.12.30] as col2,[10.0,20.0] as col3,[10.0,20.0] as col4,[10.0,20.0] as col5,[10.0,20.0] as col6,[10.0,20.0] as col7,[10.0,20.0] as col8,[10,20] as col9,[10,20] as col10,[10,20] as col11,[10,20] as col12,[10,20] as col13,[10,20] as col14)
trades.tableInsert(tmp)

2
```

对于未分区表，如果使用`tableInsert`函数往表中插入数据，新数据可以用元组的形式表示。
```
a=(`S`IBM,[2000.12.31,2000.12.30],[10.0,20.0],[10.0,20.0],[10.0,20.0],[10.0,20.0],[10.0,20.0],[10.0,20.0],[10,20],[10,20],[10,20],[10,20],[10,20],[10,20])
trades.tableInsert(a)
```

### 3.2 增加列

可以通过以下三种方法为内存表增加列：

1. SQL update 语句

```
update trades set logPrice1=log(price1), newQty1=double(qty1);

```
2. `update!`函数

```
trades.update!(`logPrice1`newQty1, <[log(price1), double(qty1)]>);

```
3. 赋值语句

```
trades[`logPrice1`newQty1] = <[log(price1), double(qty1)]>;
```

### 3.3 更新已存在的列

可以通过以下三种方法为内存表更新列：

1. SQL update 语句

```
update trades set qty1=qty1+10;

update trades set qty1=qty1+10 where sym=`IBM;
```

2. `update!`函数

```
trades.update!(`qty1, <qty1+10>);

trades.update!(`qty1, <qty1+10>, <sym=`IBM>);
```

3. 赋值语句

```
trades[`qty1] = <qty1+10>;

trades[`qty1, <sym=`IBM>] = <qty1+10>;
```

### 3.4 删除行

可以通过以下三种方法为内存表删除行：

1. SQL delete 语句
```
delete from trades where qty3<20;
```

2. `erase!`函数
```
trades.erase!(< qty3<30 >);
```

### 3.5 删除列

通过`drop!`函数删除列：
```
trades.drop!("qty1");
```

### 3.6 重命名列

通过`rename!`函数重命名列：
```
trades.rename!("qty2", "qty2New");
```

### 3.7 查看表结构

通过`schema`函数查看表的结构：
```
schema(trades)

partitionSchema->[XOM,V,TSLA,S,PG,MSFT,IBM,GOOG,GM,FB,...]
partitionSites->
partitionColumnIndex->0
chunkPath->
colDefs->
name   typeString typeInt comment
------ ---------- ------- -------
sym    SYMBOL     17             
date   DATE       6              
price1 DOUBLE     16             
price2 DOUBLE     16             
price3 DOUBLE     16             
price4 DOUBLE     16             
price5 DOUBLE     16             
price6 DOUBLE     16             
qty1   INT        4              
qty2   INT        4              
qty3   INT        4              
qty4   INT        4              
qty5   INT        4              
qty6   INT        4              

partitionType->1
partitionColumnName->sym
```

### 3.8 删除内存表

可以通过以下两种方法删除内存表：

1. `undef`函数

```
undef(`trades)
```

2. 把变量赋值为NULL

```
trades=NULL
```

`undef`函数会将命名空间删除，而把变量赋值为NULL仍然保留命名空间。

### 3.9 修改列的数据类型

通过`replaceColumn!`函数可以修改列的数据类型。目前只有未分区的内存表才支持修改列的数据类型，分区内存表不支持该功能。以未分区的内存表trades为例，将price1的数据类型修改为FLOAT（目前是DOUBLE）：

```
NewPrice1=float(exec price1 from trades)
replaceColumn!(trades,`price1,NewPrice1)
schema(trades)

partitionColumnIndex->-1
chunkPath->
colDefs->
name   typeString typeInt comment
------ ---------- ------- -------
sym    SYMBOL     17             
date   DATE       6              
price1 `FLOAT`      15             
price2 DOUBLE     16             
price3 DOUBLE     16             
price4 DOUBLE     16             
price5 DOUBLE     16             
price6 DOUBLE     16             
qty1   INT        4              
qty2   INT        4              
qty3   INT        4              
qty4   INT        4              
qty5   INT        4              
qty6   INT        4  

```

### 3.10 修改列的顺序

通过`reorderColumns!`函数可以修改列的顺序。目前只有未分区的内存表才支持修改列的数据类型，分区内存表不支持该功能。以未分区的内存表trades为例，将列的顺序调整为sym,date,price6,price5,...,price1,qty6,qty5,...,qty1。

```
reorderColumns!(trades,`sym`date`price6`price5`price4`price3`price2`price1`qty6`qty5`qty4`qty3`qty2`qty1)
```

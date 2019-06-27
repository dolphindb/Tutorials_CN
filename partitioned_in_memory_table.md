# 内存分区数据表使用指南

在DolphinDB中，复合分区以外的所有数据库分区方式都适用于内存数据表。使用分区内存表进行运算能充分发挥多核CPU并行计算的优势。

## 1. 加载数据到内存分区表

DolphinDB提供了多种方法将一个数据集加载到内存分区表。我们首先生成一个数据集，用于后续例子。

```
n=30000000
workDir = "C:/DolphinDB/Data"
if(!exists(workDir)) mkdir(workDir)
trades=table(rand(`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S,n) as sym, 2000.01.01+rand(365,n) as date, 10.0+rand(2.0,n) as price1, 100.0+rand(20.0,n) as price2, 1000.0+rand(200.0,n) as price3, 10000.0+rand(2000.0,n) as price4, 10000.0+rand(3000.0,n) as price5, 10000.0+rand(4000.0,n) as price6, rand(10,n) as qty1, rand(100,n) as qty2, rand(1000,n) as qty3, rand(10000,n) as qty4, rand(10000,n) as qty5, rand(10000,n) as qty6)
trades.saveText(workDir + "/trades.txt");
```

### 1.1 使用`ploadText`函数将文本文件导入为顺序分区表

这是最简单的建立分区内存表的方法，但缺乏其它导入方法的某些优点及灵活性。例如，需要导入的文本文件必须小于可用内存；无法使用函数`sortBy!`进行分区内有意义的排序，等等。

```
trades = ploadText(workDir + "/trades.txt");
```

### 1.2 使用`loadTextEx`函数将文本文件导入为指定分区格式表

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

以下对每一个sym的记录进行分组计算的SQL语句在未分区内存表、1.1中的顺序分区内存表以及本节中的按sym值分区内存表中的执行时间记录在下表中。可以看到，当分组列和分区列相同时，分组计算性能最优。

```
timer(10) select std(qty1) from trades group by sym;
```

这里的 "timer(10)" 指的是此语句被连续执行10次的总耗时。

| 数据表        | 产生时所用函数  | 计算耗时  |
|:-------------|:------------|:-------|
| 未分区内存表    | `loadText` | 3.69 秒 |
| 顺序分区内存表 | `ploadText` | 2.51 秒 |
| 以sym值分区的内存表 | `loadTextEx` |  0.17 秒 |

### 1.3 使用`loadTable`函数导入磁盘分区表全部或部分分区

这种方法适合下列情况：

* 文本文件比服务器可用内存更大，并且每次只需要用到其中的一部分数据。
* 需要重复使用数据。加载一个数据库表比导入一个文本文件要快得多。

使用`loadTestEx`在磁盘上建立一个分区表：（亦可使用`createPartitionedTable`和`append!`函数）
```
db = database(workDir+"/tradeDB", RANGE, ["A","G","M","S","ZZZZ"])
db.loadTextEx(`trades, `sym, workDir + "/trades.txt");
```

若只需要加载两个分区(["A","G")与["M","S"))到内存时：

```
db = database(workDir+"/tradeDB")
trades=loadTable(db, `trades, ["A", "M"], 1);
```

请注意，这里需要将函数`loadTable`的可选参数memoryNode设为1，否则将只会加载表的元数据。

### 1.4 使用`loadTableBySQL`函数导入磁盘分区表指定的行/列

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

### 1.5 相关函数语法

* ploadText(fileName, [delimiter], [schema])
* loadTextEx(dbHandle, tableName, partitionColumns, filename, [delimiter=','], [schema])
* database(directory, [partitionType], [partitionScheme], [locations])
* loadTable(database, tableName, [partitions], [memoryMode=false])
* loadTableBySQL(meta code representing a SQL query)
* sortBy!(table, sortColumns, [sortDirections])
* update!(table, colNames, newValues, [filter])
* drop!(table, colNames)
* erase!(table, filter)
* rename!(table, ColName, newColName)

## 2. 内存分区表数据处理

### 2.1 增加列

```
trades = ploadText(workDir + "/trades.txt");
```
1. SQL `update`语句

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

### 2.2 更新已存在列

1. SQL `update`语句

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

### 2.3 删除行

1. SQL `delete`语句

```
delete from trades where qty3<20;
```

2. `erase!`函数

```
trades.erase!(< qty3<30 >);
```

### 2.4 使用`drop!`函数删除列

```
trades.drop!("qty1");
```

### 2.5 使用`rename!`函数重命名列

```
trades.rename!("qty2", "qty2New");
```

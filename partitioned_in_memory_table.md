### 利用内存数据库修改和分析数据

DolphinDB作为一个一站式的大数据处理引擎，提供了从内存数据库，流数据，到分布式数据仓库等多种产品已满足各种应用场景的需求。本教程介绍如何将DolphinDB作为独立工作站使用，利用内存数据库的高性能，快速完成数据的加载，编辑和分析计算。Pandas目前是数据科学领域广泛使用的工作站软件包。与之相比，DolphinDB为内存数据表提供了灵活的分区机制，能充分发挥多核CPU的优势。

#### 1. 加载数据到内存表
DolphinDB提供了以下四种方法将一个大数据集加载为内存分区表。我们首先生成一个数据集，用于后面的演示。

```
n=10000000
workDir = "C:/DolphinDB/Data"
if(!exists(workDir)) mkdir(workDir)
trades=table(rand(`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S,n) as sym, 2000.01.01+rand(365,n) as date, 10.0+rand(2.0,n) as price1, 100.0+rand(20.0,n) as price2, 1000.0+rand(200.0,n) as price3, 10000.0+rand(2000.0,n) as price4, 10000.0+rand(3000.0,n) as price5, 10000.0+rand(4000.0,n) as price6, rand(10,n) as qty1, rand(100,n) as qty2, rand(1000,n) as qty3, rand(10000,n) as qty4, rand(10000,n) as qty5, rand(10000,n) as qty6)
trades.saveText(workDir + "/trades.txt")
```

#### 1.1 使用ploadText函数将一个文本文件导入为顺序分区的内存分区表

当我们需要导入的文本文件的大小比内存的大小要小时，我们可以使用这种方法。但是，顺序分区表不能用于执行分区内的排序任务。
```
trades = ploadText(workDir + "/trades.txt")
```

#### 1.2 使用loadTextEx函数将一个文本文件导入为指定分区格式的内存分区表
使用这种方法定义数据库时，loadTextEx函数的tableName参数和directory参数请使用空字符串("")。这种方法适合下列情况：
* 分区内排序
* “group by”运算的性能最优化。当分组的列和分区的列相同时，“group by”的性能最优。

```
db = database("", VALUE, `IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S)
trades = db.loadTextEx("", `sym, workDir + "/trades.txt")

// 当分组的列和分区的列相同时，分组运算性能最优。
select std(qty1) from trades group by sym

// 下列的排序操作为分区内排序
trades.sortBy!(`qty1)
trades.sortBy!(`date`qty1, false true)
trades.sortBy!(<qty1 * price1>, false)
```

#### 1.3 使用loadTable函数将磁盘上的分区数据库整个表或者部分分区导入到内存表
将一个分区表加载为内存分区表时，需要将函数的可选参数memoryNode设为1，否则将只会加载表的元数据。

这种方法适合下列情况：
 * 当我们需要使用的文本文件比服务器内存的大小更大，并且每次只需要用到其中的一部分数据时。
 * 需要重复使用相同的数据时。加载一个DolphinDB数据库表比导入一个文本文件要快得多。

有两种方法可以在一个磁盘的分区数据库上创建一个分区数据表：
 * 使用loadTextEx函数
 * 使用createPartitionedTable和append!函数
 
```
// 在磁盘的分区数据库中使用loadTestEx建立一个分区表
db = database(workDir+"/tradeDB", RANGE, ["A","G","M","S","ZZZZ"])
db.loadTextEx(`trades, `sym, workDir + "/trades.txt")

// 当我们需要加载表的部分分区到内存时：
db = database(workDir+"/tradeDB")
trades=loadTable(db, `trades, ["A", "M"], 1)   // load the partitions ["A","G"] and ["M","S"]
```

#### 1.4 使用loadTableBySQL函数将磁盘上的分区数据库导入到内存表

这种方法和第3种方法的适用情况一样。但和第3种方法相比，这种方法更加灵活，可以使用SQL语句选择指定的行和列。

```
db = database(workDir+"/tradeDB")
trades=loadTable(db, `trades)
sample=loadTableBySQL(<select * from trades where date between 2000.03.01 : 2000.05.01>)
sample=loadTableBySQL(<select sym, date, price1, qty1 from trades where date between 2000.03.01 : 2000.05.01>)

dates = 2000.01.16 2000.02.14 2000.08.01
st = sql(<select sym, date, price1, qty1>, trades, expr(<date>, in, dates))
sample = loadTableBySQL(st)

colNames =`sym`date`qty2`price2
st= sql(sqlCol(colNames), trades)
sample = loadTableBySQL(st)
```

#### 1.5 相关函数语法

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


#### 2. 内存分区表数据处理

以下运算可以在任何内存分区表中进行。如果选择在(3)和(4)的内存表中进行运算，请先确认下列运算所需的列在表中都存在。

#### 2.1 在内存表中增加列的三种方法

```
trades = ploadText(workDir + "/trades.txt")

//1 use sql update
update trades set logPrice1= log(price1), newQty1= double(qty1)

//2 use update! function
trades.update!(`logPrice1`newQty1, <[log(price1), double(qty1)]>)

//3 use assignment statement
trades[`logPrice1`newQty1] = <[log(price1), double(qty1)]>
```

#### 2.2 更新已存在列的三种方法
```
//1 use sql update statement
update trades set qty1 = qty1 + 10
update trades set qty1 = qty1 + 10 where sym = `IBM

//2 use update! function
trades.update!(`qty1, <qty1+10>)
trades.update!(`qty1, <qty1+10>, <sym=`IBM>)

//3 use assginment statement
trades[`qty1] = <qty1 + 10>
trades[`qty1, <sym=`IBM>] = <qty1+10>
```

#### 2.3 从内存表中删除行
```
//1 use sql delete statement to delete rows
delete from trades where qty3 <20

//2 use erase! function
trades.erase!(< qty3 <30 >)
```

#### 2.4 删除和重命名列
```
// 使用function删除列 
trades.drop!("qty1")

// 重命名列
trades.rename!("qty2", "qty2New")
```

### DolphinDB数据表详解

DolphinDB按照存储介质的不同，支持三种类型的数据表，内存表(in-memory table)、磁盘表(disk table)和分布式表(DFS table)。磁盘表将数据表存储在本地磁盘上。分布式表将表存储在分布式文件系统上。按照分区与否，数据表又可以分成分区表(在系统中称为 partitioned table 或 segmented table) 和未分区表。下面我们将详细介绍这些表在创建，读写数据，是否支持事务，是否支持并发等方面的异同之处。

### 1. 三种数据表的不同之处

内存表只存在于内存中，写入和查询速度很快，但是数据并不会持久化。通常它在系统运行时作为临时数据载体使用，它使用简单方便，也适合作为新手学习入门使用。内存表支持分区，将内存表进行分区可以更充分的利用计算机并行多线程特性。

磁盘表数据保存在本地磁盘上，数据写入和查询速度要比内存表慢，但是它的优点是即使机器断电或节点关闭，通过脚本就可以将数据重新从磁盘加载到内存。磁盘表支持分区，将磁盘表进行分区可以将表数据切分成小块进行无损压缩并保存磁盘，每次根据分析脚本加载需要的部分，减少内存的占用；同时也可以更充分的利用计算机并行多线程特性。

分布式表的数据分布在不同的节点的磁盘上，通过DolphinDB的分布式计算引擎，逻辑上仍然可以像本地表一样做统一查询。要将数据保存在分布式系统中，将数据进行切分是一个前提，所以分布式表必须进行分区，系统不支持创建未分区的分布式数据库。分布式表的优点是支持集群，支持横向扩展。通过DolphinDB的分布式文件系统，分布式计算引擎将多机器多节点上的数据进行统一的协调调度和分析计算，使得整个系统可以处理的数据量可以无限扩展，而不会受限于单服务器磁盘容量和内存容量的限制。

下表列出这三种类型的数据表的适用场景
表类型 | 适用场景
---|---
内存表| 临时数据载体，学习入门
磁盘表| 单用户静态数据集分析
分布式表| 团队开发，多用户并发读写

### 2. 创建数据表
创建数据表，会涉及到分区概念(具体分区概念请参考[数据分区教程](https://github.com/dolphindb/Tutorials_CN/blob/master/database.md)），分区会影响到数据的存储分布和处理的并行度，下面按照三种类型的表结合分区和未分区的情况来做示例：

### 2.1 创建内存表

- 未分区内存表

要创建一个内存表，需要使用table函数创建，比如下面的脚本创建一个表，包含两个字段id,name,第一个参数`1000:0`代表初始空间和初始下标。初始空间表示创建表时的预留空间，当数据行数少于预留空间时，新增数据不需要重新分配空间，执行会非常高效。直到数据行数超出初始空间后，系统会为每次新增数据动态分配空间。
```
t = table(1000:0, `id`name, [INT,STRING])
```
- 内存分区表
要对数据表进行分区，必须将表纳入某一个分区数据库中，示例如下，将表按照id进行分区，按照1到100，每个id值分一个区。`database`的第一个路径参数留空表示内存分区数据库：
```
t = table(1000:0, `id`name, [INT,STRING])
db=database(,VALUE,1..100)
db.createPartitionedTable(t,`partitionedTable1,`id)

```
### 2.2 创建磁盘表
- 未分区磁盘表

磁盘表的建立也需要依赖于数据库，首先创建磁盘数据库，然后将表加入到数据库中，示例代码如下：
```
dbPath = "/home/user1/mydb"
t = table(1000:0, `id`name, [INT,STRING])
db=database(dbPath)
db.saveTable(t,`diskTable1)

```

- 磁盘分区表

创建磁盘分区表与创建内存分区表的唯一区别是指定一个磁盘路径。
```
dbPath = "/home/user1/mydb"
t = table(1000:0, `id`name, [INT,STRING])
db=database(dbPath, VALUE, 1..100)
db.createPartitionedTable(t,`partitionedTable1,`id)

```
### 2.3 创建分布式表

创建分布式分区表与磁盘分区表基本方式是一致的，区别在于分布式表需要指定分布式路径`dfs://`。
```
dbPath = "dfs://mydb"
t = table(1000:0, `id`name, [INT,STRING])
db=database(dbPath, VALUE, 1..100)
db.createPartitionedTable(t,`partitionedTable1,`id)

```
### 3. 操作数据

### 3.1 读取数据
系统提供了`loadTable`来加载表数据，针对磁盘表或分布式表，根据分区或不分区的情况，loadTable的表现有少许不同。
- 未分区磁盘表：未分区磁盘表是用于学习演练或小数据量分析使用，所以当使用`loadTable`来加载未分区磁盘表时，会全量加载到内存。
- 分区磁盘表：分区磁盘表通常是针对大数据量的单用户分析场景，工作机内存是无法一次性加载所有数据的，所以直接调用`loadTable`来加载数据并不会直接加载所有数据，只会加载数据表结构元数据到内存中，后续根据具体的Query语句按需加载分区数据。虽然说分区表
- 分区分布式表：分布式表是为多用户同时分析大数据集场景而设计的，所以`loadTable`也只会加载数据表结构元数据，与磁盘分区表不同的是，系统会缓存已加载的表结构元数据，供多用户使用。
加载数据脚本示例
```
//本地磁盘表
tb = loadTable("/home/diskDB",`table1)
//分布式表
tb = loadTable("dfs://dfsDB",`table1)
```
### 3.2 写入数据
数据表的更新和删除是比较常见的场景，为了保障对海量数据的分析性能，DolphinDB对不同类型表的更新和删除行为做了控制。

下表简单展示了各种类型数据表在写数据方便的异同点

table类型 | 是否支持修改删除 | Append!是否直接落盘
---|---|---
内存表-未分区-不共享| 是|
内存表-未分区-共享| 是|
内存表-分区-不共享| 是|
内存表-分区-共享| 否|
流数据表 | 否|
磁盘表-未分区| 是 | 更新内存，不更新磁盘
磁盘表-分区| 否 | 更新磁盘，不更新内存
分布式表-分区| 否|更新磁盘，内存数据动态加载

### 3.2.1 内存表

向内存表写入数据可以使用SQL语句，也可以使用`tableInsert`函数和`append!`函数。

使用SQL语句来追加数据：
```
insert into table1 values(1,'tom')
//使用insert直接批量插入数据
insert into table1 value(1..100,take(`tom`jason`bob,100))
```
使用 [`tableInsert`](http://www.dolphindb.com/cn/help/tableInsert.html) 函数追加数据：
```
t = table(1000:0, `id`name, [INT,STRING])
ids = 1..100
names = take(`tom`jason`bob,100)
//接受tuple类型的数据
tableInseret(t,[ids,names])
//接受table类型的数据
data = table(ids as id,names as name)
tableInseret(t,data)
```

使用`append!`函数追加数据：
```
t = table(1000:0, `id`name, [INT,STRING])
data = table(1..100 as id,take(`tom`jason`bob,100) as name)
t.append!(data)
```
内存表除了追加数据，也可以更新和删除数据：
- update语句修改
```
update table1 set name = 'value' where id=1
```
- delete删除
```
delete from table1 where id =1
```
- 直接访问修改，除了用sql语句之外，内存表可以直接访问列进行修改
```
t = table(1000:0, `id`name, [INT,STRING])
t1 = select * from t where id = 2
t1[`name] = 'Tom'
```
### 3.2.2 磁盘表

磁盘表的设计场景是用于单用户的静态大数据集分析，当数据集规模不大，可以全部载入内存的话，那么可以采用不分区的磁盘表；如果数据集规模较大，可以采用分区磁盘表，系统每次会根据分析脚本自动选择需要的分区数据加载到内存，在分区的情况下，系统会充分使用多线程并行操作来加快速度。

磁盘表写入数据使用`append!`函数，而分区和未分区的磁盘表在写入时，表现并不相同，这是由于对使用场景做了针对性设计。

- 未分区表写入数据，当对未分区的表写入数据时，由于未分区的磁盘表是整体载入内存进行操作，所以当对未分区表`append!`进行写入时，数据是直接写入到内存，并不会实时更新到磁盘，要更新磁盘需要调用`saveTable`。
```
t = table(1000:0, `id`name, [INT,STRING])
db  = database("/home/hduser1/llin/mydb")
db.saveTable(t,`unPartitionedTable)

tb = loadTable(db,`unPartitionedTable)
data = table(1..100 as id,take(`tom`jason`bob,100) as name)
tb.append!(data)

select count(*) from tb //=100,此时内存表中已经追加数据
select count(*) from loadTable(db,`unPartitionedTable) //=0，数据还未落盘
//数据落盘
db.saveTable(tb,`unPartitionedTable)
```
- 分区磁盘表是针对全量存盘、部分载入内存分析的场景而设计的，所以使用`append!`函数追加数据到分区磁盘表时，数据直接落盘。当对磁盘表执行分析语句时，更新的数据会按需载入内存。
```
t = table(1000:0, `id`name, [INT,STRING])
db  = database("/home/user1/mydb1",VALUE,1..100)
db.createPartitionedTable(t,`partitionedTable,`id)

tb = loadTable(db,`partitionedTable)
data = table(1..100 as id,take(`tom`jason`bob,100) as name)
tb.append!(data)
select count(*) from tb //=0，内存中未载入数据
select count(*) from loadTable(db,`partitionedTable) //=100，数据已经落盘
```
### 3.2.3 向分布式表写入数据
分布式表要求数据分布式存储，所以不存在不分区的情况，每个分布式表都要分区。当往分布式表写数据时，系统使用分布式事务保障分布式数据的一致性。在追加数据时，分布式表和磁盘表不同的是，数据会同时落盘并载入内存。
```
t = table(1000:0, `id`name, [INT,STRING])
db  = database("dfs://mydfsdb",VALUE,1..100)
db.createPartitionedTable(t,`dfsPartitionedTable,`id)

tb = loadTable(db,`dfsPartitionedTable)
data = table(1..100 as id,take(`tom`jason`bob,100) as name)
tb.append!(data)
select count(*) from tb //=100
select count(*) from loadTable(db,`dfsPartitionedTable) //=100
```
分布式数据表当前不支持单条数据或指定记录的精确删除和更新，需要定期清理数据，可以使用`dropPartition`命令来删除指定分区；若要更新部分数据，可以按如下思路以分区粒度进行更新:
比如要更新的分区路径为`/mydfsdb/20180111`
- 取出指定分区的完整数据形成内存表
- 使用update语句对内存表做更新操作
- dropPartition("/mydfsdb/20180111")
- 使用`append!`函数将更新完成的内存表重新追加到表

假设数据库是按照日期每天分一个区，那么要更新某一天的数据的指定数据，示例脚本如下：
```
db  = database("dfs://mydfsdb",VALUE,2018.11.01..2018.11.31)
//取出指定分区的完整数据形成内存表
updateData = select * from loadTable("dfs://mydfsdb",`dfsPartitionedTable) where date = 2018.01.11
//更新指定数据，省略update语句
...
//删除分区
dropPartition("/mydfsdb/20180111")
//将更新数据更新回数据表
db.loadTable(`dfsPartitionedTable).append!(updateData)
```
### 4. 并发性比较

从设计上来看，分布式表是为了团队多用户场景设计的，在多用户并发性上有更多针对性设计，它支持快照级别的事务隔离，在单个最小分区的数据级别，可以实现一写多读。从整表层面，在避免同时写单一分区的前提下，支持多用户的并发读写。

而磁盘表是为单用户分析静态数据集的场景设计，静态数据集可以支持多用户同时读取和分析，但是不保证写入的同时读取数据的一致性和完整性。

内存表根据会话隔离，所以并不存在并发的情况。系统提供`share`关键字可以将内存表共享，可以由不同的会话访问，此时共享内存表可以提供多用户并发读写。

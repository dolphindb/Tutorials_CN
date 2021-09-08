# DolphinDB数据表详解

DolphinDB database 按照存储介质的不同，支持三种类型的数据表，内存表(in-memory table)、磁盘表(disk table)和分布式表(DFS table)。磁盘表将数据表存储在本地磁盘上。分布式表将表存储在分布式文件系统上。按照分区与否，数据表又可以分成分区表(在系统中称为 partitioned table 或 segmented table) 和未分区表。下面我们将详细介绍这些表在创建，读写数据，是否支持事务，是否支持并发等方面的异同之处。

本文的例子中使用了两个数据文件：[sample.csv](data/sample.csv)和[sample.bin](data/sample.bin)。

## 1. 三种数据表的不同之处

内存表只存在于内存中，写入和查询速度很快，但是数据并不会持久化。通常它在系统运行时作为临时数据载体使用，它使用简单方便，也适合作为新手学习入门使用。内存表支持分区，将内存表进行分区可以更充分的利用计算机并行多线程特性。

磁盘表数据保存在本地磁盘上，数据写入和查询速度要比内存表慢，但是它的优点是即使机器断电或节点关闭，通过脚本就可以将数据重新从磁盘加载到内存。磁盘表支持分区，将磁盘表进行分区可以将表数据切分成小块进行无损压缩并保存磁盘，每次根据分析脚本加载需要的部分，减少内存的占用；同时也可以更充分的利用计算机并行多线程特性。

分布式表的数据分布在不同的节点的磁盘上，通过DolphinDB的分布式文件系统仍然可以像本地表一样做统一查询。要将数据保存在分布式系统中，将数据进行切分是一个前提，所以分布式表必须进行分区，系统不支持创建未分区的分布式数据库。分布式表的优点是支持集群，支持横向扩展。通过DolphinDB的分布式文件系统，分布式计算引擎将多机器多节点上的数据进行统一的协调调度和分析计算，使得整个系统可以处理的数据量可以无限扩展，而不会受限于单服务器磁盘容量和内存容量的限制。

下表列出这三种类型的数据表的适用场景

表类型 | 适用场景
---|---
内存表| 临时数据载体，学习入门
磁盘表| 单用户静态数据集分析
分布式表| 团队开发，多用户并发读写

## 2. 创建数据表

创建数据表，会涉及到分区概念(具体分区概念请参考[数据分区教程](https://github.com/dolphindb/Tutorials_CN/blob/master/database.md)），分区会影响到数据的存储分布和处理的并行度，下面按照三种类型的表结合分区和未分区的情况来做示例：

### 2.1 创建内存表

#### 2.1.1 未分区内存表

未分区内存表（以下简称内存表）通常在系统运行时作为临时数据载体使用，各种查询语句与计算函数返回的结果都以内存表的形式返回，因此在DolphinDB中，创建内存表的方式也相对丰富，主要可以通过以下3种方式创建内存表：

- `table`函数创建内存表
- `loadText`和`loadRecord`方法返回内存表
- SQL查询返回内存表

下面分别给出通过这3种方式创建内存表的示例。

**(1) `table`函数创建内存表**

在DolphinDB中，使用[table](https://www.dolphindb.cn/cn/help/table.html)函数可以创建一个未分区的内存表。`table`函数主要有两种用法，具体示例如下。

- 使用向量、矩阵或者元组创建表

  如下所示，使用向量x，矩阵y和元组z创建一个内存表。

  ```
  >x=1..6
  y=11..22$6:2
  z=(101..106, 201..206)
  t=table(x,y,z)
  t.rename!(`x`y1`y2`z1`z2);
  >t;
  x y1 y2 z1  z2 
  - -- -- --- ---
  1 11 17 101 201
  2 12 18 102 202
  3 13 19 103 203
  4 14 20 104 204
  5 15 21 105 205
  6 16 22 106 206
  ```
  
  > 请注意，创建表时所使用的元素（向量、矩阵或元组）长度都必须相同。

- 指定表的结构创建表

  如下所示，通过指定表的容量、初始大小、列名以及列的数据类型来初始化表。例子使用`table`函数创建表，指定列名为id和name，列的数据类型分别是INT和STRING。其中，第一个参数取值为“1000:0”，代表初始空间和初始下标。初始空间表示创建表时的预留空间，当数据行数少于预留空间时，新增数据不需要重新分配空间，执行会非常高效。直到数据行数超出初始空间后，系统会为每次新增数据动态分配空间。 

  ```
  >t=table(1000:0, `id`name, [INT,STRING]);
  ```

**(2) `loadText`和`loadRecord`方法返回内存表**

在DolphinDB中，可以通过[loadText](https://www.dolphindb.cn/cn/help/loadText.html)，[loadRecord](https://www.dolphindb.cn/cn/help/loadRecord.html)等方法导入数据文件，数据导入到DolphinDB后，以内存表的形式存储。

下面的例子使用了两个文件：sample.csv和sample.bin。例子中的"YOUR_DIR"为存放数据文件的路径。

sample.csv包含id和price两个字段，下面通过`loadText`函数将该文件导入到DolphinDB，存放在t_csv表中。下例中，t_csv表就是一个内存表。

```
>t_csv=loadText(YOUR_DIR+"sample.csv");
>t_csv;
id price    
-- ---------
1  38.959012
2  30.2263  
3  58.125723
4  59.340818
5  36.449339
6  81.542495
7  82.127893
8  41.231077
9  35.615633
10 83.113151
...
```

sample.bin为一个二进制文件，包含id和price两个字段。下面通过`loadRecord`函数将该二进制文件导入到DolphinDB，存放在t_bin中。下例中，t_bin也是一个内存表。

```
>schema=[("id", INT),("price",DOUBLE)];
t_bin=loadRecord(YOUR_DIR+"sample.bin",schema);
>t_bin;
id price    
-- ---------
1  38.959012
2  30.2263  
3  58.125723
4  59.340818
5  36.449339
6  81.542495
7  82.127893
8  41.231077
9  35.615633
10 83.113151
...
```

**(3) SQL查询返回内存表**

在DolphinDB中，所有涉及对表（包括内存表、磁盘表和分布式表）进行的查询操作，返回的查询结果均是内存表。

例如，使用SQL语句查询[分布式表](#23-创建分布式表)的数据，符合查询条件的记录会被加载到内存，保存在内存表中。

> 请注意，只有启用enableDFS=1的集群环境或者DolphinDB单例模式才能使用分布式表。

首先创建一个分布式数据库"dfs://dolphindbDatabase"和表"partitionedTable1"，并向分布式表中追加tdata中的数据。

```
>login(`admin, `123456)
dbPath="dfs://dolphindbDatabase"
n=5000
tdata=table(take(1..100,n) as id, rand(`Alice`Betty`Cargo, n) as name, rand(100.5,n) as price)
db=database(dbPath, VALUE, 1..100)
tb=db.createPartitionedTable(tdata,`partitionedTable1,`id)
tb.append!(tdata);
```

查询名为Alice的所有记录，查询返回一个内存表，使用t_result来保存该内存表。由于数据是随机生成的，以下输出结果仅供参考。

```
>t_result=select * from loadTable("dfs://dolphindbDatabase", `partitionedTable1) where name="Alice";
>t_result;
id name  price    
-- ----- ---------
1  Alice 15.622302
1  Alice 61.98541 
1  Alice 19.394159
1  Alice 92.481627
1  Alice 12.179253
1  Alice 36.858704
1  Alice 26.014262
1  Alice 50.697725
1  Alice 31.491535
1  Alice 74.167275
```

#### 2.1.2 内存分区表

在DolphinDB中，主要可以通过`createPartitionedTable`函数和`ploadText`函数创建内存分区表。
 
- `createPartitionedTable`函数创建内存分区表

要对数据表进行分区，必须将表纳入某一个分区数据库中，在使用`database`函数创建数据库时，第一个路径参数留空表示内存分区数据库。下面给出使用`createPartitionedTable`函数创建内存分区表的2个例子。

**示例1**

使用一个内存表创建内存分区表：首先创建内存分区数据库，分区方案为值分区，取值范围为从1至100，然后调用`createPartitionedTable`函数创建内存分区表，按照字段id进行分区，每个id值分一个区。

```
>t=table(1000:0, `id`name, [INT,STRING])
db=database(,VALUE,1..100)
tb=createPartitionedTable(db, t,`partitionedTable1,`id);
```

**示例2**

使用一系列内存表创建内存分区表：首先创建内存分区数据库，分区方案为范围分区，范围包含下限不包含上限。然后创建两个表tdata1和tdata2，最后调用`createPartitionedTable`函数创建内存分区表tb，按照字段name进行分区，一共分为2个分区。

```
>n=4
db=database(, RANGE, `A`C`E)
tdata1=table(take(1..4,n) as id, rand(`Alice`Betty`Cargo`Danny, n) as name, rand(100.5,n) as price)
tdata2=table(take(1..4,n) as id, rand(`Alice`Bob`Catty`Daniel, n) as name, rand(100.5,n) as price)
tb=createPartitionedTable(db, [tdata1, tdata2], `partitionedTable1, `name);
>select * from tb;
id name  price    
-- ----- ---------
1  Betty 68.287133
2  Alice 22.588541
3  Betty 76.211358
4  Betty 61.07317 
1  Alice 85.087942
2  Bob   22.76464 
3  Bob   97.104663
4  Catty 44.58062 
```

> 请注意，使用一系列内存表创建内存分区表时，一系列表的个数需要与分区数相同，且这些表的结构也应一致。

- `ploadText`函数导入数据到内存分区表

通过`ploadText`函数导入数据，数据将并行导入到内存中，返回的是一个内存分区表。下面的例子使用`ploadText`函数导入sample.csv文件，例子中的"YOUR_DIR"为存放数据文件的路径。

```
>tb=ploadText(YOUR_DIR+"sample.csv")
```

### 2.2 创建磁盘表

- 未分区磁盘表

磁盘表的建立也需要依赖于数据库，首先创建磁盘数据库，然后将表保存到数据库中，示例代码如下：
```
>dbPath="/home/dolphindb/database/mydbd"
n=10000
t=table(take(1..100,n) as id, rand(`Alice`Betty`Cargo`Danny, n) as name)
db=database(dbPath)
db.saveTable(t,`diskTable1);
```

- 磁盘分区表

创建磁盘分区表与创建内存分区表的唯一区别是：磁盘分区表需要指定一个磁盘路径。
```
>login(`admin, `123456)
dbPath="/home/dolphindb/database/mydbp"
n=10000
tdata=table(take(1..100,n) as id, rand(`Alice`Betty`Cargo`Danny, n) as name)
db=database(dbPath, VALUE, 1..100)
db.createPartitionedTable(t,`partitionedTable1,`id).append!(tdata);
```

### 2.3 创建分布式表

- 创建维度表

维度表是分布式数据库中没有分区的表，一般用于存储不频繁更新的小数据集。我们可以使用`createTable`函数来创建维度表。

下面的例子中，使用`database`函数创建数据库，指定数据库路径为"dfs://dimensionDB"。需要注意的是，维度表的数据不以分区方式存储，因此这里与分区相关的参数partitionType和partitionScheme无效。然后调用`createTable`函数创建维度表，并追加数据。
```
>login(`admin, `123456)
db=database("dfs://dimensionDB",RANGE, 1 2)
n=10000
tdata=table(take(1..4,n) as id, rand(`Alice`Betty`Cargo`Danny, n) as name, rand(100.5,n) as price)                   
dt=db.createTable(tdata,`dt).append!(tdata);
```

- 创建分布式表

创建分布式分区表与磁盘分区表基本方式是一致的，区别在于分布式表需要指定分布式路径"dfs://"。
```
>login(`admin, `123456)
dbPath="dfs://dolphindbDatabase"
n=10000
tdata=table(take(1..4,n) as id, rand(`Alice`Betty`Cargo`Danny, n) as name, rand(100.5,n) as price)        
db=database(dbPath, VALUE, 1..100)
tb=db.createPartitionedTable(tdata,`partitionedTable1,`id).append!(tdata);
```

## 3. 操作数据

### 3.1 读取数据

#### 3.1.1 使用`loadTable`加载表数据

系统提供了[loadTable](https://www.dolphindb.cn/cn/help/loadTable.html)来加载表数据，针对磁盘表或分布式表，根据分区或不分区的情况，`loadTable`的表现有少许不同。

- 未分区磁盘表：未分区磁盘表是用于学习演练或小数据量分析使用，所以当使用`loadTable`来加载未分区磁盘表时，会全量加载到内存。

- 分区磁盘表：分区磁盘表通常是针对大数据量的单用户分析场景，工作机内存是无法一次性加载所有数据的，所以直接调用`loadTable`来加载数据并不会直接加载所有数据，只会加载数据表结构元数据到内存中，后续根据具体的Query语句按需加载分区数据。

- 分区分布式表：分布式表是为多用户同时分析大数据集场景而设计的，所以`loadTable`也只会加载数据表结构元数据，与磁盘分区表不同的是，系统会缓存已加载的表结构元数据，供多用户使用。

- 维度表：维度表是分布式数据库中没有分区的表，一般用于存储不频繁更新的小数据集。由于维度表也是分布式表，因此调用`loadTable`来加载数据并不会直接加载所有数据，只会加载数据表结构元数据到内存中。

加载数据脚本示例

- 加载磁盘表

加载[第2节](#22-创建磁盘表)中创建的未分区磁盘表：

```
//未分区磁盘表
>tb=loadTable("/home/dolphindb/database/mydbd", `diskTable1);
>tb;
id name 
-- -----
1  Cargo
2  Cargo
3  Cargo
4  Alice
5  Alice
...

>select count(*) from tb;
count
-----
10000
```

加载[第2节](#22-创建磁盘表)中创建的磁盘分区表,由于是按照id进行分区，因此在加载磁盘分区的数据时，数据按照id的取值递增输出：

```
//磁盘分区表
>tb=loadTable("/home/dolphindb/database/mydbp", `partitionedTable1);
>tb;
id name 
-- -----
1  Danny
1  Betty
1  Betty
1  Betty
1  Danny
...

>select count(*) from tb;
count
-----
10000
```

- 加载分布式表

加载[第2节](#23-创建分布式表)中创建的分布式分区表，由于分布式表不允许直接访问，因此需要通过SQL语句选择数据：

```
//分布式分区表
>tb=loadTable("dfs://dolphindbDatabase", `partitionedTable1);
>select * from tb;
id name  price    
-- ----- ---------
1  Cargo 89.770549
1  Danny 17.467475
1  Alice 49.183698
1  Danny 18.397749
1  Cargo 67.743099
...

>select count(*) from tb;
count
-----
10000
```

加载[第2节](#23-创建分布式表)中创建的维度表：

```
//维度表
>tb=loadTable("dfs://dimensionDB", `dt);
>select * from tb;
id name  price    
-- ----- ---------
1  Alice 64.557855
2  Alice 20.694495
3  Cargo 28.921734
4  Betty 82.949798
1  Danny 98.370399

>select count(*) from tb;
count
-----
10000
```

#### 3.1.2 使用`loadTableBySQL`加载表数据

DolphinDB还提供了[loadTableBySQL](https://www.dolphindb.cn/cn/help/loadTableBySQL.html)函数，用于将分区表中满足SQL查询的记录行加载到内存中。返回的是分区的内存表。需要注意的是，`loadTableBySQL`函数只能对分区表使用，且对于磁盘分区表和分布式表，需要先通过`loadTable`函数获得分区表结构的元数据，再使用`loadTableBySQL`函数进行查询。

- 加载内存分区表

```
>n=1000
t=table(take(1..100,n) as id, rand(`Alice`Betty`Cargo`Danny, n) as name, rand(100.5,n) as price)
db=database(,VALUE,1..100)
tb=createPartitionedTable(db, t,`partitionedTable1,`id).append!(t);
sample=select * from loadTableBySQL(<select * from tb where id between 50:60>);
>sample;
id name  price    
-- ----- ---------
50 Danny 94.986752
50 Cargo 9.580574 
50 Cargo 49.542103
50 Danny 41.396863
50 Betty 69.838291
...
```

- 加载磁盘分区表

加载[第2节](#22-创建磁盘表)中创建的磁盘分区表：
```
>tb=loadTable("/home/dolphindb/database/mydbp", `partitionedTable1)
sample=select * from loadTableBySQL(<select * from tb where id between 50:60>);
>sample;
id name 
-- -----
50 Alice
50 Cargo
50 Betty
50 Alice
50 Betty
...
```

- 加载分布式表

下面的例子使用[sql](https://www.dolphindb.cn/cn/help/sql1.html)函数创建SQL语句，再通过`loadTableBySQL`函数加载[第2节](#23-创建分布式表)中创建的分布式表。

```
>tb=loadTable("dfs://dolphindbDatabase", `partitionedTable1)
st=sql(<select *>, tb, expr(<name>, in, `Cargo`Alice))
sample=select * from loadTableBySQL(st);
>sample;
id name  price    
-- ----- ---------
1  Cargo 89.770549
1  Alice 49.183698
1  Cargo 67.743099
1  Alice 5.747787 
1  Alice 62.065592
...
```

### 3.2 写入数据

数据表的更新和删除是比较常见的场景，为了保障对海量数据的分析性能，DolphinDB对不同类型表的更新和删除行为做了控制。

下表简单展示了各种类型数据表在写数据方面的差异

table类型 | 是否支持修改删除 | Append!是否直接落盘
---|---|---
未分区内存表| 是|-
分区内存表| 是|-
共享分区内存表| 否|-
流数据表 | 否|-
未分区磁盘表-| 是 | 更新内存，不更新磁盘，需要saveTable保存到磁盘
分区磁盘表| 否 | 更新磁盘，不更新内存，读取最新数据需要重新loadTable
分布式表| 否|更新到分布式文件系统，读取数据按需动态加载，无需重新loadTable

#### 3.2.1 向内存表写入数据

向内存表写入数据可以使用SQL语句，也可以使用[tableInsert](http://www.dolphindb.cn/cn/help/tableInsert.html)函数和[append!](https://www.dolphindb.cn/cn/help/append1.html)函数。

使用SQL语句来追加数据：

```
table1=table(1000:0, `id`name, [INT,STRING])
//使用insert插入单条数据
insert into table1 values(1,'tom')
//使用insert插入批量数据
insert into table1 values(1..100,take(`tom`jason`bob,100))
//使用insert指定列名插入单条数据
insert into table1(id) values(1)
//使用insert指定列名插入批量数据
insert into table1(name,id) values(take(`tom`jason`bob,100),1..100)
```

使用`tableInsert`函数追加数据：

```
t=table(1000:0, `id`name, [INT,STRING])
ids=1..100
names=take(`tom`jason`bob,100)
//接受tuple类型的数据
tableInseret(t,[ids,names])
//接受table类型的数据
data=table(ids as id,names as name)
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

- 直接访问修改

除了用SQL语句之外，内存表可以直接访问列进行修改
```
t = table(1000:0, `id`name, [INT,STRING])
t1 = select * from t where id = 2
t1[`name] = 'Tom'
```

#### 3.2.2 向磁盘表写入数据

磁盘表的设计场景是用于单用户的静态大数据集分析，当数据集规模不大，可以全部载入内存的话，那么可以采用不分区的磁盘表；如果数据集规模较大，可以采用分区磁盘表，系统每次会根据分析脚本自动选择需要的分区数据加载到内存，在分区的情况下，系统会充分使用多线程并行操作来加快速度。

磁盘表写入数据使用`append!`函数，而分区和未分区的磁盘表在写入时，表现并不相同，这是由于对使用场景做了针对性设计。

- 向未分区磁盘表写入数据

当对未分区的表写入数据时，由于未分区的磁盘表是整体载入内存进行操作，所以当对未分区表`append!`进行写入时，数据是直接写入到内存，并不会实时更新到磁盘，要更新磁盘需要调用`saveTable`。
```
t = table(1000:0, `id`name, [INT,STRING])
db  = database("/home/dolphindb/database/mydb")
db.saveTable(t,`unPartitionedTable)

tb = loadTable(db,`unPartitionedTable)
data = table(1..100 as id,take(`tom`jason`bob,100) as name)
tb.append!(data)

select count(*) from tb //=100,此时内存表中已经追加数据
select count(*) from loadTable(db,`unPartitionedTable) //=0，数据还未落盘
//数据落盘
db.saveTable(tb,`unPartitionedTable)
select count(*) from loadTable(db,`unPartitionedTable) //=100，重新加载该磁盘表数据，数据已经写入磁盘表
```

- 向磁盘分区表写入数据

分区磁盘表是针对全量存盘、部分载入内存分析的场景而设计的，所以使用`append!`函数追加数据到分区磁盘表时，数据直接落盘。当对磁盘表执行查询语句时，更新的数据会按需载入内存。
```
t = table(1000:0, `id`name, [INT,STRING])
db  = database("/home/dolphindb/database/mydb1",VALUE,1..100)
db.createPartitionedTable(t,`partitionedTable,`id)

tb = loadTable(db,`partitionedTable)
data = table(1..100 as id,take(`tom`jason`bob,100) as name)
tb.append!(data)
select count(*) from tb //=0，内存中未载入数据
select count(*) from loadTable(db,`partitionedTable) //=100，数据已经落盘
```

#### 3.2.3 向分布式表写入数据

分布式表要求数据分布式存储，所以不存在不分区的情况，每个分布式表都要分区。当往分布式表写数据时，系统使用分布式事务保障分布式数据的一致性。在追加数据时，分布式表和磁盘表不同的是，数据在落盘的同时也会载入内存，不需要重新加载一次。

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

假设要更新的分区路径为`/mydfsdb/20180111`

1. 取出指定分区的完整数据形成内存表
2. 使用update语句对内存表做更新操作
3.  dropPartition("/mydfsdb/20180111")
4. 使用`append!`函数将更新完成的内存表重新追加到表

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

## 4. 并发性比较

从设计上来看，分布式表是为了团队多用户场景设计的，在多用户并发性上有更多针对性设计，它支持快照级别的事务隔离，在单个最小分区的数据级别，可以实现一写多读。从整表层面，在避免同时写单一分区的前提下，支持多用户的并发读写。

而磁盘表是为单用户分析静态数据集的场景设计，静态数据集可以支持多用户同时读取和分析，但是不保证写入的同时读取数据的一致性和完整性。

内存表根据会话隔离，所以并不存在并发的情况。系统提供[share](https://www.dolphindb.cn/cn/help/Share.html)关键字可以将内存表共享，可以由不同的会话访问，此时共享内存表可以提供多用户并发读写。

例如，将内存表"t"共享为t_global，则多个会话都能够访问t_global：
```
>t = table(1..5 as id, 1..5*2.5 as value)
share t as t_global;
>t_global;
id value
-- -----
1  2.5  
2  5    
3  7.5  
4  10   
5  12.5 

//向t_global中插入数据，数据也会被插入到t中；
>insert into t_global values(6..8, 1..3*4.5);
>t;
id value
-- -----
1  2.5  
2  5    
3  7.5  
4  10   
5  12.5 
6  4.5  
7  9    
8  13.5 
```

若需要取消定义该共享变量，使用[undef](https://www.dolphindb.cn/cn/help/undef.html)函数:

```
>undef(`t_global,SHARED); 
```
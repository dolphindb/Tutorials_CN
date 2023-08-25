# TSDB 存储引擎介绍

本文介绍 DolphinDB 在2.0版本中新推出的存储引擎 TSDB。

## 1. OLAP 与 TSDB 适用的场景

OLAP 是 DolphinDB 在2.0版本之前的唯一存储引擎。数据表中每个分区的每一列存为一个文件。数据在表中的存储顺序与数据写入的顺序一致，数据写入有非常高的效率。

OLAP 引擎的主要局限有以下几点：

(1) 分区内不支持索引，即使只是检索几行数据，也必须加载整个分区（的相关列）。

(2) 写入过程设计简单，不支持去重；

(3) 不适合几百几千列的宽表存储。

(4) 即使修改一条记录，也必须重写整个分区。

TSDB 是 DolphinDB 基于 LSM 树自研的新的存储引擎。它很好的克服了 OLAP 引擎的局限，功能更加全面。每一个分区的数据写在一个或多个 level file 中。每一个 level file 内部的数据按照指定的列进行排序且创建块索引。

TSDB 引擎具有以下优点：

(1) 过滤条件使用分区列以及分区内排序字段的点查询非常高效。

(2) 可以在写入时对数据进行排序和去重。

(3) 适合存储几百几千列的宽表，也适合存储 array vector 和 BLOB 类型的数据。

(4) 若指定去重时保留最后一条记录（设置 keepDuplicates=LAST），则修改数据时重写数据所在 level file 即可，不需要重写整个分区。

与 OLAP 引擎相比，TSDB 引擎的不足之处在于：

(1) 写入吞吐量低。TSDB 引擎中，数据需在 cache engine 中进行排序；level file 会进行合并与压缩。

(2) 读取整个分区数据或整个分区的某几列数据时，效率低于 OLAP。

下面通过一个例子来解释 OLAP 与 TSDB 引擎适合的 query。假设数据表 t 按照股票代码与交易日进行 COMPO 分区。以下是该数据表中的4行数据：

| StockID | Timestamp           | Bid  |
| ------- | ------------------- | ---- |
| AAPL    | 2021.08.05T09:30:00 | 1.5  |
| MSFT    | 2021.08.05T09:30:00 | 1.3  |
| AAPL    | 2021.08.05T09:31:00 | 1.6  |
| GOOG    | 2021.08.05T09:31:00 | 1.4  |
|......   |......               |......|

OLAP 存储引擎的建库建表脚本如下：

```
dbTime = database("", VALUE, 2021.08.01..2021.09.01)
dbStockID = database("", HASH, [SYMBOL, 100])

db = database(directory="dfs://stock",partitionType=COMPO,partitionScheme=[dbTime,dbStockID],engine="OLAP")

schema = table(1:0, `Timestamp`StockID`bid, [TIMESTAMP, SYMBOL, DOUBLE])
stocks = db.createPartitionedTable(table=schema, tableName=`stocks, partitionColumns=`Timestamp`StockID)
```

TSDB 存储引擎的建库建表脚本如下：

```
dbTime = database("", VALUE, 2021.08.01..2021.09.01)
dbStockID = database("", HASH, [SYMBOL, 100])

db = database(directory="dfs://stock",partitionType=COMPO,partitionScheme=[dbTime,dbStockID],engine="TSDB")

schema = table(1:0, `Timestamp`StockID`bid, [TIMESTAMP, SYMBOL, DOUBLE])
stocks = db.createPartitionedTable(table=schema, tableName=`stocks, partitionColumns=`Timestamp`StockID, sortColumns=`StockID`Timestamp)
```

和 OLAP 的脚本相比，TSDB 的脚本在 database 初始化的时候指定存储引擎为 "TSDB"，并在创建表格的时候指定 `sortColumns` 为 `StockID` 和 `Timestamp`。

OLAP 引擎适合执行以下的 query：

```
select avg(Bid) from t where date=2021.08.05 group by StockID
```

TSDB 引擎适合执行以下的 query：

```
select * from table where StockID='AAPL', Timestamp > 2021.08.05T09:30:00, Timestamp < 2021.08.05T09:35:00
```

使用 OLAP 引擎所创建的数据库中，每个分区内部无索引，一个 query 从数据库中读取数据的最小单位是一个分区的一列。即使要查找一行数据，也必须读取该行数据所在分区的所有行，耗时一般在100毫秒以上。TSDB 引擎则在每个分区内部设置了索引，查找少量数据时无需读取分区内所有行，耗时可以低至几毫秒。TSDB 引擎在海量数据查询与分析方面的性能仅仅略慢于 OLAP 引擎。因此，若对查询少量数据有极致性能要求，推荐使用 TSDB 引擎。

## 2. TSDB原理简介

本节叙述中，为简便起见，我们将结合上一节中的例子。

### 2.1. redo log

redo log 类似于 Write-Ahead Log。数据加载到内存之后，会先持久化到 redo log 中。即便数据库在写入时宕机了，重启时，系统仍能够从 redo log 中恢复数据。

### 2.2. Cache Engine

确认数据写入 WAL 之后，数据会写入内存中的 cache engine。

新写入 cache engine 的数据是直接追加（append）的，且未经排序的（unsorted write buffer）。待缓存的数据量达到一个阈值之后，对其按照 StockID 排序（sorted write buffer）。sorted write buffer 是只读的，可在内存中开启压缩，以在内存中存储更多的数据，降低查询数据的时延。待产生多个 sorted write buffer，其总数据量达到一个阈值（由配置参数 *TSDBCacheEngineSize* 设定）之后，TSDB 会将所有 sorted write buffer 中的数据按照 Timestamp 排序后写入磁盘的数据文件（称为 level file）。

TSDB cache engine 的这种从 unsorted write buffer 到 sorted write buffer 两阶段的设计，与大多数的基于 LSMT 系统的 cache engine（或称 MemTable）有所不同。这种独特的设计是为了平衡系统的读性能与写性能。

请注意，在数据从 cache engine 写入磁盘的过程中，如果又有数据写入 cache engine，则 cache engine 会分配新的空间来存储新写入 cache engine 的数据。因此，在极端情况下，TSDB的 cache engine 最多会占用两倍的 *TSDBCacheEngineSize* 的空间。 

### 2.3. Sort Columns

类似上例中 StockID 与 Timestamp 这样用于将数据进行排序的列，在 TSDB 中被称为 sort columns。sort columns 的最后一列必须为时间类型。sortColumns 除了最后一列的其他列通常为在点查中过滤条件会用到的列，其唯一值组合，称为 sort key。使用 TSDB 引擎，查询时可利用 sort key 直接定位到过滤条件所指定的数据块，然后仅读取这些数据块的数据，点查性能可大幅提升。

### 2.4. Level File

每个 level file 中的数据均按照 StockID 与 Timestamp 排序。每个 StockID 的记录会存储为多个一定大小（16KB）的数据块，并将每个数据块在该文件中存储的起始位置记录下来。后续写入的数据会写入另一个 level file，依此类推。

level file 最多可有4个 level。Level 0 的文件由 cache engine 写入到磁盘而产生，而更高层次的 level file 是由更低层次的 level file 合并生成的。每个 level 0 文件最大为32MB。每次从 cache engine 写入同一分区的数据量若大于 32MB，则产生多个 level 0 文件。从 level 0 到 level 1 的过程如下：当一个分区内的 level 0 文件数量超过10个或 level 0 总数据量大于某个阙值（256MB）时，所有 level 0 文件会被合并压缩为一个 level 1 的文件，以此类推。合并文件时会将数据按照 StockID 与 Timestamp 进行排序。通过不断进行数据文件的合并压缩，可以有效控制  level file 的数量，以免 level file 数量过多导致性能降低。

## 3. TSDB 使用技巧

本文在这一部分简单介绍 TSDB 的一些配置项和使用技巧。

### 3.1. 如何处理重复数据

一个分区内 sortColumns 重复的数据应当如何处理，由建表时 `createPartitionedTable` 函数的 *keepDuplicates* 参数指定。在上面这个例子中，即股票代码与时间列都一致的数据。默认的值为 ALL，即保留所有数据。若设置为 FIRST，则仅会保留重复数据中的第一条；若设置为 LAST，则仅会保留重复数据中的最新一条。

### 3.2. 控制 sort key 数量

为保证性能最优，建议每个分区内 sort key 最好不超过1000个。若 sort key 过多，每个 sort key 对应的数据量少，造成部分数据块内的数据量可能不足 *TSDBMaxBlockSize*，数据块数量也很多。当用户查询数据时，由于读取大量数据块，造成读文件耗时增加。此时，用户可通过建表函数指定 *sortKeyMappingFunction*，对 sort key 降维。请注意，降维操作一定程度上将影响写入性能，建议用户优先合理规划 sortColumns。

### 3.3. 设置 cache engine 容量

使用配置参数 *TSDBCacheEngineSize* 设定 cache engine 容量（以 GB 为单位）。默认值为 1GB，建议设置 1GB 或以上。

### 3.4. 设置 TSDB 数据块大小

使用配置参数 *TSDBMaxBlockSize* 设置存储时拆分的数据块（block）在压缩前的大小（以 bytes 为单位），默认值为16,384。这个参数越大，则数据的压缩率越高，但点查的性能也会有所下降。

### 3.5. 触发 level file 合并

level file 的数量越多，则查询的效率会越低。对不再有数据写入的分区，可使用 `triggerTSDBCompaction` 命令以手动触发 level 0 file 的合并，既可以提升查询性能，亦可提升压缩率。
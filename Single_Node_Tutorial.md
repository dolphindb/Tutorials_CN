##  DolphinDB单节点基本操作入门教程

本文档适用于完成单节点安装后，通DolphinDB GUI连接到节点上，进行DolphinDB database操作。单节点安装请参考[单节点安装教程](standalone_server.md)。

### 1. 创建/删除数据库

#### 1.1 创建数据库

```
db = database("dfs://DolphinDB");
```
  * 若目录"dfs://DolphinDB"不存在，则自动创建该文件目录并创建数据库。
  * 若目录"dfs://DolphinDB"存在，且只包含`DolphinDB`创建的表及相关文件，则会打开该数据库。
  * 若目录"dfs://DolphinDB"存在，但包含有非`DolphinDB`创建的表及相关文件，则数据库创建失败。需要清空"dfs://DolphinDB"目录再次尝试。

#### 1.2 删除数据库
```
dropDatabase("dfs://DolphinDB");
```
* 函数`dropDatabase`以数据库的路径作为参数。

### 2. 创建/删除表

#### 2.1 创建表

有三种创建数据表的方法：使用`table`函数创建内存表；使用`loadTable`函数从数据库中加载数据表；使用`loadText`函数将磁盘上的文本文件加载为数据表。
  
##### 2.1.1 使用`table`函数创建内存表

* 创建一个内存表：

```
t1 = table(take(1..10, 100) as id, rand(10, 100) as x, rand(10.0, 100) as y);
```
* 使用`table`函数建立内存表，包含id、x、y 三列，共100行。

* 将内存表保存到分布式数据库中：

```
db = database("dfs://DolphinDB",VALUE,1..10)
pt=createPartitionedTable(db,t1,`pt,`id).append!(t1)
```
* 使用`createPartitionedTable` 函数将内存表t1追加到数据库db中的分区表pt中。
<!--  
* 在数据库路径下，生成了t1.tbl的表文件和t1的文件夹。
 
* 在t1文件夹下，生成了id.col、x.col、y.col三个列文件，分别存储表t1的三列。
-->
##### 2.1.2 使用`loadTable`函数从数据库中加载表

* 获取已存在的数据库的句柄：

```
db = database("dfs://DolphinDB");
```
* 从数据库中读取表名为pt的表：

```
t = loadTable(db, "pt");
```
* 使用`typestr`函数查看表的类型为"SEGMENTED DFS TABLE"，即分布式分区表。

```
typestr(t);
```

##### 2.1.3 使用`loadText`函数将磁盘上的文本文件转换为数据表

将一个文本文件test.csv加载到内存中：

```
t = loadText(C:/test.csv);
```
* `loadText`把文本文件转换为内存表。默认列以逗号(,)分隔。
  

#### 2.2 使用`dropTable`删除数据库中的表
```
db = database("dfs://DolphinDB")
dropTable(db, "tableName"); 
```

### 3. 内存表的增删改查 

按照标准的SQL语言操作

* 查询操作使用select语句。DolphinDB中的SQL语句只支持小写。

```
select * from t
```
* 插入操作使用insert语句。

```
insert into t values (5, 6, 2.5)
```
* 可使用`append!`函数进行批量插入。

```
ta = loadTable(db, "t1")
tb = loadTable(db, "t1")
select count(*) from ta
select count(*) from tb
ta.append!(tb)
select count(*) from ta
```
* 更新操作使用update语句：

```
update t set y = 1000.1 where x = 5
```
* 删除操作使用delete语句：

```
delete from t where id=3
```
* 持久化

内存表操作结果没有被记录到磁盘上。若需要对修改的表进行持久化，使用`saveTable`，或使用 `createPartitionedTable` 函数创建分区表，再使用 `append!` 函数或 `tableInsert` 函数把数据保存至分区表中。

### 4. 更多高级教程
  * __独立服务器__：作为一个独立的工作站或服务器使用，无需配置。详见教程：[单节点部署](./standalone_server.md)
  * __单机集群搭建__：控制节点(controller)、代理节点（agent）、数据节点(data node)部署在同一个物理机器上。详见教程：[单服务器集群部署](./single_machine_cluster_deploy.md)
  * __多机集群搭建__：在多个物理机器上部署 DolphinDB 集群。详见教程：[多服务器集群部署](./multi_machine_cluster_deployment.md)
  * __内存数据库计算__：作为独立工作站使用，利用高性能内存数据库，快速完成数据的加载，编辑和分析计算。详见教程：[内存数据表](./partitioned_in_memory_table.md)
  * __分区数据库__：支持多种灵活的分区方式，如顺序分区，范围分区，值分区，列表分区，复合分区。详见教程：[分区数据库](./database.md)
  * __脚本语言__：类似SQL与Python，易学，灵活，提供丰富的内置函数。详见教程：[编程语言介绍](./hybrid_programming_paradigms.md)
  * __权限与安全配置__：提供了强大、灵活、安全的权限控制系统，以满足企业级各种应用场景。详见教程：[权限管理和安全](./ACL_and_Security.md)
  

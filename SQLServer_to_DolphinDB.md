# 从 SQL Server 迁移数据到 DolphinDB

作为传统的事务型数据库，SQL Server 有着出色的读写性能，但当面对高吞吐量数据写入以及海量的数据分析等场景时，却无法满足需求。即使数据量较小，能满足数据写入的要求，也不能同时响应实时计算的请求。

DolphinDB 是一款国产的高性能分布式时序数据库产品。既有非常高的吞吐量，又有较低的延时；既能够实时处理流数据，又能够处理海量的历史数据；既能满足简单的点查询的要求，又能满足批量数据复杂分析的要求。在金融和物联网领域，DolphinDB 以天然的分布式构架，强大的流式增量计算能力，丰富的函数库，以及易用性等优势吸引了大量海内外用户。

本文旨在为有从 SQL Server 迁移至 DolphinDB 需求的用户提供一份简洁明了的参考。

- [从 SQL Server 迁移数据到 DolphinDB](#从-sql-server-迁移数据到-dolphindb)
  - [1. 实现方法](#1-实现方法)
  - [2. 应用需求](#2-应用需求)
  - [3. 迁移步骤](#3-迁移步骤)
    - [3.1 通过 ODBC 插件迁移](#31-通过-odbc-插件迁移)
    - [3.2 通过 DataX 驱动迁移](#32-通过-datax-驱动迁移)
  - [4. 性能比较](#4-性能比较)

## 1. 实现方法

从 SQL Server 迁移数据到 DolphinDB 可以选择以下两种软件

* ODBC 插件

ODBC(Open Database Connectivity) 插件是 DolphinDB 提供的通过 ODBC 接口访问 SQL Server 的开源产品。插件配合 DolphinDB 脚本使用，与服务器在同一个进程空间内运行，能高效地完成 SQL Server 数据到 DolphinDB 的数据写入。

ODBC 提供如下函数，函数的具体使用请参考 [DolphinDB ODBC plugin](https://gitee.com/dolphindb/DolphinDBPlugin/blob/release200/odbc/README.md)

1.  `odbc::connect(connStr, [dataBaseType])`
2.  `odbc::close(conn)`
3.  `odbc::query(connHandle or connStr, querySql, [t], [batchSize], [tranform])`
4.  `odbc::execute(connHandle or connStr, SQLstatements)`
5.  `odbc::append(connHandle, tableData, tablename, [createTableIfNotExist], [insertIgnore])`

* DataX 驱动

DataX 是可扩展的数据同步框架，将不同数据源的同步抽象为从源头数据源读取数据的 Reader 插件，以及向目标端写入数据的 Writer 插件，理论上 DataX 框架可以支持任意数据源类型的数据同步工作。

DolphinDB 提供基于 DataXReader 和 DataXWriter 的开源驱动。DolphinDBWriter 插件实现了向 DolphinDB 写入数据，使用 DataX 的现有 reader 插件结合 DolphinDBWriter 插件，即可实现从不同数据源向 DolphinDB 同步数据。用户可以在 Java 项目中包含 DataX 的驱动包，开发从 SQL Server 数据源到 DolphinDB 的数据迁移软件。

DataX 驱动的开发基于 Java SDK，支持高可用。

|     |     |     |
| --- | --- | --- |
| **实现途径** | **数据写入效率** | **高可用** |
| ODBC 插件 | 高   | 不支持 |
| DataX 驱动 | 中   | 支持  |

## 2. 应用需求

很多之前使用 SQL Server 的用户不可避免地需要将数据迁移同步至 DolphinDB。DolphinDB 提供了多种灵活的数据同步方法，来帮助用户方便地把海量数据从多个数据源进行全量同步或增量同步。本文中的实践案例基于该需求，提供了将深交所逐笔委托数据从 SQL Server 迁移至 DolphinDB 的高性能解决方案。

现有最近 10 年的逐笔委托数据，存储于 SQL Server。其部分数据示例如下：


|TradeDate| OrigTime| SendTime| RecvTime| LocalTime| ChannelNo| MDStreamID| ApplSeqNum| SecurityID| SecurityIDSource |Price |OrderQty| TransactTime| Side| OrderType| ConfirmID| Contactor| ContactInfo |ExpirationDays| ExpirationType|
| ------- | ------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | ---------|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3090000|	2013|	11|	1	|300104	|102|	2.74|	911100|	2019-01-02 09:15:00.000|	1|	2|	0.0	|NULL|	NULL|	0|	0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3130000|	2023|	11|	1|	159919|	102|	3.002|	100	|2019-01-02 09:15:00.000|	1|	2|	0.0	|NULL|	NULL	|0	|0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2023|	11|	2	|159919|	102|	3.002|	100	|2019-01-02 09:15:00.000|	1|	2	|0.0|	NULL|	NULL	|0|	0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2023|	11|	3	|159919|	102	|3.002|	100|	2019-01-02 09:15:00.000|	1	|2|	0.0	|NULL|	NULL|	0|	0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2023|	11|	4	|159919	|102	|3.002|	100	|2019-01-02 09:15:00.000|	1|	2|	0.0	|NULL|	NULL	|0	|0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2023|	11|	5	|159919	|102|	3.002|	100	|2019-01-02 09:15:00.000|	1|	2|	0.0	|NULL|	NULL|	0|	0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2023|	11|	6|	159919|	102	|3.002|	100|	2019-01-02 09:15:00.000	|1|	2|	0.0	|NULL|	NULL|	0|	0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2013|	11|	2|	002785|	102|	10.52|	664400|	2019-01-02 09:15:00.000|	1	|2|	0.0|	NULL|	NULL|	0	|0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2013|	11|	3|	200613|	102|	5.12|	4400	|2019-01-02 09:15:00.000|	2|	2|	0.0|	NULL|	NULL|	0|	0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2013|	11|	4|	002785|	102	|10.52|	255500|	2019-01-02 09:15:00.000|	1|	2|	0.0|	NULL|	NULL|	0	|0|


为方便后期与其他数据源的逐笔委托数据整合，数据迁移过程中要对表结构进行部分调整，字段对应表如下所示：

|     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- |
| **SQL Server 字段含义** | **SQL Server 字段** | **SQL Server 数据类型** | **DolphinDB 字段含义** | **DolphinDB 字段** | **DolphinDB 数据类型** |
| 交易日期 | tradedate | date |     |     |     |
| 数据生成时间 | OrigTime | time(7) |     |     |     |
| 发送时间 | SendTime | time(7) |     |     |     |
| 接收时间 | Recvtime | time(7) |     |     |     |
| 入库时间 | LocalTime | time(7) | 入库时间 | LocalTime | TIME |
| 频道代码 | ChannelNo | int | 频道代码 | ChannelNo | INT |
| 行情类别 | MDStreamID | int | 行情类别 | MDStreamID | INT |
| 委托订单号 | ApplSeqNum | bigint | 委托订单号 | ApplSeqNum | LONG |
| 证券代码 | SecurityID | varchar(255) | 证券代码 | SecurityID | SYMBOL |
| 证券代码源 | SecurityIDSource | int | 证券代码源 | SecurityIDSource | INT |
| 委托价格 | Price | float | 委托价格 | Price | DOUBLE |
| 委托数量 | OrderQty | int | 委托数量 | OrderQty | INT |
| 委托时间 | TransactTime | datetime | 委托时间 | TransactTime | TIMESTAMP |
| 买卖方向 | Side | varchar(255) | 买卖方向 | Side | SYMBOL |
| 委托类别 | OrderType | varchar(255) | 委托类别 | OrderType | SYMBOL |
| 定价行情约定号 | ConfirmID | varchar(255) |     |     |     |
| 联系人 | Contactor | varchar(255) |     |     |     |
| 联系方式 | ContactInfo | varchar(255) |     |     |     |
| 期限  | ExpirationDays | int |     |     |     |
| 期限类型 | ExpirationType | varchar(255) |     |     |     |
|     |     |     | 业务序列号 | BizIndex | LONG |
|     |     |     | 数据状态 | DataStatus | INT |
|     |     |     | SeqNo | SeqNo | LONG |
|     |     |     | 交易市场 | Market | SYMBOL |

## 3. 迁移步骤

### 3.1 通过 ODBC 插件迁移

#### 3.1.1 安装 ODBC 驱动 <!-- omit in toc -->

本例中部署 DolphinDB 的服务器操作系统为 ubuntu22.04。

1.  终端中运行以下命令安装 freeTDS 程序库、unixODBC 库和 SQL Server ODBC 驱动。

```
# 安装 freeTDS
apt install -y freetds

# 安装 unixODBC 库
apt-get install unixodbc unixodbc-dev

# 安装 SQL Server ODBC 驱动
apt-get install tdsodbc
```

2. 在 / etc/freetds/freetds.conf 中添加 SQL Server 的 ip 和 port

```
[sqlserver]
host = 127.0.0.1
port = 1433
```

3. 在 / etc/odbcinst.ini 中完成以下配置：

```
[SQLServer]
Description = ODBC for SQLServer
Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
FileUsage = 1
```

若是 CentOS 操作系统，则通过以下步骤安装：

1.  终端中运行以下命令安装 freeTDS 程序库和 unixODBC 库。

```
# 安装 freeTDS
yum install -y freetds

# 安装 unixODBC 库
yum install unixODBC-devel
```

2. 在 / etc/freetds.conf 中添加 SQL Server 的 ip 和 port

3. 在 / etc/odbcinst.ini 中完成以下配置

```
[SQLServer]
Description = ODBC for SQLServer
Driver = /usr/lib64/libtdsodbc.so.0.0.0
Setup = /usr/lib64/libtdsodbc.so.0.0.0
FileUsage = 1
```

#### 3.1.2 同步数据 <!-- omit in toc -->

1.  运行以下命令加载 ODBC 插件

```
loadPlugin("/home/Linux64_V2.00.8/server/plugins/odbc/PluginODBC.txt")
```

2. 运行以下命令建立与 SQL Server 的连接

```
conn =odbc::connect("Driver={SQLServer};Servername=sqlserver;Uid=sa;Pwd=DolphinDB;database=historyData;;");
```

3. 运行以下脚本执行同步

```
def transform(mutable msg){
	msg.replaceColumn!(`LocalTime,time(temporalParse(msg.LocalTime,"HH:mm:ss.nnnnnn")))
    msg.replaceColumn!(`Price,double(msg.Price))
	msg[`SeqNo]=int(NULL)
	msg[`DataStatus]=int(NULL)
	msg[`BizIndex]=long(NULL)
	msg[`Market]="SZ"
	msg.reorderColumns!(`ChannelNo`ApplSeqNum`MDStreamID`SecurityID`SecurityIDSource`Price`OrderQty`Side`TransactTime`OrderType`LocalTime`SeqNo`Market`DataStatus`BizIndex)
    return msg
}

def synsData(conn,dbName,tbName){
    odbc::query(conn,"select ChannelNo,ApplSeqNum,MDStreamID,SecurityID,SecurityIDSource,Price,OrderQty,Side,TransactTime,OrderType,LocalTime from data",loadTable(dbName,tbName),100000,transform)
}

submitJob("synsData","synsData",synsData,conn,dbName,tbName)
```

```
startTime                      endTime
2022.11.28 11:51:18.092        2022.11.28 11:53:20.198
```

耗时约 122 秒。

借助 DolphinDB 提供的 scheduleJob 函数，可以实现增量同步。

示例如下，每天 00:05 同步前一天的数据。

```
def synchronize(){
	login(`admin,`123456)
    conn =odbc::connect("Driver={SQLServer};Servername=sqlserver;Uid=sa;Pwd=DolphinDB;database=historyData;;")
    sqlStatement = "select ChannelNo,ApplSeqNum,MDStreamID,SecurityID,SecurityIDSource,Price,OrderQty,Side,TransactTime,OrderType,LocalTime from data where TradeDate ='" + string(date(now())-1) + "';"
    odbc::query(conn,sqlStatement,loadTable("dfs://TSDB_Entrust",`entrust),100000,transform)
}
scheduleJob(jobId=`test, jobDesc="test",jobFunc=synchronize,scheduleTime=00:05m,startDate=2022.11.11, endDate=2023.01.01, frequency='D')
```

**注意**：为防止节点重启时定时任务解析失败，预先在配置文件里添加 `preloadModules=plugins::odbc`

### 3.2 通过 DataX 驱动迁移

#### 3.2.1 部署 DataX <!-- omit in toc -->

从 [DataX 下载地址](https://datax-opensource.oss-cn-hangzhou.aliyuncs.com/202210/datax.tar.gz) 下载 DataX 压缩包后，解压至自定义目录。

#### 3.2.2 部署 DataX-DolphinDBWriter 插件 <!-- omit in toc -->

将 [Github 链接](https://github.com/dolphindb/datax-writer) 中源码的 ./dist/dolphindbwriter 目录下所有内容拷贝到 DataX/plugin/writer 目录下，即可使用。

#### 3.2.3 执行 DataX 任务 <!-- omit in toc -->

配置文件 synchronization.json 置于 data/job 目录下：

```
{
    "core": {
        "transport": {
            "channel": {
                "speed": {
                    "byte": 5242880
                }
            }
        }
    },
    "job": {
        "setting": {
            "speed": {
                "byte":10485760
            }
        },
        "content": [
            {
                "reader": {
                    "name": "sqlserverreader",
                    "parameter": {
                        "username": "sa",
                        "password": "DolphinDB123",
                        "column": [
                            "ChannelNo","ApplSeqNum","MDStreamID","SecurityID","SecurityIDSource","Price","OrderQty","Side","TransactTime","OrderType","LocalTime"
                        ],
                        "connection": [
                            {
                                "table": [
                                    "data"
                                ],
                                "jdbcUrl": [
                                    "jdbc:sqlserver://127.0.0.1:1433;databasename=historyData"
                                ]
                            }
                        ]
                    }
                },
                "writer": {
                    "name": "dolphindbwriter",
                    "parameter": {
                        "userId": "admin",
                        "pwd": "123456",
                        "host": "127.0.0.1",
                        "port": 8888,
                        "dbPath": "dfs://TSDB_Entrust",
                        "tableName": "entrust",
                        "batchSize": 100000,
                        "saveFunctionDef": "def customTableInsert(dbName, tbName, mutable data) {data.replaceColumn!(`LocalTime,time(temporalParse(data.LocalTime,\"HH:mm:ss.nnnnnn\")));data.replaceColumn!(`Price,double(data.Price));data[`SeqNo]=int(NULL);data[`DataStatus]=int(NULL);data[`BizIndex]=long(NULL);data[`Market]=`SZ;data.reorderColumns!(`ChannelNo`ApplSeqNum`MDStreamID`SecurityID`SecurityIDSource`Price`OrderQty`Side`TransactTime`OrderType`LocalTime`SeqNo`Market`DataStatus`BizIndex);pt = loadTable(dbName,tbName);pt.append!(data)}",
                        "saveFunctionName" : "customTableInsert",
                        "table": [
                            {
                                "type": "DT_INT",
                                "name": "ChannelNo"
                            },
                            {
                                "type": "DT_LONG",
                                "name": "ApplSeqNum"
                            },
                            {
                                "type": "DT_INT",
                                "name": "MDStreamID"
                            },
                            {
                                "type": "DT_SYMBOL",
                                "name": "SecurityID"
                            },
                            {
                                "type": "DT_INT",
                                "name": "SecurityIDSource"
                            },
                            {
                                "type": "DT_DOUBLE",
                                "name": "Price"
                            },
                            {
                                "type": "DT_INT",
                                "name": "OrderQty"
                            },
                            {
                                "type": "DT_SYMBOL",
                                "name": "Side"
                            },
                            {
                                "type": "DT_TIMESTAMP",
                                "name": "TransactTime"
                            },
                            {
                                "type": "DT_SYMBOL",
                                "name": "OrderType"
                            },
                            {
                                "type": "DT_STRING",
                                "name": "LocalTime"
                            }
                        ]

                    }
                }
            }
        ]
    }
}
```

2. Linux 终端中执行以下命令执行 DataX 任务

```
cd ./DataX/bin/
python DataX.py ../job/synchronization.json
```

```
任务启动时刻                    : 2022-11-28 17:58:52
任务结束时刻                    : 2022-11-28 18:02:24
任务总计耗时                    :                212s
任务平均流量                    :            3.62MB/s
记录写入速度                    :          78779rec/s
读出记录总数                    :            16622527
读写失败总数                    :                   0
```

同样的，若需要增量同步，可在 synchronization.json 中的 "reader" 增加 "where" 条件，增加对交易日期的过滤，每次执行同步任务时只同步 where 条件中过滤的数据，例如这些数据可以是前一天的数据。

以下例子仅供参考：

```
"reader": {
                    "name": "sqlserverreader",
                    "parameter": {
                        "username": "sa",
                        "password": "DolphinDB123",
                        "column": [
                            "ChannelNo","ApplSeqNum","MDStreamID","SecurityID","SecurityIDSource","Price","OrderQty","Side","TransactTime","OrderType","LocalTime"
                        ],
                        "connection": [
                            {
                                "table": [
                                    "data"
                                ],
                                "jdbcUrl": [
                                    "jdbc:sqlserver://127.0.0.1:1433;databasename=historyData"
                                ]
                            }
                        ]
                        "where":"TradeDate=(select CONVERT ( varchar ( 12) , dateadd(d,-1,getdate()), 102))"
                    }
                }
```

## 4. 性能比较

本案例中使用的软件版本为：

* DolphinDB: DolphinDB\_Linux64\_V2.00.8.6
* SQL Server: Microsoft SQL Server 2017 (RTM-CU31) (KB5016884) - 14.0.3456.2 (X64)

分别使用 ODBC 插件和 DataX 驱动进行数据迁移的耗时对比如下表所示：

|     |     |
| --- | --- |
| ODBC 插件 | DataX |
| 122s | 212s |

由此可见，ODBC 插件的性能优于 DataX。当数据量增大，尤其时表的数量增多时，ODBC 插件的速度优势更为明显。而且即使不需要对同步数据进行处理，DataX 也需要对每一个表配置一个 json，而 ODBC 则只需要更改表名即可，实现难度明显低于 DataX。

|     |     |     |
| --- | --- | --- |
|     | **使用场景** | **实现难度** |
| ODBC 插件 | 全量同步，增量同步 | 可完全在 DolphinDB 端实现 |
| DataX | 全量同步，增量同步 | 需要部署 DataX 并编写 json |
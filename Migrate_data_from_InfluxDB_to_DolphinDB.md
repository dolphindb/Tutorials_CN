# 从 InfluxDB 迁移数据到 DolphinDB

InfluxDB 是一款流行的时序数据处理平台，有着丰富的数据导入方式，完善的集数据处理、预警、可视化等功能为一体的操作界面。其主要是面向物联网场景开发的，同时从 2.0 版本开始，使用了基于 Flux 语言的操作模型来处理数据，不过对于用户来讲有一定的学习成本。

DolphinDB 是一款国产的高性能分布式时序数据库产品。支持 SQL 和使用类 Python 的语法来处理数据，相比 Flux 语言来讲学习成本很低。DolphinDB 提供了 1400 多个函数，对于复杂的数据处理场景有很强的表达能力，极大的降低了用户开发成本。在数据存储压缩率方面，InfluxDB 和 DolphinDB 的相差不多。而数据查询性能方面，DolphinDB 要比 InfluxDB 高很多，甚至有多个数量级的差异。DolphinDB 也有强大的流式增量计算能力，满足用户实时数据的处理需求。

本文旨在为有从 InfluxDB 迁移至 DolphinDB 需求的用户提供一份简洁明了的参考。

- [从 InfluxDB 迁移数据到 DolphinDB](#从-influxdb-迁移数据到-dolphindb)
  - [实现方法](#实现方法)
  - [迁移案例与操作步骤](#迁移案例与操作步骤)
    - [1. 生成测试数据](#1-生成测试数据)
    - [2. 在 DolphinDB 创建表](#2-在-dolphindb-创建表)
    - [3. 部署 Addax](#3-部署-addax)
    - [4. 部署 Addax-DolphinDBWriter 插件](#4-部署-addax-dolphindbwriter-插件)
    - [5. 定义迁移任务](#5-定义迁移任务)
      - [5.1 时间格式的转换](#51-时间格式的转换)
      - [5.2 编写配置文件](#52-编写配置文件)
    - [6. 执行 addax 任务](#6-执行-addax-任务)
  - [配置文件参数说明](#配置文件参数说明)
    - [InfluxDB 2.0 读插件配置项](#influxdb-20-读插件配置项)
      - [column 配置详解](#column-配置详解)
    - [DolphinDB 写插件配置项](#dolphindb-写插件配置项)
      - [table 配置详解](#table-配置详解)

## 实现方法

InfluxDB 支持丰富的数据源接入。在将数据导出时，用户可以通过 API 接口读取数据，并根据实际业务需求转换数据并导出，但这种方式会带来开发上的成本。

这种不同数据源之间的数据同步需求，催生了类似于 DataX 这样的同步工具/平台的诞生。这些工具主要通过插件实现各个数据源的读取和写入，用户只需提供一个配置文件，就可以实现不同数据源之间的同步需求。

DolphinDB 支持用户通过 DataX 插件实现数据的读写，但考虑到，InfluxDB1.0 和 2.0 版本均不支持 DataX 插件，我们基于另一个数据同步平台 Addax，开发了 DolphinDB 写入插件，通过配合 InfluxDB 的读写插件，实现将数据从 InfluxDB 迁移到 DolphinDB 的功能。

对于用户来讲，只需要配置 Addax 的任务文件，即配置 InfluxDB 的读插件参数以及 DolphinDB 的写插件参数，就可以完成从 InfluxDB 迁移数据到 DolphinDB 的功能。

## 迁移案例与操作步骤

在物联网监控场景中，数据有来源多、维度高、数据量大的特点。用户常见的需求是，在采集传感器数据时，实时写入、聚合数据，并做异常检测、预警等分析操作。这对数据库系统的吞吐量和实时分析能力提出了很高的要求。

在这方面，DolphinDB 有着丰富的实践案例，可以参考 [DolphinDB 物联网范例](https://gitee.com/dolphindb/Tutorials_CN/blob/master/iot_examples.md)，[DolphinDB 在工业物联网的应用](https://gitee.com/dolphindb/Tutorials_CN/blob/master/iot_demo.md)，[DolphinDB 流计算在物联网的应用：实时检测传感器状态变化](https://gitee.com/dolphindb/Tutorials_CN/blob/master/DolphinDB_streaming_application_in_IOT.md) 等。

我们以物联网设备传感器的数据为例，来说明如何将 InfluxDB 的数据迁移到 DolphinDB。

### 1. 生成测试数据

在实际迁移过程中，我们需要注意数据完成迁移后所使用的数据类型。具体 DolphinDB 支持的数据类型，可以参考 [数据类型](https://www.dolphindb.cn/cn/help/200/DataTypesandStructures/DataTypes/index.html)

这里以 InfluxDB 官方提供的示例数据里的“设备示例数据”([Sample data](https://docs.influxdata.com/influxdb/v2.5/reference/sample-data/#machine-production-sample-data) ) 为例，说明如何把数据导入到 DolphinDB。

在导入之前，我们创建一个 InfluxDB 的 bucket, 并使用 Flux 脚本导入测试数据到测试的 bucket，代码文件 [genMockData.flux](script/Migrate_data_from_InfluxDB_to_DolphinDB/genMockData.flux) 内容如下：

```
import "influxdata/influxdb/sample"

sample.data(set: "machineProduction")
    |> to(bucket: "demo-bucket")
```

### 2\. 在 DolphinDB 创建表

针对上面的测试数据，我们需要在 DolphinDB 里创建对应的库表，用于存储迁移过来的数据。对于实际的数据，需要综合考虑被迁移数据的字段，类型，数据量，在 DolphinDB 是否需要分区，分区方案，使用 OLAP 还是 TSDB 引擎等情况，去设计建库建表方案。一些数据存储库表设计实践，可以参考 [分区数据库](https://gitee.com/dolphindb/Tutorials_CN/blob/master/database.md)

本例建表文件 [createTable.dos](script/Migrate_data_from_InfluxDB_to_DolphinDB/createTable.dos) 内容如下:

```
login("admin","123456")

dbName="dfs://demo"
tbName="pt"

colNames=`time`stateionID`grinding_time`oil_temp`pressure`pressure_target`rework_time`state
colTypes=[NANOTIMESTAMP,SYMBOL,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,SYMBOL]
schemaTb=table(1:0,colNames,colTypes)

db = database(dbName, VALUE,2021.08.01..2022.12.31)
pt = db.createPartitionedTable(schemaTb, "pt", `time)
```

### 3. 部署 Addax

Addax 有2种安装方式，一种是下载已经编译好的二进制包，一种是下载源码，并从源码编译安装。可以参考其官方[快速使用](https://wgzhao.github.io/Addax/develop/quickstart/)来部署。

### 4. 部署 Addax-DolphinDBWriter 插件

下载已编译好的 Addax 的 DolphinDB [写插件](https://github.com/dolphindb/AddaxDolphinDBWriter/tree/master/dolphindbwriter)，拷贝到 Addax 的插件目录 plugin/writer 目录下。

或者也可以自行编译插件。

### 5\. 定义迁移任务

在定义迁移任务，主要是按照 Addax 的[任务配置](https://wgzhao.github.io/Addax/develop/setupJob/)，配置 InfluxDB 2.0 [读插件](https://wgzhao.github.io/Addax/develop/reader/influxdb2reader/) 和 DolphinDB [写插件](https://github.com/dolphindb/AddaxDolphinDBWriter/blob/master/README_CN.md) 参数。对于时间类型的数据，也需要注意一下格式转换的问题。

#### 5.1 时间格式的转换

InfluxDB 2.0 中存储时间类型数据，采用的是带有时区信息的 RFC3339 格式。而 DolphinDB 里存储的是本地时间，没有时区的概念。在使用 InfluxDB2.0 插件读取数据时，此时如果直接写入 DolphinDB 表，会造成转换错误。因此需要自定义函数，去处理和转化数据。这部分转换规则可以在 dolphindb 的写入插件中去定义，通过定义参数 saveFunctionName 和 saveFunctionDef 来指定转换函数（具体转换函数的格式参数，可以参考 [datax-writer](https://github.com/dolphindb/datax-writer#readme)）来实现时间列数据转换（可以参考下面的案例）。

#### 5.2 编写配置文件

编写数据迁移任务的配置文件 [influx2ddb.json](script/Migrate_data_from_InfluxDB_to_DolphinDB/influx2machine.json)（具体的每个配置参数的含义，可以参考附录说明），文件内容如下:

```
{
  "job": {
    "content": {
      "reader": {
        "name": "influxdb2reader",
        "parameter": {
          "column": ["*"],
          "connection": [
            {
              "endpoint": "http://183.136.170.168:8086",
              "bucket": "demo-bucket",
              "table": [
                  "machinery"
              ],
              "org": "zhiyu"
            }
          ],
          "token": "GLiPjQFQIxzVO0-atASJHH4b075sTlyEZGrqW20XURkelUT5pOlfhi_Yuo2fjcSKVZvyuO00kdXunWPrpJd_kg==",
          "range": [
            "2007-08-09"
          ]
        }
      },
      "writer": {
        "name": "dolphindbwriter",
        "parameter": {
          "userId": "admin",
          "pwd": "123456",
          "host": "115.239.209.122",
          "port": 3134,
          "dbPath": "dfs://demo",
          "tableName": "pt",
          "batchSize": 1000000,
          "saveFunctionName": "transData",
          "saveFunctionDef": "def parseRFC3339(timeStr) {if(strlen(timeStr) == 20) {return localtime(temporalParse(timeStr,'yyyy-MM-ddTHH:mm:ssZ'));} else if (strlen(timeStr) == 24) {return localtime(temporalParse(timeStr,'yyyy-MM-ddTHH:mm:ss.SSSZ'));} else {return timeStr;}};def transData(dbName, tbName, mutable data) {timeCol = exec time from data; timeCol=each(parseRFC3339, timeCol);  writeLog(timeCol);replaceColumn!(data,'time', timeCol); loadTable(dbName,tbName).append!(data); }",
          "table": [
              {
                "type": "DT_STRING",
                "name": "time"
              },
              {
                "type": "DT_SYMBOL",
                "name": "stationID"
              },
              {
                "type": "DT_DOUBLE",
                "name": "grinding_time"
              },
              {
                "type": "DT_DOUBLE",
                "name": "oil_temp"
              },
              {
                "type": "DT_DOUBLE",
                "name": "pressure"
              },
              {
                "type": "DT_DOUBLE",
                "name": "pressure_target"
              },
              {
                "type": "DT_DOUBLE",
                "name": "rework_time"
              },
              {
                "type": "DT_SYMBOL",
                "name": "state"
              }
          ]
        }
      }
    },
    "setting": {
      "speed": {
        "bytes": -1,
        "channel": 1
      }
    }
  }
}
```

其中 saveFunctionDef 的定义为:

```
def parseRFC3339(timeStr) {
	if(strlen(timeStr) == 20) {
		return localtime(temporalParse(timeStr,'yyyy-MM-ddTHH:mm:ssZ'));
	} else if (strlen(timeStr) == 24) {
		return localtime(temporalParse(timeStr,'yyyy-MM-ddTHH:mm:ss.SSSZ'));
	} else {
		return timeStr;
	}
}

def transData(dbName, tbName, mutable data) {
	timeCol = exec time from data; writeLog(timeCol);
	timeCol=each(parseRFC3339, timeCol);
	replaceColumn!(data, 'time', timeCol);
	loadTable(dbName,tbName).append!(data);
}
```

这里主要定义了2个函数，转换函数入口是 transData。在 writer 的定义里，需要把参数 saveFunctionName 设置为转换入口函数"transData"。上面的函数实现里，主要是先对这个字符串类型的时间列做解析，生成需要的时间列，最后调用 [append!](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/FunctionReferences/a/append!.html) 去写入分布式表。

在转换时间列时，通过函数 [temporalParse](https://www.dolphindb.cn/cn/help/200/FunctionsandCommands/FunctionReferences/t/temporalParse.html) 去分析时间字符串，并通过函数 [localtime](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/l/localtime.html) 去将 UTC 时间转换成本地时间并进行存储。如果业务上有需要，也可以不做时区转换，存储 temporalParse 的结果。关于时间信息处理相关的实践例子，可以参考 [DolphinDB 中有关时间信息的最佳实践指南](https://gitee.com/dolphindb/Tutorials_CN/blob/master/timezone.md) 。

### 6\. 执行 addax 任务

```
./bin/addax.sh ~/addax/job/influx2ddb.json
```

(上面路径根据实际 addax 的位置，以及配置文件路径来修改）

运行结果如下：

```
2022-12-13 21:17:17.870 [job-0] INFO  JobContainer         -
任务启动时刻                    : 2022-12-13 21:17:14
任务结束时刻                    : 2022-12-13 21:17:17
任务总计耗时                    :                  3s
任务平均流量                    :          345.07KB/s
记录写入速度                    :           6568rec/s
读出记录总数                    :               19705
读写失败总数                    :                   0
```

若需要实现增量同步，可以在 influx2ddb.json 中的 reader 里，修改 range 字段，指定开始时间和结束时间来[过滤数据](https://wgzhao.github.io/Addax/develop/reader/influxdb2reader/)。

以上就是一个 InfluxDB 2.0 数据迁移到 DolphinDB 的过程。对于 InfluxDB 1.0 的数据迁移任务，只需要修改上面的任务配置文件（influx2ddb.json），将里面的读插件替换为 InfluxDB 1.0 的读插件，然后做对应的配置即可。

除了定义迁移任务配置文件，更重要的是需要考虑 DolphinDB 数据存储方案，包括是否分区，分区方案，使用引擎等。

## 配置文件参数说明

### InfluxDB 2.0 读插件配置项

|     |     |     |     |     |
| --- | --- | --- | --- | --- |
| **配置项** | **是否必须** | **数据类型** | **默认值** | **描述** |
| endpoint | 是   | string |     | 无   |
| token | 是   | string | 无   | 访问数据库的 token |
| table | 否   | list | 无   | 所选取的需要同步的表名（即指标) |
| org | 是   | string | 无   | 指定 InfluxDB 的 org 名称 |
| bucket | 是   | string | 无   | 指定 InfluxDB 的 bucket 名称 |
| column | 否   | list | 无   | 所配置的表中需要同步的列名集合，具体参考后面 column 配置详解 |
| range | 是   | list | 无   | 读取数据的时间范围 |
| limit | 否   | int | 无   | 限制获取记录数 |

#### column 配置详解

column 是配置的表中需要同步的列名集合，使用 JSON 的数组描述字段信息。用户使用 `*` 代表默认使用所有列配置，例如 \["\*"\]。

支持列裁剪，即列可以挑选部分列进行导出。

支持列换序，即列可以不按照表 schema 信息进行导出。

支持常量配置，用户需要按照 JSON 格式:

```
["id", "`table`", "1", "'bazhen.csy'", "null", "to_char(a + 1)", "2.3" , "true"]
```

*   `id` 为普通列名
*   `` `table` `` 为包含保留在的列名
*   `1` 为整形数字常量
*   `'bazhen.csy'` 为字符串常量
*   `null` 为空指针，注意，这里的 `null` 必须以字符串形式出现，即用双引号引用
*   `to_char(a + 1)` 为表达式
*   `2.3` 为浮点数
*   `true` 为布尔值，同样的，这里的布尔值也必须用双引号引用

### DolphinDB 写插件配置项

|     |     |     |     |     |
| --- | --- | --- | --- | --- |
| **配置项** | **是否必须** | **数据类型** | **默认值** | **描述** |
| host | 是   | string | 无   | Server Host |
| port | 是   | int | 无   | Server Port |
| userId | 是   | string | 无   | DolphinDB 用户名  <br> 导入分布式库时，必须要有权限的用户才能操作，否则会返回 |
| pwd | 是   | string | 无   | DolphinDB 用户密码 |
| dbPath | 是   | string | 无   | 需要写入的目标分布式库名称，比如 "dfs://MYDB"。 |
| tableName | 是   | string | 无   | 目标数据表名称 |
| batchSize | 否   | int | 10000000 | datax 每次写入 dolphindb 的批次记录数 |
| table | 是   |     |     | 写入表的字段集合，具体参考后续 table 项配置详解 |
| saveFunctionName | 否   | string | 无   | 自定义数据处理函数。若未指定此配置，插件在接收到 reader 的数据后，会将数据提交到 DolphinDB 并通过 tableInsert 函数写入指定库表；如果定义此参数，则会用指定函数替换 tableInsert 函数。 |
| saveFunctionDef | 否   | string | 无   | 数据入库自定义函数。此函数指 用 dolphindb 脚本来实现的数据入库过程。 此函数必须接受三个参数：dfsPath（分布式库路径），tbName（数据表名）， data（从 datax 导入的数据，table 格式） |

#### table 配置详解

table 用于配置写入表的字段集合。内部结构为

```
 {"name": "columnName", "type": "DT_STRING", "isKeyField":true}
```

请注意此处列定义的顺序，需要与原表提取的列顺序完全一致。

*   name：字段名称
*   isKeyField：是否唯一键值，可以允许组合唯一键。本属性用于数据更新场景，用于确认更新数据的主键，若无更新数据的场景，无需设置
*   type：枚举值以及对应 DolphinDB 数据类型如下


| DolphinDB 类型 | 配置值 |
| --- | --- |
| DOUBLE | DT\_DOUBLE |
| FLOAT | DT\_FLOAT |
| BOOL | DT\_BOOL |
| DATE | DT\_DATE |
| MONTH | DT\_MONTH |
| DATETIME | DT\_DATETIME |
| TIME | DT\_TIME |
| SECOND | DT\_SECOND |
| TIMESTAMP | DT\_TIMESTAMP |
| NANOTIME | DT\_NANOTIME |
| NANOTIMETAMP | DT\_NANOTIMETAMP |
| INT | DT\_INT |
| LONG | DT\_LONG |
| UUID | DT\_UUID |
| SHORT | DT\_SHORT |
| STRING | DT\_STRING |
| SYMBOL | DT\_SYMBOL |
# 物联网数据库设计实践

## 1.概述
DolphinDB内置分布式文件系统，实现数据库的存储和基本事务机制。数据库以分区为单位进行管理。每个分区副本的数据采用列式增量压缩存储。DolphinDB通过数据分区而不是索引的方式来快速定位数据，十分适合海量数据的存储，检索和计算。为了让数据管理更高效，在查询和计算时性能更好，以达到更低延时和更高吞吐量，用户需要理解DolphinDB的分区机制。本文描述几个物联网领域常见场景的数据库设计例子，以帮助用户快速上手分区数据库设计。建议用户在阅读本文之前先阅读[`DolphinDB的分区数据库教程`](https://github.com/dolphindb/Tutorials_CN/blob/master/database.md)。

## 2.案例1--单值模式 
#### 2.1 需求描述
某电厂有10台机组，每台机组的振动系统有3000个测点（在工业场景中，一个被监控的参数称为一个测点，比如一个设备的温度指标算一个测点，十个设备的十个指标就是100个测点）。具体需求如下：
* 对每个测点，每1秒钟采集一次数据。将采集到的原始数据存入数据库。实际业务中，每台机组的3000个测点不是同时获取和写入的,即分快变量、慢变量和波形,快变量是变化比较快的振动指标。一般快变量150个，慢变量50个， 波形50个，其他指标预留给别的系统。
* 对测点按顺序进行编号：1--3000是一号机组，3001~6000是二号机组，其他以此类推。所有测点的数据类型都是float浮点数。
* 典型的历史数据查询是1个月，也可以多个月。做大数据分析时一般也是按照月进行查询和计算。
* 每次查询一个指标或多个指标，一次分析不会超过10个指标。

#### 2.1 数据库设计方案
数据模型分单值模型和多值模拟。单值模型指在写入时会对每一个测点建一个模型，查询时会针对每个测点去查询数值，单值模型的写入效率非常高。多值模型，类似面向对象的处理方式，例如风机是一种数据模型，可以包括温度、压力等多个测量维度，还包括经纬度、编号等指标信息，这样对外提供服务时会更适合分析的场景。本案例在应用场景中，每台设备的3000个指标不是同时采集和写入，即写入时间戳不对齐，因此用单值建模更灵活，适应性更强，后续增加指标也更方便。而且DolphinDB的sql语句提供了pivot by的功能，若采用单值建模，写入时间不对齐，在查询的时候，pivot by功能可以把多个指标按时间对齐，返回一个二维表，其中每一行是时间，每一列是指标。表结构定义如下：

|列名|数据类型|备注|
|----|-----|-----|
|id	 | INT|指标编号|
|tm	 | DATETIME|时间|
|val | FLOAT|指标值|

本案例的查询和计算主要按月和指标进行，所以数据库按照两层分区，第一层按月分区，第二层按照指标分区。每个指标每月的数据约30MB（86400条/天*30天*12字节/条）。DolphinDB建议每个分区大小控制在100兆左右，所以第二层分区采用范围（RANGE）分区，设置每3个指标为一个分区。参考代码如下：
```
def createDatabase(dbName,tableName){
	tableSchema = table(100:0,`id`tm`val,[INT,DATETIME,FLOAT]);
	db1 = database("",VALUE,2017.01M..2020.12M)
	db2 = database("",RANGE,0..10000*3+1)
	db = database(dbName,COMPO,[db1,db2])
	dfsTable = db.createPartitionedTable(tableSchema,tableName,`tm`id)
}
```

## 3.案例2--多值模式 
#### 3.1 需求描述
现在有300辆列车，每辆车有3000个测点需要采集。具体需求如下：
* 要求每200毫秒采集和写入数据库。
* 数据查询场景需求为：列车数小于等于30；变量数小于等于20；时间范围：1小时、1天、7天、30天。

另外：六种基本类型的数据（Float、Double、Int16、Int32、Int64、Bool），每种类型数据各500列；数据库测点名称命名规则：TAG+数字，TAG0001~TAG3000。

#### 3.2 数据库设计方案设计方案
本案例对每辆车的测点可同时采集和写入数据库，所以用多值模型更适合查询、分析。表结构定义如下：

|列名|数据类型|备注|
|----|-----|-----|
|id	 | INT|列车编号|
|tm	 | TIMESTAMP|时间戳|
|TAG0001-TAG0500 | FLOAT|指标值1-500|
|TAG0501-TAG1000 | DOUBLE|指标值501-1000|
|TAG1001-TAG1500 | FLOAT|指标值1001-1500|
|TAG1501-TAG2000 | DOUBLE|指标值1501-2000|
|TAG2001-TAG2500 | FLOAT|指标值2001-2500|
|TAG2501-TAG3000 | DOUBLE|指标值2501-3000|

本案例的查询和计算主要按天和车辆进行，所以数据库按照两层分区，第一层按天分区，第二层按照车辆分区。每辆车每天的记录数为432,000条。在大数据应用中，对宽表设计，即一个表有几千几百个字段，但是单个应用只会使用一部分字段，在这种情况下，DolphinDB可以适当放大分区上限的范围。因此，我们按查询最多30变量，每变量8字节计算，每辆车每天数据约10MB（43200条*240字节/条），所以第二层分区可采用范围（RANGE）分区，设置每10辆车为一个分区。参考代码如下：
```
def createDatabase(dbName,tableName){
	N=500
	m = "tag" + string(decimalFormat(1..3000,'0000'))
	tableSchema = table(100:0,`trainID`ts join m ,[INT,TIMESTAMP] join take(FLOAT,N) join take(DOUBLE,N) join take(SHORT,N) join take(INT,N) join take(LONG,N) join take(BOOL,N))
	db1 = database("",VALUE,(today()-90)..(today()+60))
	db2 = database("",RANGE,0..30*10+1)
	db = database(dbName,COMPO,[db1,db2])
	db.createPartitionedTable(tableSchema,tableName,`ts`trainID)
}
```
## 4.案例3--维度表 
#### 4.1 需求描述
企业的生产车间内总共有3000个传感设备，每个设备每1秒钟采集一次数据，采集变量包括电池、cpu和内存相关信息共11个指标。需要完成的任务包括：
* 采集到的原始数据存入数据库。
* 有一张设备信息表，包含设备编号、api版本号、制造商、产品型号、操作系统等字段。查询时，除了要求按设备和时间进行简单查询，还要求按这些设备信息进行关联查询和计算。

### 4.2 数据库设计方案设计方案
维度表是分布式数据库中没有分区的表，一般用于存储不频繁更新的小数据集。在DolphinDB中，分布式表可以连接不同数据库中的维度表。虽然我们也可以把2张表合成一张，但这对存储空间有点浪费，所以我们建议把设备信息表设计为维度表。
表结构定义如下：

device_info表

|列名|数据类型|备注|
|----|-----|-----|
|device_id|	SYMBOL|设备编号，格式为“demo“+6位数字|
|api_version|SYMBOL|版本号|
|manufacturer|SYMBOL|制造商|
|model|	SYMBOL|产品型号|
|os_name|SYMBOL|操作系统|

device_readings表

|列名|数据类型|备注|
|----|-----|-----|
|time|	DATETIME|时间戳|
|device_id|	SYMBOL|设备编号|
|battery_level|	INT|电池水平|
|battery_status|SYMBOL|电池状态|
|battery_temperature|DOUBLE|电池温度|
|bssid|	SYMBOL|wifi的bssid|
|cpu_avg_1min|	DOUBLE|最近1分钟cpu平均占用率|
|cpu_avg_5min|	DOUBLE|最近5分钟cpu平均占用率|
|cpu_avg_15min|	DOUBLE|最近1分钟cpu平均占用率|
|mem_free|	LONG|剩余内存|
|mem_used|	LONG|已使用内存|
|rssi|	SHORT|wifi强度|
|ssid|	SYMBOL|wifi的ssid|

reading表的第一层按天分区，第二层按设备分区。每个分区每天的数据约6MB（86400*74字节），所以采用范围分区，每15个设备一个分区。参考代码如下所示：

```
// ----------------- 创建 info维度表
COLS_INFO 		= `device_id`api_version`manufacturer`model`os_name
TYPES_INFO		= `SYMBOL`SYMBOL`SYMBOL`SYMBOL`SYMBOL
schema_info 	= table(COLS_INFO, TYPES_INFO)
db=database("dfs://DolphinDB")
db.createTable(schema_info,`info);

// ----------------- 创建 readings分布式数据库表
COLS_READINGS 	= `time`device_id`battery_level`battery_status`battery_temperature`bssid`cpu_avg_1min`cpu_avg_5min`cpu_avg_15min`mem_free`mem_used`rssi`ssid
TYPES_READINGS  = `DATETIME`SYMBOL`INT`SYMBOL`DOUBLE`SYMBOL`DOUBLE`DOUBLE`DOUBLE`LONG`LONG`SHORT`SYMBOL
schema_readings = table(COLS_READINGS, TYPES_READINGS)
ID_RANGE 	= ('demo' + lpad((0..200* 15)$STRING, 6, "0"))$SYMBOL
db1   = database('', VALUE, 2020.01.01..2020.12.31)
db2   = database('', RANGE, ID_RANGE)
db = database("dfs://DolphinDB",COMPO,[db1,db2])
db.createPartitionedTable(schema_readings,“readings”,`ts`trainID)
```
## 附录：
1.案例完整代码 

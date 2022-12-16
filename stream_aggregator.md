# DolphinDB教程：流数据时序引擎

DolphinDB提供了多种轻量且使用方便的流数据引擎。本教程讲述流数据时序引擎。

## 1. 创建时序引擎

流数据时序引擎由函数`createTimeSeriesEngine`创建。该函数返回一个抽象的表对象，为时序引擎入口。向这个抽象表写入数据，就意味着数据进入时序引擎进行计算。

`createTimeSeriesEngine`函数必须与`subscribeTable`函数配合使用。通过`subscribeTable`函数，时序引擎入口订阅一个流数据表。新数据进入流数据表后会被推送到时序引擎入口，按照指定规则进行计算，并将计算结果输出。

### 1.1 语法

createTimeSeriesEngine(name, windowSize, step, metrics, dummyTable, outputTable, [timeColumn], [useSystemTime=false], [keyColumn], [garbageSize], [updateTime], [useWindowStartTime], [roundTime=true], [snapshotDir], [snapshotIntervalInMsgCount], [fill='none'])

### 1.2 参数介绍

本节对各参数进行简单介绍。在下一小节中，对部分参数结合实例进行详细介绍。

- name

类型: 字符串

必选参数，表示时序引擎的名称，是时序引擎在一个数据节点上的唯一标识。可包含字母，数字和下划线，但必须以字母开头。

- useSystemTime

类型：布尔值

可选参数，表示时序引擎计算的触发方式。

当参数值为true时，引擎会按照数据进入引擎的时刻（毫秒精度的本地系统时间，与数据中的时间列无关），每隔固定时间截取固定长度窗口的流数据进行计算。只要一个数据窗口中含有数据，数据窗口结束后就会自动进行计算。结果中的第一列为计算发生的时间戳，与数据中的时间无关。

当参数值为false（默认值）时，引擎根据流数据中的timeColumn列来截取数据窗口。一个数据窗口结束后的第一条新数据才会触发该数据窗口的计算。请注意，触发计算的数据并不会参与该次计算。

例如，一个数据窗口从10:10:10到10:10:19。若useSystemTime=true，则只要该窗口中至少有一条数据，该窗口的计算会在窗口结束后的10:10:20触发。若useSystemTime=false，且10:10:19后的第一条数据为10:10:25，则该窗口的计算会在10:10:25触发。

- windowSize

类型：整型或者整型的数组

必选参数，指定数据窗口长度。数据窗口包含左边界，但不包含右边界。

- step

类型：整型

必选参数，指定窗口每次移动的时间间隔。windowSize必须可被step整除。

windowSize与step的单位取决于useSystemTime参数。若useSystemTime=true，windowSize与step的单位是毫秒。若useSystemTime=false，windowSize与step的单位是timeColumn列的精度。例如，若timeColumn列是timestamp类型，那么windowSize与step的单位是毫秒；如果timeColumn列是datetime类型，那么windowSize与step的单位是秒。

为了方便观察和对比计算结果，系统会对第一个数据窗口的起始时刻进行规整。例如若第一条数据进入引擎的时刻为2018.10.10T03:26:39.178，且step=100，那么系统会将第一个窗口起始时间规整为2018.10.10T03:26:39.100。规整数据窗口的细节在第1.3.1小节中介绍。

当引擎使用分组计算时，所有分组的窗口均进行统一的规整。相同时刻的数据窗口在各组均有相同的边界。

- metrics

类型：元代码或者元代码的数组

必选参数。引擎的核心参数，以元代码的格式表示计算公式。它可以是一个或多个系统内置或用户自定义的聚合函数，比如<[sum(volume),avg(price)]>；可对聚合结果使用表达式，比如<[avg(price1)-avg(price2)]>；也可对列与列的计算结果进行聚合计算，例如<[std(price1-price2)]>；也可以是一个函数返回多个指标。若自定义函数 func(price)返回两个结果，则可以指定metrics为<[func(price) as ['res1','res2']> 。

如果windowSize为数组，则metrics必须和windowSize大小一致的数组，一一对应计算。比如定义windowSize=[3,6], metrics=[<[sum(volume),avg(price)]>, <std(volume)>], 则sum(volume)和avg(price)按windowSize=3聚合，std(volume)按windowSize=6聚合。

DolphinDB 针对部分内置的聚合函数在流数据时序引擎中的使用进行了优化，最大程度降低了重复计算，显著提高运行速度，详情参照用户手册[createTimeSeriesEngine](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/c/createTimeSeriesEngine.html)函数。


- dummyTable

类型：表

必选参数。该表的唯一作用是为引擎提供流数据中每一列的数据类型，可以含有数据，亦可为空表。该表的schema必须与订阅的流数据表相同。

- outputTable

类型：表

必选参数，为结果的输出表。

在使用`createTimeSeriesEngine`函数之前，需要将输出表预先设立为一个空表，并指定各列列名以及数据类型。流数据引擎会将计算结果插入该表。

输出表的schema需要遵循以下规范：

(1) 输出表的第一列必须是时间类型。若useSystemTime=true，为TIMESTAMP类型；若useSystemTime=false，数据类型与timeColumn列一致。

(2) 如果分组列keyColumn参数不为空，那么输出表的第二列必须是分组列。

(3) 最后保存计算结果。

输出表的schema为"时间列，分组列(可选)，结果列1，结果列2..."这样的格式。

- timeColumn

类型：字符串

可选参数。当useSystemTime=false时，指定订阅的流数据表中时间列的名称。

- keyColumn

类型：字符串标量

可选参数，表示分组字段名。若设置，则分组进行计算，例如以每支股票为一组进行计算。

- garbageSize

类型：整型

随着订阅的流数据在时序引擎中不断积累，存放在内存中的数据会越来越多，这时需要清理不再需要的历史数据。当内存中历史数据行数超过garbageSize值时，系统会清理本次计算不需要的历史数据。garbageSize的默认值是50,000。

如果指定了keyColumn，内存清理是各组内独立进行的。当一个组在内存中的历史数据记录数超出garbageSize时，会清理该组中本次计算中不需要的历史数据。

- updateTime

类型：整型

如果没有指定updateTime，一个数据窗口结束前，不会发生对该数据窗口数据的计算。若要求在当前窗口结束前对当前窗口已有数据进行计算，可指定updateTime。step必须是updateTime的整数倍。要设置updateTime，useSystemTime必须设为false。

如果指定了updateTime，当前窗口内可能会发生多次计算。这些计算触发的规则为：

(1) 将当前窗口分为windowSize/updateTime个小窗口，每个小窗口长度为updateTime。一个小窗口结束后，若有一条新数据到达，且在此之前当前窗口内有未参加计算的的数据，会触发一次计算。请注意，该次计算不包括这条新数据。

(2) 一条数据到达时序引擎之后经过2\*updateTime（若2\*updateTime不足2秒，则设置为2秒），若其仍未参与计算，会触发一次计算。该次计算包括当时当前窗口内的所有数据。

若分组计算，则每组内进行上述操作。

请注意，当前窗口内每次计算结果的时间戳均为当前数据窗口开始时间或开始时间 + windowSize（由参数useWindowStartTime决定），而非当前窗口内的时刻。

如果指定了updateTime，输出表必须是键值内存表（使用`keyedTable`函数创建）：如果没有指定keyColumn，输出表的主键是timeColumn；如果指定了keyColumn，输出表的主键是timeColumn和keyColumn。输出表若使用普通内存表或流数据表，每次计算均会增加一条记录，会产生大量带有相同时间戳的结果。输出表亦不可为键值流数据表，因为键值流数据表不可更新记录。

1.3.6小节使用例子详细介绍了指定updateTime参数后的计算过程。

- useWindowStartTime

类型：布尔类型

可选参数，表示输出表中的时间是否为数据窗口起始时间。默认值为false，表示输出表中的时间为数据窗口起始时间 + windowSize。如果windowSize为多个窗口大小，则必须为fasle。

- roundTime

类型：布尔类型

可选参数，是一个布尔值，表示若数据时间精度为毫秒或者秒且step>一分钟，如何对窗口边界值进行规整处理。默认值为true，表示按照既定的多分钟规则进行规整。若为false，则按一分钟规则进行窗口规整。细节请参阅 1.3.1 小节中有关 step 部分的alignmentSize取值规则。

- snapshotDir

类型：字符串类型

可选参数，表示保存引擎快照的文件目录，可以用于系统出现异常之后，对引擎进行恢复。该目录必须存在，否则系统会提示异常。创建流数据引擎的时候，如果指定了snapshotDir，也会检查相应的快照是否存在。如果存在，会加载该快照，恢复引擎的状态。

- snapshotIntervalInMsgCount

类型：整型

可选参数，表示保存引擎快照的消息间隔。

- fill
    - 'none': 不输出结果。
    - 'null': 输出结果为NULL.
    - 'ffill': 输出上一个有数据的窗口的结果。
    - '具体数值'：该值的数据类型需要和对应的metrics计算结果的类型保持一致。

可选参数，是一个标量或向量，表示若（某个key的）某个窗口无数据时，如何处理。可取如上值。


fill可以输入向量，为每个metrics指定不同的fill方式。其中，向量中各项只能是'null', 'ffill'或一个数值，不能是'none'。

### 1.3 参数详细介绍及用例

#### 1.3.1 step

系统按照数据时间精度以及参数step的值确定一个规整尺度alignmentSize，对第一个数据窗口的边界值进行规整处理。

若timeColumn精度为秒，如DATETIME或SECOND类型，alignmentSize取值规则如下表：

step | alignmentSize
---|---
0~2 |2
3 |3
4~5 |5
6~10|10
11~15|15
16~20|20
21~30|30
31~60|60

如果 roundTime = false, 对于step > 60, alignmentSize 都为60。 如果 roundTime = true，则alignmentSize取值规则如下表：

| step      | alignmentSize  |
| --------- | -------------- |
| 61～120   | 120（2分钟）   |
| 121~180   | 180（3分钟）   |
| 181~300   | 300（5分钟）   |
| 301~600   | 600（10分钟）  |
| 601~900   | 900（15分钟）  |
| 901~1200  | 1200（20分钟） |
| 1201~1800 | 1800（30分钟） |
| >1800     | 3600（1小时）  |

若数据时间精度为毫秒，如TIMESTAMP或TIME类型，alignmentSize取值规则如下表：

step | alignmentSize
---|---
0~2 |2
3~5 |5
6~10 |10
11~20 |20
21~25 |25
26~50|50
51~100|100
101~200|200
201~250|250
251~500|500
501~1000|1000（1秒）
1001~2000|2000（2秒）
2001~3000|3000（3秒）
3001~5000|5000（5秒）
5001~10000|10000（10秒）
10001~15000|15000（15秒）
15001~20000|20000（20秒）
20001~30000|30000（30秒）
30001~60000|60000（1分钟）

如果 roundTime = false, 对于step > 60000, alignmentSize 都为60000。 如果 roundTime = true，则alignmentSize取值规则如下表：

| step            | alignmentSize     |
| --------------- | ----------------- |
| 60001~120000    | 120000（2分钟）   |
| 120001~180000   | 180000（3分钟）   |
| 120001~300000   | 300000（5分钟）   |
| 300001~600000   | 600000（10分钟）  |
| 600001~900000   | 900000（15分钟）  |
| 900001~1200000  | 1200000（20分钟） |
| 1200001~1800000 | 1800000（30分钟） |
| \>= 1800001     | 3600000（1小时）  |

DolphinDB系统将各种时间类型数据存储为以最小精度为单位的整形。例如，13:30:10存储为13\*60\*60+30\*60+10=48610。系统将第一个数据窗口的左边界规整为第一条数据时刻之前最后一个可被alignmentSize整除的时刻。

若第一条数据时刻为x，数据类型为TIMESTAMP，那么第一个数据窗口的左边界经过规整后为timestamp(x/alignmentSize\*alignmentSize)，其中`/`代表相除后取整。例如，若第一条数据的时间为2018.10.08T01:01:01.365，step为60000，那么alignmentSize为60000，第一个数据窗口的左边界为timestamp(2018.10.08T01:01:01.365/60000*60000)，即2018.10.08T01:01:00.000。

下例说明数据窗口如何规整以及流数据时序引擎如何进行计算。以下代码建立流数据表trades，包含time和volume两列。创建时序引擎streamAggr1，每3毫秒对过去6毫秒的数据计算sum(volume)。time列的精度为毫秒，模拟插入的数据流频率也设为每毫秒一条数据。
```
share streamTable(1000:0, `time`volume, [TIMESTAMP, INT]) as trades
outputTable = table(10000:0, `time`sumVolume, [TIMESTAMP, INT])
tradesAggregator = createTimeSeriesEngine(name="streamAggr1", windowSize=6, step=3, metrics=<[sum(volume)]>, dummyTable=trades, outputTable=outputTable, timeColumn=`time)
subscribeTable(tableName="trades", actionName="append_tradesAggregator", offset=0, handler=append!{tradesAggregator}, msgAsTable=true)    
```

向流数据表trades中写入10条数据，并查看流数据表trades内容：
```
def writeData(t, n){
    timev = 2018.10.08T01:01:01.001 + timestamp(1..n)
    volumev = take(1, n)
    insert into t values(timev, volumev)
}
writeData(trades, 10)

select * from trades;
```
time	|volume
---|---
2018.10.08T01:01:01.002	|1
2018.10.08T01:01:01.003	|1
2018.10.08T01:01:01.004	|1
2018.10.08T01:01:01.005	|1
2018.10.08T01:01:01.006	|1
2018.10.08T01:01:01.007	|1
2018.10.08T01:01:01.008	|1
2018.10.08T01:01:01.009	|1
2018.10.08T01:01:01.010	|1
2018.10.08T01:01:01.011	|1

再查看结果表outputTable:
```
select * from outputTable;
```
time|sumVolume
---|---
2018.10.08T01:01:01.003	|1
2018.10.08T01:01:01.006	|4
2018.10.08T01:01:01.009	|6

根据第一条数据时刻规整第一个窗口的起始时间后，窗口以step为步长移动。下面详细解释时序引擎的计算过程。为简便起见，以下提到时间时，省略相同的2018.10.08T01:01:01部分，只列出毫秒部分。基于第一行数据的时间002，第一个窗口的起始时间规整为000，到002结束，只包含002一条记录，计算被003记录触发，sum(volume)的结果是1；第二个窗口从000到005，包含了四条数据，计算被006记录触发，计算结果为4；第三个窗口从003到008，包含6条数据，计算被009记录触发，计算结果为6。虽然第四个窗口从006到011且含有6条数据，但是由于该窗口结束之后没有数据，所以该窗口的计算没有被触发。

若需要重复执行以上程序，应首先解除订阅，并将流数据表trades与时序引擎streamAggr1二者删除：
```
unsubscribeTable(tableName="trades", actionName="append_tradesAggregator")
undef(`trades, SHARED)
dropStreamEngine("streamAggr1")
```

#### 1.3.2 windowSize

DolphinDB时序引擎支持多个窗口。

下例说如何对相同的metrics按不同的windowSize聚合。以下代码建立流数据表trades，包含time和volume两列。创建时序引擎streamAggr1，每3毫秒对过去6毫秒和过去12毫秒的数据计算sum(volume)。time列的精度为毫秒，模拟插入的数据流频率也设为每毫秒一条数据。

```
share streamTable(1000:0, `time`volume, [TIMESTAMP, INT]) as trades
outputTable = table(10000:0, `time`sumVolume1`sumVolume2, [TIMESTAMP, INT,INT])
tradesAggregator = createTimeSeriesEngine(name="streamAggr1", windowSize=[6,12], step=3, metrics=[<sum(volume)>,<sum(volume)>], dummyTable=trades, outputTable=outputTable, timeColumn=`time)
subscribeTable(tableName="trades", actionName="append_tradesAggregator", offset=0, handler=append!{tradesAggregator}, msgAsTable=true)    
```

```
def writeData(t, n){
    timev = 2018.10.08T01:01:01.001 + timestamp(1..n)
    volumev = take(1, n)
    insert into t values(timev, volumev)
}
writeData(trades, 20)

select * from trades;
```

再查看结果表outputTable:

```
select * from outputTable;
```

| time                    | sumVolume1 | sumVolume2 |
| ----------------------- | ---------- | ---------- |
| 2018.10.08T01:01:01.003 | 1          | 1          |
| 2018.10.08T01:01:01.006 | 4          | 4          |
| 2018.10.08T01:01:01.009 | 6          | 7          |
| 2018.10.08T01:01:01.012 | 6          | 10         |
| 2018.10.08T01:01:01.015 | 6          | 12         |
| 2018.10.08T01:01:01.018 | 6          | 12         |
| 2018.10.08T01:01:01.021 | 6          | 12         |

#### 1.3.3 metrics

DolphinDB时序引擎支持使用多种表达式进行实时计算。

- 一个或多个聚合函数：
```
tsAggregator = createTimeSeriesEngine(name="streamAggr1", windowSize=6, step=3, metrics=<sum(ask)>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)
```

- 使用聚合结果进行计算：
```
tsAggregator = createTimeSeriesEngine(name="streamAggr1", windowSize=6, step=3, metrics=<max(ask)-min(ask)>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)
```

- 对列与列的操作结果进行聚合计算：
```
tsAggregator = createTimeSeriesEngine(name="streamAggr1", windowSize=6, step=3, metrics=<max(ask-bid)>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)
```

- 输出多个聚合结果
```
tsAggregator = createTimeSeriesEngine(name="streamAggr1", windowSize=6, step=3, metrics=<[max((ask-bid)/(ask+bid)*2), min((ask-bid)/(ask+bid)*2)]>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)
```

- 使用多参数聚合函数
```
tsAggregator = createTimeSeriesEngine(name="streamAggr1", windowSize=6, step=3, metrics=<corr(ask,bid)>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)

tsAggregator = createTimeSeriesEngine(name="streamAggr1", windowSize=6, step=3, metrics=<percentile(ask-bid,99)/sum(ask)>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)
```

- 使用自定义函数
```
defg diff(x,y){
	return sum(x)-sum(y)
}
tsAggregator = createTimeSeriesEngine(name="streamAggr1", windowSize=6, step=3, metrics=<diff(ask, bid)>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)
```

- 使用多个返回结果的函数

```
defg sums(x){
	return [sum(x),sum2(x)]
}
tsAggregator = createTimeSeriesEngine(name="streamAggr1", windowSize=6, step=3, metrics=<sums(ask) as `sumAsk`sum2Ask>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)

```

注意：不支持聚合函数嵌套调用，例如sum(spread(ask,bid))。


#### 1.3.4 dummyTable

系统利用dummyTable的schema来决定订阅的流数据中每一列的数据类型。dummyTable有无数据对结果没有任何影响。
```
share streamTable(1000:0, `time`volume, [TIMESTAMP, INT]) as trades
modelTable = table(1000:0, `time`volume, [TIMESTAMP, INT])
outputTable = table(10000:0, `time`sumVolume, [TIMESTAMP, INT])
tradesAggregator = createTimeSeriesEngine(name="streamAggr1", windowSize=5, step=5, metrics=<[sum(volume)]>, dummyTable=modelTable, outputTable=outputTable, timeColumn=`time)
subscribeTable(tableName="trades", actionName="append_tradesAggregator", offset=0, handler=append!{tradesAggregator}, msgAsTable=true)    

def writeData(t,n){
    timev = 2018.10.08T01:01:01.001 + timestamp(1..n)
    volumev = take(1, n)
    insert into t values(timev, volumev)
}

writeData(trades, 6)

sleep(1)
select * from outputTable
```

#### 1.3.5 outputTable

计算结果可以输出到内存表或流数据表。输出到内存表的数据可以更新或删除，而输出到流数据表的数据无法更新或删除，但是可以通过流数据表将结果作为另一个引擎的数据源再次发布。

下例中，时序引擎electricityAggregator1订阅流数据表electricity，进行移动均值计算，并将结果输出到流数据表outputTable1。时序引擎electricityAggregator2订阅outputTable1表，并对移动均值计算结果求移动峰值。
```
share streamTable(1000:0,`time`voltage`current,[TIMESTAMP,DOUBLE,DOUBLE]) as electricity

//将第一个时序引擎的输出表定义为流数据表，可以再次订阅
share streamTable(10000:0,`time`avgVoltage`avgCurrent,[TIMESTAMP,DOUBLE,DOUBLE]) as outputTable1 

electricityAggregator1 = createTimeSeriesEngine(name="electricityAggregator1", windowSize=10, step=10, metrics=<[avg(voltage), avg(current)]>, dummyTable=electricity, outputTable=outputTable1, timeColumn=`time, garbageSize=2000)
subscribeTable(tableName="electricity", actionName="avgElectricity", offset=0, handler=append!{electricityAggregator1}, msgAsTable=true)

//订阅计算结果，再次进行聚合计算
outputTable2 =table(10000:0, `time`maxVoltage`maxCurrent, [TIMESTAMP,DOUBLE,DOUBLE])
electricityAggregator2 = createTimeSeriesEngine(name="electricityAggregator2", windowSize=100, step=100, metrics=<[max(avgVoltage), max(avgCurrent)]>, dummyTable=outputTable1, outputTable=outputTable2, timeColumn=`time, garbageSize=2000)
subscribeTable(tableName="outputTable1", actionName="maxElectricity", offset=0, handler=append!{electricityAggregator2}, msgAsTable=true);

//向electricity表中插入500条数据
def writeData(t, n){
        timev = 2018.10.08T01:01:01.000 + timestamp(1..n)
        voltage = 1..n * 0.1
        current = 1..n * 0.05
        insert into t values(timev, voltage, current)
}
writeData(electricity, 500);
```
聚合计算结果:
```
select * from outputTable2;
```
time	|maxVoltage	|maxCurrent
---|---|---
2018.10.08T01:01:01.100	|8.45	|4.225
2018.10.08T01:01:01.200	|18.45	|9.225
2018.10.08T01:01:01.300	|28.45	|14.225
2018.10.08T01:01:01.400	|38.45	|19.225
2018.10.08T01:01:01.500	|48.45	|24.225

若要对上述脚本进行重复使用，需先执行以下脚本以清除共享表、订阅以及流数据引擎：
```
unsubscribeTable(tableName="electricity", actionName="avgElectricity")
undef(`electricity, SHARED)
unsubscribeTable(tableName="outputTable1", actionName="maxElectricity")
undef(`outputTable1, SHARED)
dropStreamEngine("electricityAggregator1")
dropStreamEngine("electricityAggregator2")
```

#### 1.3.6 keyColumn

下例中，设定keyColumn参数为sym。
```
share streamTable(1000:0, `time`sym`volume, [TIMESTAMP, SYMBOL, INT]) as trades
outputTable = table(10000:0, `time`sym`sumVolume, [TIMESTAMP, SYMBOL, INT])
tradesAggregator = createTimeSeriesEngine(name="streamAggr1", windowSize=3, step=3, metrics=<[sum(volume)]>, dummyTable=trades, outputTable=outputTable, timeColumn=`time, useSystemTime=false, keyColumn=`sym, garbageSize=50)
subscribeTable(tableName="trades", actionName="append_tradesAggregator", offset=0, handler=append!{tradesAggregator}, msgAsTable=true)    

def writeData(t, n){
    timev = 2018.10.08T01:01:01.001 + timestamp(1..n)
    symv =take(`A`B, n)
    volumev = take(1, n)
    insert into t values(timev, symv, volumev)
}

writeData(trades, 6)
```
为了方便观察，对"trades"表的sym列排序输出：
```
select * from trades order by sym;
```
time|sym|volume
---|---|---
2018.10.08T01:01:01.002	|A	|1
2018.10.08T01:01:01.004	|A	|1
2018.10.08T01:01:01.006	|A	|1
2018.10.08T01:01:01.003	|B	|1
2018.10.08T01:01:01.005	|B	|1
2018.10.08T01:01:01.007	|B	|1

分组计算结果：
```
select * from outputTable; 
```
time	|sym|	sumVolume
---|---|---
2018.10.08T01:01:01.003	|A|	1
2018.10.08T01:01:01.006	|A|	1
2018.10.08T01:01:01.006	|B|	2

各组窗口规整后统一从000时间点开始，根据windowSize=3以及step=3，每个组的窗口会按照000-003-006划分。
- (1) 在003，B组有一条数据，但是由于B组在第一个窗口没有任何数据，不会进行计算也不会产生结果，所以B组第一个窗口没有结果输出。
- (2) 004的A组数据触发A组第一个窗口的计算。
- (3) 006的A组数据触发A组第二个窗口的计算。
- (4) 007的B组数据触发B组第二个窗口的计算。

如果进行分组聚合计算，流数据源中的每个分组中的'timeColumn'必须是递增的，但是整个数据源的'timeColumn'可以不是递增的；如果没有进行分组聚合，那么整个数据源的'timeColumn'必须是递增的，否则时序引擎的输出结果会与预期不符。

#### 1.3.7 updateTime

通过以下两个例子，可以理解updateTime的作用。

首先创建流数据表并写入数据：
```
share streamTable(1000:0, `time`sym`volume, [TIMESTAMP, SYMBOL, INT]) as trades
insert into trades values(2018.10.08T01:01:01.785,`A,10)
insert into trades values(2018.10.08T01:01:02.125,`B,26)
insert into trades values(2018.10.08T01:01:10.263,`B,14)
insert into trades values(2018.10.08T01:01:12.457,`A,28)
insert into trades values(2018.10.08T01:02:10.789,`A,15)
insert into trades values(2018.10.08T01:02:12.005,`B,9)
insert into trades values(2018.10.08T01:02:30.021,`A,10)
insert into trades values(2018.10.08T01:04:02.236,`A,29)
insert into trades values(2018.10.08T01:04:04.412,`B,32)
insert into trades values(2018.10.08T01:04:05.152,`B,23);
```

- 不指定updateTime：
```
output1 = table(10000:0, `time`sym`sumVolume, [TIMESTAMP, SYMBOL, INT])
agg1 = createTimeSeriesEngine(name="agg1", windowSize=60000, step=60000, metrics=<[sum(volume)]>, dummyTable=trades, outputTable=output1, timeColumn=`time, useSystemTime=false, keyColumn=`sym, garbageSize=50, useWindowStartTime=false)
subscribeTable(tableName="trades", actionName="agg1", offset=0, handler=append!{agg1}, msgAsTable=true)

sleep(10)

select * from output1;
```

time                    |sym| sumVolume
----------------------- |---| ------
2018.10.08T01:02:00.000 |A   |38    
2018.10.08T01:03:00.000 |A   |25    
2018.10.08T01:02:00.000 |B   |40   
2018.10.08T01:03:00.000 |B   |9   

- 将updateTime设为1000：
```
output2 = keyedTable(`time`sym,10000:0, `time`sym`sumVolume, [TIMESTAMP, SYMBOL, INT])
agg2 = createTimeSeriesEngine(name="agg2", windowSize=60000, step=60000, metrics=<[sum(volume)]>, dummyTable=trades, outputTable=output2, timeColumn=`time, useSystemTime=false, keyColumn=`sym, garbageSize=50, updateTime=1000, useWindowStartTime=false)
subscribeTable(tableName="trades", actionName="agg2", offset=0, handler=append!{agg2}, msgAsTable=true)

sleep(2010)

select * from output2;
```

time                    |sym| sumVolume
----------------------- |---| ------
2018.10.08T01:02:00.000 |A   |38    
2018.10.08T01:03:00.000 |A   |25    
2018.10.08T01:02:00.000 |B   |40   
2018.10.08T01:03:00.000 |B   |9   
2018.10.08T01:05:00.000 |B   |55   
2018.10.08T01:05:00.000 |A   |29     

下面我们介绍以上两个例子在最后一个数据窗口（01:04:00.000到01:05:00.000）的区别。为简便起见，我们省略日期部分，只列出（小时:分钟:秒.毫秒）部分。假设time列时间亦为数据进入时序引擎的时刻。

(1) 在01:04:04.236时，A分组的第一条记录到达后已经过2000毫秒，触发一次A组计算，输出表增加一条记录(01:05:00.000, `A, 29)。

(2) 在01:04:05.152时的B组记录为01:04:04.412所在小窗口[01:04:04.000, 01:04:05.000)之后第一条记录，触发一次B组计算，输出表增加一条记录(01:05:00.000,"B",32)。

(3) 2000毫秒后，在01:04:07.152时，由于01:04:05.152时的B组记录仍未参与计算，触发一次B组计算，输出一条记录(01:05:00.000,"B",55)。由于输出表的主键为time和sym，并且输出表中已有(01:05:00.000,"B",32)这条记录，因此将该记录更新为(01:05:00.000,"B",55)。

#### 1.3.7 snapshot

通过以下这个例子，可以理解snapshotDir和snapshotIntervalInMsgCount的作用。如果启用snapshot，引擎订阅流表时，handler需是appendMsg函数，需指定handlerNeedMsgId=true，用来记录快照的消息位置。

```
share streamTable(10000:0,`time`sym`price`id, [TIMESTAMP,SYMBOL,INT,INT]) as trades
output1 =table(10000:0, `time`sumprice, [TIMESTAMP,INT]);
Agg1 = createTimeSeriesEngine(name=`Agg1, windowSize=100, step=50, metrics=<sum(price)>, dummyTable=trades, outputTable=output1, timeColumn=`time, snapshotDir="/home/server1/snapshotDir", snapshotIntervalInMsgCount=100)
subscribeTable(server="", tableName="trades", actionName="Agg1",offset= 0, handler=appendMsg{Agg1}, msgAsTable=true, handlerNeedMsgId=true)

n=500
timev=timestamp(1..n) + 2021.03.12T15:00:00.000
symv = take(`abc`def, n)
pricev = int(1..n)
id = take(-1, n)
insert into trades values(timev, symv, pricev, id)

select * from output1
```

| time                    | sumprice |
| ----------------------- | -------- |
| 2021.03.12T15:00:00.050 | 1225     |
| 2021.03.12T15:00:00.100 | 4950     |
| 2021.03.12T15:00:00.150 | 9950     |
| 2021.03.12T15:00:00.200 | 14950    |
| 2021.03.12T15:00:00.250 | 19950    |
| 2021.03.12T15:00:00.300 | 24950    |
| 2021.03.12T15:00:00.350 | 29950    |
| 2021.03.12T15:00:00.400 | 34950    |
| 2021.03.12T15:00:00.450 | 39950    |
| 2021.03.12T15:00:00.500 | 44950    |

```
getSnapshotMsgId(Agg1)
>499
```

取消订阅并删除引擎来模拟系统异常

```
unsubscribeTable(, "trades", "Agg1")
dropStreamEngine("Agg1")
Agg1=NULL
```

此时发布端仍在写入数据

```
n=500
timev=timestamp(501..1000) + 2021.03.12T15:00:00.000
symv = take(`abc`def, n)
pricev = int(1..n)
id = take(-1, n)
insert into trades values(timev, symv, pricev, id)
```

再次创建aggr, 加载snapshot，从上次处理最后一条消息开始重新订阅

```
Agg1 = createTimeSeriesEngine(name=`Agg1, windowSize=100, step=50, metrics=<sum(price)>, dummyTable=trades, outputTable=output1, timeColumn=`time, snapshotDir="/home/server1/snapshotDir", snapshotIntervalInMsgCount=100)

ofst=getSnapshotMsgId(Agg1)
print(ofst)
>499

subscribeTable(server="", tableName="trades", actionName="Agg1",offset=ofst+1, handler=appendMsg{Agg1}, msgAsTable=true, handlerNeedMsgId=true)

select * from output1
```

| time                        | sumprice  |
| :-------------------------- | --------- |
| 2021.03.12T15:00:00.050     | 1225      |
| 2021.03.12T15:00:00.100     | 4950      |
| 2021.03.12T15:00:00.150     | 9950      |
| 2021.03.12T15:00:00.200     | 14950     |
| 2021.03.12T15:00:00.250     | 19950     |
| 2021.03.12T15:00:00.300     | 24950     |
| 2021.03.12T15:00:00.350     | 29950     |
| 2021.03.12T15:00:00.400     | 34950     |
| 2021.03.12T15:00:00.450     | 39950     |
| 2021.03.12T15:00:00.500     | 44950     |
| **2021.03.12T15:00:00.550** | **25450** |
| **2021.03.12T15:00:00.600** | **5450**  |
| 2021.03.12T15:00:00.650     | 9950      |
| 2021.03.12T15:00:00.700     | 14950     |
| 2021.03.12T15:00:00.750     | 19950     |
| 2021.03.12T15:00:00.800     | 24950     |
| 2021.03.12T15:00:00.850     | 29950     |
| 2021.03.12T15:00:00.900     | 34950     |
| 2021.03.12T15:00:00.950     | 39950     |
| 2021.03.12T15:00:01.000     | 44950     |

结果和订阅不中断一样。

```
share streamTable(10000:0,`time`sym`price`id, [TIMESTAMP,SYMBOL,INT,INT]) as trades
output1 =table(10000:0, `time`sumprice, [TIMESTAMP,INT]);
Agg1 = createTimeSeriesEngine(name=`Agg1, windowSize=100, step=50, metrics=<sum(price)>, dummyTable=trades, outputTable=output1, timeColumn=`time)
subscribeTable(server="", tableName="trades", actionName="Agg1",offset= 0, handler=append!{Agg1}, msgAsTable=true)

n=500
timev=timestamp(1..n) + 2021.03.12T15:00:00.000
symv = take(`abc`def, n)
pricev = int(1..n)
id = take(-1, n)
insert into trades values(timev, symv, pricev, id)

n=500
timev=timestamp(501..1000) + 2021.03.12T15:00:00.000
symv = take(`abc`def, n)
pricev = int(1..n)
id = take(-1, n)
insert into trades values(timev, symv, pricev, id)

select * from output1
```

| time                        | sumprice  |
| :-------------------------- | --------- |
| 2021.03.12T15:00:00.050     | 1225      |
| 2021.03.12T15:00:00.100     | 4950      |
| 2021.03.12T15:00:00.150     | 9950      |
| 2021.03.12T15:00:00.200     | 14950     |
| 2021.03.12T15:00:00.250     | 19950     |
| 2021.03.12T15:00:00.300     | 24950     |
| 2021.03.12T15:00:00.350     | 29950     |
| 2021.03.12T15:00:00.400     | 34950     |
| 2021.03.12T15:00:00.450     | 39950     |
| 2021.03.12T15:00:00.500     | 44950     |
| **2021.03.12T15:00:00.550** | **25450** |
| **2021.03.12T15:00:00.600** | **5450**  |
| 2021.03.12T15:00:00.650     | 9950      |
| 2021.03.12T15:00:00.700     | 14950     |
| 2021.03.12T15:00:00.750     | 19950     |
| 2021.03.12T15:00:00.800     | 24950     |
| 2021.03.12T15:00:00.850     | 29950     |
| 2021.03.12T15:00:00.900     | 34950     |
| 2021.03.12T15:00:00.950     | 39950     |
| 2021.03.12T15:00:01.000     | 44950     |

如果不开启snapshot，即使从上次中断的地方开始订阅，得到的结果也与订阅不中断不一样。

```
share streamTable(10000:0,`time`sym`price`id, [TIMESTAMP,SYMBOL,INT,INT]) as trades
output1 =table(10000:0, `time`sumprice, [TIMESTAMP,INT]);
Agg1 = createTimeSeriesEngine(name=`Agg1, windowSize=100, step=50, metrics=<sum(price)>, dummyTable=trades, outputTable=output1, timeColumn=`time)
subscribeTable(server="", tableName="trades", actionName="Agg1",offset= 0, handler=append!{Agg1}, msgAsTable=true)

n=500
timev=timestamp(1..n) + 2021.03.12T15:00:00.000
symv = take(`abc`def, n)
pricev = int(1..n)
id = take(-1, n)
insert into trades values(timev, symv, pricev, id)

unsubscribeTable(, "trades", "Agg1")
dropStreamEngine("Agg1")
Agg1=NULL

n=500
timev=timestamp(501..1000) + 2021.03.12T15:00:00.000
symv = take(`abc`def, n)
pricev = int(1..n)
id = take(-1, n)
insert into trades values(timev, symv, pricev, id)

Agg1 = createTimeSeriesEngine(name=`Agg1, windowSize=100, step=50, metrics=<sum(price)>, dummyTable=trades, outputTable=output1, timeColumn=`time)
subscribeTable(server="", tableName="trades", actionName="Agg1",offset= 500, handler=append!{Agg1}, msgAsTable=true)

select * from output1
```

| time                        | sumprice |
| :-------------------------- | -------- |
| 2021.03.12T15:00:00.050     | 1225     |
| 2021.03.12T15:00:00.100     | 4950     |
| 2021.03.12T15:00:00.150     | 9950     |
| 2021.03.12T15:00:00.200     | 14950    |
| 2021.03.12T15:00:00.250     | 19950    |
| 2021.03.12T15:00:00.300     | 24950    |
| 2021.03.12T15:00:00.350     | 29950    |
| 2021.03.12T15:00:00.400     | 34950    |
| 2021.03.12T15:00:00.450     | 39950    |
| 2021.03.12T15:00:00.500     | 44950    |
| **2021.03.12T15:00:00.550** | **1225** |
| **2021.03.12T15:00:00.600** | **4950** |
| 2021.03.12T15:00:00.650     | 9950     |
| 2021.03.12T15:00:00.700     | 14950    |
| 2021.03.12T15:00:00.750     | 19950    |
| 2021.03.12T15:00:00.800     | 24950    |
| 2021.03.12T15:00:00.850     | 29950    |
| 2021.03.12T15:00:00.900     | 34950    |
| 2021.03.12T15:00:00.950     | 39950    |
| 2021.03.12T15:00:01.000     | 44950    |

## 2. 过滤流数据

使用`subscribeTable`函数时，可利用handler参数过滤订阅的流数据。

在下例中，传感器采集电压和电流数据并实时上传作为流数据源，其中电压voltage<=122或电流current=NULL的数据需要在进入时序引擎之前过滤掉。
```
share streamTable(1000:0, `time`voltage`current, [TIMESTAMP, DOUBLE, DOUBLE]) as electricity
outputTable = table(10000:0, `time`avgVoltage`avgCurrent, [TIMESTAMP, DOUBLE, DOUBLE])

//自定义数据处理过程，过滤 voltage<=122 或 current=NULL的无效数据。
def append_after_filtering(inputTable, msg){
	t = select * from msg where voltage>122, isValid(current)
	if(size(t)>0){
		insert into inputTable values(t.time,t.voltage,t.current)		
	}
}
electricityAggregator = createTimeSeriesEngine(name="electricityAggregator", windowSize=6, step=3, metrics=<[avg(voltage), avg(current)]>, dummyTable=electricity, outputTable=outputTable, timeColumn=`time, garbageSize=2000)
subscribeTable(tableName="electricity", actionName="avgElectricity", offset=0, handler=append_after_filtering{electricityAggregator}, msgAsTable=true)

//模拟产生数据
def writeData(t, n){
        timev = 2018.10.08T01:01:01.001 + timestamp(1..n)
        voltage = 120+1..n * 1.0
        current = take([1,NULL,2]*0.1, n)
        insert into t values(timev, voltage, current);
}
writeData(electricity, 10)
```
流数据表：
```
select * from electricity
```
time	|voltage	|current
---|---|---
2018.10.08T01:01:01.002	|121	|0.1
2018.10.08T01:01:01.003	|122	|
2018.10.08T01:01:01.004	|123	|0.2
2018.10.08T01:01:01.005	|124	|0.1
2018.10.08T01:01:01.006	|125	|
2018.10.08T01:01:01.007	|126	|0.2
2018.10.08T01:01:01.008	|127	|0.1
2018.10.08T01:01:01.009	|128	|
2018.10.08T01:01:01.010	|129	|0.2
2018.10.08T01:01:01.011	|130	|0.1

聚合计算结果：
```
select * from outputTable
```
time	|avgVoltage |avgCurrent
---|-----|---
2018.10.08T01:01:01.006	|123.5 |0.15
2018.10.08T01:01:01.009	|125  |0.15

由于voltage<=122或current=NULL的数据已经在进入时序引擎时被过滤了，所以第一个窗口[000,003)里没有数据，也就没有发生计算。

## 3. 多个引擎串联使用

outputTable参数除了可以是表之外还可以是其他流数据计算引擎：

```
share streamTable(1000:0, `time`sym`price`volume, [TIMESTAMP, SYMBOL, DOUBLE, INT]) as trades

share streamTable(1000:0, `time`sym`open`close`high`low`volume, [TIMESTAMP, SYMBOL, DOUBLE, DOUBLE, DOUBLE, DOUBLE, INT]) as kline

outputTable=table(1000:0, `sym`factor1, [SYMBOL, DOUBLE])

Rengine=createReactiveStateEngine(name="reactive", metrics=<[mavg(open, 3)]>, dummyTable=kline, outputTable=outputTable, keyColumn="sym")

Tengine=createTimeSeriesEngine(name="timeseries", windowSize=6000, step=6000, metrics=<[first(price), last(price), max(price), min(price), sum(volume)]>, dummyTable=trades, outputTable=Rengine, timeColumn=`time, useSystemTime=false, keyColumn=`sym)
//时间序列引擎的结果输入响应式状态引擎

subscribeTable(server="", tableName="trades", actionName="timeseries", offset=0, handler=append!{Tengine}, msgAsTable=true)   
```


## 4. 流数据引擎管理函数

DolphinDB database提供流数据引擎的管理函数，方便查询和管理系统中已经存在的流数据引擎。

- 获取已定义的流数据引擎清单，可使用函数[`getStreamEngineStat (deprecated name: getAggregatorStat)`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getStreamEngineStat.html)。
- 获取流数据引擎的句柄，可使用函数[`getStreamEngine (deprecated name: getAggregator)`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getStreamEngine.html)。
- 删除流数据引擎，可使用函数[`dropStreamEngine (deprecated name: dropAggregator)`](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/d/dropStreamEngine.html)。


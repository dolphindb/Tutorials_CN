# DolphinDB教程：流数据会话窗口引擎

DolphinDB提供了轻量且使用方便的流数据计算引擎。本教程讲述流数据会话窗口引擎。

## 1. 创建时序聚合引擎

流数据会话窗口引擎由函数`createSessionWindowEngine`创建。该函数返回一个抽象的表对象，为引擎入口。向这个抽象表写入数据，就意味着数据进入引擎进行计算。

`createSessionWindowEngine`函数必须与`subscribeTable`函数配合使用。通过`subscribeTable`函数，聚合引擎入口订阅一个流数据表。新数据进入流数据表后会被推送到聚合引擎入口，按照指定规则进行计算，并将计算结果输出。

### 1.1 语法

createSessionWindowEngine(name, sessionGap, metrics, dummyTable, outputTable, [timeColumn], [useSystemTime=false], [keyColumn], [updateTime], [useSessionStartTime=true],  [snapshotDir], [snapshotIntervalInMsgCount])

### 1.2 参数介绍

本节对各参数进行简单介绍。在下一小节中，对部分参数结合实例进行详细介绍。

- name

类型: 字符串

必选参数，表示引擎的名称，是聚合引擎在一个数据节点上的唯一标识。可包含字母，数字和下划线，但必须以字母开头。

- sessionGap

类型: 整型

必选参数，每个会话窗口之间的时间间隔，即两条数据之间超过多少时间为一个新的session。

- metrics

类型：元代码或者元代码的数组

必选参数。聚合引擎的核心参数，以元代码的格式表示计算公式。它可以是一个或多个系统内置或用户自定义的聚合函数，比如<[sum(volume),avg(price)]>；可对聚合结果使用表达式，比如<[avg(price1)-avg(price2)]>；也可对列与列的计算结果进行聚合计算，例如<[std(price1-price2)]>；也可以是一个函数返回多个指标，如自定义函数 func(price) , 则可以指定metrics为<[func(price) as ['res1','res2']> 。

- useSystemTime

类型：布尔值

可选参数，表示聚合引擎计算的触发方式。

当参数值为true时，聚合引擎会按照数据进入聚合引擎的时刻（毫秒精度的本地系统时间，与数据中的时间列无关），来判断会话是否结束。只要一个数据窗口中含有数据，数据窗口结束后就会自动进行计算。

当参数值为false（默认值）时，聚合引擎根据流数据中的timeColumn列来截取数据窗口。一个数据窗口结束后的第一条新数据才会触发该数据窗口的计算。请注意，触发计算的数据并不会参与该次计算。

- dummyTable

类型：表

必选参数。该表的唯一作用是为聚合引擎提供流数据中每一列的数据类型，可以含有数据，亦可为空表。该表的schema必须与订阅的流数据表相同。

- outputTable

类型：表

必选参数，为聚合结果的输出表。

在使用`createSessionWindowEngine`函数之前，需要将输出表预先设立为一个空表，并指定各列列名以及数据类型。集合引擎会将计算结果插入该表。

输出表的schema需要遵循以下规范：

(1) 输出表的第一列必须是时间类型。若useSystemTime=true，为TIMESTAMP类型；若useSystemTime=false，数据类型与timeColumn列一致。

(2) 如果分组列keyColumn参数不为空，那么输出表的第二列必须是分组列。

(3) 最后保存聚合计算的结果。

输出表的schema为"时间列，分组列(可选)，聚合结果列1，聚合结果列2..."这样的格式。

- timeColumn

类型：字符串

可选参数。当useSystemTime=false时，指定订阅的流数据表中时间列的名称。

- keyColumn

类型：字符串标量

可选参数，表示分组字段名。若设置，则分组进行聚合计算，例如以每支股票为一组进行聚合计算。

- updateTime

类型：整型

如果没有指定updateTime，一个数据窗口结束前，不会发生对该数据窗口数据的计算。若要求在当前会话窗口结束前对当前窗口已有数据进行计算，可指定updateTime。要设置updateTime，useSystemTime必须设为false。

如果指定了updateTime，当前窗口内可能会发生多次计算。这些计算触发的规则为：

(1) 将当前窗口分为n个大小为updateTime的小窗口，一个小窗口结束后，若有一条新数据到达，且在此之前当前窗口内有未参加计算的的数据，会触发一次计算。请注意，该次计算不包括这条新数据。

 (2) 一条数据到达聚合引擎之后经过2*updateTime（若2*updateTime不足2秒，则设置为2秒），若其仍未参与计算，会触发一次计算。该次计算包括当时当前窗口内的所有数据。

若分组计算，则每组内进行上述操作。

请注意，当前窗口内每次计算结果的时间戳均为当前会话窗口开始时间。

如果指定了updateTime，输出表必须是键值内存表（使用`keyedTable`函数创建）：如果没有指定keyColumn，输出表的主键是timeColumn；如果指定了keyColumn，输出表的主键是timeColumn和keyColumn。输出表若使用普通内存表或流数据表，每次计算均会增加一条记录，会产生大量带有相同时间戳的结果。输出表亦不可为键值流数据表，因为键值流数据表不可更新记录。

1.3.6小节使用例子详细介绍了指定updateTime参数后的计算过程。

- useSessionStartTime

类型：布尔类型

可选参数，表示输出表中的时间是否为会话窗口起始时间。默认值为true，表示输出表中的时间为数据窗口起始时间，即每个窗口中第一条数据的时间，如果useSessionStartTime = false，则输出的是session结束的时间，即每个窗口中最后一条数据的时间+sessionGap，如果指定updateTime，useSessionStartTime必须为true。

- snapshotDir

类型：字符串类型

可选参数，表示保存引擎快照的文件目录，可以用于系统出现异常之后，对引擎进行恢复。该目录必须存在，否则系统会提示异常。创建流数据引擎的时候，如果指定了snapshotDir，也会检查相应的快照是否存在。如果存在，会加载该快照，恢复引擎的状态。

- snapshotIntervalInMsgCount

类型：整型

可选参数，表示保存引擎快照的消息间隔。

### 1.3 参数详细介绍及用例

#### 1.3.1 sessionGap

下例说明如何划分会话窗口以及流数据聚合引擎如何进行计算。以下代码建立流数据表trades，包含time和volume两列。创建会话窗口引擎engine1，设定sessionGap = 10000，time列的精度为毫秒，模拟插入的数据流频率也设为每毫秒一条数据。
```
share streamTable(1000:0, `time`volume, [TIMESTAMP, INT]) as trades
outputTable = keyedTable(`time,10000:0, `time`sumVolume, [TIMESTAMP, INT])
engine = createSessionWindowEngine(name = "engine", sessionGap = 5, metrics = <sum(volume)>, dummyTable = trades, outputTable = outputTable, timeColumn = `time)
subscribeTable(, "trades", "append_engine", 0, append!{engine}, true)    
```

向流数据表trades中写入16条数据，并查看流数据表trades内容：
```
n = 5
timev = 2018.10.12T10:01:00.000 + (1..n)
volumev = (1..n)%1000
insert into trades values(timev, volumev)

n = 5
timev = 2018.10.12T10:01:00.010 + (1..n)
volumev = (1..n)%1000
insert into trades values(timev, volumev)

n = 3
timev = 2018.10.12T10:01:00.020 + (1..n)
volumev = (1..n)%1000
timev.append!(2018.10.12T10:01:00.027 + (1..n))
volumev.append!((1..n)%1000)
insert into trades values(timev, volumev)

select * from trades;
```
time	|volume
---|---
 2018.10.12T10:01:00.001 |1
 2018.10.12T10:01:00.002 |2
 2018.10.12T10:01:00.003 |3
2018.10.12T01:01:00.004	|4
2018.10.12T01:01:00.005	|5
2018.10.12T01:01:00.011	|1
2018.10.12T01:01:00.012	|2
2018.10.12T01:01:00.013	|3
2018.10.12T10:01:00.014	|4
2018.10.12T10:01:00.015	|5
2018.10.12T10:01:00.021	|1
2018.10.12T10:01:00.022	|2
2018.10.12T10:01:00.023	|3
2018.10.12T10:01:00.028	|1
2018.10.12T10:01:00.029	|2
2018.10.12T10:01:00.030	|3

再查看结果表outputTable:
```
select * from outputTable;
```
time|sumVolume
---|---
 2018.10.12T10:01:00.001 |15
 2018.10.12T10:01:00.011 |15
2018.10.12T10:01:00.021	|6

前5条数据都相隔1ms所以没有触发计算，第6条和第5条数据时间列相差6ms，大于sessionGap，所以此时触发计算得到一条结果。之后的4条也都相隔1ms所以不触发计算，第11条和第10条数据时间列相差6ms，此时触发第二次计算，之后同理在2018.10.12T10:01:00.028时，触发第三次计算。

若需要重复执行以上程序，应首先解除订阅，并将流数据表trades与聚合引擎streamAggr1二者删除：
```
unsubscribeTable(tableName="trades", actionName="append_engine")
undef(`trades, SHARED)
dropAggregator("engine")
```

#### 1.3.2 metrics

DolphinDB聚合引擎支持使用多种表达式进行实时计算。

- 一个或多个聚合函数：
```
engine = createSessionWindowEngine(name="engine", sessionGap=10000 metrics=<sum(ask)>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)
```

- 使用聚合结果进行计算：
```
engine = createSessionWindowEngine(name="engine", sessionGap=10000 metrics=<max(ask)-min(ask)>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)
```

- 对列与列的操作结果进行聚合计算：
```
engine = createSessionWindowEngine(name="engine", sessionGap=10000 metrics=<max(ask-bid)>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)
```

- 输出多个聚合结果
```
engine = createSessionWindowEngine(name="engine", sessionGap=10000 metrics=<[max((ask-bid)/(ask+bid)*2), min((ask-bid)/(ask+bid)*2)]>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)
```

- 使用多参数聚合函数
```
engine = createSessionWindowEngine(name="engine", sessionGap=10000 metrics=<corr(ask,bid)>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)

engine = createSessionWindowEngine(name="engine", sessionGap=10000 metrics=<percentile(ask-bid,99)/sum(ask)>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)
```

- 使用自定义函数
```
def spread(x,y){
	return abs(x-y)/(x+y)*2
}
engine = createSessionWindowEngine(name="engine", sessionGap=10000 metrics=<spread(ask,bid)>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)
```

- 使用多个返回结果的函数

```
def sums(x){
	return [sum(x),sum2(x)]
}
engine = createSessionWindowEngine(name="engine", sessionGap=10000 metrics=<sums(ask) as `sumAsk`sum2Ask>, dummyTable=quotes, outputTable=outputTable, timeColumn=`time)
```

注意：不支持聚合函数嵌套调用，例如sum(spread(ask,bid))。


#### 1.3.3 dummyTable

系统利用dummyTable的schema来决定订阅的流数据中每一列的数据类型。dummyTable有无数据对结果没有任何影响。
```
share streamTable(1000:0, `time`volume, [TIMESTAMP, INT]) as trades
modelTable = table(1000:0, `time`volume, [TIMESTAMP, INT])
outputTable = keyedTable(`time,10000:0, `time`sumVolume, [TIMESTAMP, INT])
engine = createSessionWindowEngine(name = "engine", sessionGap = 5, metrics = <sum(volume)>, dummyTable = modelTable, outputTable = outputTable, timeColumn = `time)
subscribeTable(, "trades", "append_engine", 0, append!{engine}, true)    
```

#### 1.3.4 outputTable

聚合结果可以输出到内存表或流数据表。输出到内存表的数据可以更新或删除，而输出到流数据表的数据无法更新或删除，但是可以通过流数据表将聚合结果作为另一个聚合引擎的数据源再次发布。

下例中，聚合引擎engine1订阅流数据表trades，进行均值计算，并将结果输出到流数据表outputTable1。聚合引擎engine2订阅outputTable1表，并对均值计算结果求峰值。
```

share streamTable(1000:0,`time`sym`prices, [TIMESTAMP,SYMBOL,DOUBLE]) as trades

//将第一个聚合引擎的输出表定义为流数据表，可以再次订阅
share streamTable(10000:0,`time`avgPrices, [TIMESTAMP,DOUBLE]) as outputTable1 

engine1 = createSessionWindowEngine(name="engine1", sessionGap=10000, metrics=<avg(prices)>, dummyTable=trades, outputTable=outputTable1, timeColumn=`time)
subscribeTable(tableName="trades", actionName="avg", offset=0, handler=append!{engine1}, msgAsTable=true)

//订阅聚合结果，再次进行聚合计算
outputTable2 =table(10000:0, `time`maxAvgPrices, [TIMESTAMP,DOUBLE])
engine2 = createSessionWindowEngine(name="engine2", sessionGap=10000, metrics=<max(avgPrices)>, dummyTable=outputTable1, outputTable=outputTable2, timeColumn=`time)
subscribeTable(tableName="outputTable1", actionName="max", offset=0, handler=append!{engine2}, msgAsTable=true);
//向trades表中插入300条数据
def writeData(t, n){
        timev = 2018.10.08T01:01:01.000 + timestamp(1..n)
        timev.append!(2018.10.08T01:01:01.000 + timestamp((n+1+11000)..(2*n+11000)))
        timev.append!(2018.10.08T01:01:01.000 + timestamp((2*n+1+22000)..(3*n+22000)))
        symv = take("A" + string(1..5), 3*n)
        pricesv = 1..(3*n) * 0.1
        insert into t values(timev, symv, pricesv)
}
writeData(trades, 100);
```
聚合计算结果:
```
select * from outputTable2;
```
time	|maxAvgPrices	
---|---
2018.10.08T01:01:01.001	|5.05	

若要对上述脚本进行重复使用，需先执行以下脚本以清除共享表、订阅以及聚合引擎：
```
unsubscribeTable(tableName="trades", actionName="avg")
undef(`trades, SHARED)
unsubscribeTable(tableName="outputTable1", actionName="max")
undef(`outputTable1, SHARED)
dropAggregator("engine1")
dropAggregator("engine2")
```

#### 1.3.5 keyColumn

下例中，设定keyColumn参数为sym。
```
share streamTable(1000:0,`time`sym`prices, [TIMESTAMP,SYMBOL,DOUBLE]) as trades
outputTable1 = table(10000:0,`time`sym`avgPrices, [TIMESTAMP,SYMBOL,DOUBLE]) 

engine1 = createSessionWindowEngine(name="engine1", sessionGap=10000, metrics=<avg(prices)>, dummyTable=trades, outputTable=outputTable1, timeColumn=`time, keyColumn=`sym)

subscribeTable(tableName="trades", actionName="avg", offset=0, handler=append!{engine1}, msgAsTable=true)

```
分组计算结果：
```
select * from outputTable; 
```
time	|sym|	sumVolume
---|---|---
 2018.10.08T01:01:01.001 |A1| 4.85 
2018.10.08T01:01:12.101	|A1| 14.85 
2018.10.08T01:01:01.002	|A2| 4.95 
2018.10.08T01:01:12.102	|A2| 14.95 
2018.10.08T01:01:01.003	|A3| 5.05 
2018.10.08T01:01:12.103	|A3| 15.05 
2018.10.08T01:01:01.004	|A4| 5.15 
2018.10.08T01:01:12.104	|A4| 15.15 
2018.10.08T01:01:01.005	|A5| 5.25 
2018.10.08T01:01:12.105	|A5| 15.25 

如果进行分组聚合计算，流数据源中的每个分组中的'timeColumn'必须是递增的，但是整个数据源的'timeColumn'可以不是递增的；如果没有进行分组聚合，那么整个数据源的'timeColumn'必须是递增的，否则聚合引擎的输出结果会与预期不符。

#### 1.3.6 updateTime

如果一个会话窗口持续的时间很长，那么系统很长一段时间里都收不到反馈，此时可以指定updateTime，周期性得触发计算，不断更新输出表中的结果。通过以下两个例子，可以理解updateTime的作用。

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
insert into trades values(2018.10.08T01:04:05.152,`B,23)
insert into trades values(2018.10.08T01:04:05.365,`A,36)
```

- 不指定updateTime：
```
output1 = table(10000:0, `time`sym`sumVolume, [TIMESTAMP, SYMBOL, INT])

engine1 = createSessionWindowEngine(name="engine1", sessionGap=10000, metrics=<sum(volume)>, dummyTable=trades, outputTable=output1, timeColumn=`time, keyColumn=`sym)
subscribeTable(tableName="trades", actionName="engine1_append", offset=0, handler=append!{engine1}, msgAsTable=true)

sleep(10)

select * from output1;
```

time                    |sym| sumVolume
----------------------- |---| ------
 2018.10.08T01:01:01.785 |A   |10    
2018.10.08T01:01:12.457 |A   |28    
 2018.10.08T01:02:10.789 |A   |15   
2018.10.08T01:02:30.021 |A   |10   
2018.10.08T01:01:02.125 |B |40 
2018.10.08T01:02:12.005 |B |9 

- 将updateTime设为1000：
```
output2 = keyedTable(`time`sym,10000:0, `time`sym`sumVolume, [TIMESTAMP, SYMBOL, INT])
engine2 = createSessionWindowEngine(name="engine2", sessionGap=10000, metrics=<sum(volume)>, dummyTable=trades, outputTable=output2, timeColumn=`time, keyColumn=`sym,updateTime=1000, useSessionStartTime=true)
subscribeTable(tableName="trades", actionName="engine2_append", offset=0, handler=append!{engine2}, msgAsTable=true)

sleep(2010)

select * from output2;
```

| time                    | sym  | sumVolume |
| ----------------------- | ---- | --------- |
| 2018.10.08T01:01:01.785 | A    | 10        |
| 2018.10.08T01:01:12.457 | A    | 28        |
| 2018.10.08T01:02:10.789 | A    | 15        |
| 2018.10.08T01:02:30.021 | A    | 10        |
| 2018.10.08T01:04:02.236 | A    | 65        |
| 2018.10.08T01:01:02.125 | B    | 40        |
| 2018.10.08T01:02:12.005 | B    | 9         |
| 2018.10.08T01:04:04.412 | B    | 55        |

下面我们介绍以上两个例子在2018.10.08T01:04:02.236和2018.10.08T01:04:04.412的区别。为简便起见，我们省略日期部分，只列出（小时:分钟:秒.毫秒）部分。假设time列时间亦为数据进入聚合引擎的时刻。

(1) 在01:04:05.365时，A分组内还有一条数据未参与过计算，且时间列之差大于updateTime，触发一次A组计算，输出表增加一条记录(2018.10.08T01:04:02.236, "A", 29)。2000毫秒之后01:04:05.365的这条数据还没参与计算，此时再次触发计算，更新2018.10.08T01:04:02.236的记录为 (2018.10.08T01:04:02.236, "A", 65)

(2) 在01:04:05.152时的B组记录01:04:04.412为所在会话窗口的第一条记录，且时间差小于updateTime此时不触发计算， 2000毫秒后，窗口中有两条数据未计算，触发一次计算，输出表增加一条记录(01:05:00.000,"B",55)。

#### 1.3.7 snapshot

通过以下这个例子，可以理解snapshotDir和snapshotIntervalInMsgCount的作用。如果启用snapshot，引擎订阅流表时，handler需是appendMsg函数，需指定handlerNeedMsgId=true，用来记录快照的消息位置。

假设需要对自动售卖机的售卖情况进行收集分析，设定超过两分钟无交易则认定本次交易结束。

```
snapshotDir = "/home/server1/snapshotDir"

share streamTable(10000:0,`time`deviceID`goodsID`prices`cost`volume, [TIMESTAMP,SYMBOL,SYMBOL,DOUBLE,DOUBLE,INT]) as trades
output1 =table(10000:0, `time`deviceID`profit, [TIMESTAMP,SYMBOL,DOUBLE]);

engine1 = createSessionWindowEngine(name="engine1", sessionGap=120000, metrics=<sum((prices-cost)*volume)>, dummyTable=trades, outputTable=output1, timeColumn=`time, keyColumn=`deviceID, snapshotDir=snapshotDir, snapshotIntervalInMsgCount=10)

subscribeTable(server="", tableName="trades", actionName="engine1",offset= 0, handler=appendMsg{engine1}, msgAsTable=true, handlerNeedMsgId=true)
//不开启snapshot
output2 =table(10000:0, `time`deviceID`profit, [TIMESTAMP,SYMBOL,DOUBLE]);
engine2 = createSessionWindowEngine(name="engine2", sessionGap=120000, metrics=<sum((prices-cost)*volume)>, dummyTable=trades, outputTable=output2, timeColumn=`time, keyColumn=`deviceID)

subscribeTable(server="", tableName="trades", actionName="engine2",offset= 0, handler=append!{engine2}, msgAsTable=true)
//写入数据
insert into trades values(2018.10.08T01:01:01.785,`A1,`P1001,10.0,6.0,1)
insert into trades values(2018.10.08T01:01:02.125,`A2,`P1002,8.0,5.0,2)
insert into trades values(2018.10.08T01:01:10.263,`A3,`P1003,7.0,3.5,2)
insert into trades values(2018.10.08T01:01:12.457,`A4,`P1002,8.0,5.0,3)
insert into trades values(2018.10.08T01:02:10.789,`A5,`P1003,7.0,3.5,1)
insert into trades values(2018.10.08T01:02:12.005,`A2,`P1001,10.0,6.0,1)
insert into trades values(2018.10.08T01:02:30.021,`A3,`P1006,6.5,3.5,2)
insert into trades values(2018.10.08T01:04:02.236,`A1,`P1005,12.0,6.5,3)
insert into trades values(2018.10.08T01:04:04.412,`A1,`P1005,12.0,6.5,1)
insert into trades values(2018.10.08T01:04:05.152,`A3,`P1001,10.0,6.0,3);
insert into trades values(2018.10.08T01:06:05.365,`A2,`P1002,8.0,5.0,2)

select * from output1
```

| time                    | deviceID | profit |
| ----------------------- | -------- | ------ |
| 2018.10.08T01:01:01.785 | A1       | 4      |
| 2018.10.08T01:01:02.125 | A2       | 10     |

```
getSnapshotMsgId(engine1)
>9
```

取消订阅并删除引擎来模拟系统异常

```
unsubscribeTable(, "trades", "engine1")
dropAggregator("engine1")
engine1=NULL

unsubscribeTable(, "trades", "engine2")
dropAggregator("engine2")
engine2=NULL
```

此时发布端仍在写入数据

```
insert into trades values(2018.10.08T01:06:06.785,`A1,`P1001,10.0,6.0,1)
insert into trades values(2018.10.08T01:07:07.125,`A3,`P1002,8.0,5.0,2)
insert into trades values(2018.10.08T01:07:07.263,`A2,`P1003,7.0,3.5,2)
insert into trades values(2018.10.08T01:09:12.457,`A5,`P1002,8.0,5.0,3)
insert into trades values(2018.10.08T01:12:10.789,`A5,`P1003,7.0,3.5,1)
```

再次创建engine1, 加载snapshot，从上次处理最后一条消息开始重新订阅

```
engine1 = createSessionWindowEngine(name="engine1", sessionGap=120000, metrics=<sum((prices-cost)*volume)>, dummyTable=trades, outputTable=output1, timeColumn=`time, keyColumn=`deviceID, snapshotDir=snapshotDir, snapshotIntervalInMsgCount=10)

ofst=getSnapshotMsgId(Agg1)
print(ofst)
>9

subscribeTable(server="", tableName="trades", actionName="engine1",offset=ofst+1, handler=appendMsg{engine1}, msgAsTable=true, handlerNeedMsgId=true)

select * from output1
```

| time                    | deviceID | profit |
| ----------------------- | -------- | ------ |
| 2018.10.08T01:01:01.785 | A1       | 4      |
| 2018.10.08T01:01:02.125 | A2       | 10     |
| 2018.10.08T01:04:02.236 | A1       | 22     |
| 2018.10.08T01:01:10.263 | A3       | 25     |
| 2018.10.08T01:02:10.789 | A5       | 3.5    |
| 2018.10.08T01:09:12.457 | A5       | 9      |

如果不开启snapshot，从上次中断的地方开始订阅，得到的结果如下：

```
engine2 = createSessionWindowEngine(name="engine2", sessionGap=120000, metrics=<sum((prices-cost)*volume)>, dummyTable=trades, outputTable=output2, timeColumn=`time, keyColumn=`deviceID)

subscribeTable(server="", tableName="trades", actionName="engine2",offset= 11, handler=append!{engine2}, msgAsTable=true)

select * from output2
```

| time                    | deviceID | profit |
| ----------------------- | -------- | ------ |
| 2018.10.08T01:01:01.785 | A1       | 4      |
| 2018.10.08T01:01:02.125 | A2       | 10     |
| 2018.10.08T01:09:12.457 | A5       | 9      |

可以看到不开启snapshot丢失了一部分数据。
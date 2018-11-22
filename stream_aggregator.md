## DolphinDB流数据聚合引擎

&emsp;&emsp;流数据是指随时间延续而增长的动态数据集合，金融机构的交易数据、物联网的传感器数据和互联网的运营数据都属于流数据的范畴。流数据的特性决定了它的数据集一直是动态变化的，传统的面向静态数据表的计算引擎无法胜任流数据领域的分析和计算任务，所以流数据场景需要一套针对性的计算引擎。

DolphinDB提供了灵活的面向流数据的聚合引擎，通过`createStreamAggregator`函数创建流数据聚合引擎，能够持续地对流数据做聚合计算，并且将计算结果持续输出到指定的数据表中。

### 1.聚合引擎应用框架

&emsp;&emsp;流聚合引擎本身是一个独立的计算引擎，只要向聚合引擎写入数据就可以触发计算，并将计算结果输出到目标表。而在流数据场景下，聚合引擎与流数据订阅功能(`subscribeTable`)配合，可以方便的将流数据持续的提供给聚合引擎。示例代码如下，通过`subscribeTable` 函数订阅流数据，每次有新数据流进入就会按指定规则触发`append!{tradesAggregator}`，将流数据持续输入聚合引擎。

```
tradesAggregator = createStreamAggregator(5, 5, <[sum(qty)]>, trades, outputTable, `time)
subscribeTable(, "trades", "tradesAggregator", 0, append!{tradesAggregator}, true)    
```
这里对聚合引擎涉及到的一些概念做简要介绍：

- 流数据表：DolphinDB为流式数据提供一种特定的表对象：streamTable，它提供流式数据的发布功能，通过`subscribeTable`函数，其他的节点或App可以订阅和消费流数据。

- 聚合引擎数据源：这是为聚合引擎提供"原料"的通道，`createStreamAggregator`返回一个抽象表，向这个抽象表写入数据，就意味着数据进入聚合引擎进行计算。

- 聚合表达式 ：以元数据的格式提供一组处理流数据的聚合函数，类似如下格式`<[sum(qty)]>`,`<[sum(qty),max(qty),avg(price)]>`。聚合引擎支持使用系统内所有的聚合函数，也支持使用表达式来满足更复杂的场景，比如 `<[avg(price1)-avg(price2)]>`,`<[std(price1-price2)]>`这样的组合表达式。

- 数据窗口(`windowSize`) ：指定每次计算时截取的流数据窗口长度。

- 计算周期(`step`): 指定进行计算的间隔。

### 2.数据窗口  

&emsp;&emsp;每次对流数据进行聚合计算，必须截取一段数据。截取的数据我们也称为数据窗口，其长度由参数`windowSize`设定。

&emsp;&emsp;针对持续变化的流数据的计算是间隔一定时间重复进行的，参数`step`设定计算间隔。

&emsp;&emsp;数据窗口长度和计算间隔的单位由参数`useSystemTime`决定。流数据聚合计算场景有两种时间概念，一是数据的生成时间，通常以时间戳的格式记录于数据中，它可能采用天，分钟，秒，毫秒，纳秒等不同的精度；二是数据进入聚合引擎的时间，我们也称为系统时间，这个时间是由聚合引擎给数据打上的时间戳，取自聚合引擎所在服务器的系统时间，精度为毫秒。系统通过参数`useSystemTime`来确定数据窗口长度和计算间隔是以哪一个时间的精度为单位，当`useSystemTime=true`时以系统时间精度为单位，否则以数据生成时间精度为单位。

&emsp;&emsp;若根据第一条数据进入系统的时间来构造数据窗口的边界，边界时间一般不会是很规整的时间。若数据有很多组，且每组都根据各自第一条数据进入系统的时间来构造数据窗口的边界，则无法将各组在相同数据窗口中进行对比。综合上述因素，系统按照`step`值对第一个数据窗口的边界值进行规整处理，具体规整公式与时间精度和`step`有关，规则如下：

根据`step`的大小， 系统会确定一个整型的规整尺度alignmentSize。

当数据时间精度为秒时，如DATETIME、SECOND类型，alignmentSize取值规则如下表：

step | alignmentSize
---|---
0~2 |2
3~5 |5
6~10|10
11~15|15
16~20|20
21~30|30
31~60|60

当数据时间精度为毫秒时，如TIMESTAMP、TIME类型，alignmentSize取值规则如下表：

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
501~1000|1000

假设第一条数据时间的最小精度值为`firstDataTime`，那么第一个数据窗口的左边界最小精度经过规整后为 `firstDataTime/alignmentSize*alignmentSize`，其中`/`代表相除后取整。举例来说，若第一条数据时间为 2018.10.08T01:01:01.365，则`firstDataTime`=365。若`step`=100，根据上表，alignmentSize=100，可得出规整后的第一个数据窗口左边界最小精度为365\100*100=300，因此规整后的第一个数据窗口范围为 2018.10.08T01:01:01.300 至 2018.10.08T01:01:01.400。

下面我们通过一个例子来详细说明系统是如何进行流数据计算的。输入流数据表包含time和qty两列，time精度为毫秒，根据设定的窗口对流数据进行持续`sum(qty)`计算。本示例的流数据表中使用的时间精度为毫秒，为了方便观察，模拟输入的数据流频率也设为每毫秒一条数据的频率。以下代码建立流数据表trades，设定聚合计算参数，并定义函数`writeData`向流数据表trades中写入模拟数据。 
```
share streamTable(1000:0, `time`qty, [TIMESTAMP, INT]) as trades
outputTable = table(10000:0, `time`sumQty, [TIMESTAMP, INT])
tradesAggregator = createStreamAggregator(5, 5, <[sum(qty)]>, trades, outputTable, `time)
subscribeTable(, "trades", "tradesAggregator", 0, append!{tradesAggregator}, true)    

def writeData(n){
    timev = 2018.10.08T01:01:01.001 + timestamp(1..n)
    qtyv = take(1, n)
    insert into trades values(timev, qtyv)
}
```

第一次操作：向流数据表trades中写入5条数据
```
writeData(5)
```
使用 `select * from trades` 查看流数据表，表里已有5条数据：

time	                |qty
---|---
2018.10.08T01:01:01.002	| 1
2018.10.08T01:01:01.003	| 1
2018.10.08T01:01:01.004	| 1
2018.10.08T01:01:01.005	| 1
2018.10.08T01:01:01.006	| 1

再用`select * from outputTable`查看输出表，可见已经发生了一次计算：

time|	sumQty
---|---
2018.10.08T01:01:01.000 |3

发生计算的时间是2018.10.08T01:01:01.000。可以看出，系统对首个数据的时间2018.10.08T01:01:01.002做了规整操作。


第二次操作：清空数据表，设置 `windowSize=6`，`step=3`，模拟写入10条数据：

```
share streamTable(1000:0, `time`qty, [TIMESTAMP, INT]) as trades
outputTable = table(10000:0, `time`sumQty, [TIMESTAMP, INT])
tradesAggregator = createStreamAggregator(6, 3, <[sum(qty)]>, trades, outputTable, `time)
subscribeTable(, "trades", "tradesAggregator", 0, append!{tradesAggregator}, true)    

def writeData(n){
    timev = 2018.10.08T01:01:01.001 + timestamp(1..n)
    qtyv = take(1, n)
    insert into trades values(timev, qtyv)
}
writeData(10)
```

查看流数据表trades内容：

time	|qty
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

time|sumQty
---|---
2018.10.08T01:01:00.997	|1
2018.10.08T01:01:01.000	|4
2018.10.08T01:01:01.003	|6

可以看到已经成功触发了三次计算。

从这个结果也可以发现聚合引擎窗口计算的规则：窗口起始时间是以第一条数据时间规整后为准，窗口是以`windowSize`为大小，`step`为步长移动的。

下面根据三次计算的过程来解释聚合引擎是如何进行窗口数据的确定的。为方便阅读，对时间的描述中省略相同的2018.10.08T01:01:01部分，只列出毫秒部分。窗口的起始是第一个数据的时间`002`为基础进行对齐，时间对齐后为`000`，所以第一次触发计算的时间是`000`，根据`windowSize=6`，所以理论上窗口边界是从上一秒的`997`到`002`，最终第一次计算窗口中只包含了`002`一条记录，计算`sum(qty)`的结果是1；而第二次计算发生在`000`，根据`windowSize=6`,那么实际窗口大小是6毫秒(从`000`到`005`)，实际窗口中包含了从`002`到`005`四个数据，计算结果为4；以此类推，第三次的计算窗口是从`003`到`008`,实际包含了6个数据，计算结果为6。


### 3.聚合表达式

在实际的应用中，通常要对流数据进行比较复杂的聚合计算，这对聚合引擎的表达式灵活性提出了较高的要求。DolphinDB聚合引擎支持使用复杂的表达式进行实时计算。

- 纵向聚合计算(按时间序列聚合)

```
tradesAggregator = createStreamAggregator(6, 3, <sum(ofr)>, trades, outputTable, `time)
```

- 横向聚合计算(按维度聚合)
```
tradesAggregator = createStreamAggregator(6, 3, <max(ofr)-min(ofr)>, trades, outputTable, `time)

tradesAggregator = createStreamAggregator(6, 3, <max(ofr-bid)>, trades, outputTable, `time)
```

- 输出多个聚合结果
```
tradesAggregator = createStreamAggregator(6, 3, <[max((ofr-bid)/(ofr+bid)*2), min((ofr-bid)/(ofr+bid)*2)]>, trades, outputTable, `time)
```

- 多参数聚合函数的调用

有些聚合函数会使用多个参数，例如 `corr`，`percentile`等。
```
tradesAggregator = createStreamAggregator(6, 3, <corr(ofr,bid)>, trades, outputTable, `time)

tradesAggregator = createStreamAggregator(6, 3, <percentile(ofr-bid,99)/sum(ofr)>, trades, outputTable, `time)
```

- 调用自定义函数

```
def spread(x,y){
	return abs(x-y)/(x+y)*2
}
tradesAggregator = createStreamAggregator(6, 3, <spread(ofr, bid)>, trades, outputTable, `time)
```
*注意：不支持聚合函数嵌套调用，比如若要在流数据引擎中计算`sum(spread(ofr,bid))`，系统会给出异常提示：Nested aggregated function is not allowed*

### 4. 流数据源

DolphinDB的聚合引擎使用流数据表(streamTable)来作为输入数据源，流数据表提供流式数据的发布功能，通过`subscribeTable`函数可以订阅流数据并触发数据处理流程，而聚合引擎就是处理数据的方式之一。

streamTable作为聚合引擎的数据源，它并不仅仅是简单的将原始数据灌入聚合引擎，通过`subscribeTable`函数，可以在数据进入聚合引擎之前对数据做初步清洗，下面的例子展示如何对流数据做初步过滤。

传感器采集电压和电流数据并实时上传作为流数据源，但是其中电压`voltage<=0.02`或电流`electric==NULL`的数据需要在进入聚合引擎之前过滤掉。

```
share streamTable(1000:0, `time`voltage`electric, [TIMESTAMP, DOUBLE, INT]) as trades
outputTable = table(10000:0, `time`avgElectric, [TIMESTAMP, DOUBLE])
//模拟产生传感器数据
def writeData(blockNumber){
        timev = 2018.10.08T01:01:01.001 + timestamp(1..blockNumber)
        vt = 1..blockNumber * 0.01
        bidv = take([1,NULL,2], blockNumber)
        insert into trades values(timev, vt, bidv);
}
//自定义数据处理过程，msg即实时流入的数据
def dataPreHandle(aggrTable, msg){
    //过滤 voltage<=0.02 或 electric==NULL的无效数据
	t = select * from msg where voltage >0.02,not electric == NULL
	if(size(t)>0){
		insert into aggrTable values(t.time,t.voltage,t.electric)		
	}
}
tradesAggregator = createStreamAggregator(6, 3, <[avg(electric)]>, trades, outputTable, `time , false, , 2000)
//订阅数据源时使用自定义的数据处理函数
subscribeTable(, "trades", "tradesAggregator", 0, dataPreHandle{tradesAggregator}, true)

writeData(10)
```
从流数据源中可以看到有两个voltage<=0.02和三个electric==NULL的数据：
```
select * from trades
```

time	|voltage	|electric
---|---|---
2018.10.08T01:01:01.002	|0.01	|1
2018.10.08T01:01:01.003	|0.02	|
2018.10.08T01:01:01.004	|0.03	|2
2018.10.08T01:01:01.005	|0.04	|1
2018.10.08T01:01:01.006	|0.05	|
2018.10.08T01:01:01.007	|0.06	|2
2018.10.08T01:01:01.008	|0.07	|1
2018.10.08T01:01:01.009	|0.08	|
2018.10.08T01:01:01.010	|0.09	|2
2018.10.08T01:01:01.011	|0.1	|1

观察聚合计算结果
```
select * from outputTable
```
time	|avgElectric
---|---
2018.10.08T01:01:01.000	|1.5
2018.10.08T01:01:01.003	|1.5

从结果可以看到，`voltage<=0.02 or electric==NULL`的数据已经被过滤了，所以第一个计算窗口没有数据，所以也没有聚合结果。


### 5. 聚合引擎输出

聚合结果可以输出到新建或已存在的内存表，也可以输出到流数据表。内存表对数据操作上较为灵活，可以进行更新或删除操作；输出到流数据表的数据无法再做变动，但是可以通过流数据表将聚合结果再次发布。下面的例子展示如何将聚合结果表作为另一个聚合引擎的数据源。

本例从一个初始的流数据表trades里，通过聚合引擎tradesAggregator进行移动均值计算，并将结果输出到流数据表aggrOutput，再通过订阅aggrOutput表并关联聚合引擎SecondAggregator对计算结果求移动峰值。
```
share streamTable(1000:0, `time`voltage`electric, [TIMESTAMP, DOUBLE, INT]) as trades
//将输出表定义为流数据表，可以再次订阅
outputTable = streamTable(10000:0, `time`avgElectric, [TIMESTAMP, DOUBLE])
share outputTable as aggrOutput 

def writeData(blockNumber){
        timev = 2018.10.08T01:01:01.001 + timestamp(1..blockNumber)
        vt = 1..blockNumber * 0.01
        bidv = take([1,2], blockNumber)
        insert into trades values(timev, vt, bidv);
}

tradesAggregator = createStreamAggregator(6, 3, <[avg(electric)]>, trades, outputTable, `time , false, , 2000)
subscribeTable(, "trades", "tradesAggregator", 0, append!{tradesAggregator}, true)

//对聚合结果进行订阅做二次聚合计算
outputTable2 =table(10000:0, `time`maxAggrElec, [TIMESTAMP, DOUBLE])
SecondAggregator = createStreamAggregator(6, 3, <[max(avgElectric)]>, aggrOutput, outputTable2, `time , false, , 2000)
subscribeTable(, "aggrOutput", "SecondAggregator", 0, append!{SecondAggregator}, true)

writeData(10)
```
观察聚合计算结果
```
select * from outputTable2
```
time	|maxAggrElec
---|---
2018.10.08T01:01:00.992	|1
2018.10.08T01:01:00.995	|1.5

### 6. `createStreamAggregator`函数介绍及语法

`createStreamAggregator`函数关联了流数据聚合应用的3个主要信息：

- 输入数据源

    输入数据源指定一个流数据表(streamTable)，应用时通过订阅的方式把数据源和聚合引擎联系起来。
    
- 聚合表达式

    定义聚合计算的逻辑。聚合引擎根据聚合表达式对流数据做计算，并将结果输出。
    
- 输出目的地

    聚合结果可以输出到新建或已存在的内存表，也可以输出到流数据表。内存表对数据操作上较为灵活，可以做更新删除操作；而输出到流数据表的数据无法再做变动，但是可通过流数据表将聚合结果再次发布。

在此之外，函数也提供多个可选参数来满足不同的使用场景。

#### 6.1 语法

createStreamAggregator(windowSize, step, aggregators, dummyTable, outputTable, timeColumn, [useSystemTime, keyColumn, garbageSize])

#### 6.2 返回对象

返回一个抽象的表对象，作为聚合引擎的入口，向这个表写入数据，意味着数据进入聚合引擎进行计算。

#### 6.3 参数

- `useSystemTime`

类型：布尔值

说明：聚合引擎的驱动方式，为可选参数，缺省值为false。当参数值为true时，表示时间驱动方式：每当到达一个预定的时间点，聚合引擎就会激活并以设定的窗口截取流数据进行计算。在此模式下，系统内部会给每一个进入的数据添加一个毫秒精度的系统时间戳作为数据窗口截取的依据。而当参数值为false时，为数据驱动方式：只有当数据进入系统时，聚合引擎才会被激活，此时窗口的截取依据是`timeColumn`列内容，时间的精度也取决于`timeColumn`列的时间精度。

- `windowSize`

类型：整型

说明：聚合窗口大小，必选参数。对流数据进行聚合计算，每次要截取一段静态数据集用于计算，这个截取出来的静态数据集我们也称为数据窗口。`windowSize`参数指定数据窗口的大小。

`windowSize`的单位取决于`useSystemTime`参数。当`useSystemTime=true`时，`windowSize`的单位是毫秒；当`useSystemTime=false`时，`windowSize`的单位与数据本身的time列的精度相同，比如`timeColumn`列是timestamp类型，那么`windowSize`的单位是毫秒；如果`timeColumn`列是datetime类型，那么`windowSize`的单位是秒。数据窗口的边界原则是下包含上不包含。

- `step`

类型：整型

说明：聚合计算频率，必选参数。`step`参数指定触发计算的时间间隔。

当`useSystemTime=true`时，`step` 值是系统时间间隔，单位是毫秒，比如`step=3`，代表每隔3毫秒触发一次计算。

当`useSystemTime=false`时，`step` 值是数据本身包含的时间间隔，`step`应该和数据本身时间列具有相同的精度。比如数据时间是timestamp格式，精度为毫秒，那么`step`也以毫秒为单位；如果数据时间是datetime格式，精度为秒，那么`step`也应秒为单位。

基于简化场景复杂度的考量，我们要求`windowSize`必须能被`step`整除。

为了便于对计算结果的观察和对比，系统会对窗口的起始时间进行规整，第一条进入系统的数据时间往往不是很规整的时间，例如2018.10.10T03:26:39.178，如果`step`设置为100，那么系统会将其窗口起始时间规整为2018.10.10T03:26:39.100，对齐移动范围最大不超过1秒。具体对齐公式与时间精度与`step`有关，具体请参照2.数据窗口。当聚合引擎使用分组计算时，所有分组使用统一的起始时间，所有分组的起始时间以最早进入系统的数据按规整公式计算得出。

- `aggregators`

类型：元数据

说明：必选参数。这是聚合引擎的核心参数，它以元数据的格式提供一组使用流数据的聚合函数，类似如下格式`<[sum(qty)]>`,`<[sum(qty),max(qty),avg(price)]>`。支持系统内所有的聚合函数，也支持对聚合结果使用表达式来满足更复杂的场景，比如 `<[avg(price1)-avg(price2)]>`,`<[std(price1-price2)]>`这样的写法。

由于原始的聚合函数是对每个窗口内的全部数据进行计算，为了提升流数据聚合的性能，DolphinDB进行了针对性的优化，函数在计算时充分利用上一个窗口的计算结果，最大程度降低了重复计算，可显著提高运行速度。下表列出了当前已优化的聚合函数清单：

函数名 | 函数说明 
---|---
corr|相关性
covar|协方差
first|第一个元素
last|最后一个元素
max|最大值
med|中位数
min|最小值
percentile|根据给定的百分比，为向量返回一个标量
std|标准差
sum|求和
sum2|平方和
var|方差
wavg|加权平均
wsum|加权和

- `dummyTable`

类型：表

说明：必选参数。提供一个样本表对象，该对象不需要有数据，但是表结构必须与输入流数据表相同。

- `outputTable`

类型: 表

说明：必选参数。聚合结果的输出表。输出表的结构需要遵循以下规范：

输出表的第一列必须是时间类型，用于存放计算发生的时间戳，这个列的数据类型要和`dummyTable`的时间列类型一致。

如果`keyColumn`参数不为空，那么输出表的第二列必须是分组列。

从第三列开始，按照顺序保存聚合计算的结果。最终的表结构是`时间列，分组列(可选)，聚合结果列1，聚合结果列2...` 这样的格式。

- `timeColumn`

类型：字符串

说明：必选参数。指定流数据表时间列的名称。根据`timeColumn`参数，聚合引擎从流数据表中取得对应列的时间数据。

- `keyColumn`

类型：字符串

说明：聚合分组字段名，可选参数。指定分组计算的组别，以对流数据分组进行聚合计算。比如以股市报价数据中的每支股票为一组进行聚合计算。

- `garbageSize`

类型：整型

说明：此参数可选，设定一个阈值，当内存中缓存的历史数据的行数超出阈值时清理无用缓存。

当流数据聚合引擎在运行时，每次计算都会需要载入新的窗口数据到内存中进行计算，随着计算过程的持续，内存中缓存的数据会越来越多，这时候需要有一个机制来清理不再需要的历史数据。当内存中保留的历史数据行数超过`garbageSize`设定值时会引发清理内存。

当需要分组计算时，每个分组的历史数据记录数是分别统计的，所以内存清理的动作也是各分组独立进行的。当每个组的历史数据记录数超出`garbageSize`时都会引发清理内存。

#### 6.4. 示例

#####  6.4.1. dummyTable示例

本例展示`dummyTable`的作用。增加一个结构完全与trades相同的modelTable对象，将modelTable作为`dummyTable`参数，而实际的数据仍然写入trades。
```
share streamTable(1000:0, `time`qty, [TIMESTAMP, INT]) as trades
modelTable = table(1000:0, `time`qty, [TIMESTAMP, INT])
outputTable = table(10000:0, `time`sumQty, [TIMESTAMP, INT])
tradesAggregator = createStreamAggregator(5, 5, <[sum(qty)]>, modelTable, outputTable, `time)
subscribeTable(, "trades", "tradesAggregator", 0, append!{tradesAggregator}, true)    

def writeData(n){
    timev = 2018.10.08T01:01:01.001 + timestamp(1..n)
    qtyv = take(1, n)
    insert into trades values(timev, qtyv)
}

writeData(6)
```
最后仍然输出了结果，说明聚合引擎的`dummyTable`参数只是一个样本表，它是否包含数据对结果并没有影响。

##### 6.4.2. 分组聚合示例

输入的流数据表增加了分组列sym，在聚合计算时设定`keyColumn`为sym。
```
share streamTable(1000:0, `time`sym`qty, [TIMESTAMP, SYMBOL, INT]) as trades
outputTable = table(10000:0, `time`sym`sumQty, [TIMESTAMP, SYMBOL, INT])
tradesAggregator = createStreamAggregator(3, 3, <[sum(qty)]>, trades, outputTable, `time, false,`sym, 50)
subscribeTable(, "trades", "tradesAggregator", 0, append!{tradesAggregator}, true)    

def writeData(n){
    timev = 2018.10.08T01:01:01.001 + timestamp(1..n)
    symv =take(`A`B, n)
    qtyv = take(1, n)
    insert into trades values(timev, symv, qtyv)
}

writeData(6)
```
为了观察方便，对执行结果的sym列排序输出：

```
select * from trades order by sym
```
time|sym|qty
---|---|---
2018.10.08T01:01:01.002	|A	|1
2018.10.08T01:01:01.004	|A	|1
2018.10.08T01:01:01.006	|A	|1
2018.10.08T01:01:01.003	|B	|1
2018.10.08T01:01:01.005	|B	|1
2018.10.08T01:01:01.007	|B	|1

outputTable的结果是根据sym列的内容进行的分组计算。
```
select * from outputTable 
```
time	|sym|	sumQty
---|---|---
2018.10.08T01:01:01.000	|A|	1
2018.10.08T01:01:01.003	|A|	1
2018.10.08T01:01:01.003	|B|	2

各组时间规整后统一从`000`时间点开始，根据`windowSize=3`, `step=3`, 每个组的窗口会按照`000`-`003`-`006`划分，计算触发在`003`,`006`两个时间点。 需要注意的是窗口内若没有任何数据，系统不会计算也不会产生结果，所以B组第一个窗口没有结果输出。

### 7. 总结


DolphinDB提供的streamAggregator是一个轻量、使用方便的流数据聚合引擎，它通过与streamTable流数据表合作来完成流数据的实时计算任务。它能够支持纵向聚合和横向聚合以及组合计算，支持自定义函数计算，分组聚合，无效数据预清洗，多级计算等功能，能满足流数据实时计算各方面需求。

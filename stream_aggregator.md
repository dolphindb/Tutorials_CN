# DolphinDB流数据聚合引擎

### 1. 概念

流数据是指随时间延续而增长的动态数据集合，金融机构的交易数据、物联网的传感器数据和互联网的运营数据都属于流数据的范畴。流数据的特性决定了它的数据集一直是动态变化的，传统的面向静态数据表的计算引擎无法胜任流数据领域的分析和计算任务，所以流数据场景需要一套针对性的计算引擎。

DolphinDB提供了灵活的面向流数据的聚合引擎，通过`createStreamAggregator`函数创建流数据聚合引擎，能够持续不间断地对流数据做聚合计算，并且将计算结果持续输出到指定的内存表中。

### 2. 函数说明

#### 2.1 语法

createStreamAggregator(windowTime, rollingTime, aggregators, dummyTable, outputTable, timeColumn, [useSystemTime, keyColumn, garbageSize])

#### 2.2 返回对象

返回一个抽象的表对象，作为聚合引擎的入口，往这个表写入数据，意味着数据进入聚合引擎进行计算。

#### 2.3 参数

- `useSystemTime`

类型：布尔值

说明：聚合引擎的驱动方式，为可选参数，缺省值为false。当参数值为true时，表示时间驱动方式：每当到达一个预定的时间点，聚合引擎就会激活并以设定的窗口截取流数据进行计算。在此模式下，系统内部会给每一个进入的数据添加一个毫秒级的系统时间戳作为数据窗口截取的依据。而当参数值为false时，为数据驱动方式：只有当数据进入系统时，聚合引擎才会被激活，此时窗口的截取依据是`timeColumn`列内容，时间的精度也取决于`timeColumn`列的时间精度。

- `windowTime`

类型：整型

说明：必选参数。由于流数据是持续变化的，而要对流数据进行聚合计算，每次要截取一段静态数据集用于计算，这个截取出来的静态数据集我们也称为数据窗口。`windowTime`参数用于指定数据窗口的大小。

`windowTime`的单位取决于`useSystemTime`参数。当`useSystemTime=true`时，`windowTime`的单位是毫秒；当`useSystemTime=false`时，`windowTime`的单位与数据本身的time列的精度相同，比如`timeColumn`列是timestamp类型，那么`windowTime`的单位是毫秒；如果`timeColumn`列是datetime类型，那么`windowTime`的单位是秒。数据窗口的边界原则是下包含上不包含。

- `rollingTime`

类型：整型

说明：必选参数。`rollingTime`参数指定触发计算的时间间隔。

当`useSystemTime=true`时，`rollingTime` 值是系统时间间隔，单位是毫秒，比如`rollingTime=3`，代表每隔3毫秒触发一次计算。

当`useSystemTime=false`时，`rollingTime` 值是数据本身包含的时间间隔，`rollingTime`应该和数据本身时间列具有相同的精度。比如数据时间是timestamp格式，精度为毫秒，那么`rollingTime`也以毫秒为单位；如果数据时间是datetime格式，精度为秒，那么`rollingTime`也应秒为单位。

基于简化场景复杂度的考量，我们要求`windowTime`必须能被`rollingTime`整除。

为了便于对计算结果的观察和对比，系统会对窗口的起始时间统一对齐，第一条进入系统的数据时间往往不是很规整的时间，例如2018.10.10T03:26:39.178，如果`rollingTime`设置为100，那么系统会将其窗口起始时间规整为2018.10.10T03:26:39.100，对齐移动范围最大不超过1秒。具体对齐的公式如下：

窗口起始时间 = `firstDataTime - mod(firstDataTime,rollingTime)`。其中firstDataTime为第一条数据进入的时间。当聚合引擎使用分组计算时，所有分组使用统一的起始时间，所有分组的起始时间以最早进入系统的数据按以上公式计算得出。

- `aggregators`

类型：元数据

说明：必选参数。这是聚合引擎的核心参数，它以元数据的格式提供一组消费流数据的聚合函数。类似如下格式`<[sum(qty)]>`,`<[sum(qty),max(qty),avg(price)]>`。支持系统内所有的聚合函数，也支持对聚合结果使用表达式来满足更复杂的场景，比如 `<[avg(price1)-avg(price2)]>`,`<[std(price1-price2)]>`这样的写法。

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

输出表的第一列必须是时间类型，用于存放发生计算的时间点，这个列的数据类型要和`dummyTable`的时间列类型一致。

如果`keyColumn`参数不为空，那么输出表的第二列必须是分组列。

从第三列开始，按照顺序保存聚合计算的结果。最终的表结构是`时间列，分组列(可选)，聚合结果列1，聚合结果列2...` 这样的格式。

- `timeColumn`

类型：字符串

说明：必选参数。指定流数据表时间列的名称。根据`timeColumn`参数，聚合引擎从流数据表中取得对应列的时间数据。

- `keyColumn`

类型：字符串

说明：可选参数。指定分组计算的组别，以对流数据分组进行聚合计算。比如以股市报价数据中的每支股票为一组进行聚合计算。

- `garbageSize`

类型：整型

说明：此参数可选，设定一个阈值，当内存中缓存的历史数据的行数超出阈值时清理无用缓存。

当流数据聚合引擎在运行时，每次计算都会需要载入新的窗口数据到内存中进行计算，随着计算过程的持续，内存中缓存的数据会越来越多，这时候需要有一个机制来清理不再需要的历史数据。当内存中保留的历史数据行数超过`garbageSize`设定值时会引发清理内存。

当需要分组计算时，每个分组的历史数据记录数是分别统计的，所以内存清理的动作也是各分组独立进行的。当每个组的历史数据记录数超出`garbageSize`时都会引发清理内存。

### 3. 示例

#### 3.1. `windowTime` 与 `rollingTime`

输入流数据表包含time和qty两列，time精度为毫秒，根据设定的窗口对流数据进行持续`sum(qty)`计算。本示例的流数据表中使用的时间精度为毫秒，为了方便观察，模拟输入的数据流频率也设为每毫秒一条数据的频率。

以下代码建立流数据表trades，设定聚合计算参数，并定义函数`writeData`以生成模拟数据。 
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

第一次操作：模拟写入5条数据
```
writeData(5)
```
使用 `select * from trades` 查看流数据表，表里已经有5条数据：

time	                |qty
---|---
2018.10.08T01:01:01.002	| 1
2018.10.08T01:01:01.003	| 1
2018.10.08T01:01:01.004	| 1
2018.10.08T01:01:01.005	| 1
2018.10.08T01:01:01.006	| 1

再用`select * from outputTable`查看输出表，发现已经发生了一次计算：

time|	sumQty
---|---
2018.10.08T01:01:01.005 |3

发生计算的时间是2018.10.08T01:01:01.005。根据`windowTime=5`，起始时间应该是2018.10.08T01:01:01.000，可以看出，系统对首个数据的时间2018.10.08T01:01:01.002做了对齐操作。


第二次操作：清空数据表，设置 `windowTime=6`，`rollingTime=3`，模拟写入10条数据：

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

然后查看流数据表trades内容：

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
2018.10.08T01:01:01.003	|1
2018.10.08T01:01:01.006	|4
2018.10.08T01:01:01.009	|6

可以看到已经成功触发了三次计算。

从这个结果也可以发现`windowTime`的规则：窗口起始时间是以第一个数据时间对齐后为准，窗口是以`windowTime`为大小，`rollingTime`为步长移动的。

下面根据三次计算的过程来解释聚合引擎是如何进行窗口数据的确定的。为方便阅读，下段的案例说明中对时间的描述省略相同的2018.10.08T01:01:01部分，只列出毫秒部分。

本例中，窗口的起始是第一个数据的时间`002`为基础进行对齐，时间对齐后为`000`，因为`rollingTime=3`，所以第一次触发计算的时间是`003`，第一个窗口的实际大小是3毫秒的时间(从`000`到`003`)。 由于触发计算的数据本身`003`是不包含在窗口内的，最终第一次计算窗口中只包含了`002`一条记录，计算`sum(qty)`的结果是1；而第二次计算发生在`006`，根据`windowTime=6`,那么实际窗口大小是6毫秒(从`000`到`006`)，实际窗口中包含了从`002`到`005`四个数据，计算结果为4；以此类推，第三次的计算窗口是从`003`到`009`,实际包含了从`003`到`008`的6个数据，计算结果为6。

#### 3.2. dummyTable示例

以上述示例脚本作为基础，这里稍作改变来展示`dummyTable`的作用。增加一个结构完全与trades相同的modelTable对象，将modelTable作为`dummyTable`参数，而实际的数据仍然写入trades。
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
最后执行的结果仍然是与示例3.1相同，说明聚合引擎的`dummyTable`参数只是一个样本表，它是否包含数据对结果并没有影响。

#### 3.3. keyColumn示例

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


观察outputTable，看到结果是根据sym列的内容进行的分组计算。
```
select * from outputTable 
```
time	|sym|	sumQty
---|---|---
2018.10.08T01:01:01.003	|A|	1
2018.10.08T01:01:01.006	|A|	1
2018.10.08T01:01:01.006	|B|	2

各组时间对齐后统一从`000`时间点开始，根据`windowTime=3`, `rollingTime=3`, 每个组的窗口会按照`000`-`003`-`006`划分，计算触发在`003`,`006`两个时间点。 需要注意的是窗口内若没有任何数据，系统不会计算也不会产生结果，所以B组第一个窗口没有结果输出。

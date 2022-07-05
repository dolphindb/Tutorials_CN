### 流数据横截面引擎

DolphinDB提供流数据横截面引擎，对实时流数据最新的截面数据进行计算。


### 设计

DolphinDB database 横截面引擎对实时数据中每组的最新数据进行运算，比如金融里对所有股票的最新交易量求聚合值，工业物联网里对一批设备的最新温度求聚合值等，都需要用到横截面引擎。

横截面引擎包含两个部分，一是横截面数据表，二是计算引擎。横截面数据表保存所有分组的最新记录。计算引擎是一组聚合计算表达式以及触发器，系统会按照指定的规则触发对横截面数据表进行计算，计算结果会保存到指定的数据表中。


### createCrossSectionalAggregator函数

* 语法
```
createCrossSectionalAggregator(name, [metrics], dummyTable, [outputTable], keyColumn, [triggeringPattern="perBatch"], [triggeringInterval=1000], [useSystemTime=true], [timeColumn])
```

* 参数

name是一个字符串，表示横截面引擎的名称，是横截面引擎的唯一标识。它可以包含字母，数字和下划线，但必须以字母开头。

metrics是元代码。它可以是系统内置或用户自定义的函数，如<[sum(qty), avg(price)]>，可以对结果使用表达式，如<[avg(price1)-avg(price2)]>，也可以对计算列进行运算，如<[std(price1-price2)]>，也可以是一个函数返回多个指标，如自定义函数 func(price) , 则可以指定metrics为<[func(price) as ['res1','res2']> 。详情可参考[元编程](https://www.dolphindb.cn/cn/help/Objects/Metaprogramming.html)。metrics可以都是聚合表达式，也可以都是非聚合表达式，不能混合。如果是非聚合表达式，输出的记录数必须等于输入的记录数。

dummyTable是表对象，它可以不包含数据，但它的结构必须与订阅的流数据表相同。

outputTable是表对象，用于保存计算结果。输出表的列数为metrics数量+1，第一列为TIMESTAMP类型，用于存放发生计算的时间戳，其他列的数据类型必须与metrics返回结果的数据类型一致。

keyColumn是一个字符串，指定dummyTable的某列为横截面引擎的key。横截面引擎的每次计算，仅使用每个key对应的最新一行记录。

triggeringPattern是一个字符串，表示触发计算的方式。它可以是以下取值：
- "perRow": 每插入一行数据触发一次计算
- "perBatch": 每插入一次数据触发一次计算
- "interval": 按一定的时间间隔触发计算
- "keyCout": 当前时间下更新的key的个数达到设定值，就会触发一次计算, 但如果达到设定值之前，有一个key的时间比当前时间更新，也会触发计算，同时把当前更新到新的时间, 指定keyCount，则必须指定timeColumn，同时假定，同一批次的数据的时间都相同，数据按时间顺序插入。

triggeringInterval是一个整数。只有当triggeringPattern的取值为"interval"时才生效，表示触发计算的时间间隔。默认值为1000毫秒。

useSystemTime是一个可选参数，表示outputTable中第一列（时间列）为系统时间(useSystemTime=true)或数据中时间列(useSystemTime=false)。

timeColumn是一个字符串。当useSystemTime=false时，指定订阅的流数据表中时间列的名称。仅支持TIMESTAMP类型。

* 详情

返回一个表对象，向该表中写入数据意味着这些数据进入横截面引擎进行计算。keyColumn指定列中的每一个key对应表中的唯一一行，如果新插入的数据中的key已经存在，那么将进行更新操作，如果key不存在，那么将在横截面引擎表的末尾添加一行新的记录。因此，横截面引擎中的数据总是每个key最新的数据。

### 示例

股市的交易数据会实时以流数据的形式写入数据表trades。该表结构如下：

股票代码(sym)| 时间(time)|成交价(price)| 成交数量(qty)
---|---|---|---

trades表会随着时间推进不断积累各个股票从开盘到当前为止的交易数据。在交易数据持续写入的过程中，用户需要实时计算所有股票的最新成交量之最大值、最新成交金额之最大值，以及最新交易金额之和。

* 在以下步骤中，使用横截面引擎结合流数据订阅，以实现上述场景：

    * 定义流数据表，以写入模拟交易数据。
    ```
    share streamTable(10:0,`time`sym`price`qty,[TIMESTAMP,SYMBOL,DOUBLE,INT]) as trades
    ```
    
    * 定义结果表，以保存横截面引擎计算的结果。
    ```
    outputTable = table(10:0, `time`maxQty`maxDollarVolume`sumDollarVolume, [TIMESTAMP,INT,DOUBLE,DOUBLE])
    ```
    
    * 创建横截面引擎，指定表达式、输入表、结果表、分组列、计算频率。返回的对象 tradesCrossAggregator 为保存横截面数据的表。
    ```
    tradesCrossAggregator=createCrossSectionalAggregator(name="CrossSectionalDemo", metrics=<[max(qty), max(price*qty), sum(price*qty)]>, dummyTable=trades, outputTable=outputTable, keyColumn=`sym, triggeringPattern=`perRow, useSystemTime=false, timeColumn=`time)
    ```
    
    * 订阅流数据表，将新写入的流数据追加到横截面引擎中。
    ```
    subscribeTable(tableName="trades", actionName="tradesCrossAggregator", offset=-1, handler=append!{tradesCrossAggregator}, msgAsTable=true)
    ```
    
    * 最后模拟生成实时交易流数据。
    ```
    def writeData(n){
       timev  = 2000.10.08T01:01:01.001 + timestamp(1..n)
       symv   = take(`A`B, n)
       pricev = take(102.1 33.4 73.6 223,n)
       qtyv   = take(60 74 82 59, n)
       insert into trades values(timev, symv, pricev, qtyv)
    }
    writeData(4);
    ```
    
* 完整脚本：
    ```
    share streamTable(10:0,`time`sym`price`qty,[TIMESTAMP,SYMBOL,DOUBLE,INT]) as trades
    outputTable = table(10:0, `time`maxQty`maxDollarVolume`sumDollarVolume, [TIMESTAMP,INT,DOUBLE,DOUBLE])
    tradesCrossAggregator=createCrossSectionalAggregator(name="CrossSectionalDemo", metrics=<[max(qty), max(price*qty), sum(price*qty)]>, dummyTable=trades, outputTable=outputTable, keyColumn=`sym, triggeringPattern=`perRow, useSystemTime=false, timeColumn=`time)
    subscribeTable(tableName="trades", actionName="tradesCrossAggregator", offset=-1, handler=append!{tradesCrossAggregator}, msgAsTable=true)
    def writeData(n){
       timev  = 2000.10.08T01:01:01.001 + timestamp(1..n)
       symv   = take(`A`B, n)
       pricev = take(102.1 33.4 73.6 223, n)
       qtyv   = take(60 74 82 59, n)
       insert into trades values(timev, symv, pricev,qtyv)
    }
    writeData(4);
    ```
执行完成后，查询流数据表，共有A与B两只股票的4笔交易数据：
```
select * from trades
```
   time|sym |price |qty
   ---|---|---|---
   2000.10.08T01:01:01.002| A | 102.1| 60
   2000.10.08T01:01:01.003| B | 33.4| 74
   2000.10.08T01:01:01.004| A | 73.6| 82
   2000.10.08T01:01:01.005| B | 223 | 59

截面数据表保存了A与B两只股票最新的交易数据：
```
select * from tradesCrossAggregator
```
   time|	sym|	price|	qty
   ---|---|---|---
   2000.10.08T01:01:01.004|A|73.6|82
   2000.10.08T01:01:01.005|B|223|59

由于横截面引擎采用了"perRow"每行触发计算的频率，所以每向横截面表写入一行数据，横截面引擎都会进行一次计算，向结果表插入一条结果数据：
```
select * from outputTable
```

   time         |           maxQty| maxDollarVolume | sumDollarVolume  
   ---|---|---|---
   2019.04.08T04:26:01.634 | 60 | 6126  | 6126  
   2019.04.08T04:26:01.634 | 74 | 6126 | 8597.6
   2019.04.08T04:26:01.634 | 82 | 6035.2 | 8506.8
   2019.04.08T04:26:01.634 | 82 | 13157 | 19192.2

在进行后续操作之前，我们首先取消以上订阅，并取消横截面引擎的调用，并删除数据表trades。
```
unsubscribeTable(,`trades, "tradesCrossAggregator")
dropAggregator("CrossSectionalDemo")
undef(`trades, SHARED)
```

triggeringPattern 支持三种模式，若取值"perBatch"时表示每追加一批数据触发一次写入。以下按"perBatch"模式启用横截面引擎，脚本共生成12条记录，分三批写入，预期产生3次输出：

```
share streamTable(10:0,`time`sym`price`qty,[TIMESTAMP,SYMBOL,DOUBLE,INT]) as trades
outputTable = table(1:0, `time`maxQty`maxDollarVolume`sumDollarVolume, [TIMESTAMP,INT,DOUBLE,DOUBLE])
tradesCrossAggregator=createCrossSectionalAggregator("CrossSectionalDemo", <[max(qty), max(price*qty), sum(price*qty)]>, trades, outputTable, `sym, `perBatch, useSystemTime=false, timeColumn=`time)
subscribeTable(,"trades","tradesCrossAggregator",-1,append!{tradesCrossAggregator},true)
def writeData1(){
  timev  = 2000.10.08T01:01:01.001 + timestamp(1..4)
  symv   = take(`A`B, 4)
  pricev = 102.1 33.4 102.3 33.2
  qtyv   = 10 20 40 30
  insert into trades values(timev, symv, pricev,qtyv)
}
def writeData2(){
  timev  = 2000.10.08T01:01:01.005 + timestamp(1..2)
  symv   = `A`B
  pricev = 102.4 33.1
  qtyv   = 120 60
  insert into trades values(timev, symv, pricev,qtyv)
}
//写入2批数据，预期会触发2次计算，输出2次聚合结果。
writeData1();
sleep(100)
writeData2();
dropAggregator(`CrossSectionalDemo)
unsubscribeTable(, `trades, `tradesCrossAggregator)
```

trades表中，共写入了6条记录：
```
select * from trades
```
   time|sym|price|qty|
   ---|---|---|---|
   2000.10.08T01:01:01.002 | A   | 102.1 | 10 |
   2000.10.08T01:01:01.003 | B   | 33.4  | 20 |
   2000.10.08T01:01:01.004 | A   | 102.3 | 40 |
   2000.10.08T01:01:01.005 | B   | 33.2  | 30 |
   2000.10.08T01:01:01.006 | A   | 102.4  | 120 |
   2000.10.08T01:01:01.007 | B   | 33.1   | 60 |

横截面表包含每组最新记录：
```
select * from tradesCrossAggregator
```
   time|sym|price|qty|
   ---|---|---|---|
   2000.10.08T01:01:01.006 | A   | 102.4  | 120  |
   2000.10.08T01:01:01.007 | B   | 33.1   | 60  |

由于分2次写入，在perBatch模式下，横截面引擎输出了2条记录：
```
select * from outputTable
```
   time| maxQty | maxDollarVolume | sumDollarVolume   |
   ---|---|---|---|
   2019.04.08T04:52:50.255 | 40    | 4092    | 5088 |
   2019.04.08T04:52:50.355 | 120    | 12288    | 14274 |

 triggeringPattern取值"interval"时，必须配合triggeringInterval参数一起使用，表示每隔triggeringInterval毫秒触发一次计算。本例分6次写入数据，每500毫秒触发一次计算，每次1条数据，间隔500或1000毫秒。请注意，这里没有指定useSystemTime参数为false，会返回计算发生的时刻。
   ```
   share streamTable(10:0,`time`sym`price`qty,[TIMESTAMP,SYMBOL,DOUBLE,INT]) as trades
   outputTable = table(1:0, `time`avgPrice`volume`dollarVolume`count, [TIMESTAMP,DOUBLE,INT,DOUBLE,INT])
   tradesCrossAggregator=createCrossSectionalAggregator(name="tradesCrossAggregator", metrics=<[avg(price), sum(qty), sum(price*qty), count(price)]>, dummyTable=trades, outputTable=outputTable, keyColumn=`sym, triggeringPattern="interval", triggeringInterval=500)
   subscribeTable(tableName="trades", actionName="tradesStats", offset=-1, handler=append!{tradesCrossAggregator}, msgAsTable=true)

   insert into trades values(2020.08.12T09:30:00.000, `A, 10, 20)
   sleep(500)
   insert into trades values(2020.08.12T09:30:00.000 + 500, `B, 20, 10)
   sleep(500)
   insert into trades values(2020.08.12T09:30:00.000 + 1000, `A, 10.1, 20)
   sleep(1000)
   insert into trades values(2020.08.12T09:30:00.000 + 2000, `B, 20.1, 30)
   sleep(500)
   insert into trades values(2020.08.12T09:30:00.000 + 2500, `B, 20.2, 40)
   sleep(500)
   insert into trades values(2020.08.12T09:30:00.000 + 3000, `A, 10.2, 20)

   select * from outputTable;
   ```

   time|avgPrice|volume|dollarVolume|count
   ---|---|---|---|---|
2021.07.27T10:54:00.303	| 10 | 20 | 200 | 1
2021.07.27T10:54:00.818 | 15 | 30 | 400 | 2
2021.07.27T10:54:01.331 | 15.05 | 30 | 402 | 2
2021.07.27T10:54:02.358 | 15.1 | 50 | 805 | 2
2021.07.27T10:54:02.871 | 15.15 | 60 | 1010 | 2
2021.07.27T10:54:03.386 | 15.2 | 60 | 1012 | 2


   输出表的记录数会不断增长。这是因为triggeringPattern="interval"时，计算是按照系统时间定时触发，与是否有新数据进入无关。


   * 横截面表作为最终结果

   在以上的例子中，createCrossSectionalAggregator的返回结果（以下称为横截面表）是为聚合计算提供的一个中间结果，但横截面表亦可为最终结果。例如若需要定时刷新某只股票的最新交易价格，按照常规思路是从实时交易表中按代码筛选股票并取出最后一条记录，而交易表的数据量是随着时间快速增长的，如果频繁做这样的查询，无论从系统的资源消耗还是从查询的效能来看都不是最优的做法。而横截面表永远只保存所有股票的最近一次交易数据，数据量是稳定的，对于这种定时轮询的场景非常合适。

   要将横截面表作为最终结果，需要在创建横截面时，对metrics与outputTable这两个参数置空。
      
   ```
   tradesCrossAggregator=createCrossSectionalAggregator("CrossSectionalDemo", , trades, , `sym, `perRow)
   ```


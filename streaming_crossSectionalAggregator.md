### 流数据横截面引擎
在处理实时流数据时，不仅需要使用时序聚合引擎按时间做纵向聚合计算，也需要对所有分组最新的截面数据做计算。针对这种计算需求，DolphinDB提供了流数据横截面聚合引擎。


### 设计
DolphinDB database 横截面聚合引擎对流数据中所有分组的最新数据做聚合运算，比如金融里对所有股票的最新交易量求极值，工业物联网里对一批设备的最新温度求均值等，都需要用到横截面引擎。

横截面聚合引擎包含两个部分，一是横截面数据表，二是计算引擎。横截面数据表保存所有分组的最新记录。计算引擎是一组聚合计算表达式以及触发器，系统会按照指定的规则触发对横截面数据表做聚合计算，计算结果会保存到指定的数据表中。


### createCrossSectionalAggregator函数

* 语法
```
createCrossSectionalAggregator(name, [metrics], dummyTable, [outputTable], keyColumn, [triggeringPattern="perBatch"], [triggeringInterval=1000])
```

* 参数

name是一个字符串，表示横截面聚合引擎的名称，是横截面聚合引擎的唯一标识。它可以包含字母，数字和下划线，但必须以字母开头。

metrics是元代码。它可以是系统内置或用户自定义的函数，如<[sum(qty), avg(price)]>，可以对聚合结果使用表达式，如<[avg(price1)-avg(price2)]>，也可以对计算列进行聚合运算，如<[std(price1-price2)]>。详情可参考[元编程](https://www.dolphindb.cn/cn/help/Metaprogramming.html)。

dummyTable是表对象，它可以不包含数据，但它的结构必须与订阅的流数据表相同。

outputTable是表对象，用于保存计算结果。输出表的列数为metrics数量+1，第一列为TIMESTAMP类型，用于存放发生计算的时间戳,，其他列的数据类型必须与metrics返回结果的数据类型一致。

keyColumn是一个字符串，指定dummyTable的某列为横截面聚合引擎的key。keyColumn指定列中的每一个key对应表中的唯一一行。

triggeringPattern是一个字符串，表示触发计算的方式。它可以是以下取值：
- "perRow": 每插入一行数据触发一次计算
- "perBatch": 每插入一次数据触发一次计算
- "interval": 按一定的时间间隔触发计算

triggeringInterval是一个整数。只有当triggeringPattern的取值为"interval"时才生效，表示触发计算的时间间隔。默认值为1000毫秒。

* 详情

返回一个表对象，向该表中写入数据意味着这些数据进入横截面聚合引擎进行计算。keyColumn指定列中的每一个key对应表中的唯一一行，如果新插入的数据中的key已经存在，那么将进行更新操作，如果key不存在，那么将在横截面聚合引擎表的末尾添加一行新的记录。因此，横截面聚合引擎中的数据总是每个key最新的数据。

### 示例

接下来用一个例子来讲解横截面的应用：

股市的交易数据会实时以流数据的形式写入数据表trades。该表结构如下：

股票代码(sym)| 时间(time)|成交价(price)| 成交数量(qty)
---|---|---|---

trades表会随着时间推进不断积累各个股票从开盘到当前为止的交易数据。在交易数据持续写入的过程中，用户需要实时计算所有股票的最新成交量之最大值、最新成交金额之最大值，以及最新交易金额之和。

* 在以下步骤中，使用横截面聚合引擎结合流数据订阅，以实现上述场景：

    * 定义流数据表，以写入模拟交易数据。
    ```
    share streamTable(10:0,`time`sym`price`qty,[TIMESTAMP,SYMBOL,DOUBLE,INT]) as trades
    ```
    
    * 定义结果表，以保存聚合引擎计算的结果。
    ```
    outputTable = table(1:0, `time`maxQty`maxDollarVolume`sumDollarVolume, [TIMESTAMP,INT,DOUBLE,DOUBLE])
    ```
    
    * 创建横截面聚合引擎，指定表达式、输入表、结果表、分组列、计算频率。返回的对象 tradesCrossAggregator 为保存横截面数据的表。
    ```
    tradesCrossAggregator=createCrossSectionalAggregator("CrossSectionalDemo", <[max(qty), max(price*qty), sum(price*qty)]>, trades, outputTable, `sym, `perRow)
    ```
    
    * 订阅流数据表，将新写入的流数据追加到横截面聚合引擎中。
    ```
    subscribeTable(,"trades","tradesCrossAggregator",-1,append!{tradesCrossAggregator},true)
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
    outputTable = table(1:0, `time`maxQty`maxDollarVolume`sumDollarVolume, [TIMESTAMP,INT,DOUBLE,DOUBLE])
    tradesCrossAggregator=createCrossSectionalAggregator("CrossSectionalDemo", <[max(qty), max(price*qty), sum(price*qty)]>, trades, outputTable, `sym, `perRow)
    subscribeTable(,"trades","tradesCrossAggregator",-1,append!{tradesCrossAggregator},true)
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

查询截面数据表，里面保存了A与B两只股票最新的交易数据：
```
select * from tradesCrossAggregator
```
   time|	sym|	price|	qty
   ---|---|---|---
   2000.10.08T01:01:01.004|A|73.6|82
   2000.10.08T01:01:01.005|B|223|59

查询聚合结果表，由于横截面引擎采用了"perRow"每行触发计算的频率，所以每往横截面表写入一行数据，聚合引擎都会做一次计算，在结果表产生一条结果数据：
```
select * from outputTable
```

   time         |           maxQty| maxDollarVolume | sumDollarVolume  
   ---|---|---|---
   2019.04.08T04:26:01.634 | 60 | 6126  | 6126  
   2019.04.08T04:26:01.634 | 74 | 6126 | 8597.6
   2019.04.08T04:26:01.634 | 82 | 6035.2 | 8506.8
   2019.04.08T04:26:01.634 | 82 | 13157 | 19192.2

在进行后续操作之前，我们首先取消以上订阅，并取消聚合引擎的调用，并删除数据表trades。
```
unsubscribeTable(,`trades, "tradesCrossAggregator")
dropAggregator("CrossSectionalDemo")
undef(`trades, SHARED)
```

triggeringPattern 支持三种模式，若取值"perBatch"时表示每追加一批数据触发一次写入。以下按"perBatch"模式启用横截面引擎，脚本共生成12条记录，分三批写入，预期产生3次输出：

```
share streamTable(10:0,`time`sym`price`qty,[TIMESTAMP,SYMBOL,DOUBLE,INT]) as trades
outputTable = table(1:0, `time`maxQty`maxDollarVolume`sumDollarVolume, [TIMESTAMP,INT,DOUBLE,DOUBLE])
tradesCrossAggregator=createCrossSectionalAggregator("CrossSectionalDemo", <[max(qty), max(price*qty), sum(price*qty)]>, trades, outputTable, `sym, `perBatch)
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

由于分2次写入，在perBatch模式下，聚合引擎输出了2条记录：
```
select * from outputTable
```
   time| maxQty | maxDollarVolume | sumDollarVolume   |
   ---|---|---|---|
   2019.04.08T04:52:50.255 | 40    | 4092    | 5088 |
   2019.04.08T04:52:50.355 | 120    | 12288    | 14274 |

 triggeringPattern取值"interval"时，必须配合triggeringInterval参数一起使用，表示每隔triggeringInterval毫秒触发一次计算。本例分6次写入数据，每次间隔500毫秒，共耗时3000毫秒，横截面引擎设置为每1000毫秒触发1次计算，预期最终计算输出3条记录。
   ```
   share streamTable(10:0,`time`sym`price`qty,[TIMESTAMP,SYMBOL,DOUBLE,INT]) as trades
   outputTable = table(1:0, `time`maxQty`maxDollarVolume`sumDollarVolume, [TIMESTAMP,INT,DOUBLE,DOUBLE])
   tradesCrossAggregator=createCrossSectionalAggregator("CrossSectionalDemo", <[max(qty), max(price*qty), sum(price*qty)]>, trades, outputTable, `sym, `interval,1000)
   subscribeTable(,"trades","tradesCrossAggregator",-1,append!{tradesCrossAggregator},true)
   def writeData(n){
      timev  = 2000.10.08T01:01:01.001 + timestamp(1..n)
      symv   = take(`A`B, n)
      pricev = take(102.1 33.4 102.3 33.2,n)
      qtyv   = take(10 20 40 30, n)
      insert into trades values(timev, symv, pricev,qtyv)
   }
   a = now()
   writeData(2);
   sleep(500)
   writeData(1);
   sleep(500)
   writeData(3);
   sleep(500)
   writeData(2);
   sleep(500)
   writeData(4);
   sleep(500)
   writeData(3);
   sleep(500)
   b = now()
   select count(*) from outputTable
   ```
   结果与预期一致，为3。若再次执行 select count(*) from outputTable 会发现随着时间推移，计算输出会不断增长。因为在"interval"模式下，无论是否有新的数据写入，计算均会定时触发。

   * 横截面表作为最终结果

   虽然在上面的例子中，横截面表是为聚合计算提供的一个中间数据表，但横截面表亦可为最终结果。比如我们需要定时刷新某只股票的最新交易价格，按照常规思路是从实时交易表中按代码筛选股票并取出最后一条记录，而交易表的数据量是随着时间快速增长的，如果频繁做这样的查询，无论从系统的资源消耗还是从查询的效能来看都不是最优的做法。而横截面表永远只保存所有股票的最近一次交易数据，数据量是稳定的，对于这种定时轮询的场景非常合适。

   要将横截面表作为最终结果，需要在创建横截面时，对metrics与outputTable这两个参数置空。
      
   ```
   tradesCrossAggregator=createCrossSectionalAggregator("CrossSectionalDemo", , trades, , `sym, `perRow)
   ```


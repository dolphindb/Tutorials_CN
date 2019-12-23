### 高频因子的实时计算

本示例通过DolphinDB实现市场行情数据实时计算因子，本例中使用到了DolphinDB以下功能：

* 流数据发布
	
	用户通过API将实时的市场数据写入到DolphinDB的流数据表中，流数据表的数据可在DolphinDB中通过订阅的方式进行实时处理。

* 流数据订阅

	当实时市场数据进入流数据表之后，通过订阅函数`subscribeTable`可以将实时数据和数据处理函数之间建立关联，使得进入流数据表的数据被即时处理。

* 并行计算

	当需要使用同一份流数据计算多个因子时，通过使用`ploop`高阶函数结合`call`函数，在同一个订阅处理函数中实现并行多因子计算，提高数据的处理效率。
	
#### 1. 系统配置

本次示例程序的服务器程序采用单机模式启动，启用流数据发布和订阅。配置文件（默认为dolphindb.cfg）的内容建议如下：
```
mode=single
maxPubConnections=8
subPort=20001
persistenceDir=dbCache
maxMemSize=24
```

单机模式启动后，默认端口为8848.

#### 2. 模拟产生高频交易数据

模拟产生100只股票的数据。symbol从000001到000100，总共100,000,000条记录，22列：symbol, time, ap1..ap5, bp1..bp5, av1..av5, bv1..bv5。其中ap1..ap5代表前5档卖方出价，av1..av5代表卖方出价对应的量，bp1..bp5以及bv1..bv5为前5档买方出价以及对应的量。我们对模拟数据做如下限制：ap1<ap2<ap3<ap4<ap5, bp1>bp2>bp3>bp4>bp5, 均为小数点后两位。 

* 创建流数据表tick，以存放高频数据。
```
def createTickTable(){
	share(streamTable(1000:0, `symbol`time`ap1`ap2`ap3`ap4`ap5`bp1`bp2`bp3`bp4`bp5`av1`av2`av3`av4`av5`bv1`bv2`bv3`bv4`bv5`mp, [SYMBOL,TIME,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,INT]), `tick)
	clearTablePersistence(objByName(`tick))
	enableTablePersistence(table=objByName(`tick), cacheSize=100000)
}
createTickTable()
```

* 定义generateData函数，循环生成100,000,000笔成交记录，并写入tick表。此函数将在任务提交时执行。
```
def generateData(times){
	for(j in 0..times){
		batchSize = 1
		sym = rand(symbol(lpad(string(1..100),6,"0")), batchSize)
		tim = take(time(now()),batchSize)
		ap1= rand(100..105, batchSize)/100.0
		ap2= rand(100..105, batchSize)/100.0
		ap3= rand(100..105, batchSize)/100.0
		ap4= rand(100..105, batchSize)/100.0
		ap5= rand(100..105, batchSize)/100.0
		bp1= rand(100..107, batchSize)/100.0
		bp2= rand(100..107, batchSize)/100.0
		bp3= rand(100..107, batchSize)/100.0
		bp4= rand(100..107, batchSize)/100.0
		bp5= rand(100..107, batchSize)/100.0
		av1= rand(100..500, batchSize)
		av2= rand(100..500, batchSize)
		av3= rand(100..500, batchSize)
		av4= rand(100..500, batchSize)
		av5= rand(100..500, batchSize)
		bv1= rand(100..500, batchSize)
		bv2= rand(100..500, batchSize)
		bv3= rand(100..500, batchSize)
		bv4= rand(100..500, batchSize)
		bv5= rand(100..500, batchSize)
		mp= rand(1..10, batchSize)
		data = table(sym as symbol,tim as time,ap1,ap2,ap3,ap4,ap5,bp1,bp2,bp3,bp4,bp5,av1,av2,av3,av4,av5,bv1,bv2,bv3,bv4,bv5,mp)
		objByName(`tick).tableInsert(data)
	}
}
```

#### 3. DolphinDB订阅高频数据，实时计算因子

本示例中需要计算5个因子factor1~5。
* 其中1~3号因子使用当前数据计算得到
* 4~5号时序数据相关因子，需要结合历史数据计算，所以需要传入完整的tick表。在满足因子计算的前提下，tick表设置在内存中保留不超过100000行记录。

实现思路如下

* 实现各因子的计算函数。
* 在流数据订阅处理函数中，将订阅到的流数据作为参数传递给因子计算函数。
* 在需要计算较多的因子的情况下，可以使用并行方式调用计算函数。在示例中用 `ploop` + `call`函数的结合即可实现。
* 并行计算得到的结果合并保存到factor表中，factor结构如下：

 	 symbol | time | factorValue | factorType
	---|---|---|---
	000001 | 17:38:41.894 | 0.024329 | factor1

具体的实现脚本如下：

* 因子的实现函数
```
def factor1(t){
	return select symbol,time(now()) as time, (av1-bv1)/(av1+bv1) as factorValue, "factor1" as factorType from t
}

def factor2(t){
	return select symbol,time(now()) as time, (av1+av2+av3+av4+av5-bv1-bv2-bv3-bv4-bv5)/ (av1+av2+av3+av4+av5+bv1+bv2+bv3+bv4+bv5) as factorValue, "factor2" as factorType from t
}
def factor3(t){
 	w = exp(-10 * 0..4/t.mp[0])
 	return select symbol, time(now()) as time, 0.5*log(rowSum([bv1,bv2,bv3,bv4,bv5]*w)/rowSum([av1,av2,av3,av4,av5]*w)) as factorValue, "factor3" as factorType from t
}
def factor4(tickTable, t){
	sym = exec distinct(symbol) from t
 	t1 = select symbol,ap1/mavg(ap1, 30)-1 as factorValue from tickTable where symbol in sym context by symbol
 	return select symbol,time(now()) as time, factorValue, "factor4" as factorType from t1 where !isNull(factorValue)
} 
def factor5(tickTable, t){
	sym = exec distinct(symbol) from t
	t1 =  select symbol, ap1/move(ap1, 30)-1 as factorValue from tickTable where symbol in sym context by symbol
 	return select symbol,time(now()) as time, factorValue, "factor5" as factorType from t1 where !isNull(factorValue)
}
```

* 创建数据表factor，以存放因子计算结果。
```
def createFactorTable(){
	t =	streamTable(100:0, `symbol`time`factorValue`factorType, [SYMBOL,TIME, DOUBLE, SYMBOL]);
	share(t,`factor )
}
createFactorTable()
```
* 定义函数factorHandler作为流数据的处理函数，多个因子通过`ploop`结合`call`并行计算。
```
def factorHandler(mutable factorTable, tickTable, msg){
	funcs = [factor1{msg}, factor2{msg}, factor3{msg}, factor4{tickTable,msg}, factor5{tickTable,msg}]
	factorTable.tableInsert(ploop(call, funcs).unionAll(false))
}
```
* 设置市场实时数据的订阅，将实时数据和因子计算函数相关联。

本示例中除了必要参数，其他订阅参数都采用默认值。若实时数据流入速度非常快，而因子计算相对较慢，可能会导致处理滞后。此时可以调整batchSize和throttle等参数，使得实时数据的处理速度匹配流入速度。具体的参数含义以及流数据性能调优可以参考[DolphinDB流数据教程](https://github.com/dolphindb/Tutorials_CN/blob/master/streaming_tutorial.md)。

 ```
subscribeTable(tableName=`tick, actionName=`createFactor, handler=factorHandler{objByName(`factor), objByName(`tick)}, msgAsTable=true)
```
以上代码中，msgAsTable参数设为true，订阅收到的数据会以table的形式传递给factorHandler，方便在factorHandler内部使用SQL语句进行数据操作。

* 提交产生模拟数据的任务，模拟数据每次随机提交1到10行数据写入流数据表tick中，每次提因子计算函数都会被触发。
```
submitJob("gendata", "generate data", generateData, 100000000)
```

#### 4.观察结果

* 在GUI中运行如下代码，查看因子的线性趋势图：

```
t = select last(factorValue) as factorValue from factor where symbol = `000001,factorType=`factor1 group by time
plot(t.factorValue, t.time)
```

* 可以通过 pivot by 关键字，对不同因子进行行列转置，得到按不同因子横向排列的最新计算结果：

```
select factorValue from factor pivot by symbol, factorType
```

symbol | factor1 | factor2 | factor3 |factor4 | factor5
---|---|---|---|---|---
1 |0.192389|0.015152|-0.184673|-0.184673|-0.184673
2 |-0.300448|0.01182|0.273232|-0.184673|-0.184673
3 |0.165049|-0.002542|-0.101841|-0.184673|-0.184673

#### 5.通过API订阅和处理因子数据

在上述示例中，因子的计算结果保存到流数据表中，当第三方程序需要实时获取因子的计算结果并进行后续处理或者显示时，可以通过流数据API来订阅结果表。以下代码展示了Java和Python使用API订阅流数据的例子。本示例中统一使用了本地端口20002来进行数据订阅。

##### 5.1 Java API订阅例子

* Java 订阅因子表

```java
import com.xxdb.streaming.client.ThreadedClient;
import java.io.IOException;

public class main {
    public static void main(String[] args) throws IOException {
        ThreadedClient client = new ThreadedClient(20002);
        FactorHandler handler = new FactorHandler();
        client.subscribe("localhost", 8848, "factor", "consume_factor", handler,-1);
    }
}
```

* 订阅处理FactorHandler代码 
```java

import com.xxdb.data.BasicDouble;
import com.xxdb.data.BasicString;
import com.xxdb.data.BasicTime;
import com.xxdb.streaming.client.IMessage;
import com.xxdb.streaming.client.MessageHandler;

public class FactorHandler  implements MessageHandler {
    @Override
    public void doEvent(IMessage msg) {

        BasicString symbol = msg.getValue("symbol");
        BasicTime time = msg.getValue("time");
        BasicDouble factor1 = msg.getValue("factor1");
        BasicDouble factor2 = msg.getValue("factor2");
        System.out.println(symbol.getString() + " | " + time.getString() + " | " + factor1.getString() + " | " + factor2.getString());
    }
}
```

##### 5.2 Python API订阅例子

* Python订阅代码
```python
import dolphindb as ddb
import numpy as np
s = ddb.session()
s.enableStreaming(20002)

def myHandler(lst):
    print(lst)

s.subscribe("localhost", 8848, myHandler, "factor", "sub_factor", -1,False, None)
```

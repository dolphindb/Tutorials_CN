### 实现步骤

#### 1. 模拟产生高频数据

模拟产生100只股票的数据。symbol从1到100，总共100,000,000条记录，22列：symbol, time, ap1..ap5, bp1..bp5, av1..av5, bv1..bv5。 限制：ap1<ap2<ap3<ap4<ap5, bp1>bp2>bp3>bp4>bp5, 均为小数点后两位；av1-av5, bv1-bv5均为整数，无大小限制。 

* 创建流数据表tick，以存放高频数据。
```
def createTable(){
	share(streamTable(1000:0, `symbol`time`ap1`ap2`ap3`ap4`ap5`bp1`bp2`bp3`bp4`bp5`av1`av2`av3`av4`av5`bv1`bv2`bv3`bv4`bv5, [SYMBOL,TIME,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE]), `tick)
}
createTable()
```

* 定义generateData函数，在每个时间戳生成1-10笔随机数据，并写入tick表。此函数将在任务提交时执行。
```
def generateData(times){
	for(j in 0..times){
		batchSize = rand(1..10,1)[0]
		for(i in 0..batchSize){
			sym = rand(symbol(string(1..100)), batchSize)
			tim = take(time(now()),batchSize)
			ap1= rand(100..150, batchSize)/100.0
			ap2= rand(151..200, batchSize)/100.0
			ap3= rand(201..250, batchSize)/100.0
			ap4= rand(251..300, batchSize)/100.0
			ap5= rand(301..350, batchSize)/100.0
			bp1= rand(100..150, batchSize)/100.0
			bp2= rand(151..200, batchSize)/100.0
			bp3= rand(201..250, batchSize)/100.0
			bp4= rand(251..300, batchSize)/100.0
			bp5= rand(301..350, batchSize)/100.0
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
			data = table(sym as symbol,tim as time,ap1,ap2,ap3,ap4,ap5,bp1,bp2,bp3,bp4,bp5,av1,av2,av3,av4,av5,bv1,bv2,bv3,bv4,bv5)
			objByName(`tick).tableInsert(data)
		}
	}
}
```

#### 2. DolphinDB订阅高频数据并实时计算2个因子

本例中，需要计算以下两个因子：
```
factor1 = (av1-bv1)/(av1+bv1)
factor2 = (av1+av2+av3+av4+av5-bv1-bv2-bv3-bv4-bv5)/(av1+av2+av3+av4+av5+bv1+bv2+bv3+bv4+bv5)
```

* 创建因子表factor，以存放因子计算结果。
```
def createFactorTable(){
	t=streamTable(100:0, `symbol`time`factor1`factor2, [SYMBOL,TIME,DOUBLE,DOUBLE]);
	share(t,`factor)
}
createFactorTable()
```
* 定义函数factorHandler，以计算因子。
```
def factorHandler(mutable dst, msg){
	data = select symbol, time(now()) as time, (av1-bv1)/(av1+bv1) as factor1, (av1+av2+av3+av4+av5-bv1-bv2-bv3-bv4-bv5)/(av1+av2+av3+av4+av5+bv1+bv2+bv3+bv4+bv5) as factor2 from msg
	dst.tableInsert(data)
}
```
* 订阅高频数据，并实时计算因子。
```
subscribeTable(tableName=`tick, actionName=`createFactor, handler=factorHandler{objByName(`factor)}, msgAsTable=true)
```

* 提交产生模拟数据的任务，数据生成后即写入流数据表tick中，并触发流数据计算任务。计算结果写入factor表中。
```
submitJob("gendata", "generate data", generateData, 5000000)
```

#### 3.观察结果
```
//观察最新计算的10条记录
select top 10 * from objByName(`factor) order by time desc
```
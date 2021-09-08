# 响应式状态引擎实现传感器数据状态变化检测

DolphinDB中的响应式状态引擎`ReactiveStateEngine`拥有非常强大的功能。在另一篇文章中，我们曾介绍过在金融领域，如何使用该引擎简单、高效、快捷地实现金融高频因子的流批统一计算。在物联网场景中，我们同样可以发挥响应式状态引擎的优势，在准确精简的同时，有效提升性能。

本篇将以传感器数据状态变化检测这一案例，通过响应式状态引擎`ReactiveStateEngine`与自定义函数方式的对比，来说明响应状态式引擎的实现原理、使用方法以及它的优势。

在生产环境中，我们会有非常多的测点，其中也包括各个机器的状态，大致的数据会是下面这样：

| id   | ts                  | value    |
| ---- | ------------------- | -------- |
| 10   | 2021.01.25T14:00:01 | run      |
| 11   | 2021.01.25T14:00:02 | run      |
| 16   | 2021.01.25T14:00:03 | alarm    |
| 16   | 2021.01.25T14:00:04 | stand_by |
| 14   | 2021.01.25T14:00:05 | run      |
| 11   | 2021.01.25T14:00:06 | stand_by |
| 8    | 2021.01.25T14:00:07 | alarm    |
| 20   | 2021.01.25T14:00:08 | stand_by |
| 18   | 2021.01.25T14:00:09 | stand_by |
| 12   | 2021.01.25T14:00:10 | alarm    |
| 9    | 2021.01.25T14:00:11 | run      |
| 8    | 2021.01.25T14:00:12 | alarm    |
| 3    | 2021.01.25T14:00:13 | off_line |

通常我们需要检测各个机器的状态变化。传统的方式是采用自定义的方式来进行过滤输出，而DolphinDB提供了更为强大的响应式状态引擎`ReactiveStateEngine`。下面我们进行对比。

## 1. 响应式状态引擎

我们先用DolphinDB中的响应式状态引擎`ReactiveStateEngine`来实现传感器数据状态变化的检测。步骤如下：

#### 1.1 建流表

这里先建一个简化的流表来模拟。

```
data_st =  streamTable(10000:0, `id`ts`value,[INT,DATETIME,SYMBOL])
```
#### 1.2 开启共享以及持久化

一般在生产环境中，我们建议开启持久化。具体`enableTableShareAndPersistence`这个函数的具体参数配置，可以在用户手册中查询。

```
enableTableShareAndPersistence(table=data_st , tableName=`machine_SheBei, asynWrite=false, compress=true, cacheSize=1000000)
```
开启共享以及持久化之后，我们可以在Shared Table文件夹下面看到一个名为"machine_SheBei"的共享表。目前表中还没有数据。

#### 1.3 定义订阅时的过滤列

指定流数据表的过滤列：

```
setStreamTableFilterColumn(machine_SheBei,`value)
```

这个函数是配合之后 `subscribeTable` 函数的 `filter` 参数一起使用。`filter` 是一个向量，`streamTable` 的 columnName 列在 `filter` 中的数据才会发布到订阅端，不在 `filter` 中的数据不会发布。一个流数据表只能指定一个过滤列。

#### 1.4 定义输出表

定义响应式状态引擎参数`outputTable`的输出表结构：

```
share streamTable(10000:0,`faultId`time`statusCode,[INT,DATETIME,INT]) as resultTable
```

#### 1.5 创建响应式状态引擎

接下来就可以创建响应式状态引擎了。
`name` 表示响应式状态引擎的名称，是其在一个数据节点上的唯一标识。可包含字母，数字和下划线，但必须以字母开头。这里我们定义这个引擎的名字为“reactive_engine”。
`metrics` 是以元代码的形式表示计算公式。这里我们调整了“ts”列的数据结构，以及“value”列的数据值。
`dummyTable` 是一个表对象，该表的唯一作用是提供流数据中每一列的数据类型。该表的schema必须与订阅的流数据表相同。
`outputTable` 是结果的输出表。即最后输出的结果可以在我们之前创建的“resultTable”中查看到。
`keyColumn` 是一个字符串标量或向量，表示分组列名。在这里即以每个id为一组进行计算。
`filter` 是以元代码的形式表示过滤条件。这里我们会把状态值有变化的数据过滤出来输出到结果表中。


`createReactiveStateEngine`这个函数的其他各个参数详见用户手册。
为了方便起见，我们用`dict`函数将原数据中"value"状态"run""alarm""stand_by""off_line"赋值。

```

dic=dict(`run`alarm`stand_by`off_line, [1, 0 ,2, 3])

engine = createReactiveStateEngine(name=`reactive_engine, metrics=<[datetime(ts), dic[value]]>, dummyTable=data_st,outputTable= resultTable,keyColumn= "id",filter=<dic[value]!=prev(dic[value]) && prev(dic[value])!=NULL>)
```

#### 1.6 订阅

通过`subscribeTable`函数订阅流数据，每次有新数据流入就会按指定规则触发append!{engine}，将流数据持续输入聚合引擎（指定的数据表中）。

```
subscribeTable(tableName=`machine_SheBei, actionName="ReactiveStateEngine_SheBei", offset=0, handler=append!{engine}, msgAsTable=true,filter=`run`alarm`stand_by`off_line)
```
#### 1.7 写入模拟数据

```
n=10000
data = table(rand(1..20,n) as id, 2021.01.25T14:00:00+1..n as ts, rand(`run`alarm`stand_by`off_line,n) as value)

tableInsert(machine_SheBei, data)
```
写入之后，我们可以看到“resultTable”中看到状态变化的所有数据。

##### 完整代码如下：
```
//1.建流表
data_st =  streamTable(10000:0, `id`ts`value,[INT,DATETIME,SYMBOL])
//2.开启共享以及持久化
enableTableShareAndPersistence(table=data_st , tableName=`machine_SheBei, asynWrite=false, compress=true, cacheSize=1000000)
go
//3.定义订阅时的过滤列
setStreamTableFilterColumn(machine_SheBei,`value)

//4.输出表
share streamTable(10000:0,`faultId`time`statusCode,[INT,DATETIME,INT]) as  resultTable

dic=dict(`run`alarm`stand_by`off_line, [1, 0 ,2, 3])

//5.创建响应式状态引擎
engine = createReactiveStateEngine(name=`reactive_engine, metrics=<[datetime(ts), dic[value]]>, dummyTable=data_st,outputTable= resultTable,keyColumn= "id",filter=<dic[value]!=prev(dic[value]) && prev(dic[value])!=NULL>)

//6.订阅
subscribeTable(tableName=`machine_SheBei, actionName="ReactiveStateEngine_SheBei", offset=0, handler=append!{engine}, msgAsTable=true,filter=`run`alarm`stand_by`off_line)


//7.模拟数据
n=10000
data = table(rand(1..20,n) as id, 2021.01.25T14:00:00+1..n as ts, rand(`run`alarm`stand_by`off_line,n) as value)

tableInsert(machine_SheBei, data)

//8.取消
dropAggregator(`reactive_engine)
engine1=NULL
unsubscribeTable(tableName=`machine_SheBei, actionName="ReactiveStateEngine_SheBei")
```


## 2. 自定义函数

#### 2.1 建流表、开启共享以及持久化

首先仍旧是建流表开启共享以及持久化：
```
data_st =  streamTable(10000:0, `id`ts`value,[INT,DATETIME,SYMBOL])

enableTableShareAndPersistence(table=data_st , tableName=`machine_SheBei, asynWrite=false, compress=true, cacheSize=1000000)
```

#### 2.2 建状态变化输出表 machine_status_output; 含ID，现在状态，现在时间
```
share streamTable(10000:0,`faultId`time`statusCode,[INT,DATETIME,INT]) as  machine_status_output
```

#### 2.3 创建键值内存表

```
machine_kt=keyedTable(`id,1500:0,`id`ts`status,[INT,DATETIME,INT])
```

#### 2.4 自定义消息处理函数
不用响应式状态引擎的话，我们需要自己自定义消息处理函数：
```
def checkZhongDuan(mutable keyedTable,mutable outputTable ,msg ){
	// run=1 alarm=0  stand_by=2 off_line=3 
            //使用id查看是否存在记录
            //如果不存在记录，使用append添加记录
            	for(i  in 0..(size(msg)-1)){
            		//查询键值内存表中是否存在id
            		dic=dict(`run`alarm`stand_by`off_line, (1, 0 ,2, 3));
            	 	t=select * from keyedTable where id=msg[`id][i]
            	 	time=msg[`ts][i];
            	 	status1=dic find msg[`value][i]
            	 	if (t.size()==0) { //如果id不存在，则将新数据插入keyedTable
            	 		if (status1 != NULL ) {
	            	 		new=table(msg[`id][i] as id,time as ts,status1 as status)
	            	 		keyedTable.append!(new)
            	 		}            	 		
            	 	}else {//如果id存在，比较status
            	 		if (status1 != NULL ) {
	            	 	  	if ( t[`status][0] !=status1){//状态不一致，更改tag对应status 和ts
	            	 			status_change=table(msg[`id][i] as id,time as ts,status1 as status)
	            	 			keyedTable.append!(status_change)
	            	 			outputTable.append!(status_change)
	            	 		}
            	 		}
            	 		//如果一致，不做任何处理
            	 	} 		
            	}			
	}
```

#### 2.5 订阅

```
subscribeTable(tableName="machine_SheBei", actionName="check_machine_SheBei", offset=getPersistenceMeta(machine_SheBei).diskOffset,handler=checkZhongDuan{machine_kt, machine_status_output}, msgAsTable=true,batchSize=500,throttle=5,hash=1)
```

#### 2.6 写入模拟数据

```
n=10000
data = table(rand(1..20,n) as id, 2021.01.25T14:00:00+1..n as ts, rand(`run`alarm`stand_by`off_line,n) as value)

tableInsert(machine_SheBei, data)
```
写入之后，我们可以看到“machine_status_output”中看到状态变化的所有数据。

##### 完整代码如下：
```
//1. 建流表、开启共享以及持久化
data_st =  streamTable(10000:0, `id`ts`value,[INT,DATETIME,SYMBOL])
enableTableShareAndPersistence(table=data_st , tableName=`machine_SheBei, asynWrite=false, compress=true, cacheSize=1000000)

//2. 建状态变化输出表 machine_status_output
share streamTable(10000:0,`faultId`time`statusCode,[INT,DATETIME,INT]) as  machine_status_output

//3.创建键值内存表
machine_kt=keyedTable(`id,1500:0,`id`ts`status,[INT,DATETIME,INT])

//4. 自定义消息处理函数
def checkZhongDuan(mutable keyedTable,mutable outputTable ,msg ){
	// run=1 alarm=0  stand_by=2 off_line=3 
            //使用id查看是否存在记录
            //如果不存在记录，使用append添加记录
            	for(i  in 0..(size(msg)-1)){
            		//查询键值内存表中是否存在id
            		dic=dict(`run`alarm`stand_by`off_line, (1, 0 ,2, 3));
            	 	t=select * from keyedTable where id=msg[`id][i]
            	 	time=msg[`ts][i];
            	 	status1=dic find msg[`value][i]
            	 	if (t.size()==0) { //如果id不存在，则将新数据插入keyedTable
            	 		if (status1 != NULL ) {
	            	 		new=table(msg[`id][i] as id,time as ts,status1 as status)
	            	 		keyedTable.append!(new)
            	 		}            	 		
            	 	}else {//如果id存在，比较status
            	 		if (status1 != NULL ) {
	            	 	  	if ( t[`status][0] !=status1){//状态不一致，更改tag对应status 和ts
	            	 			status_change=table(msg[`id][i] as id,time as ts,status1 as status)
	            	 			keyedTable.append!(status_change)
	            	 			outputTable.append!(status_change)
	            	 		}
            	 		}
            	 		//如果一致，不做任何处理
            	 	} 		
            	}			
	}

//5.订阅
subscribeTable(tableName="machine_SheBei", actionName="check_machine_SheBei", offset=getPersistenceMeta(machine_SheBei).diskOffset,handler=checkZhongDuan{machine_kt, machine_status_output}, msgAsTable=true,batchSize=500,throttle=5,hash=1)


//6. 模拟数据
n=10000
data = table(rand(1..20,n) as id, 2021.01.25T14:00:00+1..n as ts, rand(`run`alarm`stand_by`off_line,n) as value)

tableInsert(machine_SheBei, data)

//7. 取消
dropAggregator(`reactive_engine2)
engine2=NULL
unsubscribeTable(tableName=`machine_SheBei, actionName="check_machine_SheBei")
dropStreamTable("machine_SheBei")

```


## 3. 性能对比

#### 3.1 代码长度更简洁
不难看出，使用响应式状态引擎的代码长度远小于自定义函数的实现。自定义函数中，我们需要多层写入和判断，代码的可读性也相对较差。

#### 3.1 运算速度更快
我们来比较一下两者连跑10次的时间：

```
//1. 响应式状态引擎实现：
timer(10) getStreamEngine(`reactive_engine).append!(data)
//10次总共用时260 ms


//2. 自定义函数实现：
timer(10) checkZhongDuan(machine_kt, machine_status_output,machine_SheBei)
/10次总共用时3213 ms
```
使用响应式状态引擎的效率是自定义函数实现的十倍。

## 4. 总结

无论从代码角度还是从运算效率角度，响应式状态引擎都能更高效的满足需求。在物联网场景下，响应式状态引擎的运用更有优势。


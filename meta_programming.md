# DolphinDB元编程教程

元编程是指使用程序代码来生成可以动态运行的程序代码。元编程的目的一般是延迟执行代码或动态创建代码。

## 1. DolphinDB实现元编程的方法

DolphinDB支持使用元编程来动态创建表达式，包括函数调用的表达式、SQL查询表达式等。DolphinDB有两种实现元编程的方法：

（1）使用一对尖括号<>来表示需要延迟执行的动态代码。例如，

```
a = <1 + 2 * 3>
typestr(a);
CODE
//a是元代码，它的数据类型是CODE

eval(a);
7
//eval函数用于执行元代码
```

（2）使用函数来创建各种表达式。常用的元编程函数包括expr, parseExpr, partial, sqlCol, sqlColAlias, sql, eval, makeCall. 下面介绍这几个函数的用法。

- [expr](https://www.dolphindb.cn/cn/help/expr.html)函数根据输入的对象、运算符或其他元代码生成元代码。例如：

```python
a = expr(1, +, 2, *, 3)
a.typestr();
CODE

a;
< 1 + 2 * 3 >
```

- [parseExpr](http://www.dolphindb.cn/cn/help/parseExpr.html)函数可以把字符串转换为元代码。例如：

```python
parseExpr("1+2")

< 1 + 2 >
```

- [partial](http://www.dolphindb.cn/cn/help/partital.html)函数可以固定一个函数的部分参数，产生一个参数较少的函数。例如：

```
partial(add,1)(2)
3

def f(a,b):a pow b
g=partial(f, 2)
g(3)

8
```

- [sqlCol](https://www.dolphindb.cn/cn/help/sqlCol.html), [sqlColAlias](https://www.dolphindb.cn/cn/help/sqlColAlias.html)和[sql](https://www.dolphindb.cn/cn/help/sql1.html)函数用于动态生成SQL表达式。sqlCol函数可以将列名转换成表达式，sqlColAlias常用于生成计算列的元代码，sql函数可以动态地生成SQL语句。

```python
sym = take(`GE,6) join take(`MSFT,6) join take(`F,6)
date=take(take(2017.01.03,2) join take(2017.01.04,4), 18)
PRC=31.82 31.69 31.92 31.8  31.75 31.76 63.12 62.58 63.12 62.77 61.86 62.3 12.46 12.59 13.24 13.41 13.36 13.17
vol=2300 3500 3700 2100 1200 4600 8800 7800 6400 4200 2300 6800 4200 5600 8900 2300 6300 9600
t1 = table(sym, date, PRC, vol);

sql(sqlCol("*"),t1)
< select * from t1 >

sql(sqlCol("*"),t1,[<sym="MSFT">,<PRC>=5000>])
< select * from t1 where sym == "MSFT",PRC >= 5000 >

sql(sqlColAlias(<avg(vol)>,"avg_vol"),t1,<sym="MSFT">,sqlCol("date"))
< select avg(vol) as avg_vol from t1 where sym == "MSFT" group by date >

sql(sqlColAlias(<avg(vol)>,"avg_vol"),t1,<sym="MSFT">,sqlCol("date"),,,,<avg(vol)>3000>)
< select avg(vol) as avg_vol from t1 where sym == "MSFT" group by date having avg(vol) > 3000 >

sql(sqlColAlias(<avg(vol)>,"avg_vol"),t1,<sym="MSFT">,sqlCol("date"),0)
< select avg(vol) as avg_vol from t1 where sym == "MSFT" context by date >

sql(sqlColAlias(<avg(vol)>,"avg_vol"),t1,<sym="MSFT">,sqlCol("date"),0,sqlCol("avg_vol"),0)
< select avg(vol) as avg_vol from t1 where sym == "MSFT" context by date csort avg_vol desc >

sql(sqlCol("*"),t1,,,,,,,sqlCol(`vol),0,5)
< select top 5 * from t1 order by vol desc >
```

- [eval](https://www.dolphindb.cn/cn/help/eval.html)函数可以执行元代码。例如：

```python
a = <1 + 2 * 3>
eval(a);
7

sql(sqlColAlias(<avg(vol)>,"avg_vol"),t1,,sqlCol(["sym","date"])).eval();
sym  date       avg_vol
---- ---------- -------
F    2017.01.03 4900   
F    2017.01.04 6775   
GE   2017.01.03 2900   
GE   2017.01.04 2900   
MSFT 2017.01.03 8300   
MSFT 2017.01.04 4925   
//这里使用的t1是第（2）部分的t1
```

- [makeCall](https://www.dolphindb.cn/cn/help/makeCall.html)函数可以根据指定的函数和输入参数生成元代码。例如，查询表t1时，把date列输出为字符串，并以类似于03/01/2017的形式显示。

```python
sql([sqlColAlias(makeCall(temporalFormat,sqlCol(`date),"dd/MM/yyyy"),"date"),sqlCol(`sym),sqlCol(`PRC),sqlCol(`vol)],t1)
< select temporalFormat(date, "dd/MM/yyyy") as date,sym,PRC,vol from t1 >
```

## 2.DolphinDB元编程应用

### 2.1 更新分区内存表

分区内存表的更新、删除等操作不仅可以通过SQL语句完成，也可以通过元编程完成。
创建分区内存表：

```python
n=1000000
sym=rand(`IBM`MSFT`GOOG`FB`IBM`MSFT,n)
date=rand(2018.01.02 2018.01.02 2018.01.02 2018.01.03 2018.01.03 2018.01.03,n)
price=rand(1000.0,n)
qty=rand(10000,n)
t=table(sym,date,price,qty)

db=database("",VALUE,`IBM`MSFT`GOOG`FB`IBM`MSFT)
trades=db.createPartitionedTable(t,`trades,`sym).append!(t)
```

#### 2.1.1 更新数据

例如，更新股票代码为IBM的交易数量：

```
trades[`qty,<sym=`IBM>]=<qty+100>
//等价于update trades set qty=qty+100 where sym=`IBM
```

#### 2.1.2 新增一个列

例如，添加一个新的列volume，用于保存交易量：

```python
trades[`volume]=<price*qty>
//等价于update trades set volume=price*qty
```

#### 2.1.3 删除数据

例如，删除qty为0的数据：

```python
trades.erase!(<qty=0>)
//等价于delete from trades where qty=0
```

#### 2.1.4 动态生成过滤条件并更新数据

本例使用了以下数据表。

```python
ind1=rand(100,10)
ind2=rand(100,10)
ind3=rand(100,10)
ind4=rand(100,10)
ind5=rand(100,10)
ind6=rand(100,10)
ind7=rand(100,10)
ind8=rand(100,10)
ind9=rand(100,10)
ind10=rand(100,10)
indNum=1..10
t=table(ind1,ind2,ind3,ind4,ind5,ind6,ind7,ind8,ind9,ind10,indNum)
```

我们需要对数据表进行更新操作，SQL语句如下：

```sql
update t set ind1=1 where indNum=1
update t set ind2=1 where indNum=2
update t set ind3=1 where indNum=3
update t set ind4=1 where indNum=4
update t set ind5=1 where indNum=5
update t set ind6=1 where indNum=6
update t set ind7=1 where indNum=7
update t set ind8=1 where indNum=8
update t set ind9=1 where indNum=9
update t set ind10=1 where indNum=10
```

如果数据表的列数较多，需要手工编写非常多的SQL语句。观察以上语句可以发现，列名和过滤条件是有一定关系的。使用元编程可以非常方便地完成以上操作。

```python
for(i in 1..10){
	t["ind"+i,<indNum=i>]=1
}
```

### 2.2 在内置函数中使用元编程

DolphinDB的一些内置函数会使用到元编程。

#### 2.2.1 窗口连接

在窗口连接（window join）中，需要为右表的窗口数据集指定一个或多个聚合函数以及这些函数运行时需要的参数。由于问题的描述和执行在两个不同的阶段，我们采用元编程来实现延后执行。

```
t = table(take(`ibm, 3) as sym, 10:01:01 10:01:04 10:01:07 as time, 100 101 105 as price)
q = table(take(`ibm, 8) as sym, 10:01:01+ 0..7 as time, 101 103 103 104 104 107 108 107 as ask, 98 99 102 103 103 104 106 106 as bid)
wj(t, q, -2 : 1, < [max(ask), min(bid), avg((bid+ask)*0.5) as avg_mid]>, `time)

sym time     price max_ask min_bid avg_mid
--- -------- ----- ------- ------- -------
ibm 10:01:01 100   103     98      100.25
ibm 10:01:04 101   104     99      102.625
ibm 10:01:07 105   108     103     105.625

```

#### 2.2.2 流计算引擎

DolphinDB有三种类型的流计算引擎：时间序列聚合引擎（createTimeSeriesAggregator）、横截面引擎（createCrossSectionalAggregator）和异常检测引擎（createAnomalyDetectionEngine）。在使用这些流计算引擎时，需要为数据窗口中的数据集指定聚合函数或表达式以及它们运行时所需的参数。这种情况下，我们采用元编程来表示聚合函数或表达式以及它们所需的参数。以时间序列聚合引擎的应用为例：

```
share streamTable(1000:0, `time`sym`qty, [DATETIME, SYMBOL, INT]) as trades
output1 = table(10000:0, `time`sym`sumQty, [DATETIME, SYMBOL, INT])
agg1 = createTimeSeriesAggregator("agg1",60, 60, <[sum(qty)]>, trades, output1, `time, false,`sym, 50,,false)
subscribeTable(, "trades", "agg1",  0, append!{agg1}, true)

insert into trades values(2018.10.08T01:01:01,`A,10)
insert into trades values(2018.10.08T01:01:02,`B,26)
insert into trades values(2018.10.08T01:01:10,`B,14)
insert into trades values(2018.10.08T01:01:12,`A,28)
insert into trades values(2018.10.08T01:02:10,`A,15)
insert into trades values(2018.10.08T01:02:12,`B,9)
insert into trades values(2018.10.08T01:02:30,`A,10)
insert into trades values(2018.10.08T01:04:02,`A,29)
insert into trades values(2018.10.08T01:04:04,`B,32)
insert into trades values(2018.10.08T01:04:05,`B,23)

select * from output1

time                sym sumQty
------------------- --- ------
2018.10.08T01:02:00 A   38    
2018.10.08T01:03:00 A   25    
2018.10.08T01:02:00 B   40    
2018.10.08T01:03:00 B   9  
```

### 2.3 定制报表

元编程可以用于定制报表。下例定义了一个用于生成报表的自定义函数，用户只需要输入数据表、字段名称以及字段相应的格式字符串即可。

```python
def generateReport(tbl, colNames, colFormat, filter){
	colCount = colNames.size()
	colDefs = array(ANY, colCount)
	for(i in 0:colCount){
		if(colFormat[i] == "") 
			colDefs[i] = sqlCol(colNames[i])
		else
			colDefs[i] = sqlCol(colNames[i], format{,colFormat[i]})
	}
	return sql(colDefs, tbl, filter).eval()
}
```

创建模拟的历史数据库：

```python
if(existsDatabase("dfs://historical_db")){
	dropDatabase("dfs://historical_db")
}
n=5000000
dates=2012.09.01..2012.09.30
syms=symbol(`IBM`MSFT`GOOG`FB`AAPL)
t=table(rand(dates,n) as date, rand(syms,n) as sym, rand(200.0,n) as price, rand(1000..2000,n) as qty)

db1=database("",VALUE,dates)
db2=database("",VALUE,syms)
db=database("dfs://historical_db",COMPO,[db1,db2])
stock=db.createPartitionedTable(t,`stock,`date`sym).append!(t)
```

选择2012年9月1日股票代码为IBM的数据生成报表：

```python
generateReport(stock,`date`sym`price`qty,["MM/dd/yyyy","","###.00","#,###"],<date=2012.09.01 and sym=`IBM >)
date       sym price  qty  
---------- --- ------ -----
09/01/2012 IBM 90.97  1,679
09/01/2012 IBM 22.36  1,098
09/01/2012 IBM 133.42 1,404
09/01/2012 IBM 182.08 1,002
09/01/2012 IBM 144.67 1,468
09/01/2012 IBM 6.59   1,256
09/01/2012 IBM 73.09  1,149
09/01/2012 IBM 83.35  1,415
09/01/2012 IBM 93.13  1,006
09/01/2012 IBM 88.05  1,406
...
```

上面的语句等价于以下SQL语句：

```sql
select format(date,"MM/dd/yyyy") as date, sym, format(price,"###.00") as price, format(qty,"#,###") as qty  from stock where date=2012.09.01 and sym=`IBM
```

### 2.4 物联网中动态生成计算指标

在物联网的实时流计算中，数据源包含tag, timestamp和value三个字段。现在需要对输入的原始数据进行实时的指标计算。由于每次收到的原始数据的tag数量和种类有可能不同，并且每次计算的指标也可能不同，我们无法将计算指标固定下来，因此这种情况下我们可以采用元编程的方法。我们需要定义一个配置表，将计算的指标放到该表中，可以根据实际增加、删除或修改计算指标。每次实时计算时，从配置表中动态地读取需要计算的指标，并把计算的结果输出到另外一个表中。

以下是示例代码。pubTable是流数据的发布表。config表是存储计算指标的配置表，由于计算指标有可能每次都不相同，这里采用的是并发版本控制表（mvccTable）。subTable通过订阅pubTable，对流数据进行实时计算。

```python
t1=streamTable(1:0,`tag`value`time,[STRING,DOUBLE,DATETIME])
share t1 as pubTable

config = mvccTable(`index1`index2`index3`index4 as targetTag, ["tag1 + tag2", "sqrt(tag3)", "floor(tag4)", "abs(tag5)"] as formular)

subTable = streamTable(100:0, `targetTag`value, [STRING, FLOAT])

def calculateTag(mutable subTable,config,msg){
	pmsg = select value from msg pivot by time, tag
	for(row in config){
		try{
			insert into subTable values(row.targetTag, sql(sqlColAlias(parseExpr(row.formular), "value"), pmsg).eval().value)
		}
			catch(ex){print ex}
	}
}

subscribeTable(,`pubTable,`calculateTag,-1,calculateTag{subTable,config},true)

//模拟写入数据
tmp = table(`tag1`tag2`tag3`tag4 as tag, 1.2 1.3 1.4 1.5 as value, take(2019.01.01T12:00:00, 4) as time)
pubTable.append!(tmp)

select * from subTable

targetTag value   
--------- --------
index1    2.5     
index2    1.183216
index3    1       

```

### 2.5 执行一组查询，合并查询结果

在数据分析中，有时我们需要对同一个数据集执行一组相关的查询，并将查询结果合并展示出来。如果每次都手动编写全部SQL语句，工作量大，并且扩展性差。通过元编程动态生成SQL可以解决这个问题。

本例使用的数据集结构如下（以第一行为例）：

mt       |vn       |bc |cc  |stt |vt |gn |bk   |sc |vas |pm |dls        |dt         |ts     |val   |vol  
-------- |-------- |-- |--- |--- |-- |-- |---- |-- |--- |-- |---------- |---------- |------ |----- |-----
52354955 |50982208 |25 |814 |11  |2  |1  |4194 |0  |0   |0  |2020.02.05 |2020.02.05 |153234 |5.374 |18600                  

我们需要对每天的数据都执行一组相关的查询。比如：

```sql
select * from t where vn=50982208,bc=25,cc=814,stt=11,vt=2, dsl=2020.02.05, mt<52355979 order by mt desc limit 1
select * from t where vn=50982208,bc=25,cc=814,stt=12,vt=2, dsl=2020.02.05, mt<52355979 order by mt desc limit 1
select * from t where vn=51180116,bc=25,cc=814,stt=12,vt=2, dsl=2020.02.05, mt<52354979 order by mt desc limit 1
select * from t where vn=41774759,bc=1180,cc=333,stt=3,vt=116, dsl=2020.02.05, mt<52355979 order by mt desc limit 1
```

可以观察到，这一组查询中，过滤条件包含的列和排序列都相同，并且都是取排序后的第一行记录，还有部分过滤条件的值相同。为此，我们编写了自定义函数bundleQuery：

```python
def bundleQuery(tbl, dt, dtColName, mt, mtColName, filterColValues, filterColNames){
	cnt = filterColValues[0].size()
	filterColCnt =filterColValues.size()
	orderByCol = sqlCol(mtColName)
	selCol = sqlCol("*")
	filters = array(ANY, filterColCnt + 2)
	filters[filterColCnt] = expr(sqlCol(dtColName), ==, dt)
	filters[filterColCnt+1] = expr(sqlCol(mtColName), <, mt)
	
	queries = array(ANY, cnt)
	for(i in 0:cnt)	{
		for(j in 0:filterColCnt){
			filters[j] = expr(sqlCol(filterColNames[j]), ==, filterColValues[j][i])
		}
		queries.append!(sql(select=selCol, from=tbl, where=filters, orderBy=orderByCol, ascOrder=false, limit=1))
	}
	return loop(eval, queries).unionAll(false)
}
```

bundleQuery中各个参数的含义如下：

- tbl是数据表
- dt是过滤条件中日期的值
- dtColName是过滤条件中日期列的名称
- mt是过滤条件中mt的值
- mtColName是过滤条件中mt列的名称，以及排序列的名称
- filterColValues是其他过滤条件中的值，用元组表示，其中的每个向量表示一个过滤条件，每个向量中的元素表示该过滤条件的值
- filterColNames是其他过滤条件中的列名，用向量表示

上面一组SQL语句，相当于执行以下代码：

```
dt = 2020.02.05 
dtColName = "dls" 
mt = 52355979 
mtColName = "mt"
colNames = `vn`bc`cc`stt`vt
colValues = [50982208 50982208 51180116 41774759, 25 25 25 1180, 814 814 814 333, 11 12 12 3, 2 2 2 116]

bundleQuery(t, dt, dtColName, mt, mtColName, colValues, colNames)
```

我们可以执行以下脚本把bundleQuery函数定义为函数视图，这样在集群的任何节点或者重启系统之后，都可以直接使用该函数。

```
//please login as admin first
addFunctionView(bundleQuery)
```

## 3.小结

DolphinDB的元编程功能强大，使用简单，能够极大地提高程序开发效率。



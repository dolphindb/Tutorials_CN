# 使用DolphinDB进行大数据分析——淘宝用户行为分析

DolphinDB database 是新一代的高性能分布式时序数据库，同时具有丰富的数据分析和分布式计算功能。本教程使用DolphinDB对淘宝APP的用户行为数据进行分析，进一步分析业务问题。

数据来源：[https://tianchi.aliyun.com/dataset/dataDetail?dataId=649&userId=1](https://tianchi.aliyun.com/dataset/dataDetail?dataId=649&userId=1)

本教程中，我们已经把数据导入到DolphinDB的分布式数据库dfs://user_behavior 中。它包含一张表user，保存了2017年11月25日到2017年12月3日之间将近一百万淘宝APP用户的行为记录。我们采用组合分区方式，第一层按照日期分区，每天一个分区，第二层按照userID进行哈希分区，一共划分为180个分区。user表的结果如下所示：

|列名      |数据类型      |含义            |
|----------|-------------|----------------|
|userID    |INT          |用户ID          |
|itemID    |INT          |商品ID          |
|categoryID|INT          |商品所属类目ID   |
|behavior  |SYMBOL       |用户行为，包含四种类型：pv、buy、cart和fav|
behaveTime |DATETIME     |行为发生的时间戳  |

各种用户行为类型的含义如下：

- pv：浏览商品详情页
- buy：商品购买
- cart：将商品加入购物车
- fav：收藏商品

## 1. 下载docker部署包

本教程已经把DolphinDB以及使用到的数据封装到docker容器中。使用前确保docker环境已经部署好。docker安装教程请参考[https://docs.docker.com/install/](https://docs.docker.com/install/)。从[http://www.dolphindb.cn/downloads/bigdata.tar.gz](http://www.dolphindb.cn/downloads/bigdata.tar.gz)下载部署包，到部署包所在目录执行以下代码。

解压部署包：

```bash
gunzip bigdata.tar.gz
```

导入容器快照作为镜像：
```bash
cat bigdata.tar | docker import - my/bigdata:v1
```

获取镜像my/bigdata:v1的ID:
```bash
docker images
```

启动容器（根据实际情况替换images id）

```bash
docker run -dt -p 8888:8848 --name test <image id> /bin/bash ./dolphindb/start.sh
```

在浏览器地址栏中输入本机IP地址:8888，如localhost:8888，进入DolphinDB Notebook。以下代码均可在DolphinDB Notebook中执行。

## 2. 用户行为分析

查看数据量

```python
login("admin","123456")
user=loadTable("dfs://user_behavior","user")
select count(*) from user
```

> 98914533

user表中一共有98,914,533条记录。

分析用户从浏览到最终购买商品整个过程的行为情况

```python
PV=exec count(*) from user where behavior="pv"
```
> 88596903

```python
UV=count(exec distinct userID from user)
```
> 987984

在这9天中，淘宝APP的页面访问量为88,596,903，独立访客为987,984。

上面使用到的[`exec`](https://www.dolphindb.cn/cn/help/exec.html)是DolphinDB独有的功能，它与[`select`](https://www.dolphindb.cn/cn/help/select.html)类似。两者的区别是，`select`语句总是返回一个表，`exec`选择一列时会返回一个向量，与聚合函数一起使用时会返回一个标量，与[`pivoy by`](https://www.dolphindb.cn/cn/help/pivotby.html)一起使用时会返回一个矩阵，方便后续对数据的计算。

统计只浏览一次页面的用户数量

```python
onceUserNum=count(select count(behavior) from user group by userID having count(behavior)=1)
```
> 92

```python
jumpRate=onceUserNum\UV*100
```
> 0.009312

只有92个用户只浏览过一个页面就离开了APP，占总用户数的0.0093%，几乎可以忽略不计，说明淘宝有足够的吸引力让用户停留在APP中。

统计各个用户行为的数量

```
behaviors=select count(*) as num from user group by behavior
```
|behavior |num   |  
|-------- |--------|
|pv       |88596903|
|buy      |1998976 |
|fav      |2852536 |
|cart     |5466118 |

计算从有浏览到有意向购买的转化率

将商品加入购物车和收藏商品都可以认为用户有意向购买。

统计有意向购买的用户行为数量

```python
fav_cart=exec sum(num) from behaviors where behavior="fav" or behavior="cart"
```
> 8318654

```python
intentRate=fav_cart\PV*100
```
> 9.389328

从浏览到有意向购买只有9.38%的转化率。

```python
buy=(exec num from behaviors where behavior="buy")[0]
```
> 1998976

```python
buyRate=buy\PV*100
```
> 2.256259

```python
intent_buy=buy\fav_cart*100
```
> 24.030041

从浏览到最终购买只有2.25%的转化率，从有意向购买到最终购买的转化率为24.03%，说明大部分用户用户会把中意的商品收藏或加入购物车，但不一定会立即购买。

对各种用户行为的独立访客进行统计

```python
userNums=select count(userID) as num from (select count(*) from user group by behavior,userID) group by behavior
```
|behavior |num   |
|-------- |------|
|buy      |670370|
|cart     |737393|
|fav      |388261|
|pv       |984080|

```python
pay_user_rate=(exec num from userNums where behavior="buy")[0]\UV*100
```
> 67.852313

这9天中，使用淘宝APP的付费用户占67.8%，说明大部分用户会在淘宝APP上购物。

统计每天各种用户行为的用户数量

```python
dailyUserNums=select sum(iif(behavior=="pv",1,0)) as pageView, sum(iif(behavior=="fav",1,0)) as favorite, sum(iif(behavior=="cart",1,0)) as shoppingCart, sum(iif(behavior=="buy",1,0)) as payment from user group by date(behaveTime) as date
```
|date       |pageView |favorite |shoppingCart |payment|
|---------- |-------- |-------- |------------ |-------|
|2017.11.25 |9435257  |305814   |569236       |201298 |
|2017.11.26 |9475590  |305722   |575420       |214314 |
|2017.11.27 |8966430  |289413   |539212       |218402 |
|2017.11.28 |8849194  |289431   |533807       |211757 |
|2017.11.29 |9241649  |299588   |554747       |223082 |
|2017.11.30 |9442000  |304428   |573032       |222238 |
|2017.12.01 |10002288 |314121   |642251       |212855 |
|2017.12.02 |12475206 |404821   |801367       |259555 |
|2017.12.03 |10709289 |339198   |677046       |235475 |

周五、周六和周日（2017.11.25、2017.11.26、2017.12.02、2017.12.03）淘宝APP的访问量明显增加。

[`iif`](https://www.dolphindb.cn/cn/help/iif.html)是DolphinDB的条件运算符，它的语法是iif(cond, trueResult, falseResult)，cond通常是布尔表达式，如果满足cond，则返回trueResult，如果不满足cond，则返回falseResult。

分别统计每天不同时间段下各种用户行为的数量。我们提供了以下两种方法：

第一种方法是分别统计各个时间段的数据，再把各个结果合并。例如，统计工作日2017.11.29（周三）不同时间段的用户行为数量。

```python
re1=select first(behaveTime) as time, sum(iif(behavior=="pv",1,0)) as pageView, sum(iif(behavior=="fav",1,0)) as favorite, sum(iif(behavior=="cart",1,0)) as shoppingCart, sum(iif(behavior=="buy",1,0)) as payment from user where behaveTime between 2017.11.29T00:00:00 : 2017.11.29T05:59:59

re2=select first(behaveTime) as time, sum(iif(behavior=="pv",1,0)) as pageView, sum(iif(behavior=="fav",1,0)) as favorite, sum(iif(behavior=="cart",1,0)) as shoppingCart, sum(iif(behavior=="buy",1,0)) as payment from user where behaveTime between 2017.11.29T06:00:00 : 2017.11.29T08:59:59

re3=select first(behaveTime) as time, sum(iif(behavior=="pv",1,0)) as pageView, sum(iif(behavior=="fav",1,0)) as favorite, sum(iif(behavior=="cart",1,0)) as shoppingCart, sum(iif(behavior=="buy",1,0)) as payment from user where behaveTime between 2017.11.29T09:00:00 : 2017.11.29T11:59:59

re4=select first(behaveTime) as time, sum(iif(behavior=="pv",1,0)) as pageView, sum(iif(behavior=="fav",1,0)) as favorite, sum(iif(behavior=="cart",1,0)) as shoppingCart, sum(iif(behavior=="buy",1,0)) as payment from user where behaveTime between 2017.11.29T12:00:00 : 2017.11.29T13:59:59

re5=select first(behaveTime) as time, sum(iif(behavior=="pv",1,0)) as pageView, sum(iif(behavior=="fav",1,0)) as favorite, sum(iif(behavior=="cart",1,0)) as shoppingCart, sum(iif(behavior=="buy",1,0)) as payment from user where behaveTime between 2017.11.29T14:00:00 : 2017.11.29T17:59:59

re6=select first(behaveTime) as time, sum(iif(behavior=="pv",1,0)) as pageView, sum(iif(behavior=="fav",1,0)) as favorite, sum(iif(behavior=="cart",1,0)) as shoppingCart, sum(iif(behavior=="buy",1,0)) as payment from user where behaveTime between 2017.11.29T18:00:00 : 2017.11.29T21:59:59

re7=select first(behaveTime) as time, sum(iif(behavior=="pv",1,0)) as pageView, sum(iif(behavior=="fav",1,0)) as favorite, sum(iif(behavior=="cart",1,0)) as shoppingCart, sum(iif(behavior=="buy",1,0)) as payment from user where behaveTime between 2017.11.29T22:00:00 : 2017.11.29T23:59:59

re=unionAll([re1,re2,re3,re4,re5,re6,re7],false)
```
|time                |pageView |favorite |shoppingCart |payment|
|------------------- |-------- |-------- |------------ |-------|
|2017.11.29T00:00:00 |2582410  |87924    |152219       |73304  |
|2017.11.29T06:00:00 |1464755  |47217    |85417        |40206  |
|2017.11.29T09:00:00 |1419843  |43456    |82057        |34443  |
|2017.11.29T12:00:00 |1442703  |41315    |85035        |31216  |
|2017.11.29T14:00:00 |1746561  |59304    |112516       |34303  |
|2017.11.29T18:00:00 |234915   |8175     |14569        |3598   |
|2017.11.29T22:00:00 |350462   |12197    |22934        |6012   |

这种方法比较简单，但是需要编写大量重复代码。当然也可以把重复代码封装成函数。

```
def calculateBehavior(startTime,endTime){
    return select first(behaveTime) as time, sum(iif(behavior=="pv",1,0)) as pageView, sum(iif(behavior=="fav",1,0)) as favorite, sum(iif(behavior=="cart",1,0)) as shoppingCart, sum(iif(behavior=="buy",1,0)) as payment from user where behaveTime between startTime : endTime
}
```

这样只需要指定时间段的起始时间即可。

另外一种方法是通过DolphinDB的Map-Reduce框架来完成。例如，统计工作日2017.11.29（周三）的用户行为。

```python
def caculate(t){
	return select first(behaveTime) as time, sum(iif(behavior=="pv",1,0)) as pageView, sum(iif(behavior=="fav",1,0)) as favorite, sum(iif(behavior=="cart",1,0)) as shoppingCart, sum(iif(behavior=="buy",1,0)) as payment from t	
}
ds1 = repartitionDS(<select * from user>, `behaveTime, RANGE,2017.11.29T00:00:00 2017.11.29T06:00:000 2017.11.29T09:00:00 2017.11.29T12:00:00 2017.11.29T14:00:00 2017.11.29T18:00:00 2017.11.29T22:00:00 2017.11.29T23:59:59)

WedBehavior = mr(ds1, caculate, , unionAll{, false})
```
|time                |pageView |favorite |shoppingCart |payment|
|------------------- |-------- |-------- |------------ |-------|
|2017.11.29T00:00:00 |2582410  |87924    |152219       |73304  |
|2017.11.29T06:00:00 |1464755  |47217    |85417        |40206  |
|2017.11.29T09:00:00 |1419843  |43456    |82057        |34443  |
|2017.11.29T12:00:00 |1442703  |41315    |85035        |31216  |
|2017.11.29T14:00:00 |1746561  |59304    |112516       |34303  |
|2017.11.29T18:00:00 |234915   |8175     |14569        |3598   |
|2017.11.29T22:00:00 |350391   |12195    |22931        |6012  |

我们使用[`repartitionDS`](https://www.dolphindb.cn/cn/help/repartitionDS.html)函数对user表重新按照时间范围来分区（不改变user表原来的分区方式），并生成多个数据源，然后通过[`mr`](https://www.dolphindb.cn/cn/help/mr.html)函数，对数据源进行并行计算。DolphinDB会把caculate函数应用到各个数据源上，然后把各个结果合并。

工作日，凌晨（0点到6点）淘宝APP的使用率最高，其次是下午（14点到16点）。

统计周六（2017.11.25）和周日（2017.11.26）的用户行为

```python
ds2 = repartitionDS(<select * from user>, `behaveTime, RANGE,2017.11.25T00:00:00 2017.11.25T06:00:000 2017.11.25T09:00:00 2017.11.25T12:00:00 2017.11.25T14:00:00 2017.11.25T18:00:00 2017.11.25T22:00:00 2017.11.25T23:59:59)

SatBehavior = mr(ds2, caculate, , unionAll{, false})
```
|time                |pageView |favorite |shoppingCart |payment|
|------------------- |-------- |-------- |------------ |-------|
|2017.11.25T00:00:00 |2465507  |83185    |148451       |64379  |
|2017.11.25T06:00:00 |1478819  |47654    |86446        |36692  |
|2017.11.25T09:00:00 |1497958  |47060    |86635        |31319  |
|2017.11.25T12:00:00 |1480358  |43894    |88071        |27809  |
|2017.11.25T14:00:00 |1881748  |63171    |119473       |32077  |
|2017.11.25T18:00:00 |251537   |8866     |15583        |3593   |
|2017.11.25T22:00:00 |379236   |11980    |24576        |5428 |

```python
ds3 = repartitionDS(<select * from user>, `behaveTime, RANGE,2017.11.26T00:00:00 2017.11.26T06:00:000 2017.11.26T09:00:00 2017.11.26T12:00:00 2017.11.26T14:00:00 2017.11.26T18:00:00 2017.11.26T22:00:00 2017.11.26T23:59:59)

SunBehavior = mr(ds3, caculate, , unionAll{, false})
```
|time                |pageView |favorite |shoppingCart |payment|
|------------------- |-------- |-------- |------------ |-------|
|2017.11.26T00:00:00 |2537125  |86390    |152900       |64245  |
|2017.11.26T06:00:00 |1484409  |47248    |87369        |37040  |
|2017.11.26T09:00:00 |1504735  |46633    |87364        |33127  |
|2017.11.26T12:00:00 |1522666  |44447    |91968        |29455  |
|2017.11.26T14:00:00 |1849318  |61396    |120420       |39414  |
|2017.11.26T18:00:00 |236410   |8237     |13819        |3994   |
|2017.11.26T22:00:00 |340857   |11370    |21579        |7038   |

周六和周日各个时间段淘宝APP的使用率都比工作日的使用率要高。同样地，周六日淘宝APP使用高峰是凌晨（0点到6点）。

## 3. 商品分析

```python
allItems=select distinct(itemID) from user
```
> 4142583

在这9天中，一共涉及到4,142,583种商品。

统计每个商品的购买次数

```
itemBuyTimes=select count(userID) as times from user where behavior="buy" group by itemID order by times desc
```

统计销量前20的商品

```python
salesTop=select top 20 * from itemBuyTimes order by times desc
```
|itemID	|times|
|------ |-------|
|3122135	|1408|
|3031354	|942|
|3964583	|671|
|2560262	|658|
|2964774	|614|
|740947	|553|
|,910706	|546|
|1116492	|512|
|705557	|495|
|4443059	|490|
|1415828	|484|
|1034594	|476|
|1168232	|462|
|3189426	|451|
|4219087	|441|
|265985	|439|
|257772	|404|
|1535294	|402|
|2955846	|393|
|5062984	|391|

ID为3122135的商品销量最高，一共有1,408次购买。

统计各个购买次数下商品的数量

```python
buyTimesItemNum=select count(itemID) as itemNums from itemBuyTimes group by times order by itemNums desc
```

结果显示，绝大部分（370,747种）商品在这9天中都只被购买了一次，占所有商品的8.94%。购买次数越多，涉及到的商品数量越少。

统计所有商品的用户行为数量

```python
allItemsInfo=select sum(iif(behavior=="pv",1,0)) as pageView, sum(iif(behavior=="fav",1,0)) as favorite, sum(iif(behavior=="cart",1,0)) as shoppingCart, sum(iif(behavior=="buy",1,0)) as payment from user group by itemID 
```

统计浏览量前20的商品

```python
pvTop=select top 20 itemID,pageView from allItemsInfo order by pageView desc
```
|itemID  |pageView|
|------- |--------|
|812879  |29720   |
|3845720 |25290   |
|138964  |20927   |
|2331370 |19348   |
|2032668 |19075   |
|1535294 |17830   |
|59883   |17313   |
|4211339 |17235   |
|3371523 |17156   |
|2338453 |17044   |
|3031354 |16975   |
|2367945 |16189   |
|1591862 |16185   |
|2818406 |15888   |
|987143  |15696   |
|4649427 |14959   |
|1583704 |14619   |
|2453685 |14451   |
|2279428 |14257   |
|4443059 |14016 |

浏览量最高的商品ID为812879，共有29,720次浏览，但是销量仅为135，没有进入到销量前20。

统计销量前20的商品各个用户行为的数量

```python
select * from ej(salesTop,allItemsInfo,`itemID) order by times desc
```
|itemID  |times |pageView |favorite |shoppingCart |payment|
|------- |----- |-------- |-------- |------------ |-------|
|3122135 |1408  |1777     |151      |342          |1408   |
|3031354 |942   |16975    |508      |1730         |942    |
|3964583 |671   |4960     |155      |567          |671    |
|2560262 |658   |10289    |308      |1258         |658    |
|2964774 |614   |6490     |129      |712          |614    |
|740947  |553   |7634     |467      |803          |553    |
|1910706 |546   |1628     |52       |165          |546    |
|1116492 |512   |893      |47       |163          |512    |
|705557  |495   |9236     |184      |873          |495    |
|4443059 |490   |14016    |334      |948          |490    |
|1415828 |484   |2746     |23       |470          |484    |
|1034594 |476   |668      |5        |0            |476    |
|1168232 |462   |2871     |89       |361          |462    |
|3189426 |451   |3432     |74       |345          |451    |
|4219087 |441   |4194     |113      |476          |441    |
|265985  |439   |4711     |111      |455          |439    |
|257772  |404   |2381     |51      | 133          |404 |

销量最高的商品3122135的浏览量为1777，没有进入浏览量前20，从浏览到购买的转化率高达79.2%，该商品有可能是刚需用品，用户不需要太多浏览就决定购买。


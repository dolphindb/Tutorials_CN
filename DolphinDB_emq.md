# EMQ+DolphinDB搭建MQTT物联网可视化平台

  - [1.模拟生成环境数据并推送到EMQ](#1模拟生成环境数据并推送到EMQ)
    - [1.1 安装mqtt插件](#11-安装mqtt插件)
    - [1.2 模拟数据并推送到EMQ](#12-模拟数据并推送到EMQ)
  - [2.商业版EMQ连接DolphinDB](#2商业版emq连接dolphindb)
  - [3.开源版EMQ连接DolphinDB](#3开源版emq连接dolphindb)
  - [4.使用Grafana可视化数据](#4使用grafana可视化数据)

本文主要演示如何将EMQ数据写入DolphinDB，并搭建可视化平台。

总的来看，有两种方式实现EMQ数据写入DolphinDB。一是EMQ实现DolphinDB相关接口，将数据推送给DolphinDB。二是在DolphinDB这边，通过mqtt插件，订阅EMQ的数据。

关于第一种方式，EMQ推送数据到DolphinDB。在EMQ的商业版本中，实现了基于TCP协议的将数据写入DolphinDB的功能。但是开源版本没有开放这个功能。
在EMQ的开源版本中，实现了Webhook的方式，通过Restful API将数据POST 到对应的后端。目前DolphinDB的Restful API还没有实现。不过可以通过mqtt插件来订阅EMQ的数据，然后存储到表。


## 1.模拟生成环境数据并推送到EMQ

本节中，我们通过在DolphinDB里面，模拟生成一些数据，然后通过mqtt插件，来写入EMQ，以模拟生产环境中，数据生成和写入EMQ的过程。如果已经有数据，可以跳过本章，查看对应版本的EMQ（商业版/开源版）如何连接DolphinDB。


### 1.1 安装mqtt插件

默认官网下载的DolphinDB包自带的插件里，没有包含mqtt插件。需要从[DolphinDBPlugin](https://gitee.com/dolphindb/DolphinDBPlugin)里下载获取。

可以先clone代码库

``` shell
[jzchen@cnserver9 ~]$ git clone https://gitee.com/dolphindb/DolphinDBPlugin.git
```

在DolphinDBPlugin/mqtt/bin目录下，包括了linux64和win64两个平台的已经编译好的插件，只需要将插件拷贝到DolphinDB的server目录下的plugins里

``` shell
[jzchen@cnserver9 server]$ cp -R ~/DolphinDBPlugin/mqtt/bin/linux64 ~/server/plugins/mqtt
```
上面命令中，我们将linux64下的插件，拷贝到了server/plugins目录下，并将其命名为mqtt以方便区分。

之后打开GUI,连接到server，通过loadPlugin来验证是否成功，脚本如下

``` shell
loadPlugin(getHomeDir()+"/plugins/mqtt/PluginMQTTClient.txt")
```

### 1.2 模拟数据并推送到EMQ


我们生成一些数据来模拟物联网的传感器数据采集的场景,如下：

``` shell
host='115.239.209.122'
port=1883
topic="sensor/s001"
colNames=`time`device_id`battery_level`battery_status`battery_temperature
colTypes=`TIMESTAMP`INT`INT`STRING`DOUBLE
```

上面代码中，我们先定义一些公共的变量。包括EMQ的相关连接信息（host,port,topic)，还有模拟数据的结构信息。其中`time`表示时间，`device_id`表示设备号，`battery_level`表示设备电池水平，`battery_status`表示设备状态,包括charging和discharging两种，`battery_temperature`表示设备当前的温度。


接下去，我们定义一个函数，随机生成一些数据，并通过[mqtt插件](https://gitee.com/dolphindb/DolphinDBPlugin/blob/master/mqtt/README_CN.md)的publish，来将数据推送到EMQ,来模拟实际环境中的数据生成的过程。


``` shell
f = createJsonFormatter()

def publishTableData(server,topic,f, n){
    	conn=connect(server,1883,0,f,100)
    	t=table(
			take(now(), n) as time, 
			take(1..2, n) as device_id, 
			take(0..100, n) as battery_level, 
			take(`charging`discharging, n) as battery_status,
			take(rand(370,900)/3.0, n) as battery_temperature
		)	
		publish(conn,topic,t)
		close(conn)
}
submitJob("submit_pub1", "submit_p1", publishTableData{host,topic,f, n})
```

上面代码里的`createJsonFormatter`函数，创建了一个JSON的格式化函数。在`publishTableData`函数里，我们创建连接，并模拟是生成一些数据，并且推送到EMQ存储。之后，我们通过[submitJob](http://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/s/submitJob.html?highlight=submitjob)来把作业任务提交到节点。


## 2.商业版EMQ连接DolphinDB

在EMQ的商业版中，提供了GUI上的设置界面，直接把数据写入DolphinDB。

首先我们来创建一个规则引擎，来接收上面步骤2在DolphinDB里模拟并发送的数据。

![](images/emq/rule.png)

如上图所示，我们在规则引擎的SQL输入里输入

``` shell
foreach
  json_decode(payload)
do
  item as p
FROM "sensor/#"
```

这里，在模拟数据时，发送到EMQ的数据是一个JSON Array，所以这里需要通过`json_decode`来获取出里面的每一条记录item,并命名为p。

接着，在响应动作里，可以针对记录p来做处理。

![](images/emq/action.png)

添加一个action,其动作类型为持久化，保存数据到DolphinDB。

在SQL模板里，填入

``` shell
insert into dt values(
  ${p.time}, 
  ${p.device_id}, 
  ${p.battery_level}, 
  '${p.battery_status}', 
  ${p.battery_temperature})
```

这里，将数据写入一个共享表dt。dt在DolphinDB里的定义如下:

``` shell
deviceTable=table(10000:0, colNames, colTypes)
share deviceTable as dt;
```

当然，实际场景中也可以使用分布式表，这里使用内存表只是作为一个示例。


在保存规则前，还需要在编辑动作的页码中，新建一个DolphinDB的资源链接

![](images/emq/conn.png)

填写完信息后，最后保存。这样当模拟的数据被推送到EMQ后，就会自动的写入内存表dt


## 3.开源版EMQ连接DolphinDB


在开源版本的EMQ中，没有上面直接设置就能写入数据到DolphinDB的功能，不过我们通过DolphinDB订阅EMQ，获取数据并存储的过程。代码如下:

``` shell
sp=createJsonParser([TIMESTAMP, INT, INT, STRING, DOUBLE], colNames)
deviceTable=table(10000:0, colNames, colTypes)
mqtt::subscribe(host, port, "sensor/#", sp, deviceTable)
```

上面代码中，我们通过`createJsonFormatter`来创建了一个JSON格式的分析函数，因为之前的模拟数据是通过`createJsonParser`创建的。除了JSON格式之外，DolphinDB还支持CSV格式的数据。

之后，我们定一个deviceTable内存表来存储接收到的数据。实际环境中，可以使用[分布式表](https://gitee.com/dolphindb/Tutorials_CN/blob/master/database.md)来存储。


在订阅数据之后，通过调用之前定义的模拟数据生成的函数，可以生成模拟数据推送到EMQ,这里的deviceTable就能接收到EMQ的数据了。

完整代码如下:

``` shell
loadPlugin(getHomeDir()+"/plugins/mqtt/PluginMQTTClient.txt")

use mqtt;
// mqtt config
host='115.239.209.122'
port=1883
topic="sensor/s001"
colNames=`time`device_id`battery_level`battery_status`battery_temperature
colTypes=`TIMESTAMP`INT`INT`STRING`DOUBLE

//publish
f = createJsonFormatter()
n=100000
def publishTableData(server,topic,f, n){
    	conn=connect(server,1883,0,f,100)

    	t=table(
		take(now(), n) as time, 
		take(1..2, n) as device_id, 
		take(0..100, n) as battery_level, 
		take(`charging`discharging, n) as battery_status,
		take(rand(370,900)/3.0, n) as battery_temperature
	)	
   	publish(conn,topic,t)
    	close(conn)
}
submitJob("submit_pub1", "submit_p1", publishTableData{host,topic,f, n})


//subscribe
sp=createJsonParser([TIMESTAMP, INT, INT, STRING, DOUBLE], colNames)
deviceTable=table(10000:0, colNames, colTypes)
mqtt::subscribe(host, port, "sensor/#", sp, deviceTable)
```

## 4.使用Grafana可视化数据

先参考[grafana教程](https://gitee.com/dolphindb/grafana-datasource/blob/master/README_CN.md)来安装和配置DolphinDB数据源。

在DolphinDB里，我们可以自定义一个函数视图，来格式化好时间字段，使Grafana里能够调用该视图，以便正常显示时间。如下:

``` shell
login("admin","123456")
def getLatestBattery() {
	return select  temporalFormat(time, "yyyy-MM-dd HH:mm:ss")  as Time, battery_temperature from dt order by time desc;
}
addFunctionView(getLatestBattery)
```

在grafana里,我们可以创建一个dashboard,选择DolphinDB的数据源，然后输入查询语句。如下:

``` shell
login("admin","123456"); getLatestBattery();
```

当模拟数据源源不断生成并且推送到EMQ，再通过DolphinDB订阅或者商业版的GUI配置写入DolphinDB时。grafana这里查询就能收到持续的数据，然后绘制图形。如下:

![](images/emq/grafana.png)
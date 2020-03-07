# DolphinDB启动脚本 
DolphinDB database从1.0版本开始，提供了启动脚本功能。用户可以通过配置参数startup来指定用户级的启动脚本，默认值是startup.dos。通过设定启动脚本，DolphinDB启动的时候会自动完成每次启动都需要执行的工作，譬如初始化流数据，定义共享变量，加载插件脚本等。

## 1. DolphinDB启动顺序
DolphinDB节点的启动是一个复杂的过程。与启动脚本相关的脚本和任务至少包括：系统级的初始化脚本（通过init参数指定，默认值dolphindb.dos），函数视图(function view)以及定时任务(scheduled job)。启动脚本以及相关组件资源的初始化顺序如下图所示。

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/startup.png?raw=true){.center}

系统级初始化脚本是必需的，默认是版本发布目录中的dolphindb.dos，其中定义了一些系统级的函数。从启动顺序图中我们可以看到，dolphindb.dos脚本在执行时脚本解释器、工作线程等已完成初始化，但系统的网络和分布式文件系统尚未启动、函数视图尚未加载。而启动脚本执行前，系统的网络和分布式文件系统已启动，函数视图已加载。因此在启动脚本中我们几乎可以做任何事情。

从图中也可以看到用户事先安排的定时任务在启动脚本执行后加载。因此scheduled jobs中若用到了插件函数、共享表等，需要在启动脚本中预先加载或定义，否则反序列化scheduled job会失败。需要注意的是，函数视图的加载在启动脚本执行之前。如果函数视图中用了插件，加载插件必须在dolphindb.dos中完成。与定时任务存储在数据节点不同，函数视图存储在控制节点。所以我们不建议在函数视图中使用插件，否则在集群中每个节点的dolphindb.dos都需要加载插件。

## 2. 执行启动脚本

启动脚本的配置项名为startup，参数值是自定义的启动脚本文件名，可配置绝对路径或相对路径，参数的默认值是startup.dos。若配置了相对路径或者没有指定目录，系统会在节点的home目录、工作目录和可执行文件所在目录依次搜索。该参数单机模式时在dolphindb.cfg中配置，集群模式时在节点配置文件cluster.cfg中配置。

配置举例如下:
```
startup=/home/streamtest/init/server/startup.dos
```

启动脚本以本地管理员的身份运行，但并没有登录集群，所以访问集群的分布式功能时以guest身份运行。因此，若要远程执行控制节点的某些功能，访问集群中的某个分布式表，需要先以管理员(admin)或其他授权用户身份登录。具体可以通过`login`函数来完成。

脚本执行过程中若遇到错误，执行会中断，但系统不会退出，而是继续运行。运行过程中的所有输出，都会记录在本地节点的日志文件中。

## 3.常见应用场景

系统重启后可能需要做的初始化工作主要有：定义并共享内存表，定义、加载并共享流数据表、订阅流数据、加载插件等。

**例子1**：定义内存表并共享

下面代码中定义了一张内存表t，并分享为sharedT。在其他会话中就可以对表sharedT进行增加、更新、删除和查询记录。
```
t=table(1:0,`date`sym`val,[DATE,SYMBOL,INT])
share(t, `sharedT); 
```

**例子2**：定义、加载流数据表并共享、订阅

流数据表的定义不可在DolphinDB中持久化保存，所以流数据表的初始化工作可在启动脚本中执行。下面代码加载并共享了流数据表st1：
```
login("admin","123456")
t1=streamTable(1:0,`date`sym`val,[DATE,SYMBOL,INT])
enableTableShareAndPersistence(table=t1,tableName=`st1,cacheSize=1000)
```
流数据表的订阅也可在启动脚本中完成。下面的代码订阅了上述流数据表st1，并把订阅的数据保存到分布式库表：
```
tb=loadTable("dfs://db1","tb")
subscribeTable(,"st1","subst",-1,append!{tb},true)
```

**例子3**：加载插件

若scheduled jobs中用到了插件函数，必须在启动脚本中加载插件，否则会因反序列化失败导致系统退出。下列代码在scheduled jobs中用到了odbc插件：
```
use odbc
def jobDemo(){
	conn = odbc::connect("dsn=mysql_factorDBURL");
	//...
}
scheduleJob("job demo","example of init",jobDemo,15:48m, 2019.01.01, 2020.12.31, 'D')
```
但odbc插件在系统启动时没有加载，所以读取scheduled job的时候，因无法识别这个函数，输出下列日志后退出系统。
```
<ERROR>:Failed to unmarshall the job [job demo]. Failed to deserialize assign statement.. Invalid message format
```
在启动脚本中加入下列代码加载odbc插件后，系统即启动成功。
```
loadPlugin("plugins/odbc/odbc.cfg")
```
## 4. 编写启动脚本

编写DolphinDB启动脚本时，可以使用[`module`](https://github.com/dolphindb/Tutorials_CN/blob/master/module_tutorial.md)来声明和使用可重用模块，可以自定义函数，可以使用分布式的功能。几乎没有限制。

若需要调试启动脚本，可以在脚本中用`print`与`writeLog`等函数打印日志。系统会把启动脚本运行情况输出到节点日志，譬如一开始系统会输出下列日志表示启动脚本开始执行：
```
 <INFO> :Executing the startup script: 
```
编写启动脚本时，为了防止出现异常而停止执行后续的脚本，可使用try-catch语句俘获异常。

## 5. 不适合启动脚本的任务

启动脚本几乎可以做任何事情，但是少数功能和任务仍然不适合在启动脚本中完成。

* 定时任务在启动脚本之后运行，所以不能在启动脚本中使用跟定时任务相关的任何功能，包括函数`scheduleJob`, `getScheduledJobs`和`deleteScheduledJob`。
* 若需要定义系统级的函数，所有用户都能看到，而且不能被覆盖，请在初始化脚本dolphindb.dos中定义。
* 若任务需要依赖其他节点，不适合在启动脚本中完成，极有可能其他节点尚未启动。




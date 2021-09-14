# DolphinDB定时作业 

DolphinDB提供的定时作业（scheduled job）功能，可以让系统在指定的时间以指定的频率自动执行作业。当我们需要数据库定时自动执行一些脚本进行计算分析（譬如每日休市后分钟级的K线计算、每月统计报表生成）、数据库管理（譬如数据库备份、数据同步）、操作系统管理（譬如过期的日志文件删除）等工作时，可以用这个功能来实现。

定时作业用一个函数来表示，这给了作业定义极大的灵活性。凡是能用函数来表示的工作，都可以作为定时任务来运行。定时作业通过[scheduleJob](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/s/scheduleJob.html)函数提交，并按设定时间在后台运行。作业创建后，作业相关定义信息序列化保存到数据节点的磁盘文件。节点重启后，系统会反序列化并加载定时作业。定时作业每次运行的结果也会保存到节点磁盘上，我们可以使用[getJobMessage](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getJobMessage.html)和[getJobReturn](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getJobReturn.html)来查看每个作业的运行日志和返回值。

## 1.功能介绍
### 1.1 创建定时作业
创建定时作业使用函数[scheduleJob](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/s/scheduleJob.html)。作业创建后，系统会序列化作业定义信息并保存到文件`<homeDir>/sysmgmt/jobEditlog.meta`。函数语法如下：
```
scheduleJob(jobId, jobDesc, jobFunc, scheduledTime, startDate, endDate, frequency, [days])
```
其中要注意的是：
* 参数jobFunc（作业函数）是一个不带参数的函数。
* 参数scheduledTime（预定时间）可以是minute类型的标量或向量。当它为向量时，注意相邻2个时间点的间隔不能小于30分钟。
* 函数返回值是定时作业的作业ID。如果输入的jobId与已有定时作业的作业ID不重复，系统返回输入的jobId。否则在jobId后面添加当前日期，"000"，“001”等作为后缀，直到产生唯一的作业ID。

众所周知，执行一个函数必须提供函数需要的所有参数。在函数化编程中，一个提供了所有参数的函数，实际上就是原函数的一个特殊的[部分应用](https://www.dolphindb.cn/cn/help/Functionalprogramming/PartialApplication.html)（Partial Application），也即一个不带参数的函数。在DolphinDB中，我们用花括号{}来表示部分应用。

自定义函数、内置函数、插件函数、函数视图（Function View）和模块中的函数等各类函数都可以作为作业函数。因此，定时作业几乎能做任何事情。比如用自定义函数、插件函数等做计算分析，用内置函数run运行一个脚本文件，用shell函数执行操作系统管理等等。下面例子中的作业调用了一个自定义函数getMaxTemperature，用于计算前一天某个设备温度指标的最大值，参数是设备编号，创建作业时，用getMaxTemperature{1}给设备编号赋值1，定时作业在每天0点执行。
```
def getMaxTemperature(deviceID){
    maxTemp=exec max(temperature) from loadTable("dfs://dolphindb","sensor")
            where ID=deviceID ,ts between (today()-1).datetime():(today().datetime()-1)
    return  maxTemp
}
scheduleJob(`testJob, "getMaxTemperature", getMaxTemperature{1}, 00:00m, today(), today()+30, 'D');
```
下面的例子执行了一个脚本文件。作业函数用了run函数，并指定脚本文件monthlyJob.dos的完整路径作为参数，作业在2020年的每月1号0点执行。
```
scheduleJob(`monthlyJob, "Monthly Job 1", run{"/home/DolphinDB/script/monthlyJob.dos"}, 00:00m, 2020.01.01, 2020.12.31, 'M', 1);
```
下面的例子执行了一个删除日志文件的操作系统命令。作业函数用了shell函数，并指定具体的命令“rm /home/DolphinDB/server/dolphindb.log”作为参数。作业在每周的周日1点执行。
```
scheduleJob(`weeklyjob, "rm log", shell{"rm /home/DolphinDB/server/dolphindb.log"}, 1:00m, 2020.01.01, 2021.12.31, 'W', 6);
```
在实际应用中，用函数参数、函数返回值进行输入输出有点不太方便，我们更常用的做法是从数据库中取出数据，计算后把结果再存到数据库中。下面的例子是在每日休市后，计算分钟级的K线。自定义函数computeK中，行情数据从分布式数据库表trades中取出，计算后存入分布式数据库表OHLC中。作业的frequency为"W"、days为[1,2,3,4,5]，scheduledTime为15:00m，表示作业在每周一到周五的15点执行。
```
def computeK(){
	barMinutes = 7
	sessionsStart=09:30:00.000 13:00:00.000
	OHLC =  select first(price) as open, max(price) as high, min(price) as low,last(price) as close, sum(volume) as volume 
		from loadTable("dfs://stock","trades")
		where time >today() and time < now()
		group by symbol, dailyAlignedBar(timestamp, sessionsStart, barMinutes*60*1000) as barStart
	append!(loadTable("dfs://stock","OHLC"),OHLC)
}
scheduleJob(`kJob, "7 Minutes", computeK, 15:00m, 2020.01.01, 2021.12.31, 'W', [1,2,3,4,5]);
```
### 1.2 查询定时作业
查询节点中的定时作业定义信息可以用[getScheduledJobs](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getScheduledJobs.html)。函数语法如下：
```
getScheduledJobs([jobIdPattern])
```
其中参数jobIdPattern是表示作业ID或作业ID模式的字符串。它支持通配符“%”和“?”。函数的返回值是表格形式的定时作业信息。若jobId没有指定，则返回所有作业。

系统会对每次作业的执行情况进行保存，包括定时作业的运行日志和返回值。运行日志保存在jodId.msg 文件中，定时作业的返回值保存在jobId.object文件中。这些文件都保存在目录`<homeDir>/batchJobs`下。我们可以分别使用[getJobMessage](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getJobMessage.html)和[getJobReturn](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getJobReturn.html)来查看每个作业的运行日志和返回值。但要注意jobID的取值，一是创建作业时，如前所述，若jobId与已有定时作业的作业ID重复，系统返回的不是输入的jobId；二是对会多次执行的作业，每次执行定时作业时，作业ID是不一样的。因此我们需要用[getRecentJobs](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getRecentJobs.html)来查看已完成的定时作业。比如我们定义如下定时作业：
```
def foo(){
	print "test scheduled job at"+ now()
	return now()
}
scheduleJob(`testJob, "foo", foo, 17:00m+0..2*30, today(), today(), 'D');
```
运行getRecentJobs()后得到如下信息：
```
jobId	            jobDesc	startTime	            endTime
------              ------- ----------------------- ----------------------
testJob	            foo1	2020.02.14T17:00:23.636	2020.02.14T17:00:23.639
testJob20200214	    foo1	2020.02.14T17:30:23.908	2020.02.14T17:30:23.910
testJob20200214000  foo1	2020.02.14T18:00:23.148	2020.02.14T18:00:26.749
```
从中我们看到，第一次执行的作业ID是“testJob”，第二次是“testJob20200214”...每次都有变化。如下所示，我们可用getJobMessage和getJobReturn查看了第3次的执行情况：
```
>getJobMessage(`testJob20200214000);
2020-02-14 18:00:23.148629 Start the job [testJob20200214000]: foo
2020-02-14 18:00:23.148721 test the scheduled job at 2020.02.14T18:00:23.148
2020-02-14 18:00:26.749111 The job is done.

>getJobReturn(`testJob20200214000);
2020.02.14T18:00:23.148
```
### 1.3 删除定时作业
删除定时作业用函数[deleteScheduledJob](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/d/deleteScheduledJob.html)。语法如下：
```
deleteScheduledJob(jobId)
```
参数jobId是作业ID。删除前可用[getScheduledJobs](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getScheduledJobs.html)得到想要删除作业的作业ID。

## 2.定时作业运行时的权限
用户创建定时作业时以什么身份登录，执行定时作业时就以这个身份运行。因此用户创建定时作业时，需要确保用户有权限访问用到的资源。比如登录用户不是授权用户，就不能访问集群的分布式功能，若用到了集群的分布式功能，执行时就会出错。以下例子中用户guestUser1没有访问DFS权限：
```
def foo1(){
	print "Test scheduled job "+ now()
	cnt=exec count(*) from loadTable("dfs://FuturesContract","tb")
	print "The count of table is "+cnt
	return cnt
}
login("guestUser1","123456")
scheduleJob(`guestGetDfsjob, "dfs read", foo1, [12:00m, 21:03m, 21:45m], 2020.01.01, 2021.12.31, "D");
```
作业执行后，用getJobMessage(`guestGetDfsjob)查询，如下所示，定时作业没有权限去读取分布式数据库：
```
2020-02-14 21:03:23.193039 Start the job [guestGetDfsjob]: dfs read
2020-02-14 21:03:23.193092 Test the scheduled job at 2020.02.14T21:03:23.193
2020-02-14 21:03:23.194914 Not granted to read table dfs://FuturesContract/tb
```
因此，若要远程执行控制节点的某些功能，访问集群中的某个分布式表，需要先以管理员(admin)或其他授权用户身份登录。具体可以通过[login](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/l/login.html)函数来完成。

从所示日志中也可以发现，访问分布式表后的语句没有执行，也就是说作业执行过程中若遇到错误，执行会中断。为了防止出现异常而停止执行后续的脚本，可使用try-catch语句俘获异常。运行过程中需要输出运行信息，可以用print打印，输出都会记录在jodId.msg日志文件中。

## 3.定时作业的序列化
定时作业在创建后，系统会把创建用户（userID）、作业的ID、描述信息、起始时间、作业频率、作业的定义等持久化保存。存储路径为`<homeDir>/sysmgmt/jobEditlog.meta`。作业用一个DolphinDB的函数来表示。函数的定义包括了一系列语句，这些语句又会调用其他函数和一些全局类对象，譬如共享变量(shared variable)。共享变量序列化时用名称来表示。反序列化时，共享变量必须存在，否则会失败。作业函数或其依赖的函数根据是否经过编译可以分两类：经过编译的函数包括内置函数和插件函数和脚本函数包括自定义函数、函数视图和模块中的函数等。这两类函数的序列化方法有所不同，下面分别进行说明。
### 3.1 经过编译的函数的序列化
对经过编译的函数的序列化，只序列化函数名称和模块名称。反序列化的时候，会在系统中搜索这些模块及函数，若搜索不到，就会失败。所以定时作业中若用到了插件函数，就需要在反序列化之前预先加载。系统与定时作业相关组件资源的初始化顺序依次是：系统级初始化脚本（dolphindb.dos），函数视图(function view)、用户级[启动脚本](Startup.md)（startup.dos）和定时作业。定时作业在启动脚本执行后加载。如下例所示，在作业函数jobDemo中用到了odbc插件：
```
use odbc
def jobDemo(){
	conn = odbc::connect("dsn=mysql_factorDBURL");
}
scheduleJob("job demo","example of init",jobDemo,15:48m, 2019.01.01, 2020.12.31, 'D')
```
但odbc插件在系统启动时没有加载，所以读取定时作业的时候，因无法识别这个函数，输出下列日志后退出系统。
```
<ERROR>:Failed to unmarshall the job [job demo]. Failed to deserialize assign statement.. Invalid message format
```
在启动脚本中加入下列代码加载odbc插件后，系统即启动成功。
```
loadPlugin("plugins/odbc/odbc.cfg")
```
### 3.2 脚本函数的序列化
脚本函数会序列化函数参数以及函数定义的每一个语句。语句中若又包含了依赖的脚本函数，也会序列化这些依赖函数的定义。

创建定时作业后，若这些脚本函数被删除或被修改了，或它依赖的脚本函数被修改，不影响定时作业运行。若希望定时作业按新的函数执行，就需要先删除定时作业、然后重新创建定时作业，否则会运行旧的序列化的函数。其中要注意关联的函数也需要重新定义。下面举例说明：
* 例子1，作业函数在创建定时作业后被修改，如下所示，作业函数f在创建scheduleJob后被重新定义：
```
def f(){
	print "The old function is called " 
}
scheduleJob(`test, "f", f, 11:05m, today(), today(), 'D');
go
def f(){
	print "The new function is called " 
}
```
定时作业执行后，用getJobMessage(`test)得到如下信息，从中看到定时作业执行的还是旧的自定义函数。
```
2020-02-14 11:05:53.382225 Start the job [test]: f
2020-02-14 11:05:53.382267 The old function is called 
2020-02-14 11:05:53.382277 The job is done.
```
* 例子2，作业函数在创建定时作业后依赖的函数被修改，如下所示，作业函数是函数视图fv，fv调用了函数foo，在scheduleJob后，函数foo重新被定义，函数视图也重新生成：
```
def foo(){
	print "The old function is called " 
}
def fv(){
	foo()
}
addFunctionView(fv)  

scheduleJob(`testFvJob, "fv", fv, 11:36m, today(), today(), 'D');
go
def foo(){
	print "The new function is called " 
}
dropFunctionView(`fv)
addFunctionView(fv) 
```
定时作业执行后，然后getJobMessage(`testFvJob)得到如下信息，从中看到定时作业执行的还是旧的函数。
```
2020-02-14 11:36:23.069892 Start the job [testFvJob]: fv
2020-02-14 11:36:23.069939 The old function is called 
2020-02-14 11:36:23.069951 The job is done.
```
用模块函数也是如此。我们创建一个模块printLog.dos,其内容如下：
```
module printLog
def printLogs(logText){
	writeLog(string(now()) + " : " + logText)
	print "The old function is called"
}
```
然后创建一个定时作业调用这个printLog::printLogs函数：
```
use printLog
def f5(){
	printLogs("test my log")
}
scheduleJob(`testModule, "f5", f5, 13:32m, today(), today(), 'D');
```
在运行定时作业之前修改模块如下：
```
module printLog
def printLogs(logText){
	writeLog(string(now()) + " : " + logText)
	print "The new function is called"
}
```
定时作业执行后，然后getJobMessage(`testModule)得到如下信息，从中看到定时作业执行的还是旧的函数。
```
2020-02-14 13:32:22.870855 Start the job [testModule]: f5
2020-02-14 13:32:22.871097 The old function is called
2020-02-14 13:32:22.871106 The job is done.
```
## 4.定时运行脚本文件
在创建定时作业时，若作业函数是run一个脚本文件，因为序列化时只保存了文件名，没有保存文件内容，所以需要把依赖的自定义函数都放到脚本文件中，否则会因为找不到自定义的函数而执行失败。比如创建一个脚本文件testjob.dos，文件内容如下：
```
foo()
```
然后在DolphinDB GUI中执行下列脚本：
```
def foo(){
	print ("Hello world!")
}
run "/home/xjqian/testjob.dos"
```
结果显示能正常执行：
```
2020.02.14 13:47:00.992: executing code (line 104-108)...
Hello world!
```
再创建定时作业run这个脚本文件，代码如下所示：
```
scheduleJob(`dailyfoofile1, "Daily Job 1", run {"/home/xjqian/testjob.dos"}, 16:14m, 2020.01.01, 2020.12.31, 'D');
```
但运行这个作业时却发生了如下异常：
```
Exception was raised when running the script [/home/xjqian/testjob.dos]:Syntax Error: [line #3] Cannot recognize the token foo
```
这是foo函数定义和定时作业执行不在同一个会话(session)中，作业执行时找不到函数定义的缘故。把foo()的定义放到脚本文件中，修改testjob.dos文件内容如下：
```
def foo(){
	print ("Hello world!")
}
foo()
```
再重新创建定时作业运行这个脚本文件，就能顺利完成。
## 5.小结和展望
#### 常见故障及排除
- 作业函数引用了共享变量，但是作业加载前没有定义该共享变量。一般建议在用户的启动脚本中定义该共享变量。
- 作业函数引用了插件中的函数，但是作业加载前没有加载该插件。一般建议在用户的启动脚本中定义加载该插件。
- 定时运行一个脚本文件，找不到依赖的函数。脚本文件必须包含依赖的自定义函数。
- 创建定时作业的用户没有访问分布式数据库表的权限。授权该用户访问相应数据库的权限。
- 在启动脚本中使用函数[scheduleJob](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/s/scheduleJob.html)、 [getScheduledJobs](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getScheduledJobs.html)和[deleteScheduledJob](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/d/deleteScheduledJob.html)时抛出异常。节点启动时，定时作业的初始化在[启动脚本](Startup.md)之后，因此不能在启动脚本中使用跟定时作业相关的功能

在某些罕见的情况下，可能出现在系统重启时，发生定时作业加载失败，甚至导致系统无法启动的情况。尤其是版本升级的时候，内置函数、插件函数等函数接口可能会有变化从而导致作业无法加载，或者出现一些兼容性bug导致系统重启失败。因此，我们开发时需要保留定义定时作业的脚本。若因定时任务导致系统无法启动，可以先删除定时作业的序列化文件`<homeDir>/sysmgmt/jobEditlog.meta`，在系统重启后再重新创建这些定时作业。
#### 后续功能开发
- 增加浏览作业函数以及依赖的函数的定义的功能。
- 定义和实现定时作业之间的依赖关系。
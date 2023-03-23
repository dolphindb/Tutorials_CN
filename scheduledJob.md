# DolphinDB定时作业

DolphinDB 定时作业（scheduled job）功能，实现系统在规定时间以指定频率自动执行作业。该功能广泛应用于数据库定时计算分析（如每日休市后分钟级的 K 线计算、每月统计报表生成）、数据库管理（如数据库备份、数据同步）、操作系统管理（如删除过期日志文件）等场景。

## 1. 创建定时作业

使用函数 [scheduleJob](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/s/scheduleJob.html) 创建定时作业。作业创建后，系统会序列化作业定义信息并保存到文件`<homeDir>/sysmgmt/jobEditlog.meta`。语法如下：

```
scheduleJob(jobId, jobDesc, jobFunc, scheduleTime, startDate, endDate, frequency, [days], [onComplete])
```

注意：

1. *jobFun* 是一个没有参数的函数，通常是一个[部分应用](https://www.dolphindb.cn/cn/help/Functionalprogramming/PartialApplication.html)，可以设置为自定义函数、内置函数、插件函数、函数视图和模块中的函数等。这给了作业定义极大的灵活性：凡是能用函数来表示的工作，都可以作为定时任务来运行。比如用自定义函数、插件函数等做计算分析，用内置函数 [run](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/r/run.html) 运行一个脚本文件，用 [shell](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/s/shell.html) 函数执行操作系统管理等等。
2. 函数返回值是定时作业的作业 ID。如果输入的 jobId 与已有定时作业的作业 ID 不重复，系统返回输入的 jobId。否则在 jobId 后面添加当前日期，"000", "001" 等作为后缀，直到产生唯一的作业 ID。
3. 当到达设定时间，定时作业将在后台运行。
4. 两次定时任务的执行时间（scheduleTime）的最小间隔为5分钟。

- 示例1：调用自定义函数 `getMaxTemperature`，在每天0点计算前一天某个设备温度指标的最大值。

```
def getMaxTemperature(deviceID){
    maxTemp=exec max(temperature) from loadTable("dfs://dolphindb","sensor")
            where ID=deviceID ,ts between (today()-1).datetime():(today().datetime()-1)
    return  maxTemp
}
scheduleJob(`testJob, "getMaxTemperature", getMaxTemperature{1}, 00:00m, today(), today()+30, 'D');
```

注意：自定义函数 `getMaxTemperature` 的参数是设备编号，[部分应用](https://www.dolphindb.cn/cn/help/Functionalprogramming/PartialApplication.html) getMaxTemperature{1} 代表给设备编号赋值1。

- 示例2：在2020年每个月1号的0点使用 run 函数执行脚本文件 monthlyJob.dos。

```
scheduleJob(`monthlyJob, "Monthly Job 1", run{"/home/DolphinDB/script/monthlyJob.dos"}, 00:00m, 2020.01.01, 2020.12.31, 'M', 1);
```

注意：指定脚本文件 monthlyJob.dos 的完整路径作为[部分应用](https://www.dolphindb.cn/cn/help/Functionalprogramming/PartialApplication.html) run 函数的参数。

- 示例3：在每周日的1点执行删除日志文件的操作系统命令。作业函数使用 shell 函数，并指定命令 "rm /home/DolphinDB/server/dolphindb.log" 作为参数。

```
scheduleJob(`weeklyjob, "rm log", shell{"rm /home/DolphinDB/server/dolphindb.log"}, 01:00m, 2020.01.01, 2021.12.31, `W`, 0);
```

在实际应用中，更常用的做法是从数据库中取出数据作为参数传入作业函数，计算后将结果存入数据库。示例4中的自定义函数 computeK，从分布式数据库表 trades 中取出行情数据，计算后将结果存入分布式数据库表 OHLC 中。

- 示例4：在每周一到每周五的15点，计算分钟级的 K 线。

```
def computeK(){
	barMinutes = 7
	sessionsStart=09:30:00.000 13:00:00.000
	OHLC =  select first(price) as open, max(price) as high, min(price) as low,last(price) as close, sum(volume) as volume 
		from loadTable("dfs://stock","trades")
		where time > today() and time < now()
		group by symbol, dailyAlignedBar(timestamp, sessionsStart, barMinutes*60*1000) as barStart
	append!(loadTable("dfs://stock","OHLC"),OHLC)
}
scheduleJob(`kJob, "7 Minutes", computeK, 15:00m, 2020.01.01, 2021.12.31, 'W', [1,2,3,4,5]);
```

- 示例5：定时任务执行结束后可发送邮件通知。参数onComplete 是一个有4个参数的回调函数，当定时作业执行完毕（包括有异常的情况）后，会执行该函数。

以下脚本运行前需安装 [HttpClient 插件](https://gitee.com/dolphindb/DolphinDBPlugin/blob/release200/httpClient/README.md)。

```
def sendEmail(jobId, jobDesc, success, result){
desc = "jobId=" + jobId + " jobDesc=" + jobDesc
if(success){
desc += " successful " + result
res = httpClient::sendEmail('patrick.mahomes@dolphindb.com','password','andy.reid@dolphindb.com','This is a subject',desc)
}
else{
desc += " with error: " + result
res = httpClient::sendEmail('patrick.mahomes@dolphindb.com','password','andy.reid@dolphindb.com','This is a subject',desc)
}
}
scheduleJob(jobId=`PnL, jobDesc="Calculate Profit & Loss", jobFunc=run{"PnL.dos"}, scheduleTime=[12:00m, 02
```

## 2. 查询定时作业

使用函数 [getScheduledJobs](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getScheduledJobs.html) 查询节点中的定时作业定义信息。函数语法如下：

```
getScheduledJobs([jobIdPattern])
```

注意：

1. 参数 *jobIdPattern* 是表示作业 ID 或作业 ID 模式的字符串，支持通配符"%"和"?"；
2. 函数的返回值是表格形式的定时作业信息。若 *jobId* 没有指定，则返回所有作业；
3. 可以通过 pnodeRun(getScheduledJobs) 或在 web 上的作业管理“已定时的作业”中查看查询集群的定时作业信息。

系统会将每次作业的执行情况保存在目录 `<homeDir>/batchJobs` 下，包括定时作业的运行日志和返回值。运行日志保存在 `<jodId>.msg` 文件中；如果定时任务有返回值，它会保存在 `<jobId>.object` 文件中。可以使用函数 [getJobMessage](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getJobMessage.html) 查看每个作业的运行日志，使用函数 [getJobReturn](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getJobReturn.html) 查看作业的返回值。

注意 *jobID* 的取值：

1. 创建作业时，若指定的 *jobId* 与已有定时作业的作业 ID 重复，系统将为其添加后缀直到作业 ID 不重复；
2. 对多次执行的作业，每次执行定时作业时，作业 ID 是不一样的，需要用函数 [getRecentJobs](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getRecentJobs.html) 查看已完成的定时作业。

- 示例5：定义定时作业，查询定时作业的信息。

```
def foo(){
	print "test scheduled job at"+ now()
	return now()
}
scheduleJob(`testJob, "foo", foo, 17:00m+0..2*30, today(), today(), 'D');
```

运行 getRecentJobs()得到示例5的作业信息。

```
jobId	            jobDesc	startTime	            endTime
------              ------- ----------------------- ----------------------
testJob	            foo 	2020.02.14T17:00:23.636	2020.02.14T17:00:23.639
testJob20200214	    foo 	2020.02.14T17:30:23.908	2020.02.14T17:30:23.910
testJob20200214000  foo 	2020.02.14T18:00:23.148	2020.02.14T18:00:26.749
```

第一次执行的作业 ID 是“testJob”，第二次执行的作业 ID 是“testJob20200214”，……，每次执行的作业 ID 不同。根据相应的作业ID，我们可用函数 getJobMessage 和 getJobReturn 查看第3次作业的执行情况。

```
>getJobMessage(`testJob20200214000);
2020-02-14 18:00:23.148629 Start the job [testJob20200214000]: foo
2020-02-14 18:00:23.148721 test the scheduled job at 2020.02.14T18:00:23.148
2020-02-14 18:00:26.749111 The job is done.

>getJobReturn(`testJob20200214000);
2020.02.14T18:00:23.148
```

## 3. 删除定时作业

使用函数 [deleteScheduledJob](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/d/deleteScheduledJob.html) 删除定时作业。语法如下：

```
deleteScheduledJob(jobId)
```

注意：

- 删除前可以使用函数 [getScheduledJobs](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getScheduledJobs.html) 得到作业 ID。
- 使用该命令时，管理员可以删除其他用户创建的任务，非管理员用户只能删除自己创建的任务。

## 4. 定时作业运行时的权限

定时作业运行时的权限由用户创建定时作业时的登录身份的权限决定。用户创建定时作业时，需要确保其有权限访问待使用的资源。比如当登录用户不是授权用户，就不能访问集群的分布式表，否则执行作业时就会出错。

- 示例6：用户 guestUser1 创建定时作业。本例中用户 guestUser1 没有访问 DFS 分布式表的权限。

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

作业执行后，使用函数 getJobMessage(`guestGetDfsjob) 进行查询。结果如下所示，定时作业没有权限读取分布式数据库：

```
2020-02-14 21:03:23.193039 Start the job [guestGetDfsjob]: dfs read
2020-02-14 21:03:23.193092 Test the scheduled job at 2020.02.14T21:03:23.193
2020-02-14 21:03:23.194914 Not granted to read table dfs://FuturesContract/tb
```

因此，若定时作业要访问集群中的某个分布式表，需要先以管理员 (admin) 或其他授权用户身份登录。具体操作可以通过函数 [login](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/l/login.html) 完成。

注意：

从上述日志中可以发现，访问分布式表后的语句没有被执行，即作业执行过程中若遇到错误，执行就会中断。为防止出现异常而停止执行后续脚本，可使用 [try-catch ](https://www.dolphindb.cn/cn/help/ProgrammingStatements/tryCatch.html?highlight=try%20catch)语句俘获异常。代码运行中可以使用函数 print 打印运行信息，输出结果记录在日志文件 `<jobId>.msg` 中。

## 5. 定时作业的序列化与反序列化

定时作业创建后，作业的ID、描述信息、起始时间、作业频率、作业函数及创建用户（userID）将被序列化并保存到当前节点的磁盘文件中，存储路径为`<homeDir>/sysmgmt/jobEditlog.meta`。在节点重启时，系统将对文件反序列化以进行加载。

作业函数用一个 DolphinDB 的函数来表示，函数的定义包括了一系列语句，这些语句又会调用其他函数和一些全局类对象，譬如共享变量(shared variable)。共享变量序列化时用名称来表示。反序列化时，共享变量必须存在于内存中，否则会失败。

作业函数或其依赖的函数根据是否经过编译可以分为两类：

1. 经过编译的函数，包括内置函数和插件函数；
2. 脚本函数，包括自定义函数、函数视图和模块中的函数等。

这两类函数的序列化方法不同，下面分别进行说明。

### 5.1 经过编译的函数

对经过编译的函数进行序列化，只序列化函数名称和模块名称。反序列化时，会在系统中搜索这些模块及函数，若搜索不到则失败。

若已创建的定时作业中使用了插件函数，必须在反序列化前进行预先加载，否则系统启动失败。系统与定时作业的相关组件资源的初始化顺序依次是：系统级初始化脚本（dolphindb.dos），函数视图（function view），用户级启动脚本（startup.dos）和定时作业。示例7进行代码演示。

- 示例7：在作业函数 jobDemo 中用到了 odbc 插件。

```
use odbc
def jobDemo(){
	conn = odbc::connect("dsn=mysql_factorDBURL");
}
scheduleJob("job demo","example of init",jobDemo,15:48m, 2019.01.01, 2020.12.31, 'D')
```

创建定时作业后，由于重新启动系统时没有加载插件 odbc，所以读取定时作业时，系统无法识别函数 odbc，输出下列日志后退出：

```
<ERROR>:Failed to unmarshall the job [job demo]. Failed to deserialize assign statement. Invalid message format
```

若在启动脚本中加入下列代码以加载插件 odbc，系统将顺利启动：

```
loadPlugin("plugins/odbc/odbc.cfg")
```

### 5.2 脚本函数

脚本函数会序列化函数参数以及函数定义的每一个语句。语句中若又包含了依赖的脚本函数，也会序列化这些依赖函数的定义。

创建定时作业后，若这些脚本函数被删除或被修改了，或它依赖的脚本函数被修改，不影响定时作业运行。若希望定时作业按新的函数执行，就需要先删除定时作业、然后重新创建定时作业，否则会运行已序列化的函数。其中要注意关联的函数也需要重新定义。下面举例说明：

下面进行举例说明：

- 示例8：创建定时作业后，重新定义作业函数 f。

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

定时作业执行后，使用函数 getJobMessage(`test)得到如下信息，从中看到定时作业执行的仍然是旧的自定义函数：

```
2020-02-14 11:05:53.382225 Start the job [test]: f
2020-02-14 11:05:53.382267 The old function is called 
2020-02-14 11:05:53.382277 The job is done.
```

- 示例9：作业函数是函数视图 fv，fv 调用函数 foo，在创建定时作业后重新定义依赖的函数 foo，函数视图也重新生成。

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

定时作业执行后，使用函数 getJobMessage(`testFvJob)得到如下信息，从中看到定时作业执行的仍然是旧的函数：

```
2020-02-14 11:36:23.069892 Start the job [testFvJob]: fv
2020-02-14 11:36:23.069939 The old function is called 
2020-02-14 11:36:23.069951 The job is done.
```

- 示例10：创建一个模块 printLog.dos。

```
module printLog
def printLogs(logText){
	writeLog(string(now()) + " : " + logText)
	print "The old function is called"
}
```

然后创建一个定时作业调用函数 printLog::printLogs：

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

定时作业执行后，使用函数 getJobMessage(`testModule)得到如下信息，从中看到定时作业执行的仍然是旧的函数：

```
2020-02-14 13:32:22.870855 Start the job [testModule]: f5
2020-02-14 13:32:22.871097 The old function is called
2020-02-14 13:32:22.871106 The job is done.
```

## 6. 定时运行脚本文件

在创建定时作业时，若作业函数是使用函数 run 运行一个脚本文件，因为序列化时只保存文件名，不保存文件内容，所以需要把依赖的自定义函数都放到脚本文件中，否则会因为找不到自定义的函数而执行失败。

- 示例11：创建一个脚本文件 testjob.dos：

```
foo()
```

然后在 DolphinDB GUI 中执行下列脚本：

```
def foo(){
	print ("Hello world!")
}
run "/home/user/testjob.dos"
```

结果显示可以正常执行：

```
2020.02.14 13:47:00.992: executing code (line 104-108)...
Hello world!
```

再创建定时作业使用函数 run 运行该脚本文件，代码如下所示：

```
scheduleJob(`dailyfoofile1, "Daily Job 1", run {"/home/user/testjob.dos"}, 16:14m, 2020.01.01, 2020.12.31, `D`);
```

直接运行作业，将会发生如下异常：

```
Exception was raised when running the script [/home/user/testjob.dos]:Syntax Error: [line #3] Cannot recognize the token foo
```

异常原因：函数 foo 的定义和定时作业的执行不在同一个会话 (session) 中，作业执行时找不到函数定义。

把函数 foo 的定义放到脚本文件中，修改 testjob.dos 文件内容如下：

```
def foo(){
	print ("Hello world!")
}
foo()
```

再重新创建定时作业运行这个脚本文件，即可顺利完成。

## 7. 常见故障及排除

| **常见故障**                                 | **排除操作**                                 |
| ---------------------------------------- | ---------------------------------------- |
| 作业函数引用了共享变量，但是作业加载时找不到该共享变量。             | 建议在用户的启动脚本中定义该共享变量。                    |
| 作业函数引用了插件中的函数，但是作业加载前没有加载该插件。            | 建议在用户的启动脚本中定义加载该插件。                    |
| 定时运行一个脚本文件，执行时找不到依赖的函数。                  | 脚本文件必须包含依赖的自定义函数。                        |
| 创建定时作业的用户没有访问分布式数据库表的权限。                 | 授权该用户访问相应数据库的权限。                         |
| 在启动脚本中使用函数 [scheduleJob](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/s/scheduleJob.html),  [getScheduledJobs](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/g/getScheduledJobs.html) 和 [deleteScheduledJob](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/d/deleteScheduledJob.html) 时抛出异常。 | 节点启动时，定时作业在启动脚本之后加载，所以不能在启动脚本中使用与定时作业相关的任何功能，包括函数scheduleJob, getScheduledJobs 和deleteScheduledJob。如果需要在系统启动时初始化某些定时作业相关的任务，只能在初始化定时任务模块完成后通过 postStart 脚本执行。postStart 脚本文件路径由参数 postStart 指定。`if(getScheduledJobs().jobDesc.find("daily resub") == -1){	scheduleJob(jobId=`daily, jobDesc="daily resub", jobFunc=run{"/home/appadmin/server/resubJob.dos"}, scheduleTime=08:30m, startDate=2021.08.30, endDate=2023.12.01, frequency='D')	}` |

特殊情况下，可能出现在系统重启时定时作业加载失败，甚至系统无法启动的情况。尤其是版本升级时，可能因为内置函数、插件函数等函数接口变化导致作业无法加载，或者出现一些兼容性 bug 导致系统重启失败。因此，建议用户在开发时保留定义定时作业的脚本。若因定时任务导致系统无法启动，可以先删除定时作业的序列化文件`<homeDir>/sysmgmt/jobEditlog.meta`，在系统重启后再重新创建定时作业。
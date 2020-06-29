## DolphinDB模块复用教程
在软件团队开发项目中，要提升开发效率和质量，代码必然要进行封装和重用。在使用DolphinDB的脚本进行开发时，可以使用`module`和`use`方法，来声明和使用可重用模块。

### 1. Module(模块)介绍
在DolphinDB中，模块是指只包含函数定义的代码包。它具有以下特点：

* 以.dos作为模块文件的后缀，dos是"dolphindb script"的缩写
* 模块文件保存在DolphinDB节点的 [home]/modules目录下
* 模块文件第一行以声明模块语句`module moduleName`开头
* 模块文件内容仅包含函数定义

### 2. 定义模块

#### 2.1 创建模块目录

默认情况下，所有的模块定义在[home]/modules目录下，[home]由系统配置参数`home`决定，可以通过`getHomeDir()`函数获取。比如DolphinDB节点的home目录为:

```bash
/root/DolphinDB/server
```

那么我们需要在该目录下创建modules子目录来保存模块文件，最终模块目录为:

```bash
/home/root/DolphinDB/server/modules
```

#### 2.2 创建模块文件

在modules目录下创建以.dos为后缀的模块文件，比如FileLog.dos。模块文件的第一行必须是模块声明语句。模块声明语句的语法如下：

```
module moduleName
```

moduleName必须与模块文件的名称一致，比如在FileLog.dos中声明模块：

```
module FileLog
```

声明模块后，我们可以开始编写模块代码。例如，FileLog.dos的内容如下：

```
module FileLog
//向指定日志文件写入日志
def appendLog(filePath, logText){
	f = file(filePath,"a+")
	f.writeLine(string(now()) + " : " + logText)
	f.close()
}
```

在模块文件中，**仅允许封装函数定义，其他非函数定义代码将被忽略**。

### 3. 导入模块

在DolphinDB中，使用`use`关键字来导入一个模块。注意，`use`关键字导入的模块是会话隔离的，仅对当前会话有效。导入模块后，我们可以通过以下两种方式来使用模块内的自定义函数：

(1)直接使用模块中的函数：

```
use FileLog
appendLog("mylog.txt", "test my log")
```

(2)通过完整路径来调用模块中的函数：

```
use FileLog
FileLog::appendLog("mylog.txt", "test my log")
```

### 4. 规划模块

DolphinDB引入了命名空间的概念，支持对模块进行分类和规划。

#### 4.1 声明模块命名空间

如果我们需要对模块进行分类，可以通过多级路径为规划模块的命名空间。例如，现有两个模块FileLog和DateUtil，它们的存放路径分别为modules/system/log/FileLog.dos和modules/system/temperal/DateUtil.dos，那么这两个模块相应的声明语句如下：

* modules/system/log/FileLog.dos
```
module system::log::FileLog
```

* modules/system/temperal/DateUtil.dos
```
module system::temperal::DateUtil
```

#### 4.2 调用命名空间模块

我们可以在`use`关键字后加完整路径来导入命名空间下的模块。例如，导入FileLog模块：

```
use system::log::FileLog
//全路径调用
system::log::FileLog::appendLog("mylog.txt", "test my log")
//直接调用已导入模块中的函数
appendLog("mylog.txt", "test my log")

```

### 5. GUI中远程调试模块

当工作机和DolphinDB服务器不是同一台机器时，我们在工作机上编辑的模块代码，不能直接在远程服务器的DolphinDB上通过`use`导入，需要先将模块文件上传到[home]/modules的对应目录，才能通过`use`调用模块。

DolphinDB GUI从0.99.2版本开始提供了远程同步模块的功能，具体用法如下图所示：

![image](images/gui/module_sync.png)

此操作会将Modules目录下的所有文件和子目录同步到GUI连接的DolphinDB节点的[home]/modules目录下，同步完成后，就可以在Server上直接执行`use`代码导入模块。

### 6. 注意事项

#### 6.1 同名函数定义规则

不同模块可以定义相同名字的函数。如果使用全路径调用函数，DolphinDB可以通过模块命名空间来区分函数名。如果直接调用函数：

* 如果已导入的模块中只有一个模块包含该函数，DolphinDB会调用该模块的函数。

* 如果已导入的模块中有多个模块包含该函数，DolphinDB解析脚本时会以下抛出异常：
```
Modules [Module1] and [Module2] contain function [functionName]. Please use module name to qualify the function.
```
* 如果已导入模块中与自定义函数重名，系统会默认使用模块中的函数。如果要调用自定义函数，需要声明命名空间。自定义函数和内置函数的默认命名空间为根目录，用两个冒号表示。比如：

```
//定义模块
module sys
def myfunc(){
 return 3
}

//自定义函数
login("admin","123456")
def myfunc(){
 return 1
}
addFunctionView(myfunc)

//调用
use sys
sys::myfunc() //调用模块的函数
myfunc() //调用模块的函数
::myfunc() //调用自定义函数
```

* 如果已导入的模块中不包含该函数，DolphinDB会在系统内置函数中搜索该函数。如果内置函数中也没有该函数，将抛出函数为定义的异常。

#### 6.2 刷新模块定义

在开发阶段调试模块代码时，开发人员需要反复修改模块代码并刷新定义，此时可以重新打开模块文件并全选执行模块代码即可，这种方法仅对当前会话有效。

#### 6.3 模块间互相调用
模块之间可以单向引用，比如模块a 引用 b , b 引用 c。模块之间不支持交叉引用，比如模块a 引用 b， 模块b又引用a。

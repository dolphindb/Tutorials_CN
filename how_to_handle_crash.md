# DolphinDB教程：如何正确定位节点宕机的原因

在使用DolphinDB时，有时客户端会打印运行日志：Connection refused 。这时若用ps命令去linux操作系统上查一下，会发现dolphindb进程不见了。本教程针对节点宕机的各种场景进行定位和分析，主要内容有：

- [1.查看节点日志排查是否人为原因 ](#1-查看节点日志排查是否人为原因)
- [2.查看操作系统日志排查OOM killer](#2-查看操作系统日志排查oom-killer)
- [3.查看core文件](#3-查看core文件)
  - [3.1 Core文件设置](#31-Core文件设置)
    - [3.1.1控制Core文件生成](#311-控制core文件生成)
    - [3.1.2修改core文件保存路径](#312-修改core文件保存路径)
    - [3.1.3测试Core文件是否能够生成](#313-测试core文件是否能够生成)
  - [3.2 gdb调试Core文件](#32- gdb调试core文件)
  - [3.3  Core文件不生成的情况](#33-core文件不生成的情况)
- [4.避免节点宕机](#4-避免节点宕机)
  - [4.1 监控磁盘容量，避免磁盘满](#41-监控磁盘容量避免磁盘满)
  - [4.2 监控内存使用，避免内存高位运行](#42-监控内存使用避免内存高位运行)
  - [4.3 避免多线程并发访问内存表](#43-避免多线程并发访问内存表)
  - [4.4 自定义开发插件俘获异常](#44-自定义开发插件俘获异常)
- [5.总结](#5-总结)

## 1. 查看节点日志排查是否人为原因

DolphinDB每个节点的运行情况会记录在相应的日志文件中。通过分析日志，能有效地掌握Dolphindb运行状况，发现和定位一些错误原因。当节点宕机时，被自己或同伴等人为关闭的情形常见有以下三种：

* __Web集群管理界面上或用`stopDataNode`函数手动停止节点__
* __操作系统kill命令杀死节点进程__
* __License有效期到期关机__

排查这些原因，可查看节点在退出前是否打印了日志：MainServer shutdown。下面假设宕机节点为`datanode1`，操作命令示例如下：

```shell
less datanode1.log|grep "MainServer shutdown"
```

若命令执行结果如下图，并且时间点也合理，那就可初步认定为系统主动退出。

![](./images/handle%20shutdown/handle_shutdown3-4.png)


第一种Web集群管理界面上或用`stopDataNode`函数手动停止节点的情形，可继续查看控制节点日志`controller.log`，操作命令示例如下：

```shell
less controller.log|grep "has gone offline"
```

![](./images/handle%20shutdown/handle_shutdown3-5.png)

若日志产生的信息如上图，则可判断为通过Web界面或或用`stopDataNode`函数主动关机。

第二种操作系统kill命令杀死节点进程的情形，查看对应宕机节点运行日志是否含有Received signal的信息。操作命令示例如下：

```shell
less datanode1.log|grep "Received signal"
```

![](./images/handle%20shutdown/handle_shutdown3-6.png)

若有相应时间点如上图所示信息，则可判定为被kill命令杀掉进程。

第三种License有效期到期关机的情形，可查看节点日志是否打印了：The license has expired。操作命令示例如下：

![](./images/handle%20shutdown/handle_shutdown3-7.png)

则可以判断是license到期退出。这里要注意的是，DolphinDB 1.20.20之前版本不支持在线更新license，更换license时，不仅需要重启数据节点，也需要重启控制节点和代理节点。若未重启代理节点或控制节点，会导致节点退出。


如果在节点宕机时，未查询到上述的日志信息，需进一步查看相应操作系统日志。


> 注意：在实践过程中常见的问题是找不到节点日志存放在哪里。单节点模式默认在安装目录server下，文件名为dolphindb.log，集群默认在server/log目录下。节点的日志文件只能在命令行中通过logFile配置项指定。若是集群，若有节点在运行，可通过如下ps命令查看每一个节点对应的log生成位置，其中logFile参数表示日志文件的路径和名称：

![](./images/handle%20shutdown/handle_shutdown2-1.png)


## 2. 查看操作系统日志排查OOM killer

Linux 内核有个机制叫OOM killer(Out Of Memory killer)，该机制会监控那些占用内存过大，尤其是瞬间占用内存很快的进程，然后防止内存耗尽而自动把该进程杀掉。排查OOM killer可用dmesg命令，示例如下：
	

```
dmesg -T|grep dolphindb
```

![](./images/handle%20shutdown/handle_shutdown1-3.png)

如上图，若出现了“Out of memory: Kill process”这样的字样，那说明DolphinDB使用的内存超过了操作系统所剩余的空闲内存，导致操作系统杀死了DolphinDB进程。解决这种问题的办法是：通过参数maxMemSize(单节点模式修改dolphindb.cfg，集群模式修改cluster.cfg)设定节点的最大内存使用量。这个参数设置要合理，如果设置太小，会严重限制集群的性能，如果设置太大，可能会触发操作系统杀掉进程。若机器内存为16GB，并且只部署1个节点，建议将该参数设置为12GB左右。

使用上述dmesg命令显示日志信息时，若看到如下图所示的“segfault”，那就发生了段错误：

![](./images/handle%20shutdown/handle_shutdown1-2.png)

段错误就是指应用程序访问的内存超出了系统所给的内存空间。可能导致段错误的原因有：

* 访问系统数据区，最常见就是操作0x00地址的指针
* 内存越界(数组越界，变量类型不一致等)： 访问到不属于你的内存区域
* 栈溢出(Linux一般默认栈空间大小为8192kb，ulimit -s命令查看)

此时若正确开启了core功能，会生成相应的core文件，然后就可以用gdb对core文件进行调试。

## 3. 查看core文件

当程序运行的过程中异常终止或崩溃，操作系统会将程序当时的内存状态记录下来，保存在一个文件中，这种行为就叫做Core Dump（中文有的翻译成“核心转储”)。可认为 Core Dump 是“内存快照”，但实际上，除了内存信息之外，还有些关键的程序运行状态也会同时 dump 下来，例如寄存器信息（包括程序指针、栈指针等）、内存管理信息、其他处理器和操作系统状态和信息。Core Dump 对于编程人员诊断和调试程序是非常有帮助的，因为对于有些程序错误是很难重现的，例如指针异常，而 Core Dump 文件可以再现程序出错时的情景。文件默认生成位置与可执行程序位于同一目录下，文件名为core.\*\**,其中\***是某一数字。

### 3.1 Core文件设置

#### 3.1.1 控制Core文件生成

首先在终端中输入```ulimit -c```查看core文件是否被开启。若结果为0，则表示关闭了此功能，不会生成core文件。若不为"unlimited",则用下列命令设置：

 ```
 ulimit -c unlimited
```
`unlimited`表示core文件的大小不受限制。以上配置只对当前会话起作用，下次重新登陆后，还得重新配置。要想配置永久生效有两种方式：

* 在/etc/profile 中增加一行```ulimit -S -c unlimited >/dev/null 2>&1``` 后保存退出，重启服务器，或者不重启服务器，使用```source /etc/profile```使配置马上生效。`/etc/profile`对所有用户有效，若想只针对某一用户有效，则修改此用户的`~/.bashrc`或者`~/.bash_profile`文件。
* 在`/etc/security/limits.conf`最后增加如下两行记录:为所有用户开启了Core Dump

![](./images/handle%20shutdown/handle_shutdown3-1.png)

> 注意： 由于DolphinDB数据节点是通过代理节点进行启动的，在不重启代理节点的情况下，开启core功能无法生效，开启core功能后需要重启代理节点再重启数据节点。

#### 3.1.2 修改core文件保存路径

core默认的文件名称是core.pid，pid指的是产生段错误的程序的进程号。默认路径是产生段错误的程序的当前目录。

`/proc/sys/kernel/core_uses_pid`可控制产生的core文件的文件名中是否添加pid作为扩展，如果添加则文件内容为1，否则为0。可通过以下命令修改此文件：
```
echo "1" > /proc/sys/kernel/core_uses_pid 
```
`/proc/sys/kernel/core_pattern`可设置core文件保存的位置和文件名,可通过以下命令将core文件存放到/corefile目录下，产生的文件名为：core-命令名-pid-时间戳: 
```
 echo /corefile/core-%e-%p-%t > /proc/sys/kernel/core_pattern  
```
**以下是参数列表:**  

* %p - insert pid into filename 添加pid  
* %u - insert current uid into filename 添加当前uid  
* %g - insert current gid into filename 添加当前gid 
* %s - insert signal that caused the coredump into the filename 添加导致产生core的信号  
* %t - insert UNIX time that the coredump occurred into filename 添加core文件生成时的unix时间  
* %h - insert hostname where the coredump happened into filename 添加主机名  
* %e - insert coredumping executable name into filename 添加命令名。  

一般情况下，无需修改，按照默认的方式即可。

> 注意：
>
> 设置core文件保存路径时首先要先创建这个路径，其次特别要注意所在磁盘的剩余空间大小，不要影响DolphinDB元数据、分区数据的存储。

#### 3.1.3 测试Core文件是否能够生成

使用下列命令对某进程（用ps查到进程号为24758）使用SIGSEGV 信号，可以kill掉这个进程：

```
kill -s SIGSEGV 24758
```
若在core文件夹下生成了core文件，则设置正确有效。

### 3.2 gdb调试Core文件

若gdb没有安装，需要先安装，以Centos系统为例，安装gdb用命令如下：

``````
yum install gdb
``````
gdb调试命令格式：`gdb [exec file] [core file]`,然后执行bt看堆栈信息：

![](./images/handle%20shutdown/handle_shutdown3-2.png)

### 3.3 Core文件不生成的情况

Linux 中信号是一种异步事件处理的机制，每种信号对应有其默认的操作，你可以在 **[这里](http://man7.org/linux/man-pages/man7/signal.7.html)** 查看 Linux 系统提供的信号以及默认处理。默认操作主要包括忽略该信号（Ingore）、暂停进程（Stop）、终止进程（Terminate）、终止并发生core dump（core）等。如果我们信号均是采用默认操作，那么，以下列出几种信号，它们在发生时会产生 core dump:

| Signal  | Action | Comment                                                      |
| ------- | ------ | ------------------------------------------------------------ |
| SIGQUIT | Core   | Quit from keyboard                                           |
| SIGILL  | Core   | Illegal Instruction                                          |
| SIGABRT | Core   | Abort signal from [abort](http://man7.org/linux/man-pages/man3/abort.3.html) |
| SIGSEGV | Core   | Invalid memory reference                                     |
| SIGTRAP | Core   | Trace/breakpoint trap                                        |

当然不仅限于上面的几种信号。这就是为什么我们使用 `Ctrl+z` 来挂起一个进程或者 `Ctrl+C` 结束一个进程均不会产生 core dump，因为前者会向进程发出 **SIGTSTP** 信号，该信号的默认操作为暂停进程（Stop Process）；后者会向进程发出**SIGINT** 信号，该信号默认操作为终止进程（Terminate Process）。同样上面提到的 `kill -9` 命令会发出 **SIGKILL** 命令，该命令默认为终止进程，同样不会产生Core文件。

另外在下列条件下不产生core文件：

( a )进程是设置-用户-ID，而且当前用户并非程序文件的所有者；

( b )进程是设置-组-ID，而且当前用户并非该程序文件的组所有者；

( c )用户没有写当前工作目录的许可权；

( d )文件太大。core文件的许可权(假定该文件在此之前并不存在)通常是用户读/写，组读和其他读。

> 注意：
>
> 查看dolphindb对应日志，假设日志信息有:Received signal 15，如下图，即用SIGTERM(kill命令默认信号)杀死dolphindb进程，不生成core文件。

![](./images/handle%20shutdown/handle_shutdown3-6.png)

## 4. 避免节点宕机

在企业的生产环境中，DolphinDB往往作为流数据中心以及历史数据仓库，为业务人员提供数据查询和计算。当用户较多时，不当的使用容易造成Server端宕机。可遵循以下建议，尽量避免异常使用Dolphindb。

### 4.1 监控磁盘容量，避免磁盘满

当硬盘的可用空间小到一定程度时，就会造成系统的交换文件、临时文件缺乏可用空间，降低了系统的运行效率。更为重要的是由于我们平时频繁在硬盘上储存、删除各种软件，使得硬盘的可用空间变得支离破碎，因此系统在存储文件时常常没有按连续的顺序存放，这将导致系统存储和读取文件时频繁移动磁头，极大地降低了系统的运行速度。下面以Linux为例，监控磁盘容量，当硬盘空间不够时，我们很关心哪些目录或文件比较大，步骤如下：

（1）查看目录的剩余空间大小。

```
df -h 查看整台服务器的硬盘使用情况
du -lh --max-depth=1 : 查看当前目录下一级子文件和子目录占用的磁盘容量。
```

（2）Linux系统下查找大文件或目录

当硬盘空间不够时，我们就很关心哪些目录或文件比较大，看看能否干掉一些了，怎么才能知道呢？以易读的格式显示指定目录或文件的大小，-s选项指定对于目录不详细显示每个子目录或文件的大小

```
du -sh [dirname|filename]
//当前目录的大小：du -sh .
//当前目录下个文件或目录的大小：du -sh *
//显示前10个占用空间最大的文件或目录：
du -s * | sort -nr | head
```

（3）删除对应无用大文件

### 4.2 监控内存使用，避免内存高位运行

内存高位运行容易发生OOM，如何监控和高效使用内存详见**[DolphinDB教程：内存管理](./memory_management.md)**中第6节与第七节

### 4.3 避免多线程并发访问内存表

DolphinDB内置编程语言，在操作访问表时有一些规则，如[内存表详解](./in_memory_table.md#42-%E5%B9%B6%E5%8F%91%E6%80%A7)第4.2节就说明了有些内存表不能并发写入。若不遵守规则，就容易奔溃。下例创建了一个以id字段进行RANGE分区的常规内存表：

```
t=table(1:0,`id`val,[INT,INT])
db=database("",RANGE,1 101 201 301)
pt=db.createPartitionedTable(t,`pt,`id)
```
下面的代码启动了两个写入任务，并且写入的分区相同，运行后即导致系统崩溃。
```
def writeData(mutable t,id,batchSize,n){
	for(i in 1..n){
		idv=take(id,batchSize)
		valv=rand(100,batchSize)
		tmp=table(idv,valv)
		t.append!(tmp)
	}
}

job1=submitJob("write1","",writeData,pt,1..300,1000,1000)
job2=submitJob("write2","",writeData,pt,1..300,1000,1000)
```
产生的core文件如下图：

![](./images/handle%20shutdown/handle_shutdown3-2.png)

### 4.4 自定义开发插件俘获异常

DolphinDB支持用户自己开发插件以扩展系统功能。插件与DolphinDB server在同一个进程中运行，若插件奔溃，那整个系统就会奔溃。因此在开发的插件时候要注意完善错误检测机制，除了插件函数所在线程可以抛出异常（server在调用插件函数时俘获了异常），其他线程都必须自己俘获异常，并不得抛出异常。详情请参阅[DolphinDB Plugin](https://gitee.com/dolphindb/DolphinDBPlugin/tree/master#dolphindb-plugin)。

## 5. 总结

分布式数据库DolphinDB设计十分复杂，发生宕机的情况各有不同，若发生节点宕机，请按本文所述步骤一步步排查：

* 先排查是否人为原因，如是否为通过Web集群管理界面或用stopDataNode函数手动停止节点，是否为用kill命令杀死节点进程，是否是License有效期到期退出等，当人为导致数据库宕机时，相关的记录信息都会记录在运行日志中，请检查对应时间点查看是否有相应的操作进行排查即可；
* 其次排查是否因为内存耗尽而被操作系统杀掉。排查OOM killer可查看操作系统日志；
* 再次检查一下编写的脚本是否有使用不当，如多线程并发访问了没有共享的分区表、插件没有俘获一些异常等；
* 最后请查看core文件，用gdb调试获取堆栈信息。若确定系统有问题，请保存节点日志文件、操作系统日志和core文件，并及时与DolphinDB工程师联系。
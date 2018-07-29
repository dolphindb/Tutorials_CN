### DolphinDB 单节点部署

在单节点运行DolphinDB，只需下载DolphinDB软件包，解压缩后即可运行。

例如解压到如下目录

```
/DolphinDB
```

#### 1. 软件授权许可更新

如果用户拿到了企业版试用授权许可，只需用其替换如下文件即可。

```
/DolphinDB/server/dolphindb.lic
```

#### 2. 运行 DolphinDB Server

进入server目录 /DolphinDB/server/, 运行dolphindb

Linux: 执行以下指令
```
./dolphindb
```
Windows: 运行dolphindb.exe

Linux 后台执行dolphindb，执行以下指令:
```
nohup ./dolphindb -console 0 &
```
注意：该场景下，如果要使得dolphindb后台运行，除了命令行首尾加"nohup" 和 "&" 外，参数 -console 0 也是必须的，如果不加该参数，会导致dolphindb运行一段时间后自动退出。 原因是如果不加 -console 0,dolpindb默认会从当前标准输入读取命令行，而nohup重定向了标准输入为/dev/null，因此使得程序一直能成功读取到内容为空的命令，无限循环，最终内存耗尽，被操作系统强制终止。

系统默认端口号是8848. 如果需要指定其它端口可以通过如下命令行：

Linux:
```
./dolphindb -localhost:8900:local8900
```

Windows:
```
dolphindb.exe -localhost:8900:local8900
```

软件授权书指定 DolphinDB 可用的最大内存。用户也可以根据实际情况来调低此上限。这个设置在启动dophindb的时候可以通过参数 -maxMem 来调整，以GB为单位。

Linux:
```
./dolphindb -localHost:8900:local8900 -maxMem 32
```
Windows:
```
dolphindb.exe -localHost:8900:local8900 -maxMem 32
```


#### 3. 网络连接到DolphinDB Server

到浏览器中输入(目前支持浏览器为Chrome与Firefox)：localhost:8848 (如果换成其它端口号，请修改为相应端口号)


#### 4. 通过网络界面运行DolphinDB脚本

在DolphinDB notebook的编辑器窗口输入以下DolphinDB代码。下图展示了运行结果。
```
table(1..5 as id, 6..10 as v)
```
![](images/single_web.JPG)


#### 5. 更多详细信息，请参阅DolphinDB帮助文档
中文

http://dolphindb.com/cn/help/

英文

http://dolphindb.com/help/

### DolphinDB 单节点部署

在单节点运行DolphinDB，只需下载DolphinDB软件包，解压缩后即可运行。

例如解压到如下目录：

```
/DolphinDB
```

#### 1. 软件授权许可更新

如果用户拿到企业版试用授权许可，只需用其替换如下文件即可。

```
/DolphinDB/server/dolphindb.lic
```

#### 2. 运行DolphinDB Server

进入server目录 /DolphinDB/server/, 运行dolphindb。

在运行dolphindb可执行文件前，需要修改文件权限：

```
chmod 777 dolphindb
```

在Linux环境中可执行以下指令：
```
./dolphindb
```
在Linux后台执行dolphindb，可执行以下指令:
```
nohup ./dolphindb -console 0 &
```

建议通过Linux命令nohup（头）和 &（尾）启动为后台运行模式，这样即使终端失去连接，DolphinDB也会持续运行。 

“-console”默认是为 1，如果要设置为后台运行，必须要设置为0（"-console 0")，否则系统运行一段时间后会自动退出。


在Windows环境中需运行dolphindb.exe。

系统默认端口号是8848。如果需要指定其它端口可以通过如下命令行：

Linux:
```
./dolphindb -localSite localhost:8900:local8900
```

Windows:
```
dolphindb.exe -localSite localhost:8900:local8900
```

软件授权书dolphindb.lic指定DolphinDB可用的最大内存，用户也可以根据实际情况来调低此上限。这个设置在启动dolphindb时可通过参数maxMemSize来调整，以GB为单位。

Linux:
```
./dolphindb -localSite localhost:8900:local8900 -maxMemSize 32
```
Windows:
```
dolphindb.exe -localSite localhost:8900:local8900 -maxMemSize 32
```


#### 3. 网络连接到DolphinDB Server

到浏览器中输入localhost:8848(或其它端口号)。目前支持Chrome与Firefox浏览器。


#### 4. 通过网络界面运行DolphinDB脚本

在DolphinDB notebook的编辑器窗口输入以下DolphinDB代码：
```
table(1..5 as id, 6..10 as v)
```
下图展示了运行结果。

![](images/single_web.JPG)


#### 5. 更多详细信息，请参阅DolphinDB帮助文档
中文

https://www.dolphindb.cn/cn/help/index.html

英文

http://dolphindb.com/help/

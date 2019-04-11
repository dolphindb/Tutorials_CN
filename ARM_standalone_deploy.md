DolphinDB ARM单板部署


#### 系统要求


操作系统：  Linux（内核3.10以上版本）

内存：        2GB以上

Flash：       8GB以上

支持的ARM CPU :  CORTEXA15   CORTEXA9   ARMV7  
             ARMV8  CORTEXA53  CORTEXA57  CORTEXA72  CORTEXA73  
             FALKOR  THUNDERX  THUNDERX2T99  TSV110 

DolphinDB ARM版使用的交叉编译器32位系统为arm-linux-gnueabihf4.9，64位系统为aarch64-linux-gnu_4.9.3。若用户在实际板子上运行时出现问题，请反馈给我们。


#### 1. 安装系统

从DolphinDB网站下载DolphinDB嵌入式ARM版软件包，解压缩后即可运行。

例如解压到如下目录：

```
/DolphinDB
```

#### 2. 软件授权许可更新

如果用户拿到企业版试用授权许可，只需用其替换如下文件即可。

```
/DolphinDB/server/dolphindb.lic
```

#### 3. 运行DolphinDB server

进入server目录 /DolphinDB/server/, 运行dolphindb。

在运行dolphindb可执行文件前，需要修改文件权限：

```
chmod 777 dolphindb
```

然后可在dolphindb.cfg文件中修改配置参数:

	系统默认端口号是8848。如果需要指定其它端口可以通过参数localSite设置，例如修改端口为8900：

```
localSite=localhost:8900:local8900
```
	可通过参数maxMemSize来指定DolphinDB可用的最大内存，以GB为单位，例如修改为0.8GB：

```
maxMemSize=0.8 
```
	参数regularArrayMemoryLimit设置数组的内存限制（以MB为单位）。该参数必须是2的指数幂。默认值是512。建议根据实际内存大小设置，例如修改为64MB：
```
regularArrayMemoryLimit=64
```

	另外建议根据闪存大小修改maxLogSize（当日志文件达到指定大小（单位为MB）时，系统会将日志文件存档。默认值是1024，最小值是100），例如修改为100MB：
```
maxLogSize=100

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



#### 4. 网络连接到DolphinDB server

到浏览器中输入设备ip地址:8848(或其它端口号)。目前支持Chrome与Firefox浏览器。请注意，在浏览器中连接DolphinDB server时，若10分钟内无命令执行，系统会自动关闭会话以释放DolphinDB系统资源。建议用户在DolphinDB GUI中编写代码与执行命令。DolphinDB GUI中的会话在用户关闭之前会一直存在。


#### 5. 通过网络界面运行DolphinDB脚本

在DolphinDB notebook的编辑器窗口输入以下DolphinDB代码：
```
table(1..5 as id, 6..10 as v)
```
下图展示了运行结果。

![](images/single_web.JPG)

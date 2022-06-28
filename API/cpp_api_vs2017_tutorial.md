# 用VS2017编译DolphinDB C++ API动态库

- [用VS2017编译DolphinDB C++ API动态库](#用vs2017编译dolphindb-c-api动态库)

  - [1. 环境准备](#1-环境准备)
    - [1.1 下载安装VS2017](#11-下载安装vs2017)
    - [1.2 安装Git](#12-安装git)
  - [2. 下载C++ API代码](#2-下载c-api代码)
  - [3. 创建和编译项目](#3-创建和编译项目)
    - [3.1 新建项目](#31-新建项目)
    - [3.2 添加源码到项目](#32-添加源码到项目)
    - [3.3 配置项目属性](#33-配置项目属性)
    - [3.4 编译动态库](#34-编译动态库)
  - [4. 案例验证](#4-案例验证)
    - [4.1 新建项目](#41-新建项目)
    - [4.2 导入例子代码](#42-导入例子代码)
    - [4.3 配置项目属性](#43-配置项目属性)
    - [4.4 编译和运行](#44-编译和运行)
  - [5. 说明](#5-说明)

  

> 本文示例的 DolphinDB C++ API 编译配置如下：
>
> * 编译环境：Visual Studio 2017
>
> * 编译模式：Release x64



## 1. 环境准备

### 1.1 下载安装Visual Studio 2017

下载链接：[Visual Studio 2017 15.9 Release Notes | Microsoft Docs](https://docs.microsoft.com/en-us/visualstudio/releasenotes/vs2017-relnotes)。

下载后双击一路默认安装即可。

### 1.2 安装Git

下载链接：[Git - Downloading Package](https://git-scm.com/download/win) 。

下载后双击一路默认安装即可，在cmd中运行`git --version`，显示如下图所示版本信息即表明安装成功。
![image](../images/vs2017/git.png?raw=true)

## 2. 下载C++ API代码

C++ API链接：[dolphindb/api-cplusplus](https://github.com/dolphindb/api-cplusplus)

在终端运行`git clone -b release130 https://github.com/dolphindb/api-cplusplus.git` 即可下载。

若 Github 网速较慢，可访问[国内镜像](https://gitee.com/dolphindb/api-cplusplus)。

> 注意:
> API 分支须与 DolphinDB Server 的版本相匹配，可通过 git 指令的 -b 指定版本对应的分支，即若 DolphinDB Server 是 1.30 版本，API 须切换到 release130 分支进行下载；若 DolphinDB Server 是 2.00 版本，API 须切换到 release200 分支下载，其他版本依此类推。

## 3. 创建和编译项目

### 3.1 新建项目

打开 Visual Studio 后，点击主菜单`文件` -> `新建` -> `项目`，弹出 `新建项目`对话框。在对话框左侧面板中的 Visual C++ 下选择`windows 桌面`，中间面板中选择`动态链接库(DLL)`，然后在下面编辑框中输入工程名称和保存路径，如下图所示：

![image](../images/vs2017/newProject.png?raw=true)

### 3.2 添加源码到项目

项目默认生成了一些框架代码文件，可如下图所示选中移除：

![image](../images/vs2017/delPch.png?raw=true)

然后选择主菜单`源文件` -> `添加` -> `现有项`，弹出`添加现有项`对话框,如下图所示，选中下载的 API 代码（src 子目录下所有 .cpp 文件和 .h 头文件），再点击`添加`按钮：

![image](../images/vs2017/selAllsrc.png?raw=true)

添加现有项成功后，源码会被添加到项目的源文件目录下，如下图所示：

![image](../images/vs2017/srcImported.png?raw=true)

### 3.3 配置项目属性

选中解决方案资源管理器中的项目 `cppApi130`，然后再选择主菜单`项目`->`属性`，弹出“属性页”对话框。或者右键该项目弹出菜单后选中`属性`。

![image](../images/vs2017/properties.png?raw=true)

在属性页对话框中先选择`配置`（Debug/Release)，再选择`平台`（x86/x64）。本文以 Release x64 为例，修改如下属性配置：

(1) 目标文件名

`常规` -> `目标文件名`：输入```libDolphinDBAPI```，用于配置生成解决方案后输出的动态库名（libDolphinDBAPI.dll）。

![image](../images/vs2017/destName.png?raw=true)

(2) 包含 SSL 的头文件和库目录

`VC++目录` -> 

* `包含目录`：添加 OpenSSL 的头文件目录。
* `库目录`：添加 OpenSSL 库目录。

目前 DolphinDB 默认支持 ssl 1.0，编译 SSL 可参阅 [Windows10+VS2017下安装和 编译openssl库](https://blog.csdn.net/tianse12/article/details/72844231)，或者使用已编译的 [Binaries](https://wiki.openssl.org/index.php/Binaries)。

DolphinDB api-cplusplus 项目也在 bin 子目录下提供了一个 SSL 库方便大家编译。

如下图所示即采用了 API 自身携带的 SSL 库：

![image](../images/vs2017/libDir.png?raw=true)

(3) 配置预处理宏定义

`C/C++` -> `预处理器`：添加选项```WIN32_LEAN_AND_MEAN;_WINSOCK_DEPRECATED_NO_WARNINGS;_CRT_SECURE_NO_WARNINGS;WINDOWS;NOMINMAX;```

![image](../images/vs2017/PreprocessorDefinitions.png?raw=true)

> 注意：
>
> - x86 平台须添加选项 `BIT32`。
> - SSL1.1 须添加选项 `SSL1_1`。

(4) 设置预编译头

`C/C++` -> `预编译头`：选择“不使用预编译头”。

![image](../images/vs2017/notprecompiledHeader.png?raw=true)

(5) 设置依赖项

`链接器` -> `输入` -> `附加依赖项` ：添加依赖项```ws2_32.lib;ssleay32MD.lib;libeay32MD.lib;```

![image](../images/vs2017/linker.png?raw=true)

### 3.4 编译动态库

选择主菜单`生成` -> `生成解决方案`即可编译。注意须在编译界面上方编译选项中选择 Debug/Release 和 x64/x86（如下图所示）。
![image](../images/vs2017/compile.png?raw=true)


> 注意:编译时选择 Release/x64 生成 lib 位于 ./x64/Release 目录，选择 Debug/x64 生成 lib 在 ./x64/Debug 目录，选择 Release/x86 生成 lib 在 ./Release 目录，选择 Debug/x86 生成 lib 在 ./Debug 目录。

## 4. 案例验证

该案例的将[时序数据库DolphinDB和TimescaleDB 性能对比测试报告](https://zhuanlan.zhihu.com/p/56982951)中提到的[小数据集(4.2GB)](https://timescaledata.blob.core.windows.net/datasets/devices_big.tar.gz)导入到DolphinDB分布式数据表中。对不方便下载4.2GB数据集的用户，本文也准备了一个[样本文件](../data/devices_big_readings_samples.zip)供下载。

程序的实现思路是利用开源软件 [rapidCsv](https://github.com/d99kris/rapidcsv) 读入csv文件，然后调用DolphinDB C++ API中的 [BatchTableWriter 对象](https://gitee.com/dolphindb/api-cplusplus/blob/master/README_CN.md#84-%E6%89%B9%E9%87%8F%E5%BC%82%E6%AD%A5%E5%86%99%E5%85%A5%E6%95%B0%E6%8D%AE)写入分布式表。

数据集包含了 3000 个设备在 10000 个时间间隔（2016.11.15 - 2016.11.18）内的电池、 内存和 CPU 等指标的统计信息。

分区方案：将 time 作为分区的第一个维度，每天一个分区共 4 个区，再将 device_id 作为分区的第二个维度，每天按 HASH 方式分 10 个区，每个分区所包含的原始数据大小约为 100 MB。

建库建表脚本如下：

```
login(`admin, `123456)
if (exists('dfs://iot') ) dropDatabase('dfs://iot')
db1 = database('',VALUE,2016.11.15..2016.11.18)
db2 = database('',HASH,[SYMBOL,10])
db = database('dfs://iot',COMPO,[db1,db2])

schema=table(1:0,`time`device_id`battery_level`battery_status`battery_temperature`bssid`cpu_avg_1min`cpu_avg_5min`cpu_avg_15min`mem_free`mem_used`rssi`ssid,
 [DATETIME,SYMBOL,INT,SYMBOL,DOUBLE,SYMBOL,DOUBLE,DOUBLE,DOUBLE,LONG,LONG,SHORT,SYMBOL])
 db.createPartitionedTable(schema,`readings,`time`device_id)
```

### 4.1 新建项目

打开 Visual Studio 后，点击主菜单`文件` -> `新建` -> `项目`，弹出“新建项目”对话框。在对话框左侧面板中的 Visual C++ 下选择 windows桌面，  中间面板中选择控制台应用，然后在下面编辑框中输入工程名称 appApiDemo 和保存路径，如下图所示：

![image](../images/vs2017/demoNewProject.png?raw=true)

### 4.2 导入例子代码

下载 [cppApiDemo.cpp](../script/vs2017/cppApiDemo.cpp) 并替换项目同名文件 `D:\DolphinDB\api-cplusplus\cppApiDemo\cppApiDemo\cppApiDemo.cpp`，下载 [rapidcsv.h](../script/vs2017/rapidcsv.h) 并拷贝到 cppApiDemo.cpp 所在目录。

### 4.3 配置项目属性

先选中解决方案资源管理器中的项目`cppApiDemo`，然后再选择主菜单 `项目` -> `属性`，或者右键解决方案资源管理器中的项目`cppApiDemo`，然后选择`属性`，弹出“属性页”对话框。

在属性页对话框中先选择 Debug 还是 Release 模式，再选择 x86 还是 x64 平台。本文以 Release x64 为例，修改如下属性配置：

(1) 包含头文件和库目录

`VC++目录` -> 

* `包含目录`：添加 OpenSSL 和 API 的头文件目录
* `库目录`：添加 OpenSSL 和 API 的库目录。

![image](../images/vs2017/demoLibDir.png?raw=true)

(2) 配置预处理宏定义

`C/C++` ->`预处理器`：添加选项```WIN32_LEAN_AND_MEAN;_WINSOCK_DEPRECATED_NO_WARNINGS;_CRT_SECURE_NO_WARNINGS;WINDOWS;NOMINMAX;```

> 注意：x86平台还要添加选项`BIT32`。

(3) 设置预编译头

`C/C++` -> `预编译头`：选择`不使用预编译头`。

(4) 设置依赖项

`链接器` -> `输入` -> `附加依赖项`：添加依赖项```libDolphinDBAPI.lib;ssleay32MD.lib;libeay32MD.lib;```

![image](../images/vs2017/DemoLinker.png?raw=true)

### 4.4 编译和运行

选择主菜单`生成` -> `生成解决方案`即可编译。

运行前需要在本地部署一个 DolphinDB server，并用上述建库建表脚本先创建 `dfs://iot/readings`。

在普通的台式机上，部署 [DolphinDB 单节点模式](../安装和部署/standalone_server.md)，采用社区版默认配置，导入上述数据集（1200万条记录），约耗时2分钟。

在此过程中如果遇到如下问题：

- 生成解决方案时报无法打开源文件 "openssl/err.h"的错误

  解决方案：可能由于选择的编译平台不正确，比如下图所示错选了 Release x86，没有选本例要求的 Release x64。

![image](../images/vs2017/demoCompile.png?raw=true)

- 生成失败，报错`LINK : fatal error LNK1181: 无法打开输入文件“libDolphinDBAPI.lib”`

  解决方案：可能由于库文件目录书写错误，请检查4.3节步骤（1）中包含的头文件和目录是否正确。

- 运行时报 libDolphinDBAPI.dll 或 ssleay32MD.dll、libeay32MD.dll 库找不到的错误

  解决方案：需要把对应库拷贝至可执行程序所在目录（如本例对应的目录是`D:\DolphinDB\api-cplusplus\cppApiDemo\cppApiDemo\x64\Release`）。
  
  另外，在下载的`D:\DolphinDB\api-cplusplus\bin\vs2017_x64`子目录中提供了 ssleay32MD.dll、libeay32MD.dll。

- 运行抛出异常`ios_base::failbit set: iostream stream error`

  解决方案：该异常有可能是由于没有更改 cppApiDemo.cpp 源码中的本地 csv 路径：```path = "d:/data/devices_big_readings.csv"```; 

  若更改过路径，检查是否需要修改 Windows 中的路径（如”d:\data\devices_big_readings.csv”，需要修改 “\” 为 “/”）。

## 5. 说明

本文以 VS2017 Release/x64 平台为例，一步一步介绍了如何搭建 DolphinDB C++ API 的 Visual Studio 开发环境，并用源码编译 API 动态库。然后结合实例讲解如何利用API动态库开发 API 应用程序。读者可以参照本文的描述举一反三，自己动手编译其他 Release/Debug 模式，其他 x64/x86 平台，或其他 Visual Studio 版本如 VS2015/VS2019/VS2022 等的动态库。

若使用 Visual Studio 2017 或 Visual Studio 2019 Release 模式在 x64/x86 平台上开发，且不需要修改源码，可以直接使用 `api-cplusplus/bin` 下提供的已编译完成的 Visual Studio 2017 Release 模式动态库。

更多 API 接口的使用教程，请参阅 [C++ API使用教程](https://gitee.com/dolphindb/api-cplusplus/blob/master/README_CN.md) 和 [C++ API 数据读写指南](./c++api.md)。


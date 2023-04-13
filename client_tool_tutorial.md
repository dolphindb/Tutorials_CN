# DolphinDB客户端软件教程

DolphinDB提供了从基于Java的GUI, VS Code Extension, Web界面，到命令行等各种灵活友好的交互界面，具体包括以下几种客户端交互方式。

**目录**

  - [1. DolphinDB GUI](#1-dolphindb-gui)
    - [1.1 核心概念](#11-核心概念)
    - [1.2 安装和启动](#12-安装和启动)
    - [1.3 程序执行及结果查看](#13-程序执行及结果查看)
    - [1.4 中文出现乱码](#14-中文出现乱码)
    - [1.5 精度配置](#15-精度配置)
    - [1.6 `java.lang.OutOfMemoryError: Java heap space`](#16-javalangoutofmemoryerror-java-heap-space)
  - [2. VS Code Extension](#2-vs-code-extension)
    - [2.1 下载安装插件](#21-下载安装插件)
    - [2.2 连接DolphinDB Server](#22-连接dolphindb-server)
    - [2.3 编辑和运行DolphinDB脚本](#23-编辑和运行dolphindb脚本)
    - [2.4 观察变量](#24-观察变量)
  - [3. DolphinDB Notebook](#3-dolphindb-notebook)
    - [3.1 启动](#31-启动)
    - [3.2 登录](#32-登录)
    - [3.3 集群管理以及系统监控](#33-集群管理以及系统监控)
    - [3.4 程序执行以及结果查看](#34-程序执行以及结果查看)
  - [4. DolphinDB Jupyter Notebook 扩展插件 （已停止维护）](#4-dolphindb-jupyter-notebook-扩展插件-已停止维护)
    - [4.1 下载安装插件](#41-下载安装插件)
    - [4.2 配置Jupyter Notebook工作路径](#42-配置jupyter-notebook工作路径)
    - [4.3 连接DolphinDB Server](#43-连接dolphindb-server)
    - [4.4 编辑和运行DolphinDB脚本](#44-编辑和运行dolphindb脚本)
  - [5. DolphinDB终端(DolphinDB Terminal)](#5-dolphindb终端dolphindb-terminal)
  - [6. 命令行远程脚本执行](#6-命令行远程脚本执行)
  - [7. 命令行本地脚本执行](#7-命令行本地脚本执行)


## 1. DolphinDB GUI

DolphinDB GUI是基于Java的功能最齐全的图形化编程以及数据浏览界面，可在任何支持Java的操作系统上使用，例如: Windows, Linux, 以及Mac。DolphinDB GUI的特点是速度快，功能齐全，用户友好，适合用于管理和开发DolphinDB脚本、模块，以及数据库交互，查看运行结果等。GUI提供非常友好的编程界面：查找替换文本、保留字高亮显示、系统函数提示、行号显示，选择部分代码执行、执行结果浏览、log信息、临时变量浏览、数据库浏览。通过Project浏览器，可以浏览所有项目。通过Database浏览器，可以浏览所有DFS数据库以及其分区表的schema。

### 1.1 核心概念

#### Server

GUI菜单中的server是指DolphinDB数据库服务器。完成添加后，会自动出现在server下拉菜单中。默认添加的server为localhost:8848。这里值得注意的是，连接远端服务器，我们一般建议连接数据节点，因为DolphinDB关于数据库的操作都是在数据节点上执行的。

#### Login

登录数据库服务器主要有三种方法：

* 在添加server的时候指定用户名和密码
* 通过工具条中的login按钮
* 通过脚本中使用login函数

#### Workspace

启动GUI时，首先会要求用户指定workspace路径，用于项目管理。Workspace下面可以有多个项目。一个用户只能同时使用一个workspace。

#### Project

指定workspace后，可以通过 `New Project`来创建新的项目，也可以通过 `Import Folder`来导入已有的项目。

#### File

创建project后，用户可以在project下面通过 `New Folder`以及 `New File`来生成脚本目录以及脚本文件。脚本文件创建之后，即可通过编辑器来编写、修改、以及执行脚本。

#### Synchronize to server

在远端服务器上执行一个脚本文件或者调用了一个module都会在该服务器上查找对应的脚本文件。当GUI和DolphinDB server不在一个机器上时，有可能需要把本地最新编辑的脚本文件同步到远程服务器上。为此，DolphinDB提供了 `Synchronize to server`, 即文件同步功能。在项目浏览器中右键点击需要同步的目录或者文件，并选择 `Synchronize to server`，将其传送到服务器的对应目录。通过以下方式指定“Remote Directory”后才可使用文件同步功能：

* 添加远程服务器时通过“Remote Directory”指定相应目录；需要注意，远端服务器的用户必须拥有创建“remote Directory”的权限。
* 若上步中未指定，则可通过 Server->Edit Server菜单来指定。

举个例子，如果将“Remote Directory”设置为'/home/usr1'，并且需要同步的本地文件名是"C:/users/usr1/Project/scripts/test.dos"，那么系统会在远端自动创建目录和相应文件'/home/usr1/Project/scripts/test.dos'。

### 1.2 安装和启动

在启动GUI前，需要确保已经安装[java 8 64bit](https://www.oracle.com/java/technologies/javase-jre8-downloads.html) 以及以上版本。
DolphinDB GUI无需安装，可以直接运行。在Windows环境下，双击gui.bat即可。在Linux和Mac环境下，在Terminal中输入：

```
cd /your/gui/folder
./gui.sh
```

#### 常见无法正常启动原因

如果DolphinDB GUI无法正常启动，可能有以下三个原因：

* 没有安装Java。Java下载地址：https://www.oracle.com/technetwork/java/javase/downloads/index.html。
* Java不在系统路径中。在Windows环境下，需要查看是否在 `Path`中；在Linux环境中，需要查看是否在 `PATH`中。
* 安装的Java版本不符合要求。DolphinDB GUI使用环境需要64 位Java 8及以上版本。32位的Java即使版本正确，由于不支持Server模式，只有Client模式，将无法启动GUI。我们可以在命令行中使用 `java -version`命令查看Java的版本信息。

符合要求的Java版本如下：

```
java -version

java version "1.8.0_121"

Java(TM) SE Runtime Environment (build 1.8.0_121-b13)

Java HotSpot(TM) 64-Bit Server VM (build 25.121-b13, mixed mode)
```

如果版本信息的最后一行如下，那么DolphinDB GUI将无法正常启动。

```
Java HotSpot(TM) Client VM
```

### 1.3 程序执行及结果查看

GUI编程界面提供代码查询、修改、高亮显示、函数提示等功能。用户可以选择部分代码执行，也可以点击文件执行代码。执行完毕，可以立刻看到执行结果，以及查看所有的局部变量和共享变量的值。
关于GUI更详细具体的功能介绍请参阅[GUI帮助手册](https://www.dolphindb.cn/cn/gui/index.html)。

![image](images/GUI/code_editing.JPG?raw=true)

### 1.4 中文出现乱码

如果中文显示出现乱码，需要在文件菜单Preferences中设置中文字体，例如微软雅黑(Microsoft Yahei)。 然后print(变量)名，查看输出结果，乱码会消失。

### 1.5 精度配置

DolphinDB GUI默认精度是4位。如果需要更高或低的精度，需要在Preferences中，将精度配置项 `Default number of decimal place`设置成想要的精度，例如8。

### 1.6 `java.lang.OutOfMemoryError: Java heap space`

如果出现内存溢出，说明GUI的默认2048M启动内存不能满足需要，可以通过修改gui/gui.bat或者gui/gui.sh中的 `-Xmx`启动参数来扩大内存，如下:

```
start javaw -classpath dolphindb.jar;dolphingui.jar;jfreechart-1.0.1.jar;jcommon-1.0.0.jar;jxl-2.6.12.jar;rsyntaxarea.jar;autocomplete.jar -Dlook=cross -Xmx4096m com.xxdb.gui.XXDBMain
```

## 2. VS Code Extension

VS Code 是微软开发的一款轻便又有极强扩展性的代码编辑器。它提供强大的插件框架，可通过插件支持不同编程语言，达到语法高亮、智能语法提示以及代码运行等效果。DolphinDB database 提供了VS Code的插件，用户可以使用VS Code编写DolphinDB脚本并运行。

DolphinDB VS Code 插件提供如下功能：

* 自动识别dos和txt后缀的文件
* 连接DolphinDB server
* 编辑和执行DolphinDB脚本
* 观察变量

VS Code 插件与GUI功能非常相似。优点是VS Code使用者无需安装其它软件，直接下载插件即可使用，学习成本低，上手快。缺点是不支持GUI的画图功能以及DFS数据库浏览器功能。

### 2.1 下载安装插件

点击VS Code左侧导航栏的Extensions图标，或者通过ctrl+shift+X快捷键打开插件安装窗口，在搜索框中输入DolphinDB，即可搜索到DolphinDB插件。点击Install进行安装。安装完成后，以txt和dos为后缀的文件都可以被DolphinDB插件识别。

![image](images/vscode/1.png?raw=true)

### 2.2 连接DolphinDB Server

在编辑并运行脚本之前，需要先新增并选择一个数据节点作为运行脚本的服务器。新建并打开一个txt或dos文件，通过右键菜单可以增加、选择和移除DolphinDB Server。

![image](images/vscode/server.png?raw=true)

#### 新增服务器

选择右键菜单的“DolphinDB:addServer”，依次输入server名称、数据节点IP地址以及端口号。

#### 选择服务器

选择右键菜单的“DolphinDB:chooseServer”，选择要连接的server。

#### 移除服务器

选择右键菜单的“DolphinDB:removeServer”，选择要移除的server。

### 2.3 编辑和运行DolphinDB脚本

VS Code打开txt或dos文件时，DolphinDB插件会自动加载右键菜单并且识别脚本，支持语法高亮、智能语法提示。通过 ctrl+E 快捷键或者下拉菜单"executeCode"来执行选中代码，若没有选中代码，则会执行当前光标所在的行。

  ![image](images/vscode/4.gif?raw=true)

### 2.4 观察变量

DolphinDB 插件在左边导航增加了变量面板，面板显示当前服务器上的所有本地和共享变量，每次执行代码时面板上变量会更新。点击变量右边的"show"链接可以在输出面板查看变量的值

  ![image](images/vscode/5.gif?raw=true)

## 3. DolphinDB Notebook

DolphinDB Notebook是DolphinDB服务器安装包自带的，基于网页的图形化交互工具。它主要用于系统监控、日志查看、以及数据浏览。同时也可用于快速编辑执行代码、查看变量、以及基本的画图功能。与DolphinDB终端一样，它更适合临时任务，不适于执行复杂的开发任务。为了保证DolphinDB服务器的性能，若10分钟内无命令执行，系统会自动关闭DolphinDB Notebook的会话以释放DolphinDB系统资源。

### 3.1 启动

DolphinDB Notebook通过是通过HTML+Javascript编写的Web前端。在single node模式下，启动DolphinDB服务器，只要在浏览器输入网址(默认为 http://localhost:8848)即可访问。在集群模式下只要在浏览器输入controller节点的网址加端口号即可访问。

若无法访问Notebook，需要查看以下几个方面：

* 确保DolphinDB server的license没有过期
* 确保该节点的端口没有被防火墙屏蔽
* 确保web目录在server目录下面

在Linux环境下，如果端口没有开放，可以尝试如下命令：

```
>firewall-cmd --get-active-zones

public
interfaces: eth1

>sudo firewall-cmd --zone=public --permanent --add-port=8848/tcp

success
```

### 3.2 登录

DolphinDB Notebook不会强制用户登录服务器，但是有些功能例如浏览/创建数据库，浏览/创建分区表需要登录才能访问。如果需要用户执行任何代码前都需要登录，可以在single node模式下的dolphindb.config中添加webLoginRequired=true；集群模式下需要在controller.cfg和cluster.cfg中添加。

若用户成功登录，会在屏幕上方显示登录用户名。若10分钟内无命令执行，会自动退出登录。

### 3.3 集群管理以及系统监控

DolphinDB Notebook 最主要的功能是用于集群节点管理、系统监控以及数据浏览。

#### 启动节点

集群模式下，启动节点过程中，如果按刷新键没有看到节点状态更新状态。 可以注意以下几个方面：

* 有的时候由于Cache的原因，所以需要刷新网页 (SHIFT键+刷新)
* 如果长时间状态没有更新，则需要查看系统log(点击ServerLog列对应节点的View超链接)得出具体未启动原因：
  * License过期
  * 节点端口被其它进程占用
  * 正在恢复元数据
  * 其它原因

![image](images/Notebook/manage_interface.JPG?raw=true)

### 3.4 程序执行以及结果查看

在集群模式下，用户需要点击节点名字的链接来打开notebook界面。此外，需要浏览DFS数据库以及分区表时，single node模式按钮在屏幕右上角，cluster模式则在屏幕左上角。

![image](images/Notebook/code_editing.JPG?raw=true)

## 4. DolphinDB Jupyter Notebook 扩展插件 （已停止维护）

Jupyter Notebook 是基于网页的用于交互计算的应用程序，可被应用于全过程计算：开发、文档编写、运行代码和展示结果。用户可以直接通过浏览器编辑和交互式运行代码。DolphinDB database 提供了Jupyter Notebook 的插件。

**注意**：DolphinDB 已停止对该插件的研发和维护。有关最新版本 DolphinDB server 的使用及其他应用教程，请参考：

* [DolphinDB VSCode 插件说明](https://github.com/dolphindb/vscode-extension/blob/master/README.zh.md "DolphinDB VSCode 插件说明")
* [DolphinDB GUI使用手册](https://www.dolphindb.cn/cn/gui/index.html "DolphinDB GUI使用手册")
* [DolphinDB 用户手册](https://www.dolphindb.cn/cn/help/200/index.html "DolphinDB 用户手册")
* [DolphinDB 教程](https://gitee.com/dolphindb/Tutorials_CN/tree/master "DolphinDB 教程")

DolphinDB Jupyter Notebook 扩展插件提供以下功能：

- 为用户提供 Jupyter Notebook 连接DolphinDB Server 的配置界面。
- 使 Jupyter Notebook 支持 DolphinDB 脚本语言的执行。

### 4.1 下载安装插件

- 在命令行中，首先使用pip安装 DolphinDB Jupyter Notebook 插件

`pip install dolphindb_notebook`

- 安装完成后启用插件

`jupyter nbextension enable dolphindb/main`

### 4.2 配置Jupyter Notebook工作路径

Jupyter Notebook内核（kernels）是编程语言特定的进程，它们独立运行并与Jupyter应用程序及其用户界面进行交互。DolphinDB Jupyter Notebook 扩展插件提供了运行DolphinDB脚本的内核。用户需要通过以下步骤配置Jupyter Notebook的工作路径，以便在程序运行时DolphinDB内核能够顺利导入。

- 通过命令行jupyter kernelspec list查看Jupyter Notebook Kernel的工作路径

  - Linux系统

  ```Shell
  >jupyter kernelspec list
  Available kernels:
      dolphindb   /home/admin/.local/share/jupyter/kernels/dolphindb
      python3       /home/admin/.local/share/jupyter/kernels/python3
  ```

  将/home/admin/.local/share/jupyter/kernels复制下来，方便下一步配置时粘贴。

  - Windows系统

  ```Shell
  >jupyter kernelspec list
  Available kernels:
      dolphindb   C:\Users\admin\appdata\local\programs\python3\python37\share\jupyter\kernels\dolphindb
      python3       C:\Users\admin\appdata\local\programs\python3\python37\share\jupyter\kernels\python3
  ```

  将 C:\Users\admin\appdata\local\programs\python3\python37\share\jupyter\kernels复制下来，方便下一步配置时粘贴。
- 通过命令行 `jupyter notebook --generate-config`生成一个配置文件jupyter_notebook_config.py，打开这个配置文件，找到c.NotebookApp.notebook_dir选项，设为上一步复制下来的工作路径，并去掉注释#。
- 注意：Windows系统中，需要将路径中的一个反斜杠\都替换成两个反斜杠\\\\，因为一个反斜杠\会被系统误认为是转义字符。

### 4.3 连接DolphinDB Server

- 在命令行输入 `jupyter notebook`，启动Jupyter Notebook。
- 在Jupyter Notebook的页面右侧点击新建，选择DolphinDB，新建一个DolphinDB notebook。
- 点击notebook工具栏的 Connect to DolphinDB Server 按钮。选择相应的server，然后点击右下角Connect按钮，即与DolphinDB server建立连接（如果不需要该server，可以点击Delete按钮删除）。
- 也可以通过New按钮，输入新的server信息，然后点击Save & Connect按钮即与DolphinDB server建立连接，并保存该信息以便下次使用。

### 4.4 编辑和运行DolphinDB脚本

连接DolphinDB Server后，在代码块区域编写DolphinDB脚本，点击运行即可运行相应代码块。每次运行DolphinDB脚本后，运行结果都会在相应的代码块下方展示。对于DolphinDB的绘图功能，以PNG展示结果。

**注意：**

- 对于一些数据量较大的结果，可能会出现IOPub数据率超出限制的问题，可以启用Jupyter Notebook配置文件中的c.NotebookApp.iopub_data_rate_limit一项，去掉注释符号后，按需调高数值。
- 对于超出60行的表格，只显示前五行与后五行。

## 5. DolphinDB终端(DolphinDB Terminal)

DolphinDB终端(DolphinDB Terminal)是一个命令行交互式工具，用于连接到远程的DolphinDB服务器执行命令。使用终端的优点是可以快速连接到远端数据库上执行一些交互命令和脚本。缺点是没有图形化界面，不适用于开发和执行大量复杂代码。

DolphinDB终端和DolphinDB服务器用的是同一个程序，1.10.4及以上版本方可支持。当用户启动DolphinDB的时候，如果指定参数 `remoteHost`和 `remotePort`，当前进程将被启动为DolphinDB终端。如果服务器不允许guest用户登录，启动时可参数 `uid`和 `pwd`指定用户名和密码，也可以在启动后的终端中通过login命令登录。DolphinDB的工作非常简单，接受用户的输入并发送到远程服务器执行，最后把执行结果在终端显示。因此DolphinDB终端不需要license，也不需要系统初始化脚本dolphindb.dos以及其它配置文件。DolphinDB的终端可以是跨操作系统的，例如Windows上的终端可以访问Linux的DolphinDB的服务器。

下面的命令是在Linux上启动DolphinDB终端的示例。由于默认shell不支持命令上下回滚，所以需要借助rlwrap命令来实现。

```
rlwrap -r ./dolphindb -remoteHost 127.0.0.1 -remotePort 8848 -uid admin -pwd 123456
```

下面的命令是在Windows上启动DolphinDB终端的示例。

```
dolphindb.exe -remoteHost 127.0.0.1 -remotePort 8848 -uid admin -pwd 123456
```

成功登入后，系统会显示DolphinDB Termninal，如下：

```
DolphinDB Terminal 1.10.4 (Build:2020.04.03). Copyright (c) 2011~2019 DolphinDB, Inc.
```

如果启动终端时不指定登录信息，可以在连接后使用login命令。

```
>DolphinDB Terminal 1.10.4 (Build:2020.04.03). Copyright (c) 2011~2019 DolphinDB, Inc.
>login("admin","123456");
```

DolphingDB终端支持单行或多行脚本。只要在代码末尾加上分号 `;`或者 `go`语句，系统就会将代码发送到远端执行。通过分号 `;`单句提交示例如下：

```
1+2;
```

多句提交示例如下：

```
def myFunc(x,y){
    return x+y
}
myFunc(1,2); 
```

由于分号 `;`会触发解析它们之前的代码，如果将其放在自定义函数中间，会造成函数定义无法完整传送到远端，从而造成解析错误，例如:

```
def myFunc(x,y){
    return x+y;
}
myFunc(1,2);

//抛出语法接异常
Syntax Error: [line #2] } expected to end function definition
```

退出终端使用quit指令。

```
quit + Enter
```

为方便在任何工作目录下启动终端，可以将DolphinDB可执行文件目录（即包含dolphindb或者dolphindb.exe的目录），添加到系统的搜索路径中。Linux上可以export到 `PATH`

```
export PATH=/your/dolphindb/excutable/path:$PATH
```

在Windows上可以将可执行文件路径添加到系统环境变量 `Path`中。格式为分号加全路径（注意分号必须是英文分号）。路径设置完成后，可以通过打开dos或者PowerShell窗口，在任意目录下,通过dolphindb命令启动终端。

## 6. 命令行远程脚本执行

DolphinDB终端可以让用户方便的连接到远端的DolphinDB服务器，并以交互的方式执行命令。但是如果所有需要执行的脚本已经写在一个脚本文件中，那么我们有更简单的办法在远端服务器上批处理执行这些脚本。只要在启动DolphinDB终端的命令中额外指定一个参数 `run`，即可以将 `run`参数指定的本地脚本文件发送到远端服务器上执行。执行完成后终端马上退出。我们称这种模式为 `命令行远程脚本执行`。使用示例如下。需要特别说明的是，`/home/usr1/test.dos`是本地而非远程服务器上的脚本文件。

```
./dolphindb -remoteHost 127.0.0.1 -remotePort 8848 -uid admin -pwd 123456 -run /home/usr1/test.dos
```

命令行远程脚本执行是DolphinDB终端的一个特殊应用。相对于终端模式，优点是无需在终端中输入代码，可以执行更复杂的代码，以及用于重复执行特定任务。例如，定期连接到远端服务器数据库执行脚本中的代码，执行完即退出。缺点是，没有交互模式。

**注意：**

> 通过 -run 使用远端服务器执行本地脚本文件时，如遇异常，返回非0值。

## 7. 命令行本地脚本执行

通过终端交互式或批量执行脚本覆盖了大部分的应用场景。但是某些场景下，需要同时能够在本地和远端执行脚本。譬如，本地读取一个csv文件，然后追加到运行在远端DolphinDB数据库中。这种模式我们称之为 `命令行本地脚本执行`。下面是在Linux上启动命令行本地脚本执行的示范：

```
./dolphindb  -run /home/usr1/test.dos

```

Windows上启动命令行本地脚本执行非常类似：

```
dolphindb.exe -run c:/users/usr1/test.dos
```

启动命令行本地脚本执行，只要通过启动参数run指定一个本地的脚本文件，同时不指定参数remoteHost即可。本质上是启动了一个DolphinDB的工作站(workstation)来执行脚本，完成后退出。因此，命令行本地执行脚本文件的配置跟工作站的配置一样，需要dolphindb.lic和dolphidnb.dos。在Windows下，还需要tzdb目录。

那么在本地脚本执行过程中，如何连接到远端数据库进行操作呢？我们需要通过xdb函数创建一个到远程数据库的连接，然后使用remoteRun函数执行一个脚本或进行rpc调用。DolphinDB对rpc调用进行了扩展，不仅可以调用远端服务器上定义的函数，也可以将本地的函数序列化到远端服务器执行。如果需要执行的脚本比较复杂，一般我们建议定义成一个本地的函数，然后通过rpc调用来完成。

下面的脚本文件 `test.dos`，演示了如何将本地的一个csv文件，写入到远程的一个分布式数据库表中。

```
def appendData(dbPath, partitionTable, t1){
    pt = loadTable(dbPath, partitionTable)
    return tableInsert(pt, t1)
}

conn=xdb("127.0.0.1",8848,"admin","123456")
remoteRun(conn, appendData, "dfs://db1", "pt", loadText("c:/users/usr1/data.csv"))
```

我们首先定义一个函数 `appendData`，将一个内存表写入到指定的数据库表中。然后创建一个远程连接conn。最后通过 `loadText`函数加载本地的csv文件，rpc调用 `appendData`函数。

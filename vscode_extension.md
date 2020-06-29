## DolphinDB VS code 插件

VS Code 是微软开发的一款轻便又有极强扩展性的代码编辑器，它提供强大的插件框架，可以让VS Code通过插件来支持不同编程语言，达到语法高亮、智能语法提示以及代码运行等效果。DolphinDB database 提供了VS Code的插件，用户可以使用VS Code编写DolphinDB脚本并运行。

DolphinDB VS Code 插件提供如下功能：

* 自动识别dos和txt后缀的文件
* 连接DolphinDB Server
* 编辑和指定DolphinDB脚本
* 观察变量

## 1. 下载安装插件

  点击VS Code左侧导航栏的Extensions图标，或者通过ctrl+shift+X快捷键打开插件安装窗口，在搜索框中输入DolphinDB，即可搜索到DolphinDB插件。点击Install进行安装。安装完成后，以txt和dos为后缀的文件都可以被DolphinDB插件识别。
  
  ![image](images/vscode/1.png?raw=true)

## 2. 连接DolphinDB Server
  在编辑并运行脚本之前，需要先新增并选择一个数据节点作为运行脚本的服务器。新建并打开一个txt或dos文件，通过右键菜单可以增加、选择和移除DolphinDB Server。
    
> 新增服务器

选择右键菜单的“DolphinDB:addServer”，依次输入server名称、数据节点IP地址以及端口号。

![image](images/vscode/1.gif?raw=true)

> 选择服务器

选择右键菜单的“DolphinDB:chooseServer”，选择要连接的server。

![image](images/vscode/2.gif?raw=true)

> 移除服务器

选择右键菜单的“DolphinDB:removeServer”，选择要移除的server。

![image](images/vscode/3.gif?raw=true)

## 3. 编辑和运行DolphinDB脚本

 VS Code打开txt或dos文件时，DolphinDB插件会自动加载右键菜单并且识别脚本，支持语法高亮、智能语法提示。通过 ctrl+E 快捷键或者下拉菜单"executeCode"来执行选中代码，若没有选中代码，则会执行当前光标所在的行。

  ![image](images/vscode/4.gif?raw=true)


## 4. 观察变量

DolphinDB 插件在左边导航增加了变量面板，面板显示当前服务器上的所有本地和共享变量，每次执行代码时面板上变量会更新。点击变量右边的"show"链接可以在输出面板查看变量的值

  ![image](images/vscode/5.gif?raw=true)

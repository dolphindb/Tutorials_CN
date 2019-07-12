## DolphinDB vscode 插件

VS code 是微软开发的一款轻便又有极强扩展性的代码编辑器，它提供强大的插件框架，可以让VS code通过插件来支持不同编程语言，达到语法高亮、智能语法提示以及代码运行等效果。DolphinDB提供了VS code的插件，用户可以使用VS code编写DolphinDB Script 并且运行它。

DolphinDB VS code 插件提供如下特性

* 自动识别`dos,txt`两种后缀的文件。
* 设置服务器。
* 编辑脚本语言。
* 运行脚本语言。
* 观察变量。

## 下载安装插件

  在 VS Code 左边导航栏点击Extensions图标，或者`ctrl+shift+x`快捷键打开插件安装窗口，在搜索框输入`DolphinDB`关键字，就会搜索到DolphinDB 插件，点击安装插件后，新建一个文件，保存后缀名为`dos`文件并打开，即可激活插件。

## 设置服务器
  在编辑并运行脚本之前，需要先新增并选择一个数据节点作为运行脚本的服务器。插件通过右键菜单提供了新增/移除/选择服务器的功能。
    
> 新增服务器

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/vscode/1.gif?raw=true)

> 选择服务器

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/vscode/2.gif?raw=true)

> 移除服务器

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/vscode/3.gif?raw=true)

## 编辑&运行脚本
  DolphinDB 插件会在vscode 打开 `dos,txt`后缀的文件时，自动加载右键菜单并且识别脚本，支持语法高亮；编写脚本时，会根据DolphinDB脚本的语法进行智能提示；通过 `ctrl+E` 快捷键或者下拉菜单 `executeCode` 来执行选中代码，若没有选中代码，则会执行当前光标所在的行。

  ![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/vscode/4.gif?raw=true)


## 观察变量

DolphinDB 插件在左边导航增加了变量面板，面板显示当前服务器上的所有本地和共享变量，每次执行代码时面板上变量会更新。点击变量右边的`show`链接可以在输出面板查看变量的值

  ![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/vscode/5.gif?raw=true)
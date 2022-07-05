# API交互协议

DolphinDB API有以下三个交互阶段：
* 连接
* 客户端发送报文
* 服务端返回报文

## 1. 连接

连接阶段是客户端和服务端握手的阶段。客户端向服务器发送`connect`命令请求连接，服务端返回'OK'，并且分配新的SessionID给客户端。

> 客户端发送连接请求

长度(Byte) | 报文 | 说明
---|---|---
3| API | 请求类型
1| 空格| char(0x20)
1|0 | SESSIONID
1| 空格|  char(0x20)
2| 8| 报文指令长度，固定字符串connect\n
1|  换行符(LF)| char(0x10)
8| "connect\n"  | 固定字符串

> 服务端应答报文请求

长度(Byte) | 报文 | 说明
---|---|---
不固定| 例如'1195587396' | SESSIONID  
1| 空格| char(0x20)
1|0 | 返回对象数量
1| 空格|  char(0x20)
1| 1| 大小端，1-小端，0-大端
1|  换行符(LF)| char(0x10)
不固定| 执行结果  | "OK"

## 2. 指令交互

### 2.1. 请求报文

```txt
| 请求类型 | 空格 | SESSIONID | 空格 | 报文指令长度 | 换行符(LF)
| 指令类型 | 换行符(LF)
| 指令参数 | 数据 |
```

### 2.2. 应答报文

```txt
| SESSIONID | 空格 | 返回对象数量 | 空格 | 大小端 | 换行符(LF)
| 执行结果 | 换行符(LF)
```

### 2.3. 会话

会话编号(session ID)代表终端与DolphinDB建立的一次TCP连接。终端通过`connect`连接成功后DolphinDB会返回一个新的session ID，在此之后所有的报文交互都基于此session ID进行，直到此连接被终端主动关闭。

如果请求报文的session ID为0，或者服务器找不到指定的session ID，服务器会创建并返回一个新的session ID。

session ID是一个随机的长整型。

### 2.4. 请求类型

请求方式 | 说明
---|---
API | 调用并返回结果，无进度信息返回。
API2| 调用返回结果的同时，持续返回执行中脚本输出的信息。此方式仅支持script指令。

### 2.5. 指令类型

DolphinDB database 支持以下三种指令类型:

* script: 这种指令使用非常灵活，它以字符串形式发送脚本，服务器会返回脚本执行的结果。
* function: 这种指令可以调用指定的函数，可以是内置函数或自定义函数。函数可以接受多个对象作为函数参数。
* variable: 将客户端对象变量上传到服务器并指定其变量名。

### 2.5.1 script

script指令用来向DolphinDB发送脚本字符串，DolphinDB执行脚本并返回执行结果。

> 请求报文格式

长度(Byte) | 报文 | 说明 | 样本
---|---|---|---
3 或 4| 请求类型 | API，API2 | API
1| 空格| char(0x20) |
不固定|SESSIONID | 长度不固定，到空格为止  | 2247761467
1| 空格| char(0x20) |
2| 报文指令长度| 包含从“script"到脚本内容结束为止的长度，如"script\n1+1"  | 11
1| 换行符 | char(0x10) |
7| 指令 | script | "script"
1| 换行符 | char(0x10) |
不固定| 脚本内容 | 长度到下一个换行符为止| select * from loadTable('dfs://db','tb1') 或 sum(1..100) + avg(1..100)

> 响应报文格式

长度(Byte) | 报文 | 说明 | 样本
---|---|---|---
不固定|MSG| 如果请求类型为API2, 并且脚本中间有print等输出脚本,在返回报文包含MSG段 | MSG<br>"this is output message1"<br>MSG<br>"this is output message2"
不固定| SESSIONID | 长度不固定，到空格为止  | 2247761467
1| 空格| char(0x20) |
1|大小端 | 1-小端，0-大端 | 1
1| 换行符(LF) | char(0x10) |
1| 执行成功否| 返回文本OK表示执行成功 | "OK"
1| 换行符(LF) | char(0x10) |
不固定| 返回结果 | 数据格式参考第3节 |

### 2.5.2 function

function指令用来向DolphinDB发送函数调用请求，DolphinDB会执行指定函数并返回执行结果。

>请求报文

长度(Byte) | 报文 | 说明 | 样本
---|---|---|---
3| 请求类型 | API | API
1| 空格| char(0x20) |
不固定|SESSIONID | 长度不固定，到空格为止 | 2247761467，638252939
1| 空格| char(0x20) |
2| 报文指令长度| 包含从“function"到大小端标志为止的长度，如"function\nsum\n1\n1" | 16
1| 换行符 | char\(0x10\) |
8| 指令 | function | "function"
1| 换行符 | char(0x10) |
不固定| 函数名称 | 长度到下一个换行符为止| sum
1| 换行符 | char(0x10) |
1| 参数数量 | 传递到函数的参数个数 | 1
1| 换行符 | char(0x10) |
1| 大小端标志 | 1-小端，0-大端 | 1
不固定| 参数数据 | 数据格式参考第3节 |

> 响应报文格式

长度(Byte) | 报文 | 说明 | 样本
---|---|---|---
3| SESSIONID | 长度不固定，到空格为止   | API
1| 空格| char(0x20) |
1|大小端 | 1-小端，0-大端 | 1
1| 换行符(LF) | char(0x10) |
1| 执行成功否| 返回文本OK表示执行成功 | "OK"
1| 换行符(LF) | char(0x10) |
不固定| 返回结果 | 数据格式参考第3节 |

### 2.5.3 variable

variable指令用来向DolphinDB发送本地数据，DolphinDB会在Server端生成指定变量。

长度(Byte) | 报文 | 说明 | 样本
---|---|---|---
3| 请求类型 | API | API
1| 空格| char(0x20) |
不固定|SESSIONID | 长度不固定，到空格为止  | 2247761467
1| 空格| char(0x20) |
2| 报文指令长度| 包含从“variable"到大小端标志为止的长度，如"variable\na,b\n2\n1" | 16
1| 换行符 | char(0x10) |
8| 指令 | variable | "variable"
1| 换行符 | char(0x10) |
不固定| 变量名 | 多个变量通过","号分隔，字符串 | a,b
1| 换行符 | char(0x10) |
1| 变量数量 | 传递到函数的变量个数 | 2
1| 换行符 | char(0x10) |
1| 大小端标志 | 1-小端，0-大端 | 1
不固定| 变量数据 | 数据格式参考第3节 |

> 响应报文格式

占位(Byte) | 报文 | 说明 | 样本
---|---|---|---
3| SESSIONID | 长度不定，到空格为止  | API
1| 空格| char(0x20) |
1|大小端 | 1-小端，0-大端 | 1
1| 换行符(LF) | char(0x10) |
1| 执行成功否| 返回文本OK表示执行成功 | "OK"

### 2.5.4 行为标识
在 提交 script，function 报文时，在 "报文指令长度" 之后，增加"行为标识"报文来指示Server按照指定的要求来执行脚本或函数。

行为标识以字符串方式传输。每一个标识用下划线_分隔，整个字符串的含义如下：

标识名 | 标识范围 | 说明 | 样本
---|---|---|---
flag | (0，1，2，4，8，16)任意数字组的和 | 一组开关量标识，按位取值， 参考flag表格 | 4
cancellable |0,1 | 任务是否可以取消 | 1
priority | 0~8  |指定本任务优先级 | 8
parallelism | 0~64 | 指定本任务并行度| 8
rootId | 整数 | 根任务编号，内部使用，API中固定为空| 12
fetchSize | | 指定分块返回的块大小| 10000
offset | | API中固定为空|


一个标准的行为标识字符串用"/ "开头，以换行符结束。如："/ 4_1_8_8__10000\n"。

flag的含义如下：

数位(从低位开始) |标识名 | 说明
---|---|---
0| isUrgent | 是否紧急任务。即使系统繁忙，isUrgent=1的任务会通过紧急通道得以执行。
1| isSecondaryJob | API提交的任务，isSecondaryJob必须为0
2| isAsync | 是否异步任务
3| isPickle | 让服务端以picle协议返回数据，固定为0 
4| isClearSessionMemory | 本次任务完成后
5| isAPIClient | 内部使用，固定为0


## 3 数据报文

### 3.1 数据形式

* 标量(DF_SCALAR)

 报文字段 | 长度(Byte) | 说明
---|---|---
|DataType|1| 数据类型
|DataForm|1| 数据形式
|Data|不固定| 数据，具体参考 #1.4

* 向量(DF_VECTOR)

 报文字段 | 长度(Byte) | 说明
---|---|---
|DataForm|1| 数据形式
|DataType|1| 数据类型
|Rows|4| 行数
|Columns|4| 列数，向量的columns是1
|Data|不固定| 数据

* 数据对(DF_PAIR)

报文字段 | 长度(Byte) | 说明
---|---|---
|DataForm|1| 固定为2
|DataType|1| 数据类型
|Rows|4| 行数，固定为2
|Columns|4| 列数，固定为1
|values|不固定|数据， 参照*向量*格式

* 矩阵(DF_MATRIX)

 报文字段 | 长度(Byte) | 说明
---|---|---
|HasRowLabel|1bit| Byte中第一个bit， 0000 0001
|HasColumnLabel|1bit| Byte中第二个bit，0000 0010
|DataForm|1| 数据形式
|DataType|1| 数据类型
|RowLabels|不固定| 行名称
|ColumnsLabels|1| 列名称
|Rows|4|行数
|Columns|4|列数
|Data|不固定| 数据

* 集合(DF_SET)

报文字段 | 长度(Byte) | 说明
---|---|---
|DataForm|1| 固定为4
|DataType|1| 数据类型
|Rows|4| 行数
|Columns|4| 列数，固定为1
|values|不固定|数据， 参照*向量*格式

* 字典(DF_DICTIONARY)

报文字段 | 长度(Byte) | 说明
---|---|---
|DataForm|1| 固定为5
|DataType|1| 数据类型
|Keys|不固定| 键， 参照*向量*格式
|values|不固定|值， 参照*向量*格式

* 表（Table）

报文字段 | 长度(Byte) | 说明
---|---|---
|DataForm|1| 固定为6
|DataType|1| 数据类型
|Rows|4|行数
|Columns|4|列数
|TableName|不固定| 行名称
|ColumnNames1 |不固定| 列名称1
|ColumnNamesn |不固定| 列名称n
|VectorData1| 不固定| 列1数据， 参照*向量*格式
|VectorDatan| 不固定| 列n数据， 参照*向量*格式

### 3.2 数据类型

API使用基本的数据类型包括Byte，Short，Int，Long，Float，Double，String这几种，所有的日期和时间类型在系统内部都是用INT或者LONG来存储和传输数据。

数据类型 | 长度 | 说明 | 样例
---|---|---|---
BOOL|1|1b, 0b | true, false
CHAR|1|-2^7+1 ~ 2^7-1|'a', 97c
SHORT|2|-2^15+1 ~ 2^15-1|122h
INT|4|-2^31+1 ~ 2^31-1|22
LONG|8|-2^63+1 ~ 2^63-1|22l
DATE|4|INT|2013.06.13
MONTH|4|INT|2012.06M
TIME|4|INT|13:30:10.008
MINUTE|4|INT|13:30m
SECOND|4|INT|13:30:10
DATETIME|4|INT|2012.06.13 13:30:10 or 2012.06.13T13:30:10
TIMESTAMP|8|LONG|2012.06.13 13:30:10.008 or 2012.06.13T13:30:10.008
NANOTIME|8|LONG|13:30:10.008007006
NANOTIMESTAMP|8|LONG|2012.06.13 13:30:10.008007006 or 2012.06.13T13:30:10.008007006
FLOAT|4||2.1f
DOUBLE|8||2.1
STRING|不固定|采用UTF8编码，每个字符串用0做终止符|"String Hello World0"

## 附录-数据报文编码

* 数据类型(DataType)

数据类型| 报文值
---|---
DT_VOID|0
DT_BOOL|1
DT_BYTE|2
DT_SHORT|3
DT_INT|4
DT_LONG|5
DT_DATE|6
DT_MONTH|7
DT_TIME|8
DT_MINUTE|9
DT_SECOND|10
DT_DATETIME|11
DT_TIMESTAMP|12
DT_NANOTIME|13
DT_NANOTIMESTAMP|14
DT_FLOAT|15
DT_DOUBLE|16
DT_SYMBOL|17
DT_STRING|18
DT_UUID|19
DT_FUNCTIONDEF|20
DT_HANDLE|21
DT_CODE|22
DT_DATASOURCE|23
DT_RESOURCE|24
DT_ANY|25
DT_DICTIONARY|26
DT_OBJECT|27

* 数据形式(DataForm)

数据形式|报文值
---|---
DF_SCALAR|0
DF_VECTOR|1
DF_PAIR|2
DF_MATRIX|3
DF_SET|4
DF_DICTIONARY|5
DF_TABLE|6
DF_CHART|7
DF_CHUNK|8
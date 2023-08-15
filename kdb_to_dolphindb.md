# 从 kdb+ 到 DolphinDB

kdb+ 以程序体积小、代码简洁、运行速度快而闻名。它是美国华尔街各大金融机构20多年来处理大规模时序数据的首选系统，通常用于高频交易，非常适用于高速存储、分析、处理和检索时序数据集。kdb+ 还提供了专门的编程语言 q 语言，其简洁而且灵活，天生具有处理大规模时序数据的能力。

2018年初发布的 DolphinDB，同样是性能极佳的时间序列数据库。作为一款国产的高性能分布式数据库产品，DolphinDB 迅速崛起，成为国内头部券商、私募公募的首选方案。DolphinDB 功能强大的编程语言和高容量高速度的流数据分析系统，能在满足低延时高吞吐量数据读写的要求的同时，轻松实现因子挖掘、流式计算、股票行情回放、实时计算高频因子等功能，为金融和物联网领域的数据存储和分析计算提供一站式解决方案。近几年来，DolphinDB 天然的分布式构架，强大的流式增量计算能力，丰富的函数库，以及易用性等优势吸引了大量海内外用户使用 DolphinDB 代替 kdb+。

本教程作为 kdb+ 使用者迁移到 DolphinDB 的一份简明参考，考察了两者的相同点和区别，介绍了如何将 kdb+ 数据迁移到 DolphinDB，并总结了从 kdb+ 到 DolphinDB 编程语法方面的映射。
 
- [从 kdb+ 到 DolphinDB](#从-kdb-到-dolphindb)
  - [1. kdb+ vs DolphinDB](#1-kdb-vs-dolphindb)
    - [1.1 DolphinDB 与 kdb+ 的相同点](#11-dolphindb-与-kdb-的相同点)
    - [1.2 DolphinDB 与 kdb+ 的区别](#12-dolphindb-与-kdb-的区别)
  - [2. 从 kdb+ 导入数据到 DolphinDB](#2-从-kdb-导入数据到-dolphindb)
  - [3. 给 kdb+ 使用者的 DolphinDB 语法参考](#3-给-kdb-使用者的-dolphindb-语法参考)
    - [3.1 数据类型](#31-数据类型)
    - [3.2 关键字](#32-关键字)
    - [3.3 运算符](#33-运算符)
    - [3.4 副词](#34-副词)
    - [3.5 执行控制](#35-执行控制)
 
## 1. kdb+ vs DolphinDB

### 1.1 DolphinDB 与 kdb+ 的相同点

* 数据库类型

DolphinDB 和 kdb+ 都是列存储的时间序列数据库，都包括磁盘数据库和内存数据库，支持并鼓励对表进行分区。数据库系统都内置了编程语言，非常适合库内开发重度的数据应用。

* 编程语言

DolphinDB 和 kdb+ 在编程语言方面有许多相似的地方。DolphinDB 同样支持元编程、向量处理和函数式编程，部分 SQL 语句可以在 DolphinDB 脚本中直接使用。kdb+ 的数据类型、函数和关键字大多能在 DolphinDB 中找到对应，大部分的 kdb+ 脚本都可以一对一翻译为 DolphinDB 脚本。

* 金融支持

DolphinDB 和 kdb+ 都非常好地服务于金融领域。作为列式存储的时序数据库，两者不仅具备关系型数据库的精确性、稳定性和安全性，还具备存储和处理结构化时序数据天然的优势。两者都支持对向量、矩阵、表等多种类型的数据进行数值分析的操作，非常适合追求高性能和高灵活性的金融应用领域。此外，DolphinDB 和 kdb+ 还都具备对海量流数据进行实时分析的能力，是流数据库、内存数据库和历史数据三合一的全栈数据平台。

### 1.2 DolphinDB 与 kdb+ 的区别

* 系统架构

DolphinDB 和 kdb+ 在架构上有很大的不同。DolphinDB 的构架引入了分布式文件系统，天然具备数据高可用、系统高容错、集群易扩展等分布式系统设计所带来的优势。相比之下，主要基于高性能计算机设计的 kdb+，虽然也能通过脚本修改路由网关的方式，运行在多服务器集群上，但这种方式具有很大的局限性。除了集群的部署难度和扩展性受限，kdb+ 很难像 DolphinDB 一样实现自动平衡节点负载来提升并行计算的性能，或是在某个节点故障时保证系统的高可用性。

* 多用户接入支持

DolphinDB 相对于 kdb+ 在架构上的优势还体现在它对多线程的支持上。DolphinDB 支持多用户同时接入系统进行作业，用户可以使用 Web 端管理页面、VS code 插件或是桌面端的 DolphinDB GUI 连接服务器运行脚本。而 kdb+ 虽然支持并发运算，它对多用户并发任务的支持却没有那么完善，一个运行非常耗时的任务作业就会导致整个数据库系统的阻塞，从而无法响应其他用户。实际生产中，这个缺陷在临近市场开放和结束的一段时间里可能会造成问题。

同时，kdb+ 对多用户接入的设计是让所有用户共享一个 session，用 domain 来区分不同用户创建的变量或自定义函数，但不强制要求用户创建自己的 namespace。而 DolphhinDB 为每一个用户创建自己的 session，相互之间不可见，自定义变量和函数的共享则通过使用 share 关键字以及创建 module 或 functionView 的方式实现。相对而言，kdb+ 的用户 session 管理机制对用户自己操作规范的要求更高。

* 数据库特性

DolphinDB 和 kdb+ 磁盘存储的模式不同。kdb+ 使用离线存储模式，数据持久化需要频繁读写磁盘，在部分应用场景会因为 IO 的限制而效率较低。DolphinDB 使用在线存储，可以保持数据随时可用的状态。

此外，DolphinDB 数据库还有许多 kdb+ 没有的特性。DolphinDB 内置了 OLAP 和 TSDB 双引擎，对事务的 ACID 有严格的支持。DolphinDB 提供包括技术分析指标库（TA-lib）、MyTT（My麦语言、T通达信、T同花顺）指标库和 WorldQuant 101 Alpha 因子指标库在内的1000多个内置函数，能更好地支持金融领域的应用场景。针对高频数据的实时分析处理，DolphinDB 内置多种流计算引擎，支持增量计算和并发计算，窗口函数的性能不受限于窗口长度，能很好地满足物联网和金融领域的应用需求。

* 编程友好

DolphinDB 和 kdb+ 编程语言的设计理念有很大不同。kdb+ 要求代码尽可能简短，来减小整个程序的 footprint，从而换取更少的访存时间。kdb+ 编程语言对同一操作符做了多种重载，表达式从左到右解析，运算符没有优先级，错误信息也非常简单。而 DolphinDB 的编程语言设计上非常注重代码的可读性，语法更接近 Python，表达式跟大部分编程语言的习惯相同，从右到左解析，并尊重运算符的优先级。DolphinDB 编程语言可读性高，上手难度低，代码更容易更新维护，是比 kdb+ 更加适合现代软件工程团队协作的编程语言。

* 中文友好

与 kdb+ 相比，DolphinDB 对中文用户更加友好。DolphinDB 由浙江智臾科技有限公司自主研发，有丰富的中文教程和氛围良好的技术交流社区。DolphinDB 团队也在不断地对产品进行更新和维护。

## 2. 从 kdb+ 导入数据到 DolphinDB

DolphinDB 为导入 kdb+ 数据提供插件支持，插件代码已开源在 github/gitee 平台，具体使用请参考 [github ](https://github.com/dolphindb/DolphinDBPlugin/blob/release200/kdb/README_CN.md)或 [gitee](https://gitee.com/dolphindb/DolphinDBPlugin/blob/release200/kdb/README_CN.md) 上的教程。

DolphinDB 的 kdb+ 插件为用户提供了两种数据导入方式：

* 从 kdb+ 数据库导入：连接正在运行的 kdb+ 数据库，以 kdb+ 数据库作为中间管道导入数据；
* 直接读取磁盘上的 kdb+ 数据文件进行导入。

以上两种方式都会将数据加载为 DolphinDB 的内存表。

使用 DolphinDB 的 kdb+ 插件导入数据，在脚本中用 `loadPlugin("/path/to/plugin/PluginKDB.txt")` 语句加载插件，就可以用插件提供的函数进行数据导入。对于第一种导入方式，首先需要使用 `connect` 函数建立与 kdb+ 数据库的连接，获取连接句柄，之后可以用 `close` 函数断开连接。使用 `loadTable` 函数通过 kdb+ 数据库读取数据，需要提供表文件的路径和 sym 文件路径，sym 文件路径可以为空。

```
// 加载插件
loadPlugin("/home/DolphinDBPlugin/kdb/build/PluginKDB.txt")

// 确保插件加载完毕再执行之后的代码
go

// 连接 kdb+ 数据库，用户名和密码字段可以为空
handle = kdb::connect("127.0.0.1", 5000, "admin:123456")

// 指定文件路径
DATA_DIR="/home/kdb/data/kdb_sample"

// 通过 loadTable，加载数据到 DolphinDB
Daily = kdb::loadTable(handle, DATA_DIR + "/2022.06.17/Daily/", DATA_DIR + "/sym")
Minute = kdb::loadTable(handle, DATA_DIR + "/2022.06.17/Minute", DATA_DIR + "/sym")
Ticks = kdb::loadTable(handle, DATA_DIR + "/2022.06.17/Ticks/", DATA_DIR + "/sym")
Orders = kdb::loadTable(handle, DATA_DIR + "/2022.06.17/Orders", DATA_DIR + "/sym")

// 关闭连接
kdb::close(handle)
```

对于第二种文件导入方式，使用 `loadFile` 函数直接读取磁盘上的 kdb+ 文件，需要提供表文件的路径和可选的 sym 文件路径，sym 文件路径可以为空。

```
// 加载插件
loadPlugin("/home/DolphinDBPlugin/kdb/build/PluginKDB.txt")

// 确保插件加载完毕再执行之后的代码
go

// 指定文件路径
DATA_DIR="/home/kdb/data/kdb_sample"

// 通过 loadFile，加载数据到 DolphinDB
Daily2 = kdb::loadFile(DATA_DIR + "/2022.06.17/Daily", DATA_DIR + "/sym")
Minute2= kdb::loadFile(DATA_DIR + "/2022.06.17/Minute/", DATA_DIR + "/sym")
Ticks2 = kdb::loadFile(DATA_DIR + "/2022.06.17/Ticks/", DATA_DIR + "/sym")
Orders2 = kdb::loadFile(DATA_DIR + "/2022.06.17/Orders/", DATA_DIR + "/sym")
```

## 3. 给 kdb+ 使用者的 DolphinDB 语法参考

本节基于 [kdb+ 和 q 官方参考文档](https://code.kx.com/q/ref/)和 [DolphinDB 2.0用户手册](https://www.dolphindb.cn/cn/help/index.html)，所提及的 kdb+ 函数或关键字在 DolphinDB 中的对应，仅保证功能上的可替代性，使用方法可能与原函数略有差异。建议在使用前查阅 [DolphinDB 2.0用户手册](https://www.dolphindb.cn/cn/help/index.html)。
 
### 3.1 数据类型

#### 3.1.1 基本数据类型 <!-- omit in toc -->

| **kdb+ 数据类型** | **DolphinDB 数据类型** | **举例**                         | **字节数** | **范围**     
| ------------- | ------------------ | ---------------------------------------- | ------- | ---------------- |
|               | VOID               | NULL                                     | 1       |                  |
| boolean       | BOOL               | 1b, 0b, true, false                      | 1       | 0~1              |
| byte          |                    |                                          |         |                  |
| char          | CHAR               | 'a', 97c                                 | 1       | -2 7 +1~2 7 -1   |
| short         | SHORT              | 122h                                     | 2       | -2 15 +1~2 15 -1 |
| int           | INT                | 21                                       | 4       | -2 31 +1~2 31 -1 |
| long          | LONG               | 22, 22l                                  | 8       | -2 63 +1~2 63 -1 |
| real          | FLOAT              | 2.1f                                     | 4       | 有效位数：06~09 位 |
| float         | DOUBLE             | 2.1                                      | 8       | 有效位数：15~17 位 |
| date          | DATE               | 2013.06.13                               | 4       |                  |
| month         | MONTH              | 2012.06M                                 | 4       |                  |
| time          | TIME               | 13:30:10.008                             | 4       |                  |
| minute        | MINUTE             | 13:30m                                   | 4       |                  |
| second        | SECOND             | 13:30:10                                 | 4       |                  |
| (datetime)    | DATETIME           | 2012.06.13 13:30:10 or 2012.06.13T13:30:10 | 4       |                |
| (datetime)    | TIMESTAMP          | 2012.06.13 13:30:10.008 or 2012.06.13T13:30:10.008 | 8       |        |
|               | DATEHOUR           | 2012.06.13T13                            | 4       |                  |
| timespan      | NANOTIME           | 13:30:10.008007006                       | 8       |                  |
| timestamp     | NANOTIMESTAMP      | 2012.06.13 13:30:10.008007006 or 2012.06.13T13:30:10.008007006 | 8 |  |
| symbol        | SYMBOL             |                                          | 4       |                  |
| symbol        | STRING             | "Hello" or 'Hello' or `Hello             |         |                  |
| guid          | UUID               | 5d212a78-cc48-e3b1-4235-b4d91473ee87     | 16      |                  |

**说明：**

- DolphinDB 目前暂无对应 kdb+ 中 byte 的数据类型。
- kdb+ 中的 char 类型使用双引号标识，而 DolphinDB 的 CHAR 使用单引号。`"c"` 在 DolphinDB 中会被识别为字符串。
- kdb+ 中的 long 类型与 DolphinDB 的 LONG 数据类型的后缀标识不同。一个值为42的长型整数若表示为 `42j`，则无法被 DolphinDB 识别。
- kdb+ 中的 month 类型后缀标识为 m，而 DolphinDB 使用 m 作为 MINUTE 类型的后缀，使用 M 作为 MONTH 类型的后缀。故 2006.07m 在 DolphinDB 中会报错。
- DolphinDB 使用4个字节存放 DATETIME 类型，而 kdb+ 使用8个字节存放 datetime 类型。
- DolphinDB 的 SYMBOL 类型是特殊的字符串类型，相当于枚举类型。通过 SYMBOL，将字符串存储为一个整数，因此可更高效地进行数据排序。具体使用请参照[数据类型](https://dolphindb.cn/cn/help/DataTypesandStructures/DataTypes/index.html)。

##### 关于 NULL 和 INF <!-- omit in toc -->

DolphinDB 不提供表示各个类型正负无穷值的字面量。对于整型、浮点类型和时间类型，可以使用 `00<数据类型符号>` 作为对应数据类型 NULL 值的字面量。当各类型数据溢出时，会被处理为该类型的 NULL 值。通常，在赋值语句或表达式中使用无返回值的函数时，也会得到一个 VOID 类型的 NULL。

通过函数 `isVoid` 判断是否为 VOID 类型的 NULL，通过函数 `isNull` 和 `isValid` 可以检查所有 NULL 值，包括 VOID 和有类型的 NULL。对于不关心 NULL 类型的用户，建议使用 `isNull` 或 `isValid` 进行条件判断。

对于 NULL 值的初始化、运算，以及在普通向量函数、聚合函数和高阶函数中的使用方法，参考[NULL 值的操作](https://dolphindb.cn/cn/help/DataManipulation/NullValueManipulation/index.html)。

#### 3.1.2 其他数据类型 <!-- omit in toc -->

| **kdb+ 数据类型** | **DolphinDB 数据结构** | **举例** |
| ------------- | -------------------------- | --------- |
| list          | ANY, MATRIX, DICTIONARY    | (1,2,3)   |
| enums         |                            |           |
| anymap        | ANY DICTIONARY, DICTIONARY | {a:1,b:2} |
| dictionary    | ANY DICTIONARY, DICTIONARY | {a:1,b:2} |
| table         | IN-MEMORY TABLE            |           |

**说明：**
- DolphinDB 的 ANY DICTIONARY 表示 JSON 数据类型。
- DolphinDB 字典的键必须是标量，值可以是任何数据形式与数据类型。支持字典嵌套。kdb+ 的字典在输出或进行遍历时，键值对会保留输入时的顺序，但 DolphinDB 的字典是否保留键值顺序由创建时用户传入的 ordered 参数决定。字典默认不保留键值输入顺序，按照 key 在 bucket 内的顺序输出键值对。若创建字典时用户指定 ordered = true，则键值对的顺序与输入顺序保持一致。
- kdb+ 的矩阵由嵌套的 list 表示，遵循行优先。DolphinDB 的矩阵提供数据类型 matrix 存放矩阵，遵循列优先。kdb+ 矩阵输入到 DolphinDB 时需要转换方向。
- DolphinDB 支持包括标量、向量、数据对、矩阵、集合、字典和表在内的多种数据形式，并针对不同的使用场景做了具体优化。请参考[数据形式](https://dolphindb.cn/cn/help/DataTypesandStructures/DataForms/index.html)。
 
#### 3.1.3 数据类型检查函数 <!-- omit in toc -->

DolphinDB提供了 `typestr` 和 `type` 函数用于检查数据类型。`typestr` 返回的是数据类型的名称（字符串常量）；`type` 返回的是数据类型 ID（整数）。

### 3.2 关键字

#### 3.2.1 control 类 <!-- omit in toc -->

| **kdb+** | **DolphinDB** |
| -------- | ------------- |
| do       | do-while      |
| exit     |               |
| if       | if-else       |
| while    | do-while      |

#### 3.2.2 env 类 <!-- omit in toc -->

| **kdb+** | **DolphinDB** |
| -------- | ------------- |
| getenv   | getEnv        |
| gtime    | gmtime        |
| ltime    | localtime     |
| setenv   |               |

#### 3.2.3 interpret 类 <!-- omit in toc -->

| **kdb+** | **DolphinDB**                            |
| -------- | ---------------------------------------- |
| eval     | eval                                     |
| parse    | parseExpr                                |
| reval    |                                          |
| show     | print                                    |
| system   | shell                                    |
| value    | 查询字典、表的值：values <br> 查询普通变量的值：print <br> 将字符串作为元代码执行：parseExpr <br> 将列表作为元代码执行：expr |

#### 3.2.4 join 类 <!-- omit in toc -->

| **join 方式** | **kdb+**               | **DolphinDB** |
| ----------- | ------------------------ | ------------- |
| as-of join  | aj, aj0, ajf, ajf0, asof | aj            |
| equal join  | ej                       | ej, sej       |
| innner join | ij, ijf                  | inner join    |
| left join   | lj, ljf                  | lj, lsj       |
| plus join   | pj                       |               |
| union join  | uj, ujf                  |               |
| window join | wj, wj1                  | wj, pwj       |

#### 3.2.5 list 类 <!-- omit in toc -->

| **kdb+** | **DolphinDB**                            |
| -------- | ---------------------------------------- |
| count    | 非 NULL 元素个数：count <br> 包括 NULL 元素个数：size |
| mcount   | mcount                                   |
| cross    | `join:C`, `cross(join, X, Y)`            |
| cut      | cut                                      |
| enlist   | `[]`, array, bigArray                    |
| except   |                                          |
| fills    | ffill, ffill!                            |
| first    | first                                    |
| last     | last                                     |
| flip     | flip, transpose                          |
| group    | groups                                   |
| in       | in                                       |
| inter    | `intersection(set(X), set(Y))`           |
| next     | next                                     |
| prev     | prev                                     |
| xprev    | move                                     |
| raze     | 将一个矩阵或一系列向量转换成一维向量：flatten |
| reverse  | reverse                                  |
| rotate   |                                          |
| sublist  | head, tail, subarray, subtuple           |
| sv       | 连接字符、字符串向量：concat              |
| til      | til                                      |
| union    | `union(set(X), set(Y))` 或 `distinct(join(X, Y))` |
| vs       | 分割字符串：split                              |
| where    |                                          |

#### 3.2.6 logic 类 <!-- omit in toc -->

| **kdb+** | **DolphinDB** |
| -------- | ------------- |
| all      | all           |
| and      | and           |
| any      | any           |
| not      | not           |
| or       | or            |

#### 3.2.7 math 类 <!-- omit in toc -->

| **kdb+**   | **DolphinDB** |
| ---------- | ------------- |
| abs        | abs           |
| cos        | cos           |
| acos       | acos          |
| sin        | sin           |
| asin       | asin          |
| tan        | tan           |
| atan       | atan          |
| avg        | avg, mean     |
| avgs       | cumavg        |
| ceiling    | ceil          |
| cor        | corr          |
| cov        |               |
| scov       | covar         |
| deltas     | deltas        |
| dev        | stdp          |
| mdev       | mstdp         |
| sdev       | std           |
| div        | div           |
| ema        | ema           |
| exp        | exp           |
| xexp       | pow           |
| floor      | floor         |
| inv        | inverse       |
| log        | log           |
| xlog       |               |
| lsq        |               |
| mavg       | mavg          |
| wavg       | wavg          |
| max        | max           |
| maxs       | cummax        |
| mmax       | mmax          |
| med        | med           |
| min        | min           |
| mins       | cummin        |
| mmin       | mmin          |
| mmu        | dot           |
| mod        | mod           |
| sum        | sum           |
| sums       | cumsum        |
| msum       | msum          |
| wsum       | wsum          |
| neg        | neg           |
| prd        | prod          |
| prds       | cumprod       |
| rand       | rand          |
| ratios     | ratios        |
| reciprocal | reciprocal    |
| signum     | signum        |
| sqrt       | sqrt          |
| within     | between, in   |
| var        | varp          |
| svar       | var           |

**说明：**
- DolphinDB 的 TA-lib 系列函数窗口确定规则与 kdb+ 不同。DolphinDB 会忽略元素开头的空值，并将这些空值保留到结果中，然后从第一个非空元素开始进行滑动窗口的计算。当以元素个数衡量窗口时，根据滑动窗口的计算规则，只有当 window 内的元素填满窗口时，才开始第一次计算，即前（window - 1）个元素的计算结果默认为 NULL。
- DolphinDB 的 m 系列（滑动窗口系列）函数的窗口确定规则：在没有指定 minPeriods 参数的情况下，将前（window - 1）个元素视为 NULL。若要得到与 kdb+ 相同的计算结果，请将 minPeriods 参数指定为1。
- DolphinDB 的 [ratios](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/r/ratio.html) 函数，若输入参数是向量，返回结果的第一个元素是 NULL。

#### 3.2.8 meta 类 <!-- omit in toc -->

| **kdb+**    | **DolphinDB**             |
| ----------- | ------------------------- |
| attr        |                           |
| null        | isNull, isNothing, isVoid |
| tables      | getTables                 |
| type        | type, typestr, form       |
| view, views |                           |

#### 3.2.9 SQL类 <!-- omit in toc -->

| **kdb+** | **DolphinDB**                            |
| -------- | ---------------------------------------- |
| delete   | delete, sqlDelete                        |
| exec     | exec                                     |
| fby      | contextby                                |
| select   | select                                   |
| update   | 更改记录：update, sqlUpdate <br> 添加新的记录：insert into <br> 添加新的列：alter, addColumn |

#### 3.2.10 sort 类 <!-- omit in toc -->

| **kdb+**  | **DolphinDB** |
| --------- | ------------- |
| asc       | sort, sort!   |
| iasc      | isort, isort! |
| xasc      | sortBy!       |
| bin, binr | binsrch       |
| desc      | sort, sort!   |
| idesc     | isort, isort! |
| xdesc     | sortBy!       |
| differ    | valueChanged  |
| distinct  | distinct      |
| rank      | rank          |
| xbar      | bar           |
| xrank     | bucket        |

#### 3.2.11 table 类 <!-- omit in toc -->

| **kdb+**               | **DolphinDB**                            |
| ---------------------- | ---------------------------------------- |
| cols                   | columnNames                              |
| xcol                   | rename!                                  |
| xcols                  | reorderColumns!                          |
| csv                    | csv 格式分隔符：`,`                      |
| fkeys, key, keys, xkey |                                          |
| insert                 | insert into, tableInsert, append!, push! |
| meta                   | schema                                   |
| ungroup, xgroup        |                                          |
| upsert                 | insert into, tableInsert, append!, push! |
| xasc                   | sortBy!                                  |
| xdesc                  | sortBy!                                  |

#### 3.2.12 text 类 <!-- omit in toc -->

| **kdb+** | **DolphinDB** |
| -------- | ------------- |
| like     | like, iliek   |
| lower    | lower         |
| upper    | upper         |
| trim     | trim          |
| ltrim    | ltrim         |
| rtrim    | rtrim         |
| md5      | md5           |
| ss       | regexFind     |
| ssr      | regexReplace  |
| string   | string        |

#### 3.2.13 自定义函数 <!-- omit in toc -->

| **kdb+**                                 | **DolphinDB**                            |
| ---------------------------------------- | ---------------------------------------- |
| signed lambda:`f:{[x;y](x*x)+(y*y)+2*x*y}` <br> unsigned lambda:`{(x*x)+(y*y)+2*x*y}[20;4]` | 命名函数：`def func(x, y) { return (x*x)+(y*y)+2*x*y; }` <br> 匿名函数：`def (x, y) { return (x*x)+(y*y)+2*x*y; }` <br> lambda表达式（只有一个语句的函数）:`def func(x,y)：(x*x)+(y*y)+2*x*y;` <br> 或`def(x,y)：(x*x)+(y*y)+2*x*y;` <br> 或`def(x,y)-> (x*x)+(y*y)+2*x*y;` <br> 或`x->x*x` |

**说明：**
- 在 kdb+ 的语法中，“lambda” 与 “function” 等价。而在 DolphinDB 的 lambda 是只有一个语句的函数。
- kdb+ 允许无参数列表的函数定义，默认 x, y, z 按顺序作为可使用的参数名。而 DolphinDB 要求自定义函数必须有非空或者空的参数列表。
- DolphinDB 支持在定义函数时使用默认参数，支持使用 const 和 mutable 关键字修饰参数。

```
// default argument
def func(x=1): x+1;

// mutable argument
def i2t(mutable tb) { return tb.replaceColumn!(`time, time(tb.time/10); }
```

- DolphinDB 的自定义函数支持即时编译（JIT），能保证函数的执行效率。
- DolphinDB 允许自定义函数使用内置函数的全部调用方式，即可以用标准格式（前缀）和对象方法格式（后缀）调用用户的自定义函数。若用户定义函数的参数数量为一个或两个，还可以使用运算符格式（中缀）调用函数。

```
def f(x, y): x+y+1;
p = 2;
q = 3;

f(p, q);   // standard

p.f(q);    // method of object

p f q;     // operator
```

### 3.3 运算符

与 kdb+ 相同，DolphinDB 的运算符根据作用对象的数目可分为一元运算符和二元运算符。DolphinDB 支持许多类型的基本运算符，包括算术运算符、布尔运算符、关系运算符、成员运算符等，以及多种运算数据类型，包括标量、向量、集合、矩阵、字典和表。

与 kdb+ 不同的是，DolphinDB 表达式的运算顺序是从左往右。DolphinDB 的运算符优先级顺序与大多数编程语言相似，表达式中优先级最高的运算符首先被执行，具有相同优先级的运算符则按从左到右的顺序执行。

#### `.` dot <!-- omit in toc -->

| **kdb+ 含义** | **DolphinDB** |
| ----------- | ------------- |
| Apply       | `call()`      |
| Index       | `[]`          |
| Trap        | try-catch     |
| Amend       |               |

#### `@` at <!-- omit in toc -->

| **kdb+ 含义** | **DolphinDB** |
| ----------- | ------------- |
| Apply At    | `call()`      |
| Index At    | `[]`          |
| Trap At     | try-catch     |
| Amend At    |               |

#### `$` dollar <!-- omit in toc -->

| **kdb+ 含义** | **DolphinDB**    |
| ----------- | ------------------ |
| Cast        | `$`, `cast()`      |
| Tok         | 类型转换函数可直接转换字符串 |
| Enumerate   |                    |
| Pad         | `lpad()`, `rpad()` |
| mmu         | `**`               |

#### `!` bang <!-- omit in toc -->

| **kdb+ 含义**                            | **DolphinDB**           |
| ---------------------------------------- | ----------------------- |
| Dict                                     | `dict()`                |
| Enkey, Unkey, Enumeration, Flip Splayed, internal |                |
| Display                                  | `print()`               |
| Update                                   | `update()`, `update!()` |
| Delete                                   | `erase!()`              |

#### `?` query <!-- omit in toc -->

| **kdb+ 含义**      | **DolphinDB**    |
| ------------------ | ---------------- |
| Find               | `in()`, `find()` |
| Roll               | `rand()`         |
| Deal, Enum Extend  |                  |
| Select             | `select`         |
| Exec, Simple Exec  | `exec`           |
| Vector Conditional | `iif()`          |

#### `##` hash <!-- omit in toc -->

| **kdb+ 含义** | **DolphinDB** |
| ------------- | ------------- |
| Take          | `take()`      |
| Set Attribute |               |

#### 其他运算符 <!-- omit in toc -->

| **kdb+ 符号** | **kdb+ 含义**                           | **DolphinDB**              |
| ------------ | ---------------------------------------- | -------------------------- |
| `+`          | Add                                      | `+`                        |
| `-`          | Substract                                | `-`                        |
| `*`          | Multiply                                 | `*`                        |
| `%`          | Divide                                   | `\`                        |
| `=`          | Equals                                   | `==`                       |
| `<>`         | Not Equals                               | `!=`                       |
| `~`          | Match                                    |                            |
| `<`          | Less Than                                | `<`                        |
| `<=`         | Up To                                    | `<=`                       |
| `>=`         | At Least                                 | `>=`                       |
| `>`          | Greater Than                             | `>`                        |
| `|`          | Greater                                  | `max()`                    |
| `|`          | OR                                       | \|                         |
| `&`          | Lesser                                   | `min()`                    |
| `&`          | AND                                      | `&`                        |
| `_`          | Cut                                      | `cut()`                    |
| `_`          | Drop                                     | `drop()`                   |
| `:`          | Assign                                   | `=`                        |
| `^`          | Fill                                     | `ffill()`, `ffill!()`      |
| `^`          | Coalesce                                 | `append!()`                |
| `,`          | Join                                     | `<-`                       |
| `'`          | Compose                                  |                            |
| `0: 1: 2:`   | File Text, File Binary, Dynamic Load     | `loadText()`, `saveText()` |
| `0 ±1 ±2 ±n` | write to console, stdout, stderr, handle n | `print()`                  |

### 3.4 副词

kdb+ 和 DolphinDB 中的副词，即高阶函数，是以一个函数与数据对象作为输入的函数，用以扩展或增强函数或者运算符的功能。输入数据首先以一种预设的方式被分解成多个数据块（可能重叠），然后将函数应用于每个数据块，最后将所有的结果组合为一个对象返回。

kdb+ 和 DolphinDB 高阶函数的输入数据均可为标量、向量、矩阵、字典或表。在DolphinDB中，使用高阶函数时，一个向量被分解成多个标量，一个矩阵被分解成多列（向量），一个表被分解成多行（字典）。在组装阶段，标量类型合并组成一个向量，向量合并成一个矩阵，字典合并成一张表。DolphinDB 高阶函数按元素遍历向量，按列遍历矩阵，按行遍历表。

#### `'` quote <!-- omit in toc -->

| **kdb+ 含义**          | **DolphinDB**      |
| -------------------- | ------------------ |
| Each, each           | `each()` 或 `:E`    |
| Case                 |                    |
| Each Parallel, peach | `peach()`          |
| Each Prior, prior    | `eachPre()` 或 `:P` |

#### 其他副词 <!-- omit in toc -->

| **kdb+ 符号** | **kdb+ 含义** | **DolphinDB**         |
| ----------- | ----------- | --------------------- |
| `/:`        | Each Right  | `eachRight()` 或 `:R`  |
| `\:`        | Each Left   | `eachLeft()` 或 `:L`   |
| `/`         | Over, over  | `reduce()` 或 `:T`     |
| `\`         | Scan, scan  | `accumulate()` 或 `:A` |

### 3.5 执行控制

| **kdb+ 符号**                            | **kdb+ 含义**           | **DolphinDB**                            |
| -----------------------------------------| ----------------------- | ---------------------------------------- |
| `.[f;x;e]`                               | Trap                    | try-catch                                |
| `@[f;x;e]`                               | Trap-At                 | try-catch                                |
| `:`                                      | Return                  | return                                   |
| `'`                                      | Signal                  | throw                                    |
| do                                       |                         | do-while                                 |
| exit                                     |                         | quit                                     |
| while                                    |                         | do-while                                 |
| if                                       |                         | if-else                                  |
| `$[x;y;z]`                               | Cond                    | if-else                                  |
| `x:y`                                    | Assign                  | `<variable>=<object>`                    |
| `x[i]:y`                                 | Indexed assign          | `<variable>[index]=<object>`             |
| `x op:y`, `op:[x;y]`或`x[i]op:y`, `op:[x i;y]` | Assign through operator | 支持以下运算符扩展的赋值：`+=`, `-=`. `*=`, `/=`, `\=` |
| `\t`                                     | Timer                   | timer                                    |

**说明：**
- DolphinDB 支持多变量赋值，可将一个或多个值一次性赋予多个变量。
- DolphinDB 支持引用赋值，直接引用原值的内存地址以避免不必要的拷贝，有效地节约内存空间。例如，对于交换两个变量的值的操作，引用赋值的效率高于按值赋值的效率。

```
n=20000000;
x=rand(200000.0, n);
y=rand(200000.0, n);

timer x, y = y, x;        // Time elapsed: 1240.119 ms
timer {&t=x;&x=y;&y=t;}      // Time elapsed: 0.004 ms
```

- DolphinDB 允许用户通过取消变量或函数定义来手动释放内存。使用 `undef` 或 `<variable>=NULL`，详情请参考[DolphinDB 2.0用户手册](https://dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/u/undef.html)。

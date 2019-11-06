## DolphinDB Python API

DolphinDB Python API 支持Python 3.4~3.7版本。

通过执行如下指令进行安装。

```Console
$ pip install dolphindb
```

由于实现原因，Python API暂时无法与Linux平台Jupyter Notebook共同使用，将在后续解决这个问题。

下面主要介绍以下内容：

- [建立DolphinDB连接](#1-建立dolphindb连接)
- [运行DolphinDB脚本](#2-运行dolphindb脚本)
- [运行DolphinDB函数](#3-运行dolphindb函数)
- [上传本地对象到DolphinDB服务器](#4-上传本地对象到dolphindb服务器)
- [导入数据到DolphinDB服务器](#5-导入数据到dolphindb服务器)
- [从DolphinDB数据库中加载数据](#6-从dolphindb数据库中加载数据)
- [追加数据到DolphinDB数据表](#7-追加数据到dolphindb数据表)
- [操作数据库和表](#8-操作数据库和表)
- [SQL查询](#9-sql查询)
- [更多实例](#10-更多实例)
- [Python Streaming API](#python-streaming-api)

### 1 建立DolphinDB连接

Python API 提供的最核心的类是Session类。Python应用通过会话与DolphinDB服务器上执行脚本和函数，并在两者之间双向传递数据。Session类方法中，最为常用的方法如下：

| 方法名        | 详情          |
|:------------- |:-------------|
|connect(host, port, [username, password])|将会话连接到DolphinDB服务器|
|login(username,password,enableEncryption)|登陆服务器|
|run(script)|将脚本在DolphinDB服务器运行|
|run(functionName,args)|调用DolphinDB服务器上的函数|
|upload(variableObjectMap)|将本地数据对象上传到DolphinDB服务器|
|close()|关闭当前会话|

在下面的例子中，通过import语句导入API以后，在Python中创建一个session，然后使用指定的域名或IP地址和端口号把该会话连接到DolphinDB服务器。在执行以下Python脚本前，需要先启动DolphinDB服务器。

```Python
import dolphindb as ddb
s = ddb.session()
s.connect("localhost", 8848)
```

如果需要使用用户名和密码连接DolphinDB，使用以下脚本：

```Python
s.connect("localhost", 8848, YOUR_USER_NAME, YOUR_PASS_WORD)
```

DolphinDB默认的管理员用户名为“admin”，密码为“123456”，并且默认会在连接时对YOUR_USER_NAME和YOUR_PASS_WORD进行加密传输。

### 2 运行DolphinDB脚本

通过`run(script)`方法运行DolphinDB脚本,如果脚本在DolphinDB中返回对象，`run`会把DolphinDB对象转换成Python中的对象。

```Python
a=s.run("`IBM`GOOG`YHOO")
repr(a)

# output
"array(['IBM', 'GOOG', 'YHOO'], dtype='<U4')"
```

需要注意的是，脚本的最大长度为65,535字节。

### 3 运行DolphinDB函数

除了运行脚本之外，`run`命令可以直接在远程DolphinDB服务器上执行DolphinDB内置或用户自定义函数。`run`方法的第一个参数DolphinDB中的函数名，第二个参数是要在DolphinDB中调用的函数的参数。

下面的示例展示Python程序通过`run`调用DolphinDB内置的`add`函数。`add`函数有两个参数x和y。参数的存储位置不同，也会导致调用方式的不同。可能有以下三种情况：

* 所有参数都在DolphinDB Server端

若变量x和y已经通过Python程序在服务器端生成，

```Python
s.run("x = [1,3,5];y = [2,4,6]")
```

那么在Python端要对这两个向量做加法运算，只需直接使用`run(script)`即可。

```Python
a=s.run("add(x,y)")
repr(a)

# output
'array([ 3,  7, 11], dtype=int32)'
```

* 仅有一个参数在DolphinDB Server端存在

若变量x已经通过Python程序在服务器端生成，

```Python
s.run("x = [1,3,5]")
```

而参数y要在Python客户端生成，这时就需要使用“部分应用”方式，把参数x固化在`add`函数内。具体请参考[部分应用文档](https://www.dolphindb.com/cn/help/PartialApplication.html)。

```Python
import numpy as np

y=np.array([1,2,3])
result=s.run("add{x,}", y)
repr(result)
result.dtype

# output
'array([2, 5, 8])'
dtype('int64')
```

* 两个参数都待由Python客户端赋值

```Python
import numpy as np

x=np.array([1.5,2.5,7])
y=np.array([8.5,7.5,3])
result=s.run("add", x, y)
repr(result)
result.dtype

# output
'array([10., 10., 10.])'
dtype('float64')
```

### 4 上传本地对象到DolphinDB服务器

#### 4.1 使用`upload`函数上传

Python API提供`upload`函数将Python对象上传到DolphinDB服务器。`upload`函数的输入是Python的字典对象，它的key对应的是DolphinDB中的变量名，value对应的是Python对象，可以是Numbers，Strings，Lists，DataFrame等数据对象。

* 上传 Python list

```Python
a = [1,2,3.0]
s.upload({'a':a})
a_new = s.run("a")
a_type = s.run("typestr(a)")
print(a_new)
print(a_type)

# output
[1. 2. 3.]
ANY VECTOR
```

注意，Python中像a=[1,2,3.0]这种类型的内置list，上传到DolphinDB后，会被识别为any vector。这种情况下，建议使用numpy.array代替内置list，即通过a=numpy.array([1,2,3.0],dtype=numpy.double)指定统一的数据类型，这样上传a以后，a会被识别为double类型的向量。

* 上传 NumPy array

```Python
import numpy as np

arr = np.array([1,2,3.0],dtype=np.double)
s.upload({'arr':arr})
arr_new = s.run("arr")
arr_type = s.run("typestr(arr)")
print(arr_new)
print(arr_type)

# output
[1. 2. 3.]
FAST DOUBLE VECTOR
```

* 上传pandas DataFrame

```Python
import pandas as pd
import numpy as np

df = pd.DataFrame({'id': np.int32([1, 2, 3, 4, 3]), 'value':  np.double([7.8, 4.6, 5.1, 9.6, 0.1]), 'x': np.int32([5, 4, 3, 2, 1])})
s.upload({'t1': df})
print(s.run("t1.value.avg()"))

# output
5.44
```
#### 4.2 使用`table`函数上传

在Python中使用`table`函数创建DolphinDB表对象，并上传到server端，`table`函数的输入可以是字典、DataFrame或DolphinDB中的表名。

* 上传dict

下面的例子定义了一个函数`createDemoDict()`，该函数创建并返回一个字典。

```Python
import numpy as np

def createDemoDict():
    return {'id': [1, 2, 2, 3],
            'date': np.array(['2019-02-04', '2019-02-05', '2019-02-09', '2019-02-13'], dtype='datetime64[D]'),
            'ticker': ['AAPL', 'AMZN', 'AMZN', 'A'],
            'price': [22, 3.5, 21, 26]}
```

通过自定义的函数创建一个字典之后，调用`table`函数将该字典上传到DolphinDB server端，并指定参数将该表表命名为"testDict"，再通过API提供的`loadTable`函数读取和查看表内数据。

```Python
import numpy as np

# save the table to DolphinDB server as table "testDict"
dt = s.table(data=createDemoDict(), tableAliasName="testDict")

# load table "testDict" on DolphinDB server 
print(s.loadTable("testDict").toDF())

# output
   id       date ticker  price
0   1 2019-02-04   AAPL   22.0
1   2 2019-02-05   AMZN    3.5
2   2 2019-02-09   AMZN   21.0
3   3 2019-02-13      A   26.0
```

**请注意**，在不指定表名的情况下，每次调用`table`会在DolphinDB服务端创建一个临时表，因此，若在循环中反复调用`table`函数，将会在DolphinDB服务端产生大量的临时表，极易造成内存溢出。如果只是想把表上传后立刻插入到内存表或DFS表中，而不进行其他操作，请参考[第7节](#7-追加数据到dolphindb数据表)。

* 上传pandas DataFrame

下面的例子定义了一个函数`createDemoDataFrame()`，该函数创建并返回一个pandas的DataFrame对象，该对象覆盖了DolphinDB提供的所有数据类型。

```Python
import pandas as pd

def createDemoDataFrame():
    data = {'cid': np.array([1, 2, 3], dtype=np.int32),
            'cbool': np.array([True, False, np.nan], dtype=np.bool),
            'cchar': np.array([1, 2, 3], dtype=np.int8),
            'cshort': np.array([1, 2, 3], dtype=np.int16),
            'cint': np.array([1, 2, 3], dtype=np.int32),
            'clong': np.array([0, 1, 2], dtype=np.int64),
            'cdate': np.array(['2019-02-04', '2019-02-05', ''], dtype='datetime64[D]'),
            'cmonth': np.array(['2019-01', '2019-02', ''], dtype='datetime64[M]'),
            'ctime': np.array(['2019-01-01 15:00:00.706', '2019-01-01 15:30:00.706', ''], dtype='datetime64[ms]'),
            'cminute': np.array(['2019-01-01 15:25', '2019-01-01 15:30', ''], dtype='datetime64[m]'),
            'csecond': np.array(['2019-01-01 15:00:30', '2019-01-01 15:30:33', ''], dtype='datetime64[s]'),
            'cdatetime': np.array(['2019-01-01 15:00:30', '2019-01-02 15:30:33', ''], dtype='datetime64[s]'),
            'ctimestamp': np.array(['2019-01-01 15:00:00.706', '2019-01-01 15:30:00.706', ''], dtype='datetime64[ms]'),
            'cnanotime': np.array(['2019-01-01 15:00:00.80706', '2019-01-01 15:30:00.80706', ''], dtype='datetime64[ns]'),
            'cnanotimestamp': np.array(['2019-01-01 15:00:00.80706', '2019-01-01 15:30:00.80706', ''], dtype='datetime64[ns]'),
            'cfloat': np.array([2.1, 2.658956, np.NaN], dtype=np.float32),
            'cdouble': np.array([0., 47.456213, np.NaN], dtype=np.float64),
            'csymbol': np.array(['A', 'B', '']),
            'cstring': np.array(['abc', 'def', ''])}
    return pd.DataFrame(data)
```

通过自定义的函数创建一个字典之后，调用`Table`函数将该字典上传到DolphinDB server端，命名为"testDataFrame"，再通过API提供的`loadTable`函数读取和查看表内数据。

```Python
import pandas as pd

# save the table to DolphinDB server as table "testDataFrame"
dt = s.table(data=createDemoDataFrame(), tableAliasName="testDataFrame")

# load table "testDataFrame" on DolphinDB server 
print(s.loadTable("testDataFrame").toDF())

# output
   cid  cbool  cchar  cshort  ...    cfloat    cdouble csymbol cstring
0    1   True      1       1  ...  2.100000   0.000000       A     abc
1    2  False      2       2  ...  2.658956  47.456213       B     def
2    3   True      3       3  ...       NaN        NaN                
[3 rows x 19 columns]
```

### 5 导入数据到DolphinDB服务器

DolphinDB数据库根据存储方式可以分为3种类型：内存数据库、本地文件系统的数据库和分布式文件系统（DFS）中的数据库。DFS能够自动管理数据存储和备份，并且DolphinDB在DFS模式中性能达到最优。因此，推荐用户使用分布式文件系统，部署方式请参考[多服务器集群部署](https://github.com/dolphindb/Tutorials_CN/blob/master/multi_machine_cluster_deploy.md)。为简化起见，在本教程中也给出了本地文件系统数据库的例子。

下面的例子中，我们使用了一个csv文件：[example.csv](data/example.csv)。

#### 5.1 把数据导入到内存表中

可以使用`loadText`方法把文本文件导入到DolphinDB的内存表中。该方法会在Python中返回一个DolphinDB内存表对象。可以使用`toDF`方法把Python中的DolphinDB Table对象转换成pandas DataFrame。

```Python
WORK_DIR = "C:/DolphinDB/Data"

# return a DolphinDB table object in Python
trade=s.loadText(WORK_DIR+"/example.csv")

# convert the imported DolphinDB table object into a pandas DataFrame
df = trade.toDF()
print(df)

# output
TICKER        date       VOL        PRC        BID       ASK
0       AMZN  1997.05.16   6029815   23.50000   23.50000   23.6250
1       AMZN  1997.05.17   1232226   20.75000   20.50000   21.0000
2       AMZN  1997.05.20    512070   20.50000   20.50000   20.6250
3       AMZN  1997.05.21    456357   19.62500   19.62500   19.7500
4       AMZN  1997.05.22   1577414   17.12500   17.12500   17.2500
5       AMZN  1997.05.23    983855   16.75000   16.62500   16.7500
...
13134   NFLX  2016.12.29   3444729  125.33000  125.31000  125.3300
13135   NFLX  2016.12.30   4455012  123.80000  123.80000  123.8300

```
`loadText`函数导入文件时的默认分隔符是“,”。用户也可指定其他符号作为分隔符。例如，导入表格形式的文本文件：

```Python
t1=s.loadText(WORK_DIR+"/t1.tsv", '\t')
```

#### 5.2 把数据导入到分区数据库中

如果需要导入的文件比可用内存大，可把数据导入到分区数据库中。

#### 5.2.1 创建分区数据库

创建了分区数据库后，一般不能改变分区方案。唯一的例外是值分区（或者复合分区中的值分区）创建后，可以添加分区。为了保证使用的不是已经存在的数据库，需要先检查数据库valuedb是否存在。如果存在，将其删除。

```Python
if s.existsDatabase(WORK_DIR+"/valuedb"):
    s.dropDatabase(WORK_DIR+"/valuedb")
```

使用`database`方法创建值分区（VALUE）的数据库。由于example.csv文件中只有3个股票代码，使用股票代码作为分区字段。参数partitions表示分区方案。下例中，我们先导入DolphinDB的关键字，再创建数据库。

```Python
import dolphindb.settings as keys

# 'db' indicates the database handle name on the DolphinDB server.
s.database('db', partitionType=keys.VALUE, partitions=['AMZN','NFLX', 'NVDA'], dbPath=WORK_DIR+'/valuedb')
```

上述创建数据库的语句等价于：

```Python
s.run("db=database(WORK_DIR+'/valuedb', VALUE, ['AMZN','NFLX', 'NVDA'])")
```

在DFS（分布式文件系统）创建分区数据库，只需把数据库的路径改成以`dfs://`开头。下面的例子需要在集群中执行。请参考教程[多服务器集群部署](https://github.com/dolphindb/Tutorials_CN/blob/master/multi_machine_cluster_deploy.md)配置集群。

```Python
import dolphindb.settings as keys

s.database('db', partitionType=keys.VALUE, partitions=['AMZN','NFLX', 'NVDA'], dbPath='dfs://valuedb')
#equals to s.run("db=database('dfs://valuedb', VALUE, ['AMZN','NFLX', 'NVDA'])")
```

除了值分区（VALUE），DolphinDB还支持顺序分区（SEQ）、哈希分区（HASH）、范围分区（RANGE）、列表分区（LIST）与组合分区（COMPO），具体请参见[database函数](https://www.dolphindb.cn/cn/help/database1.html)。

#### 5.2.2 创建分区表，并导入数据到表中

创建数据库后，可使用函数`loadTextEx`把文本文件导入到分区数据库的分区表中。如果分区表不存在，函数会自动生成该分区表并把数据追加到表中。如果分区表已经存在，则直接把数据追加到分区表中。

函数`loadTextEx`的各个参数如下：
- dbPath表示数据库路径
- tableName表示分区表的名称
- partitionColumns表示分区列
- filePath表示文本文件的绝对路径
- delimiter表示文本文件的分隔符（默认分隔符是逗号）

下面的例子使用函数`loadTextEx`创建了分区表trade，并把example.csv中的数据追加到表中。

```Python
import dolphindb.settings as keys

if s.existsDatabase(WORK_DIR+"/valuedb"):
    s.dropDatabase(WORK_DIR+"/valuedb")
s.database('db', partitionType=keys.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")

trade = s.loadTextEx("db",  tableName='trade',partitionColumns=["TICKER"], filePath=WORK_DIR + "/example.csv")
print(trade.toDF())

# output
TICKER        date       VOL        PRC        BID       ASK
0       AMZN  1997.05.16   6029815   23.50000   23.50000   23.6250
1       AMZN  1997.05.17   1232226   20.75000   20.50000   21.0000
2       AMZN  1997.05.20    512070   20.50000   20.50000   20.6250
3       AMZN  1997.05.21    456357   19.62500   19.62500   19.7500
4       AMZN  1997.05.22   1577414   17.12500   17.12500   17.2500
5       AMZN  1997.05.23    983855   16.75000   16.62500   16.7500
...
13134   NFLX  2016.12.29   3444729  125.33000  125.31000  125.3300
13135   NFLX  2016.12.30   4455012  123.80000  123.80000  123.8300

[13136 rows x 6 columns]

#返回表中的行数：
print(trade.rows)
13136

#返回表中的列数：
print(trade.cols)
6

#展示表的结构：
print(trade.schema)
     name typeString  typeInt
0  TICKER     SYMBOL       17
1    date       DATE        6
2     VOL        INT        4
3     PRC     DOUBLE       16
4     BID     DOUBLE       16
5     ASK     DOUBLE       16
```

访问表：

```Python
trade = s.table(dbPath=WORK_DIR+"/valuedb", data="trade")
```

#### 5.3 把数据导入到内存的分区表中

#### 5.3.1 使用`loadTextEx`

可把数据导入到内存的分区表中。由于内存分区表使用了并行计算，因此对它进行操作比对内存未分区表进行操作要快。

使用`loadTextEx`函数创建内存分区数据库时，dbPath参数为空字符串。

```Python
import dolphindb.settings as keys

s.database('db', partitionType=keys.VALUE, partitions=["AMZN","NFLX","NVDA"], dbPath="")

trade=s.loadTextEx(dbPath="db", partitionColumns=["TICKER"], tableName='trade', filePath=WORK_DIR + "/example.csv")
```

#### 5.3.2 使用`ploadText`

`ploadText`函数可以并行加载文本文件到内存分区表中。它的加载速度要比`loadText`函数快。

```Python
trade=s.ploadText(WORK_DIR+"/example.csv")
print(trade.rows)

# output
13136
```

### 6 从DolphinDB数据库中加载数据

#### 6.1 使用`loadTable`函数

可以使用`loadTable`从数据库中加载数据。参数tableName表示分区表的名称，dbPath表示数据库的路径。如果没有指定dbPath，`loadTable`函数会加载内存中的表。

对于分区表，若参数memoryMode=true且未指定partition参数，把表中的所有数据加载到内存的分区表中；若参数memoryMode=true且指定了partition参数，则只加载指定的分区数据到内存的分区表中；如果参数memoryMode=false，只把元数据加载到内存。

#### 6.1.1 加载整个表的数据

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
trade.toDF()

# output
TICKER        date       VOL        PRC        BID       ASK
0       AMZN  1997.05.16   6029815   23.50000   23.50000   23.6250
1       AMZN  1997.05.17   1232226   20.75000   20.50000   21.0000
2       AMZN  1997.05.20    512070   20.50000   20.50000   20.6250
3       AMZN  1997.05.21    456357   19.62500   19.62500   19.7500
4       AMZN  1997.05.22   1577414   17.12500   17.12500   17.2500
5       AMZN  1997.05.23    983855   16.75000   16.62500   16.7500
...
13134   NFLX  2016.12.29   3444729  125.33000  125.31000  125.3300
13135   NFLX  2016.12.30   4455012  123.80000  123.80000  123.8300

[13136 rows x 6 columns]
```

#### 6.1.2 加载指定分区的数据

只加载AMZN分区的数据：

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", partitions="AMZN")
print(trade.rows)

# output
4941
```

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", partitions=["NFLX","NVDA"], memoryMode=True)
print(trade.rows)

# output
8195
```

#### 6.2 使用`loadTableBySQL`函数

`loadTableBySQL`函数把磁盘上的分区表中满足SQL语句过滤条件的数据加载到内存的分区表中。

```Python
import os
import dolphindb.settings as keys

if s.existsDatabase(WORK_DIR+"/valuedb"  or os.path.exists(WORK_DIR+"/valuedb")):
    s.dropDatabase(WORK_DIR+"/valuedb")
s.database(dbName='db', partitionType=keys.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")
t = s.loadTextEx("db",  tableName='trade',partitionColumns=["TICKER"], filePath=WORK_DIR + "/example.csv")

trade = s.loadTableBySQL(tableName="trade", dbPath=WORK_DIR+"/valuedb", sql="select * from trade where date>2010.01.01")
print(trade.rows)

# output
5286
```

#### 6.3 从DolphinDB下载数据到Python时的数据转换

#### 6.3.1 数据形式的转换

DolphinDB Python API使用Python原生的各种形式的数据对象来存放DolphinDB服务端返回的数据，下面给出从DolphinDB的数据对象到Python的数据对象的映射关系。

|DolphinDB|Python|DolphinDB生成数据|Python数据|
|-------------|----------|-------------|-----------|
|scalar|Numbers, Strings, NumPy.datetime64|见6.3.2小节|见6.3.2小节
|vector|NumPy.array|1..3|[1 2 3]
|pair|Lists|1:5|[1, 5]
|matrix|Lists|1..6$2:3|[array([[1, 3, 5],[2, 4, 6]], dtype=int32), None, None]
|set|Sets|set(3 5 4 6)|{3, 4, 5, 6}|
|dictionary|Dictionaries|dict(['IBM','MS','ORCL'], 170.5 56.2 49.5)|{'MS': 56.2, 'IBM': 170.5, 'ORCL': 49.5}|
|table|pandas.DataFame|见[第6.1小节](#61-使用loadtable函数)|见[第6.1小节](#61-使用loadtable函数)

#### 6.3.2 数据类型的转换

下表展示了从DolphinDB数据库中通过`toDF()`函数下载数据到Python时，数据类型的转换。需要指出的是：
- DolphinDB CHAR类型会被转换成Python int64类型。对此结果，用户可以使用Python的`chr`函数使之转换为字符。
- 由于Python pandas中所有有关时间的数据类型均为datetime64，DolphinDB中的所有时间类型数据[均会被转换为datetime64类型](https://github.com/pandas-dev/pandas/issues/6741#issuecomment-39026803)。MONTH类型，如2012.06M，会被转换为2012-06-01（即月份当月的第一天）。
- TIME, MINUTE, SECOND与NANOTIME类型不包含日期信息，转换时会自动添加1970-01-01，例如13:30m会被转换为1970-01-01 13:30:00。

|DolphinDB类型|Python类型|DolphinDB数据|Python数据|
|-------------|----------|-------------|-----------|
|BOOL|bool|[true,00b]|[True, nan]|
|CHAR|int64|[12c,00c]|[12, nan]|
|SHORT|int64|[12,00h]|[12, nan]|
|INT|int64|[12,00i]|[12, nan]|
|LONG|int64|[12l,00l]|[12, nan]|
|DOUBLE|float64|[3.5,00F]|[3.5,nan]|
|FLOAT|float64|[3.5,00f]|[3.5, nan]|
|SYMBOL|object|symbol(["AAPL",NULL])|["AAPL",""]|
|STRING|object|["AAPL",string()]|["AAPL", ""]|
|DATE|datetime64|[2012.6.12,date()]|[2012-06-12, NaT]|
|MONTH|datetime64|[2012.06M, month()]|[2012-06-01, NaT]|
|TIME|datetime64|[13:10:10.008,time()]|[1970-01-01 13:10:10.008, NaT]|
|MINUTE|datetime64|[13:30,minute()]|[1970-01-01 13:30:00, NaT]|
|SECOND|datetime64|[13:30:10,second()]|[1970-01-01 13:30:10, NaT]|
|DATETIME|datetime64|[2012.06.13 13:30:10,datetime()]|[2012-06-13 13:30:10,NaT]|
|TIMESTAMP|datetime64|[2012.06.13 13:30:10.008,timestamp()]|[2012-06-13 13:30:10.008,NaT]|
|NANOTIME|datetime64|[13:30:10.008007006, nanotime()]|[1970-01-01 13:30:10.008007006,NaT]|
|NANOTIMESTAMP|datetime64|[2012.06.13 13:30:10.008007006,nanotimestamp()]|[2012-06-13 13:30:10.008007006,NaT]|

#### 6.4 缺失值处理

从DolphinDB下载数据到Python，并使用`toDF()`方法把DolphinDB数据转换为Python的DataFrame，DolphinDB中的逻辑型、数值型和时序类型的NULL值默认情况下是NaN、NaT，字符串的NULL值为空字符串。

### 7 追加数据到DolphinDB数据表

使用Python API的一个重要场景是，用户从其他数据库系统或是第三方Web API中取得数据后存入DolphinDB数据表中。本节将介绍通过Python API将取到的数据上传并保存到DolphinDB的数据表中。

DolphinDB数据表按存储方式分为三种:

- 内存表：数据仅保存在内存中，存取速度最快，但是节点关闭后数据就不存在了。
- 本地磁盘表：数据保存在本地磁盘上。可以从磁盘加载到内存。
- 分布式表：数据分布在不同的节点，通过DolphinDB的分布式计算引擎，仍然可以像本地表一样做统一查询。

#### 7.1 追加数据到DolphinDB内存表

DolphinDB提供多种方式来保存数据到内存表：

- 通过`insert into`语句保存数据
- 通过`tableInsert`函数批量保存多条数据

下面分别介绍三种方式保存数据的实例，在例子中使用到的数据表有4个列，分别是INT,DATE，STRINR，DOUBLE类型，列名分别为id, date，ticker和price。
在Python中执行以下脚本，该脚本通过`run`函数在DolphinDB服务器上创建内存表：

```Python
import dolphindb as ddb

s = ddb.session()
s.connect(host, port, "admin", "123456")

# 生成内存表
script = """t = table(1:0,`id`date`ticker`price, [INT,DATE,STRING,DOUBLE])
share t as tglobal"""
s.run(script)
```

上面的例子中，我们通过`table`函数在DolphinDB server端来创建表，指定了表的容量和初始大小、列名和数据类型。由于内存表是会话隔离的，所以普通内存表只有当前会话可见。为了让多个客户端可以同时访问t，我们使用`share`在会话间共享内存表。

#### 7.1.1 使用`INSERT INTO`语句追加数据

我们可以采用如下方式保存单条数据。

```Python
import numpy as np

script = "insert into tglobal values(%s, date(%s), %s, %s);tglobal"% (1, np.datetime64("2019-01-01").astype(np.int64), '`AAPL', 5.6)
s.run(script)
```

**请注意**，由于DolphinDB的内存表并不提供数据类型自动转换的功能，因而我们在向内存表追加数据时，需要在服务端显示地调用时间转换函数对时间类型的列进行转换，首先要确保插入的数据类型与内存表schema中的数据类型一致，再追加数据。

上例中，我们将numpy的时间类型强制转换成64位整型，并且在insert语句中显示地调用`date`函数，在服务端将时间列的整型数据转换成对应的类型。

我们也可以使用`INSERT INTO`语句一次性插入多条数据，实现如下:

```Python
import numpy as np
import random

rowNum = 5
ids = np.arange(1, rowNum+1, 1, dtype=np.int32)
dates = np.array(pd.date_range('4/1/2019', periods=rowNum), dtype='datetime64[D]')
tickers = np.repeat("AA", rowNum)
prices = np.arange(1, 0.6*(rowNum+1), 0.6, dtype=np.float64)
s.upload({'ids':ids, "dates":dates, "tickers":tickers, "prices":prices})
script = "insert into tglobal values(ids,dates,tickers,prices);"
s.run(script)
```

上例中，通过指定`date_range()`函数的dtype参数为`datetime64[D]`，生成了只含有日期的时间列，这与DolphinDB的date类型保持一致，因此直接通过insert语句插入数据，无需显示转换。若这里时间数据类型为datetime64，则需要这样追加数据到内存表：

```Python
script = "insert into tglobal values(ids,date(dates),tickers,prices);" 
s.run(script)
```

#### 7.1.2 使用`tableInsert`函数批量追加多条数据

若Python程序获取的数据可以组织成List方式，且保证数据类型正确的情况下，我们可以直接使用`tableInsert`函数来批量保存多条数据。这个函数可以接受多个数组作为参数，将数组追加到数据表中。这样做的好处是，可以在一次访问服务器请求中将上传数据对象和追加数据这两个步骤一次性完成，相比7.1.1小节中的做法减少了一次访问DolphinDB服务器的请求。

```Python
args = [ids, dates, tickers, prices]
s.run("tableInsert{tglobal}", args)
s.run("tglobal")
```

#### 7.1.3 使用`tableInsert`函数追加表

我可以通过`tableInsert`函数直接向内存表追加一个表，其中，时间列仍然需要特殊说明。

- 若表中没有时间列

我们可以直接通过部分应用的方式，将一个DataFrame直接上传到服务器并追加到内存表。

```Python
import pandas as pd

# 生成内存表
script = """t = table(1:0,`id`ticker`price, [INT,STRING,DOUBLE])
share t as tdglobal"""
s.run(script)

# 生成要追加的DataFrame
tb=pd.DataFrame({'id': [1, 2, 2, 3],
                 'ticker': ['AAPL', 'AMZN', 'AMZN', 'A'],
                 'price': [22, 3.5, 21, 26]})
s.run("tableInsert{tdglobal}",tb)
```

- 若表中有时间列

由于Python pandas中所有[有关时间的数据类型均为datetime64](https://github.com/pandas-dev/pandas/issues/6741#issuecomment-39026803)，上传一个DataFrame到DolphinDB以后所有时间类型的列均为nanotimestamp类型，因此在追加一个带有时间列的DataFrame时，我们需要在DolphinDB服务端对时间列进行数据类型转换：先将该DataFrame上传到服务端，通过select语句将表内的每一列都选出来，并进行时间类型转换（该例子将nanotimestamp类型转换为date类型），再追加到内存表中，具体如下：

```Python
import pandas as pd
tb=pd.DataFrame(createDemoDict())
s.upload({'tb':tb})
s.run("tableInsert(tglobal,(select id, date(date) as date, ticker, price from tb))")
```

把数据保存到内存表，还可以使用`append!`函数，它可以把一张表追加到另一张表。但是，一般不建议通过`append!`函数保存数据，因为`append!`函数会返回一个表的schema，增加通信量。

- 若表中没有时间列

```Python
import pandas as pd

# 生成内存表
script = """t = table(1:0,`id`ticker`price, [INT,STRING,DOUBLE])
share t as tdglobal"""
s.run(script)

# 生成要追加的DataFrame
tb=pd.DataFrame({'id': [1, 2, 2, 3],
                 'ticker': ['AAPL', 'AMZN', 'AMZN', 'A'],
                 'price': [22, 3.5, 21, 26]})
s.run("append!{tdglobal}",tb)
```

- 若表中有时间列

```Python
import pandas as pd
tb=pd.DataFrame(createDemoDict())
s.upload({'tb':tb})
s.run("append!(tglobal, (select id, date(date) as date, ticker, price from tb))")
```

#### 7.2 追加数据到本地磁盘表

本地磁盘表通用用于静态数据集的计算分析，既可以用于数据的输入，也可以作为计算的输出。它不支持事务，也不持支并发读写。

在Python中执行以下脚本，在DolphinDB server端创建一个本地磁盘表，使用`database`函数创建数据库，调用`saveTable`函数将内存表保存到磁盘中：

```Python
import dolphindb as ddb

s = ddb.session()
s.connect(host, port, "admin", "123456")

# 生成磁盘表
dbPath="/home/user/dbtest/testPython"
tableName='dt'
script = """t = table(100:0, `id`date`ticker`price, [INT,DATE,STRING,DOUBLE]); 
db = database('{db}'); 
saveTable(db, t, `{tb}); 
share t as tDiskGlobal;""".format(db=dbPath,tb=tableName)
s.run(script)
```

使用`tableInsert`函数是向本地磁盘表追加数据最为常用的方式。这个例子中，我们使用`tableInsert`向共享的内存表tDiskGlobal中插入数据，接着调用`saveTable`使插入的数据保存到磁盘上。请注意，对于本地磁盘表，`tableInsert`函数只把数据追加到内存，如果要保存到磁盘上，必须再次执行`saveTable`函数。

```Python
import numpy as np
import random

rowNum = 5
ids = np.arange(1, rowNum+1, 1, dtype=np.int32)
dates = np.array(pd.date_range('4/1/2019', periods=rowNum), dtype='datetime64[D]')
tickers = np.repeat("AA", rowNum)
prices = np.arange(1, 0.6*(rowNum+1), 0.6, dtype=np.float64)
args = [ids, dates, tickers, prices]
s.run("tableInsert{tDiskGlobal}", args)
s.run("saveTable(db,tDiskGlobal,`{tb});".format(tb=tableName))
```

与[追加表到内存表](#713-使用tableinsert函数追加表)类似，本地磁盘表也支持通过`tableInsert`函数和`append!`函数直接追加一个表，同样也需要区分有无时间列的情况，唯一的区别是，本地磁盘表在追加之后要执行`saveTable`函数来保存到磁盘上，具体操作过程不再赘述。

#### 7.3 追加数据到分布式表

分布式表是DolphinDB推荐在生产环境下使用的数据存储方式，它支持快照级别的事务隔离，保证数据一致性。分布式表支持多副本机制，既提供了数据容错能力，又能作为数据访问的负载均衡。下面的例子通过Python API把数据保存至分布式表。

请注意只有启用enableDFS=1的集群环境才能使用分布式表。

在DolphinDB中使用以下脚本创建分布式表，脚本中，`database`函数用于创建数据库，`createPartitionedTable`函数用于创建分区表。

```Python
import dolphindb as ddb

s = ddb.session()
s.connect(host, port, "admin", "123456")

# 生成分布式表
dbPath="dfs://testPython"
tableName='t1'
script = """
dbPath='{db}'
if(existsDatabase(dbPath))
	dropDatabase(dbPath)
db = database(dbPath, VALUE, 0..100)
t1 = table(10000:0,`id`cbool`cchar`cshort`cint`clong`cdate`cmonth`ctime`cminute`csecond`cdatetime`ctimestamp`cnanotime`cnanotimestamp`cfloat`cdouble`csymbol`cstring,[INT,BOOL,CHAR,SHORT,INT,LONG,DATE,MONTH,TIME,MINUTE,SECOND,DATETIME,TIMESTAMP,NANOTIME,NANOTIMESTAMP,FLOAT,DOUBLE,SYMBOL,STRING])
insert into t1 values (0,true,'a',122h,21,22l,2012.06.12,2012.06M,13:10:10.008,13:30m,13:30:10,2012.06.13 13:30:10,2012.06.13 13:30:10.008,13:30:10.008007006,2012.06.13 13:30:10.008007006,2.1f,2.1,'','')
t = db.createPartitionedTable(t1, `{tb}, `id)
t.append!(t1)""".format(db=dbPath,tb=tableName)
s.run(script)
```

DolphinDB提供`loadTable`方法来加载分布式表，通过`tableInsert`方式追加数据，具体的脚本示例如下。脚本中，我们通过自定义的函数`createDemoDataFrame()`创建一个DataFrame，再追加数据到DolphinDB数据表中。与内存表和磁盘表不同的是，分布式表在追加表的时候提供时间类型自动转换的功能，因此无需显示地进行类型转换。

```Python
tb = createDemoDataFrame()
s.run("tableInsert{{loadTable('{db}', `{tb})}}".format(db=dbPath,tb=tableName), tb)
```

把数据保存到分布式表，还可以使用`append!`函数，它可以把一张表追加到另一张表。但是，一般不建议通过append!函数保存数据，因为`append!`函数会返回一个表结构，增加通信量。

```Python
tb = createDemoDataFrame()
s.run("append!{{loadTable('{db}', `{tb})}}".format(db=dbPath,tb=tableName),tb)
```

### 8 操作数据库和表

#### 8.1 操作数据库和表的方法说明

除了第1节列出的常用方法之外，`Session`类还提供了一些与DolphinDB内置函数作用等同的方法，用于操作数据库和表，具体如下：

* 数据库相关

| 方法名        | 详情          |
|:------------- |:-------------|
|database|创建数据库|
|dropDatabase(dbPath)|删除数据库|
|dropPartition(dbPath, partitionPaths)|删除数据库的某个分区|
|existsDatabase|判断是否存在数据库|

* 表和分区相关

| 方法名        | 详情          |
|:------------- |:-------------|
|dropTable(dbPath, tableName)|删除数据库中的表|
|existsTable|判断是否存在表|
|loadTable|加载本地磁盘表或者分布式表到内存|
|table|创建表|

我们在Python中得到一个表对象以后，可以对这个对象调用如下的方法，这些方法是`Table`类方法。

| 方法名        | 详情          |
|:------------- |:-------------|
|append|向表中追加数据|
|drop(colNameList)|删除表中的某列|
|executeAs(tableName)|执行结果保存为指定表名的内存表|
|execute()|执行脚本。与`update`和`delete`一起使用|
|toDF()|把DolphinDB表对象转换成pandas的DataFrame对象|

以上只是列出其中最为常用的方法，关于`Session`类和`Table`类提供的所有方法请参见session.py和table.py文件。

**请注意**，Python API实质上封装了DolphinDB的脚本语言。Python代码被转换成DolphinDB脚本在DolphinDB服务器执行，执行结果保存到DolphinDB服务器或者序列化到Python客户端。例如，在Python客户端创建一个数据表时，有如下几种方式：

1.调用`Session`类提供的`table`方法：

```Python
tdata = {'id': [1, 2, 2, 3],
         'date': np.array(['2019-02-04', '2019-02-05', '2019-02-09', '2019-02-13'], dtype='datetime64[D]'),
         'ticker': ['AAPL', 'AMZN', 'AMZN', 'A'],
         'price': [22, 3.5, 21, 26]}
s.table(data=tdata).executeAs('tb')
```

2.调用`Session`类提供的`upload`方法：

```Python
tdata = pd.DataFrame({'id': [1, 2, 2, 3], 
                      'date': np.array(['2019-02-04', '2019-02-05', '2019-02-09', '2019-02-13'], dtype='datetime64[D]'),
                      'ticker': ['AAPL', 'AMZN', 'AMZN', 'A'], 
                      'price': [22, 3.5, 21, 26]})
s.upload({'tb': tdata})
```

3.调用`Session`类提供的`run`方法：
```Python
s.run("tb=table([1, 2, 2, 3] as id, [2019.02.04,2019.02.05,2019.02.09,2019.02.13] as date, ['AAPL','AMZN','AMZN','A'] as ticker, [22, 3.5, 21, 26] as price)")
```

以上3种方式都等价于在DolphinDB服务端调用`table`方法创建一个名为'tb'的内存数据表：

```
tb=table([1, 2, 2, 3] as id, [2019.02.04,2019.02.05,2019.02.09,2019.02.13] as date, ['AAPL','AMZN','AMZN','A'] as ticker, [22, 3.5, 21, 26] as price)
```

下面，我们在Python环境中调用`Session`类提供的各种方法创建分布式数据库和表，并向表中追加数据。

```Python
import dolphindb as ddb
import dolphindb.settings as keys
import numpy as np

s = ddb.session()
s.connect(HOST, PORT, "admin", "123456")
dbPath="dfs://testDB"
tableName='tb'
if s.existsDatabase(dbPath):
    s.dropDatabase(dbPath)
s.database('db', keys.VALUE, ["AAPL", "AMZN", "A"], dbPath)
tdata=s.table(data=createDemoDict()).executeAs("testDict")
s.run("db.createPartitionedTable(testDict, `{tb}, `ticker)".format(tb=tableName))
tb=s.loadTable(tableName, dbPath)
tb.append(tdata)
tb.toDF()

# output
    id       date ticker  price
 0   3 2019-02-13      A   26.0
 1   1 2019-02-04   AAPL   22.0
 2   2 2019-02-05   AMZN    3.5
 3   2 2019-02-09   AMZN   21.0
```

类似地，我们也可以在Python环境中直接调用`Session`类提供的`run`方法来创建数据库和表，再调用DolphinDB的内置函数`append！`来追加数据。需要注意的是，在Python客户端远程调用DolphinDB内置函数`append！`时，服务端会向客户端返回一个表结构，增加通信量。因此，我们建议通过`tableInsert`函数来追加数据。

```Python
import dolphindb as ddb
import numpy as np

s = ddb.session()
s.connect(HOST, PORT, "admin", "123456")
dbPath="dfs://testDB"
tableName='tb'
testDict=pd.DataFrame(createDemoDict())
script="""
dbPath='{db}'
if(existsDatabase(dbPath))
    dropDatabase(dbPath)
db=database(dbPath, VALUE, ["AAPL", "AMZN", "A"])
testDictSchema=table(5:0, `id`date`ticker`price, [INT,DATE,STRING,DOUBLE])
db.createPartitionedTable(testDictSchema, `{tb}, `ticker)""".format(db=dbPath,tb=tableName)
s.run(script)
# s.run("append!{{loadTable({db}, `{tb})}}".format(db=dbPath,tb=tableName),testDict)
s.run("tableInsert{{loadTable('{db}', `{tb})}}".format(db=dbPath,tb=tableName),testDict)
s.run("select * from loadTable('{db}', `{tb})".format(db=dbPath,tb=tableName))
```

上述两个例子等价于在DolphinDB服务端执行以下脚本，创建分布式数据库和表，并向表中追加数据。

```
login("admin","123456")
dbPath="dfs://testDB"
tableName=`tb
if(existsDatabase(dbPath))
    dropDatabase(dbPath)
db=database(dbPath, VALUE, ["AAPL", "AMZN", "A"])
testDictSchema=table(5:0, `id`date`ticker`price, [INT,DATE,STRING,DOUBLE])
tb=db.createPartitionedTable(testDictSchem, tableName, `ticker)
testDict=table([1, 2, 2, 3] as id, [2019.02.04,2019.02.05,2019.02.09,2019.02.13] as date, ['AAPL','AMZN','AMZN','A'] as ticker, [22, 3.5, 21, 26] as price)
tb.append!(testDict)
```

#### 8.2 操作数据库

#### 8.2.1 创建数据库

使用`database`创建分区数据库。

```Python
import dolphindb.settings as keys

s.database('db', partitionType=keys.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")
```

#### 8.2.2 删除数据库

使用`dropDatabase`删除数据库。

```Python
if s.existsDatabase(WORK_DIR+"/valuedb"):
    s.dropDatabase(WORK_DIR+"/valuedb")
```

#### 8.2.3 删除DFS数据库的分区

使用`dropPartition`删除DFS数据库的分区。

```Python
import dolphindb.settings as keys

if s.existsDatabase("dfs://valuedb"):
    s.dropDatabase("dfs://valuedb")
s.database('db', partitionType=keys.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath="dfs://valuedb")
trade=s.loadTextEx(dbPath="dfs://valuedb", partitionColumns=["TICKER"], tableName='trade', filePath=WORK_DIR + "/example.csv")
print(trade.rows)

# output
13136

s.dropPartition("dfs://valuedb", partitionPaths=["/AMZN", "/NFLX"])
trade = s.loadTable(tableName="trade", dbPath="dfs://valuedb")
print(trade.rows)
# output
4516

print(trade.select("distinct TICKER").toDF())

  distinct_TICKER
0            NVDA
```

#### 8.3 表操作

#### 8.3.1 加载数据库中的表

请参考[第6节](#6-从dolphindb数据库中加载数据)。

#### 8.3.2 数据表添加数据

我们可以通过`append`方法追加数据。

下面的例子把数据追加到磁盘上的分区表。如果需要使用追加数据后的表，需要重新把它加载到内存中。

```py
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.rows)

# output
13136

# take the top 10 rows of table "trade" on the DolphinDB server
t = trade.top(10).executeAs("top10")

trade.append(t)

# table "trade" needs to be reloaded in order to see the appended records
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print (trade.rows)

# output
13146
```

下面的例子把数据追加到内存表中。

```py
trade=s.loadText(WORK_DIR+"/example.csv")
t = trade.top(10).executeAs("top10")
t1=trade.append(t)

print(t1.rows)

# output
13146
```

关于追加表的具体介绍请参考[第7节](#7-追加数据到dolphindb数据表)。

#### 8.3.3 更新表

`update`只能用于更新内存表，并且必须和`execute`一起使用。

```Python
trade = s.loadTable(tableName="trade", dbPath=WORK_DIR+"/valuedb", memoryMode=True)
trade = trade.update(["VOL"],["999999"]).where("TICKER=`AMZN").where(["date=2015.12.16"]).execute()
t1=trade.where("ticker=`AMZN").where("VOL=999999")
print(t1.toDF())

# output

  TICKER        date     VOL        PRC        BID        ASK
0      AMZN  1997.05.15  999999   23.50000   23.50000   23.62500
1      AMZN  1997.05.16  999999   20.75000   20.50000   21.00000
2      AMZN  1997.05.19  999999   20.50000   20.50000   20.62500
3      AMZN  1997.05.20  999999   19.62500   19.62500   19.75000
4      AMZN  1997.05.21  999999   17.12500   17.12500   17.25000
...
4948   AMZN  1997.05.27  999999   19.00000   19.00000   19.12500
4949   AMZN  1997.05.28  999999   18.37500   18.37500   18.62500
4950   AMZN  1997.05.29  999999   18.06250   18.00000   18.12500

[4951 rows x 6 columns]
```

#### 8.3.4 删除表中的记录

`delete`必须与`execute`一起使用来删除表中的记录。

```Python
trade = s.loadTable(tableName="trade", dbPath=WORK_DIR+"/valuedb", memoryMode=True)
trade.delete().where('date<2013.01.01').execute()
print(trade.rows)

# output
3024
```

#### 8.3.5 删除表中的列

```Python
trade = s.loadTable(tableName="trade", dbPath=WORK_DIR + "/valuedb", memoryMode=True)
t1=trade.drop(['ask', 'bid'])
print(t1.top(5).toDF())

  TICKER        date      VOL     PRC
0   AMZN  1997.05.15  6029815  23.500
1   AMZN  1997.05.16  1232226  20.750
2   AMZN  1997.05.19   512070  20.500
3   AMZN  1997.05.20   456357  19.625
4   AMZN  1997.05.21  1577414  17.125
```

#### 8.3.6 删除表

```Python
s.dropTable(WORK_DIR + "/valuedb", "trade")
```

### 9 SQL查询

DolphinDB提供了灵活的方法来生成SQL语句。

#### 9.1 `select`

#### 9.1.1 使用一系列的列名作为输入内容

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", memoryMode=True)
print(trade.select(['ticker','date','bid','ask','prc','vol']).toDF())

# output
  TICKER        date      VOL     PRC     BID     ASK
0   AMZN  1997.05.15  6029815  23.500  23.500  23.625
1   AMZN  1997.05.16  1232226  20.750  20.500  21.000
2   AMZN  1997.05.19   512070  20.500  20.500  20.625
3   AMZN  1997.05.20   456357  19.625  19.625  19.750
4   AMZN  1997.05.21  1577414  17.125  17.125  17.250
...

```
可以使用`showSQL`来展示SQL语句。

```Python
print(trade.select(['ticker','date','bid','ask','prc','vol']).where("date=2012.09.06").where("vol<10000000").showSQL())

# output
select ticker,date,bid,ask,prc,vol from T64afd5a6 where date=2012.09.06 and vol<10000000
```

#### 9.1.2 使用字符串作为输入内容

```Python
print(trade.select("ticker,date,bid,ask,prc,vol").where("date=2012.09.06").where("vol<10000000").toDF())

# output
  ticker       date        bid     ask     prc      vol
0   AMZN 2012-09-06  251.42999  251.56  251.38  5657816
1   NFLX 2012-09-06   56.65000   56.66   56.65  5368963
...
```

#### 9.2 `top`

`top`用于取表中的前n条记录。

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
trade.top(5).toDF()

# output
      TICKER        date       VOL        PRC        BID       ASK
0       AMZN  1997.05.16   6029815   23.50000   23.50000   23.6250
1       AMZN  1997.05.17   1232226   20.75000   20.50000   21.0000
2       AMZN  1997.05.20    512070   20.50000   20.50000   20.6250
3       AMZN  1997.05.21    456357   19.62500   19.62500   19.7500
4       AMZN  1997.05.22   1577414   17.12500   17.12500   17.2500

```

#### 9.3 `where`

`where`用于过滤数据。

#### 9.3.1 多个条件过滤

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", memoryMode=True)

# use chaining WHERE conditions and save result to DolphinDB server variable "t1" through function "executeAs"
t1=trade.select(['date','bid','ask','prc','vol']).where('TICKER=`AMZN').where('bid!=NULL').where('ask!=NULL').where('vol>10000000').sort('vol desc').executeAs("t1")
print(t1.toDF())
# output

         date    bid      ask     prc        vol
0  2007.04.25  56.80  56.8100  56.810  104463043
1  1999.09.29  80.75  80.8125  80.750   80380734
2  2006.07.26  26.17  26.1800  26.260   76996899
3  2007.04.26  62.77  62.8300  62.781   62451660
4  2005.02.03  35.74  35.7300  35.750   60580703
...
print(t1.rows)

765
```

可以使用`showSQL`来查看SQL语句。

```Python
print(trade.select(['date','bid','ask','prc','vol']).where('TICKER=`AMZN').where('bid!=NULL').where('ask!=NULL').where('vol>10000000').sort('vol desc').showSQL())

# output
select date,bid,ask,prc,vol from Tff260d29 where TICKER=`AMZN and bid!=NULL and ask!=NULL and vol>10000000 order by vol desc
```

#### 9.3.2 使用字符串作为输入内容

`select`的输入内容可以是包含多个列名的字符串，`where`的输入内容可以是包含多个条件的字符串。

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.select("ticker, date, vol").where("bid!=NULL, ask!=NULL, vol>50000000").toDF())

# output
   ticker        date        vol
0    AMZN  1999.09.29   80380734
1    AMZN  2000.06.23   52221978
2    AMZN  2001.11.26   51543686
3    AMZN  2002.01.22   57235489
4    AMZN  2005.02.03   60580703
...
38   NVDA  2016.11.11   54384267
39   NVDA  2016.12.28   57384116
40   NVDA  2016.12.29   54384676
```

#### 9.4 `groupby`

`groupby`后面需要使用聚合函数，如`count`、`sum`、`agg`和`agg2`。

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.select('count(*)').groupby(['ticker']).sort(bys=['ticker desc']).toDF())

# output
  ticker  count_ticker
0   NVDA          4516
1   NFLX          3679
2   AMZN          4941

```

分别计算每个股票的vol总和与prc总和。

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.select(['vol','prc']).groupby(['ticker']).sum().toDF())

# output

   ticker      sum_vol       sum_prc
0   AMZN  33706396492  772503.81377
1   NFLX  14928048887  421568.81674
2   NVDA  46879603806  127139.51092
```

`groupby`与`having`一起使用：

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.select('count(ask)').groupby(['vol']).having('count(ask)>1').toDF())
# output

       vol  count_ask
0   579392          2
1  3683504          2
2  5732076          2
3  6299736          2
4  6438038          2
5  6946976          2
6  8160197          2
7  8924303          2
...

```

#### 9.5 `contextby`

`contextby`与`groupby`相似，区别在于`groupby`为每个组返回一个标量，但是`contextby`为每个组返回一个向量。每组返回的向量长度与这一组的行数相同。

```Python
df= s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb").contextby('ticker').top(3).toDF()
print(df)

  TICKER       date      VOL      PRC      BID      ASK
0   AMZN 1997-05-15  6029815  23.5000  23.5000  23.6250
1   AMZN 1997-05-16  1232226  20.7500  20.5000  21.0000
2   AMZN 1997-05-19   512070  20.5000  20.5000  20.6250
3   NFLX 2002-05-23  7507079  16.7500  16.7500  16.8500
4   NFLX 2002-05-24   797783  16.9400  16.9400  16.9500
5   NFLX 2002-05-28   474866  16.2000  16.2000  16.3700
6   NVDA 1999-01-22  5702636  19.6875  19.6250  19.6875
7   NVDA 1999-01-25  1074571  21.7500  21.7500  21.8750
8   NVDA 1999-01-26   719199  20.0625  20.0625  20.1250

```

```Python
df= s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb").select("TICKER, month(date) as month, cumsum(VOL)").contextby("TICKER,month(date)").toDF()
print(df)

    TICKER     month  cumsum_VOL
0       AMZN  1997.05M     6029815
1       AMZN  1997.05M     7262041
2       AMZN  1997.05M     7774111
3       AMZN  1997.05M     8230468
4       AMZN  1997.05M     9807882
...
13133   NVDA  2016.12M   367356016
13134   NVDA  2016.12M   421740692
13135   NVDA  2016.12M   452063951
```

```Python
df= s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb").select("TICKER, month(date) as month, sum(VOL)").contextby("TICKER,month(date)").toDF()
print(df)

 TICKER     month    sum_VOL
0       AMZN  1997.05M   13736587
1       AMZN  1997.05M   13736587
2       AMZN  1997.05M   13736587
3       AMZN  1997.05M   13736587
4       AMZN  1997.05M   13736587
5       AMZN  1997.05M   13736587
...
13133   NVDA  2016.12M  452063951
13134   NVDA  2016.12M  452063951
13135   NVDA  2016.12M  452063951
```

```Python
df= s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade").contextby('ticker').having("sum(VOL)>40000000000").toDF()
print(df)

     TICKER        date       VOL       PRC       BID       ASK
0      NVDA  1999.01.22   5702636   19.6875   19.6250   19.6875
1      NVDA  1999.01.25   1074571   21.7500   21.7500   21.8750
2      NVDA  1999.01.26    719199   20.0625   20.0625   20.1250
3      NVDA  1999.01.27    510637   20.0000   19.8750   20.0000
4      NVDA  1999.01.28    476094   19.9375   19.8750   20.0000
5      NVDA  1999.01.29    509718   19.0000   19.0000   19.3125
...
4512   NVDA  2016.12.27  29857132  117.3200  117.3100  117.3200
4513   NVDA  2016.12.28  57384116  109.2500  109.2500  109.2900
4514   NVDA  2016.12.29  54384676  111.4300  111.2600  111.4200
4515   NVDA  2016.12.30  30323259  106.7400  106.7300  106.7500
```

#### 9.6 表连接

`merge`用于内部连接、左连接和外部连接，`merge_asof`表示asof join，`merge_window`表示窗口连接。

#### 9.6.1 `merge`

如果连接列名称相同，使用on参数指定连接列，如果连接列名称不同，使用left_on和right_on参数指定连接列。可选参数how表示表连接的类型。默认的连接类型时内部连接。

```Python
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")
t1 = s.table(data={'TICKER': ['AMZN', 'AMZN', 'AMZN'], 'date': np.array(['2015-12-31', '2015-12-30', '2015-12-29'], dtype='datetime64[D]'), 'open': [695, 685, 674]})
print(trade.merge(t1,on=["TICKER","date"]).toDF())

# output
  TICKER        date      VOL        PRC        BID        ASK  open
0   AMZN  2015.12.29  5734996  693.96997  693.96997  694.20001   674
1   AMZN  2015.12.30  3519303  689.07001  689.07001  689.09998   685
2   AMZN  2015.12.31  3749860  675.89001  675.85999  675.94000   695
```

当连接列名称不相同时，需要指定left_on参数和right_on参数。

```Python
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")
t1 = s.table(data={'TICKER1': ['AMZN', 'AMZN', 'AMZN'], 'date1': ['2015.12.31', '2015.12.30', '2015.12.29'], 'open': [695, 685, 674]})
print(trade.merge(t1,left_on=["TICKER","date"], right_on=["TICKER1","date1"]).toDF())

# output
  TICKER        date      VOL        PRC        BID        ASK  open
0   AMZN  2015.12.29  5734996  693.96997  693.96997  694.20001   674
1   AMZN  2015.12.30  3519303  689.07001  689.07001  689.09998   685
2   AMZN  2015.12.31  3749860  675.89001  675.85999  675.94000   695
```

左连接时，把how参数设置为“left”。

```Python
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")
t1 = s.table(data={'TICKER': ['AMZN', 'AMZN', 'AMZN'], 'date': ['2015.12.31', '2015.12.30', '2015.12.29'], 'open': [695, 685, 674]})
print(trade.merge(t1,how="left", on=["TICKER","date"]).where('TICKER=`AMZN').where('2015.12.23<=date<=2015.12.31').toDF())

# output
  TICKER       date      VOL        PRC        BID        ASK   open
0   AMZN 2015-12-23  2722922  663.70001  663.48999  663.71002    NaN
1   AMZN 2015-12-24  1092980  662.78998  662.56000  662.79999    NaN
2   AMZN 2015-12-28  3783555  675.20001  675.00000  675.21002    NaN
3   AMZN 2015-12-29  5734996  693.96997  693.96997  694.20001  674.0
4   AMZN 2015-12-30  3519303  689.07001  689.07001  689.09998  685.0
5   AMZN 2015-12-31  3749860  675.89001  675.85999  675.94000  695.0
```

外部连接时，把how参数设置为“outer”。分区表只能与分区表进行外部链接，内存表只能与内存表进行外部链接。

```Python
t1 = s.table(data={'TICKER': ['AMZN', 'AMZN', 'NFLX'], 'date': ['2015.12.29', '2015.12.30', '2015.12.31'], 'open': [674, 685, 942]})
t2 = s.table(data={'TICKER': ['AMZN', 'NFLX', 'NFLX'], 'date': ['2015.12.29', '2015.12.30', '2015.12.31'], 'close': [690, 936, 951]})
print(t1.merge(t2, how="outer", on=["TICKER","date"]).toDF())

# output
  TICKER        date   open TMP_TBL_ec03c3d2_TICKER TMP_TBL_ec03c3d2_date  \
0   AMZN  2015.12.29  674.0                    AMZN            2015.12.29   
1   AMZN  2015.12.30  685.0                                                 
2   NFLX  2015.12.31  942.0                    NFLX            2015.12.31   
3                       NaN                    NFLX            2015.12.30   

   close  
0  690.0  
1    NaN  
2  951.0  
3  936.0  
```

#### 9.6.2 `merge_asof`

`merge_asof`对应DolphinDB中的asof join（aj）。asof join用于非同步连接，它与left join非常相似，主要有以下区别：

1.asof join的最后一个连接列通常是时序类型。对于左表中某行的时间t，如果右表没有与t对应的时间，asof join会取右表中t之前的最近时间对应的记录。如果有多个相同的时间，它会取最后一个时间对应的记录。

2.如果只有一个连接列，右表必须按照连接列排好序。如果有多个连接列，右表必须在其他连接列的每个组内根据最后一个连接列排好序，右表不需要按照其他连接列排序，左表不需要排序。如果右表不满足这些条件，计算结果将会不符合预期。

本节与下节的例子使用了[trades.csv](data/trades.csv)和[quotes.csv](data/quotes.csv)，它们含有NYSE网站下载的AAPL和FB的2016年10月24日的交易与报价数据。

```Python
import dolphindb.settings as keys

WORK_DIR = "C:/DolphinDB/Data"
if s.existsDatabase(WORK_DIR+"/tickDB"):
    s.dropDatabase(WORK_DIR+"/tickDB")
s.database('db', partitionType=keys.VALUE, partitions=["AAPL","FB"], dbPath=WORK_DIR+"/tickDB")
trades = s.loadTextEx("db",  tableName='trades',partitionColumns=["Symbol"], filePath=WORK_DIR + "/trades.csv")
quotes = s.loadTextEx("db",  tableName='quotes',partitionColumns=["Symbol"], filePath=WORK_DIR + "/quotes.csv")

print(trades.top(5).toDF())

# output
                        Time  Exchange  Symbol  Trade_Volume  Trade_Price
0 1970-01-01 08:00:00.022239        75    AAPL           300        27.00
1 1970-01-01 08:00:00.022287        75    AAPL           500        27.25
2 1970-01-01 08:00:00.022317        75    AAPL           335        27.26
3 1970-01-01 08:00:00.022341        75    AAPL           100        27.27
4 1970-01-01 08:00:00.022368        75    AAPL            31        27.40

print(quotes.where("second(Time)>=09:29:59").top(5).toDF())

# output
                         Time  Exchange  Symbol  Bid_Price  Bid_Size  Offer_Price  Offer_Size
0  1970-01-01 09:30:00.005868        90    AAPL      26.89         1        27.10           6
1  1970-01-01 09:30:00.011058        90    AAPL      26.89        11        27.10           6
2  1970-01-01 09:30:00.031523        90    AAPL      26.89        13        27.10           6
3  1970-01-01 09:30:00.284623        80    AAPL      26.89         8        26.98           8
4  1970-01-01 09:30:00.454066        80    AAPL      26.89         8        26.98           1

print(trades.merge_asof(quotes,on=["Symbol","Time"]).select(["Symbol","Time","Trade_Volume","Trade_Price","Bid_Price", "Bid_Size","Offer_Price", "Offer_Size"]).top(5).toDF())

# output
  Symbol                        Time          Trade_Volume  Trade_Price  Bid_Price  Bid_Size  \
0   AAPL  1970-01-01 08:00:00.022239                   300        27.00       26.9         1   
1   AAPL  1970-01-01 08:00:00.022287                   500        27.25       26.9         1   
2   AAPL  1970-01-01 08:00:00.022317                   335        27.26       26.9         1   
3   AAPL  1970-01-01 08:00:00.022341                   100        27.27       26.9         1   
4   AAPL  1970-01-01 08:00:00.022368                    31        27.40       26.9         1   

   Offer_Price  Offer_Size  
0       27.49           10  
1       27.49           10  
2       27.49           10  
3       27.49           10  
4       27.49           10  
[5 rows x 8 columns]
```

使用asof join计算交易成本：

```Python
print(trades.merge_asof(quotes, on=["Symbol","Time"]).select("sum(Trade_Volume*abs(Trade_Price-(Bid_Price+Offer_Price)/2))/sum(Trade_Volume*Trade_Price)*10000 as cost").groupby("Symbol").toDF())

# output
  Symbol       cost
0   AAPL   6.486813
1     FB  35.751041
```

#### 9.6.3 `merge_window`

`merge_window`对应DolphinDB中的window join，它是asof join的扩展。leftBound参数和rightBound参数用于指定窗口的边界w1和w2，对左表中最后一个连接列对应的时间为t的记录，在右表中选择(t+w1)到(t+w2)的时间并且其他连接列匹配的记录，然后对这些记录使用聚合函数。

window join和prevailing window join的唯一区别是，如果右表中没有与窗口左边界时间（即t+w1）匹配的值，prevailing window join会选择(t+w1)之前的最近时间。如果要使用prevailing window join，需将prevailing参数设置为True。

```Python
print(trades.merge_window(quotes, -5000000000, 0, aggFunctions=["avg(Bid_Price)","avg(Offer_Price)"], on=["Symbol","Time"]).where("Time>=07:59:59").top(10).toDF())

# output
                        Time  Exchange Symbol  Trade_Volume \
0 1970-01-01 08:00:00.022239        75   AAPL           300
1 1970-01-01 08:00:00.022287        75   AAPL           500
2 1970-01-01 08:00:00.022317        75   AAPL           335
3 1970-01-01 08:00:00.022341        75   AAPL           100
4 1970-01-01 08:00:00.022368        75   AAPL            31
5 1970-01-01 08:00:02.668076        68   AAPL          2434
6 1970-01-01 08:02:20.116025        68   AAPL            66
7 1970-01-01 08:06:31.149930        75   AAPL           100
8 1970-01-01 08:06:32.826399        75   AAPL           100
9 1970-01-01 08:06:33.168833        75   AAPL            74

   avg_Bid_Price  avg_Offer_Price
0          26.90            27.49
1          26.90            27.49
2          26.90            27.49
3          26.90            27.49
4          26.90            27.49
5          26.75            27.36
6            NaN              NaN
7            NaN              NaN
8            NaN              NaN
9            NaN              NaN

[10 rows x 6 columns]
```

使用window join计算交易成本：

```Python
trades.merge_window(quotes,-1000000000, 0, aggFunctions="[wavg(Offer_Price, Offer_Size) as Offer_Price, wavg(Bid_Price, Bid_Size) as Bid_Price]", on=["Symbol","Time"], prevailing=True).select("sum(Trade_Volume*abs(Trade_Price-(Bid_Price+Offer_Price)/2))/sum(Trade_Volume*Trade_Price)*10000 as cost").groupby("Symbol").executeAs("tradingCost")

print(s.loadTable(tableName="tradingCost").toDF())

# output
  Symbol       cost
0   AAPL   6.367864
1     FB  35.751041
```

#### 9.7 `executeAs`

`executeAs`可以把结果保存为DolphinDB中的表对象。

```Python
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")
trade.select(['date','bid','ask','prc','vol']).where('TICKER=`AMZN').where('bid!=NULL').where('ask!=NULL').where('vol>10000000').sort('vol desc').executeAs("AMZN")
```

使用生成的表：

```Python
t1=s.loadTable(tableName="AMZN")
```

#### 9.8 回归运算

`ols`用于计算最小二乘回归系数。返回的结果是一个字典。

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR + "/valuedb", memoryMode=True)
z=trade.select(['bid','ask','prc']).ols('PRC', ['BID', 'ASK'])

print(z["ANOVA"])

# output
    Breakdown     DF            SS            MS             F  Significance
0  Regression      2  2.689281e+08  1.344640e+08  1.214740e+10           0.0
1    Residual  13133  1.453740e+02  1.106937e-02           NaN           NaN
2       Total  13135  2.689282e+08           NaN           NaN           NaN

print(z["RegressionStat"])

# output
         item    statistics
0            R2      0.999999
1    AdjustedR2      0.999999
2      StdError      0.105211
3  Observations  13136.000000


print(z["Coefficient"])

# output
      factor      beta  stdError      tstat    pvalue
0  intercept  0.003710  0.001155   3.213150  0.001316
1        BID  0.605307  0.010517  57.552527  0.000000
2        ASK  0.394712  0.010515  37.537919  0.000000

print(z["Coefficient"].beta[1])

# output
0.6053065014691369
```

下面的例子在分区数据库中执行回归运算。请注意，在DolphinDB中，两个整数整除的运算符为“/”，恰好是Python的转移字符，因此在`select`中使用VOL\SHROUT。

```Python
result = s.loadTable(tableName="US",dbPath="dfs://US").select("select VOL\\SHROUT as turnover, abs(RET) as absRet, (ASK-BID)/(BID+ASK)*2 as spread, log(SHROUT*(BID+ASK)/2) as logMV").where("VOL>0").ols("turnover", ["absRet","logMV", "spread"], True)
print(result["ANOVA"])

   Breakdown        DF            SS            MS            F  Significance
0  Regression         3  2.814908e+09  9.383025e+08  30884.26453           0.0
1    Residual  46701483  1.418849e+12  3.038125e+04          NaN           NaN
2       Total  46701486  1.421674e+12           NaN          NaN           NaN
```

### 10 更多实例

#### 10.1 动量交易策略

下面的例子是使用动量交易策略进行回测。最常用的动量因素是过去一年扣除最近一个月的收益率。动量策略通常是一个月调整一次并且持有期也是一个月。本文的例子中，每天调整1/5的投资组合，并持有新的投资组合5天。为了简单起见，不考虑交易成本。

**Create server session**

```Python
import dolphindb as ddb
s=ddb.session()
s.connect("localhost",8921, "admin", "123456")
```

步骤1：加载股票交易数据，对数据进行清洗和过滤，然后为每只股票构建过去一年扣除最近一个月收益率的动量信号。注意，必须使用`executeAs`把中间结果保存到DolphinDB服务器上。数据集“US”包含了美国股票1990到2016年的交易数据。

```Python
US = s.loadTable(dbPath="dfs://US", tableName="US")
def loadPriceData(inData):
    s.loadTable(inData).select("PERMNO, date, abs(PRC) as PRC, VOL, RET, SHROUT*abs(PRC) as MV").where("weekday(date) between 1:5, isValid(PRC), isValid(VOL)").sort(bys=["PERMNO","date"]).executeAs("USstocks")
    s.loadTable("USstocks").select("PERMNO, date, PRC, VOL, RET, MV, cumprod(1+RET) as cumretIndex").contextby("PERMNO").executeAs("USstocks")
    return s.loadTable("USstocks").select("PERMNO, date, PRC, VOL, RET, MV, move(cumretIndex,21)/move(cumretIndex,252)-1 as signal").contextby("PERMNO").executeAs("priceData")

priceData = loadPriceData(US.tableName())
# US.tableName() returns the name of the table on the DolphinDB server that corresponds to the table object "US" in Python. 
```

步骤2：为动量策略生成投资组合

```Python
def genTradeTables(inData):
    return s.loadTable(inData).select(["date", "PERMNO", "MV", "signal"]).where("PRC>5, MV>100000, VOL>0, isValid(signal)").sort(bys=["date"]).executeAs("tradables")


def formPortfolio(startDate, endDate, tradables, holdingDays, groups, WtScheme):
    holdingDays = str(holdingDays)
    groups=str(groups)
    ports = tradables.select("date, PERMNO, MV, rank(signal,,"+groups+") as rank, count(PERMNO) as symCount, 0.0 as wt").where("date between "+startDate+":"+endDate).contextby("date").having("count(PERMNO)>=100").executeAs("ports")
    if WtScheme == 1:
        ports.where("rank=0").contextby("date").update(cols=["wt"], vals=["-1.0/count(PERMNO)/"+holdingDays]).execute()
        ports.where("rank="+groups+"-1").contextby("date").update(cols=["wt"], vals=["1.0/count(PERMNO)/"+holdingDays]).execute()
    elif WtScheme == 2:
        ports.where("rank=0").contextby("date").update(cols=["wt"], vals=["-MV/sum(MV)/"+holdingDays]).execute()
        ports.where("rank="+groups+"-1").contextby("date").update(cols=["wt"], vals=["MV/sum(MV)/"+holdingDays]).execute()
    else:
        raise Exception("Invalid WtScheme. valid values:1 or 2")
    return ports.select("PERMNO, date as tranche, wt").where("wt!=0").sort(bys=["PERMNO","date"]).executeAs("ports")

tradables=genTradeTables(priceData.tableName())
startDate="1996.01.01"
endDate="2017.01.01"
holdingDays=5
groups=10
ports=formPortfolio(startDate=startDate,endDate=endDate,tradables=tradables,holdingDays=holdingDays,groups=groups,WtScheme=2)
dailyRtn=priceData.select("date, PERMNO, RET as dailyRet").where("date between "+startDate+":"+endDate).executeAs("dailyRtn")
```

步骤3：计算投资组合中每只股票接下来5天的利润或损失。在投资组合形成后的5天后关停投资组合。

```Python
def calcStockPnL(ports, dailyRtn, holdingDays, endDate):
    s.table(data={'age': list(range(1,holdingDays+1))}).executeAs("ages")
    ports.select("tranche").sort("tranche").executeAs("dates")
    s.run("dates = sort distinct dates.tranche")
    s.run("dictDateIndex=dict(dates,1..dates.size())")
    s.run("dictIndexDate=dict(1..dates.size(), dates)")
    ports.merge_cross(s.table(data="ages")).select("dictIndexDate[dictDateIndex[tranche]+age] as date, PERMNO, tranche, age, take(0.0,age.size()) as ret, wt as expr, take(0.0,age.size()) as pnl").where("isValid(dictIndexDate[dictDateIndex[tranche]+age]), dictIndexDate[dictDateIndex[tranche]+age]<=min(lastDays[PERMNO], "+endDate+")").executeAs("pos")
    t1= s.loadTable("pos")
    t1.merge(dailyRtn, on=["date","PERMNO"], merge_for_update=True).update(["ret"],["dailyRet"]).execute()
    t1.contextby(["PERMNO","tranche"]).update(["expr"], ["expr*cumprod(1+ret)"]).execute()
    t1.update(["pnl"],["expr*ret/(1+ret)"]).execute()
    return t1

lastDaysTable = priceData.select("max(date) as date").groupby("PERMNO").executeAs("lastDaysTable")
s.run("lastDays=dict(lastDaysTable.PERMNO,lastDaysTable.date)")
# undefine priceData to release memory
s.undef(priceData.tableName(), 'VAR')
stockPnL = calcStockPnL(ports=ports, dailyRtn=dailyRtn, holdingDays=holdingDays, endDate=endDate)
```

步骤4：计算投资组合的利润或损失。

```Python
portPnl = stockPnL.select("pnl").groupby("date").sum().sort(bys=["date"]).executeAs("portPnl")

print(portPnl.toDF())
```

#### 10.2 时间序列操作

下面的例子计算"101 Formulaic Alphas" by Kakushadze (2015)中的98号因子。

```Python
def alpha98(t):
    t1 = s.table(data=t)
    # add two calcualted columns through function update
    t1.contextby(["date"]).update(cols=["rank_open","rank_adv15"], vals=["rank(open)","rank(adv15)"]).execute()
    # add two more calculated columns
    t1.contextby(["PERMNO"]).update(["decay7", "decay8"], ["mavg(mcorr(vwap, msum(adv5, 26), 5), 1..7)","mavg(mrank(9 - mimin(mcorr(rank_open, rank_adv15, 21), 9), true, 7), 1..8)"]).execute()
    # return the final results with three columns: PERMNO, date, and A98
    return t1.select("PERMNO, date, rank(decay7)-rank(decay8) as A98").contextby(["date"]).executeAs("alpha98")

US = s.loadTable(tableName="US", dbPath="dfs://US").select("PERMNO, date, PRC as vwap, PRC+rand(1.0, PRC.size()) as open, mavg(VOL, 5) as adv5, mavg(VOL,15) as adv15").where("2007.01.01<=date<=2016.12.31").contextby("PERMNO").executeAs("US")
result=alpha98(US.tableName()).where('date>2007.03.12').executeAs("result")
print(result.top(10).toDF())
``` 

Python Streaming API
---

## 1 流数据订阅方法说明

Python API支持流数据订阅的功能，下面简单介绍一下流数据订阅的相关方法与使用示例。

### 1.1 指定客户端的订阅端口号

使用Python API提供的`enableStreaming`函数启用流数据功能：
```Python
s.enableStreaming(port)
```

- port是指定传入数据的订阅端口，每个session具备唯一的端口。

示例：

在Python客户端中，导入 DolphinDB Python API，并启用流数据功能，指定订阅端口为8000：
```Python
import dolphindb as ddb
import numpy as np
s = ddb.session()
s.enableStreaming(8000)
```

### 1.2 调用订阅函数

使用`subscribe`函数来订阅DolphinDB中的流数据表，语法如下：

```Python
s.subscribe(host, port, handler, tableName, actionName="", offset=-1, resub=False, filter=None)
```

- host是发布端节点的IP地址。
- port是发布端节点的端口号。
- handler是用户自定义的回调函数，用于处理每次流入的数据。
- tableName是发布表的名称。
- actionName是订阅任务的名称。
- offset是整数，表示订阅任务开始后的第一条消息所在的位置。消息是流数据表中的行。如果没有指定offset，或它为负数或超过了流数据表的记录行数，订阅将会从流数据表的当前行开始。offset与流数据表创建时的第一行对应。如果某些行因为内存限制被删除，在决定订阅开始的位置时，这些行仍然考虑在内。
- resub是布尔值，表示订阅中断后，是否会自动重订阅。
- filter是一个向量，表示过滤条件。流数据表过滤列在filter中的数据才会发布到订阅端，不在filter中的数据不会发布。

示例：

请注意，发布节点需要配置maxPubConnections参数，具体请参照[DolphinDB流数据教程](https://github.com/dolphindb/Tutorials_CN/blob/master/streaming_tutorial.md)。

在DolphinDB中创建共享的流数据表，指定进行过滤的列，并插入一些随机数据：
```
share streamTable(10000:0,`time`sym`price`id, [TIMESTAMP,SYMBOL,DOUBLE,INT]) as trades
setStreamTableFilterColumn(trades, `sym)
insert into trades values(take(now(), 10), rand(`ab`cd`ef`gh`ij, 10), rand(1000,10)/10.0, 1..10)
```

在Python中订阅trades表：
```Python
def handler(lst):         
    print(lst)

s.subscribe("192.168.1.103",8921,handler,"trades","action",0,False,np.array(['ab']))

# output
[numpy.datetime64('2019-10-16T11:49:57.769'), 'cd', 29.3, 1]
[numpy.datetime64('2019-10-16T11:49:59.481'), 'ab', 61.8, 6]
[numpy.datetime64('2019-10-16T11:49:59.481'), 'ab', 76.7, 7]
[numpy.datetime64('2019-10-16T11:50:00.233'), 'gh', 27.2, 1]
[numpy.datetime64('2019-10-16T11:50:01.521'), 'ab', 21.2, 1]
[numpy.datetime64('2019-10-16T11:50:01.521'), 'ab', 37.6, 10]
[numpy.datetime64('2019-10-16T11:50:02.217'), 'ab', 20.4, 1]
[numpy.datetime64('2019-10-16T11:50:02.217'), 'ab', 26.7, 3]
```

### 1.3 获取订阅主题

通过`getSubscriptionTopics`函数可以获取所有订阅主题，主题的构成方式是：host/port/tableName/actionName，每个session的所有主题互不相同。

```Python
s.getSubscriptionTopics()
# output
['192.168.1.103/8921/trades/action']
```

### 1.4 取消订阅

使用`unsubscribe`取消订阅，语法如下：
```Python
s.unsubscribe(host,port,tableName,actionName="")
```

例如，取消示例中的订阅：
```Python
s.unsubscribe("192.168.1.103", 8921,"trades","action")
```

**请注意:**，因为订阅是异步执行的，所以订阅完成后需要保持主线程不退出，比如：

```Python
from threading import Event     # 加在第一行
Event().wait()                  # 加在最后一行
```
否则订阅线程会在主线程退出前立刻终止，导致无法收到订阅消息。

## 2 流数据订阅实例

下面的例子中，我们在Python客户端订阅第三方数据到多个DataFrame中，通过DolphinDB的流数据订阅功能将多个表中的数据写入到分布式表中。

首先，我们创建数据库和表：

```Python
import dolphindb as ddb
import pandas as pd
import numpy as np

s = ddb.session()
s.connect(host, port, "admin", "123456")

dbDir = "dfs://ticks"
tableName = 'tick'

script = """
login('admin','123456')

// 定义表结构
n=20000000
colNames =`Code`Date`DiffAskVol`DiffAskVolSum`DiffBidVol`DiffBidVolSum`FirstDerivedAskPrice`FirstDerivedAskVolume`FirstDerivedBidPrice`FirstDerivedBidVolume
colTypes = [SYMBOL,DATE,INT,INT,INT,INT,FLOAT,INT,FLOAT,INT]

// 创建数据库与分布式表
dbPath= '{dbPath}'
if(existsDatabase(dbPath))
   dropDatabase(dbPath)
db=database(dbPath,VALUE, 2000.01.01..2030.12.31)
dfsTB=db.createPartitionedTable(table(n:0, colNames, colTypes),`{tbName},`Date)
""".format(dbPath=dbDir,tbName=tableName)
```

下面，我们将定义两个流数据表`mem_stream_d`和`mem_stream_f`，客户端往流数据表写入数据，由服务端订阅数据。

```Python
script += """
// 定义mem_tb_d表,并开启流数据持久化，将共享表命名为mem_stream_d
mem_tb_d=streamTable(n:0, colNames, colTypes)
enableTableShareAndPersistence(mem_tb_d,'mem_stream_d',false,true,n)

// 定义mem_tb_f表,并开启流数据持久化，将共享表命名为mem_stream_f
mem_tb_f=streamTable(n:0,colNames, colTypes)
enableTableShareAndPersistence(mem_tb_f,'mem_stream_f',false,true,n)
"""
```

**请注意**，由于表的分区字段是按照日期进行分区，而客户端往`mem_stream_d`和`mem_stream_f`表中写的数据会有日期上的重叠， 若直接由分布式表`tick`同时订阅这两个表的数据，就会造成这两个表同时往同一个日期分区写数据，最终会写入失败。因此，我们需要定义另一个流表`ticks_stream`来订阅`mem_stream_d`和`mem_stream_f`表的数据，再让分布式表`tick`单独订阅这一个流表，这样就形成了一个二级订阅模式。

```Python
script += """
// 定义ftb表,并开启流数据持久化，将共享表命名为ticks_stream
ftb=streamTable(n:0, colNames, colTypes)
enableTableShareAndPersistence(ftb,'ticks_stream',false,true,n)
go

// ticks_stream订阅mem_stream_d表的数据
def saveToTicksStreamd(mutable TB, msg): TB.append!(select Code,Date,DiffBidVol,DiffBidVolSum,FirstDerivedBidPrice,FirstDerivedBidVolume from msg)
subscribeTable(, 'mem_stream_d', 'action_to_ticksStream_tde', 0, saveToTicksStreamd{ticks_stream}, true, 100)

// ticks_stream同时订阅mem_stream_f表的数据
def saveToTicksStreamf(mutable TB, msg): TB.append!(select Code,Date,DiffAskVol,DiffAskVolSum,FirstDerivedAskPrice,FirstDerivedAskVolume from msg)
subscribeTable(, 'mem_stream_f', 'action_to_ticksStream_tfe', 0, saveToTicksStreamf{ticks_stream}, true, 100)

// dfsTB订阅ticks_stream表的数据
def saveToDFS(mutable TB, msg): TB.append!(select * from msg)
subscribeTable(, 'ticks_stream', 'action_to_dfsTB', 0, saveToDFS{dfsTB}, true, 100, 5)
"""
s.run(script)
```

上述几个步骤中，我们定义了一个数据库并创建分布式表`tick`，以及三个流数据表，分别为`mem_stream_d`、`mem_stream_f`和`ticks_stream`。客户端将第三方订阅而来的数据不断地追加到`mem_stream_d`和`mem_stream_f`表中，而写入这两个表的数据会自动由`ticks_stream`表订阅。最后，`ticks_stream`表内的数据会被顺序地写入分布式表`tick`中。

下面，我们将第三方订阅到的数据上传到DolphinDB，通过DolphinDB流数据订阅功能将数据追加到分布式表。我们假定Python客户端从第三方订阅到的数据已经保存在两个名为`dfd`和`dff`的DataFrame中：

```Python
n = 10000
dfd = pd.DataFrame({'Code': np.repeat(['a', 'b', 'c', 'd', 'e', 'QWW', 'FEA', 'FFW', 'DER', 'POD'], n/10),
                    'Date': np.repeat(pd.date_range('2000.01.01', periods=10000, freq='D'), n/10000),
                    'DiffAskVol': np.random.choice(100, n),
                    'DiffAskVolSum': np.random.choice(100, n),
                    'DiffBidVol': np.random.choice(100, n),
                    'DiffBidVolSum': np.random.choice(100, n),
                    'FirstDerivedAskPrice': np.random.choice(100, n)*0.9,
                    'FirstDerivedAskVolume': np.random.choice(100, n),
                    'FirstDerivedBidPrice': np.random.choice(100, n)*0.9,
                    'FirstDerivedBidVolume': np.random.choice(100, n)})

n = 20000
dff = pd.DataFrame({'Code': np.repeat(['a', 'b', 'c', 'd', 'e', 'QWW', 'FEA', 'FFW', 'DER', 'POD'], n/10),
                    'Date': np.repeat(pd.date_range('2000.01.01', periods=10000, freq='D'), n/10000),
                    'DiffAskVol': np.random.choice(100, n),
                    'DiffAskVolSum': np.random.choice(100, n),
                    'DiffBidVol': np.random.choice(100, n),
                    'DiffBidVolSum': np.random.choice(100, n),
                    'FirstDerivedAskPrice': np.random.choice(100, n)*0.9,
                    'FirstDerivedAskVolume': np.random.choice(100, n),
                    'FirstDerivedBidPrice': np.random.choice(100, n)*0.9,
                    'FirstDerivedBidVolume': np.random.choice(100, n)})
```

**请注意**，在向流数据表追加一个带有时间列的表时，我们需要对时间列进行时间类型转换：首先将整个DataFrame上传到DolphinDB服务器，再通过select语句将其中的列取出，并转换时间类型列的数据类型，最后通过`tableInsert`语句追加表。具体原因与向内存表追加一个DataFrame类似，请参见[第7.1.3小节](#713-使用tableinsert函数追加表)。

```Python
s.upload({'dfd': dfd, 'dff': dff})
inserts = """tableInsert(mem_stream_d,select Code,date(Date) as Date,DiffAskVol,DiffAskVolSum,DiffBidVol,DiffBidVolSum,FirstDerivedAskPrice,FirstDerivedAskVolume,FirstDerivedBidPrice,FirstDerivedBidVolume from dfd);
tableInsert(mem_stream_f,select Code,date(Date) as Date,DiffAskVol,DiffAskVolSum,DiffBidVol,DiffBidVolSum,FirstDerivedAskPrice,FirstDerivedAskVolume,FirstDerivedBidPrice,FirstDerivedBidVolume from dff)"""
s.run(inserts)
s.run("select count(*) from loadTable('{dbPath}', `{tbName})".format(dbPath=dbDir,tbName=tableName))

# output
   count
0  30000
```

我们可以执行以下脚本结束订阅：

```Python
clear="""
def clears(tbName,action)
{
	unsubscribeTable(, tbName, action)
	clearTablePersistence(objByName(tbName))
	undef(tbName,SHARED)
}
clears(`ticks_stream, `action_to_dfsTB)
clears(`mem_stream_d,`action_to_ticksStream_tde)
clears(`mem_stream_f,`action_to_ticksStream_tfe)
"""
s.run(clear)

```
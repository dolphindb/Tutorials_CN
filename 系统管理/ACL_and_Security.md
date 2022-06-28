# 权限管理和安全

DolphinDB database 提供了强大、灵活、安全的权限控制系统。控制节点（controller）作为权限管理中心，使用RSA加密方式对用户关键信息进行加密。

主要功能：
* 提供用户和组角色，方便权限控制
* 提供9种权限控制类别，适应各种场景
* 丰富的权限控制函数
* 函数视图兼顾保护数据隐私与提供分析结果
* 对任务调度和流数据任务动态鉴权，保证系统安全
* 使用RSA对用户关键信息加密
* 支持SSO，简化登录，方便系统扩展



- [1. 权限概述](#1-权限概述)
    - [1.1 用户和组](#11-用户和组)
    - [1.2 系统管理员](#12-系统管理员)
    - [1.3 权限类别](#13-权限类别)
    - [1.4 权限设置](#14-权限设置)
    - [1.5 权限确定规则](#15-权限确定规则)
    - [1.6 基于函数视图(function view)的权限控制](#16-%E5%9F%BA%E4%BA%8E%E5%87%BD%E6%95%B0%E8%A7%86%E5%9B%BEfunction-view%E7%9A%84%E6%9D%83%E9%99%90%E6%8E%A7%E5%88%B6)
- [2. 程序调度和流计算中的权限控制](#2-程序调度和流计算中的权限控制)
    - [2.1 schedule jobs 权限设置](#21-schedule-jobs-权限设置)
    - [2.1 streaming 权限设置](#22-streaming-权限设置)
- [3. 使用HTTPS实现安全通信](#3-使用https实现安全通信)
    - [3.1 使用HTTPS配置](#31-使用https配置)
    - [3.2 HTTPS证书设置](#32-https证书设置)
        - [3.2.1 第三方认证证书](#321-第三方认证证书)
        - [3.2.2 安装自制证书](#322-安装自制证书)
- [4. 支持SSO (Single Sign On)](#4-支持sso-single-sign-on)


## 1. 权限概述

### 1.1 用户和组

用户和组是承载权限的实体。一个用户可以属于多个组，一个组也可以包括多个用户。

引入组的概念，可以方便的对具有相同权限的用户进行权限配置和管理，用户最终的实际权限是用户本身的权限，加上所属组的权限的结果。

DolphinDB系统通过用户名和密码对用户进行身份校检，通过`login` 和`logout`来进行用户的登录和登出管理。

管理员和用户都需要通过登录用户名之后才可以进行相对应的操作。 用户可以通过使用`changePwd`来改变自己的登录密码。

### 1.2 系统管理员

DolphinDB集群第一次启动时，会自动创建用户名为"admin"，密码为"123456"的系统管理员。此管理员拥有所有的权限，例如创建或删除数据库，可读写所有表，在数据库中创建或删除数据表，可使用所有的函数视图，可执行或测试脚本。
其他管理员在刚创建时，是没有任何权限的，需要手动赋予他权限。

管理员可以赋予或禁止其他管理员，用户和组的权限，亦可撤销权限设置。请注意管理员"admin"无法被删除。

管理员可使用函数或命令  `addGroupMember`, `createGroup`, `createUser`, `deleteGroup` , `deleteGroupMember`, `deleteUser`, `getGroupsByUserId`,`getGroupList`, `getUserAccess`,  `getUsersByGroupId`, `getUserList`,
 `resetPwd`对用户和组进行方便的操作。具体用法请参考DolphinDB用户手册。

### 1.3 权限类别

DolphinDB提供以下9种权限类别:

1. TABLE_READ：读取表中数据
2. TABLE_WRITE: 向表中写入数据 
3. DBOBJ_CREATE: 在某个数据库中创建数据表
4. DBOBJ_DELETE: 删除某个数据库中的数据表 
5. VIEW_EXEC: 执行视图 
6. DB_MANAGE: 创建以及删除数据库。可删除任何人所建数据库，包括具有DB_OWNER权限之用户所建数据库。
7. DB_OWNER：创建数据库并管理其创建的数据库，包括删除数据库、创建或删除数据表、增加或删除分区、可赋予、禁止或取消其他用户对自己创建的数据库的以下权限：TABLE_READ, TABLE_WRITE, DBOBJ_CREATE, DBOBJ_DELETE。
8. SCRIPT_EXEC: 运行脚本文件 
9. TEST_EXEC: 执行测试脚本


请注意，权限配置中涉及到的数据库及数据表均为在分布式文件系统（DFS）中建立的。

### 1.4 权限设置

只有管理员才可设置权限，且只能在控制节点上执行权限类操作。刚创建的用户或组没有被赋予或被禁止任何权限。管理员可使用`grant`/`deny`/`revoke`命令来设置用户或者组的权限。在1.3中的9种权限，可作为这三个命令的accessType参数值。在设置访问权限1-5时，还需要指定权限应用的具体对象。

以下通过4个例子，说明权限设置的操作。

#### 例子1

管理员登录：
```
login(`admin, `123456)
```
创建用户 NickFoles：
```
createUser("NickFoles","AB123!@")  
```
赋予用户 NickFoles 可读任何DFS数据表的权限：
```
grant("NickFoles",TABLE_READ,"*") 
```
禁止用户 NickFoles 创建或删除数据库：
```
deny("NickFoles",DB_MANAGE)   
```
创建 SBMVP 组，并且把用户 NickFoles 加入到该组： 
```
createGroup("SBMVP", "NickFoles")  
```
赋予 SBMVP 组可在数据库"dfs://db1"和"dfs://db2"中创建数据表的权限：
```
grant("SBMVP",DBOBJ_CREATE,["dfs://db1","dfs://db2"])    
```

最后用户 NickFoles 的权限为：可以访问所有的数据表，不能创建或删除数据库，可以对"dfs://db1"和"dfs://db2"进行创建数据表的操作。  

#### 例子2

通过组可以方便的设置用户权限:
```
createUser("EliManning", "AB123!@")  
createUser("JoeFlacco","CD234@#")  
createUser("DeionSanders","EF345#$")  
createGroup("football", ["EliManning","JoeFlacco","DeionSanders"])  
grant("football", TABLE_READ, "dfs://TAQ/quotes")  
grant("DeionSanders", DB_MANAGE)  
```

该例子创建了3个用户和1个组，并且这三个用户属于该组。赋予此组可读数据表dfs://TAQ/quotes" 的权限，同时只赋予用户DeionSanders创建和删除数据库的权限。

#### 例子3

可以使用`grant`或`deny`对所有对象(以\*代表)赋予或禁止权限。例如，赋予用户 JoeFlacco 可读任何DFS数据表的权限：
```
grant("JoeFlacco",TABLE_READ,"*")  
```
当`grant`或`deny`所有对象后，只可以对所有对象使用`revoke`，若对某个单一对象使用`revoke`无效:  
```
revoke("JoeFlacco",TABLE_READ,"dfs://db1/t1")
```
以上命令无效。

```
revoke("JoeFlacco",TABLE_READ,"*")
```
以上命令取消了用户 JoeFlacco 可读任何DFS数据表的权限。

与之类似，使用`grant`或`deny`对组赋予或禁止权限后，只能对该组使用`revoke`来取消该权限设置。若对某个组员使用`revoke`来取消该权限设置则无效。

#### 例子4

有DB_OWNER权限的用户可以赋予别的用户对自己创建的数据库的权限。

管理员创建了两个用户，CliffLee 和 MitchTrubisky，其中用户MitchTrubisky拥有DB_OWNER的权限：

```
createUser(`CliffLee, "GH456$%")
createUser(`MitchTrubisky, "JI3564^")
grant(`MitchTrubisky,DB_OWNER);
```
MitchTrubisky创建数据表 "dfs://dbMT/dt", 并赋予用户 CliffLee读取该数据表的权限：

```
login(`MitchTrubisky, "JI3564^");
db = database("dfs://dbMT", VALUE, 1..10)
t=table(1..1000 as id, rand(100, 1000) as x)
dt = db.createTable(t, "dt").append!(t)
grant(`CliffLee, TABLE_READ, "dfs://dbMT/dt"); 
```
尽管用户CliffLee之前没有被系统管理员赋予任何权限，但是CliffLee最后的权限为：可以访问MitchTrubisky创建的数据表 "dfs://dbMT/dt"。

### 1.5 权限确定规则

用户的最终权限由用户本身的权限与其所属的所有组的权限共同决定。不同的组有可能对某用户某权限的规定有冲突。以下为权限确定规则：
* 若用户在至少一组中被赋予某权限，而且没有在任一组中被禁止该权限，则此用户拥有此权限。
* 若用户在至少一组中被禁止某权限，即使该用户在其它组中被赋予此权限，也被被禁止了此权限。此情况下该用户要获得此权限，管理员必须在所有禁止该权限的组中使用grant命令重新赋予该权限，或者使用revoke命令撤销之前的禁止权限，并且该用户至少在一组中被赋予此权限。
请注意，在上述规则中，为了叙述方便，用户本身也可视为一个特殊的组。

```  
createUser("user1","123456")  
createUser("user2","123456")  
createGroup("group1")  
createGroup("group2")  
addGroupMember(["user1","user2"],"group1")
addGroupMember(["user1","user2"],"group2")
grant("user1",TABLE_READ,"*")  
deny("group1",TABLE_READ,"dfs://db1/t1")  
deny("group2",TABLE_READ,"dfs://db1/t2")   
```  
以上三行的结果为，用户user1可以读取除"dfs://db1/t1" 和"dfs://db1/t2" 以外的所有数据表。  

``` 
grant("user2",TABLE_WRITE,"*")  
deny("group1",TABLE_WRITE,"*")  
grant("group2",TABLE_WRITE,"dfs://db1/t2")  
```
以上三行的结果为，用户user1和user2不能写数据到任何数据表。


### 1.6 基于函数视图(function view)的权限控制

函数视图提供了一种灵活的方式来控制用户访问数据表，在不给予用户可以阅读数据表所有原始数据的权限的情况下，让用户可以获取由函数视图产生的信息。只有系统管理员有创建和删除函数视图的权限。

管理员定义一个函数视图：  
```
def countTradeAll(){  
	return exec count(*) from loadTable("dfs://TAQ","Trades")  
}
addFunctionView(countTradeAll)  
grant("NickFoles",VIEW_EXEC,"countTradeAll")  
```
以用户名NickFoles登录，执行视图countTradeAll
```
countTradeAll()
```
虽然用户NickFoles没有访问表"dfs://TAQ/Trades" 的权限，但是可以运行函数视图在此例中来获取表的行数。

函数视图也可以带参数。用户在使用的时候可以输入参数获取相应的结果。下面的例子，我们创建一个函数视图，获取某一个股票在某一天的所有交易记录。
```
def getTrades(s, d){
	return select * from loadTable("dfs://TAQ","Trades") where sym=s, date=d
}
addFunctionView(getTrades)
grant("NickFoles",VIEW_EXEC,"getTrades")  
```
以用户名NickFoles登录，并在执行视图getTrades指定股票代码和日期：
```
getTrades("IBM", 2018.07.09)
```

## 2. 程序调度和流计算中的权限控制

程序调度和流计算在后台运行，很多情况下，没有显式登录，因此权限验证跟用户显式登录的情况有些不同。这两类后台任务都是以创建该任务的用户身份来运行。

### 2.1 schedule jobs 权限设置

程序调度是指用户指定在特定的时间，以特定的频率执行一系列任务，多用于适合批处理类业务场景。 
```
login("NickFoles","AB123!@")  
def readTable(){  
	read_t1=loadTable("dfs://db1","t1")  
	return exec count(*) from read_t1  
}  
scheduleJob("readTableJob","read DFS table",readTable,minute(now()),date(now()),date(now())+1,'D');  
```

不管NickFoles有没有读"dfs://db1/t1" 的权限，`readTable`任务都能设置成功。  

在readTable任务实际运行时，如果用户NickFoles有读"dfs://db1/t1" 的权限，则成功执行，否则鉴权失败。  

另外，使用`deleteScheduledJob`命令的的时候，系统管理员可以删除其他用户制定的任务，非管理员用户只能删除自己创建的任务。

### 2.2 streaming 权限设置

当用户使用`subscribeTable`函数从一个流数据表中订阅实时数据存入数据表时，应当确认其有写入此数据表的权限。

```
login("NickFoles","AB123!@")
def saveTradesToDFS(mutable dfsTrades, msg): dfsTrades.append!(select today() as date, * from msg)  
subscribeTable("NODE1", "trades_stream", "trades", 0, saveTradesToDFS{trades}, true, 1000, 1)  
```

在上例中，流数据处理任务把接收到的数据保存到数据表dfsTrades中。在此流数据处理任务执行的时候，系统会动态地鉴定NickFoles是否有写入数据表dfsTrades的权限，如果没有则鉴权失败。

## 3. 使用HTTPS实现安全通信

DolphinDB支持使用HTTPS安全协议与web进行通信。

### 3.1 使用HTTPS配置

两种配置HTTPS的方法：

- 在控制节点的配置文件中添加`enableHTTPS=true`

- 在启动控制节点的命令行添加 `-enableHTTPS true`

### 3.2 HTTPS证书设置

DolphinDB使用服务端证书验证的安全策略。默认情况下，会生成自制证书，客户需要安装服务端的证书，否则浏览器提示不安全连接。每台物理server需要一份证书，因此控制节点和代理节点需要生成证书，数据节点使用同一个物理服务器上代理节点生成的证书。用户也可购买经过第三方认证的证书。

#### 3.2.1 第三方认证证书

将第三方证书重命名为 server.crt，并且拷贝到控制节点和代理节点的home目录下的keys文件夹中，若keys文件夹不存在，则需手动创建。由于第三方证书经过公认的权威授权机构颁布，所以浏览器默认信任该证书，不需要再手动安装。绝大部分应用场景适合使用此方式。

#### 3.2.2 安装自制证书

在小型封闭集群内部通信时，用户也可以使用自制证书进行OPENSSL安全通信，不过安装自制证书稍微繁琐，具体过程如下:

> 1. 设置 publicName
由于证书的生成需要知道计算机的域名，对需要生成证书的物理server设置该选项为计算机的域名，可以在命令行或配置文件中设置。下面是在Linux中启动控制节点的命令行例子。这里www.ABCD.com 是控制节点所在计算机的域名。  
```
./dolphindb -enableHTTPS true -home master -publicName www.ABCD.com -mode controller -localSite 192.168.1.30:8500:rh8500 -logFile  ./log/master.log
```
> 2. 查看证书是否正确生成  
启动控制节点， 在home目录下的keys文件夹中，查看是否有自制证书文件*server.crt*和私钥文件*serverPrivate.key*。

> 3. 安装自制证书到浏览器的授信证书中心
不同的浏览器安装选项稍有不同，以Google Chrome为例，选择Settings->Advanced->Manage certificates->AUTHORITIES->Import,导入上面生成的server.crt文件。

![](../images/Selection_047.png)  

在浏览器中输入 https://www.ABCD.com:8500/ 以访问集群管理器。若浏览器地址栏显示绿色的小锁，说明证书安装成功，可以进行HTTPS访问。

![](../images/Selection_046.png)

## 4. 支持SSO (Single Sign On)

在集群管理界面中，可以点击任意数据节点，链接到该节点的notebook上。从控制节点跳转到数据节点，有可能是访问了不同的物理服务器（跨域访问）。DolphinDB提供了SSO使得用户无须在集群操作中访问不同的物理服务器时重新登陆系统。

DolphinDB提供两个用于SSO的API函数：
+ `getAuthenticatedUserTicket()` 获取当前登录用户的加密ticket
+ `authenticateByTicket(ticket)` 使用上面获取的ticket登录系统

DolphinDB的开发者可以方便安全的使用这些接口来对系统进行扩展。

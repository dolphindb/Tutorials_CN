# DECIMAL 使用教程

数字运算在数据库中是很常见的需求，例如计算数量、重量、价格等，为了满足各种需求，数据库系统通常支持精准的数据类型和近似的数据类型。在金融领域中，对数据的计算精度要求极高，为保证数据的一致性以及计算结果的精准性，DolphinDB 数据库在 v2.00.8 版本中专门引入两个新的数据类型 DECIMAL32、DECIMAL64。

本文将简要介绍 DECIMAL 类型在 DolphinDB 数据库中的使用方法、计算规则，以及对比现有浮点数类型 (DOUBLE/FLOAT)  所具备的差异性。
- [DECIMAL 使用教程](#decimal-使用教程)
- [1. DECIMAL 在 DolphinDB 中的用法](#1-decimal-在-dolphindb-中的用法)
	- [1.1 语法特征](#11-语法特征)
	- [1.2 数据结构及定义](#12-数据结构及定义)
		- [1.2.1 标量](#121-标量)
		- [1.2.2 向量](#122-向量)
		- [1.2.3 表](#123-表)
- [2. 数值范围](#2-数值范围)
	- [2.1 创建数据时的溢出检查](#21-创建数据时的溢出检查)
	- [2.2 算术计算的溢出检查](#22-算术计算的溢出检查)
	- [2.3 比较运算中的溢出检查](#23-比较运算中的溢出检查)
- [3. 算术运算规则](#3-算术运算规则)
	- [3.1 DECIMAL 类型之间的算数规则及 scale 的规则](#31-decimal-类型之间的算数规则及-scale-的规则)
	- [3.2 DECIMAL 类型与整型进行计算](#32-decimal-类型与整型进行计算)
	- [3.3 DECIMAL 类型与浮点数进行计算](#33-decimal-类型与浮点数进行计算)
- [4. 导入数据成 DECIMAL 类型](#4-导入数据成-decimal-类型)
- [5. 对比 DECIMAL32/DECIMAL64 和 DOUBLE/FLOAT](#5-对比-decimal32decimal64-和-doublefloat)
	- [5.1 指定小数位数](#51-指定小数位数)
	- [5.2 精度差异](#52-精度差异)
	- [5.3 局限性](#53-局限性)

# 1. DECIMAL 在 DolphinDB 中的用法

## 1.1 语法特征

与目前 DolphinDB 中现有的浮点数数据类型 FLOAT 和 DOUBLE 不同，DECIMAL 在创建时需要指定一个输入数据和一个描述精度范围的数据，分别是 X 和 scale：即 `decimal32(X, scale)` 或者`decimal64(X, scale)`。其中：

- X 是整型/浮点型/字符串类型的标量或者向量；
- scale 是一个整型标量，指 DECIMAL 所保留的小数位数，

​        例如，decimal32(3, 2) 就是将整数3转换成含有两位小数的 DECIMAL32 类型的数据。

## 1.2 数据结构及定义

DolphinDB 目前支持 DECIMAL 类型的数据结构有：标量、向量、表等，本节主要介绍如何创建 DECIMAL 类型的各种数据结构。

### 1.2.1 标量

DolphinDB 中的 DECIMAL 类型的数据创建方式不同于 mysql 。在 mysql 中 DECIMAL 在创建时需要指定两个描述精度的数字，分别是 precision 和 scale，即 decimal (p, s)，p 代表整个 DECIMAL 包括整数和小数部分一共有多少位数字，s 代表 DECIMAL 的小数部分包含多少位数字。而在 DolphinDB 中定义一个 DECIMAL 类型的标量，我们只需要输入一个整型/浮点型/字符串类型的标量，并通过指定 scale，便可将其转换成DECIMAL 类型的数据，比如：

```
a=decimal32(142, 2)
//output：142.00

b=decimal32(1.23456, 3)
//output: 1.234

c=decimal32(`1.23456, 3)
//output: 1.234 
```

### 1.2.2 向量

在 DolphinDB 中定义一个 DECIMAL32/DECIMAL64 类型的向量，主要有以下几种方式（注意：一个DECIMAL 类型向量里的所有数据，类型和 scale 都需相同。）：

用户可以使用函数 bigarray 声明一个 DECIMAL32/DECIMAL64 类型的大数组，语法如下：

```
bigarray(DECIMAL32(scale), initialSize, [capacity], [defaultValue])
bigarray(DECIMAL64(scale), initialSize, [capacity], [defaultValue])

x=bigarray(DECIMAL32(3),0,10000000);
x.append!(1..1000)
//output:[1.000,2.000,3.000,4.000,5.000,6.000,7.000,8.000,9.000,10.000]
```

用户可以使用函数 array 声明一个 DECIMAL32/DECIMAL64 类型的数组，语法如下：

```
array(DECIMAL32(scale), [initialSize], [capacity], [defaultValue])
array(DECIMAL64(scale), [initialSize], [capacity], [defaultValue])

x=array(DECIMAL32(3), 10, 10, 2.3)
//output: [2.300,2.300,2.300,2.300,2.300,2.300,2.300,2.300,2.300,2.300]
```

或者使用以下方式进行数据类型转换：

```
m=[decimal32(1.2356, 3), decimal32(2.59874, 3), decimal32(-5.23564, 3)]
n=decimal32([1.2356, 2.59874, -5.23564], 3)
```

用户可以使用数组向量 arrayVector 声明一个 DECIMAL32/DECIMAL64 类型的大数组，语法如下：

```
array(DECIMAL32(scale)[], [initialSize], [capacity], [defaultValue])
array(DECIMAL64(scale)[], [initialSize], [capacity], [defaultValue])

x = array(DECIMAL32(5)[], 0, 10)
val1 = [1.77, 2.8, -3.77, -3.77, 77.32, 1.77]
val2 = [1.77, 2.8, NULL, -3.77, -3.77, 77.32, 1.77, NULL]
x.append!([val1, val2])
//output:[[1.77000,2.80000,-3.77000,-3.77000,77.31999,1.77000],[1.77000,2.80000,,-3.77000,-3.77000,77.31999,1.77000,]]
```

### 1.2.3 表

在 DolphinDB 中定义一个含有 DECIMAL 类型的 column，可以在建表时参考如下定义方式：

```
t=table(100:0, `id`val1`val2, [INT, DECIMAL32(4), DECIMAL64(8)])
```

可以向该表中插入 DECIMAL 类型的数据或整型/浮点型/字符串类型的数据。例如：

```
insert into t values(1, decimal32(2.345, 4), decimal64(2.3654, 8));
or
insert into t values(1, 2.345, 2.3654);
```

除了内存表支持存储 DECIMAL 类型的数据， 同样在 OLAP 和 TSDB 引擎中也支持存储 DECIMAL 类型的数据。示例如下：

```
// 在olap引擎中：
dbName="dfs://testDecimal_olap"
if(existsDatabase(dbName)){
	dropDatabase(dbName)
}
t=table(100:0, `id`sym`timev`val1`val2, [INT, SYMBOL, TIMESTAMP, DECIMAL32(4), DECIMAL64(8)])
db=database(dbName, VALUE, 1..10)
pt=db.createPartitionedTable(t, `pt, `id)
n=1000
data=table(rand(1..10, n) as id, rand("A"+string(1..10), n) as sym, rand(2022.11.24T12:23:45.456+1..100, n) as timev, rand(100.0, n) as val1, rand(100.0, n) as val2)
t.append!(data)
pt.append!(t)
select * from loadTable(dbName, `pt)

// 在tsdb引擎中：
dbName="dfs://testDecimal_tsdb"
if(existsDatabase(dbName)){
	dropDatabase(dbName)
}
t=table(100:0, `id`sym`timev`val1`val2, [INT, SYMBOL, TIMESTAMP, DECIMAL32(4), DECIMAL64(8)])
db=database(dbName, VALUE, 1..10, , "TSDB")
pt=db.createPartitionedTable(t, `pt, `id, , `sym`timev)
n=1000
data=table(rand(1..10, n) as id, rand("A"+string(1..10), n) as sym, rand(2022.11.24T12:23:45.456+1..100, n) as timev, rand(100.0, n) as val1, rand(100.0, n) as val2)
t.append!(data)
pt.append!(t)
select * from loadTable(dbName, `pt)
```

# 2. 数值范围

DECIMAL32/DECIMAL64 类型的数值范围如下表所示，其中，DECIMAL32(S) 和 DECIMAL64(S) 中的 S 表示保留的小数位数。

|                  | **底层存储数据类型** | **字节占用** | **Scale有效范围** | **有效数值范围**                        | **最大表示位数** |
| :--------------- | :------------------- | :----------- | ----------------- | --------------------------------------- | ---------------- |
| **DECIMAL32(S)** | int32_t              | 占用4个字节  | [0, 9]            | (-1 * 10 ^ (9 - S), 1 * 10 ^ (9 - S))   | 9位              |
| **DECIMAL64(S)** | int64_t              | 占用8个字节  | [0, 18]           | (-1 * 10 ^ (18 - S), 1 * 10 ^ (18 - S)) | 18位             |

在将其他数值类型转换为 DECIMAL 时，DolphinDB 不会检查其数值范围是否有效，仅在将字符串解析为DECIMAL 时进行检查。由此可知，将数值型数据强制转换为 DECIMAL32，若该数值的整数部分超过 DECIMAL32 的有效数值范围，但仍属于 [-2147483648, 2147483647]（4 字节整数（INT32）的有效数值范围），仍可转换成功；而将字符串类型数据强制转换成 DECIMAL32，其长度超过有效位数时系统抛异常。例如：强制类型转换整型数据 1000000000 为 DECIMAL32 时不会报错，因为 1000000000∈[-2147483647, 2147483648]，没有 overflow。但强制类型转换字符串"1000000000"为 DECIMAL32 时，系统会抛异常，这是因为该字符串包含10位数字，而 DECIMAL32 最多表示9位数。

因此，对 DECIMAL32/DECIMAL64 类型执行特定操作时，数值会溢出。为了保证数据结果的一致性和精准性，DolphinDB 会对计算结果做溢出校验。本章节将介绍 DolphinDB 系统中常见的三种溢出检查。

## 2.1 创建数据时的溢出检查

在创建 DECIMAL32/DECIMAL64 类型的数据时，会首先考虑有效数值范围和 scale 的有效范围，超出限定范围，则做溢出处理。若小数位超出 DECIMAL32/DECIMAL64 的 scale 有效范围，系统将报错：“Scale is out of bounds”。例如：

```
decimal32(1.2, 10)
decimal64(1.2, 19)
```

同样，若整数位数超出数据类型所能表示的最大位数也会做溢出处理，系统将报错：“Decimal math overflow”。例如：

```
decimal32(1000000000, 1)
decimal32(`1000000000, 1)
```

## 2.2 算术计算的溢出检查

即使创建数值时其没有超出有效数值范围，但随着数据在计算过程中小数位数的增多或者数值的增大，也有可能超出有效数值范围，导致溢出。例如：

```
6*decimal32(4.2, 8)
6*decimal32(100000000, 1)
```

## 2.3 比较运算中的溢出检查

溢出检查不仅存在于算术运算中，也存在于比较运算中。在比较 DECIMAL 类型的数据和其他数值类型的数据时，系统会自动将其他数值类型转换成 DECIMAL 类型，再进行比较运算。

注意：
1. 2.00.8 版本 server 会将其它数据类型转换为对应的 DECIMAL 类型。如下例，将100与 DECIMAL32 比较，会将100转换为 decimal32(100,8)，此时会报数据溢出的错误：

```
decimal32(1, 8) < 100
//output: Decimal math overflow
```
2. 2.00.9 及以上版本，在进行 DECIMAL 类型与其它数据类型的比较时，系统会将所有数据类型都转换为 DECIMAL64。此时运行上例，不会出现数据溢出的报错。

```
decimal32(1, 8) < 100
//output: true
```

# 3. 算术运算规则

## 3.1 DECIMAL 类型之间的算数规则及 scale 的规则

DolphinDB 数据库规定了 DECIMAL 类型的数据之间进行算术运算的规则，规则如下:

​        规则一：`DECIMAL32(S1) <op> DECIMAL32(S2) => DECIMAL32(S)`

```
m=decimal32(1.23, 3)+decimal32(2.45, 2)
//output:3.680
//typestr:DECIMAL32
```

​        规则二：`DECIMAL64(S1) <op> DECIMAL64(S2) => DECIMAL64(S)`

```
m=decimal64(1.23, 3)+decimal64(2.45, 2)
//output:3.680
//typestr:DECIMAL64
```

​        规则三：`DECIMAL64(S1) <op> DECIMAL32(S2) => DECIMAL64(S)`

```
m=decimal64(1.23, 3)+decimal32(2.45, 2)
//output:3.680
//typestr:DECIMAL64
```

​        规则四：`DECIMAL32(S1) <op> DECIMAL64(S2) => DECIMAL64(S)`

```
m=decimal32(1.23, 3)+decimal64(2.45, 2)
//output:3.680
//typestr:DECIMAL64
```

DolphinDB 数据库中 DECIMAL 类型的数据算术运算结果的 `scale` 由以下规则来确定:

- 对于加法和减法: `S = max(S1, S2)`
- 对于乘法: `S = S1 + S2`

```
m=decimal64(1.23, 3)*decimal32(2.45, 2)
//output:3.01350
//typestr:DECIMAL64
```

- 对于除法: `S = S1`

```
m=decimal64(1.23, 3)/decimal32(2.45, 2)
//output:0.502
//typestr:DECIMAL64
```

## 3.2 DECIMAL 类型与整型进行计算

在 DolphinDB 数据库中，DECIMAL 类型与整型 (INT/LONG) 进行运算时，会将整型转换成相同类型的 DECIMAL 再进行运算。计算 `decimal32(10, 2)*6`，相当于 `decimal32(10, 2)*decimal32(6, 0)`。因此，整数型数值乘以 scale 为 `S` 的DECIMAL类型的数据，结果的 scale 仍然为 `S`。

## 3.3 DECIMAL 类型与浮点数进行计算

在 DolphinDB 数据库中，DECIMAL 类型与浮点数之间的算术运算是未定义的，但是系统不会抛出异常， 如果确实需要这么做，建议先将浮点数强制转换成 DECIMAL 类型的数据。

# 4. 导入数据成 DECIMAL 类型

通过以下步骤，可以将导入数据转换成 DECIMAL 类型：

​       1. 使用 saveText 函数获得一个 *test_decimal.csv* 文件。

```
WORK_DIR="/hdd/hdd1/test_decimal/"
n=1000
t=table(rand(1..100, n) as id, rand(2022.11.23T12:39:56+1..100, n) as datetimev, rand(`AAPL`ARS`BSA, n) as sym, rand(rand(100.0, 10) join take(00f, 10), n) as val1, rand(rand(100.0, 10) join take(00f, 10), n) as val2)
saveText(t, WORK_DIR+"test_decimal.csv")
```

​       2. 使用 loadText 函数将 *test_decimal.csv* 中的部分列转换为 DECIMAL 类型。

```
shemaTable=table(`id`timev`sym`val1`val2 as name, [`INT, `DATETIME, `SYMBOL, "DECIMAL32(4)", "DECIMAL64(5)"] as type)
re=loadText(filePath, , shemaTable)
```

# 5. 对比 DECIMAL32/DECIMAL64 和 DOUBLE/FLOAT

## 5.1 指定小数位数

将无限多的实数压缩成有限的位数需要近似表示。尽管整数有无穷多个，但在大多数程序中，整数计算的结果可以用 32 位存储。相反，给定任何固定位数，大多数实数计算将产生无法使用那么多位数精确表示的量。因此，浮点计算的结果通常必须四舍五入以适应其有限表示。

DOUBLE 和 FLOAT 类型精度遵循 IEEE 754 标准，在表示有限的小数位数时，对数据进行四舍五入，如： 将 1.2356789 的小数位数缩减为三位，输出结果为：1.236。而 DECIMAL32/DECIMAL64 类型精度遵循 IEEE 754-2008 标准，在表示有限的小数位数时，将1.2356789 的小数位数缩减为三位，输出结果为：1.235。

## 5.2 精度差异

目前有很多种实数的表示方法， 其中最为广泛使用的是浮点数表示法（IEEE floating-point representation）。浮点数表示法有一个基数 β（通常假定为偶数）和一个精度 p，如果 β=10 且 p=3，则数字 0.1 被表示为 1.00 × 10 -1；如果 β=2 且 p=24，无法精确表示十进制数 0.1，近似为 1.10011001100110011001101 × 2 -4。

实数无法精确地表示为浮点数的原因主要有两个。第一个原因是类似于 0.1 这样的数字，具有有限的十进制表示，但是在二进制中能表示为无穷重复的数据，等于 0.1 的近似值，无法得精确数据。第二个原因是超出数据的数值范围，系统将对数据做一定处理。

数据类型 FLOAT/DOUBLE 属于 binary floating-point types，DOUBLE 型数据在运算时会先将数值转换成二进制的数值表示再做运算，但转换成二进制时，只能表示为无限循环小数，存在一定误差。而当数据超出 FLOAT 和 DOUBLE 的数值范围，在 DolphinDB 系统将结果置为 NULL，保证数据在溢出时可以继续计算。如 0/0 的结果为 NULL。而 DECIMAL 类型属于 decimal floating-point types，0.1 被表示为 1.00 × 10 -1，无精度缺失，且在数据溢出时，直接报 overflow 的错误，避免了数据超出数值范围时，结果精度的缺失。

## 5.3 局限性

在 DolphinDB 中，DECIMAL 类型与 FLOAT/DOUBLE 类型相比，目前所支持的功能和结构较少。

- 在功能方面，目前暂未支持流数据。
- 在函数支持方面，尚有少部分计算函数不支持 DECIMAL 类型。
- 数据结构方面，DolphinDB 系统目前暂未支持 DECIMAL 类型在 matrix 和 set 中使用。
- 数据类型转换方面，DolphinDB 系统暂不支持 BOOL/CHAR/SYMBOL/UUID/IPADDR/INT128 等类型和 temporal 集合下的时间相关类型与 DECIMAL 类型相互转换，其中 STRING/BLOB 类型的数据如需转换成 DECIMAL 类型，必须满足 STRING/BLOB 类型的数据可以转换成数值类型的前提。

综上所述，在选择一个合适的数据类型处理浮点数时，需要综合考虑类型的数值范围以及数据对精确度的要求等。
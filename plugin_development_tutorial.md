# DolphinDB 插件开发教程

DolphinDB 支持动态加载外部插件，以扩展系统功能。插件用 C\+\+ 编写，需要编译成 ".so" 或 ".dll" 共享库文件。插件使用的流程请参考 DolphinDB Plugin 的 [GitHub 页面](https://github.com/dolphindb/DolphinDBPlugin)。本文着重介绍如何开发插件，并详细介绍以下几个具体场景的插件开发流程：



- [1. 如何开发插件](#1-如何开发插件)
  - [1.1 基本概念](#11-基本概念)
  - [1.2 创建变量](#12-创建变量)
  - [1.3 异常处理和参数校验](#13-异常处理和参数校验)
    - [1.3.1 异常处理](#131-异常处理)
    - [1.3.2 参数校验的范例](#132-参数校验的范例)
  - [1.4 调用 DolphinDB 内置函数](#14-调用-dolphindb-内置函数)
- [2. 如何开发支持时间序列数据处理的插件函数](#2-如何开发支持时间序列数据处理的插件函数)
- [3. 如何开发用于处理分布式 SQL 的聚合函数](#3-如何开发用于处理分布式-sql-的聚合函数)
  - [3.1 聚合函数范例](#31-聚合函数范例)
  - [3.2 在 DolphinDB 中调用函数](#32-在-dolphindb-中调用函数)
  - [3.3 随机访问大数组](#33-随机访问大数组)
  - [3.4 应该选择哪种方式访问向量](#34-应该选择哪种方式访问向量)
- [4. 如何开发支持新的分布式算法的插件函数](#4-如何开发支持新的分布式算法的插件函数)
  - [4.1 分布式算法范例](#41-分布式算法范例)
  - [4.2 在 DolphinDB 中调用函数](#42-在-dolphindb-中调用函数)
- [5. 如何开发支持流数据处理的插件函数](#5-如何开发支持流数据处理的插件函数)
- [6. 如何开发支持外部数据源的插件函数](#6-如何开发支持外部数据源的插件函数)
  - [6.1 数据格式描述](#61-数据格式描述)
  - [6.2 `extractMyDataSchema` 函数](#62-extractmydataschema-函数)
  - [6.3 `loadMyData` 函数](#63-loadmydata-函数)
  - [6.4 `loadMyDataEx` 函数](#64-loadmydataex-函数)
  - [6.5 `myDataDS` 函数](#65-mydatads-函数)
- [7. 如何在插件代码中构造并使用 sql 语句](#7-如何在插件代码中构造并使用-sql-语句)
  - [7.1 使用步骤](#71-使用步骤)
    - [7.1.1 引入 *ScalarImp.h* 头文件](#711-引入-scalarimph-头文件)
    - [7.1.2 将待查询的 Table 对象放入 Heap 中](#712-将待查询的-table-对象放入-heap-中)
    - [7.1.3 拼接 sql 字符串](#713-拼接-sql-字符串)
    - [7.1.4 执行 sql](#714-执行-sql)
  - [7.2 完整代码示例](#72-完整代码示例)
    - [7.2.1 `select * from t` 的完整代码示例](#721-select--from-t-的完整代码示例)
    - [7.2.2 `select avg(x) from t` 的完整代码示例](#722-select-avgx-from-t-的完整代码示例)
- [8. 常见问题](#8-常见问题)
  - [8.1 如何处理开发的 windows 版本插件加载时的错误提示："The specified module could not be found"？](#81-如何处理开发的-windows-版本插件加载时的错误提示the-specified-module-could-not-be-found)
  - [8.2 插件开发时需要包含哪些库和头文件？](#82-插件开发时需要包含哪些库和头文件)
  - [8.3 编译时需要包含哪些选项？](#83-编译时需要包含哪些选项)
  - [8.4 如何处理编译时出现包含 std::\_\_cxx11 字样的链接问题（undefined reference）？](#84-如何处理编译时出现包含-std__cxx11-字样的链接问题undefined-reference)
  - [8.5 如何加载插件，可以卸载后重新加载吗？](#85-如何加载插件可以卸载后重新加载吗)
  - [8.6 如何处理执行插件函数时的报错信息："Connnection refused：connect" 或节点 crash 问题？](#86-如何处理执行插件函数时的报错信息connnection-refusedconnect-或节点-crash-问题)
  - [8.7 如何处理执行插件函数时的错误提示："Cannot recognize the token xxx"？](#87-如何处理执行插件函数时的错误提示cannot-recognize-the-token-xxx)
- [9. 附件](#9-附件)




# 1. 如何开发插件

## 1.1 基本概念

DolphinDB 的插件实现了能在脚本中调用的函数。一个插件函数可能是运算符函数（operator function），也可能是系统函数（system function），它们的区别在于，前者接受的参数个数小于等于 2，而后者可以接受任意个参数，并支持会话的访问操作。

开发一个运算符函数，需要编写一个原型为 ConstantSP (const ConstantSP& a, const ConstantSP& b) 的 C\+\+ 函数。当函数参数个数为 2 时，a 和 b 分别为插件函数的第一和第二个参数；当参数个数为 1 时，b 是一个占位符，没有实际用途；当没有参数时，a 和 b 均为占位符。

开发一个系统函数，需要编写一个原型为 ConstantSP (Heap* heap, vector<ConstantSP>& args) 的 C\+\+ 函数。用户在 DolphinDB 中调用插件函数时传入的参数，都按顺序保存在 C++ 的向量 args 中。heap 参数不需要用户传入。

函数原型中的 ConstantSP 可以表示绝大多数 DolphinDB 对象（标量、向量、矩阵、表，等等）。其他常用的派生自它的变量类型有 VectorSP（向量）以及 TableSP（表）等。

开发插件时所需的头文件通常位于 DolphinDBPlugin 项目的 include 目录下，用户可切换至指定版本下载。 此处给出 Gitee 中某版本插件头文件的[链接](https://gitee.com/dolphindb/DolphinDBPlugin/tree/release200.10/include)。更多说明可参阅本文 8.常见问题。

## 1.2 创建变量

创建标量，可以直接用 new 语句创建头文件 ScalarImp.h 中声明的类型对象，并将它赋值给一个 ConstantSP。 ConstantSP 是一个经过封装的智能指针，会在变量的引用计数为 0 时自动释放内存，因此，用户不需要手动删除已经创建的变量：

```cpp
ConstantSP i = new Int(1);                 // 相当于 1i
ConstantSP d = new Date(2019, 3, 14);      // 相当于 2019.03.14
ConstantSP s = new String("DolphinDB");    // 相当于 "DolphinDB"
ConstantSP voidConstant = new Void();      // 创建一个 void 类型变量，常用于表示空的函数参数
```

头文件 Util.h 声明了一系列函数，用于快速创建某个类型和格式的变量：

```cpp
VectorSP v = Util::createVector(DT_INT, 10);     // 创建一个初始长度为 10 的 INT 类型向量
v->setInt(0, 60);                                // 相当于 v[0] = 60

VectorSP t = Util::createVector(DT_ANY, 0);      // 创建一个初始长度为 0 的 ANY 类型向量（元组）
t->append(new Int(3));                           // 相当于 t.append!(3)
t->get(0)->setInt(4);                            // 相当于 t[0] = 4
// 这里不能用 t->setInt(0, 4)，因为 t 是一个元组，setInt(0, 4) 只对 INT 类型的向量有效

ConstantSP seq = Util::createIndexVector(5, 10); // 相当于 5..14
int seq0 = seq->getInt(0);                       // 相当于 seq[0]

ConstantSP mat = Util::createDoubleMatrix(5, 10);// 创建一个 10 行 5 列的 DOUBLE 类型矩阵
mat->setColumn(3, seq);                          // 相当于 mat[3] = seq
```

## 1.3 异常处理和参数校验

### 1.3.1 异常处理

插件开发时的异常抛出和处理，和一般 C\+\+ 开发中一样，都通过 throw 关键字抛出异常， try 语句块处理异常。DolphinDB 在头文件 Exceptions.h 中声明了异常类型。插件函数若遇到运行时错误，一般抛出 RuntimeException。

在插件开发时，通常会校验函数参数，如果参数不符合要求，抛出一个 IllegalArgumentException。常用的参数校验函数有：

- `ConstantSP->getType()`：返回变量的类型（INT, CHAR, DATE 等等），DolphinDB 的类型定义在头文件 Types.h 中。
- `ConstantSP->getCategory()`：返回变量的类别，常用的类别有 INTEGRAL（整数类型，包括 INT, CHAR, SHORT, LONG 等）、FLOATING（浮点数类型，包括 FLOAT, DOUBLE 等）、TEMPORAL（时间类型，包括 TIME, DATE, DATETIME 等）、LITERAL（字符串类型，包括 STRING, SYMBOL 等），都定义在头文件 Types.h 中。
- `ConstantSP->getForm()`：返回变量的格式（标量、向量、表等等），DolphinDB 的格式定义在头文件 Types.h 中。
- `ConstantSP->isVector()`：判断变量是否为向量。
- `ConstantSP->isScalar()`：判断变量是否为标量。
- `ConstantSP->isTable()`：判断变量是否为表。
- `ConstantSP->isNumber()`：判断变量是否为数字类型。
- `ConstantSP->isNull()`：判断变量是否为空值。
- `ConstantSP->getInt()`：获得变量对应的整数值。
- `ConstantSP->getString()`：获得变量对应的字符串。
- `ConstantSP->size()`：获得变量的长度。

更多参数校验函数一般在头文件 CoreConcept.h 的 Constant 类方法中。

### 1.3.2 参数校验的范例

本节将开发一个插件函数用于求非负整数的阶乘，返回一个 LONG 类型变量。DolphinDB 中 LONG 类型的最大值为 2^63-1，能表示的阶乘最大为 25!，因此只有 0~25 范围内的参数是合法的。

```cpp
#include "CoreConcept.h"
#include "Exceptions.h"
#include "ScalarImp.h"

ConstantSP factorial(const ConstantSP &n, const ConstantSP &placeholder) {
    string syntax = "Usage: factorial(n).";
    if (!n->isScalar() || n->getCategory() != INTEGRAL)
        throw IllegalArgumentException("factorial", syntax + "n must be an integral scalar.");
    int nValue = n->getInt();
    if (nValue < 0 || nValue> 25)
        throw IllegalArgumentException("factorial", syntax + "n must be a non-negative integer less than 26.");

    long long fact = 1;
    for (int i = nValue; i> 0; i--)
        fact *= i;
    return new Long(fact);
}
```

## 1.4 调用 DolphinDB 内置函数

有时需要调用 DolphinDB 的内置函数对数据进行处理。有些类已经定义了部分常用的内置函数作为方法：

```cpp
VectorSP v = Util::createIndexVector(1, 100);
ConstantSP avg = v->avg();     // 相当于 avg(v)
ConstantSP sum2 = v->sum2();   // 相当于 sum2(v)
v->sort(false);                // 相当于 sort(v, false)
```

如果需要调用其它内置函数，插件函数的类型必须是系统函数。通过 heap->currentSession()->getFunctionDef 函数获得一个内置函数，然后用 `call` 方法调用它。如果该内置函数是运算符函数，应调用原型 call(Heap, const ConstantSP&, const ConstantSP&)；如果是系统函数，应调用原型 call(Heap, vector<ConstantSP>&)。以下是调用内置函数 `cumsum` 的一个例子：

```cpp
ConstantSP v = Util::createIndexVector(1, 100);
v->setTemporary(false);                                   //v 的值可能在内置函数调用时被修改。如果不希望它被修改，应先调用 setTemporary(false)
FunctionDefSP cumsum = heap->currentSession()->getFunctionDef("cumsum");
ConstantSP result = cumsum->call(heap, v, new Void());
// 相当于 cumsum(v)，这里的 new Void() 是一个占位符，没有实际用途
```

# 2. 如何开发支持时间序列数据处理的插件函数

DolphinDB 的特色之一在于它对时间序列有良好支持。本章以编写一个 [msum](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/m/msum.html) 函数的插件为例，介绍如何开发插件函数支持时间序列数据处理。

时间序列处理函数通常接受向量作为参数，并对向量中的每个元素进行计算处理。在本例中，`msum` 函数接受两个参数：一个向量和一个窗口大小。它的原型是：

```cpp
ConstantSP msum(const ConstantSP &X, const ConstantSP &window);
```

`msum` 函数的返回值是一个和输入向量同样长度的向量。本例为简便起见，假定返回值是一个 DOUBLE 类型的向量。可以通过 Util::createVector 函数预先为返回值分配空间：

```cpp
int size = X->size();
int windowSize = window->getInt();
ConstantSP result = Util::createVector(DT_DOUBLE, size);
```

<!--
在 DolphinDB 中，一个向量可能是 Fast vector，也可能是 [bigarray](https://www.dolphindb.cn/cn/help/DataTypesandStructures/DataForms/Vector/BigArray.html)，它们的实现机制不同，需要用 `isFastMode` 函数判断，分别处理：

```
VectorSP x = X;
int windowSize = window->getInt();
if (x->isFastMode()) {
    // ...
}
else {
    // ...
}
```

## 对 Fast vector 的处理
-->

在 DolphinDB 插件编写时处理向量，可以循环使用 `getDoubleConst`, `getIntConst` 等函数，批量获得一定长度的只读数据，保存在相应类型的缓冲区中，从缓冲区中取得数据进行计算。这样做的效率比循环使用 `getDouble`, `getInt` 等函数要高。本例为简便起见，统一使用 `getDoubleConst`，每次获得长度为 Util::BUF_SIZE 的数据。这个函数返回一个 const double* ，指向缓冲区头部：

```cpp
double buf[Util::BUF_SIZE];

INDEX start = 0;
while (start < size) {
    int len = std::min(Util::BUF_SIZE, size - start);
    const double *p = X->getDoubleConst(start, len, buf);
    for (int i = 0; i < len; i++) {
        double val = p[i];
        // ...
    }
    start += len;
}
```

在本例中，`msum` 将计算 X 中长度为 windowSize 的窗口中所有数据的和。可以用一个临时变量 tmpSum 记录当前窗口的和，每当窗口移动时，只要给 tmpSum 增加新窗口尾部的值，减去旧窗口头部的值，就能计算得到当前窗口中数据的和。为了将计算值写入 result，可以循环用 result->getDoubleBuffer 获取一个可读写的缓冲区，写完后使用 result->setDouble 函数将缓冲区写回数组。`setDouble` 函数会检查给定的缓冲区地址和变量底层储存的地址是否一致，如果一致就不会发生数据拷贝。在多数情况下，用 `getDoubleBuffer` 获得的缓冲区就是变量实际的存储区域，这样能减少数据拷贝，提高性能。

需要注意的是，DolphinDB 用 DOUBLE 类型的最小值（已经定义为宏 DBL_NMIN ）表示 DOUBLE 类型的 NULL 值，要专门判断。

返回值的前 windowSize - 1 个元素为 NULL。可以对 X 中的前 windowSize 个元素和之后的元素用两个循环分别处理，前一个循环只计算累加，后一个循环执行加和减的操作。最终的实现如下：

```cpp
ConstantSP msum(const ConstantSP &X, const ConstantSP &window) {
    INDEX size = X->size();
    int windowSize = window->getInt();
    ConstantSP result = Util::createVector(DT_DOUBLE, size);

    double buf[Util::BUF_SIZE];
    double windowHeadBuf[Util::BUF_SIZE];
    double resultBuf[Util::BUF_SIZE];
    double tmpSum = 0.0;

    INDEX start = 0;
    while (start < windowSize) {
        int len = std::min(Util::BUF_SIZE, windowSize - start);
        const double *p = X->getDoubleConst(start, len, buf);
        double *r = result->getDoubleBuffer(start, len, resultBuf);
        for (int i = 0; i < len; i++) {
            if (p[i] != DBL_NMIN)    // p[i] is not NULL
                tmpSum += p[i];
            r[i] = DBL_NMIN;
        }
        result->setDouble(start, len, r);
        start += len;
    }

    result->setDouble(windowSize - 1, tmpSum);    // 上一个循环多设置了一个 NULL，填充为 tmpSum

    while (start < size) {
        int len = std::min(Util::BUF_SIZE, size - start);
        const double *p = X->getDoubleConst(start, len, buf);
        const double *q = X->getDoubleConst(start - windowSize, len, windowHeadBuf);
        double *r = result->getDoubleBuffer(start, len, resultBuf);
        for (int i = 0; i < len; i++) {
            if (p[i] != DBL_NMIN)
                tmpSum += p[i];
            if (q[i] != DBL_NMIN)
                tmpSum -= q[i];
            r[i] = tmpSum;
        }
        result->setDouble(start, len, r);
        start += len;
    }

    return result;
}
```

# 3. 如何开发用于处理分布式 SQL 的聚合函数

在 DolphinDB 中，SQL 的聚合函数通常接受一个或多个向量作为参数，最终返回一个标量。在开发聚合函数的插件时，需要了解如何访问向量中的元素。

DolphinDB 中的向量有两种存储方式。一种是常规数组，数据在内存中连续存储，另一种是 [大数组](https://www.dolphindb.cn/cn/help/DataTypesandStructures/DataForms/Vector/BigArray.html)，其中的数据分块存储。

本章将以编写一个求 [几何平均数](https://en.wikipedia.org/wiki/Geometric_mean) 的函数为例，介绍如何开发聚合函数，重点关注数组中元素的访问。

## 3.1 聚合函数范例

几何平均数 `geometricMean` 函数接受一个向量作为参数。为了防止溢出，一般采用其对数形式计算，即

```cpp
geometricMean([x1, x2, ..., xn])
    = exp((log(x1) + log(x2) + log(x3) + ... + log(xn))/n)
```

为了实现这个函数的分布式版本，可以先开发聚合函数插件 `logSum`，用以计算某个分区上的数据的对数和，然后用 defg 关键字定义一个 reduce 函数，用 mapr 关键字定义一个 MapReduce 函数。

在 DolphinDB 插件开发中，对数组的操作通常要考虑它是常规数组还是大数组。可以用 `isFastMode` 函数判断：

```cpp
ConstantSP logSum(const ConstantSP &x, const ConstantSP &placeholder) {
    if (((VectorSP) x)->isFastMode()) {
        // ...
    }
    else {
        // ...
    }
}
```

如果是常规数组，它在内存中连续存储。可以用 `getDataArray` 函数获得它数据的指针。假定数据是以 DOUBLE 类型存储的：

```cpp
if (((VectorSP) x)->isFastMode()) {
    int size = x->size();
    double *data = (double *) x->getDataArray();

    double logSum = 0;
    for (int i = 0; i < size; i++) {
        if (data[i] != DBL_NMIN)    // is not NULL
            logSum += std::log(data[i]);
    }
    return new Double(logSum);
}
```

如果是大数组，它在内存中分块存储。可以用 `getSegmentSize` 获得每个块的大小；用 `getDataSegment` 获得首个块的地址，以返回一个二级指针，指向一个指针数组，这个数组中的每个元素指向每个块的数据数组：

```cpp
// ...
else {
    int size = x->size();
    int segmentSize = x->getSegmentSize();
    double **segments = (double **) x->getDataSegment();
    INDEX start = 0;
    int segmentId = 0;
    double logSum = 0;

    while (start < size) {
        double *block = segments[segmentId];
        int blockSize = std::min(segmentSize, size - start);
        for (int i = 0; i < blockSize; i++) {
            if (block[i] != DBL_NMIN)    // is not NULL
                logSum += std::log(block[i]);
        }
        start += blockSize;
        segmentId++;
    }
    return new Double(logSum);
}
```

以上代码针对 DOUBLE 数据类型。在实际开发中，数组的底层存储不一定是 DOUBLE 类型，也可能涉及多种数据类型，此时可采用泛型编程。附件中有一个泛型编程的代码例子。

## 3.2 在 DolphinDB 中调用函数

通常需要实现一个聚合函数的非分布式版本和分布式版本，系统会基于哪个版本更高效来选择调用这个版本。

在 DolphinDB 中定义非分布式的 `geometricMean` 函数：

```cpp
def geometricMean(x) {
	return exp(logSum::logSum(x) \ count(x))
}
```

然后通过定义 Map 和 Reduce 函数，最终用 `mapr` 定义分布式的版本：

```cpp
def geometricMeanMap(x) {
	return logSum::logSum(x)
}

defg geometricMeanReduce(myLogSum, myCount) {
    return exp(sum(myLogSum) \ sum(myCount))
}

mapr geometricMean(x) { geometricMeanMap(x), count(x) -> geometricMeanReduce }
```

如果是在单机环境中执行这个函数，只需要在执行的节点上加载插件。如果有数据位于远程节点，需要在每一个远程节点加载插件。可以手动在每个节点执行 `loadPlugin` 函数，也可以用以下脚本快速在每个节点上加载插件：

```cpp
each(rpc{, loadPlugin, pathToPlugin}, getDataNodes())
```

通过以下脚本创建一个分区表，验证函数：

```cpp
db = database("", VALUE, 1 2 3 4)
t = table(take(1..4, 100) as id, rand(1.0, 100) as val)
t0 = db.createPartitionedTable(t, `tb, `id)
t0.append!(t)
select geometricMean(val) from t0 group by id;
```

## 3.3 随机访问大数组

可以对大数组进行随机访问，但要经过下标计算。用 `getSegmentSizeInBit` 函数获得块大小的二进制位数，通过位运算获得块的偏移量和块内偏移量：

```cpp
int segmentSizeInBit = x->getSegmentSizeInBit();
int segmentMask = (1 << segmentSizeInBit) - 1;
double **segments = (double **) x->getDataSegment();

int index = 3000000;    // 想要访问的下标

double result = segments[index>> segmentSizeInBit][index & segmentMask];
//                       ^ 块的偏移量                ^ 块内偏移量
```

## 3.4 应该选择哪种方式访问向量

上一章 [如何开发支持时间序列数据处理的插件函数](#2 - 如何开发支持时间序列数据处理的插件函数) 介绍了通过 `getDoubleConst`, `getIntConst` 等一组方法获得只读缓冲区，以及通过 `getDoubleBuffer`, `getIntBuffer` 等一组方法获得可读写缓冲区。这两种访问向量的方法在实际开发比较通用。

本章介绍了通过 `getDataArray` 和 `getDataSegment` 方法直接访问向量的底层存储。在某些特别的场合，例如明确知道数据存储在大数组中，且知道数据的类型，这种方法比较适合。

# 4. 如何开发支持新的分布式算法的插件函数

在 DolphinDB database 中，MapReduce 是执行分布式算法的通用计算框架。DolphinDB 提供了 [mr](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/m/mr.html) 函数和 [imr](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/i/imr.html) 函数，使用户能通过脚本实现分布式算法。在编写分布式算法的插件时，使用的同样是这两个函数。对通用计算的详细介绍，可以参考[通用计算教程](general_computing.md)。本章主要介绍如何用 C\+\+ 语言编写自定义的 map, reduce 等函数，并调用 `mr` 和 `imr` 这两个函数，最终实现分布式计算。

## 4.1 分布式算法范例

本章将使用 `mr`，实现一个函数，求分布式表中多个指定列中所有数据的平均值。我们会介绍编写 DolphinDB 分布式算法插件的整体流程，及需要注意的技术细节。

在插件开发中，用户自定义的 map, reduce, final, term 函数，可以是运算符函数，也可以是系统函数。

本例的 map 函数，对表的每个分区内的所有指定列做计算。每个分区返回一个长度为 2 的元组，包含数据之和，以及非空元素的个数。具体实现如下：

```cpp
ConstantSP columnAvgMap(Heap *heap, vector<ConstantSP> &args) {
    TableSP table = args[0];
    ConstantSP colNames = args[1];
    double sum = 0.0;
    int count = 0;

    for (int i = 0; i < colNames->size(); i++) {
        string colName = colNames->getString(i);
        VectorSP col = table->getColumn(colName);
        sum += col->sum()->getDouble();
        count += col->count();
    }

    ConstantSP result = Util::createVector(DT_ANY, 2);
    result->set(0, new Double(sum));
    result->set(1, new Int(count));
    return result;
}
```

本例的 reduce 函数，是对 map 结果的相加。可使用 DolphinDB 的内置函数 `add`。用 heap->currentSession()->getFunctionDef("add") 获得这个函数：

```cpp
FunctionDefSP reduceFunc = heap->currentSession()->getFunctionDef("add");
```

本例的 final 函数，是对 reduce 结果中的数据总和 `sum` 和非空元素个数 `count` 做除法，求得所有分区中对应列的平均数。具体实现如下：

```cpp
ConstantSP columnAvgFinal(const ConstantSP &result, const ConstantSP &placeholder) {
    double sum = result->get(0)->getDouble();
    int count = result->get(1)->getInt();

    return new Double(sum / count);
}
```

定义了 map, reduce, final 等函数后，将它们导出为插件函数（在头文件的函数声明前加上 extern "C" ，并在加载插件的文本文件中列出这些函数），然后通过 heap->currentSession->getFunctionDef 获取这些函数，就能以这些函数为参数调用 `mr` 函数。如：

```cpp
FunctionDefSP mapFunc = Heap->currentSession()->getFunctionDef("columnAvg::columnAvgMap");
```

在本例中，map 函数接受两个参数 table 和 colNames ，但 `mr` 只允许 map 函数有一个参数，因此需要以 [部分应用](https://www.dolphindb.cn/cn/help/Functionalprogramming/PartialApplication.html) 的形式调用 map 函数，可以用 Util::createPartialFunction 将它包装为部分应用，实现如下：

```cpp
vector<ConstantSP> mapWithColNamesArgs {new Void(), colNames};
FunctionDefSP mapWithColNames = Util::createPartialFunction(mapFunc, mapWithColNamesArgs);
```

用 heap->currentSession()->getFunctionDef("mr") 获得系统内置函数 `mr`，调用 mr->call 方法，就相当于在 DolphinDB 脚本中调用 `mr` 函数。

最后实现的 columnAvg 函数定义如下：

```cpp
ConstantSP columnAvg(Heap *heap, vector<ConstantSP> &args) {
    ConstantSP ds = args[0];
    ConstantSP colNames = args[1];

    FunctionDefSP mapFunc = heap->currentSession()->getFunctionDef("columnAvg::columnAvgMap");
    vector<ConstantSP> mapWithColNamesArgs = {new Void(), colNames};
    FunctionDefSP mapWithColNames = Util::createPartialFunction(mapFunc, mapWithColNamesArgs);    // columnAvgMap{, colNames}
    FunctionDefSP reduceFunc = heap->currentSession()->getFunctionDef("add");
    FunctionDefSP finalFunc = heap->currentSession()->getFunctionDef("columnAvg::columnAvgFinal");

    FunctionDefSP mr = heap->currentSession()->getFunctionDef("mr");    // mr(ds, columnAvgMap{, colNames}, add, columnAvgFinal)
    vector<ConstantSP> mrArgs = {ds, mapWithColNames, reduceFunc, finalFunc};
    return mr->call(heap, mrArgs);
}
```

## 4.2 在 DolphinDB 中调用函数

如果是在单机环境中执行这个函数，只需要在执行的节点上加载插件。但如果计算需要用到位于远程节点的数据，就需要在每一个远程节点加载插件。可以手动在每个节点执行 `loadPlugin` 函数，也可以用以下脚本快速在每个节点上加载插件：

```cpp
each(rpc{, loadPlugin, pathToPlugin}, getDataNodes())
```

加载插件后，用 `sqlDS` 函数生成数据源，并调用函数：

```cpp
n = 100
db = database("dfs://testColumnAvg", VALUE, 1..4)
t = db.createPartitionedTable(table(10:0, `id`v1`v2, [INT,DOUBLE,DOUBLE]), `t, `id)
t.append!(table(take(1..4, n) as id, rand(10.0, n) as v1, rand(100.0, n) as v2))

ds = sqlDS(<select * from t>)
columnAvg::columnAvg(ds, `v1`v2)
```

# 5. 如何开发支持流数据处理的插件函数

在 DolphinDB 中，流数据订阅端可以通过一个 handler 函数处理收到的数据。订阅数据可以是一个数据表，或一个元组，由 `subscribeTable` 函数的 msgAsTable 参数决定。通常可以用 handler 函数对流数据进行过滤、插入另一张表等操作。

本章将编写一个 handler 函数。它接受的消息类型是元组。另外接受两个参数：一个是 INT 类型的标量或向量 indices，表示元组中元素的下标，另一个是一个表 table。它将元组中对应下标的列插入到表中。

向表中添加数据的接口是 bool append(vector<ConstantSP>& values, INDEX& insertedRows, string& errMsg)，如果插入成功，返回 true，并向 insertedRows 中写入插入的行数。否则返回 false，并在 errMsg 中写入出错信息。插件的实现如下：

```cpp
ConstantSP handler(Heap *heap, vector<ConstantSP> &args) {
    ConstantSP indices = args[0];
    TableSP table = args[1];
    ConstantSP msg = args[2];

    vector<ConstantSP> msgToAppend;
    for (int i = 0; i < indices->size(); i++) {
        int index = indices->getIndex(i)
        msgToAppend.push_back(msg->get(index));
    }

    INDEX insertedRows;
    string errMsg;
    table->append(msgToAppend, insertedRows, errMsg);
    return new Void();
}
```

在实际应用中，可能需要知道插入出错时的原因。可以引入头文件 Logger.h，将出错信息写入日志中。注意需要在编译插件时加上宏定义 -DLOGGING_LEVEL_2：

```cpp
// ...
bool success = table->append(msgToAppend, insertedRows, errMsg);
if (!success)
    LOG_ERR("Failed to append to table:", errMsg);
```

可以用以下脚本模拟流数据写入，验证 handler 函数：

```cpp
loadPlugin("/path/to/PluginHandler.txt")

share streamTable(10:0, `id`sym`timestamp, [INT,SYMBOL,TIMESTAMP]) as t0
t1 = table(10:0, `sym`timestamp, [SYMBOL,TIMESTAMP])
subscribeTable(, `t0, , , handler::handler{[1,2], t1})

t0.append!(table(1..100 as id, take(`a`b`c`d, 100) as symbol, now() + 1..100 as timestamp))

select * from t1
```

# 6. 如何开发支持外部数据源的插件函数

在为第三方数据设计可扩展的接口插件时，有几个需要关注的问题：

1. 数据源（Data source）。数据源是一个特殊的数据对象，包含了数据实体的元描述，执行一个数据源能获得数据实体，可能是表、矩阵、向量等等。用户可以提供数据源调用 `olsEx`, `randomForestClassifier` 等分布式计算函数，也可以调用 `mr`, `imr` 或 ComputingModel.h 中定义的更底层的计算模型做并行计算。DolphinDB 的内置函数 `sqlDS` 就通过 SQL 表达式获取数据源。在设计第三方数据接口时，通常需要实现一个获取数据源的函数，它将大的文件分成若干个部分，每部分都表示数据的一个子集，最后返回一个数据源的元组。数据源一般用一个 Code object 表示，是一个函数调用，它的参数是元程序，返回一个表。

2. 结构（Schema）。表的结构描述了表的列数，每一列的列名和数据类型。第三方接口通常需要实现一个函数，快速获得数据的表结构，以便用户在这个结构的基础上调整列名和列的数据类型。

3. IO 问题。在多核多 CPU 的环境中，IO 可能成为瓶颈。DolphinDB 提供了抽象的 IO 接口 `DataInputStream` 和 `DataOutputStream`。这些接口封装了数据压缩，Endianness，IO 类型（网络，磁盘，buffer 等）等细节，方便开发。此外还特别实现了针对多线程的 IO 实现 (`BlockFileInputStream` 和 `BlockFileOutputStream`)。这个实现有两个优点：

    - 实现计算和 IO 并行。当一个线程在处理数据的时候，后台线程会异步帮这个线程预读取后面需要的数据。

    - 避免了多线程的磁盘竞争。当线程个数增加的时候，如果并行往同一个磁盘上读写，性能会急剧下降。这个实现，会对同一个磁盘的读写串行化，从而提高吞吐量。

本章将介绍通常需要实现的几个函数，为设计第三方数据接口提供一个简单的范例。

## 6.1 数据格式描述

假定本例中的数据储存在 [平面文件数据库](https://en.wikipedia.org/wiki/Flat-file_database)，以二进制格式按行存储，数据从文件头部直接开始存储。每行有四列，分别为 id（按有符号 64 位长整型格式存储，8 字节），symbol（按 C 字符串格式以 ASCII 码编码存储，8 字节），date（按 BCD 码格式存储，8 字节），value（按 IEEE 754 标准的双精度浮点数格式存储，8 字节），每行共 32 字节。以下是一行的例子：

| id   | symbol | date     | value |
| ---- | ------ | -------- | ----- |
| 5    | IBM    | 20190313 | 10.1  |

这一行的十六进制表示为：

```
0x 00 00 00 00 00 00 00 05
0x 49 42 4D 00 00 00 00 00
0x 02 00 01 09 00 03 01 03
0x 40 24 33 33 33 33 33 33
```

## 6.2 `extractMyDataSchema` 函数

这个函数提取数据文件的表结构。在本例中，表结构是确定的，不需要实际读取文件。通过 Util::createTable 函数创建一张结构表：

```cpp
ConstantSP extractMyDataSchema(const ConstantSP &placeholderA, const ConstantSP &placeholderB) {
    ConstantSP colNames = Util::createVector(DT_STRING, 4);
    ConstantSP colTypes = Util::createVector(DT_STRING, 4);
    string names[] = {"id", "symbol", "date", "value"};
    string types[] = {"LONG", "SYMBOL", "DATE", "DOUBLE"};
    colNames->setString(0, 4, names);
    colTypes->setString(0, 4, types);

    vector<ConstantSP> schema = {colNames, colTypes};
    vector<string> header = {"name", "type"};

    return Util::createTable(header, schema);
}
```

在实际开发中，可能需要以读取文件头等方式获得表结构。如何读文件将在后面介绍。

## 6.3 `loadMyData` 函数

`loadMyData` 函数读取文件，并输出一张 DolphinDB 表。给定一个文件的路径，可以通过 Util::createBlockFileInputStream 创建一个输入流，此后，可对这个流调用 `readBytes` 函数读取给定长度的字节，`readBool` 读取下一个 bool 值，`readInt` 读取下一个 int 值，等等。本例给 `loadMyData` 函数设计的语法为：`loadMyData(path, [start], [length])`。除了接受文件路径 path ，还接受两个 INT 类型的参数 start 和 length，分别表示开始读取的行数和需要读取的总行数。`createBlockFileInputStream` 函数可以通过参数决定开始读取的字节数和需要读取的总字节数。

```cpp
ConstantSP loadMyData(Heap *heap, vector<ConstantSP> &args) {
    ConstantSP path = args[0];
    long long fileLength = Util::getFileLength(path->getString());
    size_t bytesPerRow = 32;

    int start = args.size()>= 2 ? args[1]->getInt() : 0;
    int length = args.size()>= 3 ? args[2]->getInt() : fileLength / bytesPerRow - start;

    DataInputStreamSP inputStream = Util::createBlockFileInputStream(path->getString(), 0, fileLength, Util::BUF_SIZE, start * bytesPerRow, length * bytesPerRow);
    char buf[Util::BUF_SIZE];
    size_t actualLength;

    while (true) {
        inputStream->readBytes(buf, Util::BUF_SIZE, actualLength);
        if (actualLength <= 0)
            break;
        // ...
    }
}
```

在读取数据时，通常将数据缓存到数组中，等待缓冲区满后批量插入。例如，假定要读取一个内容全为 CHAR 类型字节的二进制文件，将它写入一个 CHAR 类型的 DolphinDB 向量 vec，最后返回只由 vec 一列组成的表：

```cpp
char buf[Util::BUF_SIZE];
VectorSP vec = Util::createVector(DT_CHAR, 0);
size_t actualLength;

while (true) {
    inputStream->readBytes(buf, Util::BUF_SIZE, actualLength);
    if (actualLength <= 0)
        break;
    vec->appendChar(buf, actualLength);
}

vector<ConstantSP> cols = {vec};
vector<string> colNames = {"col0"};

return Util::createTable(colNames, cols);
```

本节的完整代码请参考附件中的代码。在实际开发中，加载数据的函数可能还会接受表结构参数 schema，按实际需要改变读取的数据类型。

## 6.4 `loadMyDataEx` 函数

`loadMyData` 函数将数据加载到内存，当数据文件非常庞大时，工作机的内存很容易成为瓶颈。所以设计 `loadMyDataEx` 函数解决这个问题。它通过边导入边保存的方式，把静态的二进制文件以较为平缓的数据流的方式保存为 DolphinDB 的分布式表，而不是采用全部导入内存再存为分区表的方式，从而降低内存的使用需求。

`loadMyDataEx` 函数的参数可以参考 DolphinDB 内置函数 `loadTextEx`。它的语法是：`loadMyDataEx(dbHandle, tableName, partitionColumns, path, [start], [length])`。如果数据库中的表存在，则将导入的数据添加到已有的表 result 中。如果表不存在，则创建一张表 result，然后添加数据。最后返回这张表。

```cpp
string dbPath = ((SystemHandleSP) dbHandle)->getDatabaseDir();
long long fileLength = Util::getFileLength(path->getString());
vector<ConstantSP> existsTableArgs = {new String(dbPath), tableName};
bool existsTable = heap->currentSession()->getFunctionDef("existsTable")->call(heap, existsTableArgs)->getBool();    // 相当于 existsTable(dbPath, tableName)
ConstantSP result;
if (existsTable) {    // 若表存在，加载表
    vector<ConstantSP> loadTableArgs = {dbHandle, tableName};
    result = heap->currentSession()->getFunctionDef("loadTable")->call(heap, loadTableArgs);    // 相当于 loadTable(dbHandle, tableName)
}
else {    // 若表不存在，创建表
    TableSP schema = extractMyDataSchema(new Void(), new Void());
    ConstantSP dummyTable = DBFileIO::createEmptyTableFromSchema(schema);
    vector<ConstantSP> createTableArgs = {dbHandle, dummyTable, tableName, partitionColumns};
    result = heap->currentSession()->getFunctionDef("createPartitionedTable")->call(heap, createTableArgs);    // 相当于 createPartitionedTable(db, dummyTable, tableName, partitionColumns)
}
```

读取数据并添加到表中的代码实现采用了 [pipeline 框架](https://www.dolphindb.cn/cn/help/FunctionsandCommands/FunctionReferences/p/pipeline.html)。它的初始任务是一系列具有不同 start 参数的 `loadMyData` 函数调用，pipeline 的 `follower` 函数是一个部分应用 append!{result}，相当于把整个读取数据的任务分成若干份执行，调用 `loadMyData` 分块读取后，将相应的数据通过 `append!` 插入表中。核心部分的代码如下：

```cpp
int sizePerPartition = 16 * 1024 * 1024;
int partitionNum = fileLength / sizePerPartition;
vector<DistributedCallSP> tasks;
FunctionDefSP func = Util::createSystemFunction("loadMyData", loadMyData, 1, 3, false);
int partitionStart = start;
int partitionLength = length / partitionNum;
for (int i = 0; i < partitionNum; i++) {
    if (i == partitionNum - 1)
        partitionLength = length - partitionLength * i;
    vector<ConstantSP> partitionArgs = {path, new Int(partitionStart), new Int(partitionLength)};
    ObjectSP call = Util::createRegularFunctionCall(func, partitionArgs);    // 将会调用 loadMyData(path, partitionStart, partitionLength)
    tasks.push_back(new DistributedCall(call, true));
    partitionStart += partitionLength;
}
vector<ConstantSP> appendToResultArgs = {result};
FunctionDefSP appendToResult = Util::createPartialFunction(heap->currentSession()->getFunctionDef("append!"), appendToResultArgs);    // 相当于 append!{result}
vector<FunctionDefSP> functors = {appendToResult};
PipelineStageExecutor executor(functors, false);
executor.execute(heap, tasks);
```

本节的完整代码请参考附件中的代码。用 Pipeline 框架实现数据的分块导入，只是一种思路。在具体开发时，可以采用 ComputingModel.h 中声明的 `StaticStageExecutor`，也可以使用 Concurrent.h 中声明的线程模型 Thread。实现方法有很多种，需要根据实际场景选择。

## 6.5 `myDataDS` 函数

`myDataDS` 函数返回一个数据源的元组。每个数据源都是一个表示函数调用的 Code object，可以通过 Util::createRegularFunctionCall 生成。执行这个对象可以取得对应的数据。以下是基于 `loadMyData` 函数产生数据源的一个例子：

```cpp
ConstantSP myDataDS(Heap *heap, vector<ConstantSP> &args) {
    ConstantSP path = args[0];
    long long fileLength = Util::getFileLength(path->getString());
    size_t bytesPerRow = 32;

    int start = args.size()>= 2 ? args[1]->getInt() : 0;
    int length = args.size()>= 3 ? args[2]->getInt() : fileLength / bytesPerRow - start;

    int sizePerPartition = 16 * 1024 * 1024;
    int partitionNum = fileLength / sizePerPartition;

    int partitionStart = start;
    int partitionLength = length / partitionNum;

    FunctionDefSP func = Util::createSystemFunction("loadMyData", loadMyData, 1, 3, false);
    ConstantSP dataSources = Util::createVector(DT_ANY, partitionNum);
    for (int i = 0; i < partitionNum; i++) {
        if (i == partitionNum - 1)
            partitionLength = length - partitionLength * i;
        vector<ConstantSP> partitionArgs = {path, new Int(partitionStart), new Int(partitionLength)};
        ObjectSP code = Util::createRegularFunctionCall(func, partitionArgs);    // 将会调用 loadMyData(path, partitionStart, partitionLength)
        dataSources->set(i, new DataSource(code));
    }
    return dataSources;
}
```

# 7. 如何在插件代码中构造并使用 sql 语句

DolphinDB 的脚本语言中提供了两个用于构造 SQL 语句的函数：`sql` 函数和 `parseExpr` 函数。这两个函数都能够在插件代码中构造 SQL 或在插件代码中更灵活地使用 SQL 语句。本章以 `parseExpr` 函数为例介绍如何在插件代码中使用 SQL 语句。

## 7.1 使用步骤

### 7.1.1 引入 *ScalarImp.h* 头文件

通过 `parseExpr` 函数生成 SQL 语句时，解析执行的过程中需要用到 String 类型，而 String 类型是 DolphinDB 内置的一个 Scalar 类型，其类定义在插件库中 *ScalarImp.h* 这个头文件。因此， 需要先引入该头文件：

```
#include "ScalarImp.h"
```

### 7.1.2 将待查询的 Table 对象放入 Heap 中

插件中定义的函数第一个参数是 heap 对象，当通过脚本调用插件中的接口时能获取到这个对象。通过 heap 对象的 `addItem` 接口可以将 table 对象放入 heap 中维护。`addItem` 接口有两个参数：第一个参数为对象的名字，需要设置为 SQL 查询语句中 from 关键字后跟随的字符串；第二个参数为 table 对象。

在以下例子中，首先通过 `heap->addItem(“t“, t)` 构造一个名为 "t"的 table 对象 t：

```
vector<string> colNames {"id", "x"};
vector<DATA_TYPE> colTypes {DT_SYMBOL, DT_DOUBLE};
TableSP t = Util::createTable(colNames, colTypes, 0, 8);
heap->addItem("t", t);
```

之后就可以在以下这个 SQL 语句中使用字符串 ”t” 指代被查询的 table：

```
select * from t;
```

### 7.1.3 拼接 sql 字符串

接下来，我们可以将执行 `select * from t` 的结果赋予名为 sql 的字符串，其中，字符串 "t" 用于在以下的例子中指代上一节提到的 table t：

代码示例:

```
string sql = "select * from t"
```

### 7.1.4 执行 sql

执行 sql 分为两步：

1. 通过parseExpr函数将sql语句解析为元代码。即，在插件代码中，通过 `heap->currentSession()->getFunctionDef("parseExpr")` 获取函数对象。
2. 通过eval函数执行解析后的元代码。即，将参数的参数组织为 `vector<ConstantSP>` 的形式用于调用。

执行 sql 的示例如下：

```
string sql = "select * from t";
ConstantSP sqlArg =  new String(DolphinString(sql));
vector<ConstantSP> args{sqlArg};
ObjectSP sqlObj = heap->currentSession()->getFunctionDef("parseExpr")->call(heap, args);
vector<ConstantSP> evalArgs{sqlObj};
ConstantSP ret = heap->currentSession()->getFunctionDef("eval")->call(heap, evalArgs);
```

## 7.2 完整代码示例

### 7.2.1 `select * from t` 的完整代码示例

```
vector<string> colNames {"id", "x"};
vector<DATA_TYPE> colTypes {DT_SYMBOL, DT_DOUBLE};
TableSP t = Util::createTable(colNames, colTypes, 0, 8);
ConstantSP idData = Util::createVector(DT_SYMBOL, 0, 0);
ConstantSP xData = Util::createVector(DT_DOUBLE, 0, 0);
string testId("APPL");
double testX(100.1);
((Vector*)(idData.get()))->appendString(&testId, 1);
((Vector*)(xData.get()))->appendDouble(&testX, 1);
vector<ConstantSP> data = {idData, xData};
INDEX rows=0;
string errMsg;
t->append(data, rows, errMsg);
heap->addItem("t", t);
string strData = t->getString();
string sql = "select * from t";
ConstantSP sqlArg =  new String(DolphinString(sql));
vector<ConstantSP> args{sqlArg};
ObjectSP sqlObj = heap->currentSession()->getFunctionDef("parseExpr")->call(heap, args);
vector<ConstantSP> evalArgs{sqlObj};
ConstantSP ret = heap->currentSession()->getFunctionDef("eval")->call(heap, evalArgs);
```

### 7.2.2 `select avg(x) from t` 的完整代码示例

```
vector<string> colNames {"id", "x"};
vector<DATA_TYPE> colTypes {DT_SYMBOL, DT_DOUBLE};
TableSP t = Util::createTable(colNames, colTypes, 0, 8);
ConstantSP idData = Util::createVector(DT_SYMBOL, 0, 0);
ConstantSP xData = Util::createVector(DT_DOUBLE, 0, 0);
string testId("APPL");
double testX(100.1);
((Vector*)(idData.get()))->appendString(&testId, 1);
((Vector*)(xData.get()))->appendDouble(&testX, 1);
vector<ConstantSP> data = {idData, xData};
INDEX rows=0;
string errMsg;
t->append(data, rows, errMsg);
heap->addItem("t", t);
string strData = t->getString();
string sql = "select avg(x) from t";
ConstantSP sqlArg =  new String(DolphinString(sql));
vector<ConstantSP> args{sqlArg};
ObjectSP sqlObj = heap->currentSession()->getFunctionDef("parseExpr")->call(heap, args);
vector<ConstantSP> evalArgs{sqlObj};
ConstantSP ret = heap->currentSession()->getFunctionDef("eval")->call(heap, evalArgs);
```

# 8. 常见问题

## 8.1 如何处理开发的 windows 版本插件加载时的错误提示："The specified module could not be found"？

MinGW 中包含 gcc, g++ 等多种编译器，下载时请选择 x86_64-posix-seh 版本（posix 表示启用了 C++ 11 多线程特性，seh 表示异常分支处理零开销），以与 DolphinDB server 保持一致。若下载安装了 x86_64-posix-sjlj 或其他版本，某些插件能编译成功，但会加载失败，提示：The specified module could not be found。

## 8.2 插件开发时需要包含哪些库和头文件？

DolphinDB 插件代码存储于 github/gitee 的 dolphindb/DolphinDBPlugin，其中的 include 目录包含了 DolphinDB 的核心数据结构的类声明和部分工具类声明。这些类是实现插件的重要基础工具，开发插件时需要包含 include 目录下的头文件。

链接时，需要包含库目录（libDolphinDB.dll/libDolphinDB.so 所在目录），即安装 DolphinDB 的目录。

## 8.3 编译时需要包含哪些选项？

windows 版本要添加 “WINDOWS”，Linux 版本要添加 “LINUX”。对 release130 及以上分支，添加选项 "LOCKFREE_SYMBASE"。另外，为了兼容旧版本的编译器，libDolphinDB.so 编译时使用了 _GLIBCXX_USE_CXX11_ABI=0 的选项，因此用户在编译插件时也应该加入该选项。若 libDolphinDB.so 编译时使用 ABI=1，编译插件时则无需添加 _GLIBCXX_USE_CXX11_ABI=0 的选项。

编译步骤可参考已实现的插件案例，例如 NSQ 插件的 [CMakeList.txt]([https://github.com/dolphindb/Tutorials_CN/blob/master/plugin/Msum/CMakeLists.txt)。

## 8.4 如何处理编译时出现包含 std::__cxx11 字样的链接问题（undefined reference）？

请检查用于编译插件的 gcc 版本，建议其和编译 DolphinDB server 的 gcc 版本保持一致。例如普通的 Linux64 版本用 gcc 4.8.5 版本，jit 版本使用 gcc 6.2.0 版本。

## 8.5 如何加载插件，可以卸载后重新加载吗？

插件的加载方式有 2 种：第 1 种，使用 loadPlugin 函数加载插件。该函数接受一个描述插件格式的文件的路径, 例如：
```cpp
loadPlugin("/<YOUR_SERVER_PATH>/plugins/odbc/PluginODBC.txt");
```
> 注意：格式文件介绍详见插件 [插件格式](https://github.com/dolphindb/DolphinDBPlugin/blob/master/README_CN.md#加载插件), 其中文件第一行规定了 lib 文件名以及路径。缺省不写路径，即需要插件库与格式文件在同一个目录。

第 2 种，DolphinDB Server 1.20.0 及以上版本，可以通过 preloadModules 参数来自动加载。使用这个方法时需要保证预先加载的插件存在，否则 server 启动时会有异常。多个插件用逗号分离。例如:
```
preloadModules=plugins::mysql,plugins::odbc
```
已加载的插件不能卸载。重新加载需要重启节点。

## 8.6 如何处理执行插件函数时的报错信息："Connnection refused：connect" 或节点 crash 问题？

确保 include 下的头文件和 libDolphinDB.so 或 libDolphinDB.dll 实现保持一致。插件分支应与 DolphinDB Server 的版本相匹配，即若 DolphinDB Server 是 1.30 版本，插件应用 release130 分支，若 DolphinDB Server 是 2.00 版本，插件应该用 release200 分支，其他版本依此类推。

确保用于编译插件的 gcc 版本和编译 libDolphinDB.so 或 libDolphinDB.dll 的版本保持一致，以免出现不同版本的编译器 ABI 不兼容的问题。

插件与 DolphinDB server 在同一个进程中运行，若插件 crash，那整个系统就会 crash。因此在开发插件时要注意完善错误检测机制，除了插件函数所在线程可以抛出异常（server 在调用插件函数时会俘获异常），其他线程都必须自己俘获异常，并不得抛出异常。

确保编译选项中已经添加宏 LOCKFREE_SYMBASE。

## 8.7 如何处理执行插件函数时的错误提示："Cannot recognize the token xxx"？

使用前需引入插件的命名空间，例如：
```cpp
use demo;
```
或者函数前加上模块名称，例如：
```cpp
demo::f1();
```

# 9. 附件

- [插件的完整代码](https://github.com/dolphindb/Tutorials_CN/tree/master/plugin)

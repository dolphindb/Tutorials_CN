# DolphinDB 通用计算

DolphinDB database不仅可以分布式地存储数据，而且对分布式计算有良好支持。在DolphinDB中，用户可以用系统提供的通用分布式计算框架，通过脚本实现高效的分布式算法，而不需关注具体的底层实现。本文将对DolphinDB通用计算框架中的重要概念和相关函数作出详细解释，并提供丰富的具体使用场景和例子。

- [DolphinDB 通用计算](#dolphindb-通用计算)
  - [1. 数据源](#1-数据源)
  - [2. Map-Reduce框架](#2-map-reduce框架)
    - [2.1. `mr`函数](#21-mr函数)
    - [2.2. `imr`函数](#22-imr函数)
  - [3. 数据源相关函数](#3-数据源相关函数)
    - [3.1. `sqlDS`函数](#31-sqlds函数)
    - [3.2. `repartitionDS`函数](#32-repartitionds函数)
    - [3.3. `textChunkDS`函数](#33-textchunkds函数)
    - [3.4. 第三方数据源提供的数据源接口](#34-第三方数据源提供的数据源接口)
    - [3.5. 数据源缓存](#35-数据源缓存)
    - [3.6. 数据源转换](#36-数据源转换)

## 1. 数据源

数据源(data source)是DolphinDB的通用计算框架中的基本概念。它是一种特殊类型的数据对象，是对数据的元描述。通过执行数据源，用户可以获得诸如表、矩阵、向量等数据实体。在DolphinDB的分布式计算框架中，轻量级的数据源对象而不是庞大的数据实体被传输到远程节点，以用于后续的计算，这大大减少了网络流量。

在DolphinDB中，可使用`sqlDS`函数，基于一个SQL表达式产生数据源。这个函数并不直接对表进行查询，而是返回一个或多个SQL子查询的元语句，即数据源。之后，用户可以使用Map-Reduce框架，传入数据源和计算函数，将任务分发到每个数据源对应的节点，并行地完成计算，然后将结果汇总。

关于几种常用的获得数据源的方法，本文的3.1至3.4节中会详细介绍。

## 2. Map-Reduce框架

Map-Reduce函数是DolphinDB通用分布式计算框架的核心功能。

### 2.1. `mr`函数

DolphinDB的Map-Reduce函数`mr`的语法是 mr(ds, mapFunc, \[reduceFunc], \[finalFunc], \[parallel=true])，它可接受一组数据源和一个mapFunc函数作为参数。它会将计算任务分发到每个数据源所在的结点，通过mapFunc对每个数据源中的数据进行处理。可选参数reduceFunc会将mapFunc的返回值两两做计算，得到的结果再与第三个mapFunc的返回值计算，如此累积计算，将mapFunc的结果汇总。如果有M个map调用，reduce函数将被调用M-1次。可选参数finalFunc对reduceFunc的返回值做进一步处理。

官方手册中有一个通过`mr`执行分布式最小二乘线性回归的例子。本文通过以下例子，展示如何用一个`mr`调用实现对分布式表每个分区中的数据随机采样十分之一的功能：

```
// 创建数据库和DFS表
db = database("dfs://sampleDB", VALUE, `a`b`c`d)
t = db.createPartitionedTable(table(100000:0, `sym`val, [SYMBOL,DOUBLE]), `tb, `sym)
n = 3000000
t.append!(table(rand(`a`b`c`d, n) as sym, rand(100.0, n) as val))

// 定义map函数
def sampleMap(t) {
    sampleRate = 0.1
    rowNum = t.rows()
    sampleIndex = (0..(rowNum - 1)).shuffle()[0:int(rowNum * sampleRate)]
    return t[sampleIndex]
}

ds = sqlDS(<select * from t>)              // 创建数据源
res = mr(ds, sampleMap, , unionAll)        // 执行计算
```

在以上的例子中，用户自定义的sampleMap函数接受一个表（即数据源中的数据）作为参数，随机返回其中1/10的行。本例的`mr`函数没有reduceFunc参数，因此将各个map函数的返回值放在一个元组中，传给finalFunc，即`unionAll`。`unionAll`将map函数返回的多张表合并成一个顺序分区的分布式表。

### 2.2. `imr`函数

DolphinDB提供了基于Map-Reduce方法的迭代计算函数`imr`。相比`mr`，它能支持迭代计算，每次迭代使用上一次迭代的结果和输入数据集，因而能支持更多复杂算法的实现。迭代计算需要模型参数的初始值和终止标准。它的语法是 imr(ds, initValue, mapFunc, \[reduceFunc], \[finalFunc], terminateFunc, \[carryover=false])，其中initValue参数是第一次迭代的初值，mapFunc参数是一个函数，接受的参数包括数据源实体，和前一次迭代中最终函数的输出。对于第一次迭代，它是用户给出的初始值。`imr`的与`mr`函数中的类似。finalFunc函数接受两个参数，第一个参数是前一次迭代中最终函数的输出。对于第一次迭代，它是用户给出的初始值。第二个参数是调用reduce函数后的输出。terminateFunc参数用于判断迭代是否中止。它接受两个参数。第一个是前一次迭代中reduce函数的输出，第二个是当前迭代中reduce函数的输出。如果它返回true，迭代将会中止。carryover参数表示map函数调用是否生成一个传递给下一次map函数调用的对象。如果carryover为true，那么map函数有3个参数并且最后一个参数为携带的对象，同时map函数的输出结果是一个元组，最后一个元素为携带的对象。在第一次迭代中，携带的对象为NULL。

官方手册中有一个通过`imr`计算分布式数据的中位数的例子。本文将提供一个更加复杂的例子，即用牛顿法实现逻辑回归（Logistic Regression）的计算，展示`imr`在机器学习算法中的应用。

```
def myLrMap(t, lastFinal, yColName, xColNames, intercept) {
    placeholder, placeholder, theta = lastFinal
    if (intercept)
        x = matrix(t[xColNames], take(1.0, t.rows()))
    else
        x = matrix(t[xColNames])
    xt = x.transpose()
    y = t[yColName]
    scores = dot(x, theta)
    p = 1.0 \ (1.0 + exp(-scores))
    err = y - p
    w = p * (1.0 - p)
    logLik = (y * log(p) + (1.0 - y) * log(1.0 - p)).flatten().sum()
    grad = xt.dot(err)                   // 计算梯度向量
    wx = each(mul{w}, x)
    hessian = xt.dot(wx)                 // 计算Hessian矩阵
    return [logLik, grad, hessian]
}

def myLrFinal(lastFinal, reduceRes) {
    placeholder, placeholder, theta = lastFinal
    logLik, grad, hessian = reduceRes
    deltaTheta = solve(hessian, grad)    // deltaTheta等于hessian^-1 * grad，相当于解方程hessian * deltaTheta = grad
    return [logLik, grad, theta + deltaTheta]
}

def myLrTerm(prev, curr, tol) {
	placeholder, grad, placeholder = curr
	return grad.flatten().abs().max() <= tol
}

def myLr(ds, yColName, xColNames, intercept, initTheta, tol) {
    logLik, grad, theta = imr(ds, [0, 0, initTheta], myLrMap{, , yColName, xColNames, intercept}, +, myLrFinal, myLrTerm{, , tol})
    return theta
}
```

在上述例子中，map函数为数据源中的数据计算在当前的系数下的梯度向量和Hessian矩阵；reduce函数将map的结果相加，相当于求出整个数据集的梯度向量和Hessian矩阵；final函数通过最终的梯度向量和Hessian矩阵对系数进行优化，完成一轮迭代；terminate函数的判断标准是本轮迭代中梯度向量中最大分量的绝对值是否大于参数tol。

这个例子还可以通过数据源转换操作，进一步优化以提高性能，具体参见后续*数据源转换*小节。

作为经常使用的分析工具，分布式逻辑回归在DolphinDB中作为内置函数`logisticRegression`实现，并提供更多功能。

## 3. 数据源相关函数

DolphinDB提供了以下常用的方法获取数据源：

### 3.1. `sqlDS`函数

`sqlDS`函数根据输入的SQL元代码创建一个数据源列表。 如果SQL查询中的数据表有n个分区，`sqlDS`会生成n个数据源。 如果SQL查询不包含任何分区表，`sqlDS`将返回只包含一个数据源的元组。

`sqlDS`是将SQL表达式转换成数据源的高效方法。用户只需要提供SQL表达式，而不需要关注具体的数据分布，就能利用返回的数据源执行分布式算法。下面提供的例子，展示了利用`sqlDS`对DFS表中的数据执行`olsEx`分布式最小二乘回归的方法。

```
// 创建数据库和DFS表
db = database("dfs://olsDB", VALUE, `a`b`c`d)
t = db.createPartitionedTable(table(100000:0, `sym`x`y, [SYMBOL,DOUBLE,DOUBLE]), `tb, `sym)
n = 3000000
t.append!(table(rand(`a`b`c`d, n) as sym, 1..n + norm(0.0, 1.0, n) as x, 1..n + norm(0.0, 1.0, n) as y))

ds = sqlDS(<select x, y from t>)    // 创建数据源
olsEx(ds, `y, `x)                   // 执行计算
```

### 3.2. `repartitionDS`函数

`sqlDS`的数据源是系统自动根据数据的分区而生成的。有时用户需要对数据源做一些限制，例如，在获取数据时，重新指定数据的分区以减少计算量，或者，只需要一部分分区的数据。`repartitionDS`函数就提供了重新划分数据源的功能。

函数`repartitionDS`根据输入的SQL元代码和列名、分区类型、分区方案等，为元代码生成经过重新分区的新数据源。

以下代码提供了一个`repartitionDS`的例子。在这个例子中，DFS表t中有字段deviceId, time, temperature，分别为symbol, datetime和double类型，数据库采用双层分区，第一层对time按VALUE分区，一天一个分区；第二层对deviceId按HASH分成20个区。

现需要按deviceId字段聚合查询95百分位的temperature。如果直接写查询`select percentile(temperature, 95) from t group by deviceId`，由于`percentile`函数没有Map-Reduce实现，这个查询将无法完成。

一个方案是将所需字段全部加载到本地，计算95百分位，但当数据量过大时，计算资源可能不足。`repartitionDS`提供了一个解决方案：将表基于deviceId按其原有分区方案HASH重新分区，每个新的分区对应原始表中一个HASH分区的所有数据。通过`mr`函数在每个新的分区中计算95百分位的temperature，最后将结果合并汇总。

```
// 创建数据库
deviceId = "device" + string(1..100000) 
db1 = database("", VALUE, 2019.06.01..2019.06.30) 
db2 = database("", HASH, SYMBOL:20) 
db = database("dfs://repartitionExample", COMPO, [db1, db2]) 

// 创建DFS表
t = db.createPartitionedTable(table(100000:0, `deviceId`time`temperature, [SYMBOL,DATETIME,DOUBLE]), `tb, `time`deviceId)
n = 3000000
t.append!(table(rand(deviceId, n) as deviceId, 2019.06.01T00:00:00 + rand(86400 * 10, n) as time, 60 + norm(0.0, 5.0, n) as temperature))

// 重新分区
ds = repartitionDS(<select deviceId, temperature from t>, `deviceId)
// 执行计算
res = mr(ds, def(t) { return select percentile(temperature, 95) from t group by deviceId}, , unionAll{, false})
```

这个计算的结果正确性能够保证，因为`repartitionDS`产生的新分区基于deviceId的原有分区，能确保其中各个数据源的deviceId两两不重合，因此只需要将各分区计算结果合并就能取得正确结果。

### 3.3. `textChunkDS`函数

`textChunkDS`函数可以将一个文本文件分成若干个数据源，以便对一个文本文件所表示的数据执行分布式计算。它的语法是：textChunkDS(filename, chunkSize, \[delimiter=','], \[schema])。其中，filename, delimiter, schema这些参数与`loadText`函数的参数相同。而chunkSize参数表示每个数据源中数据的大小，单位为MB，可以取1到2047的整数。

以下例子是官方手册中`olsEx`例子的另一种实现。它通过`textChunkDS`函数从文本文件中生成若干数据源，每个数据源的大小为100MB，对生成的数据源经过转换后，执行`olsEx`函数，计算最小二乘参数：

```
ds = textChunkDS("c:/DolphinDB/Data/USPrices.csv", 100)
ds.transDS!(USPrices -> select VOL\SHROUT as VS, abs(RET) as ABS_RET, RET, log(SHROUT*(BID+ASK)\2) as SBA from USPrices where VOL>0)
rs=olsEx(ds, `VS, `ABS_RET`SBA, true, 2)
```

其中的数据源转换操作`transDS!`，可以参考后续*数据源转换*小节。

### 3.4. 第三方数据源提供的数据源接口

一些加载第三方数据的插件，例如HDF5，提供了产生数据源的接口。用户可以直接对它们返回的数据源执行分布式算法，而无需先将第三方数据导入内存或保存为分布式表。

DolphinDB的HDF5插件提供了`hdf5DS`函数，用户可以通过设置其dsNum参数，指定需要生成的数据源个数。以下例子从HDF5文件中生成10个数据源，并通过Map-Reduce框架对结果的第1列求样本方差：

```
ds = hdf5::hdf5DS("large_file.h5", "large_table", , 10)

def varMap(t) {
    column = t.col(0)
    return [column.sum(), column.sum2(), column.count()]
}

def varFinal(result) {
    sum, sum2, count = result
    mu = sum \ count
    populationVar = sum2 \ count - mu * mu
    sampleVar = populationVar * count \ (count - 1)
    return sampleVar
}

sampleVar = mr(ds, varMap, +, varFinal)
```

### 3.5. 数据源缓存

数据源可以有0,1或多个位置。位置为0的数据源是本地数据源。 在多个位置的情况下，这些位置互为备份。系统会随机选择一个位置执行分布式计算。当数据源被指示缓存数据对象时，系统会选择我们上次成功检索数据的位置。

用户可以指示系统对数据源进行缓存或清理缓存。对于迭代计算算法（例如机器学习算法），数据缓存可以大大提高计算性能。当系统内存不足时，缓存数据将被清除。如果发生这种情况，系统可以恢复数据，因为数据源包含所有元描述和数据转换函数。

和数据源缓存相关的函数有：

- `cacheDS!`：指示系统缓存数据源
- `cacheDSNow`：立即执行并缓存数据源，并返回缓存行的总数

### 3.6. 数据源转换

一个数据源对象还可以包含多个数据转换函数，用以进一步处理所检索到的数据。系统会依次执行这些数据转换函数，一个函数的输出作为下一个函数的输入（和唯一的输入）。

将数据转换函数包含在数据源中，通常比在核心计算操作（即map函数）中对数据源进行转换更有效。如果检索到的数据仅需要一次计算时，没有性能差异，但它对于具有缓存数据对象的数据源的迭代计算会造成巨大的差异。如果转换操作在核心计算操作中，则每次迭代都需要执行转换；如果转换操作在数据源中，则它们只被执行一次。`transDS!`函数提供了转换数据源的功能。

例如，执行迭代机器学习函数`randomForestRegressor`之前，用户可能需要手动填充数据的缺失值（当然，DolphinDB的随机森林算法已经内置了缺失值处理）。此时，可以用`transDS!`对数据源进行如下处理：对每一个特征列，用该列的平均值填充缺失值。假设表中的列x0, x1, x2, x3为自变量，列y为因变量，以下是实现方法：

```
ds = sqlDS(<select x0, x1, x2, x3, y from t>)
ds.transDS!(def (mutable t) {
    update t set x0 = nullFill(x0, avg(x0)), x1 = nullFill(x1, avg(x1)), x2 = nullFill(x2, avg(x2)), x3 = nullFill(x3, avg(x3))
    return t
})

randomForestRegressor(ds, `y, `x0`x1`x2`x3)
```

另一个转换数据源的例子是2.2节提到的逻辑回归的脚本实现。在2.2节的实现中，map函数调用中包含了从数据源的表中取出对应列，转换成矩阵的操作，这意味着每一轮迭代都会发生这些操作。而实际上，每轮迭代都会使用同样的输入矩阵，这个转换步骤只需要调用一次。因此，可以用`transDS!`将数据源转换成一个包含x, xt和y矩阵的三元组：

```
def myLrTrans(t, yColName, xColNames, intercept) {
    if (intercept)
        x = matrix(t[xColNames], take(1.0, t.rows()))
    else
        x = matrix(t[xColNames])
    xt = x.transpose()
    y = t[yColName]
    return [x, xt, y]
}

def myLrMap(input, lastFinal) {
    x, xt, y = input
    placeholder, placeholder, theta = lastFinal
    // 之后的计算和2.2节相同
}

// myLrFinal和myLrTerm函数和2.2节相同

def myLr(mutable ds, yColName, xColNames, intercept, initTheta, tol) {
    ds.transDS!(myLrTrans{, yColName, xColNames, intercept})
    logLik, grad, theta = imr(ds, [0, 0, initTheta], myLrMap, +, myLrFinal, myLrTerm{, , tol})
    return theta
}
```

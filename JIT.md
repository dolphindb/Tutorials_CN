# DolphinDB JIT教程

DolphinDB从1.01版本开始支持JIT，本篇教程将结合实际例子介绍JIT的使用和注意事项。

## 1 什么是JIT

即时编译(英文: Just-in-time compilation, 缩写: JIT)，又译及时编译、实时编译，动态编译的一种形式，是一种提高程序运行效率的方法。
通常程序有两种运行方式：编译执行和解释执行。编译执行在程序执行前全部翻译为机器码，特点是运行效率较高，C/C++就是代表。
而解释执行是一遍运行一边翻译，灵活性较强，但是通常执行效率较低，Python是代表语言。

即时编译融合了两者的优点，在运行时将代码翻译为机器码，可以达到与静态编译语言相近的执行效率，Python的第三方实现PyPy通过JIT明显改善了解释器的性能，
绝大多数的Java实现都依赖JIT以提高代码的运行效率。

## 2 为什么DolphinDB需要JIT

DolphinDB的脚本也是一种解释执行的语言，运行脚本时先对文本进行语法分析生成语法树，然后递归执行，在不能使用向量化的情况下，解释成本会比较高。
这是由于DolphinDB底层由C++实现，一次脚本中函数调用最后会变成很多次C++内的虚拟函数调用。
这个过程十分耗时，在一些场景下无法满足实时性的需求，如高频因子的计算、流数据实时处理等场景。下面举一个例子说明：

``` 
def sum_without_jit(n) {
  s = 0l
  i = 1
  do {
    s += i
    i += 1
  } while(i <= n)
  return s
}

@jit
def sum_with_jit(n) {
  s = 0l
  i = 1
  do {
    s += i
    i += 1
  } while(i <= n)
  return s
}

timer(100) sum_without_jit(1000000) //  67199.524 ms
timer(100) sum_with_jit(1000000)    //    217.618 ms
```

在上面的例子中，我们对比了使用和不使用jit的情况下，计算1到1000000之和100次需要的时间，可以看到不使用jit的时间是使用的308倍。

<!-- 向量化有点难 -->

上面的例子我们可以不用循环，直接使用DolphinDB内置的函数进行运算，运行时间类似。但是实际应用中，如高频因子生成，把循环计算转化为向量化运算需要一定的技巧。

在[知乎上的一篇专栏](https://zhuanlan.zhihu.com/p/77988657)中，我们展示了如何使用在DolphinDB中使用向量化运算，其中计算买卖信号的式子如下：

``` 
direction = (iif(signal >t1, 1h, iif(signal < t10, 0h, 00h)) - iif(signal <t2, 1h, iif(signal > t20, 0h, 00h))).ffill().nullFill(0h)
```

对于初学DolphinDB的人来说，要写出这样的计算是有一定的难度的。如果我们使用for循环改写，那么会是这样：

``` 
@jit
def calculate_with_jit(signal, n, t1, t10, t20, t2) {
  cur = 0
  idx = 0
  output = array(INT, n, n)
  for (s in signal) {
    if(s > t1) {           // (t1, inf)
      cur = 1
    } else if(s >= t10) {  // [t10, t1]
      if(cur == -1) cur = 0
    } else if(s > t20) {   // [t20, t10)
      cur = 0
    } else if(s >= t2) {   // [t2, t20]
      if(cur == 1) cur = 0
    } else {               // (-inf, t2)
      cur = -1
    }
    output[idx] = cur
    idx += 1
  }
  return output
}
```

上面的式子相对而言就容易地多，我们把@jit去掉得到不使用jit的计算函数calculate_without_jit, 然后对比三种方法的运行时间：

``` 
n = 10000000
t1= 60
t10 = 50
t20 = 30
t2 = 20
signal = rand(100.0, n)

timer(100) (iif(signal >t1, 1h, iif(signal < t10, 0h, 00h)) - iif(signal <t2, 1h, iif(signal > t20, 0h, 00h))).ffill().nullFill(0h) // 35907.611 ms
timer(100) calculate_with_jit(calculate, signal, size(signal), t1, t10, t20, t2)       //    16683.7 ms
timer(100) calculate_without_jit(signal, size(signal), t1, t10, t20, t2)               //  1069923.8 ms
```

运行结果表明，使用JIT运行速度是向量化运算的2.15倍，是不用JIT的64倍。这里JIT的运行速度比向量化还快，是因为向量化运行中调用了很多次DolphinDB的内置函数，产生了很多中间结果，
涉及到很多次内存分配以及虚拟函数调用，而JIT生成的代码则没有这些额外的开销。

这样一来，在JIT的帮助下，不用向量化我们一样可以高效处理数据。

<!-- 无法向量化 -->
另外一种情况是，某些计算无法进行向量化，比如计算ImpliedVolatility时，需要使用牛顿法，无法向量化，这种情况下如果还要满足一定的实时性，没有jit情况下的解决方案就是使用DolphinDB的[插件](https://github.com/dolphindb/DolphinDBPlugin)。

## 3 如何在DolphinDB中使用JIT

### 3.1 使用方法

DolphinDB目前仅支持对用户自定义函数进行JIT。

在DolphinDB中使用JIT非常简单，只需要定义一个函数，在函数上方加上 `@jit` 的标识即可：

``` 
@jit
def myFunc(/* arguments */) {
  /* implementation */
}
```

定义完成以后，用户在调用时，DolphinDB会根据函数接受的参数，将函数的代码实时编译为机器码后执行。

### 3.2 支持的语句

目前DolphinDB支持在JIT中使用以下几种语句：

赋值语句，比如：

``` 
@jit
def func() {
  y = 1
}
```

注意，multi assign目前是不支持的，比如：

``` 
@jit
def func() {
  a, b = 1, 2
}
func()
```

运行以上语句会抛出异常。

return语句，比如：

``` 
@jit
def func() {
  return 1
}
```

if-else语句，比如：

``` 
@jit
def myAbs(x) {
  if(x > 0) return x
  else return -x
}
```

do-while语句，比如：

``` 
@jit
def mySqrt(x) {
    diff = 0.0000001
    guess = 1.0
    guess = (x / guess + guess) / 2.0
    do {
        guess = (x / guess + guess) / 2.0
    } while(abs(guess * guess - x) >= diff)
    return guess
}
```

for语句，比如：

``` 
@jit
def mySum(vec) {
  s = 0
  for(i in vec) {
    s += i
  }
  return s
}
```

同时，以上语句的任意嵌套都是支持的。

### 3.3 支持的函数和运算符

目前DolphinDB支持在JIT函数中使用以下的数学函数： exp, log, sin, asin, cos, acos, tan, atan, abs, ceil, floor, sqrt。以上数学函数在JIT中出现时，
如果接受的参数为scalar，那么在最后生成的机器码中会调用glibc中对应的函数或者经过优化的c实现的函数；如果接收的参数为array，那么最后会调用DolphinDB
提供的数学函数。这样的好处是通过直接调用c实现的代码提升函数运行效率，减少不必要的虚拟函数调用和内存分配。

<!-- add, sub, multi, div, bitor, bitand, bitxor, seq, eq, neq, lt, le, gt, ge, neg, at, mod -->
JIT支持以下运算符：add(+), sub(-), multiply(*), divide(/), and(&&), or(||), bitand(&), bitor(|), bitxor(^), eq(==), neq(!=), ge(>=), gt(>), le(<=), lt(<), neg(-), mod(%), seq(..), at([])，以上运算在所有类型下的表现都与非jit的实现一致。

JIT支持以下DolphinDB原生函数：take, array, size，isValid, rand，cdfNormal。以后的版本中还会加入更多的原生函数。

需要注意，array函数的第一个参数必须写明，这是由于JIT编译时必须知道所有变量的类型，array返回结果的类型由第一个参数的int值确定，因此编译时必须已知这个值。

### 3.4 空值的处理

DolphinDB中每个类型都用这个类型的最小值表示该类型的空值，JIT生成的代码也考虑了空值的处理，所有的函数和运算符处理空值的方法都与原生函数和运算符一致，因此用户不需要额外考虑这个问题。

### 3.5 JIT函数之间的相互调用

DolphinDB的JIT函数支持相互调用，比如：

``` 
@jit
def myfunc1(x) {
  return sqrt(x) + exp(x)
}

@jit
def myfunc2(x) {
  return myfunc1(x)
}

myfunc2(1.5)
```

在上面的例子中，内部会先编译myfunc1, 生成一个签名为 `double myfunc1(double)` 的native函数， myfunc2生成的机器码中直接调用这个函数，而不是在运行时判断myfunc1是否为JIT函数后再执行，从而达到最高的执行效率。

注意，JIT函数内不可以调用非JIT的用户自定义函数，因为这样无法进行类型推导，关于类型推导下面会提到。

### 3.6 JIT的编译成本以及缓存机制

DolphinDB的JIT底层依赖[LLVM](https://llvm.org/)实现，每个udf在编译时都会生成自己的module，相互独立。编译主要包含以下几个部分：

1. LLVM相关变量和环境的初始化
2. 根据DolphinDB脚本的语法树生成LLVM的IR
3. 调用LLVM优化第二步生成的IR，然后编译为机器码

以上步骤中第一步耗时一般在5ms以内，后面两步的耗时与实际脚本的复杂度成正比，总体而言编译耗时基本上在50ms以内。

DolphinDB内部会对JIT函数编译的结果进行缓存，基本逻辑是这样的：用户调用一个JIT函数时，会提供若干个参数，内部根据这些参数的类型得到一个对应的字符串，然后在一个哈希表中寻找
这个字符串对应的编译结果，如果存在则直接调用；如果不存在，则开始编译，将编译结果保存到哈希表中，然后继续执行。

因此，对于一个JIT函数以及一个参数类型组合，DolphinDB内部只会编译一次。

### 3.7 DolphinDB JIT的局限

目前JIT可以使用的场景还比较有限，

1. 只支持用户自定义函数的JIT
2. 只接受scalar和array类型的参数，另外的类型如table，dict，pair, string, symbol等暂不支持。
3. 不接受subarray作为参数，这是由于目前内部实现的方法所限

## 4 DolphinDB JIT中的类型推导

在使用LLVM生成IR之前，必须知道脚本中所有变量的类型，这个步骤就是类型推导。DolphinDB的JIT实现使用的是局部推导，比如：

``` 
@jit
def foo() {
  x = 1
  y = 1.1
  z = x + y
  return z
}
```

通过 `x = 1` 知道x的类型是int；通过 `y = 1.1` 知道y的类型是 `double` ；通过 `z = x + y` ，以及上面推得的x和y的类型，知道z的类型也是double；
通过 `return z` 知道foo函数的返回类型是double。

如果函数有输入的话，比如：

``` 
@jit
def foo(x) {
  return x + 1
}
```

这个时候，foo函数的返回类型就依赖于输入值x的类型。

上面我们提到了目前JIT支持的变量类型，如果函数内部出现了不支持的类型，或者输入的变量类型不支持，那么就会导致整个函数的变量推导失败，在运行时会抛出异常，比如：

``` 
@jit
def foo(x) {
  return x + 1
}

foo(123)             // 正常执行
foo("abc")           // 抛出异常，因为目前不支持string类型
foo(1:2)             // 抛出异常，因为目前不支持pair类型
foo((1 2, 3 4, 5 6)) // 抛出异常，因为目前不支持tuple类型

@jit
def foo(x) {
  y = cumprod(x)
  z = y + 1
  return z
}

foo(1..10)             // 抛出异常，因为目前还没有支持cumprod函数，不知道该函数返回的类型，导致类型推导失败
```

因此，为了能够正常使用JIT函数，用户应该避免在函数内或者参数中使用诸如tuple，string等还未支持的类型，不要使用尚不支持类型推导的函数。

## 5 实际使用的例子

下面我们举几个实际使用的例子。

### 5.1 计算 ImpliedVolatility

上面提到过某些函数无法进行向量化，计算ImpliedVolatility就是一个例子：

``` 
@jit
def GBlackScholes(future_price, strike, input_ttm, risk_rate, b_rate, input_vol, is_call) {
  ttm = input_ttm + 0.000000000000001;
  vol = input_vol + 0.000000000000001;

  d1 = (log(future_price/strike) + (b_rate + vol*vol/2) * ttm) / (vol * sqrt(ttm));
  d2 = d1 - vol * sqrt(ttm);

  if (is_call) {
    return future_price * exp((b_rate - risk_rate) * ttm) * cdfNormal(0, 1, d1) - strike * exp(-risk_rate*ttm) * cdfNormal(0, 1, d2);
  } else {
    return strike * exp(-risk_rate*ttm) * cdfNormal(0, 1, -d2) - future_price * exp((b_rate - risk_rate) * ttm) * cdfNormal(0, 1, -d1);
  }
}

@jit
def ImpliedVolatility(future_price, strike, ttm, risk_rate, b_rate, option_price, is_call) {
  high=5.0;
  low = 0.0;

  do {
    if (GBlackScholes(future_price, strike, ttm, risk_rate, b_rate, (high+low)/2, is_call) > option_price) {
      high = (high+low)/2;
    } else {
      low = (high + low) /2;
    }
  } while ((high-low) > 0.00001);

  return (high + low) /2;
}

@jit
def test_jit(future_price, strike, ttm, risk_rate, b_rate, option_price, is_call) {
	n = size(future_price)
	ret = array(DOUBLE, n, n)
	i = 0
	do {
		ret[i] = ImpliedVolatility(future_price[i], strike[i], ttm[i], risk_rate[i], b_rate[i], option_price[i], is_call[i])
		i += 1
	} while(i < n)
	return ret
}

n = 100000
future_price=take(rand(10.0,1)[0], n)
strike_price=take(rand(10.0,1)[0], n)
strike=take(rand(10.0,1)[0], n)
input_ttm=take(rand(10.0,1)[0], n)
risk_rate=take(rand(10.0,1)[0], n)
b_rate=take(rand(10.0,1)[0], n)
vol=take(rand(10.0,1)[0], n)
input_vol=take(rand(10.0,1)[0], n)
multi=take(rand(10.0,1)[0], n)
is_call=take(rand(10.0,1)[0], n)
ttm=take(rand(10.0,1)[0], n)
option_price=take(rand(10.0,1)[0], n)

timer(10) test_jit(future_price, strike, ttm, risk_rate, b_rate, option_price, is_call)          //  21076.562 ms
timer(10) test_non_jit(future_price, strike, ttm, risk_rate, b_rate, option_price, is_call)      //   127262.615 ms

```

上面的例子中使用了两个JIT函数，其中ImpliedVolatility会调用GBlackScholes函数。我们把@jit去掉比较运行以下运行时间，JIT版本运行速度是非JIT版本的6倍，这里快的不多是因为二分法收敛的比较快，do-while循环调用的次数较少，
因此非JIT版本的劣势略微不明显一些。

### 5.2 计算 Stoploss

在这篇[知乎专栏](https://zhuanlan.zhihu.com/p/47236676)上，我们展示了如何使用DolphinDB进行技术信号回测，下面我们用JIT来实现其中的stoploss函数：

``` 
@jit
def stoploss(ret, threshold) {
	n = ret.size()
	i = 0
	curRet = 1.0
	curMaxRet = 1.0
	indicator = take(true, n)

	do {
		indicator[i] = false
		curRet *= (1 + ret[i])
		if(curRet > curMaxRet) { curMaxRet = curRet }
		drawDown = 1 - curRet / curMaxRet;
		if(drawDown >= threshold) {
			i = n // break is not supported for now
		}
		i += 1
	} while(i < n)

	return indicator
}

def stoploss2(ret, threshold){
	cumret = cumprod(1+ret)
 	drawDown = 1 - cumret / cumret.cummax()
	firstCutIndex = at(drawDown >= threshold).first() + 1
	indicator = take(false, ret.size())
	if(isValid(firstCutIndex) and firstCutIndex < ret.size())
		indicator[firstCutIndex:] = true
	return indicator
}
ret = rand(0.2,1000000) - 0.08
threshold = 0.20 // stop loss at 20%
timer(100) stoploss(ret, threshold)  // 30.441 ms
timer(100) stoploss2(ret, threshold) //  708.596 ms

```

stoploss这个函数实际上只需要找到drawdown大于threshold的第一天，不需要把cumprod和cummax全部计算出来，因此用JIT实现的版本比非JIT的向量化版本快了23倍左右。

## 6 Roadmap

在未来的版本中，我们计划逐步支持以下功能：

1. 在for, do-while语句中支持break和continue
2. 支持dictionary等数据结构，支持string等数据类型的原生操作。
3. 支持更多的数学和统计类函数
4. 增强类型推导功能。能够识别更多DolphinDB内置函数返回值的数据类型。
5. 支持在自定义函数中为输入参数，返回值和局部变量声明数据类型。

## 7 总结

为了解决金融数据中的高频因子计算、实时流数据处理问题中存在的实时性问题，DolphinDB推出了自定义函数即时编译执行的功能。
在一些原来必须向量化运算的问题上，使用简单的for循环，while循环和if-else等语句也能达到一样的效果，大大降低了从业人员的使用门槛。
而在一些本来就不可以向量化运算的问题上，这种优势则更加明显。因此，无论是在金融领域、工业物联网以及其他领域，DolphinDB都变得更加适用了。


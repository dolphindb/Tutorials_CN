# DolphinDB 即时编译（JIT）

DolphinDB从1.01版本开始支持JIT，本篇教程将结合实际例子介绍JIT的使用和注意事项。

- [DolphinDB 即时编译（JIT）](#dolphindb-即时编译jit)
  - [1. JIT简介](#1-jit简介)
  - [2. JIT在DolphinDB中的作用](#2-jit在dolphindb中的作用)
  - [3. 如何在DolphinDB中使用JIT](#3-如何在dolphindb中使用jit)
    - [3.1. 使用方法](#31-使用方法)
    - [3.2. 支持的语句](#32-支持的语句)
    - [3.3. 支持的运算符和函数](#33-支持的运算符和函数)
    - [3.4. 空值的处理](#34-空值的处理)
    - [3.5. JIT函数之间的调用](#35-jit函数之间的调用)
    - [3.6. JIT的编译成本以及缓存机制](#36-jit的编译成本以及缓存机制)
    - [3.7. 支持函数作为函数参数](#37-支持函数作为函数参数)
    - [3.8. 对矩阵的支持](#38-对矩阵的支持)
    - [3.9. 局限](#39-局限)
  - [4. 类型推导](#4-类型推导)
  - [5. 实例](#5-实例)
    - [5.1. 计算隐含波动率 (implied volatility)](#51-计算隐含波动率-implied-volatility)
    - [5.2. 计算Greeks](#52-计算greeks)
    - [5.3. 计算止损点 (stoploss)](#53-计算止损点-stoploss)
    - [5.4. 计算持仓成本](#54-计算持仓成本)
  - [6. 未来](#6-未来)
  - [7. 总结](#7-总结)

## 1. JIT简介

即时编译(英文: Just-in-time compilation, 缩写: JIT)，又译及时编译或实时编译，是动态编译的一种形式，可提高程序运行效率。

通常程序有两种运行方式：编译执行和解释执行。编译执行在程序执行前全部翻译为机器码，特点是运行效率较高，以C/C++为代表。解释执行是由解释器对程序逐句解释并执行，灵活性较强，但是执行效率较低，以Python为代表。

即时编译融合了两者的优点，在运行时将代码翻译为机器码，可以达到与静态编译语言相近的执行效率。Python的第三方实现PyPy通过JIT明显改善了解释器的性能。绝大多数的Java实现都依赖JIT以提高代码的运行效率。

## 2. JIT在DolphinDB中的作用

DolphinDB的编程语言是解释执行，运行程序时首先对程序进行语法分析生成语法树，然后递归执行。在不能使用向量化的情况下，解释成本会比较高。这是由于DolphinDB底层由C\++实现，脚本中的一次函数调用会转化为多次C\++内的虚拟函数调用。for循环，while循环和if-else等语句中，由于要反复调用函数，十分耗时，在某些场景下不能满足实时性的需求。

DolphinDB中的即时编译功能显著提高了for循环，while循环和if-else等语句的运行速度，特别适合于无法使用向量化运算但又对运行速度有极高要求的场景，例如高频因子计算、实时流数据处理等。

下面，我们使用一个最简单的例子，对比使用和不使用JIT的情况下，do-while循环计算1到1000000之和100次所需要的时间。

```
def sum_without_jit(v) {
  s = 0F
  i = 0
  n = size(v)
  do {
    s += v[i]
    i += 1
  } while(i < n)
  return s
}

@jit
def sum_with_jit(v) {
  s = 0F
  i = 0
  n = size(v)
  do {
    s += v[i]
    i += 1
  } while(i < n)
  return s
}

vec = 1..1000000

timer(100) sum_without_jit(vec)     //  91017 ms
timer(100) sum_with_jit(vec)        //    217 ms
```

不使用JIT的耗时是使用JIT的419倍。

请注意，以上例子仅是为了展示在do-while循环中JIT的性能优势。实际应用中，类似上例的简单循环计算，一般应当优先使用DolphinDB的内置函数进行向量化运算，这是由于很多内置函数采用了进一步的优化，而且使用内置函数更为方便。上例中，若使用 `sum` 函数，耗时是JIT的20%左右。一般来说，循环的操作与计算越复杂，JIT相对于使用内置函数的优势越大。



在[知乎上的一篇专栏](https://zhuanlan.zhihu.com/p/77988657)中，我们展示了如何使用在DolphinDB中使用向量化运算，其中计算交易信号的式子如下：

```
direction = (iif(signal>t1, 1h, iif(signal<t10, 0h, 00h)) - iif(signal<t2, 1h, iif(signal>t20, 0h, 00h))).ffill().nullFill(0h)
```

对于初学DolphinDB的人来说，需要了解 `iif` 函数才可写出以上语句。使用for循环改写以上语句则较为容易：

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

在上述脚本中把@jit去掉，并将函数名改为 `calculate_without_jit` ，以产生不使用JIT的自定义函数。对比三种方法的耗时：

```
n = 10000000
t1= 60
t10 = 50
t20 = 30
t2 = 20
signal = rand(100.0, n)

timer ffill!(iif(signal>t1, 1h, iif(signal<t10, 0h, 00h)) - iif(signal<t2, 1h, iif(signal>t20, 0h, 00h))).nullFill(0h) // 410.920 ms
timer calculate_with_jit(signal, size(signal), t1, t10, t20, t2)        //    170.7513 ms
timer calculate_without_jit(signal, size(signal), t1, t10, t20, t2)               //  14044.0641 ms
```

本例中，使用JIT的速度是向量化运算的2.4倍，是不用JIT的82倍。这里JIT的速度比向量化运算还要快，是因为向量化运算中调用了很多次DolphinDB的内置函数，产生了很多中间结果，
涉及到多次内存分配以及虚拟函数调用，而JIT生成的代码则没有这些额外的开销。

某些计算无法使用向量化，比如计算期权隐含波动率(implied volatility)时，需要使用牛顿法，无法使用向量化运算。这种情况下如果需要满足一定的实时性，可以选择使用DolphinDB的插件，亦可使用JIT。两者的区别在于，在任何场景下都可以使用插件，但是需要使用 C++ 编写，比较复杂；JIT的编写相对而言较为容易，但是适用的场景较为有限。JIT的运行速度与使用C++插件的速度非常接近。

## 3. 如何在DolphinDB中使用JIT

### 3.1. 使用方法

DolphinDB目前仅支持对用户自定义函数进行JIT。只需在函数定义之前的一行添加 @jit 的标识即可：

```
@jit
def myFunc(/* arguments */) {
  /* implementation */
}
```

用户在调用此函数时，DolphinDB会将函数的代码实时编译为机器码后执行。

### 3.2. 支持的语句

目前DolphinDB支持在JIT中使用以下几种语句：

* 赋值语句，例如：

```
@jit
def func() {
  y = 1
}
```

请注意，multiple assign目前是不支持的，例如：
@jit
def func() {
  a, b = 1, 2
}
func()
运行以上语句会抛出异常。


* return语句，例如：

```
@jit
def func() {
  return 1
}
```

* if-else语句，例如：

```
@jit
def myAbs(x) {
  if(x > 0) return x
  else return -x
}
```

* do-while语句，例如：

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

* for语句，例如：

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

* break和continue语句，例如：

```
@jit
def mySum(vec) {
  s = 0
  for (i in vec) {
    if(i % 2 == 0) continue
    s += i
  }
  return s
}
```

DolphinDB支持在JIT中以上语句的任意嵌套。

### 3.3. 支持的运算符和函数


目前DolphinDB支持在JIT中使用以下的运算符：add(+), sub(-), multiply(*), divide(/), and(&&), or(||), bitand(&), bitor(|), bitxor(^), eq(==), neq(!=), ge(>=), gt(>), le(<=), lt(<), neg(-), mod(%), seq(..), at(\[])，以上运算在所有数据类型下的实现都与非JIT的实现一致。

目前DolphinDB支持在JIT中使用以下的数学函数： `exp` , `log` , `sin` , `asin` , `cos` , `acos` , `tan` , `atan` , `abs` , `ceil` , `floor` , `sqrt`。以上数学函数在JIT中出现时，
如果接受的参数为scalar，那么在最后生成的机器码中会调用glibc中对应的函数或者经过优化的C实现的函数；如果接收的参数为array，那么最后会调用DolphinDB提供的数学函数。这样的好处是通过直接调用C实现的代码提升函数运行效率，减少不必要的虚拟函数调用和内存分配。


目前DolphinDB支持在JIT中使用以下的内置函数：`take`, `seq` , `array`, `size`, `isValid`, `rand`, `cdfNormal`, `cdfBeta`, `cdfBinomial`, `cdfChiSquare`, `cdfExp`, `cdfF`, `cdfGamma`, `cdfKolmogorov`, `cdfcdfLogistic`, `cdfNormal`, `cdfUniform`, `cdfWeibull`, `cdfZipf`, `invBeta`, `invBinomial`, `invChiSquare`, `invExp`, `invF`, `invGamma`, `invLogistic`, `invNormal`, `invPoisson`, `invStudent`, `invUniform`, `invWeibull`, `cbrt`, `deg2rad`, `rad2deg`, `det`, `dot`, `flatten`, `sum`, `avg`, `count`, `size`, `min`, `max`, `iif`, `round`。

需要注意，`array` 函数的第一个参数必须直接指定具体的数据类型，不能通过变量传递指定。这是由于JIT编译时必须知道所有变量的类型，而 `array` 函数返回结果的类型由第一个参数指定，因此编译时必须该值必须已知。
此外，`round` 函数在使用时必须指定第二个参数，且该参数须大于0。

目前DolphinDB已支持cum系列函数，但须注意目前仅支持输入类型为 Vector。
支持的单目函数有：`cummax`, `cummin`, `cummed`, `cumfirstNot`, `cumlastNot`, `cumrank`, `cumcount`, `cumpercentile`, `cumstd`, `cumstdp`, `cumvar`, `cumvarp`, `cumsum`, `cumsum2`, `cumsum3`, `cumsum4`, `cumavg`, `cumprod`, `cumPositiveStreak`。
支持的双目函数有：`cumbeta`, `cumwsum`, `cumwavg`, `cumcovar`, `cumcorr`。

### 3.4. 空值的处理

JIT中所有的函数和运算符处理空值的方法都与原生函数和运算符一致，即每个数据类型都用该类型的最小值来表示该类型的空值，用户不需要专门处理空值。

### 3.5. JIT函数之间的调用

DolphinDB的JIT函数可以调用另一个JIT函数。例如：

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

在上面的例子中，内部会先编译 `myfunc1` , 生成一个签名为 double myfunc1(double) 的native函数， `myfunc2` 生成的机器码中直接调用这个函数，而不是在运行时判断 `myfunc1` 是否为JIT函数后再执行，从而达到最高的执行效率。

请注意，JIT函数内不可以调用非JIT的用户自定义函数，因为这样无法进行类型推导。关于类型推导下面会提到。

### 3.6. JIT的编译成本以及缓存机制

DolphinDB的JIT底层依赖[LLVM](https://llvm.org/)实现，每个用户自定义函数在编译时都会生成自己的module，相互独立。编译主要包含以下几个步骤：

1. LLVM相关变量和环境的初始化
2. 根据DolphinDB脚本的语法树生成LLVM的IR
3. 调用LLVM优化第二步生成的IR，然后编译为机器码

以上步骤中第一步耗时一般在5ms以内，后面两步的耗时与实际脚本的复杂度成正比，总体而言编译耗时基本上在50ms以内。

对于一个JIT函数以及一个参数类型组合，DolphinDB只会编译一次。系统会对JIT函数编译的结果进行缓存。系统根据用户调用一个JIT函数时提供的参数的数据类型得到一个对应的字符串，然后在一个哈希表中寻找这个字符串对应的编译结果，如果存在则直接调用；如果不存在则开始编译，并将编译结果保存到此哈希表中，然后执行。

对需要反复执行的任务，或者运行时间远超编译耗时的任务，JIT会显著提高运行速度。

### 3.7. 支持函数作为函数参数

从1.2.0版本开始，DolphinDB的JIT支持函数以及部分应用（包括嵌套的部分应用）作为函数参数。下面举例说明：

```
@jit
def foo(f, x, y){return f(x,y)}

@jit
def h(x,y){return x+y}

@jit
def g(x,y){return foo(h, x, y)}
```
上例中，函数`g`中引用的函数`foo`的第一个参数是函数`h`。

```
@jit
def h(a,b,c){return a + b + c}

@jit
def foo(f,x,y){return f(x,y)}

@jit
def g(x,y,z){return foo(h{x}, y, z)}
```
上例中，将部分应用h{x}作为第一个参数传给foo。其中部分应用的自由参数可以是任意的，可为h{,x}，h{,,x}或者h{x,,y}等等。

```
@jit
def f1(x,y,z){return x + y + z}

@jit
def f2(g2){return g2(1)}

@jit
def f3(g3){return f2(g3{2})}

@jit
def f4(){return f3(f1{,,3})}

f4()
```
嵌套部分应用也是支持的，在上面的例子中，f4中将f1{,,3}传给f3, 在f3中对这个函数参数又进行了一次部分应用。

需要注意的是，如果同一个函数参数在一个JIT函数中有多种签名，由于编译实现的限制，执行时会报异常。例如：

```
@jit
def foo(x,y){return x + y}

@jit
def f1(f){return f(1,2) + f(1.0,2)}

@jit
def f2(){return f1(foo)}

f2() 
//抛出异常
```

### 3.8. 对矩阵的支持

从1.2.0版本开始，DolphinDB的JIT支持矩阵作为函数参数和返回值，支持矩阵的四则运算，对矩阵应用函数`det`与`flatten`, 以及矩阵转置等运算。

```
@jit
def foo(a, b) {
  c = a.dot(b)
  d = c.transpose()
  h = d * 2.0
  f = h / 3.0
  g = h + f
  return g
}

foo(1..100$10:10, 100..1$10:10)
```

### 3.9. 局限

目前DolphinDB中JIT适用的场景还比较有限：

- 只支持用户自定义函数。
- 只接受scalar、array、pair和矩阵类型的参数，另外的类型如table、dict、string、symbol、tuple等暂不支持。

## 4. 类型推导

在使用LLVM生成IR之前，必须知道脚本中所有变量的类型，这个步骤就是类型推导。DolphinDB的JIT使用的类型推导方式是局部推导，比如：

```
@jit
def foo() {
  x = 1
  y = 1.1
  z = x + y
  return z
}
```

通过 x = 1 确定x的类型是int；通过 y = 1.1 确定y的类型是 double；通过 z = x + y 以及上面推得的x和y的类型，确定z的类型也是double；通过 return z 确定 `foo` 函数的返回类型是double。

如果函数有参数的话，比如：

```
@jit
def foo(x) {
  return x + 1
}
```

`foo` 函数的返回类型就依赖于输入值x的类型。

上面我们提到了目前JIT支持的数据类型，如果函数内部出现了不支持的类型，或者输入的变量类型不支持，那么就会导致整个函数的变量类型推导失败，在运行时会抛出异常。例如：

```
@jit
def foo(x) {
  return x + 1
}

foo(123)             // 正常执行
foo(1:2)             // 正常执行
foo("abc")           // 抛出异常，因为目前不支持STRING
foo((1 2, 3 4, 5 6)) // 抛出异常，因为目前不支持tuple
```

因此，为了能够正常使用JIT函数，用户应该避免在函数内或者参数中使用尚不支持的函数。

## 5. 实例

### 5.1. 计算隐含波动率 (implied volatility)

上面提到过某些计算无法进行向量化运算，计算隐含波动率 (implied volatility)就是一个例子：

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

timer(10) test_jit(future_price, strike, ttm, risk_rate, b_rate, option_price, is_call)          //  2621.73 ms
timer(10) test_non_jit(future_price, strike, ttm, risk_rate, b_rate, option_price, is_call)      //   302714.74 ms

```

上面的例子中， `ImpliedVolatility` 会调用 `GBlackScholes` 函数。函数 `test_non_jit` 可通过把 `test_jit` 定义之前的@jit去掉以获取。JIT版本 `test_jit` 运行速度是非JIT版本 `test_non_jit` 的115倍。

### 5.2. 计算Greeks

量化金融中经常使用[Greeks](https://www.wikiwand.com/en/Greeks_(finance))进行风险评估，下面以charm(delta衰减)为例展示JIT的使用：

```
@jit
def myMax(a,b){
	if(a>b){
		return a
	}else{
		return b
	}
}

@jit
def NormDist(x) {
  return cdfNormal(0, 1, x);
}

@jit
def ND(x) {
  return (1.0/sqrt(2*pi)) * exp(-(x*x)/2.0)
}

@jit
def CalculateCharm(future_price, strike_price, input_ttm, risk_rate, b_rate, vol, multi, is_call) {
  day_year = 245.0;

  d1 = (log(future_price/strike_price) + (b_rate + (vol*vol)/2.0) * input_ttm) / (myMax(vol,0.00001) * sqrt(input_ttm));
  d2 = d1 - vol * sqrt(input_ttm);

  if (is_call) {
    return -exp((b_rate - risk_rate) * input_ttm) * (ND(d1) * (b_rate/vol/sqrt(input_ttm) - d2/2.0/input_ttm) + (b_rate-risk_rate) * NormDist(d1)) * future_price * multi / day_year;
  } else {
    return -exp((b_rate - risk_rate) * input_ttm) * (ND(d1) * (b_rate/vol/sqrt(input_ttm) - d2/2.0/input_ttm) - (b_rate-risk_rate) * NormDist(-d1)) * future_price * multi / day_year;
  }
}

@jit
def test_jit(future_price, strike_price, input_ttm, risk_rate, b_rate, vol, multi, is_call) {
	n = size(future_price)
	ret = array(DOUBLE, n, n)
	i = 0
	do {
		ret[i] = CalculateCharm(future_price[i], strike_price[i], input_ttm[i], risk_rate[i], b_rate[i], vol[i], multi[i], is_call[i])
		i += 1
	} while(i < n)
	return ret
}

def ND_validate(x) {
  return (1.0/sqrt(2*pi)) * exp(-(x*x)/2.0)
}

def NormDist_validate(x) {
  return cdfNormal(0, 1, x);
}

def CalculateCharm_vectorized(future_price, strike_price, input_ttm, risk_rate, b_rate, vol, multi, is_call) {
	day_year = 245.0;

	d1 = (log(future_price/strike_price) + (b_rate + pow(vol, 2)/2.0) * input_ttm) / (max(vol, 0.00001) * sqrt(input_ttm));
	d2 = d1 - vol * sqrt(input_ttm);
	return iif(is_call,-exp((b_rate - risk_rate) * input_ttm) * (ND_validate(d1) * (b_rate/vol/sqrt(input_ttm) - d2/2.0/input_ttm) + (b_rate-risk_rate) * NormDist_validate(d1)) * future_price * multi / day_year,-exp((b_rate - risk_rate) * input_ttm) * (ND_validate(d1) * (b_rate/vol/sqrt(input_ttm) - d2/2.0/input_ttm) - (b_rate-risk_rate) * NormDist_validate(-d1)) * future_price * multi / day_year)
}

n = 1000000
future_price=rand(10.0,n)
strike_price=rand(10.0,n)
strike=rand(10.0,n)
input_ttm=rand(10.0,n)
risk_rate=rand(10.0,n)
b_rate=rand(10.0,n)
vol=rand(10.0,n)
input_vol=rand(10.0,n)
multi=rand(10.0,n)
is_call=rand(true false,n)
ttm=rand(10.0,n)
option_price=rand(10.0,n)

timer(10) test_jit(future_price, strike_price, input_ttm, risk_rate, b_rate, vol, multi, is_call)                     //   1834 ms
timer(10) test_none_jit(future_price, strike_price, input_ttm, risk_rate, b_rate, vol, multi, is_call)                // 224099 ms
timer(10) CalculateCharm_vectorized(future_price, strike_price, input_ttm, risk_rate, b_rate, vol, multi, is_call)    //   3118 ms
```

本例比上一节更加复杂，涉及到更多的函数调用和更复杂的计算。JIT比非JIT快120倍，比向量化版本快70%。

### 5.3. 计算止损点 (stoploss)

在这篇[知乎专栏](https://zhuanlan.zhihu.com/p/47236676)中，我们展示了如何使用DolphinDB进行技术信号回测，下面我们用JIT来实现其中的stoploss函数：

```
@jit
def stoploss_JIT(ret, threshold) {
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
      break
		}
		i += 1
	} while(i < n)

	return indicator
}

def stoploss_no_JIT(ret, threshold) {
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
      break
		}
		i += 1
	} while(i < n)

	return indicator
}

def stoploss_vectorization(ret, threshold){
	cumret = cumprod(1+ret)
 	drawDown = 1 - cumret / cumret.cummax()
	firstCutIndex = at(drawDown >= threshold).first() + 1
	indicator = take(false, ret.size())
	if(isValid(firstCutIndex) and firstCutIndex < ret.size())
		indicator[firstCutIndex:] = true
	return indicator
}
ret = take(0.0008 -0.0008, 1000000)
threshold = 0.10
timer(10) stoploss_JIT(ret, threshold)              //      59 ms
timer(10) stoploss_no_JIT(ret, threshold)           //   14622 ms
timer(10) stoploss_vectorization(ret, threshold)    //     152 ms
```

用JIT实现的版本比向量化版本快了1.5倍左右，比非JIT版本快248倍左右。

本例中计算止损，只需要找到drawdown大于threshold的第一天，一般不需要使用所有的行。如果数据中最后一天才会达到threshold，那么JIT版本的速度会和向量化计算十分接近。

### 5.4. 计算持仓成本

若同一个标的的买入卖出交易反复发生，要计算每一笔卖出交易的盈利（或亏损），需要计算平均持仓成本。第一笔买入交易的价格为持仓成本；后续买入交易后，平均持仓成本为之前平均持仓成本与最新交易价格的加权平均；卖出后，平均持仓成本不变；若全部卖出，则重新开始计算持仓成本。这是一个典型的路径依赖问题，不能向量化解决。

下例中trades表的字段price表示交易价格，amount表示交易量（正数为买入，负数为卖出）。

不使用JIT计算持仓成本：
```
def holdingCost_no_JIT(price, amount){
	holding = 0.0
	cost = 0.0
	avgPrice = 0.0
	n = size(price)
	avgPrices = array(DOUBLE, n, n, 0)
	for (i in 0:n){
		holding += amount[i]
		if (amount[i] > 0){
			cost += amount[i] * price[i]
			avgPrice = cost/holding
		}
		else{
			cost += amount[i] * avgPrice
		}
	    avgPrices[i] = avgPrice
	}
	return avgPrices
}
```
使用JIT计算持仓成本：
```
@jit
def holdingCost_JIT(price, amount){
	holding = 0.0
	cost = 0.0
	avgPrice = 0.0
	n = size(price)
	avgPrices = array(DOUBLE, n, n, 0)
	for (i in 0..n){
		holding += amount[i]
		if (amount[i] > 0){
			cost += amount[i] * price[i]
			avgPrice = cost/holding
		}
		else{
			cost += amount[i] * avgPrice
		}
		avgPrices[i]=avgPrice
	}
	return avgPrices
}
```
以下为性能对比：
```
n=1000000
id = 1..n
price = take(101..109,n)
amount =take(1 2 3 -2 -1 -3 4 -1 -2 2 -1,n)
trades = table(id, price, amount)

timer (10)
t = select *, iif(amount < 0, amount*(avgPrice - price), 0) as profit
from (
  select *, holdingCost_no_JIT(price, amount) as avgPrice
  from trades
)    // 29,509ms

timer (10)
select *, iif(amount < 0, amount*(avgPrice - price), 0) as profit
from (
  select *, holdingCost_JIT(price, amount) as avgPrice
  from trades
)     // 148 ms
```
本例中，使用100万行数据进行计算，JIT版本和非JIT版本在同一台机器各运行10次，耗时分别是148毫秒和29509毫秒。JIT版本比非JIT版本快约200倍。

## 6. 未来

在后续的版本中，我们计划逐步支持以下功能：

- 支持dictionary等数据结构，支持string等数据类型。
- 支持更多的数学和统计类函数。
- 增强类型推导功能，能够识别更多DolphinDB内置函数返回值的数据类型。

## 7. 总结

DolphinDB推出了即时编译执行自定义函数的功能，显著提高了for循环，while循环和if-else等语句的运行速度，特别适合于无法使用向量化运算但又对运行速度有极高要求的场景，例如高频因子计算、实时流数据处理等。


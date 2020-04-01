# 技术分析（Technical Analysis）指标库

[TA-Lib](https://github.com/mrjbq7/ta-lib)是一个Python库，封装了用C语言实现的金融交易技术分析的诸多常用指标。为了方便用户在DolphinDB中计算这些技术指标，我们使用DolphinDB脚本实现了TA-Lib中包含的指标函数，并封装在DolphinDB ta module (ta.dos)中。 使用ta模块需要DolphinDB Database Server 1.10.3 或以上版本。

## 1. 函数及参数的命名与用法规范

* 与TA-Lib中所有函数名大写以及所有参数名小写的规范不同，ta模块中，函数名及参数名均采用驼峰式命名法。

例如，TA-Lib中DEMA函数的语法为```DEMA(close, timeperiod=30)```。在ta模块中相应的函数为```dema(close, timePeriod)```。

* TA-Lib中某些函数有可选参数。ta模块中，所有参数皆为必选。

* 为得到有意义的结果，ta模块中函数的参数timePeriod要求至少是2。

## 2. 使用范例

### 2.1 脚本中直接使用指标函数

对一个向量直接使用ta模块中的`wma`函数进行计算：
```
use ta
close = 7.2 6.97 7.08 6.74 6.49 5.9 6.26 5.9 5.35 5.63
x = wma(close, 5);
```
### 2.2 在SQL语句中分组使用

用户经常需要在数据表中对多组数据在每组内进行计算。在以下例子中，我们构造了一个包含2个股票的数据表：
```
close = 7.2 6.97 7.08 6.74 6.49 5.9 6.26 5.9 5.35 5.63 3.81 3.935 4.04 3.74 3.7 3.33 3.64 3.31 2.69 2.72
date = (2020.03.02 + 0..4 join 7..11).take(20)
symbol = take(`F,10) join take(`GPRO,10)
t = table(symbol, date, close)
```
对其中每只股票使用ta模块中的`wma`函数进行计算：
```
update t set wma = wma(close, 5) context by symbol
```

### 2.3 返回多个列的结果

某些函数会返回多个列的结果，例如函数`bBands`。

直接使用的例子：
```
close = 7.2 6.97 7.08 6.74 6.49 5.9 6.26 5.9 5.35 5.63
low, mid, high = bBands(close, 5, 2, 2, 2);
```
在SQL语句中使用的例子：
```
close = 7.2 6.97 7.08 6.74 6.49 5.9 6.26 5.9 5.35 5.63 3.81 3.935 4.04 3.74 3.7 3.33 3.64 3.31 2.69 2.72
date = (2020.03.02 + 0..4 join 7..11).take(20)
symbol = take(`F,10) join take(`GPRO,10)
t = table(symbol, date, close) 
select *, bBands(close, 5, 2, 2, 2) as `high`mid`low from t context by symbol

symbol date       close high     mid      low
------ ---------- ----- -------- -------- --------
F      2020.03.02 7.2
F      2020.03.03 6.97
F      2020.03.04 7.08
F      2020.03.05 6.74
F      2020.03.06 6.49  7.292691 6.786    6.279309
F      2020.03.09 5.9   7.294248 6.454    5.613752
F      2020.03.10 6.26  7.134406 6.328667 5.522927
F      2020.03.11 5.9   6.789441 6.130667 5.471892
F      2020.03.12 5.35  6.601667 5.828    5.054333
F      2020.03.13 5.63  6.319728 5.711333 5.102939
GPRO   2020.03.02 3.81
GPRO   2020.03.03 3.935
GPRO   2020.03.04 4.04
GPRO   2020.03.05 3.74
GPRO   2020.03.06 3.7   4.069365 3.817333 3.565302
GPRO   2020.03.09 3.33  4.133371 3.645667 3.157962
GPRO   2020.03.10 3.64  4.062941 3.609333 3.155726
GPRO   2020.03.11 3.31  3.854172 3.482667 3.111162
GPRO   2020.03.12 2.69  3.915172 3.198    2.480828
GPRO   2020.03.13 2.72  3.738386 2.993333 2.24828
```

## 3. 性能说明

ta模块中的函数与TA-Lib中对应函数相比，直接使用时的平均速度相似，但在分组计算时，ta模块中的函数性能远超TA-Lib中对应函数。本节的性能对比，我们以`wma`函数为例。

### 3.1 直接使用性能对比

在DolphinDB中：
```
use ta
close = 7.2 6.97 7.08 6.74 6.49 5.9 6.26 5.9 5.35 5.63
close = take(close, 1000000)
timer x = wma(close, 5);
```
对一个长度为1,000,000的向量直接使用ta模块中的`wma`函数，耗时为3毫秒。

与之对应的Python语句如下：
```python
close = np.array([7.2,6.97,7.08,6.74,6.49,5.9,6.26,5.9,5.35,5.63,5.01,5.01,4.5,4.47,4.33])
close = np.tile(close,100000)

import time
start_time = time.time()
x = talib.WMA(close, 5)
print("--- %s seconds ---" % (time.time() - start_time))
```
TA-Lib中`WMA`函数耗时为11毫秒，为DolphinDB ta module中`wma`函数的3.7倍。

### 3.2 分组使用性能对比

在DolphinDB中，构造一个包含1000只股票，总长度为1,000,000的数据表：
```
n=1000000
close = rand(1.0, n)
date = take(2017.01.01 + 1..1000, n)
symbol = take(1..1000, n).sort!()
t = table(symbol, date, close)
timer update t set wma = wma(close, 5) context by symbol;
```
使用ta模块中的`wma`函数对每只股票进行计算，耗时为17毫秒。

与之对应的Python语句如下：
```python
close = np.random.uniform(size=1000000)
symbol = np.sort(np.tile(np.arange(1,1001),1000))
date = np.tile(pd.date_range('2017-01-02', '2019-09-28'),1000)
df = pd.DataFrame(data={'symbol': symbol, 'date': date, 'close': close})

import time
start_time = time.time()
df["wma"] = df.groupby("symbol").apply(lambda df: talib.WMA(df.close, 5)).to_numpy()
print("--- %s seconds ---" % (time.time() - start_time))
```
使用TA-Lib中`WMA`函数对每只股票进行计算耗时为535毫秒，为ta模块中`wma`函数的31.5倍。


## 4. 向量化实现

ta模块中的所有函数与TA-Lib一样，都是向量函数：输入为向量，输出的结果也是等长的向量。TA-Lib底层是用C语言实现的，效率非常高。ta模块虽然是用DolphinDB的脚本语言实现，但充分的利用了内置的向量化函数和高阶函数, 避免了循环，极为高效。已经实现的57个函数中，28个函数比TA-Lib运行的更快，最快的函数是TA-Lib性能的3倍左右；29个函数比TA-LIB慢，最慢的性能不低于TA-Lib的1/3。

ta模块中的函数实现亦极为简洁。ta.dos总共765行，平均每个函数约14行。扣除注释、空行、函数定义的起始结束行，以及为去除输入参数开始的空值的流水线代码，每个函数的核心代码约4行。用户可以通过浏览ta模块的函数代码，学习如何使用DolphinDB脚本进行高效的向量化编程。

### 4.1. 空值的处理
若TA-Lib的输入向量开始包含空值，则从第一个非空位置开始计算。ta模块采用了相同的策略。滚动/累积窗口函数的计算过程中，每组最初的尚未达到窗口长度的值，对应位置的结果为空。这一点TA-Lib与ta模块的结果一致。但之后，若再有空值，此位置以及所有以后位置在TA-Lib函数中的结果有可能均为空值。除非窗口中非空值数据的数量不足以计算指标（例如计算方差时只有一个非空值），否则空值的数量不影响ta模块函数结果的产生。
```
//use ta in dolphindb
close = [99.9, NULL, 84.69, 31.38, 60.9, 83.3, 97.26, 98.67]
ta::var(close, 5, 1)

[,,,,670.417819,467.420569,539.753584,644.748976]

//use talib in python
close = np.array([99.9, np.nan, 84.69, 31.38, 60.9, 83.3, 97.26, 98.67])
talib.VAR(close, 5, 1)

array([nan, nan, nan, nan, nan, nan, nan, nan])
```
上面的总体方差计算中，因为close的第二个值为空值，ta模块和TA-Lib的输出不同，TA-Lib输出全部为空值。如果替换空值为81.11，ta模块和TA-Lib得到相同的结果。在第一个元素99.9之前加一个空值，两者的结果仍然相同。简而言之，当输入参数只有开始的k个元素为空时，ta模块和TA-Lib的输出结果完全一致。

### 4.2 迭代处理
技术分析的很多指标计算会用到迭代，即当前的指标值取决于前一个指标值和当前输入： r[n] = coeff * r[n-1] + input[n]。对于这一类型的计算，DolphinDB引入了函数`iterate`进行向量化处理，避免使用循环。
```
def ema(close, timePeriod) {
1 	n = close.size()
2	b = ifirstNot(close)
3	start = b + timePeriod
4	if(b < 0 || start > n) return array(DOUBLE, n, n, NULL)
5	init = close.subarray(:start).avg()
6	coeff = 1 - 2.0/(timePeriod+1)
7	ret = iterate(init, coeff, close.subarray(start:)*(1 - coeff))
8	return array(DOUBLE, start - 1, n, NULL).append!(init).append!(ret)
}
```
以`ema`函数实现为例，第5行代码计算第一个窗口的均值作为迭代序列的初始值。第6行代码定义了迭代参数。第7行代码使用`iterate`函数计算ema序列。内置函数`iterate`有非常高的运行效率，计算长度为1,000,000的向量的ema序列，窗口长度为10时，TA-Lib耗时7.4ms，ta模块仅耗时5.0ms，比TA-Lib更快。

### 4.3 滑动窗口函数的应用
大部分技术指标会指定一个滑动窗口，在每一个窗口中计算指标值。DolphinDB的内置函数中已经包括了一部分基本的滑动窗口指标的计算，包括`mcount`, `mavg`, `msum`, `mmax`, `mmin`, `mimax`, `mimin`, `mmed`, `mpercentile`, `mrank`, `mmad`, `mbeta`, `mcorr`, `mcovar`, `mstd`和`mvar`。这些基本的滑动窗口函数经过了充分的优化，大部分函数的复杂度达到了O(n)，也即与窗口长度无关。更为复杂的滑动指标可以通过叠加或变换上述基本指标来实现。ta::var是总体方差，而DolphinDB内置的mvar是样本方差，所以需要经过调整。
```
def var(close, timePeriod, nddev){
1	n = close.size()
2	b = close.ifirstNot()
3	if(b < 0 || b + timePeriod > n) return array(DOUBLE, n, n, NULL)
4	mobs =  mcount(close, timePeriod)
5	return (mvar(close, timePeriod) * (mobs - 1) \ mobs).fill!(timePeriod - 1 + 0:b, NULL)
}
```
下面我们给出一个更为复杂的例子，linearreg_slope指标的实现。linearreg_slope实际上是计算close相对于序列 0 .. (timePeriod - 1)的beta。这个指标看起来无法实现向量化，必须取出每个窗口的数据，循环进行beta计算。但事实上，这个例子中的自变量比较特殊，是一个固定的等差序列，计算后一个窗口的beta时，可以通过增量计算来优化。由于beta(A,B) = (sumAB - sumA*sumB/obs)/varB， varB和sumB是固定的，滑动窗口时，我们只需要优化sumAB和sumA的计算。通过公式化简，sumAB在两个窗口之间的变化可以通过向量化实现，具体参考代码第10行。代码第12行计算第一个窗口的sumAB。代码第13行中的sumABDelta.cumsum()向量化计算所有窗口的sumAB值。
```
def linearreg_slope(close, timePeriod){
1	n = close.size()
2	b = close.ifirstNot()
3	start = b + timePeriod
4	if(b < 0 || start > n) return array(DOUBLE, n, n, NULL)
5	x = 0 .. (timePeriod - 1)
6	sumB = sum(x).double()
7	varB = sum2(x) - sumB*sumB/timePeriod
8	obs = mcount(close, timePeriod)
9	msumA = msum(close, timePeriod)
10	sumABDelta = (timePeriod - 1) * close + close.move(timePeriod) - msumA.prev() 
11	sumABDelta[timePeriod - 1 + 0:b] = NULL
12	sumABDelta[start - 1] =  wsum(close.subarray(b:start), x)
13	return (sumABDelta.cumsum() - msumA * sumB/obs)/varB
}
```
计算长度为1,000,000的向量的linearreg_slope序列，窗口长度为10时，TA-Lib耗时13ms，ta模块耗时14ms，两者几乎相等。这对于用脚本实现的ta来说，已属不易。当窗口增加到20时，TA-Lib的耗时增加到22ms，而ta的耗时仍为14ms。这说明TA-Lib的实现采用了循环，对每一个窗口分别计算，而ta则实现了向量化计算，与窗口长度无关。

### 4.4 减少数据复制的技巧
对向量进行slice，join，append等操作时，很有可能发生大量数据的复制。通常数据复制会比很多简单的计算更耗时。这儿通过一些实际例子介绍如何减少数据复制的一些技巧。

#### 4.4.1 使用向量视图subarray减少数据复制
如果直接slice某个向量的子窗口进行计算，会产生一个新的向量，并进行数据复制，不仅占用更多内存而且耗时。DolphinDB为此推出了一个新的数据结构`subarray`。它实际上是原向量的一个视图，只是记录了原向量的指针，以及开始和结束位置，并没有分配大块内存来存储新的向量，所以实际上没有发生数据复制。所有向量的只读操作都可直接应用于subarray。ema和linearreg_slope的实现都大量使用了subarray。下面的例子中，我们对一个百万长度的向量进行100次slice操作，耗时62ms，每次操作耗时0.62ms。考虑到4.2中测试一个百万长度向量的ema操作耗时仅5ms，节约0.62ms是非常可观的。
```
close = rand(1.0, 1000000)
timer(100) close[10:]

Time elapsed: 62 ms
```

#### 4.4.2 为向量指定容量(capacity)避免扩容
当我们往一个向量末尾追加数据时，如果容量不够，那么需要分配一个更大的内存空间，并把将旧的数据复制到新的内存空间，最后释放旧的内存空间。当向量比较大的时候，这个操作可能会比较耗时。如果明确知道一个向量最后的长度，那么事先指定这个长度为向量的容量可以避免向量扩容的发生。DolphinDB的内置函数array(dataType, [initialSize], [capacity], [defaultValue])可以在创建时指定capacity。譬如ema函数的第8行，先创建一个容量为n的向量，然后append计算结果。

## 5. DolphinDB ta 指标列表

### Overlap Studies

**函数**|**语法**|**解释**
---|---|---
bBands|bBands(close, timePeriod, nbDevUp, nbDevDn, maType)|Bollinger Bands
dema|dema(close, timePeriod)|Double Exponential Moving Average
ema|ema(close, timePeriod)|Exponential Moving Average
kama|kama(close, timePeriod)|Kaufman Adaptive Moving Average
ma|ma(close, timePeriod, maType)|Moving average
mama|mama(close, fastLimit, slowLimit)|MESA Adaptive Moving Average
mavp|mavp(inReal, periods, minPeriod, maxPeriod, maType)|Moving average with variable period
midPoint|midPoint(close, timePeriod)|MidPoint over period
midPrice|midPrice(low, high, timePeriod)|Midpoint Price over period
sma|sma(close, timePeriod)|Simple Moving Average
t3|t3(close, timePeriod, vfactor)|Triple Exponential Moving Average (T3)
tema|tema(close, timePeriod)|Triple Exponential Moving Average
trima|trima(close, timePeriod)|Triangular Moving Average
wma|wma(close, timePeriod)|Weighted Moving Average

### Momentum Indicators

**函数**|**语法**|**解释**
---|---|---
adx|adx(high, low, close, timePeriod)|Average Directional Movement Index
adxr|adxr(high, low, close, timePeriod)|Average Directional Movement Index Rating
apo|apo(close,fastPeriod,slowPeriod,maType)|Absolute Price Oscillator
aroon|aroon(high,low,timePeriod)|Aroon
aroonOsc|aroonOsc(high, low, timePeriod)|Aroon Oscillator
bop|bop(open, high, low, close)|Balance Of Power
cci|cci(high, low, close, timePeriod)|Commodity Channel Index
cmo|cmo(close, timePeriod)|Chande Momentum Oscillator
dx|dx(high, low, close, timePeriod)|Directional Movement Index
macd|macd(close, fastPeriod, slowPeriod, signalPeriod)|Moving Average Convergence/Divergence
macdExt|macdExt(close, fastPeriod, fastMaType, slowPeriod, slowMaType, signalPeriod, signalMaType)|MACD with controllable MA type
macdFix|macdFix(close, signalPeriod)|Moving Average Convergence/Divergence Fix 12/26
mfi|mfi(high, low, close, volume, timePeriod)|Money Flow Index
minus_di|minus_di(high, low, close, timePeriod)|Minus Directional Indicator
minus_dm|minus_dm(high, low, timePeriod)|Minus Directional Movement
mom|mom(close, timePeriod)|Momentum
plus_di|plus_di(high, low, close, timePeriod)|Plus Directional Indicator
plus_dm|plus_dm(high, low, timePeriod)|Plus Directional Movement
ppo|ppo(close, fastPeriod, slowPeriod, maType)|Percentage Price Oscillator
roc|roc(close, timePeriod)|Rate of change : ((price/prevPrice)-1)*100
rocp|rocp(close, timePeriod)|Rate of change Percentage: (price-prevPrice)/prevPrice
rocr|rocr(close, timePeriod)|Rate of change ratio: (price/prevPrice)
rocr100|rocr100(close, timeperiod)|Rate of change ratio 100 scale: (price/prevPrice)*100
rsi|rsi(close, timePeriod)|Relative Strength Index
stoch|stoch(high, low, close, fastkPeriod, slowkPeriod, slowkMatype, slowdPeriod, slowdMatype)|Stochastic
stochf|stochf(high, low, close, fastkPeriod, fastdPeriod, fastdMatype)|Stochastic Fast
stochRsi|stochRsi(real, timePeriod, fastkPeriod, fastdPeriod, fastdMatype)|Stochastic Relative Strength Index
trix|trix(close, timePeriod)|1-day Rate-Of-Change (ROC) of a Triple Smooth EMA
ultOsc|ultOsc(high, low, close, timePeriod1, timePeriod2, timePeriod3)|Ultimate Oscillator
willr|willr(high, low, close, timePeriod)|Williams' %R

### Volume Indicators

**函数**|**语法**|**解释**
---|---|---
ad|ad(high, low, close, volume)|Chaikin A/D Line
obv|obv(close, volume)|On Balance Volume

### Volatility Indicators

**函数**|**语法**|**解释**
---|---|---
atr|atr(high, low, close, timePeriod)|Average True Range
natr|natr(high, low, close, timePeriod)|Normalized Average True Range
trange|trange(high, low, close)|True Range

### Price Transform

**函数**|**语法**|**解释**
---|---|---
avgPrice|avgPrice(open, high, low, close)|Average Price
medPrice|medPrice(high, low)|Median Price
typPrice|typPrice(high, low, close)|Typical Price
wclPrice|wclPrice(high, low, close)|Weighted Close Price

### Statistic Functions

**函数**|**语法**|**解释**
---|---|---
beta|beta(high, low, timePeriod)|Beta
correl|correl(high, low, timePeriod)|Pearson's Correlation Coefficient (r)
linearreg|linearreg(close, timePeriod)|Linear Regression
linearreg_angle|linearreg_angle(close, timePeriod)|Linear Regression Angle
linearreg_intercept|linearreg_intercept(close, timePeriod)|Linear Regression Intercept
linearreg_slope|linearreg_slope(close, timePeriod)|Linear Regression Slope
stdDev|stdDev(close, timePeriod, nbdev)|Standard Deviation
tsf|tsf(close, timePeriod)|Time Series Forecast
var|var(close, timePeriod, nbdev)|Variance

### Other Functions
* 对Ta-Lib中的 Math Transform 与 Math Operators 类函数，可使用相应的DolphinDB内置函数代替。例如，Ta-Lib中的 SQRT, LN, SUM 函数，可分别使用DolphinDB中的 `sqrt`, `log`, `msum` 函数代替。
* 下列 Ta-Lib 函数尚未在ta模块中实现：所有 Pattern Recognition 与 Cycle Indicators 类函数，以及HT_TRENDLINE(Hilbert Transform - Instantaneous Trendline), ADOSC(Chaikin A/D Oscillator), MAMA(MESA Adaptive Moving Average), SAR(Parabolic SAR), SAREXT(Parabolic SAR - Extended)函数。

## 6. 路线图(Roadmap)

* 尚未实现的指标函数，将在下一个版本中实现，预计在2020年4月完成。
* 目前DolphinDB的自定义函数不支持默认参数，也不支持函数调用时基于键值来输入参数。这两点将在DolphinDB Server 1.20.0中实现，届时ta模块将实现跟TA-Lib一致的默认参数。
* 使用ta模块前必须使用 use ta 以加载，这在交互式查询中不尽方便。DolphinDB Server将在1.20版本中允许在系统初始化时预加载模块，ta模块函数与DolphinDB内置函数将拥有同等地位，以省去加载模块这个步骤。




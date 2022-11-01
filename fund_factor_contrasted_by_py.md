# 平均性能超 Python10 倍: 如何使用 DolphinDB 计算基金日频因子

根据某个基金每日的净值数据计算得到的因子称作“基金日频因子”。基金日频因子能反映出基金的近况，是衡量基金收益、波动、风险等的重要指标。随着数据规模与日俱增，对大规模数量级的数据进行处理的需求日益旺盛，在计算的速度、准确性上对计算工具提出了更高的要求。本教程将为大家介绍如何基于 DolphinDB 计算多个基金的日频因子，并通过 Python 实现相同因子的计算，对比两者的计算性能。所用数据约220万条，均为与沪深300指数按日期对齐后的基金净值数据。结果表明在不同 CPU 核数下，DolphinDB 较 Python 均有明显的性能优势。

本教程包含如下内容：

- [平均性能超 Python10 倍: 如何使用 DolphinDB 计算基金日频因子](#平均性能超-python10-倍-如何使用-dolphindb-计算基金日频因子)
  - [1. 测试环境](#1-测试环境)
  - [2. 基金日频因子背景介绍及代码实现](#2-基金日频因子背景介绍及代码实现)
  - [3. DolphinDB 中因子计算实现及性能测试](#3-dolphindb-中因子计算实现及性能测试)
    - [3.1 数据导入及概览](#31-数据导入及概览)
    - [3.2 数据处理](#32-数据处理)
    - [3.3 因子计算](#33-因子计算)
    - [3.4 结果展示](#34-结果展示)
  - [4. Python vs DolphinDB 性能对比](#4-python-vs-dolphindb-性能对比)
    - [4.1 因子计算流程实现](#41-因子计算流程实现)
    - [4.2 性能计算结果对比](#42-性能计算结果对比)
    - [4.3 性能分析](#43-性能分析)
  - [5. 总结](#5-总结)
    - [附件](#附件)

## 1. 测试环境

安装 DolphinDB server，配置为单节点模式，其默认端口号为`8848`。本次测试所涉及到的硬件环境和软件环境如下：

- **硬件环境**

  | 硬件名称 | 配置信息                                   |
  | :------- | :----------------------------------------- |
  | 外网 IP  | xxx.xxx.xxx.122                            |
  | 操作系统 | 64位 CentOS Linux 7 (Core)                 |
  | 内存     | 256 GB                                     |
  | CPU 类型 | Intel(R) Xeon(R) Silver 4216 CPU @ 2.10GHz |

- **软件环境**

  | 软件名称                                                     | 版本信息   | 教程&下载链接                                                |
  | :----------------------------------------------------------- | :--------- | ------------------------------------------------------------ |
  | DolphinDB                                                    | V2.00.7    | [DolphinDB单节点部署教程](https://gitee.com/dolphindb/Tutorials_CN/blob/master/standalone_server.md)；[DolphinDB下载链接](https://dolphindb.cn/alone/alone.php?id=10) |
  | DolphinDB GUI                                                | V1.30.19.2 | [DolphinDB GUI下载链接](https://dolphindb.cn/alone/alone.php?id=10) |
  | Python（包含numpy、pandas、scipy等库以及 DolphinDB 的 Python API，需要预先安装） | 3.7.9      | [Python官网](https://www.python.org/)                        |

## 2. 基金日频因子背景介绍及代码实现

本教程选取了10个基金日频因子，涵盖基金评价体系的各个方面，作为性能测试的指标。其相关的背景含义、计算公式及在 DolphinDB 脚本和 Python 中的定义如下所示：

> 注：下文提到的 DailyReturn 指日收益率，BeginningtValue 指基金日净值序列中的第一个净值数据，EndingValue 指基金日净值序列中的最后一个净值数据。

- **年化收益率**

  - 因子含义：将当前收益率转换为一年内（按252个交易日计算）的收益率；

  - 公式：

    <img src="https://latex.codecogs.com/svg.image?yearReturn_{i}=(1&plus;\frac{EndingValue-BeginningValue}{BeginningValue})**(\frac{252}{730})-1"/>
    
  - 代码实现：

    - DolphinDB：

      ```sql
      defg getYearReturn(value){
            return pow(1 + ((last(value) - first(value))\first(value)), 252\730) - 1
      }
      ```

    - Python：

      ```python
      def getYearReturn(value):
          return pow(1 + ((value[-1] - value[0])/value[0]), 252/730)-1
      ```

- **年化波动率**
  
  - 因子含义：衡量投资标的波动风险
  
  - 公式：
  
    <img src="https://latex.codecogs.com/svg.image?annualVolat=\sqrt{\frac{\sum\limits_{i=1}^{n}(DailyReturn_{i}-(\overline{DailyReturn})^{2})}{n-1}}*\sqrt{252}"/>
    
  - 代码实现：
  
    - DolphinDB：
  
      ```sql
      defg getAnnualVolatility(value){
      	return std(deltas(value)\prev(value)) * sqrt(252)
      }
      ```
  
    - Python：
  
      ```python
      def getAnnualVolatility(value):
          diff_value = np.diff(value)
          rolling_value = np.roll(value, 1)
          rolling_value = np.delete(rolling_value, [0])
          return np.std(np.true_divide(diff_value, rolling_value)) * np.sqrt(252)
      ```
  
- **收益率偏度**

  - 因子含义：衡量收益偏斜程度

  - 公式：

    <img src="https://latex.codecogs.com/svg.image?skewValue=\frac{\frac{1}{n}\sum\limits_{i=1}^{n}(DailyReturn_{i}-\overline{DailyReturn})^{3}}{(\sqrt{\frac{1}{n}\sum\limits_{i=1}^{n}(DailyReturn_{i}-\overline{DailyReturn})^{2})^{3}"/>
    
  - 代码实现：

    - DolphinDB：

      ```sql
      defg getAnnualSkew(value){
      	return skew(deltas(value)\prev(value))
      }
      ```

    - Python：

      ```python
      def getAnnualSkew(value):
          diff_value = np.diff(value)
          rolling_value = np.roll(value, 1)
          rolling_value = np.delete(rolling_value, [0])
          return st.skew(np.true_divide(diff_value, rolling_value))
      ```

- **收益率峰度**
  
  - 因子含义：基金日收益率的分布相对于正态分布的峰值程度和尾部厚度
  
  - 公式：
  
    <img src="https://latex.codecogs.com/svg.image?kurValue=\frac{\frac{1}{n}\sum\limits_{i=1}^{n}(DailyReturn_{i}-\overline{DailyReturn})^{4}}{(\frac{1}{n}\sum\limits_{i=1}^{n}(DailyReturn_{i}-\overline{DailyReturn})^{2})^{4}"/>
    
  - 代码实现:
  
    - DolphinDB：
  
      ```sql
      defg getAnnualKur(value){
      	return kurtosis(deltas(value)\prev(value)) 
      }
      ```
  
    - Python：
  
      ```python
      def getAnnualKur(value):
          diff_value = np.diff(value)
          rolling_value = np.roll(value, 1)
          rolling_value = np.delete(rolling_value, [0])
          return st.kurtosis(np.true_divide(diff_value, rolling_value), fisher=False)
      ```
  
- **夏普比率**
  
  - 因子含义：反映单位风险基金净值增长率超过无风险收益率的程度
  
  - 公式：
  
    <img src="https://latex.codecogs.com/svg.image?sharpValue=(yearReturn_{value}-0.03)/annualVolat"/>
    
  - 代码实现：
  
    - DolphinDB：
  
      ```sql
      defg getSharp(value){
      	return (getYearReturn(value) - 0.03)\getAnnualVolatility(value) as sharpeRat
      }
      ```
  
    - Python：
  
      ```python
      def getSharp(value):
          return (getYearReturn(value) - 0.03)/getAnnualVolatility(value) if getAnnualVolatility(value) != 0 else 0
      ```
  
- **跟踪误差**
  - 因子含义：组合收益率与基准收益率之间差异的标准差

  - 公式：

    <img src="https://latex.codecogs.com/svg.image?trackError=\sqrt{\frac{\sum_{i=1}^{n}(DailyReturn_{i}-PriceReturn_{i})^{2}}{n-1}}"/>
    
  - 代码实现：
  
    - DolphinDB：
  
      ```sql
      defg getTrackError(value, price){
      	return std(deltas(value)\prev(value) - deltas(price)\prev(price))
      }
      ```
  
    - Python：
  
      ```python
      def getTrackError(value, price):
          diff_price = np.diff(price)
          rolling_price = np.roll(price, 1)
          rolling_price = np.delete(rolling_price, [0])
          diff_value = np.diff(value)
          rolling_value = np.roll(value, 1)
          rolling_value = np.delete(rolling_value, [0])
          return np.std(np.true_divide(diff_value, rolling_value)-np.true_divide(diff_price, rolling_price))
      ```
  
- **信息比率**
  - 因子含义：承担单位主动风险带来的超额收益
  
  - 公式：
  
    <img src="https://latex.codecogs.com/svg.image?infoRatio=(yearReturn_{value}-yearReturn_{price})/annualVolat"/>
    
  - 代码实现：
  
    - DolphinDB：
  
      ```sql
      defg getIndexFundAnReturn(price){
      	return pow(1 + ((last(price) - first(price))\first(price)), 252\487) - 1
      }
      defg getInforRatio(value, price){
      	return (pow(1 + ((last(value) - first(value))\first(value)), 252\487) - 1 - getIndexFundAnReturn(price)) \ (getTrackError(value, price) * sqrt(252))
      }
      ```
  
    - Python：
  
      ```python
      def getIndexFundAnReturn(price):
          return pow(1 + ((price[-1] - price[0]) / price[0]), 252 / 487) - 1
      def getInforRatio(value, price):
          return (pow(1 + ((value[-1] - value[0]) / value[0]), 252 / 487) - 1 - getIndexFundAnReturn(price))/(getTrackError(value, price) * np.sqrt(252))
      ```
  
- **在险价值**
  - 因子含义：在一定时间（t）内，一定置信度（此处为95%）下，最小的期望损失

  - 公式：

    <img src="https://latex.codecogs.com/svg.image?var=\frac{\sum{DailyReturn_{i}(var=0.95)}}{\sum_{i=1}^{n}{DailyReturn_{i}}}"/>
    
  - 代码实现：
  
    - DolphinDB：
  
      ```sql
      defg getVar(value){
      	return -percentile(deltas(value)\prev(value), 5)
      }
      ```
  
    - Python：
  
      ```python
      def getVar(value):
          diff_value = np.diff(value)
          rolling_value = np.roll(value, 1)
          rolling_value = np.delete(rolling_value, [0])
          res = np.percentile(np.true_divide(diff_value, rolling_value), 5)
          res = max(-res, 0)
          return res
      ```
  
- **赫斯特指数**
  - 因子含义：体现时间序列的自相关性，尤其是序列中隐藏的长期趋势的指标。此处用来揭示某只基金序列中的隐藏长期趋势。
  
  - 计算方法：
  
    a. 将收益率序列按照不同的粒度（记为 k）切分成不同的片段，此处从粒度2到粒度365开始切分序列；
  
    b. 计算每个片段的均值，此处要计算2+3+4+...+365种；
  
    ​    公式：
  
    <img src="https://latex.codecogs.com/svg.image?M=Mean=\frac{\sum_{i=1}^{k}DailyReturn_{k}}{k}"/>
  
    c. 计算每个片段的离差序列，即用每个片段的均值分别减该片段内的每个元素；
  
    ​    公式：
  
    <img src="https://latex.codecogs.com/svg.image?For\&space;every\&space;DailyReturn_{i}\&space;X_{i}=DailyReturn_{i}-M"/>
  
    d. 计算每个片段离差序列中的最大值减去最小值，记为 R；
  
    ​    公式：
  
    <img src="https://latex.codecogs.com/svg.image?R_{k}=max(X_{1},X_{2},...,X_{k})-min(X_{1},X_{2},...,X_{k})"/>
  
    e. 计算每个片段的标准差，记为 S；
  
    ​    公式：
  
    <img src="https://latex.codecogs.com/svg.image?S_{k}=\sqrt{\frac{\sum_{i=1}^{k}(X_{i}-M)^2}{k}}"/>
  
    d. 计算每个片段的 R/S 值，并计算按照不同粒度划分的所有片段中各片段元素的均值；
  
    ​    公式：
  
    <img src="https://latex.codecogs.com/svg.image?AVS=\frac{\sum_{i=1}^{n}(\frac{R}{S})^n}{n}"/>
  
    e. 以划分的标准粒度为自变量，以对应的各片段元素的均值为因变量，计算回归方程，截距即为赫斯特指数；
  
    ​    公式：AVS=a*k+b，经过计算后 b 为赫斯特指数
    
  - 代码实现：
  
    - DolphinDB：
  
      ```sql
      def calAllRs2(mret, symList, k){
              rowCount = mret.rows()/k * k
              demeanCum = rolling(cumsum, mret[0:rowCount,] - each(stretch{, rowCount}, rolling(avg, mret, k, k)), k, k)
              a = rolling(max, demeanCum, k, k) - rolling(min, demeanCum, k, k)
              RS = nullFill!(a/rolling(stdp, mret, k, k), 1.0).mean().log()
              return table(symList as fundNum, take(log(k), symList.size()) as knum, RS as factor1)
      }
      ```
  
    - Python：
  
      ```python
      def calHurst(value_list, min_k):
          n = len(value_list)
          max_k = int(np.floor(n / 2))
          r_s_dict = []
          for k in range(min_k, max_k +1):
              subset_list = [value_list[i: i+k] for i in range(0, n, k)]
              if np.mod(n, k) > 0:
                  subset_list.pop()
              df_subset = np.array(subset_list)
              df_mean = df_subset.mean(axis=1).reshape(-1,1)
              df_cusum = (df_subset - df_mean).cumsum(axis=1)
              r = df_cusum.max(axis=1) - df_cusum.min(axis=1) + np.spacing(1)
              s = df_subset.std(axis=1, ddof=0) + np.spacing(1)
              r_s_dict.append({'R_S': (r / s).mean(), 'N': k})
          log_r_s=[]
          log_n=[]
          for i in range(len(r_s_dict)):
              log_r_s.append(np.log(r_s_dict[i]['R_S']))
              log_n.append(np.log(r_s_dict[i]['N']))
          try:
              res = np.polyfit(log_n, log_r_s, 1)[0]
          except:
              res = None
          return res
      ```
  
- **HM 模型选股能力**

  - 因子含义：对选股以及择时能力进行衡量的二项式参数检验模型

  - 计算方法：

    Y = DailyReturn-(0.03\252)，X1 = PriceReturn-(0.03\252)，X2 = if(x1 > 0, x1, 0)，其中截距为1。

    对上述变量进行线程回归：Y = a1 * X1 + b1 * X2 + b，其中 a1, a2 为回归系数，b 为截距。
    
  - 代码实现：
  
    - DolphinDB：
  
      ```sql
       defg getHM1(value, price){
       	riskRatio = 0.03\252	 
       	return ols(deltas(value)\prev(value) - riskRatio, (deltas(price)\prev(price) - riskRatio, iif( deltas(price)\prev(price) - riskRatio > 0, deltas(price)\prev(price) - riskRatio, 0))) [0] as intercept
       }
      ```
  
    - Python：
  
      ```python
      def getHM1(value, price):
          diff_price = np.diff(price)
          rolling_price = np.roll(price, 1)
          rolling_price = np.delete(rolling_price, [0])
          diff_value = np.diff(value)
          rolling_value = np.roll(value, 1)
          rolling_value = np.delete(rolling_value, [0])
          y_list = np.true_divide(diff_value, rolling_value)
          x_list = np.true_divide(diff_price, rolling_price)
          x_add = sm.add_constant(np.array([[i - 0.03/252 for i in x_list], [max(i, 0) - 0.03/252 for i in x_list]]).T)
          model = sm.OLS(np.array([i - 0.03/252 for i in y_list]), x_add).fit()
          return model.params[0]
      ```

## 3. DolphinDB 中因子计算实现及性能测试

### 3.1 数据导入及概览

- **数据结构：**

  本教程选取了2019.05.24 - 2022.05.27期间多只基金的日净值数据，总数据量为330多万条。以下是净值表在 DolphinDB 中的数据结构：

  | 字段名    | 字段含义   | 数据类型（DolphinDB） |
  | --------- | ---------- | --------------------- |
  | TradeDate | 交易日期   | DATE                  |
  | fundNum   | 基金名称   | SYMBOL                |
  | value     | 基金日净值 | DOUBLE                |

  同时，本教程选取了2019.05.24 - 2022.05.27期间沪深300指数的数据，共734条，用于和基金日净值数据作对齐操作。以下是指数表在 DolphinDB 中的数据结构：

  | 字段名    | 字段含义                    | 数据类型（DolphinDB） |
  | --------- | --------------------------- | --------------------- |
  | TradeDate | 交易日期                    | DATE                  |
  | fundNum   | 指数名称（此处均为沪深300） | SYMBOL                |
  | value     | 沪深300收盘价格             | DOUBLE                |

- **数据导入：**

  本教程所使用的数据分别存储在两个 CSV 为格式的文件中，使用前需要先导入到 DolphinDB 的 `fund_OLAP` 和 `fund_hs_OLAP` 维度表中。

  首先，通过 DolphinDB GUI 连接 DolphinDB 后，定义函数分别读取 CSV 文件：

  ```
  //获取 CSV 数据列名
  def readColumnsFromWideCSV(absoluteFilename){
          schema1 = extractTextSchema(absoluteFilename)
          update schema1 set type = `STRING 
          allSymbol = loadText(absoluteFilename,,schema1)[0, 1:]
          titleSchema = extractTextSchema(absoluteFilename, skipRows = 0);
          for(x in allSymbol){
                  testValue = exec x[name] from titleSchema
                  testValue = testValue[1:]
          }
          return testValue
  }
  //获取 CSV 文件数据内容
  def readIndexedMatrixFromWideCSV(absoluteFilename){
          contracts = readColumnsFromWideCSV(absoluteFilename)
          dataZoneSchema = extractTextSchema(absoluteFilename, skipRows = 1)
          update dataZoneSchema set type = "DOUBLE" where name != "col0"//所有行全部改成double
          dataZoneWithIndexColumn = loadText(absoluteFilename, skipRows = 1, schema = dataZoneSchema)
          indexVector = exec col0 from dataZoneWithIndexColumn
          dataZoneWithoutIndex = dataZoneWithIndexColumn[:, 1:]
          dataMatrix = matrix(dataZoneWithoutIndex)
          dataMatrix.rename!(indexVector, contracts)
          return dataMatrix
  }
  ```
  
  其次，调用该函数获取文件中的数据，将之转换分别赋予新的列名，存入 DolphinDB 的内存表：
  
  ```
  //基金日净值数据
  allSymbols = readColumnsFromWideCSV(csvPath)$STRING
  dataMatrix = readIndexedMatrixFromWideCSV(csvPath)
  fundTable = table(dataMatrix.rowNames() as Tradedate, dataMatrix)
  result = fundTable.unpivot(`Tradedate, allSymbols).rename!(`Tradedate`fundNum`value)
    
  //沪深300指数
  allSymbols1 = readColumnsFromWideCSV(csvPath1)$STRING
  dataMatrix1 = readIndexedMatrixFromWideCSV(csvPath1)
  fundTable1 = table(dataMatrix1.rowNames() as Tradedate, dataMatrix1)
  result1 = fundTable1.unpivot(`Tradedate, allSymbols1).rename!(`Tradedate`fundNum`value)
  ```
  
  最后，建立分布式数据库 `dfs://fund_OLAP` 和维度表 `fund_OLAP`, `fund_hs_OLAP`，并导入数据：
  
  ```
  //创建数据库
  dbName = "dfs://fund_OLAP"
  dataDate = database(, VALUE, 2021.01.01..2021.12.31)
  symbol = database(, HASH, [SYMBOL, 20])
  if(existsDatabase(dbName)){
  	dropDatabase(dbName)
  }
  db = database(dbName, COMPO, [dataDate, symbol])
  //定义表结构
  name = `Tradedate`fundNum`value
  type = `DATE`SYMBOL`DOUBLE
  tbTemp = table(1:0, name, type)
  //创建维度表 fund_OLAP
  tbName1 = "fund_OLAP"
  db.createTable(tbTemp1, tbName)
  loadTable(dbName, tbName1).append!(result)
  //创建维度表 fund_hs_OLAP
  tbName2 = "fund_hs_OLAP"
  db.createTable(tbTemp, tbName2)
  loadTable(dbName, tbName2).append!(result1)
  ```
  
- **数据概览：**

  数据导入成功后，执行如下代码查看前十条 fund_OLAP 数据：

  ```
  select top 10 * from loadTable("dfs://fund_OLAP", "fund_OLAP")
  ```

  ![数据概览1](images/fund_factor_contrasted_by_py/fund_10.png)

  同样，执行如下代码查看前十条 fund_hs_OLAP 数据：

  ```
  select top 10 * from loadTable("dfs://fund_OLAP", "fund_hs_OLAP")
  ```

  ![数据概览2](images/fund_factor_contrasted_by_py/fund_hs_10.png)

### 3.2 数据处理

分别从两张表中取出数据，同沪深300指数按日期对齐（[aj](https://dolphindb.cn/cn/help/SQLStatements/TableJoiners/asofjoin.html)），填充空缺值，仅保留两表中日期相同的数据：

```
fund_OLAP=select * from loadTable("dfs://fund_OLAP", "fund_OLAP")
fund_hs_OLAP=select * from loadTable("dfs://fund_OLAP", "fund_hs_OLAP")
ajResult=select Tradedate, fundNum, value, fund_hs_OLAP.Tradedate as hsTradedate, fund_hs_OLAP.value as price from aj(fund_OLAP, fund_hs_OLAP, `Tradedate)
result2=select Tradedate, fundNum, iif(isNull(value), ffill!(value), value) as value, price from ajResult where Tradedate == hsTradedate
```

同时，计算多个基金的日收益率，进行赫斯特指数的计算：

```
symList = exec distinct(fundNum) as fundNum from result2 order by fundNum
portfolio = select fundNum as fundNum, (deltas(value)\prev(value)) as log, TradeDate as TradeDate from result2 where TradeDate in 2019.05.24..2022.05.27 and fundNum in symList
m_log = exec log from portfolio pivot by TradeDate, fundNum
mlog =  m_log[1:,]
```

处理后的数据共220万条，结构如下：

| 字段名    | 字段含义        | 数据类型（DolphinDB） |
| --------- | --------------- | --------------------- |
| TradeDate | 交易日期        | DATE                  |
| fundNum   | 基金名称        | SYMBOL                |
| value     | 基金日净值      | DOUBLE                |
| price     | 沪深300收盘价格 | DOUBLE                |
| log       | 基金日收益率    | DOUBLE                |

### 3.3 因子计算

本教程以提交后台作业的计算时间来反映 DolphinDB 性能。

为了对比在不同 CPU 核数下的性能，需要修改`dolphindb.cfg`文件中的 `workerNum` 参数，其配置值表示计算时所用到的 CPU 核数，更多 DolphinDB 相关配置信息可参考 [DolphinDB 单实例参数配置](https://dolphindb.cn/cn/help/DatabaseandDistributedComputing/Configuration/Thread.html)。

> 注意：每次参数修改后，需要重启 DolphinDB Server 才能生效。

- 计算9个因子（不包含赫斯特指数）的响应时间:

  首先，定义计算9个因子的函数：

  ```
  def getFactor(result2, symList){
  	Return = select fundNum, 
  	            getYearReturn(value) as annualReturn,
  	            getAnnualVolatility(value) as annualVolat,
  	            getAnnualSkew(value) as skewValue,
  	            getAnnualKur(value) as kurValue,
  	            getSharp(value) as sharpValue,
  	            getTrackError(value, price) as trackError,
  	            getVar(value) as var,
  	            getInforRatio(value, price) as infoRatio,
  	            getHM1(value, price) as intercept       
               from result2
               where TradeDate in 2019.05.24..2022.05.27 and fundNum in symList group by fundNum
   }
  ```

  其次，定义获取9个因子计算和数据操作的时间的函数，并提交后台作业：

  ```
  def parJob1(){
  	timer{fund_OLAP=select * from loadTable("dfs://fund_OLAP", "fund_OLAP")
  		  fund_hs_OLAP=select * from loadTable("dfs://fund_OLAP", "fund_hs_OLAP")
  		  ajResult = select Tradedate, fundNum, value, fund_hs_OLAP.Tradedate as hsTradedate, fund_hs_OLAP.value as price from aj(fund_OLAP, fund_hs_OLAP, `Tradedate)
  		  result2 = select Tradedate, fundNum, iif(isNull(value), ffill!(value), value) as value,price from ajResult where Tradedate == hsTradedate
  		  symList = exec distinct(fundNum) as fundNum from result2 order by fundNum
  		  symList2 = symList.cut(250)//此处，将任务切分，按每次250个不同基金数据进行计算
  	ploop(getFactor{result2}, symList2)}
  }//定义获取9个因子计算和数据操作的时间的函数
  /**
   * 提交1个 job（单用户）
   */
  submitJob("parallJob1", "parallJob_single_nine", parJob1)
  
  /**
   * 提交5个 job（多用户）
   */
  for(i in 0..4){
  	submitJob("parallJob5", "parallJob_multi_nine", parJob1)
  }
  ```

  最后，分别计算两种情形下的响应时间：

  ```
  //获取单个用户的运行时间
  select max(endTime) - min(startTime) from getRecentJobs() where jobDesc = "parallJob_single_nine"
  //获取多个用户的运行时间
  select max(endTime) - min(startTime) from getRecentJobs() where jobDesc = "parallJob_multi_nine"
  ```

- 计算10个因子的响应时间:

  首先，定义计算10个因子的函数：

  ```
  def getFactor(result2, symList){
  	Return = select fundNum, 
  	            getYearReturn(value) as annualReturn,
  	            getAnnualVolatility(value) as yearVolRat,
  	            getAnnualSkew(value) as skewValue,
  	            getAnnualKur(value) as kurValue,
  	            getSharp(value) as sharpValue,
  	            getTrackError(value, price) as trackError,
  	            getVar(value) as var,
  	            getInforRatio(value, price) as infoRatio,
  	            getHM1(value, price) as intercept       
               from result2
               where TradeDate in 2019.05.24..2022.05.27 and fundNum in symList group by fundNum
   }
  ```
  
  其次，定义获取10个因子计算和数据操作的时间的函数，并提交 job：
  
  ```
    def parJob2(){
    	timer{fund_OLAP=select * from loadTable("dfs://fund_OLAP", "fund_OLAP")
    		  fund_hs_OLAP=select * from loadTable("dfs://fund_OLAP", "fund_hs_OLAP")
    		  ajResult = select Tradedate, fundNum, value, fund_hs_OLAP.Tradedate as hsTradedate, fund_hs_OLAP.value as price from aj(fund_OLAP, fund_hs_OLAP, `Tradedate)
    		  result2 = select Tradedate, fundNum, iif(isNull(value), ffill!(value), value) as value,price from ajResult where Tradedate == hsTradedate
    		  symList = exec distinct(fundNum) as fundNum from result2 order by fundNum
                              symList2 = symList.cut(250)
    		  portfolio = select fundNum as fundNum, (deltas(value)\prev(value)) as log, TradeDate as TradeDate from result2 where TradeDate in 2019.05.24..2022.05.27 and fundNum in symList
              m_log = exec log from portfolio pivot by TradeDate, fundNum
              mlog =  m_log[1:,]
              knum = 2..365
              }//此处，将任务切分，按每次250个不同基金数据进行计算
              timer{ploop(getFactor{result2}, symList2)
              a = ploop(calAllRs2{mlog,symList}, knum).unionAll(false)
              res2 = select fundNum, ols(factor1, kNum)[0] as hist, ols(factor1, kNum)[1] as hist2, ols(factor1, kNum)[2] as hist3 from a group by fundNum}
    }//定义获取10个因子计算和数据操作的时间的函数
    /**
     * 提交1个 job（单用户）
     */
    submitJob("parallJob1", "parallJob_single_ten", parJob2)
    
    /**
     * 提交5个 job（多用户）
     */
    for(i in 0..4){
    	submitJob("parallJob5", "parallJob_multi_ten", parJob2)
    }
  ```
  
  最后，分别计算两种情形下的响应时间：
  
  ```
    //获取单个用户的运行时间
    select max(endTime) - min(startTime) from getRecentJobs() where jobDesc = "parallJob_single_ten"
    //获取多个用户的运行时间
    select max(endTime) - min(startTime) from getRecentJobs() where jobDesc = "parallJob_multi_ten"
  ```
  
- 9个日频因子计算结果展示

  ![计算结果1](images/fund_factor_contrasted_by_py/calculating_outcome.png)

### 3.4 结果展示

- 单用户

  | CPU数 | 9个因子 | 10个因子（包含赫斯特指数） |
  | ----- | ------ | ------------------------ |
  | 4     | 753ms  | 7,835ms                  |
  | 6     | 535ms  | 5,378ms                  |
  | 8     | 424ms  | 4,537ms                  |
  | 10    | 507ms  | 3,643ms                  |
  | 12    | 465ms  | 3,087ms                  |

- 多用户（此处为5用户）

  | CPU数 | 9个因子  | 10个因子（包含赫斯特指数） |
  | ----- | ------- | ------------------------ |
  | 4     | 1,980ms | 30,769ms                 |
  | 6     | 1,480ms | 24,675ms                 |
  | 8     | 1,215ms | 20,114ms                 |
  | 10    | 988ms   | 15,843ms                 |
  | 12    | 836ms   | 13,433ms                 |


> 注：由于赫斯特指数需要按照2+3+4+...+365种不同的粒度方式切分成不同种类的序列划分，同时分别对不同粒度的每一段序列分别计算均值、离差和标准差等，并最终求平均的 R/S 值，计算的子指标过大，时间复杂度较高，因此耗时相较于其它因子更长。

## 4. Python vs DolphinDB 性能对比

本教程中，我们基于 Python 实现了相同的因子计算。本节为大家展示 DolphinDB 与 Python 计算性能的差异。

我们使用 Python API 进行取数等数据处理操作，使用 `numpy`, `pandas`, `scipy` 等库实现基金日频因子的计算。由于 Python 没有自带的多线程库，本教程我们引入了 `joblib` 库中的 `Parallel` 方法，通过设置其 `n_jobs` 参数模拟不同 CPU 核数的运行环境。

### 4.1 因子计算流程实现

本节介绍如何使用 Python 计算10个基金日频因子并统计计算时间。其中 DolphinDB 脚本中的函数到 Python 代码中的函数映射关系可以参考 [DolphinDB 函数到 Python 函数的映射](https://gitee.com/dolphindb/Tutorials_CN/blob/master/function_mapping_py.md)。

首先，使用 Python 定义测算基金日收益率的 `getLog()` 函数和执行因子计算任务的 `main()` 函数：

```python
def getLog(value):
    diff_value = np.diff(value)
    rolling_value = np.roll(value, 1)
    rolling_value = np.delete(rolling_value, [0])
    return np.insert(np.true_divide(diff_value, rolling_value), 0, np.nan)

def main(li):
    value = np.array(li["value"])
    price = np.array(li["price"])
    log = np.array(li["log"])
    getYearReturn(value)
    getAnnualVolatility(value)
    getAnnualSkew(value)
    getAnnualKur(value)
    getSharp(value)
    getTrackError(value, price)
    getInforRatio(value, price)
    getVar(value)
    getHM1(value, price)
    calHurst(log, 2)
```

然后，使用 Python API 连接 DolphinDB，从两个数据表中读取数据，并对其进行数据对齐和计算基金日收益率的操作。同时修改 `Parallel` 方法的 `n_jobs` 参数模拟不同个数的 CPU 环境，并统计整个计算流程的时间：

```python
s = ddb.session()
s.connect("127.0.0.1", 8848, "admin", "123456")
start = time.time()
fund_OLAP = s.loadTable(dbPath="dfs://fund_OLAP", tableName="fund_OLAP").select("*").toDF().sort_values(['Tradedate'])
fund_hs_OLAP = s.loadTable(dbPath="dfs://fund_OLAP", tableName="fund_hs_OLAP").select("*").toDF()
fund_hs_OLAP.rename(columns={'Tradedate': 'hsTradedate'}, inplace=True)
fund_hs_OLAP = fund_hs_OLAP.sort_values(['hsTradedate'])
fund_dui_OLAP = pd.merge_asof(fund_OLAP, fund_hs_OLAP, left_on="Tradedate", right_on="hsTradedate").sort_values(['fundNum_x', 'Tradedate'])
fund_dui_OLAP = fund_dui_OLAP[fund_dui_OLAP['Tradedate'] == fund_dui_OLAP['hsTradedate']]
fund_dui_OLAP.reset_index(drop=True, inplace=True)
fund_dui_OLAP.drop(columns=['fundNum_y', 'hsTradedate'], inplace=True)
fund_dui_OLAP.columns = ['Tradedate', 'fundNum', 'value', 'price']
fund_dui_OLAP["value"].fillna(method = 'ffill', inplace = True)
fund_dui_OLAP["log"] = pd.Series(getLog(fund_dui_OLAP["value"]))
list = fund_dui_OLAP[(fund_dui_OLAP['Tradedate'] >= datetime(2019, 5, 24)) & (fund_dui_OLAP['Tradedate'] <= datetime(2022, 5, 27))].groupby('fundNum')
Parallel(n_jobs=4)(delayed(main)(i) for _,i in list)
end = time.time()
print(end-start)
```

### 4.2 性能计算结果对比

- 单用户

  | CPU数 | 响应时间（DolphinDB） | 响应时间（Python） | 性能对比（Python/DolphinDB) |
  | ----- | --------------------- | ------------------ | --------------------------- |
  | 4     | 7.83s                 | 35.56s             | 4.54                        |
  | 6     | 5.37s                 | 26.56s             | 4.94                        |
  | 8     | 4.53s                 | 21.63s             | 4.77                        |
  | 10    | 3.64s                 | 19.4s              | 5.33                        |
  | 12    | 3.08s                 | 18.2s              | 5.9                         |
  
- 多用户（此处为5用户）

  | CPU数 | 响应时间（DolphinDB） | 响应时间（Python） | 性能对比（Python/DolphinDB) |
  | ----- | --------------------- | ------------------ | --------------------------- |
  | 4     | 30.76s                | 193.42s            | 6.28                        |
  | 6     | 24.67s                | 155.29s            | 6.29                        |
  | 8     | 20.11s                | 159.43s            | 7.93                        |
  | 10    | 15.84s                | 160.79s            | 10.15                       |
  | 12    | 13.43s                | 170.51s            | 12.69                       |

> 注：在 CPU 单核和单用户的条件下，DolphinDB 和 Python 的响应时间分别为 27.06s 和 631.80s，性能对比达到了23倍。

### 4.3 性能分析

在控制其它变量一致的前提下，无论是单用户还是多用户，在不同 CPU 核数环境下 DolphinDB 均表现出了比 Python 更优越的性能。其中性能差异最高可接近 Python 的23倍，平均性能超10倍。究其原因，主要有以下几点：

- DolphinDB 强大的向量化计算能力：DolphinDB 最大程度上兼顾了向量化计算的性能，使得针对数组的向量化计算显示出了比 Python 更优越的性能；
- DolphinDB 丰富的预定义函数：DolphinDB 预定义了1000多个可以直接调用的函数。相较于 Python 减少了因子定义的代码量和封装次数，在计算过程中性能损耗更少；
- DolphinDB 自带的持久化数据存储：DolphinDB 内置数据存储引擎，可以将数据按照不同分区方式存入分布式数据库表，因子计算时的数据读取更高效；Python 在因子计算的过程中需要引入外部数据源，数据读取效率相对较低。

## 5. 总结

本教程基于3000多只基金的日净值数据，为大家介绍了如何在 DolphinDB 和 Python 中计算10种日频因子。同时，我们对比测试了不同 CPU 核数环境下，Python 和 DolphinDB 计算相同因子的性能差异。

可以看到，由于DolphinDB具有强大的支持向量化计算的能力，包含丰富的预定义函数功能，因而无论在多线程还是多任务情况下，DolphinDB 在计算因子时都有优异表现。而 Python 作为解释型脚本语句，每运行一句都要进行相应的解释，且在多线程方面存在不足。因此相较之下，DolphinDB 表现出更为显著的优势。

### 附件

[模拟测试数据文件](data/fund_factor_contrasted_by_py/datafile)

[数据导入到 DolphinDB 的脚本](script/fund_factor_contrasted_by_py/fund_data_load.txt)

[基于 DolphinDB 的十个基金日频因子响应时间计算脚本](script/fund_factor_contrasted_by_py/fund_factor.txt)

[基于 Python 的十个基金日频因子响应时间计算脚本](script/fund_factor_contrasted_by_py/fund_factor.py)
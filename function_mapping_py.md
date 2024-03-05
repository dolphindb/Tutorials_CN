# Python 到 DolphinDB 的函数映射

本篇介绍 Python 部分模块到 DolphinDB 函数库的不完全映射。

下文涉及的 python 模块如下：

- python built-in function
- numpy
- pandas
- scipy
- statsmodels
- sklearn
- TA-lib

- [Python 到 DolphinDB 的函数映射](#python-到-dolphindb-的函数映射)
  - [1.  python built-in function](#1--python-built-in-function)
  - [2.  numpy](#2--numpy)
  - [3.  pandas](#3--pandas)
  - [4.  scipy](#4--scipy)
  - [5.  statsmodels](#5--statsmodels)
  - [6.  sklearn](#6--sklearn)
  - [7.  TA-lib](#7--ta-lib)

## 1.  python built-in function 

| Python 函数 | DolphinDB 函数 |
| ----------- | -------------- |
| all         | all            |
| any         | any            |
| in          | in             |
| ==          | eq             |
| equals      | eqObj          |
| abs         | abs            |
| len         | strlen / size  |
| pow         | pow            |
| print       | print          |
| set         | set            |
| dict        | dict           |
| str         | string         |
| int         | int            |
| bool        | bool           |
| round       | round          |
| slice       | slice          |
| type        | type / typestr |
| zip         | loop(pair, x, y) |
| join        | concat         |
| format      | strReplace     |
| sort        | isort          |
| rjust /zfill | lpad /rpad     |
| lead / lag  | move           |
| itertools.product | cross + join |



## 2.  numpy

| numpy 函数                                               | DolphinDB 函数              |
| -------------------------------------------------------- | --------------------------- |
| numpy.median                                             | med                         |
| numpy.var(ddof=1)                                        | var                         |
| numpy.var                                                | varp                        |
| numpy.cov                                                | covarMatrix                 |
| numpy.cov(fweights)                                      | wcovar                      |
| numpy.std(ddof=1)                                        | std                         |
| numpy.std                                                | stdp                        |
| numpy.percentile / pandas.Series.percentile              | percentile                  |
| numpy.quantile / pandas.Series.quantile                  | quantile                    |
| numpy.quantile                                           | quantileSeries              |
| numpy.corrcoef                                           | corrMatrix                  |
| numpy.random.beta                                        | randBeta                    |
| numpy.random.binomial                                    | randBinomial                |
| numpy.random.chisquare                                   | randChiSquare               |
| numpy.random.exponential                                 | randExp                     |
| numpy.random.f                                           | randF                       |
| numpy.random.gamma                                       | randGamma                   |
| numpy.random.logistic                                    | randLogistic                |
| numpy.random.normal                                      | randNormal                  |
| numpy.random.multivariate_normal                         | randMultivariateNormal      |
| numpy.random.poisson                                     | randPoisson                 |
| numpy.random.standard_t                                  | randStudent                 |
| numpy.random.rand                                        | rand                        |
| numpy.argsort                                            | isort/isort!                |
| numpy.averge(weight)                                     | wavg                        |
| numpy.random.uniform                                     | randUniform                 |
| numpy.random.weibull                                     | randWeibull                 |
| numpy.max                                                | max                         |
| numpy.min                                                | min                         |
| numpy.mean                                               | mean/avg                    |
| numpy.sum                                                | sum                         |
| nump.random.normal                                       | norm                        |
| nump.clip                                                | winsorize                   |

## 3.  pandas

| pandas 函数                                                  | DolphinDB 函数          |
| ------------------------------------------------------------ | ----------------------- |
| df\[column]                                                   | at                      |
| pandas.Series.loc / pandas.DataFrame.loc                     | loc                     |
| pandas.Series.iat / pandas.DataFrame.iat                     | cell                    |
| pandas.Series.iloc / pandas.DataFrame.iloc                   | cells                   |
| pandas.Series.align / pandas.DataFrame.align                 | align                   |
| pandas.unique / pandas.DataFrame.unique  / pandas.Series.unique | distinct                |
| pandas.concat                                                | concatMatrix            |
| pandas.DataFrame.add / pandas.Series.add                     | withNullFill + add      |
| pandas.DataFrame.sub / pandas.Series.sub                     | withNullFill + sub      |
| pandas.DataFrame.mul / pandas.Series.mul                     | withNullFill + mul      |
| pandas.DataFrame.div / pandas.Series.div                     | withNullFill + div / ratio |
| pandas.DataFrame.pivot                                       | pivot / panel           |
| pandas.DataFrame.melt                                        | unpivot                 |
| pandas.DataFrame.merge / pandas.DataFrame.join               | merge                   |
| pandas.DataFrame.ewm.var                                     | ewmVar                  |
| pandas.Series.cov                                            | covar                   |
| pandas.DataFrame.ewm.cov                                     | ewmCov                  |
| pandas.ewmstd                                                | ewmStd                  |
| pandas.DataFrame.corr / pandas.Series.corr                   | corr                    |
| pandas.DataFrame.std / pandas.Series.std                     | std                     |
| pandas.DataFrame.median / pandas.Series.median              | med                     |
| pandas.DataFrame.ewm.corr                                    | ewmCorr                 |
| pandas.DataFrame.max / pandas.Series.max                     | max                     |
| pandas.DataFrame.min / pandas.Series.min                     | min                     |
| pandas.DataFrame.mean / pandas.Series.mean                   | mean/avg                |
| pandas.DataFrame.ewm.mean                                    | ewmMean                 |
| pandas.DataFrame.sum / pandas.Series.sum                     | sum                     |
| pandas.DataFrame.prod / pandas.Series.prod                   | prod                    |
| pandas.DataFrame.nunique / pandas.Series.nunique             | nunique                 |
| pandas.DataFrame.hist / pandas.Series.hist                   | plotHist                |
| pandas.DataFrame.sem / pandas.Series.sem                     | sem                     |
| pandas.DataFrame.mad / pandas.Series.mad                     | mad (useMedian=false)   |
| pandas.DataFrame.kurt(kurtosis) / pandas.Series.kurt(kurtosis)  | kurtosis             |
| pandas.DataFrame.skew / pandas.Series.kurt(skew)             | skew                    |
| pandas.DataFrame.count / pandas.Series.count                 | count                   |
| pandas.DataFrame.idxmax / pandas.Series.idxmax               | imax                    |
| pandas.DataFrame.idxmin / pandas.Series.idxmin               | imin                    |
| pandas.DataFrame.cummax / pandas.Series.cummax               | cummax                  |
| pandas.DataFrame.cummin / pandas.Series.cummin               | cummin                  |
| pandas.DataFrame.cumsum / pandas.Series.cumsum               | cumsum                  |
| pandas.DataFrame.cumprod / pandas.Series.cumprod             | cumprod                 |
| pandas.DataFrame.nlargest(nsmallest) / pandas.Series.nlargest(nsmallest)  |  top + order by / aggrTopN |
| pandas.DataFrame.diff / pandas.Series.diff                   | eachPost, deltas                  |
| pandas.DataFrame.quantile / pandas.Series.quantile           | quantile                |
| pandas.DataFrame.transpose                                   | transpose               |
| pandas.Series.resample / pandas.DataFrame.resample           | resample                |
| pandas.Series.copy / pandas.DataFrame.copy                   | copy                    |
| pandas.Series.describe / pandas.DataFrame.describe  类似     | stat                    |
| pandas.DataFrame.isnull/pandas.DataFrame.isna         | isNull                |
| pandas.DataFrame.notnull/pandas.DataFrame.notna       | isValid               |
| pandas.Series.between                                 | between               |
| pandas.Series.is_monotonic_decreasing                 | isMonotonicIncreasing |
| pandas.Series.is_monotonic_increasing                 | isMonotonicDecreasing |
| pandas.DataFrame.mask / pandas.Series.mask            | mask                  |
| pandas.DataFrame.bfill / pandas.Series.bfill                       | bfill/bfill!       |
| pandas.DataFrame.ffill / pandas.Series.ffill                       | ffill/ffill!       |
| pandas.DataFrame.interpolate / pandas.Series.interpolate           | interpolate        |
| pandas.DataFrame.interpolate(method='linear') / pandas.Series.interpolate(method='linear') | lfill/lfill!       |
| pandas.DataFrame.fillna / pandas.Series.fillna               | nullFill/nullFill! |
| pandas.DataFrame.sort_values / pandas.Series.sort_values     | sort/sort!            |
| pandas.DataFrame.head / pandas.Series.head                   | head                  |
| pandas.DataFrame.tail / pandas.Series.tail                   | tail                  |
| pandas.DataFrame.drop / pandas.Series.drop                   | dropColumns!          |
| pandas.DataFrame.dropna / pandas.Series.dropna               | dropna                |
| pandas.DataFrame.rename                                      | rename!               |
| pandas.DataFrame.append / pandas.Series.append               | append!               |
| pandas.DataFrame.keys / pandas.Series.keys                   | rowNames / columnNames |
| pandas.DataFrame.astype / pandas.Series.astype               | cast                  |
| pandas.DataFrame.isin / pandas.Series.isin                   | in                    |
| pandas.Series.str.isspace                                    | isSpace               |
| pandas.Series.str.isalnum                                    | isAlNum               |
| pandas.Series.str.isalpha                                    | isAlpha               |
| pandas.Series.str.isnumeric                                  | isNumeric             |
| pandas.Series.str.isdecimal                                  | isDecimal             |
| pandas.Series.str.isdigit                                    | isDigit               |
| pandas.Series.str.islower                                    | isLower               |
| pandas.Series.str.isupper                                    | isUpper               |
| pandas.Series.str.istitle                                    | isTitle               |
| pandas.Series.str.startswith                          | startsWith            |
| pandas.Series.str.endswith                            | endsWith              |
| pandas.Series.str.find                                | regexFind             |
| pandas.Series.str.replace                             | strReplace            |
| pandas.Series.duplicated /pandas.DataFrame.duplicated | isDuplicated          |
| pandas.Series.rank / pandas.DataFrame.rank                   | rank                  |
| pandas.Series.rank(method='dense') / pandas.DataFrame.rank(method='dense') | denseRank      |
| pandas.read_csv                                              | loadText / loadTextEx |
| pandas.to_csv                                                | saveText              |
| pandas.read_json                                             | fromJson              |
| pandas.DataFrame.to_json / pandas.Series.to_json             | toJson                |
| pandas.DataFrame.groupby.aggFunc                             | regroup, group by     |
| pandas.to_datetime                                           | temporalParse         |
| pandas.DataFrame.rolling / pandas.Series.rolling             | moving                |
| pandas.rolling_mean                                          | mavg                  |
| pandas.rolling_std                                           | mstd                  |
| pandas.rolling_median                                        | mmed                  |
| pandas.DataFrame.shift / pandas.Series.shift                 | move / tmove / prev / next |




## 4.  scipy

| scipy 函数                                               | DolphinDB 函数              |
| -------------------------------------------------------- | --------------------------- |
| scipy.stats.percentileofscore                            | percentileRank              |
| scipy.stats.spearmanr(X, Y)\[0]                           | spearmanr(X, Y)             |
| scipy.spatial.distance.euclidean                         | euclidean                   |
| scipy.stats.beta.cdf(X, a, b)                            | cdfBeta(a, b, X)            |
| scipy.stats.binom.cdf(X, trials, p)                      | cdfBinomial(trials, p, X)   |
| scipy.stats.chi2.cdf(x, df)                              | cdfChiSquare(df, X)         |
| scipy.stats.expon.cdf(x, scale=mean)                     | cdfExp(mean, X)             |
| scipy.stats.f.cdf(X, dfn, dfd)                           | cdfF(dfn, dfd, X)           |
| scipy.stats.gamma.cdf(X, shape, scale=scale)             | cdfGamma(shape, scale, X)   |
| scipy.stats.logistic.cdf(X, loc=mean,scale=scale)        | cdfLogistic(mean, scale, X) |
| scipy.stats.norm.cdf(X, loc=mean, scale=stdev)           | cdfNormal(mean,stdev,X)     |
| scipy.stats.poisson.cdf(X, mu=mean)                      | cdfPoisson(mean, X)         |
| scipy.stats.t.cdf(X, df)                                 | cdfStudent(df, X)           |
| scipy.stats.uniform.cdf(X, loc=lower, scale=upper-lower) | cdfUniform(lower, upper, X) |
| scipy.stats.weibull_min.cdf(X, alpha, scale=beta)        | cdfWeibull(alpha, beta, X)  |
| scipy.stats.zipfian.cdf(X, exponent, num)                | cdfZipf(num, exponent, X)   |
| scipy.stats.beta.ppf(X, a, b)                            | invBeta                     |
| scipy.stats.binom.ppf(X, trials, p)                      | invBinomial                 |
| scipy.stats.chi2.ppf(x, df)                              | invChiSquare                |
| scipy.stats.expon.ppf(x, scale=mean)                     | invExp                      |
| scipy.stats.f.ppf(X, dfn, dfd)                           | invF                        |
| scipy.stats.gamma.ppf(X, shape, scale=scale)             | invGamma                    |
| scipy.stats.logistic.ppf(X, loc=mean,scale=scale)        | invLogistic                 |
| scipy.stats.norm.ppf(X, loc=mean, scale=stdev)           | invNormal                   |
| scipy.stats.poisson.ppf(X, mu=mean)                      | invPoisson                  |
| scipy.stats.t.ppf(X, df)                                 | invStudent                  |
| scipy.stats.uniform.ppf(X, loc=lower, scale=upper-lower) | invUniform                  |
| scipy.stats.weibull_min.ppf(X, alpha, scale=beta)        | invWeibull                  |
| scipy.stats.chisquare                                    | chiSquareTest               |
| scipy.stats.f_oneway                                     | fTest                       |
| scipy.stats.ttest_ind                                    | tTest                       |
| scipy.stats.ks_2samp                                     | ksTest                      |
| scipy.stats.shapiro                                      | shapiroTest                 |
| scipy.stats.mannwhitneyu                                 | mannWhitneyUTest            |
| scipy.stats.mstats.winsorize                             | winsorize                   |
| scipy. stats.kurtosis                                    | kurtosis                    |
| scipy.stats.skew                                         | skew                        |
| scipy.stats.sem                                          | sem                         |
| scipy.stats.zscore(ddof=1)                               | zscore                      |



## 5.  statsmodels

| statsmodels 函数                       | DolphinDB 函数 |
| -------------------------------------- | -------------- |
| statsmodels.api.tsa.acf                | acf            |
| statsmodels.tsa.seasonal.STL           | stl            |
| statsmodels.stats.weightstats.ztest    | zTest          |
| statsmodels.multivariate.manova.MANOVA | manova         |
| statsmodels.api.stats.anova_lm         | anova          |
| statsmodels.regression.linear_model.OLS                 | olsolsEx               |
| statsmodels.regression.linear_model.WLS                 | wls                    |

## 6.  sklearn

| sklearn 函数                                            | DolphinDB 函数         |
| ------------------------------------------------------- | ---------------------- |
| sklearn.linear_model.LinearRegression().fit(Y, X).coef_ | beta(X, Y)             |
| sklearn.metrics.mutual_info_score                       | mutualInfo             |
| sklearn.ensemble.AdaBoostClassifier                     | adaBoostClassifier     |
| sklearn.ensemble.AdaBoostRegressor                      | adaBoostRegressor      |
| sklearn.ensemble.RandomForestClassifier                 | randomForestClassifier |
| sklearn.ensemble.RandomForestRegressor                  | randomForestRegressor  |
| sklearn.naive_bayes.GaussianNB                          | gaussianNB             |
| sklearn.naive_bayes.MultinomialNB                       | multinomialNB          |
| sklearn.linear_model.LogisticRegression                 | logisticRegression     |
| sklearn.mixture.GaussianMixture                         | gmm                    |
| sklearn.cluster.k_means                                 | kmeans                 |
| sklearn.neighbors.KNeighborsClassifier                  | knn                    |
| sklearn.linear_model.ElasticNet                         | elasticNet             |
| sklearn.linear_model.Lasso                              | lasso                  |
| sklearn.linear_model.Ridge                              | ridge                  |
| sklearn.decomposition.PCA                               | pca                    |



## 7.  TA-lib

| TA-lib 函数                                       | DolphinDB 函数  |
| ------------------------------------------------- | --------------- |
| talib.MA                                          | ma              |
| talib.EMA                                         | ema             |
| talib.WMA                                         | wma             |
| talib.SMA                                         | sma             |
| talib.TRIMA                                       | trima           |
| talib.TEMA                                        | tema            |
| talib.DEMA                                        | dema            |
| talib.KAMA                                        | kama            |
| talib.T3                                          | t3              |
| talib.LINEARREG_SLOPE / talib.LINEARREG_INTERCEPT | linearTimeTrend |
| talib.TRANGE                                      | trueRange       |

以上仅列出 DolphinDB 的内置的 TA-lib 函数。有关 TA-lib 指标函数的更多详细信息，参考 [DolphinDB 的 ta-lib 模块](../modules/ta/ta.md)。
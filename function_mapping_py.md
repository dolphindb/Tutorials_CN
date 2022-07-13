# DolphinDB 函数到 Python 函数的映射 <!-- omit in toc -->

> 注意：本篇为 DolphinDB 与 Python 函数库的不完全映射。如发现错误或需要补充相关内容，可以在下方评论或联系我们！联系方式可参考 [ DolphinDB技术支持攻略](https://gitee.com/dolphindb/Tutorials_CN/blob/master/dolphindb_support.md)。

- [统计函数](#统计函数)
- [分布函数](#分布函数)
- [数据处理的函数](#数据处理的函数)
- [校验函数](#校验函数)
- [填充函数](#填充函数)
- [排序函数](#排序函数)
- [TA-lib 函数](#ta-lib-函数)

以下函数选取自 2.00 版本 [用户手册](https://www.dolphindb.cn/cn/help/index.html)。

## 统计函数

| DolphinDB 函数          | Python 函数                                                  |
| ----------------------- | ------------------------------------------------------------ |
| med                     | numpy.median                                                 |
| var                     | numpy.var(ddof=1)                                            |
| varp                    | numpy.var                                                    |
| ewmVar                  | pandas.DataFrame.ewm.var                                     |
| covar                   | pandas.Series.cov                                            |
| ewmCov                  | pandas.DataFrame.ewm.cov                                     |
| covarMatrix             | numpy.cov                                                    |
| wcovar                  | numpy.cov(fweights)                                          |
| std                     | numpy.std(ddof=1)                                            |
| stdp                    | numpy.std                                                    |
| ewmStd                  | pandas.ewmstd                                                |
| percentile              | numpy.percentile / pandas.Series.percentile                  |
| percentileRank          | scipy.stats.percentileofscore                                |
| quantile                | numpy.quantile / pandas.Series.quantile                      |
| quantileSeries          | numpy.quantile                                               |
| corr                    | pandas.Series.corr                                           |
| corrMatrix              | numpy.corrcoef                                               |
| ewmCorr                 | pandas.DataFrame.ewm.corr                                    |
| max                     | pandas.DataFrame.max / pandas.Series.max / numpy.max         |
| min                     | pandas.DataFrame.min / pandas.Series.min / numpy.min         |
| mean                    | pandas.DataFrame.mean / pandas.Series.mean / numpy.mean      |
| ewmMean                 | pandas.DataFrame.ewm.mean                                    |
| avg                     | pandas.DataFrame.mean / pandas.Series.mean / numpy.mean      |
| wavg                    | np.averge(weight)                                            |
| acf                     | statsmodels.api.tsa.acf                                      |
| autocorr                |                                                              |
| isPeak                  |                                                              |
| isValley                |                                                              |
| sum                     | pandas.DataFrame.sum / pandas.Series.sum / numpy.sum         |
| sum2                    |                                                              |
| sum3                    |                                                              |
| sum4                    |                                                              |
| contextSum              |                                                              |
| contextSum2             |                                                              |
| sem                     | pandas.DataFrame.sem / pandas.Series.sem / scipy.stats.sem   |
| mad (**mean / median**) | **mean:** pandas.DataFrame.mad / pandas.Series.mad           |
| kurtosis                | pandas.DataFrame.kurt(kurtosis) / pandas.Series.kurt(kurtosis) / scipy. stats.kurtosis |
| skew                    | pandas.DataFrame.skew / pandas.Series.kurt(skew) / scipy.stats.skew |
| beta(X, Y)              | sklearn.linear_model.LinearRegression().fit(Y, X).coef_      |
| mutualInfo              | sklearn.metrics.mutual_info_score                            |
| spearmanr(X, Y)         | scipy.stats.spearmanr(X, Y)[0]                               |
| euclidean               | scipy.spatial.distance.euclidean                             |
| tanimoto                | [textdistance ](https://pypi.org/project/textdistance/)      |



## 分布函数

| DolphinDB 函数              | Python 函数                                              |
| --------------------------- | -------------------------------------------------------- |
| cdfBeta(a, b, X)            | scipy.stats.beta.cdf(X, a, b)                            |
| cdfBinomial(trials, p, X)   | scipy.stats.binom.cdf(X, trials, p)                      |
| cdfChiSquare(df, X)         | scipy.stats.chi2.cdf(x, df)                              |
| cdfExp(mean, X)             | scipy.stats.expon.cdf(x, scale=mean)                     |
| cdfF(dfn, dfd, X)           | scipy.stats.f.cdf(X, dfn, dfd)                           |
| cdfGamma(shape, scale, X)   | scipy.stats.gamma.cdf(X, shape, scale=scale)             |
| cdfKolmogorov               |                                                |
| cdfLogistic(mean, scale, X) | scipy.stats.logistic.cdf(X, loc=mean,scale=scale)        |
| cdfNormal(mean,stdev,X)     | scipy.stats.norm.cdf(X, loc=mean, scale=stdev)           |
| cdfPoisson(mean, X)         | scipy.stats.poisson.cdf(X, mu=mean)                      |
| cdfStudent(df, X)           | scipy.stats.t.cdf(X, df)                                 |
| cdfUniform(lower, upper, X) | scipy.stats.uniform.cdf(X, loc=lower, scale=upper-lower) |
| cdfWeibull(alpha, beta, X)  | scipy.stats.weibull_min.cdf(X, alpha, scale=beta)        |
| cdfZipf(num, exponent, X)   | scipy.stats.zipfian.cdf(X, exponent, num)                |
| invBeta                     | scipy.stats.beta.ppf(X, a, b)                            |
| invBinomial                 | scipy.stats.binom.ppf(X, trials, p)                      |
| invChiSquare                | scipy.stats.chi2.ppf(x, df)                              |
| invExp                      | scipy.stats.expon.ppf(x, scale=mean)                     |
| invF                        | scipy.stats.f.ppf(X, dfn, dfd)                           |
| invGamma                    | scipy.stats.gamma.ppf(X, shape, scale=scale)             |
| invLogistic                 | scipy.stats.logistic.ppf(X, loc=mean,scale=scale)        |
| invNormal                   | scipy.stats.norm.ppf(X, loc=mean, scale=stdev)           |
| invPoisson                  | scipy.stats.poisson.ppf(X, mu=mean)                      |
| invStudent                  | scipy.stats.t.ppf(X, df)                                 |
| invUniform                  | scipy.stats.uniform.ppf(X, loc=lower, scale=upper-lower) |
| invWeibull                  | scipy.stats.weibull_min.ppf(X, alpha, scale=beta)        |
| randBeta                    | numpy.random.beta                                        |
| randBinomial                | numpy.random.binomial                                    |
| randChiSquare               | numpy.random.chisquare                                   |
| randExp                     | numpy.random.exponential                                 |
| randF                       | numpy.random.f                                           |
| randGamma                   | numpy.random.gamma                                       |
| randLogistic                | numpy.random.logistic                                    |
| randNormal                  | numpy.random.normal                                      |
| randMultivariateNormal      | numpy.random.multivariate_normal                         |
| randPoisson                 | numpy.random.poisson                                     |
| randStudent                 | numpy.random.standard_t                                  |
| rand                        | numpy.random.rand                                        |
| randDiscrete                |                                                          |
| randUniform                 | numpy.random.uniform                                     |
| randWeibull                 | numpy.random.weibull                                     |
| chiSquareTest               | scipy.stats.chisquare                                    |
| fTest                       | scipy.stats.f_oneway                                     |
| zTest                       | statsmodels.stats.weightstats.ztest                      |
| tTest                       | scipy.stats.ttest_ind                                    |
| ksTest                      | scipy.stats.ks_2samp                                     |
| shapiroTest                 | scipy.stats.shapiro                                      |
| mannWhitneyUTest            | scipy.stats.mannwhitneyu                                 |
| norm                        | np.random.normal                                         |



## 数据处理的函数

| DolphinDB 函数         | Python 函数                                              |
| ---------------------- | -------------------------------------------------------- |
| winsorize              | scipy.stats.mstats.winsorize                             |
| resample               | pandas.Series.resample / pandas.DataFrame.resample       |
| spline                 |                                                          |
| neville                |                                                          |
| dividedDifference      |                                                          |
| loess                  |                                                          |
| copy                   | pandas.Series.copy / pandas.DataFrame.copy               |
| stl                    | statsmodels.tsa.seasonal.STL                             |
| stat                   | pandas.Series.describe / pandas.DataFrame.describe  类似 |
| trueRange              | talib.TRANGE                                             |
| manova                 | statsmodels.multivariate.manova.MANOVA                   |
| anova                  | statsmodels.api.stats.anova_lm                           |
| zigzag                 |                                                          |
| zscore                 | scipy.stats.zscore(ddof=1)                               |
| crossStat              |                                                          |
| adaBoostClassifier     | sklearn.ensemble.AdaBoostClassifier                      |
| adaBoostRegressor      | sklearn.ensemble.AdaBoostRegressor                       |
| randomForestClassifier | sklearn.ensemble.RandomForestClassifier                  |
| randomForestRegressor  | sklearn.ensemble.RandomForestRegressor                   |
| gaussianNB             | sklearn.naive_bayes.GaussianNB                           |
| multinomialNB          | sklearn.naive_bayes.MultinomialNB                        |
| logisticRegression     | sklearn.linear_model.LogisticRegression                  |
| glm                    |                                                          |
| gmm                    | sklearn.mixture.GaussianMixture                          |
| kmeans                 | sklearn.cluster.k_means                                  |
| knn                    | sklearn.neighbors.KNeighborsClassifier                   |
| elasticNet             | sklearn.linear_model.ElasticNet                          |
| lasso                  | sklearn.linear_model.Lasso                               |
| ridge                  | sklearn.linear_model.Ridge                               |
| linearTimeTrend        |                                                          |
| pca                    | sklearn.decomposition.PCA                                |
| olsolsEx               | statsmodels.regression.linear_model.OLS                  |
| wls                    | statsmodels.regression.linear_model.WLS                  |
| residual               |                                                          |



## 校验函数

| DolphinDB 函数        | Python 函数                                           |
| --------------------- | ----------------------------------------------------- |
| all                   | all                                                   |
| any                   | any                                                   |
| hasNull               |                                                       |
| isNothing             |                                                       |
| isNull                | pandas.DataFrame.isnull/pandas.DataFrame.isna         |
| isValid               | pandas.DataFrame.notnull/pandas.DataFrame.notna       |
| isVoid                |                                                       |
| in                    | in                                                    |
| between               | pandas.Series.between                                 |
| isSpace               | Series.str.isspace                                    |
| isAlNum               | Series.str.isalnum                                    |
| isAlpha               | Series.str.isalpha                                    |
| isNumeric             | Series.str.isnumeric                                  |
| isDecimal             | Series.str.isdecimal                                  |
| isDigit               | Series.str.isdigit                                    |
| isLower               | Series.str.islower                                    |
| isUpper               | Series.str.isupper                                    |
| isTitle               | Series.str.istitle                                    |
| startsWith            | pandas.Series.str.startswith                          |
| endsWith              | pandas.Series.str.endswith                            |
| regexFind             | pandas.Series.str.find                                |
| isDuplicated          | pandas.Series.duplicated /pandas.DataFrame.duplicated |
| isSorted              |                                                       |
| isMonotonicIncreasing | pandas.Series.is_monotonic_decreasing                 |
| isMonotonicDecreasing | pandas.Series.is_monotonic_increasing                 |
| iif                   |                                                       |
| ifNull                |                                                       |
| ifValid               |                                                       |
| mask                  | pandas.DataFrame.mask / pandas.Series.mask            |



## 填充函数

| DolphinDB 函数     | Python 函数                            |
| ------------------ | -------------------------------------- |
| bfill/bfill!       | pandas.DataFrame.bfill                 |
| ffill/ffill!       | DataFrame.ffill                        |
| interpolate        | DataFrame.interpolate                  |
| lfill/lfill!       | DataFrame.interpolate(method='linear') |
| nullFill/nullFill! | DataFrame.fillna                       |
| fill!              | obj[index]=value                       |



## 排序函数

| DolphinDB 函数 | Python 函数                                                  |
| -------------- | ------------------------------------------------------------ |
| sort/sort!     | pandas.Series.sort_values                                    |
| isort/isort!   | numpy.argsort                                                |
| isortTop       |                                                              |
| rank           | pandas.Series.rank/pandas.DataFrame.rank                     |
| denseRank      | pandas.Series.rank(method='dense')/pandas.DataFrame.rank(method='dense') |



## TA-lib 函数

| DolphinDB 函数  | Python 函数 |
| --------------- | ----------- |
| ma              | talib.MA    |
| ema             | talib.EMA   |
| wma             | talib.WMA   |
| sma             | talib.SMA   |
| trima           | talib.TRIMA |
| tema            | talib.TEMA  |
| dema            | talib.DEMA  |
| gema            |             |
| kama            | talib.KAMA  |
| wilder          |             |
| t3              | talib.T3    |
| linearTimeTrend | talib.LINEARREG_SLOPE / talib.LINEARREG_INTERCEPT  |

以上列出的 TA-lib 函数为 DolphinDB 的内置函数。

更多 TA-lib 指标函数请参考 DolphinDB 的 [ta 模块](https://dolphindb.net/dolphindb/dolphindbmodules/-/tree/master/ta)。
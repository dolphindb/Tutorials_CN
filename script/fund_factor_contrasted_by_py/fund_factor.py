import dolphindb as ddb
import numpy as np
import pandas as pd
import scipy.stats as st
import statsmodels.api as sm
import time
from datetime import datetime
from joblib import Parallel, delayed

s = ddb.session()
s.connect("127.0.0.1", 8848, "admin", "123456")
def getAnnualReturn(value):
    return pow(1 + ((value[-1] - value[0])/value[0]), 252/730)-1

def getAnnualVolatility(value):
    diff_value = np.diff(value)
    rolling_value = np.roll(value, 1)
    rolling_value = np.delete(rolling_value, [0])
    return np.std(np.true_divide(diff_value, rolling_value)) * np.sqrt(252)

def getAnnualSkew(value):
    diff_value = np.diff(value)
    rolling_value = np.roll(value, 1)
    rolling_value = np.delete(rolling_value, [0])
    return st.skew(np.true_divide(diff_value, rolling_value))

def getAnnualKur(value):
    diff_value = np.diff(value)
    rolling_value = np.roll(value, 1)
    rolling_value = np.delete(rolling_value, [0])
    return st.kurtosis(np.true_divide(diff_value, rolling_value), fisher=False)

def getSharp(value):
    return (getAnnualReturn(value) - 0.03)/getAnnualVolatility(value) if getAnnualVolatility(value) != 0 else 0

def getTrackError(value, price):
    diff_price = np.diff(price)
    rolling_price = np.roll(price, 1)
    rolling_price = np.delete(rolling_price, [0])
    diff_value = np.diff(value)
    rolling_value = np.roll(value, 1)
    rolling_value = np.delete(rolling_value, [0])
    return np.std(np.true_divide(diff_value, rolling_value)-np.true_divide(diff_price, rolling_price))

def getIndexFundAnReturn(price):
    return pow(1 + ((price[-1] - price[0]) / price[0]), 252 / 487) - 1

def getInforRatio(value, price):
    return (pow(1 + ((value[-1] - value[0]) / value[0]), 252 / 487) - 1 - getIndexFundAnReturn(price))/(getTrackError(value, price) * np.sqrt(252))

def getVar(value):
    diff_value = np.diff(value)
    rolling_value = np.roll(value, 1)
    rolling_value = np.delete(rolling_value, [0])
    res = np.percentile(np.true_divide(diff_value, rolling_value), 5)
    res = max(-res, 0)
    return res

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

def getHM2(value, price):
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
    return model.params[1]

def getHM3(value, price):
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
    return model.params[2]

def main(li):
    value = np.array(li["value"])
    price = np.array(li["price"])
    log = np.array(li["log"])
    getAnnualReturn(value)
    getAnnualVolatility(value)
    getAnnualSkew(value)
    getAnnualKur(value)
    getSharp(value)
    getTrackError(value, price)
    getInforRatio(value, price)
    getVar(value)
    getHM1(value, price)
    calHurst(log, 2)

def getLog(value):
    diff_value = np.diff(value)
    rolling_value = np.roll(value, 1)
    rolling_value = np.delete(rolling_value, [0])
    return np.insert(np.true_divide(diff_value, rolling_value), 0, np.nan)

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
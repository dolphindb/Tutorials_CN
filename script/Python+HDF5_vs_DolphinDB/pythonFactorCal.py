"""
Python + hdf5  多因子并行计算
"""
import os
import numpy as np
import pandas as pd
import time
from joblib import Parallel, delayed
import dolphindb as ddb


# flow 因子
def flow(df):
    buy_vol_ma = np.round(df['BidSize1'].rolling(60).mean(), decimals=5)
    sell_vol_ma = np.round((df['OfferSize1']).rolling(60).mean(), decimals=5)
    buy_prop = np.where(abs(buy_vol_ma + sell_vol_ma) < 0, 0.5, buy_vol_ma / (buy_vol_ma + sell_vol_ma))
    spd = df['OfferPX1'].values - df['BidPX1'].values
    spd = np.where(spd < 0, 0, spd)
    spd = pd.DataFrame(spd)
    spd_ma = np.round((spd).rolling(60).mean(), decimals=5)
    return np.where(spd_ma == 0, 0, pd.DataFrame(buy_prop) / spd_ma)


# 逐行求加权平均(w只有一行)
def rowWavg(x, w):
    rows = x.shape[0]
    res = [[0]*rows]
    for row in range(rows):
        res[0][row] = np.average(x[row], weights=w)
    res = np.array(res)
    return res
# 逐行求内积
def rowWsum(x, y):
    rows = x.shape[0]
    res = [[0]*rows]
    for row in range(rows):
        res[0][row] = np.dot(x[row],y[row])
    res = np.array(res)
    return res

def mathWghtCovar(x, y, w):
    v = (x - rowWavg(x, w).T)*(y - rowWavg(y, w).T)
    return rowWavg(v, w)
# 无状态因子
def mathWghtSkew(x, w):
    x_var = mathWghtCovar(x, x, w)
    x_std = np.sqrt(x_var)
    x_1 = x - rowWavg(x, w).T
    x_2 = x_1*x_1
    len = np.size(w)
    adj = np.sqrt((len - 1) * len) / (len - 2)
    skew = rowWsum(x_2, x_1) / (x_var*x_std)*adj / len
    return np.where(x_std == 0, 0, skew)

# 读取单个hdf5文件
def loadData(path):
    store = pd.HDFStore(path, mode='r')
    data = store["Table"]
    store.close()
    return data
# 读取hdf 格式hdf5数据
def loadDataSpec(path,flag):
    if flag==0:
        df = pd.read_hdf(path, 'df_key')
    else:
        df = pd.read_hdf(path, 'df_key',columns=["SecurityID","dbtime","BidPX1","BidPX2","BidPX3","BidPX4","BidPX5","BidPX6","BidPX7","BidPX8","BidPX9","BidPX10","OfferPX1","BidSize1","OfferSize1"])
    return df

# 并行任务（按股票）
def ParallelBySymbol(SecurityIDs,dirPath):
    for SecurityID in SecurityIDs:
        sec_data_list=[]
        for date in os.listdir(dirPath):
            filepath = os.path.join(dirPath,str(date),"data_"+str(date) + "_" + str(SecurityID) + ".h5")
            sec_data_list.append(loadData(filepath))

        df=pd.concat(sec_data_list)
        df_flow_res = flow(df)
        w = np.array([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        pxs = np.array(df[["BidPX1","BidPX2","BidPX3","BidPX4","BidPX5","BidPX6","BidPX7","BidPX8","BidPX9","BidPX10"]])
        np.seterr(divide='ignore', invalid='ignore')
        df_skew_res = mathWghtSkew(pxs,w)

    print("共计算"+str(len(SecurityIDs))+"标的")


# # 从第一个文件夹取股票列表
def getSecList(path):
    first_dir = os.path.join(path, os.listdir(path)[0])
    sec_list = []
    for date in os.listdir(first_dir):
        sec_list.append(date[14:20])
    return pd.Series(sec_list)


pathDir = "D:\\tmp\hdf5data"
# pathDir ="/ssd/ssd4/cydatafile/batchdata"
SecurityIDs=getSecList(pathDir)
print("共需计算 "+ str(SecurityIDs.size)+" 只股票")
# 按股票并行
start = time.time()
# 并行度
n = 1
#按并行度拆分成组
SecurityIDs_splits = np.array_split(SecurityIDs, n)

Parallel(n_jobs=n)(delayed(ParallelBySymbol)(SecurityIDs,pathDir) for SecurityIDs in SecurityIDs_splits)
end = time.time()
print("总耗时 "+str(round((end - start)*1000,3))+"ms")


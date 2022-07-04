import dolphindb as ddb
import numpy as np
import pandas as pd
import time


s = ddb.session()
s.connect("ip", {port}, "admin", "123456")
vwap=s.run("vwap1")
open=s.run("open1")
vol=s.run("vol1")
vwap.set_index("tradetime", inplace=True)
open.set_index("tradetime", inplace=True)
vol.set_index("tradetime", inplace=True)

def myrank(x):
    return ((x.rank(axis=1,method='min'))-1)/x.shape[1]

def imin(x):
    return np.where(x==min(x))[0][0]


def rank(x):
    s = pd.Series(x)
    return (s.rank(ascending=True, method="min")[len(s)-1])-1


def alpha98(vwap, open, vol):
    return myrank(vwap.rolling(5).corr(vol.rolling(5).mean().rolling(26).sum()).rolling(7).apply(lambda x: np.sum(np.arange(1, 8)*x)/np.sum(np.arange(1, 8)))) - myrank((9 - myrank(open).rolling(21).corr(myrank(vol.rolling(15).mean())).rolling(9).apply(imin)).rolling(7).apply(rank).rolling(8).apply(lambda x: np.sum(np.arange(1, 9)*x)/np.sum(np.arange(1, 9))))


start_time = time.time()
re=alpha98(vwap, open, vol)
print("--- %s seconds ---" % (time.time() - start_time))
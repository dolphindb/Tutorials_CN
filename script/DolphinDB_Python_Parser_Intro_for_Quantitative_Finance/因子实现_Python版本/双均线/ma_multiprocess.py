import pandas as pd
import os
def signal_ma(data_chunk, short, long):
    data_chunk['ma_5'] = data_chunk['CLOSE_PRICE_1'].fillna(0).rolling(int(short)).mean()
    data_chunk['ma_20'] = data_chunk['CLOSE_PRICE_1'].fillna(0).rolling(int(long)).mean()
    data_chunk['pre_ma5'] = data_chunk['ma_5'].shift(1)
    data_chunk['pre_ma20'] =  data_chunk['ma_20'].shift(1)
    data_chunk['signal'] = 0
    data_chunk.loc[((data_chunk.loc[:,'pre_ma5']< data_chunk.loc[:,'pre_ma20'])& (data_chunk.loc[:,'ma_5'] > data_chunk.loc[:,'ma_20'])), "signal"] = 1
    data_chunk.loc[((data_chunk.loc[:,'pre_ma5']> data_chunk.loc[:,'pre_ma20']) & (data_chunk.loc[:,'ma_5'] < data_chunk.loc[:,'ma_20'])), "signal"] = -1
    return data_chunk

def process_group(group):
    stock_code = group['SECURITY_ID'].iloc[0]
    print(f"正在运行股票： {stock_code} in process {os.getpid()}")
    result_group = signal_ma(group,5,10)
    return result_group
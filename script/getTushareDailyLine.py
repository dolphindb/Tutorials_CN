import datetime
import tushare as ts
import pandas as pd
import numpy as np
import dolphindb as ddb
pro=ts.pro_api('XXXXXXXXXX')
s=ddb.session()
s.connect("localhost",8711,"admin","123456")
t1=s.loadTable(tableName="hushen_daily_line",dbPath="dfs://tushare")
def dateRange(beginDate,endDate):
    dates=[]
    dt=datetime.datetime.strptime(beginDate,"%Y%m%d")
    date=beginDate[:]
    while date <= endDate:
        dates.append(date)
        dt=dt + datetime.timedelta(1)
        date=dt.strftime("%Y%m%d")
    return dates

print("import hushen_daily_line")
for dates in dateRange('20080101','20171231'):
    print(dates)
    df=pro.daily(trade_date=dates)
    df['trade_date']=pd.to_datetime(df['trade_date'])
    if len(df):
        t1.append(s.table(data=df))
        print(t1.rows)

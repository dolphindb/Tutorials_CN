import dolphindb as ddb
import pandas as pd
import os
# 从DolphinDB筛选股票快照写入到HDF5文件中
# 循环生成数据文件
def saveByHDFStore(path,df):
    store = pd.HDFStore(path)
    # 写入
    store["Table"] = df
    # 关闭句柄
    store.close()
# 通过to_HDF方法保存HDF5文件
def saveByHDF(path, df):
    df.to_hdf(path, 'df_key', format='t', data_columns=True)

def generateHdf5FilesFromDDB(savedir,TradeDates,ip,port,user,pwd):
    s = ddb.session()
    s.connect(ip, port,user,pwd)
    tb = s.loadTable(tableName="Snap", dbPath="dfs://LEVEL2_SZ")
    # 从日期第一天取股票列表
    SecurityIDs = (tb.select("count(*)").where("TradeDate =" + str(TradeDates[1]).replace('-', '.')).groupby(
        "SecurityID").toDF()).SecurityID[0:10]

    for iterDate in TradeDates:
        iterDate = str(iterDate).replace('-','.')
        # 每个日期创建一个目录
        path = os.path.join(savedir,iterDate.replace('.',''));
        if not os.path.exists(path):
            os.mkdir(path)
        for iterSecurityID in SecurityIDs:
            iterSecurityID = str(iterSecurityID)
            # 待保存数据
            savedata = tb.select("*").where("TradeDate =" + iterDate + ",SecurityID =`" + iterSecurityID).toDF()
            singlePath = os.path.join(path,"data_"+iterDate.replace('.','')+"_"+iterSecurityID+".h5")
            # 保存文件
            saveByHDFStore(singlePath,savedata)
            # saveByHDF(singlePath,savedata)

if __name__ == "__main__":
    TradeDates = pd.Series({1: "2020-01-02", 2: "2020-01-03", 3: "2020-01-06"})
    savedir = "D:\\tmp\hdf5data\special"
    # savedir ="/ssd/ssd4/datafile/batchdata"
    generateHdf5FilesFromDDB(savedir,TradeDates,"192.168.100.3",8849,"admin","123456")

import dolphindb as ddb
import pandas as pd
import numpy as np
import dolphindb.settings as keys
from datetime import datetime
import glob
# from functions import *
import sys
from threading import Event
from sklearn.linear_model import LinearRegression

s = ddb.session()
s.connect("115.239.209.121", 50848, "admin", "123456")
ss = """snapshotTB=select* from loadTable("dfs://level_2","snapshot") where date(DateTime)=2022.04.14 and SecurityID in [`600000.SH,`000001.SZ]"""
s.run(ss)
df = s.run("snapshotTB")





def timeWeightedOrderSlope(df):
    '''
    时间加权订单斜率
    :param df:
    :return:
    '''
    df = df.copy()
    df["Bid"] = df["Bid"].apply(lambda x: np.array(x.tolist()).T[0])
    df["BidQty"] = df["BidQty"].apply(lambda x: np.array(x.tolist()).T[0])
    df["Ask"] = df["Ask"].apply(lambda x: np.array(x.tolist()).T[0])
    df["AskQty"] = df["AskQty"].apply(lambda x: np.array(x.tolist()).T[0])
    df["Bid"] = df["Bid"].fillna(0)
    df["Ask"] = df["Ask"].fillna(0)
    df.loc[df.Bid == 0, "Bid"] = df.loc[df.Bid == 0, "Ask"]
    df.loc[df.Ask == 0, "Ask"] = df.loc[df.Ask == 0, "Bid"]
    df["LogQuoteSlope"] = (np.log(df.Ask) - np.log(df.Bid)) / (
            np.log(df.AskQty) - np.log(df.BidQty))
    df["LogQuoteSlope"] = df["LogQuoteSlope"].replace(np.inf, np.nan)
    df["LogQuoteSlope"] = df.groupby("SecurityID")["LogQuoteSlope"].apply(lambda x: x.fillna(method="ffill"))
    df["LogQuoteSlope"] = df.groupby("SecurityID")["LogQuoteSlope"].apply(lambda x: x.rolling(20, 1).mean())
    return df[["DateTime", "SecurityID", "LogQuoteSlope"]].fillna(0)


def wavgSOIR(df, lag=20):
    '''
     加权平均订单失衡率因子
    :param df:
    :param lag:
    :return:
    '''

    df = df.copy()
    df["tmp"] = 0.0
    for i in range(1, 10):
        a = df["BidQty"].apply(lambda x: np.array(x.tolist()).T[i]) * 1.0
        b = df["AskQty"].apply(lambda x: np.array(x.tolist()).T[i]) * 1.0
        df["tmp"] = df["tmp"] + (a-b)/(a +b) * (11 - i)
    df["Imbalance"] = df["tmp"] /sum(range(1,11))

    df["Imbalance"] = df.groupby("SecurityID")["Imbalance"].apply(lambda x: x.fillna(method="ffill")).fillna(0)
    df["pre"] = df.groupby("SecurityID")["Imbalance"].shift(-1).fillna(0)
    df["mean"] = df.groupby("SecurityID")["pre"].apply(lambda x: x.rolling(lag - 1, 2).mean())
    df["pre"] = df["pre"] * 10000000000.
    df["std"] = df.groupby("SecurityID")["pre"].apply(lambda x: x.rolling(lag - 1, 2).std() * 10000000000.)
    df["Imbalance"] = (df["Imbalance"].fillna(0) - df["mean"].fillna(0)) / df["std"]
    df.loc[df["std"] < 0.00000001, "Imbalance"] = np.nan
    df["Imbalance"] = df.groupby("SecurityID")["Imbalance"].apply(lambda x: x.fillna(method="ffill"))
    return df[["DateTime", "SecurityID", "Imbalance"]].fillna(0)


def traPriceWeightedNetBuyQuoteVolumeRatio(df, lag=20):
    '''
    成交价加权净委买比例
    :param df:
    :param lag:
    :return:
    '''
    df = df.copy()
    df["Bid0"] = df["Bid"].apply(lambda x: np.array(x.tolist()).T[0]).fillna(0)
    df["BidQty0"] = df["BidQty"].apply(lambda x: np.array(x.tolist()).T[0]).fillna(0)
    df["Ask0"] = df["Ask"].apply(lambda x: np.array(x.tolist()).T[0]).fillna(0)
    df["AskQty0"] = df["AskQty"].apply(lambda x: np.array(x.tolist()).T[0]).fillna(0)
    df["preBid0"] = df.groupby("SecurityID")["Bid0"].shift(1)
    df["preBidQty0"] = df.groupby("SecurityID")["BidQty0"].shift(1)
    df["preAsk0"] = df.groupby("SecurityID")["Ask0"].shift(1)
    df["preAskQty0"] = df.groupby("SecurityID")["AskQty0"].shift(1)
    df["preTotalValueTrade"] = df.groupby("SecurityID")["TotalValueTrade"].shift(1)
    df["preTotalVolumeTrade"] = df.groupby("SecurityID")["TotalVolumeTrade"].shift(1)
    df["deltasTotalVolumeTrade"] = df["TotalVolumeTrade"] - df["preTotalVolumeTrade"]
    df["deltasTotalValueTrade"] = df["TotalValueTrade"] - df["preTotalValueTrade"]
    df["avgprice"] = df["deltasTotalValueTrade"] / df["deltasTotalVolumeTrade"]
    df["mavgprice"] = df.groupby("SecurityID")["avgprice"].apply(lambda x: x.rolling(lag, 1).sum())
    df["bidchg"] = df["BidQty0"] - df["preBidQty0"]
    df.loc[np.round(df.Bid0 - df.preBid0, 2) > 0, "bidchg"] = df.loc[
        np.round(df.Bid0 - df.preBid0, 2) > 0, "BidQty0"]
    df.loc[np.round(df.Bid0 - df.preBid0, 2) < 0, "bidchg"] = -1. * df.loc[
        np.round(df.Bid0 - df.preBid0, 2) < 0, "preBidQty0"]
    df["offerchg"] = df["AskQty0"] - df["preAskQty0"]
    df.loc[np.round(df.Ask0 - df.preAsk0, 2) > 0, "offerchg"] = df.loc[
        np.round(df.Ask0 - df.preAsk0, 2) > 0, "preAskQty0"]
    df.loc[np.round(df.Ask0 - df.preAsk0, 2) < 0, "offerchg0"] = df.loc[
        np.round(df.Ask0 - df.preAsk0, 2) < 0, "AskQty0"]
    df.loc[(np.round(df.Ask0 - df.preAsk0, 2) < 0) & (np.round(df.Ask0, 2) == 0), "offerchg"] = \
        df.loc[
            (np.round(df.Ask0 - df.preAsk0, 2) < 0) & (
                    np.round(df.Ask0, 2) == 0), "preAskQty0"]
    df.loc[
        (np.round(df.Ask0 - df.preAsk0, 2) > 0) & (np.round(df.preAsk0, 2) == 0), "offerchg"] = \
        df.loc[
            (np.round(df.Ask0 - df.preAsk0, 2) > 0) & (
                    np.round(df.preAsk0, 2) == 0), "AskQty0"]
    df["quoteslope"] = (df["bidchg"] - df["offerchg"]) / df[["bidchg", "offerchg"]].sum() * df["avgprice"]
    df["quoteslope"] = df.groupby("SecurityID")["quoteslope"].apply(lambda x: x.rolling(lag, 1).sum())
    df["quoteslope"] = df["quoteslope"] / df["mavgprice"]
    return df[["DateTime", "SecurityID", "quoteslope"]].fillna(0)


def level10_InferPriceTrend(df, lag1=60, lag2=20):
    '''
    十档买卖委托均价线性回归斜率
    :param df:
    :param lag1:
    :param lag2:
    :return:
    '''
    df = df.copy()
    df["amount"] = 0.
    df["qty"] = 0.
    for i in range(0, 10):
        df["Bid" + str(i)] = df["Bid"].apply(lambda x: np.array(x.tolist()).T[i]) * 1.0 * df["BidQty"].apply(
            lambda x: np.array(x.tolist()).T[i])
        df["Offer" + str(i)] = df["Ask"].apply(lambda x: np.array(x.tolist()).T[i]) * df["AskQty"].apply(
            lambda x: np.array(x.tolist()).T[i])
        df["amount"] = df[["amount", "Bid" + str(i), "Offer" + str(i)]].sum()
        df["tmpQty"] = df["BidQty"].apply(lambda x: np.array(x.tolist()).T[i]).fillna(0) + df[
            "AskQty"].apply(lambda x: np.array(x.tolist()).T[i]).fillna(0)
        df["qty"] = df[["qty", "tmpQty"]].sum()
    df["inferprice"] = df["amount"] / df["qty"]
    df.loc[(df.Bid0 <= 0) | (df.Offer0 <= 0), "inferprice"] = np.nan

    def f(x):
        return LinearRegression().fit(x, np.array([i for i in range(1, len(x) + 1)])).coef_

    df["inferprice"] = df.groupby("SecurityID")["inferprice"].apply(lambda x: x.rolling(lag1 - 1, 1).apply(f))
    df["inferprice"] = df["inferprice"].fillna(0)
    df["inferprice"] = df.groupby("SecurityID")["inferprice"].apply(lambda x: x.rolling(lag2, 1).mean())
    return df["inferprice"].fillna(0)


def level10_Diff(df, lag=20):
    '''
    十档委买增额
    :param df:
    :param lag:
    :return:
    '''
    df["preBid"] = df.groupby("SecurityID")["Bid"].apply(lambda x: x.shift(1))
    df["preBidQty"] = df.groupby("SecurityID")["BidQty"].apply(lambda x: x.shift(1))

    def f(x):
        tmp = pd.DataFrame(np.array(x.tolist())).T.fillna(0)
        tmp.columns = ["Bid", "BidQty", "preBid", "preBidQty"]
        tmp = tmp[["Bid", "BidQty", "preBid", "preBidQty"]].fillna(0)
        pmin = max([int(min((10000 * (tmp.Bid.tolist())))), int(min((10000 * (tmp.preBid.tolist()))))])
        pmax = max([int(max((10000 * (tmp.Bid.tolist())))), int(max((10000 * (tmp.preBid.tolist()))))])
        tmp1 = tmp[((tmp.Bid * 10000) >= pmin) & ((tmp.Bid * 10000) <= pmax)][["Bid", "BidQty"]]
        tmp2 = tmp[((tmp.preBid * 10000) >= pmin) & ((tmp.preBid * 10000) <= pmax)][
            ["preBid", "preBidQty"]]
        return (tmp1["Bid"] * tmp1["BidQty"]).sum() - (tmp2["preBid"] * tmp2["preBidQty"]).sum()

    df["amtDiff"] = df[["Bid", "BidQty", "preBid", "preBidQty"]].apply(f, axis=1)
    df["amtDiff"] = df.groupby("SecurityID")["amtDiff"].apply(lambda x: x.rolling(lag, 1).mean())
    return df[["DateTime", "SecurityID", "amtDiff"]].fillna(0)


def calcSZOrderValue(df1, df2):
    '''
    委买委卖金额
    :param df1:
    :param df2:
    :return:
    '''
    df1 = df1.copy()
    tmp = df1[df1.Price == 0]
    tmp = tmp.sort_values(["ApplSeqNum"])
    df1 = df1[df1.Price > 0]
    df2 = df2.copy()
    tmp2 = df2[["SecurityID", "ApplSeqNum", "TradePrice"]]
    tmp2 = tmp2[(tmp2.ApplSeqNum > 0) & (tmp2.TradePrice > 0)]
    tmp2 = tmp2.sort_values(["ApplSeqNum"])
    tmp = pd.merge_asof(tmp, tmp2, on="ApplSeqNum", by="SecurityID")
    tmp["Price"] = tmp["TradePrice"]
    tmp.drop("TradePrice", axis=1, inplace=True)
    df1 = df1.append(tmp)
    df1["total"] = df1.Price * df1.OrderQty
    tmp1 = df1[df1.side == "B"].set_index("DateTime").groupby("SecurityID")[["total"]].apply(
        lambda x: x.resample('1min').sum())
    tmp2 = df1[df1.side == "S"].set_index("DateTime").groupby("SecurityID")[["total"]].apply(
        lambda x: x.resample('1min').sum())
    tmp1.columns = ["BuyOrderValue"]
    tmp2.columns = ["SellOrderValue"]
    tmp1 = pd.merge(tmp1.reset_index(), tmp2.reset_index(), on=["SecurityID", "DateTime"], how="outer")
    return tmp1.fillna(0)


def calcSZwithdrawOrderValue(df1, df2):
    '''
    买卖撤单金额
    :param df1:
    :param df2:
    :return:
    '''
    df1 = df1.copy()
    df2 = df2[["SecurityID", "SeqNo", "Price"]]
    buywithdrawOrder = pd.merge(df1[df1.BidApplSeqNum > 0], df2, how="left", left_on=["SecurityID", "BuyNo"],
                                right_on=["SecurityID", "SellNo"])
    sellwithdrawOrder = pd.merge(df1[df1.BidApplSeqNum > 0], df2, how="left", left_on=["SecurityID", "BuyNo"],
                                 right_on=["SecurityID", "SellNo"])
    buywithdrawOrder["OrderValue"] = buywithdrawOrder["Price"] * buywithdrawOrder["TradeQty"]
    sellwithdrawOrder["OrderValue"] = sellwithdrawOrder["Price"] * sellwithdrawOrder["TradeQty"]
    buywithdrawOrder = buywithdrawOrder.set_index("DateTime").groupby("SecurityID")["OrderValue"].apply(
        lambda x: x.resample('1min').sum())
    sellwithdrawOrder = sellwithdrawOrder.set_index("DateTime").groupby("SecurityID")["OrderValue"].apply(
        lambda x: x.resample('1min').sum())
    buywithdrawOrder.columns = ["BuywithdrawOrderValue"]
    sellwithdrawOrder.columns = ["SellwithdrawOrderValue"]
    tmp1 = pd.merge(buywithdrawOrder.reset_index(), sellwithdrawOrder.reset_index(), on=["SecurityID", "DateTime"],
                    how="outer")
    return tmp1.fillna(0)


def singleOrderAveragePrice(df):
    '''
    单笔订单主动买入卖出均价
    :param df:
    :return:
    '''
    def ff(data, flag="B"):
        if (flag == "B"):
            temp = data[data.BuyNo > data.SellNo]
            totolqty = temp.groupby("BuyNo")["TradeQty"].sum()
            totolMoney = temp.groupby("BuyNo").apply(lambda x: (x.TradePrice * 1.0 * x.TradeQty).sum())
        else:
            temp = data[data.BuyNo < data.SellNo]
            totolqty = temp.groupby("SellNo")["TradeQty"].sum()
            totolMoney = temp.groupby("SellNo").apply(lambda x: (x.TradePrice * 1.0 * x.TradeQty).sum())
        return (totolMoney / totolqty).mean()

    tmp1 = df[df.TradePrice > 0].groupby("SecurityID").apply(lambda x: ff(x, flag="B"))
    tmp2 = df[df.TradePrice > 0].groupby("SecurityID").apply(lambda x: ff(x, flag="S"))
    tmp1.columns = ["ActBuySingleOrderAveragePriceFactor"]
    tmp2.columns = ["ActSellSingleOrderAveragePriceFactor"]
    res = pd.merge(tmp1.reset_index(), tmp2.reset_index(), on="SecurityID", how="outer")
    res["DateTime"] = df.DateTime.max()
    return res.fillna(0)


def delayedTradeOrder(df1, df2):
    '''
    股票延时成交订单因子
    :param df1:
    :param df2:
    :return:
    '''
    df1 = df1[df1.TradePrice > 0]
    df2 = df2.drop_duplicates(['SecurityID', 'SeqNo'])
    tmpBid = df1.merge(df2, how="left", left_on=['SecurityID', 'BuyNo'], right_on=['SecurityID', 'SeqNo'])
    tmpBid = tmpBid.groupby(["SecurityID", "BuyNo"]).agg(TradeTime=('DateTime_x', max),
                                                                 TransactTime=('DateTime_y', min),
                                                                 TradeQty=('TradeQty', sum))

    tmpBid = tmpBid[(tmpBid.TradeTime - tmpBid.TransactTime).apply(lambda x: x.seconds) > 60]
    tmpBid = tmpBid.reset_index().groupby("SecurityID").agg(DelayedTradeBuyOrderNum=("BuyNo", len),
                                                            DelayedTradeBuyOrderQty=("TradeQty", sum))
    tmpOffer = df1.merge(df2, how="left", left_on=['SecurityID', 'SellNo'],
                         right_on=['SecurityID', 'SeqNo'])
    tmpOffer = tmpOffer.groupby(["SecurityID", "SellNo"]).agg(TradeTime=('DateTime_x', max),
                                                                       TransactTime=('DateTime_y', min),
                                                                       TradeQty=('TradeQty', sum))
    tmpOffer = tmpOffer[(tmpOffer.TradeTime - tmpOffer.TransactTime).apply(lambda x: x.seconds) > 60]
    tmpOffer = tmpOffer.reset_index().groupby("SecurityID").agg(DelayedTradeSellOrderNum=("SellNo", len),
                                                                DelayedTradeSellOrderQty=("TradeQty", sum))
    res = pd.merge(tmpBid.reset_index(), tmpOffer.reset_index(), on="SecurityID", how="outer")
    res["DateTime"] = df1.DateTime.max()
    return res.fillna(0)


if __name__ == '__main__':

    t0 = datetime.now()
    print("-----------TimeWeightedOrderSlope-------------------------")
    t1 = datetime.now()
    res = timeWeightedOrderSlope(df)
    t = datetime.now() - t1
    print(t)
    ###0:00:00.116201
    ###0:00:00.821459
    t = t1 + t
    print("-----------WavgSOIR-------------------------")
    t1 = datetime.now()
    res=wavgSOIR(df, lag=20)
    t = datetime.now() - t1
    print(t)
    print("-----------TraPriceWeightedNetBuyQuoteVolumeRatio-------------------------")
    t1 = datetime.now()
    res = traPriceWeightedNetBuyQuoteVolumeRatio(df)
    t1 = datetime.now() - t1
    print(t1)
    ##0:00:00.146711
    t = t1 + t
    print("-----------Level10_InferPriceTrend-------------------------")
    t1 = datetime.now()
    res = level10_InferPriceTrend(df)
    t1 = datetime.now() - t1
    print(t1)
    ##0:00:01.257858
    t = t1 + t

    print("-----------Level10_Diff-------------------------")


    def tof(x):
        try:
            return float(str(x))
        except:
            return np.nan


    df["Bid"] = df[["Bid"]].apply(tof, axis=1)
    df["BidQty"] = df[["BidQty"]].apply(tof, axis=1)
    t1 = datetime.now()
    res = level10_Diff(df)
    t1 = datetime.now() - t1
    print(t1)
    # 0:03:33.882130
    t = t1 + t

    print("-----------总耗时1-------------------------")
    print(t)

    print("\n\n-----------开始加载逐笔委托数据。。。。。。")
    entrustTB = s.loadTable("entrust", "dfs://level_2")
    entrustTB = entrustTB.select("SecurityID,DateTime,Price,OrderQty,SeqNo,OrderType,side ").where(
        "DateTime.date()=2022.04.14").where("""SecurityID in ["000001.SZ","000040.SZ"]""").toDF()
    print("-----------开始加载逐笔成交数据。。。。。。")
    tradeTB = s.loadTable("trade", "dfs://level_2")
    tradeTB = tradeTB.select("* ").where("DateTime.date()=2022.04.14").where(
        """SecurityID in ["000001.SZ","000040.SZ"];""").toDF()

    print("-----------数据加载完成")
    print(1234)
    print("-----------CalcSZOrderValue-------------------------")
    t1 = datetime.now()
    res=calcSZOrderValue(entrustTB, tradeTB)
    print(datetime.now() - t1)
    t1 = datetime.now()
    print("-----------CalcSZwithdrawOrderValue-------------------------")
    t1 = datetime.now()
    df1 = tradeTB[tradeTB.ExecType == 52].copy()
    df2 = entrustTB[entrustTB.Price > 0].copy()
    res = calcSZwithdrawOrderValue(df1, df2)
    t1 = datetime.now()-t1
    print(t1)
    print("-----------SingleOrderAveragePrice-------------------------")
    t1 = datetime.now()
    res = singleOrderAveragePrice(tradeTB)
    print(datetime.now() - t1)
    print("-----------DelayedTradeOrder-------------------------")
    t1 = datetime.now()
    res = delayedTradeOrder(tradeTB, entrustTB)
    print(datetime.now() - t1)

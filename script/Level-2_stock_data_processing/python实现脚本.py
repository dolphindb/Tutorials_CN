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
df = df.rename(columns={"BidPrice": "bid", "BidOrderQty": "bidQty", "OfferPrice": "ask", "OfferOrderQty": "askQty"})


def timeWeightedOrderSlope(df):
    '''
    时间加权订单斜率
    :param df:
    :return:
    '''

    bid = df["bid"].apply(lambda x: np.array(x.tolist()).T[0]).fillna(0)
    bidQty = df["bidQty"].apply(lambda x: np.array(x.tolist()).T[0]).fillna(0)
    ask = df["ask"].apply(lambda x: np.array(x.tolist()).T[0])
    askQty = df["askQty"].apply(lambda x: np.array(x.tolist()).T[0])
    bid[bid == 0] = ask[bid == 0]
    ask[ask == 0] = bid[ask == 0]
    LogQuoteSlope = (np.log(ask) - np.log(bid)) / (
            np.log(askQty) - np.log(bidQty))
    LogQuoteSlope = LogQuoteSlope.replace(np.inf, np.nan)
    tmp = df[["DateTime", "SecurityID"]]
    tmp.loc[:,"LogQuoteSlope"] = LogQuoteSlope
    tmp.loc[:,"LogQuoteSlope"]  = tmp.groupby("SecurityID")["LogQuoteSlope"].apply(lambda x: x.fillna(method="ffill"))
    tmp.loc[:,"LogQuoteSlope"] = tmp.groupby("SecurityID")["LogQuoteSlope"].apply(lambda x: x.rolling(20, 1).mean())
    return tmp[["DateTime", "SecurityID", "LogQuoteSlope"]].fillna(0)


def wavgSOIR(df, lag=20):
    '''
     加权平均订单失衡率因子
    :param df:
    :param lag:
    :return:
    '''

    temp = df[["DateTime","SecurityID"]]
    temp["tmp"] = 0.0
    for i in range(1, 10):
        a = df["bidQty"].apply(lambda x: np.array(x.tolist()).T[i]) * 1.0
        b = df["askQty"].apply(lambda x: np.array(x.tolist()).T[i]) * 1.0
        temp["tmp"] = temp["tmp"] + (a - b) / (a + b) * (11 - i)
    temp["Imbalance"] = temp["tmp"] / sum(range(1, 11))

    temp["Imbalance"] = temp.groupby("SecurityID")["Imbalance"].apply(lambda x: x.fillna(method="ffill")).fillna(0)
    temp["pre"] = temp.groupby("SecurityID")["Imbalance"].shift(-1).fillna(0)
    temp["mean"] = temp.groupby("SecurityID")["pre"].apply(lambda x: x.rolling(lag - 1, 2).mean())
    temp["pre"] = temp["pre"] * 10000000000.
    temp["std"] = temp.groupby("SecurityID")["pre"].apply(lambda x: x.rolling(lag - 1, 2).std() * 10000000000.)
    temp["Imbalance"] = (temp["Imbalance"].fillna(0) - temp["mean"].fillna(0)) / temp["std"]
    temp.loc[temp["std"] < 0.00000001, "Imbalance"] = np.nan
    temp["Imbalance"] = temp.groupby("SecurityID")["Imbalance"].apply(lambda x: x.fillna(method="ffill"))
    return temp[["DateTime", "SecurityID", "Imbalance"]].fillna(0)


def traPriceWeightedNetBuyQuoteVolumeRatio(df, lag=20):
    '''
    成交价加权净委买比例
    :param df:
    :param lag:
    :return:
    '''
    temp = df[["DateTime","SecurityID","TotalVolumeTrade","TotalValueTrade"]]
    temp["bid0"] = df["bid"].apply(lambda x: np.array(x.tolist()).T[0]).fillna(0)
    temp["bidQty0"] = df["bidQty"].apply(lambda x: np.array(x.tolist()).T[0]).fillna(0)
    temp["ask0"] = df["ask"].apply(lambda x: np.array(x.tolist()).T[0]).fillna(0)
    temp["askQty0"] = df["askQty"].apply(lambda x: np.array(x.tolist()).T[0]).fillna(0)
    temp["prebid0"] = temp.groupby("SecurityID")["bid0"].shift(1)
    temp["prebidQty0"] = temp.groupby("SecurityID")["bidQty0"].shift(1)
    temp["preask0"] = temp.groupby("SecurityID")["ask0"].shift(1)
    temp["preaskQty0"] = temp.groupby("SecurityID")["askQty0"].shift(1)
    temp["preTotalValueTrade"] = df.groupby("SecurityID")["TotalValueTrade"].shift(1)
    temp["preTotalVolumeTrade"] = df.groupby("SecurityID")["TotalVolumeTrade"].shift(1)
    temp["deltasTotalVolumeTrade"] = temp["TotalVolumeTrade"] - temp["preTotalVolumeTrade"]
    temp["deltasTotalValueTrade"] = temp["TotalValueTrade"] - temp["preTotalValueTrade"]
    temp["avgprice"] = temp["deltasTotalValueTrade"] / temp["deltasTotalVolumeTrade"]
    temp["mavgprice"] = temp.groupby("SecurityID")["avgprice"].apply(lambda x: x.rolling(lag, 1).sum())
    temp["bidchg"] = temp["bidQty0"] - temp["prebidQty0"]
    temp.loc[np.round(temp.bid0 - temp.prebid0, 2) > 0, "bidchg"] =temp.loc[
        np.round(temp.bid0 - temp.prebid0, 2) > 0, "bidQty0"]
    temp.loc[np.round(temp.bid0 - temp.prebid0, 2) < 0, "bidchg"] = -1. * temp.loc[
        np.round(temp.bid0 - temp.prebid0, 2) < 0, "prebidQty0"]
    temp["offerchg"] = temp["askQty0"] - temp["preaskQty0"]
    temp.loc[np.round(temp.ask0 - temp.preask0, 2) > 0, "offerchg"] = temp.loc[
        np.round(temp.ask0 - temp.preask0, 2) > 0, "preaskQty0"]
    temp.loc[np.round(temp.ask0 - temp.preask0, 2) < 0, "offerchg0"] = temp.loc[
        np.round(temp.ask0 - temp.preask0, 2) < 0, "askQty0"]
    temp.loc[(np.round(temp.ask0 - temp.preask0, 2) < 0) & (np.round(temp.ask0, 2) == 0), "offerchg"] = \
        temp.loc[
            (np.round(temp.ask0 - temp.preask0, 2) < 0) & (
                    np.round(temp.ask0, 2) == 0), "preaskQty0"]
    temp.loc[
        (np.round(temp.ask0 - temp.preask0, 2) > 0) & (np.round(temp.preask0, 2) == 0), "offerchg"] = \
        temp.loc[
            (np.round(temp.ask0 - temp.preask0, 2) > 0) & (
                    np.round(temp.preask0, 2) == 0), "askQty0"]
    temp["quoteslope"] = (temp["bidchg"] - temp["offerchg"]) / temp[["bidchg", "offerchg"]].sum() * temp["avgprice"]
    temp["quoteslope"] = temp.groupby("SecurityID")["quoteslope"].apply(lambda x: x.rolling(lag, 1).sum())
    temp["quoteslope"] = temp["quoteslope"] / temp["mavgprice"]
    return temp[["DateTime", "SecurityID", "quoteslope"]].fillna(0)


def level10_InferPriceTrend(df, lag1=60, lag2=20):
    '''
    十档买卖委托均价线性回归斜率
    :param df:
    :param lag1:
    :param lag2:
    :return:
    '''
    temp = df[["DateTime", "SecurityID"]]
    temp["amount"] = 0.
    temp["qty"] = 0.
    for i in range(0, 10):
        temp["bid" + str(i)] = df["bid"].apply(lambda x: np.array(x.tolist()).T[i]) * 1.0 * df["bidQty"].apply(
            lambda x: np.array(x.tolist()).T[i])
        temp["Offer" + str(i)] = df["ask"].apply(lambda x: np.array(x.tolist()).T[i]) * df["askQty"].apply(
            lambda x: np.array(x.tolist()).T[i])
        temp["amount"] = temp[["amount", "bid" + str(i), "Offer" + str(i)]].sum()
        temp["tmpQty"] = df["bidQty"].apply(lambda x: np.array(x.tolist()).T[i]).fillna(0) + df[
            "askQty"].apply(lambda x: np.array(x.tolist()).T[i]).fillna(0)
        temp["qty"] = temp[["qty", "tmpQty"]].sum()
    temp["inferprice"] = temp["amount"] / temp["qty"]
    temp.loc[(temp.bid0 <= 0) | (temp.Offer0 <= 0), "inferprice"] = np.nan

    def f(x):
        return LinearRegression().fit(x, np.array([i for i in range(1, len(x) + 1)])).coef_

    temp["inferprice"] = temp.groupby("SecurityID")["inferprice"].apply(lambda x: x.rolling(lag1 - 1, 1).apply(f))
    temp["inferprice"] = temp["inferprice"].fillna(0)
    temp["inferprice"] = temp.groupby("SecurityID")["inferprice"].apply(lambda x: x.rolling(lag2, 1).mean())
    return temp["inferprice"].fillna(0)


def level10_Diff(df, lag=20):
    '''
    十档委买增额
    :param df:
    :param lag:
    :return:
    '''
    temp=df[["DateTime", "SecurityID","bid","bidQty"]]
    temp["prebid"] = temp.groupby("SecurityID")["bid"].apply(lambda x: x.shift(1))
    temp["prebidQty"] = temp.groupby("SecurityID")["bidQty"].apply(lambda x: x.shift(1))

    def f(x):
        tmp = pd.DataFrame(np.array(x.tolist())).T.fillna(0)
        tmp.columns = ["bid", "bidQty", "prebid", "prebidQty"]
        tmp = tmp[["bid", "bidQty", "prebid", "prebidQty"]].fillna(0)
        pmin = max([int(min((10000 * (tmp.bid.tolist())))), int(min((10000 * (tmp.prebid.tolist()))))])
        pmax = max([int(max((10000 * (tmp.bid.tolist())))), int(max((10000 * (tmp.prebid.tolist()))))])
        tmp1 = tmp[((tmp.bid * 10000) >= pmin) & ((tmp.bid * 10000) <= pmax)][["bid", "bidQty"]]
        tmp2 = tmp[((tmp.prebid * 10000) >= pmin) & ((tmp.prebid * 10000) <= pmax)][
            ["prebid", "prebidQty"]]
        return (tmp1["bid"] * tmp1["bidQty"]).sum() - (tmp2["prebid"] * tmp2["prebidQty"]).sum()

    temp["amtDiff"] = temp[["bid", "bidQty", "prebid", "prebidQty"]].apply(f, axis=1)
    temp["amtDiff"] = temp.groupby("SecurityID")["amtDiff"].apply(lambda x: x.rolling(lag, 1).mean())
    return temp[["DateTime", "SecurityID", "amtDiff"]].fillna(0)


def calcSZOrderValue(df1, df2):
    '''
    委买委卖金额
    :param df1:
    :param df2:
    :return:
    '''
    tmp = df1[df1.Price == 0]
    tmp = tmp.sort_values(["seqNo"])
    tmp2= df1[df1.Price > 0]

    tmp3 = df2[["SecurityID", "seqNo", "TradePrice"]]
    tmp3 = tmp3[(tmp3.seqNo > 0) & (tmp3.TradePrice > 0)]
    tmp3 = tmp3.sort_values(["seqNo"])
    tmp = pd.merge_asof(tmp, tmp3, on="seqNo", by="SecurityID")
    tmp["Price"] = tmp["TradePrice"]
    tmp.drop("TradePrice", axis=1, inplace=True)
    tmp2 = tmp2.append(tmp)
    tmp2["total"] = tmp2.Price * tmp2.OrderQty
    tmp1 = tmp2[tmp2.side == "B"].set_index("DateTime").groupby("SecurityID")[["total"]].apply(
        lambda x: x.resample('1min').sum())
    tmp2 =tmp2[tmp2.side == "S"].set_index("DateTime").groupby("SecurityID")[["total"]].apply(
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
    df2 = df2[["SecurityID", "seqNo", "Price"]]
    buywithdrawOrder = pd.merge(df1[df1.buyNo > 0], df2, how="left", left_on=["SecurityID", "buyNo"],
                                right_on=["SecurityID", "seqNo"])
    sellwithdrawOrder = pd.merge(df1[df1.sellNo > 0], df2, how="left", left_on=["SecurityID", "sellNo"],
                                 right_on=["SecurityID", "seqNo"])
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
            temp = data[data.buyNo > data.sellNo]
            totolqty = temp.groupby("buyNo")["TradeQty"].sum()
            totolMoney = temp.groupby("buyNo").apply(lambda x: (x.TradePrice * 1.0 * x.TradeQty).sum())
        else:
            temp = data[data.buyNo < data.sellNo]
            totolqty = temp.groupby("sellNo")["TradeQty"].sum()
            totolMoney = temp.groupby("sellNo").apply(lambda x: (x.TradePrice * 1.0 * x.TradeQty).sum())
        return (totolMoney / totolqty).mean()

    tmp1 = df[df.TradePrice > 0].groupby("SecurityID").apply(lambda x: ff(x, flag="B"))
    tmp2 = df[df.TradePrice > 0].groupby("SecurityID").apply(lambda x: ff(x, flag="S"))
    tmp1.columns = ["ActBuySingleOrderAvgPriceFactor"]
    tmp2.columns = ["ActSellSingleOrderAvgPriceFactor"]
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
    df2 = df2.drop_duplicates(['SecurityID', 'seqNo'])
    tmpbid = df1.merge(df2, how="left", left_on=['SecurityID', 'buyNo'], right_on=['SecurityID', 'seqNo'])
    tmpbid = tmpbid.groupby(["SecurityID", "buyNo"]).agg(TradeTime=('DateTime_x', max),
                                                         TransactTime=('DateTime_y', min),
                                                         TradeQty=('TradeQty', sum))

    tmpbid = tmpbid[(tmpbid.TradeTime - tmpbid.TransactTime).apply(lambda x: x.seconds) > 60]
    tmpbid = tmpbid.reset_index().groupby("SecurityID").agg(DelayedTradeBuyOrderNum=("buyNo", len),
                                                            DelayedTradeBuyOrderQty=("TradeQty", sum))
    tmpOffer = df1.merge(df2, how="left", left_on=['SecurityID', 'sellNo'],
                         right_on=['SecurityID', 'seqNo'])
    tmpOffer = tmpOffer.groupby(["SecurityID", "sellNo"]).agg(TradeTime=('DateTime_x', max),
                                                              TransactTime=('DateTime_y', min),
                                                              TradeQty=('TradeQty', sum))
    tmpOffer = tmpOffer[(tmpOffer.TradeTime - tmpOffer.TransactTime).apply(lambda x: x.seconds) > 60]
    tmpOffer = tmpOffer.reset_index().groupby("SecurityID").agg(DelayedTradeSellOrderNum=("sellNo", len),
                                                                DelayedTradeSellOrderQty=("TradeQty", sum))
    res = pd.merge(tmpbid.reset_index(), tmpOffer.reset_index(), on="SecurityID", how="outer")
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
    # t = t1 + t
    # print("-----------WavgSOIR-------------------------")
    # t1 = datetime.now()
    # res = wavgSOIR(df, lag=20)
    # t = datetime.now() - t1
    # print(t)
    # print("-----------TraPriceWeightedNetBuyQuoteVolumeRatio-------------------------")
    # t1 = datetime.now()
    # res = traPriceWeightedNetBuyQuoteVolumeRatio(df)
    # t1 = datetime.now() - t1
    # print(t1)
    # ##0:00:00.146711
    # t = t1 + t
    # print("-----------Level10_InferPriceTrend-------------------------")
    # t1 = datetime.now()
    # res = level10_InferPriceTrend(df)
    # t1 = datetime.now() - t1
    # print(t1)
    # ##0:00:01.257858
    # t = t1 + t
    #
    # print("-----------Level10_Diff-------------------------")
    #
    #
    # def tof(x):
    #     try:
    #         return float(str(x))
    #     except:
    #         return np.nan
    #
    #
    # df["bid"] = df[["bid"]].apply(tof, axis=1)
    # df["bidQty"] = df[["bidQty"]].apply(tof, axis=1)
    # t1 = datetime.now()
    # res = level10_Diff(df)
    # t1 = datetime.now() - t1
    # print(t1)
    # # 0:03:33.882130
    # t = t1 + t

    print("-----------总耗时1-------------------------")
    print(t)

    print("\n\n-----------开始加载逐笔委托数据。。。。。。")
    entrustTB = s.loadTable("entrust", "dfs://level_2")
    entrustTB = entrustTB.select("SecurityID,DateTime,Price,OrderQty,ApplSeqNum as seqNo,OrderType,side").where(
        "DateTime.date()=2022.04.14").where("""SecurityID in ["000001.SZ","000040.SZ"]""").toDF()
    print("-----------开始加载逐笔成交数据。。。。。。")
    tradeTB = s.loadTable("trade", "dfs://level_2")
    tradeTB = tradeTB.select("SecurityID,DateTime,ApplSeqNum  as seqNo,BidApplSeqNum as buyNo,OfferApplSeqNum as sellNo,TradeQty,TradePrice,ExecType").where("DateTime.date()=2022.04.14").where(
        """SecurityID in ["000001.SZ","000040.SZ"];""").toDF()

    print("-----------数据加载完成")
    print(1234)
    print("-----------CalcSZOrderValue-------------------------")
    t1 = datetime.now()
    res = calcSZOrderValue(entrustTB, tradeTB)
    print(datetime.now() - t1)
    t1 = datetime.now()
    print("-----------CalcSZwithdrawOrderValue-------------------------")
    t1 = datetime.now()
    df1 = tradeTB[tradeTB.ExecType == 52].copy()
    df2 = entrustTB[entrustTB.Price > 0].copy()
    res = calcSZwithdrawOrderValue(df1, df2)
    t1 = datetime.now() - t1
    print(t1)
    print("-----------SingleOrderAveragePrice-------------------------")
    t1 = datetime.now()
    res = singleOrderAveragePrice(tradeTB)
    print(datetime.now() - t1)
    print("-----------DelayedTradeOrder-------------------------")
    t1 = datetime.now()
    res = delayedTradeOrder(tradeTB, entrustTB)
    print(datetime.now() - t1)

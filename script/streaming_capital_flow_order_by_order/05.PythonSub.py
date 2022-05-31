# -*- coding: utf-8 -*-
"""
DolphinDB python api version: 1.30.17.2
python version: 3.7.8
DolphinDB server version:1.30.18 or 2.00.5
last modification time: 2022.05.30
last modification developer: DolpinDB
"""
import dolphindb as ddb
import numpy as np
from threading import Event

def resultProcess(lst):
    print(lst)
s = ddb.session()
s.enableStreaming(8800)
s.subscribe(host="192.192.168.9", port=8848, handler=resultProcess, tableName="capitalFlowStream", actionName="SH600000", offset=-1, resub=False, filter=np.array(['600000']))
Event().wait()
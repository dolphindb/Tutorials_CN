import dolphindb as ddb
import time
import os
import random
from threading import Event

s = ddb.session()
hostname = "115.239.209.123"
portname = 8822
s.connect(hostname, portname, "admin", "123456")

event=Event()

def uuid(length):
    str=""
    for i in range(length):
        if(i % 3 == 0):
            str += chr(ord('A') + random.randint(0, os.getpid() + 1) % 26)
        elif(i % 3 == 1):
            str += chr(ord('a') + random.randint(0, os.getpid() + 1) % 26)
        else:
            str += chr(ord('0') + random.randint(0, os.getpid() + 1) % 10)
    return str

uuidStr = uuid(16)

stk_list = ['000616.SZ','000681.SZ']
start_date = '20211201'
end_date = '20211201'
replay_rate = -1
replay_name = ['snapshot','order','transaction']
s.upload({'stk_list':stk_list, 'start_date':start_date, 'end_date':end_date, 'replay_rate':replay_rate, 'replay_uuid':uuidStr, 'replay_name':replay_name})
s.run("stkReplay(stk_list, start_date, end_date, replay_rate, replay_uuid, replay_name)")

def myHandler(lst):
    if lst[-1] == "snapshot":
        print("SNAPSHOT: ", lst)
    elif lst[-1] == 'order':
        print("ORDER: ", lst)
    elif lst[-1] == 'transaction':
        print("TRANSACTION: ", lst)
    else:
        print("END: ", lst)
        event.set()

sd = ddb.streamDeserializer({
    'snapshot':  ["dfs://Test_snapshot", "snapshot"],
    'order': ["dfs://Test_order", "order"],
    'transaction': ["dfs://Test_transaction", "transaction"],
    'end': ["dfs://End", "endline"],
}, s)

s.enableStreaming(0)
start = time.time()
s.subscribe(host=hostname, port=portname, handler=myHandler, tableName="replay_"+uuidStr, actionName="replay_stock_data", offset=0, resub=False, msgAsTable=False, streamDeserializer=sd, userName="admin", password="123456")
event.wait()
s.unsubscribe(host=hostname, port=portname, tableName="replay_"+uuidStr, actionName="replay_stock_data")
s.run("dropStreamTable(`replay_+ replay_uuid)")
end = time.time()
print("Replay end! Cost time: %.2f秒"%(end-start))
s.close()
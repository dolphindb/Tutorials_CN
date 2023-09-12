import pandas as pd
from multiprocessing import Pool
from ma_multiprocess import process_group
import os
import time
df = pd.read_csv("mkt_equd_adj.csv")
df= df.set_index("TRADE_DATE")

start_time = time.time()
if __name__ == '__main__':
    # 按照groupby分组
    grouped = df.groupby("SECURITY_ID")

    with Pool(processes=os.cpu_count()) as pool:
        results = pool.map(process_group, [group for name, group in grouped])

    combined_results = pd.concat(results)  
    print(combined_results)
end_time = time.time()
print("耗时: {:.2f}秒".format(end_time - start_time))

# 全部3501206条数据，耗时30.54秒s；123服务器耗时14.12秒；228服务器14.01秒

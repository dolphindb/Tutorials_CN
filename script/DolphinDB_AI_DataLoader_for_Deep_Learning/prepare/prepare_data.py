import time

import dolphindb as ddb
import numpy as np

if __name__ == "__main__":
    s = ddb.session()
    s.connect("localhost", 8848, "admin", "123456")
    dbPath = "dfs://test_ai_dataloader"
    tbName = "wide_factor_table"
    symbols = ["`" + f"{i}.SH".zfill(9) for i in range(1, 251)]
    times = ["2020.01." + f"{i+1}".zfill(2) for i in range(31)]

    sql = f"""select * from loadTable("{dbPath}", "{tbName}")"""

    st = time.time()
    for symbol in symbols:
        for t in times:
            sql_tmp = sql + f""" where Symbol={symbol}, date(DateTime)={t}"""
            data = s.run(sql_tmp, pickleTableToList=True)
            data = np.array(data[2:])
            data.tofile(f"../datas/{symbol[1:]}-{t}.bin")
            print(f"[{symbol}-{t}] LOAD OVER {data.shape}")
    ed = time.time()
    # 统计数据写入文件耗时
    print("total time: ", ed-st)

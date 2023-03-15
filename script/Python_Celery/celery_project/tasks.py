from celery import Celery
import dolphindb as ddb
import numpy as np
import pandas as pd
from datetime import datetime

#建立与dolphidb的session
s = ddb.session()
s.connect("127.0.0.1", 8848, "admin", "123456")

#实例化Celery对象
app = Celery(
    'celeryApp',
    broker='redis://localhost:6379/1',
    backend='redis://localhost:6379/2'
)
app.conf.update(
    task_serializer='pickle',
    accept_content=['pickle'], 
    result_serializer='pickle',
    timezone='Asia/Shanghai',
    enable_utc=True,
)

#添加@app.task()装饰器，说明执行的任务是可供celery调用的异步任务
@app.task()
def get_alpha1(security_id, begin_date, end_time):
    return s.run("get_alpha1", security_id, begin_date, end_time)
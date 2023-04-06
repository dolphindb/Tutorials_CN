from datetime import datetime, timedelta
import pandas as pd
from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
from airflow.providers.dolphindb.operators.dolphindb import DolphinDBOperator
from airflow.operators.bash import BashOperator
from airflow.models import Variable

variable = ['ETL_dbName_origin', "ETL_tbName_origin", "ETL_dbName_process",
            "ETL_tbName_process", 'ETL_dbName_factor', 'ETL_tbName_factor',
            'ETL_dbName_factor_daily','ETL_tbName_factor_daily', "ETL_filedir",
            "ETL_start_date", "ETL_end_date"]
value = []
for var in variable:
    value.append(str(Variable.get(var)))
variables = ",".join(variable)
values = ",".join(value)
args = {
    "owner" : "Airflow",
    "start_date" : days_ago(1),
    "catchup" : False,
    'retries' : 0
}

with DAG(dag_id="addETLTest", default_args = args, schedule_interval="0 12 * * *") as dag:
    start_task = BashOperator(
        task_id="start",
        bash_command="echo start task"
    )
    create_parameter_table = DolphinDBOperator(
        task_id='create_parameter_table',
        dolphindb_conn_id='dolphindb_test',
        sql='''
            undef(`paramTable,SHARED)
            t = table(1:0, `param`value, [STRING, STRING])
            share t as paramTable
            '''
    )
    given_param = DolphinDBOperator(
        task_id='given_param',
        dolphindb_conn_id='dolphindb_test',
        sql="params = split('" + variables + "',',');" + \
            "values = split('" + values + "',',');" + \
            "for(i in 0..(params.size()-1)){" + \
            "insert into paramTable values(params[i], values[i]);}"
    )
    addLoadSnapshot = DolphinDBOperator(
        task_id='addLoadSnapshot',
        dolphindb_conn_id='dolphindb_test',
        sql='''
            pnodeRun(clearAllCache)
            undef(all)
            go;
            use  addLoadSnapshot::loadSnapshotData
            params = dict(paramTable[`param], paramTable[`value])
            dbName = params[`ETL_dbName_origin]
            tbName = params[`ETL_tbName_origin]
            fileDir = params[`ETL_filedir]
            MarketDays = getMarketCalendar("CFFEX")
            if(today() in MarketDays ){
                fileDir = params[`ETL_filedir]
                addLoadSnapshot::loadSnapshotData::loadSnapshot(2021.01.13, dbName, tbName, fileDir)
            }
            '''
    )
    addProcessSnapshot = DolphinDBOperator(
        task_id='addProcessSnapshot',
        dolphindb_conn_id='dolphindb_test',
        sql='''
            pnodeRun(clearAllCache)
            undef(all)
            go;
            use addProcessSnapshot::processSnapshotData
            params = dict(paramTable[`param], paramTable[`value])
            dbName_orig = params[`ETL_dbName_origin]
            tbName_orig = params[`ETL_tbName_origin]
            dbName_process = params[`ETL_dbName_process]
            tbName_process = params[`ETL_tbName_process]
            MarketDays = getMarketCalendar("CFFEX")
            if(today() in MarketDays ){
                addProcessSnapshot::processSnapshotData::process(2021.01.13, dbName_orig, tbName_orig, dbName_process, tbName_process)
            }
            '''
    )
    addCalMinuteFactor = DolphinDBOperator(
        task_id='addCalMinuteFactor',
        dolphindb_conn_id='dolphindb_test',
        sql='''
            pnodeRun(clearAllCache)
            undef(all)
            go;
            use addFactor::calFactorOneMinute
            params = dict(paramTable[`param], paramTable[`value])
            dbName = params[`ETL_dbName_process]
            tbName = params[`ETL_tbName_process]	
            dbName_factor = params[`ETL_dbName_factor]
            tbName_factor = params[`ETL_tbName_factor]
            factorTable = loadTable(dbName_factor, tbName_factor)
            MarketDays = getMarketCalendar("CFFEX")
            if(today() in MarketDays ){
                	addFactor::calFactorOneMinute::calFactorOneMinute(dbName, tbName,2021.01.13, factorTable)
            }
            '''
    )
    addCalDailyFactor = DolphinDBOperator(
        task_id='addCalDailyFactor',
        dolphindb_conn_id='dolphindb_test',
        sql='''
            pnodeRun(clearAllCache)
            undef(all)
            go;
            use addFactor::calFactorDaily1	
            params = dict(paramTable[`param], paramTable[`value])
            dbName = params[`ETL_dbName_process]
            tbName = params[`ETL_tbName_process]	
            dbName_factor = params[`ETL_dbName_factor_daily]
            tbName_factor = params[`ETL_tbName_factor_daily]
            factorTable = loadTable(dbName_factor, tbName_factor)
            MarketDays = getMarketCalendar("CFFEX")
            if(today() in MarketDays ){
                addFactor::calFactorDaily1::calFactorDaily(dbName, tbName,2021.01.13, factorTable)
            }
            '''
    )
    start_task >> create_parameter_table >> given_param >> addLoadSnapshot >> addProcessSnapshot >> addCalMinuteFactor >> addCalDailyFactor

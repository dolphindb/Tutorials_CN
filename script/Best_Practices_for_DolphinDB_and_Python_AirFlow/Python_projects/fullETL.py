from datetime import datetime, timedelta
import pandas as pd
from airflow import DAG
from airflow.decorators import task
from airflow.providers.dolphindb.operators.dolphindb import DolphinDBOperator
from airflow.operators.bash import BashOperator
from airflow.models import Variable

variable = ['ETL_dbName_origin', "ETL_tbName_origin", "ETL_dbName_process",
            "ETL_tbName_process",'ETL_dbName_factor', 'ETL_tbName_factor',
            'ETL_dbName_factor_daily','ETL_tbName_factor_daily', "ETL_filedir",
            "ETL_start_date", "ETL_end_date"]
value = []
for var in variable:
    value.append(str(Variable.get(var)))
variables = ",".join(variable)
values = ",".join(value)

with DAG(dag_id="ETLTest", start_date=datetime(2023, 3, 1), schedule_interval=None) as dag:
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
    loadSnapshot = DolphinDBOperator(
        task_id='loadSnapshot',
        dolphindb_conn_id='dolphindb_test',
        sql='''
            pnodeRun(clearAllCache)
            undef(all)
            go;
            use loadSnapshot::createSnapshotTable
            use  loadSnapshot::loadSnapshotData
            params = dict(paramTable[`param], paramTable[`value])
            dbName = params[`ETL_dbName_origin]
            tbName = params[`ETL_tbName_origin]
            startDate = date(params[`ETL_start_date])
            endDate = date(params[`ETL_end_date])
            fileDir = params[`ETL_filedir]
            if(not existsDatabase(dbName)){
                loadSnapshot::createSnapshotTable::createSnapshot(dbName, tbName)
            }
            start = now()
            for (loadDate in startDate..endDate){
                submitJob("loadSnapshot"+year(loadDate)+monthOfYear(loadDate)+dayOfMonth(loadDate), "loadSnapshot", loadSnapshot::loadSnapshotData::loadSnapshot{, dbName, tbName, fileDir}, loadDate)
            }
            do{
                cnt = exec count(*) from getRecentJobs() where jobDesc="loadSnapshot" and endTime is null
            }
            while(cnt != 0)
            
            cnt = exec count(*) from pnodeRun(getRecentJobs) where jobDesc="loadSnapshot" and errorMsg is not null and receivedTime > start
            if (cnt != 0){
                error = exec errorMsg from pnodeRun(getRecentJobs) where jobDesc="loadSnapshot" and errorMsg is not null and receivedTime > start
                throw error[0]
            }
            '''
    )
    processSnapshot = DolphinDBOperator(
        task_id='processSnapshot',
        dolphindb_conn_id='dolphindb_test',
        sql='''
            pnodeRun(clearAllCache)
            undef(all)
            go;
            use processSnapshot::createSnapshot_array
            use processSnapshot::processSnapshotData
            params = dict(paramTable[`param], paramTable[`value])
            dbName_orig = params[`ETL_dbName_origin]
            tbName_orig = params[`ETL_tbName_origin]
            dbName_process = params[`ETL_dbName_process]
            tbName_process = params[`ETL_tbName_process]
            startDate = date(params[`ETL_start_date])
            endDate = date(params[`ETL_end_date])
            if(not existsDatabase(dbName_process)){
                processSnapshot::createSnapshot_array::createProcessTable(dbName_process, tbName_process)
            }
            start = now()
            for (processDate in startDate..endDate){
                submitJob("processSnapshot"+year(processDate)+monthOfYear(processDate)+dayOfMonth(processDate), "processSnapshot", processSnapshot::processSnapshotData::process{, dbName_orig, tbName_orig, dbName_process, tbName_process}, processDate)
            }
            do{
                cnt = exec count(*) from getRecentJobs() where jobDesc="processSnapshot" and endTime is null
            }
            while(cnt != 0)
            
            cnt = exec count(*) from pnodeRun(getRecentJobs) where jobDesc="processSnapshot" and errorMsg is not null and receivedTime > start
            if (cnt != 0){
                error = exec errorMsg from pnodeRun(getRecentJobs) where jobDesc="processSnapshot" and errorMsg is not null and receivedTime > start
                throw error[0]
            }
            '''
    )
    calMinuteFactor = DolphinDBOperator(
        task_id='calMinuteFactor',
        dolphindb_conn_id='dolphindb_test',
        sql='''
            pnodeRun(clearAllCache)
            undef(all)
            go;
            use Factor::createFactorOneMinute
            use Factor::calFactorOneMinute
            params = dict(paramTable[`param], paramTable[`value])
            dbName = params[`ETL_dbName_process]
            tbName = params[`ETL_tbName_process]	
            dbName_factor = params[`ETL_dbName_factor]
            tbName_factor = params[`ETL_tbName_factor]
            if(not existsDatabase(dbName_factor)){
                createFactorOneMinute(dbName_factor, tbName_factor)
            }
            factorTable = loadTable(dbName_factor, tbName_factor)
            calFactorOneMinute(dbName, tbName,factorTable)
            '''
    )
    calDailyFactor = DolphinDBOperator(
        task_id='calDailyFactor',
        dolphindb_conn_id='dolphindb_test',
        sql='''
            pnodeRun(clearAllCache)
            undef(all)
            go;
            use Factor::createFactorDaily
            use Factor::calFactorDaily1	
            params = dict(paramTable[`param], paramTable[`value])
            dbName = params[`ETL_dbName_process]
            tbName = params[`ETL_tbName_process]	
            dbName_factor = params[`ETL_dbName_factor_daily]
            tbName_factor = params[`ETL_tbName_factor_daily]
            if(not existsDatabase(dbName_factor)){
                createFactorDaily(dbName_factor, tbName_factor)
            }
            factorTable = loadTable(dbName_factor, tbName_factor)
            Factor::calFactorDaily1::calFactorDaily(dbName, tbName,factorTable)
            '''
    )
    start_task >> create_parameter_table >> given_param >> loadSnapshot >> processSnapshot >> calMinuteFactor >> calDailyFactor
 
# -*- coding: utf-8 -*-

#流创建脚本
streaming_pathway_creating_script= '''
//login("admin","123456");
clearAllCache();
undef(all);
go;

use stream_and_sub_mgt;

//执行流清理函数
stream_and_sub_mgt::unsubscribe_all()//解除订阅
stream_and_sub_mgt::drop_all_stream_engines()//删引擎
stream_and_sub_mgt::remove_all_shared_table()//删流表
go;


//快照表名
db_path="dfs://snapshot_SH_L2_TSDB"
table_name="snapshot"

table_handle=loadTable(db_path,table_name)

def sum_diff(x, y){
    return (x-y)\(x+y)
}

@state
def factor1(price){
ema_20=ema(price, 20)
ema_40=ema(price, 40)
sum_diff_1000=1000 * sum_diff(ema_20, ema_40)
final_factor=ema(sum_diff_1000,10) -  ema(sum_diff_1000, 20)
return final_factor
}

//创建计算流表
snapshot_stream_instance=streamTable(100000:0, ["SecurityID","TradeTime","LastPx"], [SYMBOL,TIMESTAMP,DOUBLE])

//启用该流表持久化，持久化80万条，流表超过此行数时写磁盘
try{
	enableTableShareAndPersistence(table=snapshot_stream_instance, tableName="snapshot_stream", cacheSize=800000)
go;
}
catch (ex) {
	print("持久化启用失败:",ex)
	}

//创建计算结果流表(内存表，小数据量)，三列，字段如下，如果创建分区表保存结果，schema与此内存表相同
result_table=streamTable(100000:0, ["SecurityID","TradeTime","factor"], [SYMBOL,TIMESTAMP,DOUBLE])
try{
	enableTableShareAndPersistence(table=result_table, tableName="result_stream", cacheSize=800000)
go;
}
catch (ex) {
	print("持久化启用失败:",ex)
	}


//加载计算结果表(分区表，大数据量)
//factor_table_name="ema_factor"
//result_table = loadTable(db_path,factor_table_name)

//判断是否之前已有引擎
def whether_create_new_engine(){
stream_engine_status=getStreamEngineStat()//检查流引擎状态
if (size(stream_engine_status)==0)//没有任何流引擎
return NULL	

//当前引擎状态=stream_engine_status["ReactiveStreamEngine"]

print("已有流引擎")
demo_engine=getStreamEngine("reactiveDemo")
return demo_engine
}

demo_engine=whether_create_new_engine()

if (demo_engine==NULL){
	demo_engine = createReactiveStateEngine(name="reactiveDemo", metrics=<[TradeTime,factor1(LastPx)]>, dummyTable=snapshot_stream_instance, outputTable=result_table, keyColumn="SecurityID")
	print("流引擎未初始化，已创建流引擎")
	}
	
//demo_engine订阅snapshot_stream流表
subscribeTable(tableName=`snapshot_stream, actionName="factors", handler=append!{demo_engine},msgAsTable=true)

//创建播放数据源供replay函数历史回放；盘中的时候，改为行情数据直接写入snapshot_stream_instance流表
//inputDS = replayDS(<select SecurityID, TradeTime, LastPx from table_handle>, `TradeTime, `TradeTime)//做全年的因子
//inputDS = replayDS(<select SecurityID, TradeTime, LastPx from table_handle where date(TradeTime)=2020.01.02>, `TradeTime, `TradeTime) //试验，只做一天的因子
//inputDS = replayDS(<select SecurityID, TradeTime, LastPx from table_handle where date(TradeTime)<2020.02.01>, `TradeTime, `TradeTime)//做两个月的因子
inputDS = replayDS(<select SecurityID, TradeTime, LastPx from table_handle where date(TradeTime)<2020.07.01>, `TradeTime, `TradeTime)//做半年的因子

demo_job_name="streaming_factor_demo_job"

'''

#流启动脚本
streaming_start_script= '''
//提交job供执行，4并行度
submitJob(demo_job_name,"算因子全年",replay,inputDS,result_table, `TradeTime, `TradeTime, -1,false, 4)
'''
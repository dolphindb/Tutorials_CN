# -*- coding: utf-8 -*-

'''
依赖包：
pip install dolphindb
'''

#流创建脚本
streaming_pathway_creating_script= '''
login("admin","123456");
clearAllCache();
undef(all);
go;
//清理流函数
def cleanStreamEngines(engineNames){
	for(name in engineNames){
		try{
			dropStreamEngine(name)
		}
		catch(ex){
		}
	}
}
def createEmptyStreamTableAsTargetTable(targetTable,streamSharedName,capacity){
	targetSchema=targetTable.schema();
	sch =select name, typeString as type from  targetSchema.colDefs
	colName=sch.name
	colType=sch.type
	snapshotStreamTemp = streamTable(capacity:0, colName, colType)
	enableTableShareAndPersistence(table=snapshotStreamTemp, tableName=streamSharedName, cacheSize=capacity)
	return snapshotStreamTemp
}
//因子纵表建表函数
def createStreamTableForDoubleEmaFactor(){
	factorSchema = table(
	array(SYMBOL, 0) as SecurityID,
	array(TIMESTAMP, 0) as TradeTime,
	array(SYMBOL, 0) as factorName,
	array(DOUBLE, 0) as val)
	targetStreamTable=createEmptyStreamTableAsTargetTable(factorSchema,"doubleEmaStream",800000)
	return targetStreamTable
}
def loadSnapshotTable(){
	dbPath="dfs://snapshot_SH_L2_TSDB"
	tableName="snapshot_SH_L2_TSDB"
	tableHandle=loadTable(dbPath,tableName)
	return tableHandle
}
//定义snapshot数据源的dummy和DS
def getDummyAndDs(){
	columnPhrase='SecurityID, TradeTime,"doubleEma" as factorName, LastPx from tableHandle where date(TradeTime)<2020.07.01' //查询各列指令
	testString="select top 500 "+columnPhrase
	testPhrase=parseExpr(testString)//查询指令
	fullString="select "+columnPhrase
	fullPhrase=parseExpr(fullString)//查询指令
	schemaTable=eval(testPhrase)
	DataSource=replayDS(fullPhrase,"TradeTime", "TradeTime")//全量数据源
	return schemaTable,DataSource
}
//因子函数定义
def sumDiff(x, y){
	return (x-y)\(x+y)
}
@state
def doubleEma(price){
	ema_20=ema(price, 20)
	ema_40=ema(price, 40)
	sumDiff_1000=1000 * sumDiff(ema_20, ema_40)
	finalFactor=ema(sumDiff_1000,10) -  ema(sumDiff_1000, 20)
	return finalFactor
}
//注销之前的流表订阅
try{unsubscribeTable(tableName="doubleEmaStream",actionName="python_subscribe")}catch(ex){}
//注销流表
try{dropStreamTable("doubleEmaStream")}catch(ex){}
resultStreamTable = createStreamTableForDoubleEmaFactor()//创建新流表
tableHandle=loadSnapshotTable()
snapshotDummyTable,inputDS=getDummyAndDs()
//创建流引擎
engineName="doubleEmaFactorDemo"
cleanStreamEngines([engineName])//清理之前的同名引擎
demoEngine = createReactiveStateEngine(name=engineName, metrics=<[TradeTime,factorName,doubleEma(LastPx)]>, dummyTable=snapshotDummyTable, outputTable=resultStreamTable, keyColumn="SecurityID")
'''

#流启动脚本
streaming_start_script= '''
demoJobName="streamingFactorDemoJob"
//提交job供执行
submitJob(demoJobName,"snapshot因子半年",replay,inputDS,demoEngine, `TradeTime, `TradeTime, -1,false, 4)
'''
#以下为python代码，
from threading import Event
from dolphindb import session

DDB_server_port=8851
DDB_datanode_host= "192.168.100.3"
DDB_user_name= "admin"
DDB_password= "123456"

#流表共享名
stream_table_shared_name= "doubleEmaStream"
#流订阅行为名
action_name= "python_subscribe"

#python端回调函数，流表传入数据以后在此下游处理python端的业务
def python_callback_handler(msg):
	#显示传入的流数据
	print("流表传来数据:")
	print(msg)
	pass

def main():
	current_ddb_session=session()

	current_ddb_session.connect(DDB_datanode_host,
					DDB_server_port,
					DDB_user_name,
					DDB_password)
	
	执行结果=current_ddb_session.run(streaming_pathway_creating_script)
	print("流创建执行完成",执行结果)

	try:

		#python端收听端口
		python_receiving_port=24555

		current_ddb_session.enableStreaming(python_receiving_port)
		print(f"DDB将订阅的流发送到客户端{python_receiving_port}端口")

		current_ddb_session.subscribe(
			host=DDB_datanode_host,
			port=DDB_server_port,
			handler=python_callback_handler,
			tableName=stream_table_shared_name,
			actionName=action_name,
			offset=0,
			resub=False,
			filter=None
		)
	except Exception as current_error:
		print(current_error)

	脚本result=current_ddb_session.run(streaming_start_script)
	#阻塞函数退出，保证DDB会话不析构
	Event().wait()

	pass

if __name__ == '__main__':
	main()


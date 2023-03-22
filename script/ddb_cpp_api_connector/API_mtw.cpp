// export LD_LIBRARY_PATH=/newssl/lib
#include "DolphinDB.h"
#include "Util.h"
#include "MultithreadedTableWriter.h"

#include <iostream>
#include <thread>
#include <string>
#include <chrono>

using namespace dolphindb;
using namespace std;
using namespace std::chrono;
using std::this_thread::sleep_for;

int main(int argc, char **argv)  // argc=2 argv[1]=模拟数据的csv文件名
{
    DBConnection conn;
    bool ret = conn.connect("183.136.170.167", 9900, "admin", "123456");
    if(!ret){cout<<"connect failed!";}
	// 执行ddb脚本 模拟场景
    string script;
    string DATA_FIRE(argv[1]); 

	// 直接在 cpp 代码中使用 conn.run(script) 的方式建立 DolphinDB 连接
	/*
    string dbName = "dfs://db_mtw"
    script  = "dbname=\"dfs://db_demo\"\n
				tablename=\"collect\"\n
				if(existsDatabase(\"dfs://db_demo\")){dropDatabase(\"dfs://db_demo\")}\n
				cols_info=`ts`deviceCdoe`logicalPostionId`physicalPostionId`propertyCode`propertyValue\n
				cols_type=[DATETIME,SYMBOL,SYMBOL,SYMBOL,SYMBOL,INT]\n
				t=table(1:0,cols_info,cols_type)\n
				db=database(dbname,VALUE,[2022.11.01],engine=`TSDB)\n
				pt=createPartitionedTable(db,t,tablename,`ts,,`deviceCdoe`ts)\n
				def saveToDFS(mutable dfstable, msg): dfstable.append!(msg)\n
				try{subscribeTable(tableName=\"streamtable\", actionName=\"savetodfs\", offset=0, handler=saveToDFS{pt}, msgAsTable=true, batchSize=1000, throttle=1)}\n
				catch(ex){unsubscribeTable(,`streamtable, \"savetodfs\");}\n
				try{share streamTable(1:0, schema[`name], schema[`type]) as streamtable;}\n
				catch(ex){undef(\"streamtable\", SHARED);}\n
				share streamTable(1:0, schema[`name], schema[`type]) as streamtable;\n
				subscribeTable(tableName=\"streamtable\", actionName=\"savetodfs\", offset=0, handler=saveToDFS{pt}, msgAsTable=true, batchSize=1000, throttle=1)\n";
    conn.run(script);
    conn.run("login(\"admin\", \"123456\")");  
    */

	// 模拟数据
	TableSP bt = conn.run("t0 = loadText('"+DATA_FIRE+"');t0");
    vector<ConstantSP> datas;
    datas.reserve(bt->rows() * 6);
    for(int i = 0; i < bt->rows(); ++i){
        for(int j = 0; j < 6; ++j)
            datas.emplace_back(bt->getColumn(j)->get(i));
    }
	// 压缩方式
    vector<COMPRESS_METHOD> compress;
  	for(int i=0;i<6;i++)compress.push_back(COMPRESS_LZ4);
    
	// 开始时间戳
    system_clock::time_point now = system_clock::now();
    chrono::nanoseconds d = now.time_since_epoch();
    chrono::milliseconds millsec1 = chrono::duration_cast<chrono::milliseconds>(d);
    cout<<"begin time: "<<millsec1.count()<<"ms"<<endl;

	// 建立writer对象
    MultithreadedTableWriter writer(
			"183.136.170.167", 9900, "admin","123456","","streamtable",NULL,false,NULL,1000,1,5,"deviceid", &compress);  
	MultithreadedTableWriter::Status status;  // 保存writer状态
    
	// 这里API端采用单线程将数据放入缓冲队列，用户可根据实际场景使用多线程来使数据入队
	thread t([&]() {
		try {
			for(int i=0;i < (bt->rows())/1000;i++){
				system_clock::duration begin = system_clock::now().time_since_epoch();
				milliseconds milbegin = duration_cast<milliseconds>(begin);
				for(int j=i*1000;j<(i+1)*1000;j++){
					ErrorCodeInfo pErrorInfo;
					// 错误信息-代号  
					// EC_None = 0,
					// EC_InvalidObject=1,
					// EC_InvalidParameter=2,
					// EC_InvalidTable=3,
					// EC_InvalidColumnType=4,
					// EC_Server=5,
					// EC_UserBreak=6,
					// EC_DestroyedObject=7,
					// EC_Other=8
					// 实时打印，方便检错
					// cout<<pErrorInfo.errorInfo<<endl;   
					// cout<<pErrorInfo.errorCode<<endl;
					
					// writer.insert(pErrorInfo,
					// 	datas[j*102+0], datas[j*102+1], datas[j*102+2], datas[j*102+3], datas[j*102+4], datas[j*102+5], datas[j*102+6], 
					// 	datas[j*102+7], datas[j*102+8], datas[j*102+9], datas[j*102+10], datas[j*102+11], datas[j*102+12], datas[j*102+13], 
					// 	datas[j*102+14], datas[j*102+15], datas[j*102+16], datas[j*102+17], datas[j*102+18], datas[j*102+19], datas[j*102+20],
					// 	datas[j*102+21], datas[j*102+22], datas[j*102+23], datas[j*102+24], datas[j*102+25], datas[j*102+26], datas[j*102+27],
					// 	datas[j*102+28], datas[j*102+29], datas[j*102+30], datas[j*102+31], datas[j*102+32], datas[j*102+33], datas[j*102+34], 
					// 	datas[j*102+35], datas[j*102+36], datas[j*102+37], datas[j*102+38], datas[j*102+39], datas[j*102+40], datas[j*102+41],
					// 	datas[j*102+42], datas[j*102+43], datas[j*102+44], datas[j*102+45], datas[j*102+46], datas[j*102+47], datas[j*102+48],
					// 	datas[j*102+49], datas[j*102+50], datas[j*102+51], datas[j*102+52], datas[j*102+53], datas[j*102+54], datas[j*102+55], datas[j*102+56],
					// 	datas[j*102+57], datas[j*102+58], datas[j*102+59], datas[j*102+60], datas[j*102+61], datas[j*102+62], datas[j*102+63],
					// 	datas[j*102+64], datas[j*102+65], datas[j*102+66], datas[j*102+67], datas[j*102+68], datas[j*102+69], datas[j*102+70],
					// 	datas[j*102+71], datas[j*102+72], datas[j*102+73], datas[j*102+74], datas[j*102+75], datas[j*102+76], datas[j*102+77],
					// 	datas[j*102+78], datas[j*102+79], datas[j*102+80], datas[j*102+81], datas[j*102+82], datas[j*102+83], datas[j*102+84],
					// 	datas[j*102+85], datas[j*102+86], datas[j*102+87], datas[j*102+88], datas[j*102+89], datas[j*102+90], datas[j*102+91],
					// 	datas[j*102+92], datas[j*102+93], datas[j*102+94], datas[j*102+95], datas[j*102+96], datas[j*102+97], datas[j*102+98],
					// 	datas[j*102+99], datas[j*102+100], datas[j*102+101]
					// );
					writer.insert(pErrorInfo,
						datas[i*6+0], datas[i*6+1], datas[i*6+2], datas[i*6+3], datas[i*6+4], datas[i*6+5]
					);
				}
				system_clock::duration end = system_clock::now().time_since_epoch();
				milliseconds milend = duration_cast<milliseconds>(end);
				if((milend.count()-milbegin.count())<300000){
					sleep_for(std::chrono::milliseconds(300000-(milend.count()-milbegin.count())));
				}
			}
		}
		catch (exception &e) {
			//MTW 抛出异常
			cerr << "MTW exit with exception: " << e.what() << endl;
		}
	});
    
	writer.getStatus(status);
	if (status.hasError()) {
		cout << "error in writing: " << status.errorInfo << endl;
	}
	// 等待插入线程结束
	t.join();
	// 等待MTW完全退出
	writer.waitForThreadCompletion();
	// 再次检查完成后的MTW状态
	writer.getStatus(status);
	if (status.hasError()) {
		cout << "error after write complete: " << status.errorInfo << endl;
		// 获取未写入的数据
		std::vector<std::vector<ConstantSP>*> unwrittenData;
		writer.getUnwrittenData(unwrittenData);
		cout << "unwriterdata length " << unwrittenData.size() << endl;
		if (!unwrittenData.empty()) {
			try {
				// 重新写入这些数据，原有的MTW因为异常退出已经不能用了，需要创建新的MTW
				cout << "create new MTW and write again." << endl;
				MultithreadedTableWriter newWriter("192.168.0.61", 8848, "admin", "123456", "dfs://test_MultithreadedTableWriter", "collect", NULL,false,NULL,1000,1,5,"deviceid", &compress);
				ErrorCodeInfo errorInfo;
				// 插入未写入的数据      
				if (newWriter.insertUnwrittenData(unwrittenData, errorInfo)) {
					// 等待写入完成后检查状态
					newWriter.waitForThreadCompletion();
					newWriter.getStatus(status);
					if (status.hasError()) {
						cout << "error in write again: " << status.errorInfo << endl;
					}
				}
				else {
					cout << "error in write again: " << errorInfo.errorInfo << endl;
				}
			}
			catch (exception &e) {
				cerr << "new MTW exit with exception: " << e.what() << endl;
			}
		}
	}
	// 结束时间戳
	now = system_clock::now();
	d = now.time_since_epoch();
	chrono::milliseconds millsec2 = chrono::duration_cast<chrono::milliseconds>(d);
	cout<<"end time: "<<millsec2.count()<<"ms"<<endl;
	cout<<"totoal use time: "<<millsec2.count()-millsec1.count()<<"ms"<<endl;
  
	//检查最后写入结果
	cout<<"------------------------------\n";
	cout << conn.run("select count(*) from loadTable('dfs://db_mtw', `collect)")->getString() << endl;
}
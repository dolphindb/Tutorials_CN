// AppImportCsv.cpp : 此文件包含 "main" 函数。程序执行将在此处开始并结束。
//

#include "MultithreadedTableWriter.h"
#include "DolphinDB.h"
#include "Util.h"
#include "rapidcsv.h"
#include <string>
#include <vector>
#include <thread>
#include "ScalarImp.h"
using namespace std;
using namespace dolphindb;

Constant *createDateTime(string str) {
	int year, month, day, hour, minute, second;
	year = atoi(str.substr(0, 4).c_str());
	month = atoi(str.substr(5, 2).c_str());
	day = atoi(str.substr(8, 2).c_str());
	hour = atoi(str.substr(11, 2).c_str());
	minute = atoi(str.substr(14, 2).c_str());
	second = atoi(str.substr(17, 2).c_str());
	return Util::createDateTime(year, month, day, hour, minute, second);
}

int main(int argc, char *argv[]) {
	DBConnection::initialize();
	DBConnection conn;
	string host = "127.0.0.1";
	int port = 8848;
	string userId = "admin";
	string password = "123456";

	string path = "d:/data/devices_big/devices_big_readings.csv";
	int days = Util::countDays(2023, 9, 22);
	
	Constant* p= Util::createTimestamp(2023, 9, 22, 9, 52, 34, 0);
	Constant* seconds= Util::parseConstant(DT_TIMESTAMP, "2022.09.22T09:52:34");
	cout << days << "," << seconds->getLong() <<","<< p->getLong()<<endl;
	try {
		//MultithreadedTableWriter(String hostName, int port, String userId, String password,
		//String dbName, String tableName, boolean useSSL,
		//	boolean enableHighAvailability, String[] highAvailabilitySites,
		//	int batchSize, float throttle,
		//	int threadCount, String partitionCol,
		//	int[] compressTypes, Mode mode, String[] pModeOption, Callback callbackHandler)
/*
login(`admin, `123456)
if (exists('dfs://iot') ) dropDatabase('dfs://iot')

db1 = database('',VALUE,2016.11.15..2016.11.18)
db2 = database('',HASH,[SYMBOL,10])
db = database('dfs://iot',COMPO,[db1,db2])

schema=table(1:0,`time`device_id`battery_level`battery_status`battery_temperature`bssid`cpu_avg_1min`cpu_avg_5min`cpu_avg_15min`mem_free`mem_used`rssi`ssid,
 [DATETIME,SYMBOL,INT,SYMBOL,DOUBLE,SYMBOL,DOUBLE,DOUBLE,DOUBLE,LONG,LONG,SHORT,SYMBOL])
 db.createPartitionedTable(schema,`readings,`time`device_id)
*/
		vector<COMPRESS_METHOD> compress;
		compress.push_back(COMPRESS_DELTA);
		compress.push_back(COMPRESS_LZ4);
		compress.push_back(COMPRESS_DELTA);
		compress.push_back(COMPRESS_LZ4);
		compress.push_back(COMPRESS_LZ4);
		compress.push_back(COMPRESS_LZ4);
		compress.push_back(COMPRESS_LZ4);
		compress.push_back(COMPRESS_LZ4);
		compress.push_back(COMPRESS_LZ4);
		compress.push_back(COMPRESS_DELTA);
		compress.push_back(COMPRESS_DELTA);
		compress.push_back(COMPRESS_LZ4);
		compress.push_back(COMPRESS_LZ4);

		MultithreadedTableWriter writer("127.0.0.1", 8848, "admin", "123456", "dfs://iot", "readings",
			false, false, NULL, 10000, 1, 10, "device_id", &compress);

		rapidcsv::Document doc(path, rapidcsv::LabelParams(-1, -1));
		std::vector<string> time = doc.GetColumn<string>(0);
		std::vector<string> device_id = doc.GetColumn<string>(1);
		std::vector<int> battery_level = doc.GetColumn<int>(2);
		std::vector<string> battery_status = doc.GetColumn<string>(3);
		std::vector<double> battery_temperature = doc.GetColumn<double>(4);
		std::vector<string> bssid = doc.GetColumn<string>(5);
		std::vector<double> cpu_avg_1min = doc.GetColumn<double>(6);
		std::vector<double> cpu_avg_5min = doc.GetColumn<double>(7);
		std::vector<double> cpu_avg_15min = doc.GetColumn<double>(8);
		std::vector<long long> mem_free = doc.GetColumn<long long>(9);
		std::vector<long long> mem_used = doc.GetColumn<long long>(10);
		std::vector<int> rssi = doc.GetColumn<int>(11);
		std::vector<string> ssid = doc.GetColumn<string>(12);

		int rowNum = time.size();
		//btw.addTable("dfs://iot", "readings");
		ErrorCodeInfo errorInfo;


		long long startTime = Util::getEpochTime();
		
		for (int i = 0; i < 100/*rowNum*/; i++) {
			if (writer.insert(errorInfo, 
				createDateTime(time[i]),
				device_id[i],
				battery_level[i],
				battery_status[i],
				battery_temperature[i],
				bssid[i],
				cpu_avg_1min[i],
				cpu_avg_5min[i],
				cpu_avg_15min[i],
				mem_free[i],
				mem_used[i],
				(short)rssi[i],
				ssid[i]
				) == false) {
				//此处不会执行到
				cout << "insert failed: " << errorInfo.errorInfo << endl;
				break;
			}
				
		}
		//检查目前MTW的状态
		MultithreadedTableWriter::Status status;
		writer.getStatus(status);
		if (status.hasError()) {
			cout << "error in writing: " << status.errorInfo << endl;
		}
		writer.waitForThreadCompletion();
		//再次检查完成后的MTW状态
		writer.getStatus(status);
		if (status.hasError()) {
			cout << "error after write complete: " << status.errorInfo << endl;
			//获取未写入的数据
			std::vector<std::vector<ConstantSP>*> unwrittenData;
			writer.getUnwrittenData(unwrittenData);
			cout << "unwriterdata length " << unwrittenData.size() << endl;
		}
			   		 
		cout << "Insert Time " << Util::getEpochTime() - startTime << " ms" << endl;
		//检查最后写入结果
		cout << conn.run("select count(*) from pt")->getString() << endl;


	}
	catch (std::exception &e) {
		cerr << "Failed to insert table, with exception: " << e.what() << endl;
	}



}

// 运行程序: Ctrl + F5 或调试 >“开始执行(不调试)”菜单
// 调试程序: F5 或调试 >“开始调试”菜单

// 入门使用技巧: 
//   1. 使用解决方案资源管理器窗口添加/管理文件
//   2. 使用团队资源管理器窗口连接到源代码管理
//   3. 使用输出窗口查看生成输出和其他消息
//   4. 使用错误列表窗口查看错误
//   5. 转到“项目”>“添加新项”以创建新的代码文件，或转到“项目”>“添加现有项”以将现有代码文件添加到项目
//   6. 将来，若要再次打开此项目，请转到“文件”>“打开”>“项目”并选择 .sln 文件

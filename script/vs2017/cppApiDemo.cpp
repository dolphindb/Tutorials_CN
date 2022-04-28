#include "BatchTableWriter.h"
#include "DolphinDB.h"
#include "Util.h"
#include "rapidcsv.h"
#include <string>
#include <vector>
#include <thread>

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

	string path = "d:/data/devices_big_readings.csv";

	try	{
		dolphindb::BatchTableWriter btw(host, port, userId, password, true);

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
		btw.addTable("dfs://iot", "readings");

		long long startTime = Util::getEpochTime();

		for (int i = 0; i < rowNum; i++) {
			btw.insert("dfs://iot", "readings",
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
					   ssid[i]);
		}

		cout << "Insert Time " << Util::getEpochTime() - startTime << " ms" << endl;

		btw.removeTable("dfs://iot", "readings");
	}
	catch (std::exception &e) {
		cerr << "Failed to insert table, with exception: " << e.what() << endl;
	}
}

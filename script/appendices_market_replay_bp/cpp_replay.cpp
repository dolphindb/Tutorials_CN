#include "DolphinDB.h"
#include "Util.h" 
#include <iostream>
#include <list>
#include <string>
#include <Streaming.h>
#include <sstream>
using namespace dolphindb;
using namespace std;

string uuid(int len);

int main(int argc, char* argv[])
{
    DBConnection conn;
    string hostName = "115.239.209.123";
    int port = 8822;
    string username = "admin";
    string pwd = "123456";
    bool ret = conn.connect(hostName, port, username, pwd);
    if (!ret) {
        cout << "Failed to connect to the server" << endl;
        return 0;
    }

    VectorSP stockList = Util::createVector(DT_STRING, 0);
    vector<string> stocks;
    string out_str;
    int stock_len = strlen(argv[1]);
    for (int i = 0; i < stock_len; ++i){
		if (argv[1][i] == ','){
			argv[1][i] = ' ';
		}
	}
    istringstream out(argv[1]);
    while (out >> out_str){
		 stocks.push_back(out_str);
	}
    stockList->appendString(stocks.data(), stocks.size());

    ConstantSP startDate = Util::createString(argv[2]);
    ConstantSP endDate = Util::createString(argv[3]);

    int rate = stoi(argv[4]);
    ConstantSP replayRate = Util::createInt(rate);

    string uuidStr = uuid(16);
    ConstantSP uuid = Util::createString(uuidStr);

    VectorSP tbName = Util::createVector(DT_STRING, 0);
    stocks.clear();
    string out_str_name;
    stock_len = strlen(argv[5]);
    for (int i = 0; i < stock_len; ++i){
		if (argv[5][i] == ','){
			argv[5][i] = ' ';
		}
	}
    istringstream out_name(argv[5]);
    while (out_name >> out_str_name){
		stocks.push_back(out_str_name);
	}
    tbName->appendString(stocks.data(), stocks.size());

    vector<ConstantSP> args;
    args.push_back(stockList);
    args.push_back(startDate);
    args.push_back(endDate);
    args.push_back(replayRate);
    args.push_back(uuid);
    args.push_back(tbName);

    DictionarySP result = conn.run("stkReplay", args);
    string errorCode = result->get(Util::createString("errorCode"))->getString();
    if (errorCode != "1") 
    {
        std::cout << result->getString() << endl;
        return -1;
    }

    //订阅异构流表并解析数据
    DictionarySP snap_full_schema = conn.run("loadTable(\"dfs://Test_snapshot\", \"snapshot\").schema()");
    DictionarySP order_full_schema = conn.run("loadTable(\"dfs://Test_order\", \"order\").schema()");
    DictionarySP transac_full_schema = conn.run("loadTable(\"dfs://Test_transaction\", \"transaction\").schema()");
    DictionarySP end_full_schema = conn.run("loadTable(\"dfs://End\", \"endline\").schema()");

    unordered_map<string, DictionarySP> sym2schema;
    sym2schema["snapshot"] = snap_full_schema;
    sym2schema["order"] = order_full_schema;
    sym2schema["transaction"] = transac_full_schema;
    sym2schema["end"] = end_full_schema;

    //异构流表解析器
    StreamDeserializerSP sdsp = new StreamDeserializer(sym2schema);

    int listenport = 10260;
    ThreadedClient threadedClient(listenport);
    string tableNameUuid = "replay_" + uuidStr;

    //回调函数，可以根据实际需求修改，案例中是直接打印
    long sumcount = 0;
    long long starttime = Util::getNanoEpochTime();
    auto myHandler = [&](vector<Message> msgs)
    {
        for (auto& msg : msgs)
        {
            std::cout << msg.getSymbol() << " : " << msg->getString() << endl;
            if(msg.getSymbol() == "end")
            {
                threadedClient.unsubscribe(hostName, port, tableNameUuid,"stkReplay");
            }
            sumcount += msg->get(0)->size();
        }
        long long speed = (Util::getNanoEpochTime() - starttime) / sumcount;
        std::cout << "callback speed: " << speed << "ns" << endl;
    };


    auto startTime = std::chrono::system_clock::now();
    auto thread = threadedClient.subscribe(hostName, port, myHandler, tableNameUuid, "stkReplay", 0, true, nullptr, true, 500000, 0.001, false, "admin", "123456", sdsp);
    std::cout << "Successed to subscribe " + tableNameUuid << endl;
    thread->join();
    auto endTime = std::chrono::system_clock::now();
    std::chrono::duration<double> diff = endTime - startTime;
    std::cout << "Replay end! Cost time: " << diff.count() << "s" << endl;
    conn.upload("uuid", uuid);
    conn.run("dropStreamTable(`replay_+uuid)");
    return 0;
}


string uuid(int len)
{
    char* str = (char*)malloc(len + 1);
    srand(getpid());
    for (int i = 0; i < len; ++i)
    {
        switch (i % 3)
        {
        case 0:
            str[i] = 'A' + std::rand() % 26;
            break;
        case 1:
            str[i] = 'a' + std::rand() % 26;
            break;
        default:
            str[i] = '0' + std::rand() % 10;
            break;
        }
    }
    str[len] = '\0';
    std::string rst = str;
    free(str);
    return rst;
}

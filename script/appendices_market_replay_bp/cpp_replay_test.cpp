#include "DolphinDB.h"
#include "Util.h" 
#include <iostream>
#include <list>
#include <string>
#include <Streaming.h>
#include <sstream>
#include <unistd.h>
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


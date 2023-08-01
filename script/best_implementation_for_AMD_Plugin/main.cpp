#include "DolphinDB.h"
#include "Streaming.h"
#include "Util.h"
#include <iostream>
#include <string>

using namespace dolphindb;
using namespace std;

void dumpData(TableSP table)
{
    // 处理收到的数据
    int rows_cnt = table->rows();
    long long delaySum0 = 0; // 从收到数据到插入IPC表前
    long long delaySum1 = 0; // 全过程穿透时间
    long long now = Util::getNanoEpochTime();

    for (int i = 0; i < rows_cnt; i++)
    {
        delaySum0 += table->getColumn(17)->getLong(i);
        delaySum1 += (now - table->getColumn(15)->getLong(i));
    }

    std::cout << rows_cnt << " ";
    std::cout << delaySum0 / rows_cnt << " ";
    std::cout << (delaySum1 / rows_cnt) - (delaySum0 / rows_cnt) << " ";
    std::cout << delaySum1 / rows_cnt << std::endl;
}

void subscribeViaIPC()
{
    string tableName = "IPCExecutionTb";
    IPCInMemoryStreamClient memTableClient;
    // 创建一个存储数据的 table，要求和 createIPCInMemoryTable 中列的类型和名称一一对应
    vector<string> colNames = {"marketType", "securityCode", "execTime", "channelNo", "applSeqNum", "execPrice", "execVolume", "valueTrade", "bidAppSeqNum", "offerApplSeqNum", "side", "execType", "mdStreamId", "bizIndex", "varietyCategory", "receivedTime", "dailyIndex", "perPenetrationTime"};
    vector<DATA_TYPE> colTypes = {DT_INT, DT_SYMBOL, DT_TIMESTAMP, DT_INT, DT_LONG, DT_LONG, DT_LONG, DT_LONG, DT_LONG, DT_LONG, DT_CHAR, DT_CHAR, DT_STRING, DT_LONG, DT_CHAR, DT_NANOTIMESTAMP, DT_INT, DT_NANOTIME}; // , DT_NANOTIMESTAMP
    int rowNum = 0, indexCapacity = 10000;
    // 创建一个和共享内存表结构相同的表
    TableSP outputTable = Util::createTable(colNames, colTypes, rowNum, indexCapacity);

    // 是否覆盖前面旧的数据
    bool overwrite = true;
    ThreadSP thread = memTableClient.subscribe(tableName, dumpData, outputTable, overwrite);
    thread->join();
    // 取消订阅，结束回调
    memTableClient.unsubscribe(tableName);
}

void subscribeViaNetwork()
{
    string tableName = "execution1";
    string serverIp = "127.0.0.1";
    int serverPort = 8848;
    auto threadedClient = new dolphindb::ThreadedClient(0);

    auto myHandler = [&](vector<Message> msgs)
    {
        long long delaySum = 0; // 全过程穿透时间
        long long now = Util::getNanoEpochTime();
        for (auto &msg : msgs)
        {
            delaySum += (now - msg->get(15)->getLong());
        }
        std::cout << msgs.size() << " ";
        std::cout << msgs.front()->get(15)->getString() << " ";
        std::cout << now << " ";
        std::cout << delaySum / msgs.size() << std::endl;
    };

    auto thread1 = threadedClient->subscribe(serverIp, serverPort, myHandler, tableName, "test", -1, true, nullptr, true, 10000, 0.01);
    thread1->join();
    threadedClient->unsubscribe(serverIp, serverPort, tableName);
}

int main(int argc, char *argv[])
{
    if (argc > 1) {
        subscribeViaNetwork();
    } else {
        subscribeViaIPC();
    }

    return 0;
}
#include <iostream>
#include <thread>
#include "DolphinDB.h"
#include "Util.h"
#include "Streaming.h"
#include <string>
using namespace std;
using namespace dolphindb;

int main(int argc, char *argv[]){
    DBConnection conn;
    string hostName = "127.0.0.1";
    int port = 8848;
    bool ret = conn.connect(hostName, port);
    if(!ret){
        cout<<"Failed to connect to the server"<<endl;
        return 0;
    }
    cout<<"Successed to connect to the server"<<endl;

    conn.run("login(\"admin\", \"123456\")");
    DictionarySP t1schema = conn.run("loadTable(\"dfs://snapshotL2\", \"snapshotL2\").schema()");
    DictionarySP t2schema = conn.run("loadTable(\"dfs://trade\", \"trade\").schema()");
    DictionarySP t3schema = conn.run("loadTable(\"dfs://order\", \"order\").schema()");

    unordered_map<string, DictionarySP> sym2schema;
    sym2schema["snapshot"] = t1schema;
    sym2schema["trade"] = t2schema;
    sym2schema["order"] = t3schema;
    StreamDeserializerSP sdsp = new StreamDeserializer(sym2schema);
    auto myHandler = [&](Message msg) {
            const string &symbol = msg.getSymbol();
            cout << symbol << ":";
            size_t len = msg->size();
            for (int i = 0; i < len; i++) {
                    cout << msg->get(i)->getString() << ",";
            }
            cout << endl;
    };

    int listenport = 10260;
    ThreadedClient threadedClient(listenport);
    auto thread = threadedClient.subscribe(hostName, port, myHandler, "messageStream", "printMessageStream", -1, true, nullptr, false, false, sdsp);   
    cout<<"Successed to subscribe messageStream"<<endl;
    thread->join(); 

    return 0;
}

#include "DolphinDB.h"
#include "Util.h"
#include <iostream>
#include <climits>
#include <thread>

#include "BatchTableWriter.h"

using namespace std;
using namespace dolphindb;

int main(int argc, char *argv[]){
    DBConnection::initialize();
    DBConnection conn;
    string host = "127.0.0.1";
    int port = 8848;
    string userId = "admin";
    string password = "123456";

    try {
        bool ret = conn.connect(host, port, userId, password);
        if (!ret) {
            cout << "Failed to connect to the server" << endl;
            return 0;
        }
    } catch (exception &ex) {
        cout << "Failed to  connect  with error: " << ex.what();
        return -1;
    }


    try{
        string script;
        int rowNum = 10;
        int columnNum = 3;

        shared_ptr<BatchTableWriter> btw = make_shared<BatchTableWriter>(host, port, userId, password, true);

        /****** 内存表 ******/
        conn.run("share table(100:0, `col0`col1`col2`col3`col4`col5`col6`col7`col8`col9`col10`col11`col12, [CHAR, SHORT, LONG, FLOAT, DOUBLE, DATE, MONTH, TIME, SECOND, MINUTE, NANOTIME, TIMESTAMP, TIMESTAMP]) as tglobal\n");
        btw->addTable("tglobal");
        for(int i = 0; i < rowNum; i++){
            btw->insert("tglobal", "", 
                        't',
                        (short)1,
                        (long long)12312423423423,
                        (float)2.3,
                        (double)34.2352,
                        (int)1000,
                        (int)1000,
                        (int)1000,
                        (int)1000,
                        (int)1000,
                        (long long)123423423,
                        (long long)123423423,
                        Util::createTimestamp(2021,6,15,10,52,12,111)
                    );
        }
        btw->removeTable("tglobal");

        /****** 内存表 多线程 ******/
        conn.run("share table(100:0, `col0`col1`col2, [INT, INT, INT]) as tglobal\n");
        btw->addTable("tglobal");
        int numThreads = 10;
        vector<thread> threadVec;
        for(int i = 0; i < numThreads; i++){
            thread t([=](){
                for(int i = 0; i < rowNum * columnNum; i+=3){
                    btw->insert("tglobal", "", i,i+1,i+2);
                }
            });
            threadVec.push_back(std::move(t));
        }
        for(auto &i: threadVec)
            i.join();
        btw->removeTable("tglobal");

        /****** 分区表 ******/
        script.clear();
        script.append("dbPath='dfs://demoDB'\n");
        script.append("tableName=`demoTable\n");
        script.append("if(existsDatabase(dbPath)){dropDatabase(dbPath)}\n");
        script.append("db=database(dbPath, HASH, [INT, 3])\n");
        script.append("pt=db.createPartitionedTable(table(1000000:0, `name`date`price, [INT,INT,INT]), tableName, `date)\n");
        conn.run(script);
        btw->addTable("dfs://demoDB", "demoTable");
        for(int i = 0; i < rowNum *columnNum; i+=3){
            btw->insert("dfs://demoDB", "demoTable", i,i+1,i+2);
        }
        btw->removeTable("dfs://demoDB", "demoTable");


        /****** 磁盘未分区表 ******/
        script.clear();
        script.append("dbPath='/home/hydro/dolphindb/test/db_testing/tmp'\n");
        script.append("if(existsDatabase(dbPath)){dropDatabase(dbPath)}\n");
        script.append("db = database(dbPath)\n");
        conn.run(script);
        btw->addTable("/home/hydro/dolphindb/test/db_testing/tmp", "demoTable", false);
        for(int i = 0; i < rowNum *columnNum; i+=3){
            btw->insert("/home/hydro/dolphindb/test/db_testing/tmp", "demoTable", i,i+1,i+2);
        }
        btw->removeTable("/home/hydro/dolphindb/test/db_testing/tmp", "demoTable");

        /****** getStatus ******/
        conn.run("share table(100:0, `col0`col1`col2, [INT, INT, INT]) as tglobal\n");
        btw->addTable("tglobal");
        tuple<int,bool,bool> p = btw->getStatus("tglobal");
        btw->removeTable("tglobal");

        /****** getAllStatus ******/
        conn.run("share table(100:0, `col0`col1`col2, [INT, INT, INT]) as tglobal1\n");
        conn.run("share table(100:0, `col0`col1`col2, [INT, INT, INT]) as tglobal2\n");
        conn.run("share table(100:0, `col0`col1`col2, [INT, INT, INT]) as tglobal3\n");
        btw->addTable("tglobal1");
        btw->addTable("tglobal2");
        btw->addTable("tglobal3");
        TableSP table = btw->getAllStatus();
        btw->removeTable("tglobal1");
        btw->removeTable("tglobal2");
        btw->removeTable("tglobal3");

        /****** getUnwrittenData ******/
        conn.run("share table(100:0, `col0`col1`col2, [INT, INT, INT]) as tglobal\n");
        btw->addTable("tglobal");
        int unwrittenRowNum = 0;
        btw->insert("tglobal", "", 1, 1, 1);
        Util::sleep(1000);
        TableSP tableUnwritten;
        try{
            btw->insert("tglobal", "", 1, 1, 1);
        }
        catch(RuntimeException &e){
            cout << e.what() << endl;
            tableUnwritten = btw->getUnwrittenData("tglobal");
            unwrittenRowNum = tableUnwritten->getColumn(0)->size();
        }
        btw->removeTable("tglobal");
    }
    catch(std::exception& e){
        cerr << endl << "Failed to run test, with exception: " << e.what() << endl;
    }
}

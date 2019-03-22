#include <fstream>
#include <iostream>

#include "ComputingModel.h"
#include "CoreConcept.h"
#include "DBFileIO.h"
#include "ScalarImp.h"
#include "SysIO.h"
#include "Util.h"

#include "LoadMyData.h"

ConstantSP extractMyDataSchema(const ConstantSP &placeholderA, const ConstantSP &placeholderB) {
    ConstantSP colNames = Util::createVector(DT_STRING, 4);
    ConstantSP colTypes = Util::createVector(DT_STRING, 4);
    string names[] = {"id", "symbol", "date", "value"};
    string types[] = {"LONG", "SYMBOL", "DATE", "DOUBLE"};
    colNames->setString(0, 4, names);
    colTypes->setString(0, 4, types);

    vector<ConstantSP> schema = {colNames, colTypes};
    vector<string> header = {"name", "type"};

    return Util::createTable(header, schema);
}

ConstantSP loadMyData(Heap *heap, vector<ConstantSP> &args) {
    string syntax = "Usage: loadMyData::loadMyData(path, [start], [length]). ";
    ConstantSP path = args[0];
    if (path->getCategory() != LITERAL || !path->isScalar())
        throw IllegalArgumentException("loadMyData::loadMyData", syntax + "path must be a string.");
    long long fileLength = Util::getFileLength(path->getString());
    size_t bytesPerRow = sizeof(MyData);
    long long rowNum = fileLength / bytesPerRow;

    int start = 0;
    if (args.size() >= 2 && args[1]->getCategory() == INTEGRAL)
         start = args[1]->getInt();
    int length = rowNum - start;
    if (args.size() >= 3 && args[2]->getCategory() == INTEGRAL)
        length = args[2]->getInt();

    if (start < 0 || start >= rowNum)
        throw IllegalArgumentException("loadMyData::loadMyData", syntax + "start must be a positive number smaller than number of rows in the file.");
    if (start + length > rowNum)
        length = rowNum - start;

    DataInputStreamSP inputStream = Util::createBlockFileInputStream(path->getString(), 0, fileLength, Util::BUF_SIZE, start * bytesPerRow, length * bytesPerRow);
    char buf[Util::BUF_SIZE];
    size_t actualLength;

    long long idBuf[Util::BUF_SIZE];
    string symbolBuf[Util::BUF_SIZE];
    int dateBuf[Util::BUF_SIZE];    // DolphinDB中date类型底层用int存储
    double valueBuf[Util::BUF_SIZE];

    VectorSP id = Util::createVector(DT_LONG, 0);
    VectorSP symbol = Util::createVector(DT_SYMBOL, 0);
    VectorSP date = Util::createVector(DT_DATE, 0);
    VectorSP value = Util::createVector(DT_DOUBLE, 0);

    int cursor = 0;

    while (true) {
        inputStream->readBytes(buf, Util::BUF_SIZE, actualLength);
        if (actualLength <= 0)
            break;
        int actualRowNum = actualLength / bytesPerRow;
        int currRowNum = 0;
        for (char *row = buf; currRowNum < actualRowNum; currRowNum++, row += bytesPerRow) {
            MyData *myData = (MyData *) row;
            idBuf[cursor] = myData->id;
            symbolBuf[cursor] = myData->symbol;
            dateBuf[cursor] = parseDate(myData->date);
            valueBuf[cursor] = myData->value;
            cursor++;
            if (cursor == Util::BUF_SIZE || currRowNum == actualRowNum - 1) {    // 缓冲区已满，或读到最后一行
                id->appendLong(idBuf, cursor);
                symbol->appendString(symbolBuf, cursor);
                date->appendInt(dateBuf, cursor);
                value->appendDouble(valueBuf, cursor);
                cursor = 0;
            }
        }
    }

    vector<ConstantSP> cols = {id, symbol, date, value};
    vector<string> colNames = {"id", "symbol", "date", "value"};

    return Util::createTable(colNames, cols);
}

ConstantSP loadMyDataEx(Heap *heap, vector<ConstantSP> &args) {
    string syntax = "Usage: loadMyDataEx::loadMyDataEx(db, tableName, partitionColumns, path, [start], [length]). ";
    ConstantSP db = args[0];
    ConstantSP tableName = args[1];
    ConstantSP partitionColumns = args[2];
    ConstantSP path = args[3];
    if (!db->isDatabase())
        throw IllegalArgumentException("loadMyDataEx::loadMyDataEx", syntax + "db must be a database handle.");
    if (tableName->getCategory() != LITERAL || !tableName->isScalar())
        throw IllegalArgumentException("loadMyDataEx::loadMyDataEx", syntax + "tableName must be a string.");
    if (partitionColumns->getCategory() != LITERAL || (!partitionColumns->isScalar() && !partitionColumns->isVector()))
        throw IllegalArgumentException("loadMyDataEx::loadMyDataEx", syntax + "partitionColumns must be a string or a string vector.");
    if (path->getCategory() != LITERAL || !path->isScalar())
        throw IllegalArgumentException("loadMyDataEx::loadMyDataEx", syntax + "path must be a string.");
    long long fileLength = Util::getFileLength(path->getString());
    size_t bytesPerRow = sizeof(MyData);
    long long rowNum = fileLength / bytesPerRow;

    int start = 0;
    if (args.size() >= 2 && args[1]->getCategory() == INTEGRAL)
        start = args[1]->getInt();
    int length = rowNum - start;
    if (args.size() >= 3 && args[2]->getCategory() == INTEGRAL)
        length = args[2]->getInt();

    if (start < 0 || start >= rowNum)
        throw IllegalArgumentException("loadMyDataEx::loadMyDataEx", syntax + "start must be a positive number smaller than number of rows in the file.");
    if (start + length > rowNum)
        length = rowNum - start;

    string dbPath = ((SystemHandleSP) db)->getDatabaseDir();
    vector<ConstantSP> existsTableArgs = {new String(dbPath), tableName};
    bool existsTable = heap->currentSession()->getFunctionDef("existsTable")->call(heap, existsTableArgs)->getBool();    // 相当于existsTable(dbPath, tableName)
    ConstantSP result;

    if (existsTable) {    // 表存在，直接加载表
        vector<ConstantSP> loadTableArgs = {db, tableName};
        result = heap->currentSession()->getFunctionDef("loadTable")->call(heap, loadTableArgs);    // 相当于loadTable(db, tableName)
    }
    else {    // 表不存在，创建表
        TableSP schema = extractMyDataSchema(new Void(), new Void());
        ConstantSP dummyTable = DBFileIO::createEmptyTableFromSchema(schema);
        vector<ConstantSP> createTableArgs = {db, dummyTable, tableName, partitionColumns};
        result = heap->currentSession()->getFunctionDef("createPartitionedTable")->call(heap, createTableArgs);    // 相当于createPartitionedTable(db, dummyTable, tableName, partitionColumns)
    }

    int sizePerPartition = 16 * 1024 * 1024;
    int partitionNum = fileLength / sizePerPartition;
    vector<DistributedCallSP> tasks;
    FunctionDefSP func = Util::createSystemFunction("loadMyData", loadMyData, 1, 3, false);
    int partitionStart = start;
    int partitionLength = length / partitionNum;
    for (int i = 0; i < partitionNum; i++) {
        if (i == partitionNum - 1)
            partitionLength = length - partitionLength * i;
        vector<ConstantSP> partitionArgs = {path, new Int(partitionStart), new Int(partitionLength)};
        ObjectSP call = Util::createRegularFunctionCall(func, partitionArgs);    // 将会调用loadMyData(path, taskStart, taskLength)
        tasks.push_back(new DistributedCall(call, true));
        partitionStart += partitionLength;
    }

    vector<ConstantSP> appendToResultArgs = {result};
    FunctionDefSP appendToResult = Util::createPartialFunction(heap->currentSession()->getFunctionDef("append!"), appendToResultArgs);    // 相当于append!{result}
    vector<FunctionDefSP> functors = {appendToResult};
    PipelineStageExecutor executor(functors, false);
    executor.execute(heap, tasks);
    return result;
}

ConstantSP myDataDS(Heap *heap, vector<ConstantSP> &args) {
    string syntax = "Usage: myDataDS::myDataDS(path, [start], [length]). ";
    ConstantSP path = args[0];
    if (path->getCategory() != LITERAL || !path->isScalar())
        throw IllegalArgumentException("myDataDS::myDataDS", syntax + "path must be a string.");
    long long fileLength = Util::getFileLength(path->getString());
    size_t bytesPerRow = sizeof(MyData);
    long long rowNum = fileLength / bytesPerRow;

    int start = 0;
    if (args.size() >= 2 && args[1]->getCategory() == INTEGRAL)
        start = args[1]->getInt();
    int length = rowNum - start;
    if (args.size() >= 3 && args[2]->getCategory() == INTEGRAL)
        length = args[2]->getInt();

    if (start < 0 || start >= rowNum)
        throw IllegalArgumentException("myDataDS::myDataDS", syntax + "start must be a positive number smaller than number of rows in the file.");
    if (start + length > rowNum)
        length = rowNum - start;

    int sizePerPartition = 16 * 1024 * 1024;
    int partitionNum = fileLength / sizePerPartition;

    int partitionStart = start;
    int partitionLength = length / partitionNum;

    FunctionDefSP func = Util::createSystemFunction("loadMyData", loadMyData, 1, 3, false);
    ConstantSP dataSources = Util::createVector(DT_ANY, partitionNum);
    for (int i = 0; i < partitionNum; i++) {
        if (i == partitionNum - 1)
            partitionLength = length - partitionLength * i;
        vector<ConstantSP> partitionArgs = {path, new Int(partitionStart), new Int(partitionLength)};
        ObjectSP code = Util::createRegularFunctionCall(func, partitionArgs);    // 将会调用loadMyData(path, taskStart, taskLength)
        dataSources->set(i, new DataSource(code));
    }
    return dataSources;
}

int parseDate(char date[8]) {
    int year = date[0] * 1000 + date[1] * 100 + date[2] * 10 + date[3];
    int month = date[4] * 10 + date[5];
    int day = date[6] * 10 + date[7];
    return Util::countDays(year, month, day);
}
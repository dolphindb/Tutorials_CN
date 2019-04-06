#include "CoreConcept.h"
#include "Util.h"
#include "ScalarImp.h"

#include "ColumnAvg.h"

ConstantSP columnAvg(Heap *heap, vector<ConstantSP> &args) {
    string syntax = "Usage: columnAvg::columnAvg(ds, colNames). ";
    ConstantSP ds = args[0];
    ConstantSP colNames = args[1];

    if (!ds->isTuple())
        throw IllegalArgumentException("columnAvg::columnAvg", syntax + "ds must be a tuple of data sources.");
    
    if (colNames->getCategory() != LITERAL)
        throw IllegalArgumentException("columnAvg::columnAvg", syntax + "colNames must be must be a string or a string vector.");

    FunctionDefSP mapFunc = heap->currentSession()->getFunctionDef("columnAvg::columnAvgMap");
    vector<ConstantSP> mapWithColNamesArgs = {new Void(), colNames};
    FunctionDefSP mapWithColNames = Util::createPartialFunction(mapFunc, mapWithColNamesArgs);    // columnAvgMap{, colNames}
    FunctionDefSP reduceFunc = heap->currentSession()->getFunctionDef("add");
    FunctionDefSP finalFunc = heap->currentSession()->getFunctionDef("columnAvg::columnAvgFinal");

    FunctionDefSP mr = heap->currentSession()->getFunctionDef("mr");    // mr(ds, columnAvgMap{, colNames}, add, columnAvgFinal)
    vector<ConstantSP> mrArgs = {ds, mapWithColNames, reduceFunc, finalFunc};
    return mr->call(heap, mrArgs);
}

ConstantSP columnAvgMap(Heap *heap, vector<ConstantSP> &args) {
    TableSP table = args[0];
    ConstantSP colNames = args[1];
    double sum = 0.0;
    int count = 0;
    
    for (int i = 0; i < colNames->size(); i++) {
        string colName = colNames->getString(i);
        VectorSP col = table->getColumn(colName);
        sum += col->sum()->getDouble();
        count += col->count();
    }

    ConstantSP result = Util::createVector(DT_ANY, 2);
    result->set(0, new Double(sum));
    result->set(1, new Int(count));
    return result;
}

ConstantSP columnAvgFinal(const ConstantSP &result, const ConstantSP &placeholder) {
    double sum = result->get(0)->getDouble();
    int count = result->get(1)->getInt();
    
    return new Double(sum / count);
}
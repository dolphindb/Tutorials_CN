#include "CoreConcept.h"
#include "Exceptions.h"
#include "Logger.h"
#include "ScalarImp.h"

#include "Handler.h"

ConstantSP handler(Heap *heap, vector<ConstantSP> &args) {
    string syntax = "Usage: handler::handler(indices, table, msg). ";
    ConstantSP indices = args[0];
    TableSP table = args[1];
    ConstantSP msg = args[2];

    if (indices->getCategory() != INTEGRAL)
        throw IllegalArgumentException("handler::handler", syntax + "indices must be integral.");

    int msgSize = msg->size();

    vector<ConstantSP> msgToAppend;
    for (int i = 0; i < indices->size(); i++) {
        int index = indices->getInt(i);
        if (index < 0 || index >= msgSize)
            throw RuntimeException("Index out of range.");
        msgToAppend.push_back(msg->get(index));
    }

    INDEX insertedRows;
    string errMsg;
    bool success = table->append(msgToAppend, insertedRows, errMsg);
    if (!success)
        LOG_ERR("Failed to append to table: ", errMsg);

    return new Void();
}
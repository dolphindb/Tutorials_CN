#include "CoreConcept.h"

extern "C" ConstantSP extractMyDataSchema(const ConstantSP &placeholderA, const ConstantSP &placeholderB);
extern "C" ConstantSP loadMyData(Heap *heap, vector<ConstantSP> &args);
extern "C" ConstantSP loadMyDataEx(Heap *heap, vector<ConstantSP> &args);
extern "C" ConstantSP myDataDS(Heap *heap, vector<ConstantSP> &args);

struct MyData {
    long long id;
    char symbol[8];
    char date[8];
    double value;
};

int parseDate(char date[8]);
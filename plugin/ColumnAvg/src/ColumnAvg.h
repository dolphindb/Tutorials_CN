#include "CoreConcept.h"

extern "C" ConstantSP columnAvg(Heap *heap, vector<ConstantSP> &args);
extern "C" ConstantSP columnAvgMap(Heap *heap, vector<ConstantSP> &args);
extern "C" ConstantSP columnAvgFinal(const ConstantSP &result, const ConstantSP &placeholder);
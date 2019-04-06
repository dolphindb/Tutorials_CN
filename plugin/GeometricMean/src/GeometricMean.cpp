#include "CoreConcept.h"
#include "Exceptions.h"
#include "ScalarImp.h"

#include "GeometricMean.h"

ConstantSP geometricMean(const ConstantSP &x, const ConstantSP &placeholder) {
    string syntax = "Usage: geometricMean::geometricMean(x). ";
    if (!x->isScalar() || !x->isVector())
        throw IllegalArgumentException("geometricMean::geometricMean", syntax + "x must be a number or a numeric vector.");
    switch (x->getType()) {
        case DT_CHAR: return computeGeometricMean<char>(x);
        case DT_SHORT: return computeGeometricMean<short>(x);
        case DT_INT: return computeGeometricMean<int>(x);
        case DT_LONG: return computeGeometricMean<long long>(x);
        case DT_DOUBLE: return computeGeometricMean<double>(x);
        case DT_FLOAT: return computeGeometricMean<float>(x);
        default: throw IllegalArgumentException("geometricMean::geometricMean", syntax + "x must be a number or a numeric vector.");
    }
}
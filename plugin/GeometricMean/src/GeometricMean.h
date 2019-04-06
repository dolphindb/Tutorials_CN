#include "CoreConcept.h"

extern "C" ConstantSP geometricMean(const ConstantSP &X, const ConstantSP &placeholder);

template <typename T>
inline bool isNull(T value);

template <typename T>
ConstantSP computeGeometricMean(ConstantSP x) {
    if (((VectorSP) x)->isFastMode()) {
        int size = x->size();
        T *data = (T *)x->getDataArray();

        double logSum = 0;
        for (int i = 0; i < size; i++) {
            if (!isNull(data[i]))
                logSum += std::log(data[i]);
        }
        double mean = std::exp(logSum / size);
        return new Double(mean);
    }
    else {
        int size = x->size();
        int segmentSize = x->getSegmentSize();
        T **segments = (T **)x->getDataSegment();
        INDEX start = 0;
        int segmentId = 0;
        double logSum = 0;

        while (start < size) {
            T *block = segments[segmentId];
            int blockSize = std::min(segmentSize, size - start);
            for (int i = 0; i < blockSize; i++) {
                if (!isNull(block[i]))
                    logSum += std::log(block[i]);
            }
            start += blockSize;
            segmentId++;
        }
        double mean = std::exp(logSum / size);
        return new Double(mean);
    }
}

template <>
inline bool isNull<char>(char value) {
    return value == CHAR_MIN;
}

template <>
inline bool isNull<short>(short value) {
    return value == SHRT_MIN;
}

template <>
inline bool isNull<int>(int value) {
    return value == INT_MIN;
}

template <>
inline bool isNull<double>(double value) {
    return value == DBL_NMIN;
}

template <>
inline bool isNull<float>(float value) {
    return value == FLT_NMIN;
}

template <>
inline bool isNull<long long>(long long value) {
    return value == LLONG_MIN;
}
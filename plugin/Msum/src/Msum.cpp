#include "CoreConcept.h"
#include "Util.h"

#include "Msum.h"

ConstantSP msum(const ConstantSP &X, const ConstantSP &window) {
    string syntax = "Usage: msum::msum(X, window). ";
    if (!X->isVector() || !X->isNumber())
        throw IllegalArgumentException("msum::msum", syntax + "X must be a numeric vector.");
    INDEX size = X->size();
    int windowSize = window->getInt();
    if (windowSize <= 1)
        throw IllegalArgumentException("msum::msum", syntax + "window must be at least 2.");

    ConstantSP result = Util::createVector(DT_DOUBLE, size);

    double buf[Util::BUF_SIZE];
    double windowHeadBuf[Util::BUF_SIZE];
    double resultBuf[Util::BUF_SIZE];
    double tmpSum = 0.0;

    INDEX start = 0;
    while (start < windowSize) {
        int len = std::min(Util::BUF_SIZE, windowSize - start);
        const double *p = X->getDoubleConst(start, len, buf);
        double *r = result->getDoubleBuffer(start, len, resultBuf);
        for (int i = 0; i < len; i++) {
            if (p[i] != DBL_NMIN)    // p[i] is not NULL
                tmpSum += p[i];
            r[i] = DBL_NMIN;
        }
        start += len;
    }

    result->setDouble(windowSize - 1, tmpSum);    // 上一个循环多设置了一个NULL，填充为tmpSum

    while (start < size) {
        int bufSize = std::min(Util::BUF_SIZE - start % Util::BUF_SIZE, Util::BUF_SIZE);
        int len = std::min(bufSize, size - start);
        const double *p = X->getDoubleConst(start, len, buf);
        const double *q = X->getDoubleConst(start - windowSize, len, windowHeadBuf);
        double *r = result->getDoubleBuffer(start, len, resultBuf);
        for (int i = 0; i < len; i++) {
            if (p[i] != DBL_NMIN)
                tmpSum += p[i];
            if (q[i] != DBL_NMIN)
                tmpSum -= q[i];
            r[i] = tmpSum;
        }
        start += len;
    }

    return result;
}
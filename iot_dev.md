# iot 引擎开发文档

iot引擎的文件保存在src/iot文件夹下，主要包含了以下几个类

- Cache, Ring
- Compactor, CompactRunner
- FileStore
- Engine

## 接口部分：


1. 写数据
```c++
Engine::writeData(string key, const vector<VectorSP>& values);
```

其中key是一个时间序列的名称和tag组合起来得到的字符串，由于是多值模型，所以values是多个列的组合。写数据先写cache，
后台有一个线程不断把cache里面的数据写到磁盘上的第一个level的小文件里面。还有一个compactor不断把小文件merge成大文件。

2. 读数据
```c++
Engine::getVec(string key, int colId)
```

key的含义同上，colId表示第几列。读数据时会先同时查看cache里面和磁盘上有没有数据。


3. 获取统计值

```c++
Engine::getMin(string key, int colId);
Engine::getMax(string key, int colId);
Engine::getAvg(string key, int colId);
Engine::getSum(string key, int colId);
```

上面四个接口可以快速获得一个时间序列某一列的最大、最小、平均值以及和。


下面是一个简单的demo

```c++
string tmpdir("/home/wenxing/workspace/testiot");
rmdir(tmpdir);
Engine e(tmpdir, 1024ll * 8 * 1024 * 1024);

int n = 100000;
VectorSP v = Util::createVector(DT_LONG, n);
VectorSP v2 = Util::createVector(DT_DOUBLE, n);
VectorSP ts = Util::createVector(DT_TIMESTAMP, n);

vector<long long> d(n);
vector<double> d2(n);
for (int i = 0; i < n; ++i) d2[i] = d[i] = i * (i % 2 ? 5 : 11);

ts->setData(0, n, d.data());
v2->setData(0, n, d2.data());

for (int i = 0; i < 5000; ++i) {
    IO_ERR ret = e.writeData(std::to_string(i), {ts, v, v2});
    if (ret != OK) { throw RuntimeException("Failed to writeData"); }
}

while (true) {
    Util::sleep(1000);
    {
        auto vec = e.getVec("4999", 0);
        int n = vec->size();
        auto a = vec->getLong(0);
        auto b = vec->getLong(1);
        auto c = vec->getLong(n - 2);
        auto d = vec->getLong(n - 1);
        int _ = 1;
        std::cout << a << " " << b << " " << c << " " << d << std::endl;
    }

    {
        auto mi = e.getMin("4999", 0)->getLong();
        auto mx = e.getMax("2000", 0)->getLong();
        auto av = e.getAvg("1555", 0)->getLong();
        auto su = e.getSum("0", 0)->getLong();
        printf("min: %lld, max: %lld, avg: %lld, sum: %lld\n", mi, mx, av, su);
        int _ = 1;
    }
}
```


## Compactor

Compactor有几个接口

1. writeSnapshot(const CacheSP& cache)

这个接口把一个CacheSp里面的所有数据写到写成第一个level的小文件。

2. merge(const vector<string>& small, int toLevel, bool compres)
这个接口把若干个小的数据文件merge成下一个级别的文件。


## FileStore

这个类提供一些接口方便数据文件管理。

# C++ API 数据读写指南

DolphinDB C++ API是由DolphinDB提供的应用程序接口，可以用来与DolphinDB server进行交互。

DBConnection::run返回的是ConstantSP类型的对象，它是一个智能指针，类似std::share_ptr。

而Constant类型是DolphinDB中大多数数据类型的基类，如Table，Vector等组合类型，也有Int，Double等标量类型，下面会逐一介绍。

一般而言，对于一个未知真实类型的Constant指针，我们可以用isVector, isTable等方法判断是否为数组或表，使用isScalar方法判断是否为标量。

## 标量类型
DolphinDB C++ API中没有把实际的标量类型暴露给用户，但是用户可以通过Constant类型提供的统一接口使用他们，并使用Util中提供的工厂函数创建。

下面以int类型为例：

```c++
ConstantSP val = Util::createInt(47);
assert(val->getInt() == 47); // 47
assert(val->isScalar() && val->getForm() == DF_SCALAR && val->getType() == DT_INT);
```

## Vector
Vector类型是DolphinDB中的动态数组类型，可以使用Util::createVector方法创建，下面的例子中都以int类型为例，其他类型情况类似。
```c++
VectorSP v = Util::createVector(DT_INT, 0); // 创建一个类型为int的空Vector
```

常用的向Vector中添加数据的方法有四种，
```c++
// 添加单个数据点
v->append(Util::createInt(1));        // v = [1]

//添加单个数据点，也可以通过原生数据类型来实现
int tmp = 1;
v->appendInt(&tmp, 1);                // v = [1 1]

// 一次性添加多个相同数据点
v->append(Util::createInt(2), 2);     // v = [1 1 2 2]

// 批量添加
vector<int> v2{1, 2, 3, 4, 5};
v->appendInt(v2.data(), v2.size());   // v = [1 1 2 2 1 2 3 4 5]
```

读取Vector有三种方法, 首先使用如getInt(int index)等方法获取，
```c++
for(int i = 0; i < v->size(); ++i) {
  cout << v->getInt(i) << ' ';
}
```
其次是批量将数据复制到指定的buffer，
```c++
const int BUF_SIZE = 1024;
int buf[BUF_SIZE];
int start = 0;
int N = v->size();
while (start < N) {
    int len = std::min(N - start, BUF_SIZE);
    v->getInt(start, len, buf);
    for (int i = 0; i < len; ++i) {
        cout << buf[i << ' ';
    }
    start += len;
}
cout << endl;
```
最后是批量获取只读的buffer。这个方法与前一种方法的区别在于，当指定区间的数组内存空间是连续的时候，并不复制数据到指定的缓冲区，而是直接返回内存地址，这样提升了读的效率。
```c++
const int BUF_SIZE = 1024;
int buf[BUF_SIZE];
int start = 0;
int N = v->size();
while (start < N) {
    int len = std::min(N - start, BUF_SIZE);
    const int* p = v->getIntConst(start, len, buf);
    for (int i = 0; i < len; ++i) {
        cout << p[i] << ' ';
    }
    start += len;
}
cout << endl;
```
当数据量比较大时，推荐使用后两种方法，因为第一种方法每次都需要调用虚拟函数，开销较大，而后两种方法由于cache命中率较高、虚拟函数调用次数少，性能较好。

更新一个Vector中的数据也有多种方法，首先是更新单个数据点，

```c++
VectorSP v = Util::createVector(DT_INT, 5, 5);
// 更新单个数据点, v = [0 1 2 3 4]
for(int i = 0; i < 5; ++i) {
    v->setInt(i, i);
}
```

其次是批量更新连续数据点，
```c++

// 批量更新数据点
vector<int> tmp{5,4,3,2,1};
v->setInt(0, 5, tmp.data());    // v = [5 4 3 2 1]

// 批量更新数据点，不做类型检查
vector<int> tmp{11, 22, 33, 44, 55};
v->setData(0, 5, tmp.data());   // v = [11 22 33 44 55]

// 获取buffer后批量更新
int buf[1024];
int* p = v->getIntBuffer(0, 1024, buf);
// p[0] = ...
v->setInt(0, 1024, p);
```

为了解释上面三种数据更新方法，先介绍Vector的数据存储模式。
Vector有两种存储模式，一种是FastVector模式，数据存储在连续的内存块中；另一种是Big array模式，数据分段存储在多个不连续的内存中。一般而言，当Vector的大小超过1048576时，Vector会切换到Big array模式。

getIntBuffer方法一般情况下会直接返回内部地址，只有在区间[start, start + len)跨越Big array的内存交界处时，才会将数据拷贝至用户传入的buffer。而setInt方法会判断传入的buffer地址是否为内部存储的地址，如果是则直接返回，否则进行内存拷贝。

因此在上面列举的三种方法中，第三种方法的效率最高。因为大多数情况下，getIntBuffer返回的地址是Vector内部的buffer，setInt不会进行内存拷贝。而前面两种方法，每次都要进行额外的内存拷贝。

如果需要更新的数据点不连续，可以使用set(index, value)这种方法更新, 其中index和value都是ConstantSP，同样可以达到减少虚拟函数调用次数的目的。
```c++
VectorSP index = Util::createVector(DT_INT, 3);
VectorSP value = Util::createVector(DT_INT, 3);
vector<int> tmp{1,100,1000};
index->setInt(0, 3, tmp.data());

vector<int> tmp2{1, 2, 3};
value->setInt(0, 3, tmp2.data());

v->set(index, value); // v[1] = 1, v[100] = 3, v[1000] = 3
```


## Table
Table是DolphinDB表的底层存储类型，可以用Util::createTable方法创建。对于DBConnection::run函数返回的ConstantSP对象，可以使用isTable方法判断该对象中的指针是否指向一个Table对象。

下面的例子中，我们创建了一张包含三列的表，列名为col1, col2, col3, 列类型为int, bool, string的空表，
```c++
vector<string> colNames{"col1", "col2", "col3"};
vector<DATA_TYPE> colTypes{DT_INT, DT_BOOL, DT_STRING};
TableSP tbl = Util::createTable(colNames, colTypes, 0, 100);
```

下面的用法可以达到一样的效果，
```c++
vector<string> colNames{"col1", "col2", "col3"};
vector<ConstantSP> cols;
cols.emplace_back(Util::createVector(DT_INT, 0));
cols.emplace_back(Util::createVector(DT_BOOL, 0));
cols.emplace_back(Util::createVector(DT_STRING, 0));
TableSP tbl = Util::createTable(colNames, cols);
```

获取Table中的数据，我们可以使用getColumn方法获得某一列的指针，然后使用上一章介绍的方法获取Vector中的数据，
```c++
ConstantSP ret = conn.run("select ...");
VectorSP col0 = ret->getColumn(0); // 获得第0列
VectorSP col1 = ret->getColumn("id"); // 获取id列
```

向Table中添加数据，可以使用append方法，
```c++
// prepare data
VectorSP col0 = Util::createVector(DT_INT, 0);
VectorSP col1 = Util::createVector(DT_BOOL, 0);
// ...

// col0->append(...)
// col1->append(...)
// ...

vector<ConstantSP> cols;
cols.push_back(col0);
cols.push_back(col1);
// ...

INDEX insertedRows;
string errorMsg;
if(!c->append(cols, insertedRows, errorMsg)) {
    // error handling
}
```

需要注意的是，append方法发生错误时不会抛出异常，而是在失败时返回false，并将用户传入的第三个string参数设置为错误信息，用户需要处理这种情况。

下面举例说明如何遍历Table对象，获得每一列的内容，转换为结构体，
```c++
struct Line {
    string id;
    long long value;
    long long time;
    explicit Line(string id, long long value, long long time) : id(std::move(id)), value(value), time(time) {}
};
vector<Line> v;

DBConnection conn;
TableSP t = conn.run("select * from loadTable('dfs://testdb', 'testTbl')");

VectorSP col_id = t->getColumn("id");
VectorSP col_val = t->getColumn("val");
VectorSP col_time = t->getColumn("t");

const int BUF_SIZE = 1024;
long long buf_val[BUF_SIZE];
long long buf_time[BUF_SIZE];
char* buf_id[BUF_SIZE];

int start = 0;
int N = t->rows();
while (start < N) {
    int len = std::min(N - start, BUF_SIZE);
    char** pId = col_id->getStringConst(start, len, buf_id);
    const long long* pVal = col_val->getLongConst(start, len, buf_val);
    const long long* pTime = col_time->getLongConst(start, len, buf_time);

    for (int i = 0; i < len; ++i) {
        v.emplace_back(pId[i], pVal[i], pTime[i]);
    }
    start += len;
}
```
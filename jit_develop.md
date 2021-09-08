llvm的知识可以通过官网的一个例子来学习，[https://llvm.org/docs/tutorial/LangImpl04.html],实现了一门动态语言，和我们的jit类似。


DolphinDB JIT主要包括三个部分：

类型推导： JITUDF::inferType
代码生成： DolphinDBJIT::compile
  1. 参数绑定
  2. UserDefinedFunctionImpCodegen: 循环udf的每一个statement，执行statementCodegenProxy
  3. llvm 优化， 生成机器码，获得c函数指针

执行: DolphinDBJIT::call
  1. 参数绑定
  2. 执行
  3. 获得返回值


下面举例说明:

  ```
  @jit
  def foo(a, b){
    return a + b
  }

  foo(1, 2.0)
  ```


  1. 类型推导：通过输入值1，2.0，推测得知a和b的类型分别为int和double
  2. 参数绑定： jit生成的c函数接口为`void (*jit_func_t)(char*, char*, char*)`, 其中第一个`char*`需要输入heap指针，第二个`char*`需要输入refHolder的指针，第三个`char*`实际上是一个结构体`JITFuncArguments`的地址，这个结构体的成员`U8 returnVal;`用来存jit函数的返回值，`U8 args[0];`用来存jit函数的输入值。 C++程序把所有输入值依次存到`U8 args`里面，jit函数运行完以后，通过`U8 returnVal`获得运行结果。
     上面的例子里面，我们把输入值1和2.0的内存地址保存到 `args[0]`和`args[1]`里面，这部分代码在`DolphinDBJIT::call`里面，然后调用jit函数指针，最后从`returnVal`里面获得结果。
     DolphinDB::compile开头的位置生成的是参数绑定的代码，从第三个char*参数里面，依次把输入值拷贝到栈上。

  3. codegen分类：Constant/Variable Codegen, FlowControl Codegen, Vector Codegen， FunctionCall Codegen

    1. Constant/Variable Codegen: 比如 BoolCodegen， CharCodegen等。它们会调用cg.allocScalar，分配一块内存（一般在栈上），如果是Constant，那么把他的值赋给刚刚分配的内存。
    2. FlowControl Codegen： 比如ForStatementCodegen，DoStatementCodegen。这种代码生成，基本上就是用llvm写汇编，用llvm::CreateBr产生分支跳转指令。信静写了三个类可以不用手写这些代码，分别是JITIfConstruct，JITForConstruct和JITDoConstruct。
    3. Vector Codegen：在jit里面访问DolphinDB的vector的代码，主要有两块，一块是forEachVectorElementLocalCopy，另一个是VectorBranchAt。forEachVectorElementLocalCopy里面依照的是c++里面的写法，把vector的数据拷到一个buffer里面，然后访问，访问完了再拷一份后面的出来。VectorBranchAt里面是生成例如`v[123]`的代码，里面会判断是不是index out of bound，然后判断是不是fastVector，如果是就直接用一级解引用，如果不是，那么用两级解引用。
    4. FunctionCall Codegen：主要在函数RegularFunctionCallCodegen里面，对脚本里面的函数调用生成llvm IR。对于一些常用的数学函数，为了加快运行速度，就不调用DolphinDB里面的函数了，直接调libc的函数。


```c++
if (isScalar && supported_funcNames.count(funcName)) {
    // 获得对应的c函数在LLVM module里面的handle，这些函数在registerBuiltinFunctions里面注册，根据自己的需要可以再添加
    llvm::Function *f = cg.getModule().getFunction(getMyFuncName(funcName, arg0Dt));
    // 把函数参数load到栈上
    llvm::Value *arg = llvmLoad(rawArgs[0], cg);
    // 生成函数调用的IR, 最后生成的汇编就是   call my_function
    llvm::Value *ret = cg->CreateCall(f, arg);
    // 获得返回值的类型
    auto ty = TypeInferencer::getReturnType(funcName, DF_SCALAR, arg0Dt);
    if (ty.type == DT_VOID) { throw RuntimeException("Operator function " + funcName + " not supported yet in JIT."); }
    // 返回这个函数调用返回值到上一层codegen
    return JITValueSP(new JITScalarValue(nullptr, ty.type, ret));
}
```

另外一种情况是在jit的代码里面，调用DolphinDB的函数，具体代码在`genericCallDDBSystemFunction`里面。


  4. 代码生成的过程：代码生成实际上是一个深度优先遍历语法树的一个过程，每遇到一个节点(ObjectSP), 就调用相应的Codegen函数生成IR。比如

   ```
   s = 0.0
   for (i in vec) {
     s += exp(i)
   }
   ```

   这里首先遇到赋值语句`s=0.0`，先遍历赋值语句的elements，又先遇到Variable语句，那么就先执行VariableCodegen，然后执行赋值语句的Codegen。
   然后遇到forStatement，先生成for循环需要的条件代码。然后开始生成循环体的代码，具体就是遍历循环体的elements，逐个调用自己的codegen函数。当所有循环体的代码都生成完了，
   forStatement最后再生成跳转的语句，判断是否执行完毕，如果是则调到下一个statement，否则跳回for循环的开始处。

涉及到的主要类型介绍。

1. JITValue: 一个基类，wrap一个llvm::Value，再带上他的类型。定义了很多操作符函数。
2. JITScalarValue: 表示一个标量
3. JITVectorValue：表示DDB的vector

以JITScalarValue为例

```c++
// 生成语句 a + b 的IR，其中this是a， rhs是b, a和b都是标量
JITValueSP JITScalarValue::add(JITScalarValueSP rhs, Codegen &cg) {
    auto lhsDataType = this->getDataType();
    auto rhsDataType = rhs->getDataType();
    auto lhsDC = Util::getCategory(lhsDataType);
    auto rhsDC = Util::getCategory(rhsDataType);

    bool temporalAdd = false;

    // 判断是不是时间类型加整形
    if (isSpecialTemporalType(lhsDataType) + isSpecialTemporalType(rhsDataType) == 1) {
        if (isSpecialTemporalType(lhsDataType) && rhsDC == INTEGRAL) {
            temporalAdd = true;
        } else if (lhsDC == INTEGRAL && isSpecialTemporalType(rhsDataType)) {
          // 如果左边是整形，右边是时间类型，那么就调换一下左右顺序
            return rhs->add(sharedFromThis(), cg);
        }
    }
    // opGuard用来检 operand是否为null值，如果是null值，则直接返回null
    return opGuard(
        rhs, cg,
        [&]() {
          // 获得相加以后的值的类型, https://basecamp.com/3616762/projects/13845420/todos/344319476
            auto t = binaryOPTypePromotion(llvmLoad(this->getLLVMValue(), cg), lhsDataType, llvmLoad(rhs->getLLVMValue(), cg), rhsDataType, cg, _add);
            auto lhsVal = std::get<0>(t);
            auto rhsVal = std::get<1>(t);
            auto resType = std::get<2>(t);
            if (temporalAdd) {
                // if (t < 0 || t >= maxval)
                //     return t
                // else
                //     return ((t + rhs) % maxval + maxval) % maxval

                // ... 时间类型特殊处理, 略去
            } else {
                if (isIntegerType(resType)) {
                  // 两边都是整形，使用llvm::CreateAdd
                    return JITValueSP(new JITScalarValue(nullptr, resType, cg->CreateAdd(lhsVal, rhsVal)));
                } else if (isFloatingType(resType)) {
                  // 结果是浮点数，使用 llvm::CreateFAdd
                    return JITValueSP(new JITScalarValue(nullptr, resType, cg->CreateFAdd(lhsVal, rhsVal)));
                } else {
                    throw RuntimeException("JIT: does not support adding two " + Util::getDataTypeString(resType));
                }
            }
        },
        _add);
}
```

数组下标访问

```
def betaJIT(x, y){
sumX = 0.0
sumY = 0.0
sumXY = 0.0
sumX2 = 0.0
n = x.size()
for(i in 0:n){
    tx = x[i]
    ty = y[i]
    txy = tx * ty
    sumX = sumX + tx
    sumY = sumX + ty
    sumXY = sumXY + tx * ty
    sumX2 = sumX2 + tx * tx
}
return (sumXY - sumX*sumY/n)/(sumX2 - sumX*sumX/n)
}
```

这里`x[i]`在codegen的时候用的是vectorBranchat，相当于以下c代码

```
// 下面三行只执行一次, 提前初始化好
double** seg = v->getDataSegment();
double *p = v->getDataArray();
bool isFastMode = v->isFastMode();

double v;
if(outOfBound) {
  v = DBL_NMIN;
} else {
  if(isFastMode) {
    v = p[idx];
  } else {
    int segLen = v->getSegmentSize();
    double* p = seg[idx / segLen];
    v = p[idx % segLen];
  }
}
```


其他运算符的null值检查，都会根据operand的类型，判断他们是不是等于这个类型的NULL值。已上面的例子为例，`txy = tx * ty`与下面的c代码等价：

```
double txy;
if(tx == DBL_NMIN || ty == DBL_NMIN) {
  txy = DBL_NMIN;
} else {
  txy = tx * ty;
}
```

因此，这个for循环里面检查null值会有条件跳转，数组下标访问也会有条件跳转，所以实际执行会很慢。
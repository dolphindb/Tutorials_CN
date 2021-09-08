# DolphinDB并发编程教程

## 1.worker and local executor

DolphinDB采用多线程技术，包含多种类型的线程，具体可以参考[单实例配置](https://www.dolphindb.cn/cn/help/pipeline.html)，其中worker和local executor的数量直接决定了系统的并发计算的能力。工作线程的配置参数为workerNum，默认值是CPU的内核数，本地执行线程的配置参数为localExecutor,默认值是CPU内核数减1。在第2.1节中我们会举例说明这两个线程对系统并发计算的性能影响。

- worker： 常规交互作业的工作线程，接收客户端请求，将任务分解为多个小任务，根据任务的粒度自己执行或者发送给local executor或remote executor执行。

- local executor：本地执行线程，执行worker分配的子任务。每个本地执行线程一次只能处理一个任务。所有工作线程共享本地执行线程。

## 1. DolphinDB支持并发访问的数据结构

Dolphindb支持多线程并发访问的表有内存表，分布式表，流表和字典。在并发访问前，需要将表进行共享，否则可能会造成系统crash。需要注意的是，对于分区表，不允许多个线程同时写入同一个分区，这样会报错。下面以内存表为例，通过单线程和多线程同时对一个内存表写入30000000条数据进行性能比较。使用多线程并发编程的性能提高了很多。

```
def appendTable(mutable tableName1,tabelName2){
	return tableName1.append!(tabelName2) 
}
t1 = table(1..100 as id,101..200 as val)
share t1 as table1
t2= table(1..30000000 as id,10000001..40000000 as val)
t3= table(1..10000000 as id,10000001..20000000 as val)
```

单线程写入30000000条数据：

```
>timer{
	jobId=submitJob("append",,appendTable,table1,t2)
	getJobReturn(jobId, true)
}

Time elapsed: 202.021 m
```

多线程同时写入30000000条数据：

```
>timer{
	jobId1=submitJob("append1",,appendTable,table1,t3)
	jobId2=submitJob("append2",,appendTable,table1,t3)
	jobId3=submitJob("append3",,appendTable,table1,t3)
	getJobReturn(jobId, true)
	getRecentJobs()
}
Time elapsed: 101.118 ms
```

同时，我们还可以对字典进行并发访问。DolphinDB提供同步字典syncDic，同步字典允许多个线程对其进行并发读写，对于普通字典进行多线程并发写入可能会造成节点崩溃，如下例：

```
def task1(mutable d,n){
 for(i in 0..n){ d[i]=i*2 }
}
def task2(mutable d,n){
  for(i in 0..n){d[i]=i+1}
}
n=10000000
z1=dict(INT,INT)
jobId1=submitJob("task1",,task1,z1,n)
jobId2=submitJob("task2",,task2,z1,n)
```


同步字典z2允许多线程并发写入：

```
z2=syncDict(INT,INT)
jobId3=submitJob("task1",,task1,z2,n)
jobId4=submitJob("task2",,task2,z2,n)下例中，需要把分区表stockData转换成一个csv文件。该表包含了2008年到2018年的数据，超过了系统的可用内存，因此不能把整个表加载到内存后，再转换成csv文件。可把任务分为多个子任务，每个子任务包含两个步骤：加载一个月的数据到内存，然后将这些数据存储到csv文件中。每个月的数据存储到csv文件中时，必须保证该月数据已加载到内存，并且上个月的数据已经存储到csv文件中。
getJobReturn(jobId3, true)
getJobReturn(jobId4, true)
z2
```

## 2. DolphinDB并行函数

DolphinDB可以将大型任务分为多个小任务同时执行。 通过多线程支持并行计算，大大提高了系统的计算性能。 Dolphindb并行函数调用通常会使用以下三个函数，peach,ploop,pcall。他们分别是[each](https://www.dolphindb.cn/cn/help/index.html),[loop](https://www.dolphindb.cn/cn/help/index.htm)和[call](https://www.dolphindb.cn/cn/help/index.html)的并行版本。

DolphinDB通过多线程支持并行计算。 假设有*n*个任务和*m*个本地执行线程。 调用工作线程生成*n*个子任务并将*n***m* / (1+*m*)个子任务推送到本地执行线程的任务队列。 剩余的*n* / (1+*m*) 个子任务将由工作线程执行。 在执行n个子任务之后，工作线程将各个结果合并以产生最终结果。

要使用并行函数调用，我们需要确保配置文件里设置的本地执行线程数是一个正整数。

### 2.1 peach函数

 对于执行时间较长的任务，peach比each能节省大量的时间。但对于小任务，peach可能执行时间要比each更长，因为并行函数调用的开销很大。下面我们比较一下each和peach的性能。可以看到，相比each函数，使用peach执行时间较长的任务，大大减少了程序运行的时间。在本例中，workerNum设置为测试机器的CPU内核数量8，localExecutor设置为7。

```
>x = 1..10000000
>timer{each(log, (x,x,x,x,x,x,x))}
Time elapsed: 889.254 ms

timer{peach(log, (x,x,x,x,x,x,x))}
>Time elapsed: 369.311 ms
```

为了比较worker和local executor对并发计算的影响。我们使用同样的例子，将workerNum设置为测试机器的CPU内核数量8，localExecutor设置为7。可以看到，对于对个执行时间较长的任务，调用工作线程的数量越大，运行程序所需的时间可能会越，因此可以根据具体的任务情况来配置，以达到最好的并发计算性能。

```
>timer{peach(log, (x,x,x,x,x,x,x))}
Time elapsed: 452.311 ms
```

### 2.2 ploop函数

 loop模板与each模板很相似，区别在于函数返回值的格式和类型。对于each模板来说，第一个函数调用的返回值数据格式和类型决定了所有函数的返回值数据格式和类型。相反，loop没有这样的限制。它适用于函数返回值类型不同的情况 。因此ploop的与peach也可以类比，这里就不再另外举例。

### 2.3 pcall函数

 pcall函数会将输入参数分成几个部分，并行计算，最后将结果合并。如果输入参数的长度小于100,000，pcall函数不会并行计算。 输入参数长度为10000000，使用pcall函数减小了计算时间。

```
>x = rand(1.0, 10000000);
>timer(10) sin(x);
Time elapsed: 739.561 ms

>timer(10) pcall(sin, x);
Time elapsed: 404.56 ms
```

### 4.3 pipline

在某些场景下，我们将大量数据加载到内存中，再写入到分布式文件系统中，为了提升效率，使用多线程同时加载和写入，但如果在这种场景下使用ploop等函数，会造成多个线程往同一分区写入数据，而在dolphindb中，这样是不被允许的，并且，如果此时数据量较大，同时加载到内存中，可能会超出系统内存，此时我们可以使用[pipeline](https://www.dolphindb.cn/cn/help/pipeline.html)函数。

[pipeline](https://www.dolphindb.cn/cn/help/pipeline.html)函数通过多线程优化符合如下条件的任务：

(1) 可分解为多个子任务。

(2) 每个子任务包含多个步骤。

(3) 第i个子任务的第k个步骤必须在第i个子任务的第k-1个步骤以及第i-1个子任务的第k个步骤完成后才能执行

在下例中，需要将多个csv文件写入到分布式文件系统中。这些csv文件的总数据超过了系统的可用内存，因此不能将群不文件加载到内存后，再写入到分布式系统中。可把任务分为多个子任务，每个子任务包含两个步骤：加载一个csv数据到内存，然后将这些数据写入到分布式系统中。每个csv文件的数据写入到分布式文件系统中，必须保证该csv文件已经加载到内存，并且上一个csv文件数据已经写入到了分布式系统中，这样不仅解决了内存问题，还避免了多线程同时写入到同一个分区。

```
dbPath="dfs://stockData"
if(existsDatabase(dbPath))
	dropDatabase(dbPath)
db = database(dbPath, VALUE, 2000.01M..2018.12M)
t = table(1:0,`id`TradingTime,[INT,MONTH])
pt = db.createPartitionedTable(t, `pt, `TradingTime).append!(t)
v = "path1.csv" "path2.csv" "pth3.csv"  "pth4.csv"
def loadData(m){
   return loadText(m)
}
def saveData( mutable pt,tb){
  pt.append!(tb)
}
pipeline(each(partial{loadData}, v),saveData{pt,})
```


















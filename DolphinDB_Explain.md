# DolphinDB SQL 执行计划

为了更直观优化数据查询的性能，DolphinDB提供查询SQL执行计划的功能，便于对SQL语句进行调优。

注：执行计划指一条SQL语句在DolphinDB数据库中具体的执行方式，如命中的分区数量，各步骤执行耗时等等。

`功能发布版本：V1.30.16 / V2.00.4`


注：查看执行计划的同时内部会完整执行该条SQL语句。若对应SQL语句执行耗时较长或者可能命中的分区数较多，可以选择对SQL语句进行拆分，对拆分后各个子句进行检测；或者通过`sqlDS`函数获取命中分区，在对应分区分别检测SQL执行计划（请参考手册的sqlDS介绍。

- [DolphinDB SQL 执行计划](#dolphindb-sql-执行计划)
  - [1. 如何获取执行计划](#1-如何获取执行计划)
  - [2. 看懂执行计划](#2-看懂执行计划)
    - [2.1. 执行计划结构概述](#21-执行计划结构概述)
    - [2.2. from数据源分析](#22-from数据源分析)
    - [2.3. map分区查询分析](#23-map分区查询分析)
    - [2.4. merge合并分析](#24-merge合并分析)
    - [2.5. 最后的数据统计](#25-最后的数据统计)
  - [3. 执行计划详解与优化建议](#3-执行计划详解与优化建议)
    - [3.1. from](#31-from)
      - [3.1.1. JOIN](#311-join)
      - [3.1.2. 子查询](#312-子查询)
    - [3.2. where](#32-where)
    - [3.3. map](#33-map)
      - [3.3.1. 分区剪枝](#331-分区剪枝)
      - [3.3.2. 使用分区字段减少耗时](#332-使用分区字段减少耗时)
      - [3.3.3. optimize场景优化](#333-optimize场景优化)
    - [3.4. reduce](#34-reduce)
    - [3.5. 执行计划对于DolphinDB特有功能的解释](#35-执行计划对于dolphindb特有功能的解释)
  - [4. 附录](#4-附录)

## 1. 如何获取执行计划

若要获取SQL语句的执行计划，需要在select或者exec后面增加：`[HINT_EXPLAIN]`，该关键字必须**紧跟**在select或者exec后，然后再增加查询所需字段。

示例如下：


```
select [HINT_EXPLAIN] * from pt;
```

注：对于UPDATE或者DELETE语句，暂不支持查看执行计划。

## 2. 看懂执行计划

DolphinDB的执行计划返回的是一个JSON格式的字符串，不过与其他数据库执行计划不同的是，DolphinDB的执行计划规则为：

* 同级从上到下表示执行先后顺序。
* 缩进表示子句/子过程的执行顺序。

这里以简单地查询一个表所有的数据为例，分析SQL的执行计划。
```
// valuedb 数据库
n=1000000
month=take(2000.01M..2016.12M, n)
x=rand(1.0, n)
id = rand(1..9,n)
t=table(month, x, id)

db=database("dfs://valuedb", VALUE, 2000.01M..2016.12M)
pt = db.createPartitionedTable(t, `pt, `month)
pt.append!(t)

// 查询
select [HINT_EXPLAIN] * from loadTable("dfs://valuedb",`pt);
```
获取到的执行计划如下：
```
{
    "measurement": "microsecond",
    "explain": {
        "from": {
            "cost": 13
        },
        "map": {
            "partitions": {
                "local": 0,
                "remote": 204
            },
            "cost": 22260,
            "detail": {
                "most": {
                    "sql": "select [114699] month,x,id from pt [partition = /valuedb/200009M/1kE]",
                    "explain": {
                        "rows": 4902,
                        "cost": 9962
                    }
                },
                "least": {
                    "sql": "select [114699] month,x,id from pt [partition = /valuedb/200701M/1kE]",
                    "explain": {
                        "rows": 4902,
                        "cost": 64
                    }
                }
            }
        },
        "merge": {
            "cost": 6163,
            "rows": 1000000,
            "detail": {
                "most": {
                    "sql": "select [114691] month,x,id from pt [partition = /valuedb/201604M/1kE]",
                    "explain": {
                        "from": {
                            "cost": 4
                        },
                        "rows": 4902,
                        "cost": 157
                    }
                },
                "least": {
                    "sql": "select [114699] month,x,id from pt [partition = /valuedb/201605M/1kE]",
                    "explain": {
                        "rows": 4901,
                        "cost": 81
                    }
                }
            }
        },
        "rows": 1000000,
        "cost": 30988
    }
}

简单总结，按照从上到下的执行顺序：

* 首先获取数据源`pt`的信息，耗时13μs；

* 然后将SQL发到各个片区进行查询，涉及本地数据节点分区0个，非本地数据节点分区204个，该阶段总耗时22260μs；耗时最长的是，200009M分区，耗时9962μs，数据量4902行;

* 最后在获取所有分区的查询结果后，进行`merge`汇总，这一步骤耗时6163μs，汇总后的结果是100万行，其中，201604M分区是返回结果最多的一个分区，总行数4902。

* SQL语句获取的总数据量为100万行，总耗时为30988μs。

```

### 2.1. 执行计划结构概述

注："measurement": "microsecond"，表示执行计划中时间开销的单位为微秒。

一般来说，DolphinDB执行计划的所有内容都会包含在`explain`结构里。但是若SQL中存在多个子查询，在执行计划中，则可能存在多个嵌套的`explain`结构。

案例中的`explain`结构中由四部分组成：`from`、`map`、`merge`以及最后的统计信息`rows`和`cost`。

### 2.2. from数据源分析

```
"from": {
	"cost": 13
}
```

`from`结构体种的内容是`cost`，表示获取数据源信息的耗时，单位为μs。在上例中，我们使用`loadTable`函数从数据库中加载valuedb的pt表（的元数据），耗时为13μs。


### 2.3. map分区查询分析

DolphinDB数据库使用分布式文件系统，以分区为单位存储数据。当SQL查询涉及到多个分区时，DophinDB会首先尽可能进行分区剪枝，然后将查询语句分发到相关分区进行并行查询，最后将结果进行汇总。`map`结构体说明了将查询任务发送到相关分区的执行情况。

```
"map": {
    "partitions": {
        "local": 0,
        "remote": 204
    },
    "cost": 22260,
    "detail": {
        "most": {
            "sql": "select [114699] month,x,id from pt [partition = /valuedb/200009M/1kE]",
            "explain": {
                "rows": 4902,
                "cost": 9962
            }
        },
        "least": {
            "sql": "select [114699] month,x,id from pt [partition = /valuedb/200701M/1kE]",
            "explain": {
                "rows": 4902,
                "cost": 64
            }
        }
    }
  }
```

- `partitions`：SQL涉及的分区，包含：
    
    * `local`：本地数据节点涉及的分区数；
    * `remote`：远程数据节点涉及的分区数。
    
   通过对比涉及的分区数与总分区数，有助于分析SQL是否进行了查询优化，如分区剪枝。

- `cost`：总耗时，包含整个`map`阶段的耗时，即分发查询任务到各个分区到分区返回查询结果的耗时。
  
- `detail`：各分区子查询的详细执行计划。

由于查询时涉及分区可能较多，这里只会展示耗时最长和耗时最短的分区。

* `most`表示耗时最长的分区查询。其中：
    
    * `SQL`字段会显示使用的查询语句以及涉及的分区；
    * 嵌套的`explain`会展示各个分区的查询计划。
* `least`展示耗时最短的分区查询，内容与`most`结构相同。

  

### 2.4. merge合并分析

在上一步，各分区查询完成后会将结果发送到发起查询任务的数据节点，并由该节点进行数据汇总，`merge`用于说明汇总阶段的相关指标。

```
        "merge": {
            "cost": 6163,
            "rows": 1000000,
            "detail": {
                "most": {
                    "sql": "select [114691] month,x,id from pt [partition = /valuedb/201604M/1kE]",
                    "explain": {
                        "from": {
                            "cost": 4
                        },
                        "rows": 4902,
                        "cost": 157
                    }
                },
                "least": {
                    "sql": "select [114699] month,x,id from pt [partition = /valuedb/201605M/1kE]",
                    "explain": {
                        "rows": 4901,
                        "cost": 81
                    }
                }
            }
        },
```

在分析的内容中，`cost`为耗时，`rows`为汇总之后的数据量；`detail`包含的内容与`map`中的`detail`内容类似，区别在于，此处`detail`嵌套的的`most`和`least`指的是返回结果最多与最少的分区，而非耗时最长与最短的分区。

### 2.5. 最后的数据统计

最后的统计指标一般包括`rows`（查询获得的总记录数）与`cost`（查询总耗时，单位为μs）。

除此之外，在执行计划内容的中间部分也会报告`rows`和`cost`，为执行的某一个阶段的统计。

最后统计的查询总耗时可能多于各个阶段的耗时之和，这是因为在各个阶段中间可能会有一些数据格式的转换、数据在网络间的传输等额外的开销，而这些开销不会体现在执行计划中。

## 3. 执行计划详解与优化建议

### 3.1. from

数据来源可以是内存表、流数据表、分布式表、多表连接结果或者嵌套的SQL语句。请注意，嵌套的SQL语句不能添加`[HINT_EXPLAIN]`。

#### 3.1.1. JOIN
若查询包含表连接操作，执行计划会显示`JOIN`的相关信息。

```
if(existsDatabase("dfs://valuedb")) dropDatabase("dfs://valuedb");
if(existsDatabase("dfs://valuedb1")) dropDatabase("dfs://valuedb1");
// valuedb 数据库
n=1000000
month=take(2000.01M..2016.12M, n)
x=rand(1.0, n)
id = rand(1..9,n)
t1=table(month, x, id)
db1=database("dfs://valuedb", VALUE, 2000.01M..2016.12M)

pt1 = db1.createPartitionedTable(t1, `pt, `month).append!(t1);

// valuedb1 数据库
id = rand(1..10,n)
times = now()+ 1..n
vals = take(1..20,n) + rand(1.0,n)
t2 = table(id,times,vals)
db2=database("dfs://valuedb1",VALUE, 1..10);
pt2=db2.createPartitionedTable(t2, `pt, `id).append!(t2);

// join 查询
select [HINT_EXPLAIN] times,vals,month from lsj(loadTable("dfs://valuedb",`pt),loadTable("dfs://valuedb1",`pt),`id)
```

结果为：
```
{
  "measurement": "microsecond",
  "explain": {
    "from": {
      "cost": 29,
      "detail": "materialize for JOIN"
    },
    "map": {
      "reshuffle": {
        "cost": 9293
      },
      "partitions": {
        "local": 0,
        "remote": 204
      },
      "cost": 1961931,
      "detail": {
        "most": {
          "sql": "select [98305] times,vals,month from lsj(DataSource< select [65541] month,id from pt where hashBucket(id, 204) == 1 as pt >,DataSource< select [65541] vals,times,id from pt where hashBucket(id, 204) == 1 as pt >,\"id\",\"id\")",
          "explain": {
            "from": {
              "cost": 55134,
              "detail": "materialize for JOIN"
            },
            "join": {
              "cost": 1701
            },
            "rows": 110842,
            "cost": 57877
          }
        },
        "least": {...}
      }
    },
    "merge": {
      "cost": 12358,
      "rows": 1000000,
      "detail": {
        "most": {
          "sql": "select [98305] times,vals,month from lsj(DataSource< select [65541] month,id from pt where hashBucket(id, 204) == 3 as pt >,DataSource< select [65541] vals,times,id from pt where hashBucket(id, 204) == 3 as pt >,\"id\",\"id\")",
          "explain": {
            "from": {
              "cost": 29406,
              "detail": "materialize for JOIN"
            },
            "join": {
              "cost": 2535
            },
            "rows": 111496,
            "cost": 34450
          }
        },
        "least": {...}
      }
    },
    "rows": 1000000,
    "cost": 1979077
  }
}
```

较第二节中的例子相比，本例的执行计划在`from`部分中增加了 "detail": "materialize for JOIN"。请注意这里`from`中的耗时并不是表连接操作的耗时，而是准备用于连接的2个数据源的时间。表连接将在map阶段执行。


根据`map`部分的统计，耗时最长的分区中，`join`耗时1701μs；根据`merge`部分的统计，返回数据量最多的分区中，`join`耗时2535μs。

`map`部分中的`reshuffle`部分显示的耗时，是准备将数据根据连接列连续存放到内存中以进行表连接的耗时，仅是准备过程的耗时，并没有包括将数据取到内存的耗时。若同一数据库下，进行多表连接且连接列是分区字段，则不会包含`reshuffle`部分。（只有2.0版本支持分布式join）

#### 3.1.2. 子查询

如果`from`子句的对象是一个SQL语句（嵌套子查询），则会在执行计划中嵌套显示子查询的执行计划。

下例将表先根据 month 字段分组，计算每组 x 字段的最大值，选取小于固定值记录。

```
select [HINT_EXPLAIN] * from (select max(x) as maxx from loadTable("dfs://valuedb",`pt) group by month ) where maxx < 0.9994
```
在获取的执行计划中，可以看到`from`，`detail`项增加了很多内容。

"sql"显示的是子查询的SQL语句，该标签后的`explain`结构将展示这条子查询SQL语句的执行计划。子查询总共耗时为33571μs。
```
{
  "measurement": "microsecond",
  "explain": {
    "from": {
      "cost": 33571,
      "detail": {
        "sql": "select [98304] max(x) as maxx from loadTable(\"dfs://valuedb\", \"pt\") group by month",
        "explain": {
          "from": {
            "cost": 16
          },
          "map": {
            "partitions": {
              "local": 0,
              "remote": 204
            },
            "cost": 29744,
            "detail": {
              "most": {
                "sql": "select [114715] first(month) as month,max(x) as maxx from pt [partition = /valuedb/200412M]",
                "explain": {
                  "from": {
                    "cost": 4
                  },
                  "rows": 1,
                  "cost": 8224
                }
              },
              "least": {
                "sql": "select [114715] first(month) as month,max(x) as maxx from pt [partition = /valuedb/200112M]",
                "explain": {
                  "rows": 1,
                  "cost": 31
                }
              }
            }
          },
          "merge": {
            "cost": 1192,
            "rows": 204,
            "detail": {
              "most": {
                "sql": "select [114715] first(month) as month,max(x) as maxx from pt [partition = /valuedb/201612M]",
                "explain": {
                  "rows": 1,
                  "cost": 65
                }
              },
              "least": {
                "sql": "select [114707] first(month) as month,max(x) as maxx from pt [partition = /valuedb/200001M]",
                "explain": {
                  "from": {
                    "cost": 5
                  },
                  "rows": 1,
                  "cost": 93
                }
              }
            }
          },
          "rows": 204,
          "cost": 33571
        }
      }
    },
    "where": {
      "rows": 9,
      "cost": 13
    },
    "rows": 9,
    "cost": 33621
  }
}
```

### 3.2. where

典型的`where`部分中只有`rows`和`cost`两项。`cost`表示进行条件过滤的耗时，而`rows`表示过滤后获取的数据量。如上例中，`where`条件过滤后只剩9行数据，耗时13μs。

```
    "where": {
      "rows": 9,
      "cost": 13
    },
```
<!-- DolphinDB不支持在`where`的子查询中查询分布式表，但支持其他的表嵌套在`where`子句中，如内存表。但目前`where`不支持展示子查询的详细执行计划，也不建议在`where`中嵌套使用子查询。-->

<!-- `where`并不一定会出现在所有的`explain`中。上例中，先进行子查询，待返回结果后再进行`where`筛选，所以，最外层的`explain`包含了`where`结构的。

考虑下面这个例子：

```
select [HINT_EXPLAIN] * from loadTable("dfs://valuedb1",`pt) where ( (06:30:00<=time(times) <= 07:21:00) or (14:30:00<=time(times) <= 19:57:00) )
```
该例中，由于`where`可以分发给各个分区并行过滤然后再汇总结果，而不需要根据子查询结果过滤，因此最外层的`explain`就不包含`where`结构。

执行计划如下：

`尽量减少在分区外进行条件过滤，在各分区进行并行筛选可以增加并发度减少耗时。`

```
{
  "measurement": "microsecond",
  "explain": {
    "from": {
      "cost": 17
    },
    "map": {
      "partitions": {
        "local": 0,
        "remote": 10
      },
      "cost": 12364,
      "detail": {
        "most": {
          "sql": "select [114695] id,times,vals from pt where (06:30:00 <= time(times) <= 07:21:00) or (14:30:00 <= time(times) <= 19:57:00) [partition = /valuedb1/1]",
          "explain": {
            "from": {
              "cost": 6
            },
            "where": {
              "rows": 14266,
              "cost": 7195
            },
            "rows": 14266,
            "cost": 7532
          }
        },
        "least": {...}
      }
    },
    "merge": {
      "cost": 1452,
      "rows": 143560,
      "detail": {
        "most": {
          "sql": "select [114695] id,times,vals from pt where (06:30:00 <= time(times) <= 07:21:00) or (14:30:00 <= time(times) <= 19:57:00) [partition = /valuedb1/10]",
          "explain": {
            "from": {
              "cost": 3
            },
            "where": {
              "rows": 14544,
              "cost": 4595
            },
            "rows": 14544,
            "cost": 4927
          }
        },
        "least": {...}
      }
    },
    "rows": 143560,
    "cost": 14878
  }
}
```
-->

### 3.3. map

`map`阶段将任务分发给各个节点执行，执行计划展示了涉及的分区数、获取数据的行数、耗时、具体执行的SQL等信息。若SQL语句进行了优化，`map`部分会包含`optimize`部分，或者`map`部分被`optimize`部分取代。

#### 3.3.1. 分区剪枝

对于分布式查询，我们可以通过观察`map`的`partitions`来检查SQL涉及的分区数量是否与预期涉及的分区数量一致。如果执行计划中分区的数量与总分区数量一致，表示该SQL语句没有触发分区剪枝，遍历了所有的分区，此时参考用户手册关于分区剪枝的部分，可以对SQL语句进行优化。

建议在SQL查询前，估算一下涉及的分区数量，并与执行计划显示的分区数量进行比对，以此来判断SQL是否做到查询最少的数据。

下例按月创建了分区表，month为分区字段，总分区数量204个。现在查询2016年11月到2016年12月的数据，预期查询的分区数只有2个。
```
// 创建数据库
if( existsDatabase("dfs://valuedb") ) dropDatabase("dfs://valuedb");
// 100万，列：x,month;按month 值分区
n=1000000
month=take(2000.01M..2016.12M, n)
x=rand(1.0, n)
t=table(month, x)

db=database("dfs://valuedb", VALUE, 2000.01M..2016.12M)

pt = db.createPartitionedTable(t, `pt, `month)
pt.append!(t)

// 查询出来有204个分区
select count(*) from pnodeRun(getAllChunks) where dfsPath like '%valuedb/%' and type != 0 group by dfsPath

select [HINT_EXPLAIN] * from pt where 2016.11M <= month<= 2016.12M
```

```
{
    "measurement": "microsecond",
    "explain": {
        "from": {
            "cost": 2
        },
        "map": {
            "partitions": {
                "local": 0,
                "remote": 204
            },
            "cost": 12966,
            "detail": {
                "most": {
                    "sql": "select [114699] month,x from pt where 2016.11M <= month <= 2016.12M [partition = /valuedb/200107M/2JCB]",
                    "explain": {
        ......[以下省略]
```
以上执行计划显示，遍历了204个分区。这是因为查询条件 `2016.11M <= month <= 2016.12M` 不能进行分区剪枝。若要分区剪枝，可使用`month between 2016.11M:2016.12M`。

```
select [HINT_EXPLAIN] * from pt where month between 2016.11M : 2016.12M
```
执行计划：
```
{
    "measurement": "microsecond",
    "explain": {
        "from": {
            "cost": 3
        },
        "map": {
            "partitions": {
                "local": 0,
                "remote": 2
            },
            "cost": 912,
            "detail": {
                "most": {
    ......[以下省略]
```

#### 3.3.2. 使用分区字段减少耗时

在SQL中，建议尽量在where或者groupby等条件中使用分区字段，这可以帮助减少查询的分区数，从而减少查询耗时。

比如在下面的例子中，我的表中存在，datea列和dateb列,两列数据相同，但是dateb列为分区使用的字段。同样是查询某一天的数据，使用datea列筛选的执行计划效果如下：
```
if( existsDatabase("dfs://valuedb2") ) dropDatabase("dfs://valuedb2");
n=1000000
datea=take(2000.01.01..2000.01.02, n)
dateb=take(2000.01.01..2000.01.02, n)
x=rand(1.0, n)
t=table(datea,dateb, x)
db=database("dfs://valuedb2", VALUE, 2000.01.01..2000.01.02)
pt = db.createPartitionedTable(t, `pt, `dateb)
pt.append!(t)

select [HINT_EXPLAIN] * from pt where datea = 2000.01.01;
```
```
{
  "measurement": "microsecond",
  "explain": {
    "from": {
      "cost": 1
    },
    "map": {
      "partitions": {
        "local": 0,
        "remote": 2
      },
      "cost": 10010,
      "detail": {
        "most": {
          "sql": "select [114699] datea,dateb,x from pt where datea == 2000.01.01 [partition = /valuedb2/20000101/OD]",
          "explain": {
            "where": {
              "rows": 500000,
              "cost": 3973
            },
            "rows": 500000,
            "cost": 9783
          }
        },
        "least": {
          "sql": "select [114695] datea,dateb,x from pt where datea == 2000.01.01 [partition = /valuedb2/20000102/OD]",
          "explain": {
            "from": {
              "cost": 8
            },
            "where": {
              "rows": 0,
              "cost": 2392
            },
            "rows": 0,
            "cost": 2516
          }
        }
      }
    },
    "merge": {
      "cost": 2079,
      "rows": 500000,
      "detail": {
        "most": {
          "sql": "select [114699] datea,dateb,x from pt where datea == 2000.01.01 [partition = /valuedb2/20000101/OD]",
          "explain": {
            "where": {
              "rows": 500000,
              "cost": 3973
            },
            "rows": 500000,
            "cost": 9783
          }
        },
        "least": {
          "sql": "select [114695] datea,dateb,x from pt where datea == 2000.01.01 [partition = /valuedb2/20000102/OD]",
          "explain": {
            "from": {
              "cost": 8
            },
            "where": {
              "rows": 0,
              "cost": 2392
            },
            "rows": 0,
            "cost": 2516
          }
        }
      }
    },
    "rows": 500000,
    "cost": 13019
  }
}
```
使用dateb列的执行计划效果如下：
```
select [HINT_EXPLAIN] * from pt where dateb = 2000.01.01;
```
```
{
  "measurement": "microsecond",
  "explain": {
    "from": {
      "cost": 1
    },
    "map": {
      "partitions": {
        "local": 0,
        "remote": 1
      },
      "cost": 1275,
      "optimize": {
        "cost": 27,
        "field": "single partition query",
        "sql": "select [98307] datea,dateb,x from pt [partition = /valuedb2/20000101/OD]",
        "explain": {
          "rows": 500000,
          "cost": 1248
        }
      }
    },
    "rows": 500000,
    "cost": 2214
  }
}
```
使用普通列DolphinDB无法进行查询优化，命中了所有的分区，但是使用分区字段就可以。在上面的示例中使用分区字段后直接找到了对应的分区，查询出预期的数据。

**在TSDB引擎中建表时增加了sortColumns选项，该选项可以作为索引快速定位到需要的数据。建议在筛选条件或者组合条件中，尽量使用分区字段和sortColumns字段，可以大大提高查询效率**

#### 3.3.3. optimize场景优化
DolphinDB对于部分经典场景的SQL做了优化，比如对于物联网场景，经常需要查找某些设备最新的数据，DolphinDB在进行优化后，不需要在分发查询任务到每一个分区进行查询，而是采用新的寻径算法找到需要的数据。

在执行计划中，`map`里面会在`optimize`中展示优化的具体内容（该优化在版本`2.00.4`中发布）。如下例查找指定的2个设备所有指标的最新数据：
```
// 设备/指标/日期 1m 23s 23ms
login(`admin,`123456);devices = 1..9;metrics = 'a'..'d';days = 2020.09.01+0..1;
// 每个设备，每个指标，每天的数据量
n = 1000000;

if(existsDatabase("dfs://svmDemo"))	dropDatabase("dfs://svmDemo")
dbName="dfs://svmDemo";tableName="sensors";
tableSchema = table(1:0,`devId`metId`times`vals,[INT,CHAR,TIMESTAMP,FLOAT]);
db1 = database("", VALUE, 2020.09.01+0..1)
db2 = database("", HASH, [INT,3])
db = database(dbName,COMPO,[db1,db2],,'TSDB')
dfsTable = db.createPartitionedTable(tableSchema,tableName,`times`devId,,`devId`metId`times)
go;
t = table(1:0,`devId`metId`times`vals,[INT,CHAR,TIMESTAMP,FLOAT]);
for(day in days){
	t.clear!();	
	for (device in devices){
		for (metric in metrics){
			take(device,n)
			tmp = table(take(device,n) as devId, take(metric,n) as metId, 
				(day.timestamp()+(1..1000000)*80) as times, rand(1.0, n) as vals);
			t.append!(tmp)
		}
	}
	loadTable(dbName,tableName).append!(t);
};go;

select [HINT_EXPLAIN] * from loadTable("dfs://svmDemo","sensors") where devId in [5,9] context by devId csort times limit -1;
```
得到的执行计划如下，其中`map`进行了优化，执行效率得到了提升：
```
{
    "measurement": "microsecond",
    "explain": {
        "from": {
            "cost": 16
        },
        "map": {
            "optimize": {
                "cost": 3,
                "field": "optimize for CONTEXT BY + LIMIT: serial execution."
            },
            "cost": 6063225
        },
        "rows": 2,
        "cost": 6064123
    }
}
 
```
`optimize`里面的内容比较简单，`cost`是完成优化的耗时，而`field`展示的是具体优化措施，本例中就是，对 context by + csort + limit 组合进行执行优化。

除此之外，DolphinDB在一些特定的聚合中也有一些优化内容：
- sortKey
  
  只有使用了TSDB引擎创建的表才会有sortKey。它可能出现在context by或者group by中，值为true或者false，表示聚合时是否使用了sortColumns列来进行排序。

- algo
  
  使用算法只会出现在group by 中。目前优化的算法有："hash", "vectorize", "sort"三种，具体是否可以使用以及使用哪种算法，由数据库判断。

下例创建了一个按月分区的表，date为分区字段，导入数据时对日期进行了处理，分别以6月的日期和7月的日期导入了2次，总分区数量80个，其中6月和7月的分区各40个；

按股票代码，统计每个股票的数据量，因为股票代码是sortKey字段，执行计划sortKey的值为true，表示使用了股票代码字段进行了排序。
```
// 导入股票数据，按月分区；csv的数据请见附录。
login(`admin,`123456);
dbpath = "dfs://stocks";if(existsDatabase(dbpath)) dropDatabase(dbpath);

db1=database(,HASH,[SYMBOL,40]);
db2=database(,VALUE,2020.01M..2022.01M);
db=database(dbpath,COMPO,[db1, db2],,"TSDB")
// 这里YOURDIR替换为实际的目录
schema=extractTextSchema("YOURDIR/20200601.csv")
t=table(1:0,schema.name,schema.type)
db.createPartitionedTable(t,`quotes, `symbol`date,,`symbol`date`time)

def transDate(mutable t, diff){
	return t.replaceColumn!(`date,t.date+diff);
}
diffs = [20,60];
for(diff in diffs){
    // 这里YOURDIR替换为实际的目录
	loadTextEx(dbHandle=db,tableName=`quotes,partitionColumns=`symbol`date,filename="YOURDIR/20200601.csv",transform=transDate{,diff})
}

select [HINT_EXPLAIN] symbol from loadTable("dfs://stocks","quotes") group by symbol;
```
执行计划：
```
{
    "measurement": "microsecond",
    "explain":{
        "from":{
            "cost":19
        },
        "map":{
            "partitions":{
                "local":0,
                "remote":80
            },
            "cost":196081,
            "detail":{
                "most":{
                    "sql":"select [114699] symbol from quotes group by symbol [partition = /stocks/Key7/202007M/gK]",
                    "explain":{
                        "from":{
                            "cost":6
                        },
                        "groupBy":{
                            "sortKey":true,
                            "cost":8727
                        },
                        "rows":276,
                        "cost":20661
                    }
                },
                "least":{
                    "sql":"select [114699] symbol from quotes group by symbol [partition = /stocks/Key8/202007M/gK]",
                    "explain":{
                        "groupBy":{
                            "sortKey":true,
                            "cost":5247
                        },
                        "rows":250,
                        "cost":10605
                    }
                }
            }
        },
        "merge":{
            "cost":2951,
            "rows":23058,
            "detail":{
                "most":{
                    "sql":"select [114699] symbol from quotes group by symbol [partition = /stocks/Key39/202007M/gK]",
                    "explain":{
                        "from":{
                            "cost":7
                        },
                        "groupBy":{
                            "sortKey":true,
                            "cost":6889
                        },
                        "rows":327,
                        "cost":13987
                    }
                },
                "least":{
                    "sql":"select [114699] symbol from quotes group by symbol [partition = /stocks/Key8/202006M/gK]",
                    "explain":{
                        "groupBy":{
                            "sortKey":true,
                            "cost":5123
                        },
                        "rows":250,
                        "cost":12908
                    }
                }
            }
        },
        "reduce":{
            "sql":"select [98307] symbol from 105c5e0300000000 group by symbol",
            "explain":{
                "groupBy":{
                    "sortKey":false,
                    "algo":"sort",
                    "cost":21147
                },
                "rows":11529,
                "cost":22139
            }
        },
        "rows":11529,
        "cost":232551
    }
}
```

### 3.4. reduce

并不是所有的SQL查询都会包含`reduce`阶段，通常在需要对合并后的查询结果进行进一步处理，在SQL执行计划中可能会包含`reduce`。如：
```
select [HINT_EXPLAIN] max(vals) from loadTable("dfs://svmDemo", `sensors) where devId = 1 ;
```
在`merge`阶段汇总结果之后，DolphinDB需要再进行一次处理，此时的执行计划如下：
```
{
    "measurement": "microsecond",
    "explain": {
        "from": {
            "cost": 13
        },
        "map": {
            "partitions": {
                "local": 0,
                "remote": 2
            },
            "cost": 1397982,
            "detail": {
                "most": {...},
                "least": {...}
            }
        },
        "merge": {
            "cost": 35,
            "rows": 2,
            "detail": {
                "most": {
                    "sql": "select [114699] max(vals) as col_0_ from sensors where devId == 1 [partition = /svmDemo/20200902/Key1/gz]",
                    "explain": {
                        "rows": 1,
                        "cost": 1395804
                    }
                },
                "least": {...}
            }
        },
        "reduce": {
            "sql": "select [98307] ::max(col_0_) as max_vals from 105c5e0300000000",
            "explain": {
                "rows": 1,
                "cost": 32
            }
        },
        "rows": 1,
        "cost": 1398888
    }
}
```
在上例中，从各个片区返回的执行结果col_0进行`merge`合并之后，在`reduce`阶段继续查询最大的值max(col_0)，获得结果行数1条，耗时32μs。

`reduce`阶段的执行计划可以便于观察使用函数的耗时，从而以此判断，是否使用的函数效率较低并做出针对性的优化。比如在`map`阶段增加筛选减少需要的内容，减少`reduce`阶段的计算等等。

以下面代码为例：

```
// 继续使用前面导入的股票数据
select [HINT_EXPLAIN] last(askPrice1) \ first(askPrice1) - 1 
          from loadTable("dfs://stocks","quotes")  
          where date >= 2020.06.21
          group by symbol, segment(askLevel, false)
```

```
{
    "measurement": "microsecond",
    "explain": {
        "from": {
            "cost": 17
        },
        "map": {
            "partitions": {
                "local": 0,
                "remote": 80
            },
            "cost": 1528495,
            "detail": {
                "most": {...},
                "least": {...}
            }
        },
        "merge": {
            "cost": 18100,
            "rows": 128206,
            "detail": {
                "most": {
                    "sql": "select [114691] first(askPrice1) as col_1_,last(askPrice1) as col_0_ from quotes group by symbol,segment(askLevel, 0) as segment_askLevel [partition = /stocks/Key31/202007M/gK]",
                    "explain": {
                        "from": {
                            "cost": 8
                        },
                        "groupBy": {
                            "sortKey": true,
                            "cost": 100960
                        },
                        "rows": 2686,
                        "cost": 117555
                    }
                },
                "least": {...}
            }
        },
        "reduce": {
            "sql": "select [98307] ::last(col_0_) \ ::first(col_1_) - 1 as last_askPrice1_ratio from 105c5e0300000000 group by symbol,segment_askLevel",
            "explain": {
                "groupBy": {
                    "sortKey": false,
                    "algo": "hash",
                    "cost": 47979
                },
                "rows": 64103,
                "cost": 48091
            }
        },
        "rows": 64103,
        "cost": 1602107
    }
}
```

### 3.5. 执行计划对于DolphinDB特有功能的解释

DolphinDB有一些特有的创新功能，比如：cgroup by 、 context by 、 pivot by 、 interval 等等；通常情况下，执行计划会单独列举出来这些功能的执行耗时，方便进行性能比较，比如：
```
t = table(`A`A`A`A`B`B`B`B as sym, 
          09:30:06 09:30:28 09:31:46 09:31:59 09:30:19 09:30:43 09:31:23 09:31:56 as time, 
          10 20 10 30 20 40 30 30 as volume, 
          10.05 10.06 10.07 10.05 20.12 20.13 20.14 20.15 as price)

select [HINT_EXPLAIN] wavg(price, volume) as wvap from t 
					 group by sym 
					 cgroup by minute(time) as minute 
					 order by sym, minute
```
执行计划如下，可以看出cgroup by耗时为328μs：
```
{
    "measurement": "microsecond",
    "explain": {
        "from": {
            "cost": 0
        },
        "cgroupBy": {
            "cost": 328
        },
        "rows": 4,
        "cost": 378
    }
}
```

pivot By举例：
```
select [HINT_EXPLAIN] rowSum(ffill(last(preClose))) from loadTable("dfs://stocks", `quotes) pivot by time, symbol
```
执行计划如下：

```
{
    "measurement": "microsecond",
    "explain":{
        "from":{
            "cost":20
        },
        "map":{...},
        "merge":{...},
        "reduce":{
            "sql":"select [98307] rowSum(ffill(::last(col_0_))) as rowSum from 105c5e0300000000 pivot by time,symbol",
            "explain":{
                "pivotBy":{
                    "cost":4086121
                },
                "rows":15182,
                "cost":4086176
            }
        },
        "rows":15182,
        "cost":22514617
    }
}
```

若SQL子句包含interval，则在执行计划中会包含`fill`，表示填充耗时：
```
N = 3653
t = table(2011.11.01..2021.10.31 as date, 
          take(`AAPL, N) as code, 
          rand([0.0573, -0.0231, 0.0765, 0.0174, -0.0025, 0.0267, 0.0304, -0.0143, -0.0256, 0.0412, 0.0810, -0.0159, 0.0058, -0.0107, -0.0090, 0.0209, -0.0053, 0.0317, -0.0117, 0.0123], N) as rate)

select [HINT_EXPLAIN] std(rate) from t group by code, interval(date, 30d, "none")
```
执行计划：
```
{
    "measurement": "microsecond",
    "explain": {
        "from": {
            "cost": 1
        },
        "groupBy": {
            "sortKey": false,
            "algo": "sort",
            "fill": {
                "cost": 1
            },
            "cost": 1662
        },
        "rows": 123,
        "cost": 1736
    }
}
```


## 4. 附录
股票数据csv，参考链接：[20200601.csv](http://www.dolphindb.cn/downloads/tutorial/20200601.zip)。
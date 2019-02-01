
### DolphinDB与ElasticSearch对比测试报告附录

#### 附录1. 系统信息及配置信息

(1) CPU信息

```
Architecture:          x86_64
CPU 运行模式：    32-bit, 64-bit
Byte Order:            Little Endian
CPU(s):                12
On-line CPU(s) list:   0-11
每个核的线程数：2
每个座的核数：  6
Socket(s):             1
NUMA 节点：         1
厂商 ID：           GenuineIntel
CPU 系列：          6
型号：              158
Model name:            Intel(R) Core(TM) i7-8700 CPU @ 3.20GHz
步进：              10
CPU MHz：             899.990
CPU max MHz:           4600.0000
CPU min MHz:           800.0000
BogoMIPS:              6384.00
虚拟化：           VT-x
L1d 缓存：          32K
L1i 缓存：          32K
L2 缓存：           256K
L3 缓存：           12288K
NUMA node0 CPU(s):     0-11
```

(2) ElasticSearch的jvm.options

```
-Xms6g
-Xmx6g
```

(3) ElasticSearch的elasticsearch.yml

```
network.host: 127.0.0.1 
http.port: 9200
http.cors.enabled: true
http.cors.allow-origin: "*"
transport.tcp.port: 9300
transport.tcp.compress: true
discovery.zen.ping.unicast.hosts: ["127.0.0.1:9300", "127.0.0.1:9301", "127.0.0.1:9302", "127.0.0.1:9303"]
discovery.zen.minimum_master_nodes: 1
```

(4) DolphinDB的controller.cfg

```
localSite=localhost:6920:ctl6920
localExecutors=3
maxConnections=128
maxMemSize=4
webWorkerNum=4
workerNum=4
dfsReplicationFactor=1
dfsReplicaReliabilityLevel=0
```

(5) DolphinDB的cluster.nodes

```
localSite,mode
localhost:6910:agent,agent
localhost:6921:DFS_NODE1,datanode
localhost:6922:DFS_NODE2,datanode
localhost:6923:DFS_NODE3,datanode
localhost:6924:DFS_NODE4,datanode
```

(6) DolphinDB的cluster.cfg

```
maxConnections=128
maxMemSize=7
workerNum=4
localExecutors=3
webWorkerNum=2
```

(7) DolphinDB的agent.cfg

```
workerNum=3
localExecutors=2
maxMemSize=4
localSite=localhost:7910:agent
controllerSite=localhost:6920:ctl6920
```

#### 附录2. 创建分区表及加载数据脚本

(1) 加载Trades表的脚本

DolphinDB:

```
filepath = "/home/revenant/data/tushare_daily_data.csv"
dbpath = "dfs://rangedb"
db = database(dbpath, RANGE, 2008.01M+(0..20)*6)
timer(1)
trades = db.loadTextEx(`trades, `trade_date, filepath)
```

ElasticSearch:

```
import urllib3
import json
import csv
import time

def main():
    create_index_template()
    delete_index()  
    create_index()
    http = urllib3.PoolManager()
    t1 = time.time()
    for tmp in read_lines():
        # 分段生成小文件来加载
        data = '\n'.join(bulk_import_lines(tmp))
        data += '\n'
        response = http.request('PUT', 'http://localhost:9200/_bulk', body=data.encode('utf-8'), headers={'Content-Type': 'application/json'})
        print(response.status)
        print(response.data)
    t2 = time.time()
    print("导入数据耗时(ms):", (t2-t1)*1000)


def bulk_import_lines(lines):
    for line in lines:
        yield json.dumps({'index': {'_index': 'elastic', '_type': 'type'}})
        yield json.dumps(line)


# 读每一行转成json
def read_lines():
    with open('/home/revenant/data/tushare_daily_data.csv') as f:
        f.readline()
        field_name = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'pre_close', 'change', 'pct_change', 'vol', 'amount']
        symbols = csv.DictReader(f, fieldnames=field_name)
        cnt = 0
        temp = []
        for symbol in symbols:
            symbol.pop(None, None)
            try:
                cnt = cnt+1
                temp.append(symbol)
            except:
                pass
            if(cnt%100000==0 and cnt!=0):
                print(cnt)
                yield temp
                temp = []
        if(len(temp) > 0):
            yield temp


def create_index():
    http = urllib3.PoolManager()
    try:
        response = http.request('PUT', 'http://localhost:9200/elastic')
        print(response.status)
        print(response.data)
    except urllib3.exceptions:
        print('Connection failed.')


def delete_index():
    http = urllib3.PoolManager()
    try:
        response = http.request('DELETE', 'http://localhost:9200/elastic')
        print(response.status)
        print(response.data)
    except urllib3.exceptions:
        pass


def create_index_template():
    http = urllib3.PoolManager()
    data = json.dumps({
        'template': 'elastic',
        'settings': {
            'number_of_shards': 4,
            'number_of_replicas': 1,
            "index.refresh_interval": -1
        },
        'mappings': {
            'type': {
                '_source': {'enabled': True},
                'properties': {
                    'ts_code': {'type': 'keyword'},
                    'trade_date': {'type': 'date', "format": "yyyy.MM.dd"},
                    'open': {'type': 'double'},
                    'high': {'type': 'double'},
                    'low': {'type': 'double'},
                    'close': {'type': 'double'},
                    'pre_close': {'type': 'double'},
                    'change': {'type': 'double'},
                    'pct_change': {'type': 'double'},
                    'vol': {'type': 'double'},
                    'amount': {'type': 'double'}
                }
            }
        }
    }).encode('utf-8')
    r = http.request('PUT', 'http://localhost:9200/_template/elastic', body=data, headers={'Content-Type': 'application/json'})
    print(r.status)
    print(r.data)

main()
```

(2) 加载US_Trades表的脚本

DolphinDB:

```
filepath = "/home/revenant/data/US.csv"
dbpath = "dfs://rangedb_us"
db = database(dbpath, RANGE, 1990.01M+(0..27)*12)
timer(1)
trades = db.loadTextEx(`trades, `date, filepath)
```

ElasticSearch:

```
import urllib3
import json
import csv
import time

def main():
    create_index_template()
    delete_index()  
    create_index()
    http = urllib3.PoolManager()
    t1 = time.time()
    for tmp in read_lines():
        # 分段生成小文件来加载
        data = '\n'.join(bulk_import_lines(tmp))
        data += '\n'
        response = http.request('PUT', 'http://localhost:9200/_bulk', body=data.encode('utf-8'), headers={'Content-Type': 'application/json'})
        print(response.status)
        print('\n')
        print(response.data)
        print('\n')
    t2 = time.time()
    print("导入数据耗时(ms):", (t2-t1)*1000)


def bulk_import_lines(lines):
    for line in lines:
        yield json.dumps({'index': {'_index': 'uscsv', '_type': 'type'}})
        yield json.dumps(line)


# 读每一行转成json
def read_lines():
    with open('/home/revenant/data/US.csv') as f:
        f.readline()
        field_name = ['PERMNO', 'date', 'SHRCD', 'TICKER', 'TRDSTAT', 'PERMCO', 'HSICCD', 'CUSIP', 'DLSTCD', 'DLPRC', 'DLRET', 'BIDLO', 'ASKHI', 'PRC', 'VOL', 'RET', 'BID', 'ASK', 'SHROUT', 'CFACPR', 'CFACSHR', 'OPENPRC']
        symbols = csv.DictReader(f, fieldnames=field_name)
        cnt = 0
        temp = []
        for symbol in symbols:
            symbol.pop(None, None)
            try:
                cnt = cnt+1
                temp.append(symbol)
            except:
                pass
            if(cnt%100000==0 and cnt!=0):
                print(cnt)
                yield temp
                temp = []
        if(len(temp) > 0):
            yield temp


def create_index():
    http = urllib3.PoolManager()
    try:
        response = http.request('PUT', 'http://localhost:9200/uscsv')
        print(response.status)
        print(response.data)
    except urllib3.exceptions:
        print('Connection failed.')

def delete_index():
    http = urllib3.PoolManager()
    try:
        response = http.request('DELETE', 'http://localhost:9200/uscsv')
        print(response.status)
        print(response.data)
    except urllib3.exceptions:
        pass

def create_index_template():
    http = urllib3.PoolManager()
    data = json.dumps({
        'template': 'uscsv',
        'settings': {
            'number_of_shards': 4,
            'number_of_replicas': 1,
            "index.refresh_interval": -1
        },
        'mappings': {
            'type': {
                '_source': {'enabled': True},
                'properties': { 
                    'PERMNO': {'type': 'integer'},
                    'date': {'type': 'date', "format": "yyyy/MM/dd"},
                    'SHRCD': {'type': 'integer'},
                    'TICKER': {'type': 'keyword'},
                    'TRDSTAT': {'type': 'keyword'},
                    'PERMCO': {'type': 'keyword'},
                    'HSICCD': {'type': 'keyword'},
                    'CUSIP': {'type': 'keyword'},
                    'DLSTCD': {'type': 'keyword'},
                    'DLPRC': {'type': 'keyword'},
                    'DLRET': {'type': 'keyword'},
                    'BIDLO': {'type': 'double'},
                    'ASKHI': {'type': 'double'},
                    'PRC': {'type': 'double'},
                    'VOL': {'type': 'integer'},
                    'RET': {'type': 'keyword'},
                    'BID': {'type': 'double'},
                    'ASK': {'type': 'double'},
                    'SHROUT': {'type': 'keyword'},
                    'CFACPR': {'type': 'double'},
                    'CFACSHR': {'type': 'double'},
                    'OPENPRC': {'type': 'double'}
                }
            }
        }
    }).encode('utf-8')
    r = http.request('PUT', 'http://localhost:9200/_template/uscsv', body=data, headers={'Content-Type': 'application/json'})
    print(r.status)
    print(r.data)

main()
```

(3) 加载BIG_Trades表的脚本

DolphinDB:

```
filepath = "/home/revenant/Documents/TAQ_8/"
dbpath = "dfs://rangedb_100"
dbDate = database(, VALUE, 2007.08.06 2007.08.07 2007.08.08 2007.08.09 )
dbSym = database(, RANGE, `A `B `C `D `E `F `G `H `I `J `K `L `M `N `O `P `Q `R `S `T `U `V `W `X `Y `Z `ZZZ `ZZZZZZZZ)
db = database(dbpath, COMPO, [dbDate, dbSym])
//dropDatabase(dbpath)
for(i in 1:5){
	path = filepath + string(i) + ".csv"
	schemaTb=extractTextSchema(path)
	update schemaTb set name=`sym where name=`Symbol
	update schemaTb set name=`trade_date where name = `Date
	update schemaTb set name=`trade_time where name = `Time
	update schemaTb set name=`bid where name = `BID
	update schemaTb set name=`ofr where name = `OFR
	update schemaTb set name=`bidsiz where name = `BIDSIZ
	update schemaTb set name=`ofrsiz where name = `OFRSIZ
	update schemaTb set name=`mode where name = `MODE
	update schemaTb set name=`ex where name = `EX
	update schemaTb set name=`mmid where name = `MMID
	timer(1)
	trades = db.loadTextEx(`trades,`trade_date `sym, path,,schemaTb)
}
```

ElasticSearch:

```
import urllib3
import json
import csv
import time

def main():
    create_index_template()
    delete_index()
    create_index()
    http = urllib3.PoolManager()
    t1 = time.time()
    for tmp in read_lines():
        # 分段生成小文件来加载
        data = '\n'.join(bulk_import_lines(tmp))
        data += '\n'
        response = http.request('PUT', 'http://localhost:9200/_bulk', body=data.encode('utf-8'), headers={'Content-Type': 'application/json'})
        print(response.status)
        print('\n')
        print(response.data)
        print('\n')
    t2 = time.time()
    print("导入数据耗时(ms):", (t2-t1)*1000)


def bulk_import_lines(lines):
    for line in lines:
        yield json.dumps({'index': {'_index': 'hundred', '_type': 'type'}})
        yield json.dumps(line)


# 读每一行转成json
def read_lines():
    for i in range(1, 5):
        path = '/home/revenant/Documents/TAQ_8/' + str(i) + '.csv'
        with open(path) as f:
            f.readline()
            field_name = ['SYMBOL', 'DATE', 'TIME', 'BID', 'OFR', 'BIDSIZ', 'OFRSIZ', 'MODE', 'EX', 'MMID']
            symbols = csv.DictReader(f, fieldnames=field_name)
            cnt = 0
            temp = []
            for symbol in symbols:
                symbol.pop(None, None)
                try:
                    cnt = cnt+1
                    temp.append(symbol)
                except:
                    pass
                if(cnt%100000==0 and cnt!=0):
                    print(cnt)
                    yield temp
                    temp = []
            if(len(temp) > 0):
                yield temp


def create_index():
    http = urllib3.PoolManager()
    try:
        response = http.request('PUT', 'http://localhost:9200/hundred')
        print(response.status)
        print(response.data)
    except urllib3.exceptions:
        print('Connection failed.')

def delete_index():
    http = urllib3.PoolManager()
    try:
        response = http.request('DELETE', 'http://localhost:9200/hundred')
        print(response.status)
        print(response.data)
    except urllib3.exceptions:
        pass

def create_index_template():
    http = urllib3.PoolManager()
    data = json.dumps({
        'template': 'hundred',
        'settings': {
            'number_of_shards': 10,
            'number_of_replicas': 1,
            "index.refresh_interval": -1
        },
        'mappings': {
            'type': {
                '_source': {'enabled': True},
                'properties': { 
                    'SYMBOL': {'type': 'keyword'},
                    'DATE': {'type': 'date', "format": "yyyyMMdd"},
                    'TIME': {'type': 'keyword'},
                    'BID': {'type': 'double'},
                    'OFR': {'type': 'double'},
                    'BIDSIZ': {'type': 'integer'},
                    'OFRSIZ': {'type': 'integer'},
                    'MODE': {'type': 'integer'},
                    'EX': {'type': 'keyword'},
                    'MMID': {'type': 'keyword'}
                }
            }
        }
    }).encode('utf-8')
    r = http.request('PUT', 'http://localhost:9200/_template/hundred', body=data, headers={'Content-Type': 'application/json'})
    print(r.status)
    print(r.data)

main()
```

#### 附录3. 数据库查询性能测试用例

(1) Trades表查询性能测试用例

DolphinDB Script:

执行每个查询前，使用clearAllCache()清理缓存。

```
//根据时间过滤
timer(10) select * from trades where trade_date <= 2014.01.11

//根据股票代码过滤
timer(10) select * from trades where ts_code <= `002308.SZ

//根据股票代码、浮点型和时间过滤
timer(10) select * from trades where ts_code =  `002308.SZ and trade_date = 2015.05.12 or higb >= 15

//根据浮点型过滤
timer(10) select * from trades where pre_close > 25 and pre_close < 35

//按股票代码分组（单列）
timer(10) select avg(low) from trades group by ts_code

//按股票代码分组（多列）
timer(10) select avg(low), sum(higb) from trades group by ts_code

//按时间分组（单列）
timer(10) select max(open) from trades group by trade_date

//按时间分组（多列）
timer(10) select max(open), sum(pre_close) from trades group by trade_date

//按浮点型过滤，按股票代码分组
timer(10) select avg(higb) from trades where amount between 5000:13000 group by ts_code

//按日期过滤，按股票代码分组
timer(10) select avg(low) from trades where trade_date > 2014.01.12 group by ts_code

```

ElasticSearch Script:

```
import urllib3
import json
import time
from elasticsearch import Elasticsearch

def main():
    total = 0
    for i in range(0, 10):
        t1 = time.time()
        search_11()
        t2 = time.time()
        total += t2-t1
    delete_scroll()
    print(total * 1000)


def delete_scroll():
    http = urllib3.PoolManager()
    r = http.request("DELETE", "http://localhost:9200/_search/scroll/_all")
    print(r.status)
    print(r.data)


def search_1():
    es = Elasticsearch(['http://localhost:9200/'])
    page = es.search(
        index='elastic',
        doc_type='type',
        scroll='2m',
        size=10000,
        body={
            "query": {
                "constant_score": {
                    "filter": {
                        "range": {
                            "trade_date": {
                                "lte": "2014.01.11"
                            }
                        }
                    }
                }
            }
        }
    )
    sid = page['_scroll_id']
    scroll_size = page['hits']['total']

    print(sid)
    print(scroll_size)
    # Start scrolling
    while (scroll_size > 0):
        print("Scrolling...")
        page = es.scroll(scroll_id=sid, scroll='2m')
        # Update the scroll ID
        sid = page['_scroll_id']
        # Get the number of results that we returned in the last scroll
        scroll_size = len(page['hits']['hits'])
        print("scroll size: " + str(scroll_size))


def search_2():
    es = Elasticsearch(['http://localhost:9200/'])
    page = es.search(
        index='elastic',
        doc_type='type',
        scroll='2m',
        size=10000,
        body={
            "query": {
                "constant_score": {
                    "filter": {
                        "range": {
                            "ts_code": {
                                "lte": "002308.SZ"
                            }
                        }
                    }
                }
            }
        }
    )
    sid = page['_scroll_id']
    scroll_size = page['hits']['total']

    print(sid)
    print(scroll_size)
    # Start scrolling
    while (scroll_size > 0):
        print("Scrolling...")
        page = es.scroll(scroll_id=sid, scroll='2m')
        # Update the scroll ID
        sid = page['_scroll_id']
        # Get the number of results that we returned in the last scroll
        scroll_size = len(page['hits']['hits'])
        print("scroll size: " + str(scroll_size))


def search_3():
    es = Elasticsearch(['http://localhost:9200/'])
    page = es.search(
        index='elastic',
        doc_type='type',
        scroll='2m',
        size=10000,
        body={
            "query": {
                "constant_score": {
                    "filter": {
                        "bool": {
                            "should": [
                                {
                                    "bool": {
                                        "must": [
                                            {"term": {"ts_code": "002308.SZ"}},
                                            {"term": {"trade_date": "2015.05.12"}}
                                        ]
                                    }
                                },
                                {
                                    "range": {
                                        "high": {
                                            "gte": 15
                                        }
                                    }
                                }
                            ]

                        }
                    }
                }
            }
        }
    )
    sid = page['_scroll_id']
    scroll_size = page['hits']['total']

    print(sid)
    print(scroll_size)
    # Start scrolling
    while (scroll_size > 0):
        print("Scrolling...")
        page = es.scroll(scroll_id=sid, scroll='2m')
        # Update the scroll ID
        sid = page['_scroll_id']
        # Get the number of results that we returned in the last scroll
        scroll_size = len(page['hits']['hits'])
        print("scroll size: " + str(scroll_size))


def search_4():
    es = Elasticsearch(['http://localhost:9200/'])
    page = es.search(
        index='elastic',
        doc_type='type',
        scroll='2m',
        size=10000,
        body={
            "query": {
                "constant_score": {
                    "filter": {
                        "range": {
                            "pre_close": {
                                "gt": 25,
                                "lt": 35
                            }
                        }
                    }
                }
            }
        }
    )
    sid = page['_scroll_id']
    scroll_size = page['hits']['total']

    print(sid)
    print(scroll_size)
    # Start scrolling
    while (scroll_size > 0):
        print("Scrolling...")
        page = es.scroll(scroll_id=sid, scroll='2m')
        # Update the scroll ID
        sid = page['_scroll_id']
        # Get the number of results that we returned in the last scroll
        scroll_size = len(page['hits']['hits'])
        print("scroll size: " + str(scroll_size))


def search_5():
    http = urllib3.PoolManager()
    data = json.dumps({
        "aggs": {
            "group_by_ts_code": {
                "terms": {
                    "field": "ts_code",
                    "size": 5000  # 跟这个size有关，是否精确
                },
                "aggs": {
                    "avg_price": {
                        "avg": {"field": "low"}
                    }
                }
            }
        },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/elastic/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


def search_6():
    http = urllib3.PoolManager()
    data = json.dumps({
        "aggs": {
            "group_by_ts_code": {
                "terms": {
                    "field": "ts_code",
                    "size": 5000  # 跟这个size有关，是否精确
                },
                "aggs": {
                    "avg_low": {
                        "avg": {"field": "low"}
                    },
                    "sum_high": {
                        "sum": {"field": "high"}
                    }
                }
            }
        },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/elastic/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))



def search_7():
    http = urllib3.PoolManager()
    data = json.dumps({
        "aggs": {
            "group_by_trade_date": {
                "terms": {
                    "field": "trade_date",
                    "size": 5000
                },
                "aggs": {
                    "max_open": {
                        "max": {"field": "open"}
                    }
                }
            }
        },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/elastic/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


def search_8():
    http = urllib3.PoolManager()
    data = json.dumps({
        "aggs": {
            "group_by_trade_date": {
                "terms": {
                    "field": "trade_date",
                    "size": 5000
                },
                "aggs": {
                    "max_open": {
                        "max": {"field": "open"}
                    },
                    "sum_pre_close": {
                        "sum": {"field": "pre_close"}
                    }
                }
            }
        },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/elastic/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


def search_9():
    http = urllib3.PoolManager()
    data = json.dumps({
        "query": {
            "constant_score": {
                "filter": {
                    "range": {
                        "amount": {
                            "gte": 5000,
                            "lte": 13000
                        }
                    }
                }
            }
        },
        "aggs": {
            "group_by_ts_code": {
                "terms": {
                    "field": "ts_code",
                    "size": 5000
                },
                "aggs": {
                    "avg_high": {
                        "avg": {"field": "high"}
                    }
                }
            }
        },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/elastic/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


def search_10():
    http = urllib3.PoolManager()
    data = json.dumps({
        "query": {
            "constant_score": {
                "filter": {
                     "range": {
                        "trade_date": {
                            "gt": "2014.01.12",
                        }
                    }
                }
            }
        },
        "aggs": {
            "group_by_ts_code": {
                "terms": {
                    "field": "ts_code",
                    "size": 5000
                },
                "aggs": {
                    "avg_price": {
                        "avg": {"field": "low"}
                    }
                }
            }
        },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/elastic/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))

main()
```

(2) US_Trades表查询性能测试用例

DolphinDB Script:

```
//根据时间过滤
timer(10) select * from trades where date >= 2008.08.08 and date <= 2010.08.08

//根据股票代码过滤
timer(10) select * from trades where PERMNO between 23230:30000

//根据股票代码、浮点型和时间过滤
timer(10) select * from trades where date between 2015.05.12:2016.05.12 and PERMNO between 23240:30000 or VOL between 1500000:2000000

//根据浮点型过滤
timer(10) select * from trades where PRC > 25 and PRC < 35

//按股票代码分组（单列）
timer(10) select avg(VOL) from trades group by TICKER

//按股票代码分组（多列）
timer(10) select avg(VOL), max(OPENPRC) from trades group by TICKER

//按时间分组（单列）
timer(10) select sum(VOL) from trades group by date

//按时间分组（多列）
timer(10) select avg(ASK), max(BID) from trades group by date

//按浮点型过滤，按股票代码分组，按股票代码升序排序
timer(10) select avg(ASK) from trades where VOL between 800000:1000000 group by PERMNO order by PERMNO asc

//按日期过滤，按股票代码分组
timer(10) select avg(VOL) from trades where date > 2014.01.12 group by PERMNO

```

ElasticSearch Script:

```
import urllib3
import json
import time
from elasticsearch import Elasticsearch

def main():
    total = 0
    for i in range(0, 10):
        t1 = time.time()
        search_9()
        t2 = time.time()
        total += t2-t1
    delete_scroll()
    print(total * 1000)


def delete_scroll():
    http = urllib3.PoolManager()
    r = http.request("DELETE", "http://localhost:9200/_search/scroll/_all")
    print(r.status)
    print(r.data)


def search_1():
    es = Elasticsearch(['http://localhost:9200/'])
    page = es.search(
        index='uscsv',
        doc_type='type',
        scroll='2m',
        size=10000,
        body={
            "query": {
                "constant_score": {
                    "filter": {
                        "range": {
                            "date": {
                                "gte": "2008/08/08",
                                "lte": "2010/08/08"
                            }
                        }
                    }
                }
            }
        }
    )
    sid = page['_scroll_id']
    scroll_size = page['hits']['total']

    print(sid)
    print(scroll_size)
    while (scroll_size > 0):
        print("Scrolling...")
        page = es.scroll(scroll_id=sid, scroll='2m')
        sid = page['_scroll_id']
        scroll_size = len(page['hits']['hits'])
        print("scroll size: " + str(scroll_size))


def search_2():
    es = Elasticsearch(['http://localhost:9200/'])
    page = es.search(
        index='uscsv',
        doc_type='type',
        scroll='2m',
        size=10000,
        body={
            "query": {
                "constant_score": {
                    "filter": {
                        "range": {
                            "PERMNO": {
                                "gte": 23230,
                                "lte": 30000
                            }
                        }
                    }
                }
            }
        }
    )
    sid = page['_scroll_id']
    scroll_size = page['hits']['total']

    print(sid)
    print(scroll_size)
    while (scroll_size > 0):
        print("Scrolling...")
        page = es.scroll(scroll_id=sid, scroll='2m')
        sid = page['_scroll_id']
        scroll_size = len(page['hits']['hits'])
        print("scroll size: " + str(scroll_size))


def search_3():
    es = Elasticsearch(['http://localhost:9200/'])
    page = es.search(
        index='uscsv',
        doc_type='type',
        scroll='2m',
        size=10000,
        body={
            "query": {
                "constant_score": {
                    "filter": {
                        "bool": {
                            "should": [
                                {
                                    "bool": {
                                        "must": [
                                            {
                                                "range": {
                                                    "date": {
                                                        "gte": "2015/05/12",
                                                        "lte": "2016/05/12"
                                                    }
                                                }
                                            },
                                            {
                                                "range": {
                                                    "PERMNO": {
                                                        "gte": "23240",
                                                        "lte": "30000"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "range": {
                                        "VOL": {
                                            "gte": 1500000,
                                            "lte": 2000000
                                        }
                                    }
                                }
                            ]

                        }
                    }
                }
            }
        }
    )
    sid = page['_scroll_id']
    scroll_size = page['hits']['total']

    print(sid)
    print(scroll_size)
    while (scroll_size > 0):
        print("Scrolling...")
        page = es.scroll(scroll_id=sid, scroll='2m')
        sid = page['_scroll_id']
        scroll_size = len(page['hits']['hits'])
        print("scroll size: " + str(scroll_size))


def search_4():
    es = Elasticsearch(['http://localhost:9200/'])
    page = es.search(
        index='uscsv',
        doc_type='type',
        scroll='2m',
        size=10000,
        body={
            "query": {
                "constant_score": {
                    "filter": {
                        "range": {
                            "PRC": {
                                "gt": 25,
                                "lt": 35
                            }
                        }
                    }
                }
            }
        }
    )
    sid = page['_scroll_id']
    scroll_size = page['hits']['total']

    print(sid)
    print(scroll_size)
    while (scroll_size > 0):
        print("Scrolling...")
        page = es.scroll(scroll_id=sid, scroll='2m')
        sid = page['_scroll_id']
        scroll_size = len(page['hits']['hits'])
        print("scroll size: " + str(scroll_size))


def search_5():
    http = urllib3.PoolManager()
    data = json.dumps({
        "aggs": {
            "group_by_ticker": {
                "terms": {
                    "field": "TICKER",
                    "size": 23934  
                },
                "aggs": {
                    "avg_price": {
                        "avg": {"field": "VOL"}
                    }
                }
            }
        },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/uscsv/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


def search_6():
    http = urllib3.PoolManager()
    data = json.dumps({
        "aggs": {
            "group_by_ticker": {
                "terms": {
                    "field": "TICKER",
                    "size": 23934 
                },
                "aggs": {
                    "avg_price": {
                        "avg": {"field": "VOL"}
                    },
                    "max_open": {
                        "max": {"field": "OPENPRC"}
                    }
                }
            }
        },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/uscsv/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


def search_7():
    http = urllib3.PoolManager()
    data = json.dumps({
        "aggs": {
            "group_by_ts_code": {
                "terms": {
                    "field": "date",
                    "size": 6828  
                },
                "aggs": {
                    "sum_vol": {
                        "sum": {"field": "VOL"}
                    }
                }
            }
        },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/uscsv/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


def search_8():
    http = urllib3.PoolManager()
    data = json.dumps({
        "aggs": {
            "group_by_date": {
                "terms": {
                    "field": "date",
                    "size": 6828
                },
                "aggs": {
                    "avg_ask": {
                        "avg": {"field": "ASK"}
                    },
                    "max_bid": {
                        "max": {"field": "BID"}
                    }
                }
            }
        },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/uscsv/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


def search_9():
    http = urllib3.PoolManager()
    data = json.dumps({
        "query": {
            "constant_score": {
                "filter": {
                    "range": {
                        "VOL": {
                            "gte": 800000,
                            "lte": 1000000
                        }
                    }
                }
            }
        },
        "aggs": {
            "group_by_permno": {
                "terms": {
                    "field": "PERMNO",
                    "size": 13314
                },
                "aggs": {
                    "avg_ask": {
                        "avg": {"field": "ASK"}
                    }
                }
            }
        },
        "sort": [
            {
                "PERMNO": {"order": "asc"}
            }
        ],
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/uscsv/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


def search_10():
    http = urllib3.PoolManager()
    data = json.dumps({
        "query": {
            "constant_score": {
                "filter": {
                     "range": {
                        "date": {
                            "gt": "2014/01/12",
                        }
                    }
                }
            }
        },
        "aggs": {
            "group_by_permno": {
                "terms": {
                    "field": "PERMNO",
                    "size": 8373
                },
                "aggs": {
                    "avg_vol": {
                        "avg": {"field": "VOL"}
                    }
                }
            }
        },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/uscsv/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))

main()
```

(3) BIG_Trades表查询性能测试用例

DolphinDB Script:

```
//根据日期、时间过滤
timer(10) t1 = select * from trades where trade_date = 2007.08.06 and trade_time between 09:45:01 : 09:45:59

//根据时间过滤，按股票代码分组（单列）
timer(10) t1 = select avg(ofr) from trades where trade_date = 2007.08.09 group by sym

//根据时间过滤，按股票代码分组（多列）
timer(10) t1 = select avg(ofr), sum(bidsiz) from trades where trade_date = 2007.08.09 group by sym

//根据日期分组（单列）
timer(10) t1 = select avg(ofr) from trades group by trade_date

//根据日期分组（多列）
timer(10) t1 = select avg(bid), max(ofr) from trades group by trade_date

//按浮点型过滤，股票代码分组，并升序排列
timer(10) t1 = select avg(bidsiz) from trades where bid between 35:40 group by sym order by sym asc

//按时间过滤，按日期分组
timer(10) t1 = select avg(bid) from trades where trade_time between 07:45:16 : 08:00:00 group by trade_date

//按日期和股票代码分组
timer(10) t1 = select max(ofr) from trades group by trade_date, sym

```

ElasticSearch Script:

```
import urllib3
import json
import time
from elasticsearch import Elasticsearch


def main():
    total = 0
    for i in range(0, 10):
        t1 = time.time()
        search_1()
        t2 = time.time()
        total += t2-t1
    delete_scroll()
    print(total * 1000)


# 删除scroll
def delete_scroll():
    http = urllib3.PoolManager()
    r = http.request("DELETE", "http://localhost:9200/_search/scroll/_all")
    print(r.status)
    print(r.data)


def search_1():
    es = Elasticsearch(['http://localhost:9200/'])
    page = es.search(
        index='hundred',
        doc_type='type',
        scroll='2m',
        size=10000,
        body={
            "query": {
                "constant_score": {
                    "filter": {
                        "bool": {
                            "must": [
                                {
                                    "term": {
                                        "DATE": "20070806"
                                    }

                                },
                                {
                                    "range": {
                                        "TIME": {
                                            "gte": "09:45:01",
                                            "lte": "09:45:59"
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
    )
    sid = page['_scroll_id']
    scroll_size = page['hits']['total']

    print(sid)
    print(scroll_size)
    # Start scrolling
    while (scroll_size > 0):
        print("Scrolling...")
        page = es.scroll(scroll_id=sid, scroll='2m')
        # Update the scroll ID
        sid = page['_scroll_id']
        # Get the number of results that we returned in the last scroll
        scroll_size = len(page['hits']['hits'])
        print("scroll size: " + str(scroll_size))


def search_2():
    http = urllib3.PoolManager()
    data = json.dumps({
        "query": {
            "constant_score": {
                "filter": {
                    "term": {
                        "DATE": "20070809"
                    }
                }
            }
        },
        "aggs": {
            "group_by_symbol": {
                "terms": {
                    "field": "SYMBOL",
                    "size": 8374
                },
                "aggs": {
                    "avg_price": {
                        "avg": {"field": "OFR"}
                    }
                }
            }
        },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/hundred/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


def search_3():
    http = urllib3.PoolManager()
    data = json.dumps({
        "query": {
            "constant_score": {
                "filter": {
                    "term": {
                        "DATE": "20070809"
                    }
                }
            }
        },
        "aggs": {
            "group_by_symbol": {
                "terms": {
                    "field": "SYMBOL",
                    "size": 8374
                },
                "aggs": {
                    "avg_price": {
                        "avg": {"field": "OFR"}
                    },
                    "sum_bidsiz": {
                        "sum": {"field": "BIDSIZ"}
                    }
                }
            }
        },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/hundred/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


def search_4():
    http = urllib3.PoolManager()
    data = json.dumps({
        "aggs": {
            "group_by_date": {
                "terms": {
                    "field": "DATE",
                    "size": 4
                },
                "aggs": {
                    "avg_ofr": {
                        "avg": {"field": "OFR"}
                    }
                }
            }
        },
        "_source": ["DATE", "BID", "OFR"]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/hundred/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


def search_5():
    http = urllib3.PoolManager()
    data = json.dumps({
        "aggs": {
            "group_by_date": {
                "terms": {
                    "field": "DATE",
                    "size": 4
                },
                "aggs": {
                    "max_ofr": {
                        "max": {"field": "OFR"}
                    },
                    "avg_bid": {
                        "avg": {"field": "BID"}
                    }
                }
            }
        },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/hundred/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


def search_6():
    http = urllib3.PoolManager()
    data = json.dumps({
        "query": {
            "constant_score": {
                "filter": {
                    "range": {
                        "BID": {
                            "gte": 35,
                            "lte": 40
                        }
                    }
                }
            }
        },
        "aggs": {
            "group_by_symbol": {
                "terms": {
                    "field": "SYMBOL",
                    "size": 8374
                },
                "aggs": {
                    "avg_BIDSIZ": {
                        "avg": {"field": "BIDSIZ"}
                    }

                }
            }
        },
        "sort": [
            {
                "SYMBOL": {"order": "asc"}
            }
        ],
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/hundred/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


def search_7():
    http = urllib3.PoolManager()
    data = json.dumps({
        "query": {
            "constant_score": {
                "filter": {
                     "range": {
                        "TIME": {
                            "gte": "7:45:16",
                            "lte": "8:00:00"
                        }
                    }
                }
            }
        },
        "aggs": {
            "group_by_date": {
                "terms": {
                    "field": "DATE",
                    "size": 4
                },
                "aggs": {
                    "avg_vol": {
                        "avg": {"field": "BID"}
                    }
                }
            }
        },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/hundred/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


def search_8():
    http = urllib3.PoolManager()
    data = json.dumps({
        "aggs": {
                    "group_by_bid": {
                        "terms": {
                            "field": "DATE",
                            "size": 4
                        },
                        "aggs": {
                            "group_by_symbol": {
                                "terms": {
                                    "field": "SYMBOL"
                                }，
								"aggs": {
                                	"max_ofr": {
                                    	"max": {"field": "OFR"}
                               	 	}
                            	 }
                            }
                        }
                    }
                },
        "_source": [""]
    }).encode("utf-8")
    r = http.request("GET", "http://localhost:9200/hundred/_search", body=data,
                     headers={'Content-Type': 'application/json'})
    print(r.status)
    print(json.loads(r.data.decode()))


main()
```

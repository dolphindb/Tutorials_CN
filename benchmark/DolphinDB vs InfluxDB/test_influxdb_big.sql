show databases
drop database test2
create database test2
create retention policy one_day on test2 duration inf replication 1 shard duration 1d default

use test2

influx.exe -import -path=D:/TAQ.txt -precision=ms -database=test2

select * from taq limit 50


---------------- 综合查询性能测试
-- 查询总记录数
explain analyze select count(*) from taq where time <= '2007-08-07'
---------------
.
└── select
    ├── execution_time: 18.237080262s
    ├── planning_time: 6m50.574153806s
    ├── total_time: 7m8.811234068s



-- 1. 点查询：按股票代码、时间查询
explain analyze select * from taq where symbol = 'IBM' and '2007-08-06' <= time and time < '2007-08-07'
---------------
.
└── select
    ├── execution_time: 566.370502ms
    ├── planning_time: 3.742844ms
    ├── total_time: 570.113346ms



-- 2. 范围查询：查询某时间段内的某些股票的所有记录
explain analyze select symbol, time, bid, ofr from taq where (symbol = 'IBM' or symbol = 'MSFT' or symbol = 'GOOG' or symbol = 'YHOO') and (('2007-08-03 09:30:00' <= time and time < '2007-08-03 09:40:00') or ('2007-08-04 09:30:00' <= time and time < '2007-08-04 09:40:00') or ('2007-08-05 09:30:00' <= time and time < '2007-08-05 09:40:00') or ('2007-08-06 09:30:00' <= time and time < '2007-08-06 09:40:00') or ('2007-08-07 09:30:00' <= time and time < '2007-08-07 09:40:00')) and bid > 0 and ofr > bid
---------------


explain analyze select symbol, time, bid, ofr from taq where (symbol = 'IBM' or symbol = 'MSFT' or symbol = 'GOOG' or symbol = 'YHOO') and (('2007-08-03 09:30:00' <= time and time < '2007-08-03 09:40:00') or ('2007-08-04 09:30:00' <= time and time < '2007-08-04 09:40:00'))
-- 结果为空


-- 3. top + 排序: 按 [股票代码、日期] 过滤，按 [卖出与买入价格差] 降序 排序
-- 不能排序


-- 4. 聚合查询.单分区维度：查询每分钟的最大卖出报价、最小买入报价
explain analyze select max(bid) as max_bid, min(ofr) as min_ofr from taq where '2007-08-02' <= time and time < '2007-08-03' and symbol = 'IBM' and ofr > bid group by time(1m)
---------------
.
└── select
    ├── execution_time: 110.926258ms
    ├── planning_time: 18.209847ms
    ├── total_time: 129.136105ms
    
    

-- 5. 聚合查询.多分区维度 + 排序：按股票代码分组查询每分钟的买入报价标准差和买入数量总和
-- 不能排序



-- 6. 经典查询：按 [多个股票代码、日期，时间范围、报价范围] 过滤，查询 [股票代码、时间、买入价、卖出价]
explain analyze select symbol, time, bid, ofr from taq where (symbol = 'IBM' or symbol = 'MSFT' or symbol = 'GOOG' or symbol = 'YHOO') and '2007-08-03 09:30:00' <= time and time < '2007-08-03 14:30:00' and bid > 0 and ofr > bid;
---------------
.
└── select
    ├── execution_time: 268.204µs
    ├── planning_time: 16.614096ms
    ├── total_time: 16.8823ms



-- 7. 经典查询：按 [日期、时间范围、卖出买入价格条件、股票代码] 过滤，查询 (各个股票 每分钟) [平均变化幅度]
explain analyze select first(symbol), mean(tmp_spread) * 2 as spread from (select symbol, (ofr - bid) / (ofr + bid) as tmp_spread from taq where '2007-08-01 09:30:00' <= time and time < '2007-08-01 16:00:00' and bid > 0 and ofr > bid) where '2007-08-01 09:30:00' <= time and time < '2007-08-01 16:00:00' group by symbol, time(1m)
---------------
.
└── select
    ├── execution_time: 32m29.701935295s
    ├── planning_time: 5.358718424s
    ├── total_time: 32m35.060653719s
-- 关于时间范围的 where 需要重复指定，否则会从最旧的数据时间开始一直扫描到当前时间



-- 8. 经典查询：计算 某天 (每个股票 每分钟) 最大卖出与最小买入价之差
explain analyze select symbol, max(ofr) - min(bid) as gap from taq where '2007-08-03' <= time and time < '2007-08-04' and bid > 0 and ofr > bid group by symbol, time(1m);
-- ERR: mixing multiple selector functions with tags or fields is not supported



-- 9. 按 [股票代码、日期段、时间段] 过滤, 查询 (每天，时间段内每分钟) 均价
explain analyze select mean(tmp_avg_price) / 2.0 from (select ofr + bid as tmp_avg_price from taq where symbol = 'IBM' and '2007-08-01' <= time and time < '2007-08-07') where '2007-08-01' <= time and time < '2007-08-07' group by time(1m)
---------------
.
└── select
    ├── execution_time: 1.771671431s
    ├── planning_time: 1.69631239s
    ├── total_time: 3.467983821s



-- 10. 按 [日期段、时间段] 过滤, 查询 (每股票，每天) 均价
explain analyze select first(symbol), mean(tmp_avg_price) / 2.0 from (select symbol, (ofr + bid) as tmp_avg_price from taq where '2007-08-05 09:30:00' <= time and time <= '2007-08-07 16:00:00') where '2007-08-05 09:30:00' <= time and time <= '2007-08-07 16:00:00' group by symbol, time(1d)
---------------
.
└── select
    ├── execution_time: 34m45.256436988s
    ├── planning_time: 4.563051279s
    ├── total_time: 34m49.819488267s


-- 11. 计算 某个日期段 有成交记录的 (每天, 每股票) 加权均价，并按 (日期，股票代码) 排序
-- 不支持排序



















































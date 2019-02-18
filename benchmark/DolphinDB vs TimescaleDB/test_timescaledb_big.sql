create extension if not exists timescaledb cascade;

drop table if exists taq;

-- SYMBOL,DATE,TIME,BID,OFR,BIDSIZ,OFRSIZ,MODE,EX,MMID

-- create type Symbol as enum (...);    见 create_symbols_enum.sql

create type MMID as enum ('FLOW', 'EDGX', 'EDGA', 'NASD', '');

create table taq (
    symbol Symbol,
    date date,
    time time without time zone,
    bid double precision,
    ofr double precision,
    bidsiz integer,
    ofrsiz integer,
    mode integer,
    ex character,
    mmid Mmid
);


select create_hypertable('taq', 'date', 'symbol', 100, chunk_time_interval => interval '1 day');


---------------- 综合查询性能测试
-- 查询总记录数
select count(*) from taq
where date <= '2007.08.07';



-- 1. 点查询：按股票代码、时间查询
explain analyze
select *
from taq
where
    symbol = 'IBM' and
    date   = '2007.08.07';



-- 2. 范围查询：查询某时间段内的某些股票的所有记录
explain analyze
select symbol, time, bid, ofr
from taq
where
    symbol in ('IBM', 'MSFT', 'GOOG', 'YHOO') and
    '2007.08.03' <= date and date <= '2007.08.07' and
    '09:30:00'   <= time and time <  '09:30:59'   and
    bid > 0 and
    ofr > bid;



-- 3. top + 排序: 按 [股票代码、日期] 过滤，按 [卖出与买入价格差] 降序 排序
explain analyze
select *
from taq
where
    symbol in ('IBM', 'MSFT', 'GOOG', 'YHOO') and
    date =  '2007.08.07' and
    time >= '07:36:37'   and
    ofr > bid
order by (ofr - bid) desc
limit 1000;



-- 4. 聚合查询.单分区维度：查询每分钟的最大卖出报价、最小买入报价
explain analyze
select
    date_trunc('minute', time)  as one_minute,
    max(bid)                    as max_bid,
    min(ofr)                    as min_ofr
from taq
where
    date = '2007.08.02' and
    symbol = 'IBM' and
    ofr > bid
group by one_minute;



-- 5. 聚合查询.多分区维度 + 排序：按股票代码分组查询每分钟的买入报价标准差和买入数量总和
explain analyze
select
    symbol,
    date_trunc('minute', time)  as one_minute,
    stddev(bid)                 as std_bid,
    sum(bidsiz)                 as sum_bidsiz
from taq
where
    date = '2007.08.07' and
    '09:00:00' <= time  and time <= '21:00:00' and
    symbol in ('IBM', 'MSFT', 'GOOG', 'YHOO') and
    bid >= 20 and
    ofr > 20
group by symbol, one_minute
order by symbol asc, one_minute asc;



-- 6. 经典查询：按 [多个股票代码、日期，时间范围、报价范围] 过滤，查询 [股票代码、时间、买入价、卖出价]
explain analyze
select symbol, time, bid, ofr
from taq
where
    symbol in ('IBM', 'MSFT', 'GOOG', 'YHOO') and
    date = '2007-08-03' and
    '09:30:00' <= time and time < '14:30:00' and
    bid > 0 and
    ofr > bid;




-- 7. 经典查询：按 [日期、时间范围、卖出买入价格条件、股票代码] 过滤，查询 (各个股票 每分钟) [平均变化幅度]
explain analyze
select
    symbol,
    date_trunc('minute', time) as one_minute,
    avg( (ofr - bid) / (ofr + bid) ) * 2 as spread
from taq
where
    date = '2007.08.01'  and
    '09:30:00' <= time and time < '16:00:00'  and
    bid > 0 and
    ofr > bid
group by symbol, one_minute;



-- 8. 经典查询：计算 某天 (每个股票 每分钟) 最大卖出与最小买入价之差
explain analyze
select
    symbol,
    date_trunc('minute', time) as one_minute,
    max(ofr) - min(bid) as gap
from taq
where
    date = '2007-08-03' and
    bid > 0 and
    ofr > bid
group by symbol, one_minute;



-- 9. 按 [股票代码、日期段、时间段] 过滤, 查询 (每天，时间段内每分钟) 均价
explain analyze
select
    date,
    date_trunc('minute', time) as one_minute,
    avg(ofr + bid) / 2.0 as avg_price
from taq
where
    symbol = 'IBM' and
    '2007-08-01' <= date and date <= '2007-08-07' and
    '09:30:00'   <= time and time < '16:00:00'
group by date, one_minute;



-- 10. 按 [日期段、时间段] 过滤, 查询 (每股票，每天) 均价
explain analyze
select
    symbol,
    date,
    avg(ofr + bid) / 2.0 as avg_price
from taq
where
    '2007-08-05' <= date and date <= '2007-08-07' and
    '09:30:00'   <= time and time <= '16:00:00'
group by symbol, date;



-- 11. 计算 某个日期段 有成交记录的 (每天, 每股票) 加权均价，并按 (日期，股票代码) 排序
explain analyze
select
    date,
    symbol,
    sum(bid * bidsiz) / sum(bidsiz) as vwab
from taq
where
    '2007-08-05' <= date and date <= '2007-08-06'
group by date, symbol
    having sum(bidsiz) > 0
order by date desc, symbol;





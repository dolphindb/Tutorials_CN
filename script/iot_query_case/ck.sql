//1.建表
create table noise (
    tenantId UInt32,
    deviceId UInt32,
    soundPressureLevel Float64,
    soundPowerLevel Float64,
    ts DateTime64(3, 'Asia/Shanghai'),
    date DATE
)ENGINE=MergeTree
order by (tenantId, ts)
PARTITION BY (tenantId, date)


//2.导入数据
cat noise20220101.csv | clickhouse-client --query "INSERT INTO noise FORMAT CSV" --input_format_allow_errors_num=10
//合并下noise数据
OPTIMIZE TABLE noise

//clear os cache
//sudo bash -c "echo 3 > /proc/sys/vm/drop_caches"  


//3.测试
//3.1 case1
select * 
from noise 
where tenantId = 1055
and deviceId = 10067
and date = '2022-01-01'
order by ts asc
limit 100

//3.2 case2
select * 
from noise 
where tenantId = 1055
and date = '2022-01-01'
order by ts desc
limit 1 by deviceId


//3.3 case3
select
     min(ts) as startTs
    ,max(ts) as endTs
    ,max(soundPressureLevel)
    ,avg(soundPressureLevel)
    ,max(soundPowerLevel) 
    ,avg(soundPowerLevel) 
from noise
where tenantId = 1055
and deviceId = 10067
and date = '2022-01-01'
and ts between '2022.01.01T00:50:15.518' and '2022.01.01T00:55:15.518'


//3.4 case4
select
	*
from noise
where tenantId = 1055
and deviceId = 10067
and date = '2022-01-01'

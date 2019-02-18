----------------------------------------- TimescaleDB 性能测试脚本

--------------------- TimescaleDB 安装、配置（见 test_timescaledb.sh）

--------------------- 创建数据表
create extension if not exists timescaledb cascade;
create extension if not exists tablefunc   cascade;
create extension if not exists pg_prewarm  cascade;

drop table if exists device_info;

create type BatteryStatus as enum ('discharging', 'charging');
create type ApiVersion as enum ('19', '21', '22', '23');
create type Manufacturer as enum ('iobeam');
create type Model as enum ('focus', 'mustang', 'pinto');
create type OSName as enum ('4.4.4', '5.0.0', '5.1.0', '6.0.1');


create table device_info (
    device_id       text,
    api_version     ApiVersion,
    manufacturer    Manufacturer,
    model           Model,
    os_name         OSName
);



drop table if exists readings;
create table readings (
    time                timestamp with time zone not null,
    
    device_id           text,
    
    battery_level       integer,
    battery_status      BatteryStatus,
    battery_temperature double precision,
    
    bssid               text,
    
    cpu_avg_1min        double precision,
    cpu_avg_5min        double precision,
    cpu_avg_15min       double precision,
    
    mem_free            bigint,
    mem_used            bigint,
    
    rssi                smallint,
    ssid                text
);


SELECT create_hypertable('readings', 'time', chunk_time_interval => interval '1 day');


--------------------- 导入数据（见 test_timescaledb.sh）

-- 查看数据
-- head -n 50 /data/devices/devices_big_device_info.csv
-- head -n 50 /data/devices/devices_big_readings.csv





---------------------- 占用空间分析
SELECT *,
    pg_size_pretty(toast_bytes) AS toast,
    pg_size_pretty(index_bytes) AS INDEX,
    pg_size_pretty(table_bytes) AS TABLE,
    pg_size_pretty(total_bytes) AS total
   FROM (
   SELECT *, total_bytes-index_bytes-COALESCE(toast_bytes, 0) AS table_bytes FROM (
       SELECT c.oid,nspname AS table_schema, relname AS TABLE_NAME
              , c.reltuples AS row_estimate
              , pg_total_relation_size(c.oid) AS total_bytes
              , pg_indexes_size(c.oid) AS index_bytes
              , pg_total_relation_size(reltoastrelid) AS toast_bytes
           FROM pg_class c
           LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE relkind = 'r'
       ) a
   ) a;

select pg_size_pretty(pg_database_size('test'));

-- 无法统计 TimescaleDB 的 hyper_table
select pg_size_pretty(pg_relation_size('readings'));
select pg_size_pretty(pg_total_relation_size('readings'));


select pg_size_pretty(pg_database_size('test3'));

select count(*) from readings;

-------------------- 建立索引
-- By default, TimescaleDB automatically creates a time index on your data when a hypertable is created.
-- create index on readings (time desc);

create index on readings (device_id, time desc);
-- 1 m 23 s

create index on readings (ssid, time desc);
-- 48 s



--------------------- 导出数据（见 test_timescaledb.sh）



-------------------- 加载数据表到内存
select pg_prewarm('readings');

select pg_prewarm('_hyper_2_41_chunk');
select pg_prewarm('_hyper_2_42_chunk');
select pg_prewarm('_hyper_2_43_chunk');
select pg_prewarm('_hyper_2_44_chunk');



--------------------- 查询测试
-- 1. 查询总记录数
explain analyze
select count(*) from readings;



-- 2. 点查询：按设备 ID 查询记录数
explain analyze
select count(*)
from readings
where device_id = 'demo000101';



-- 3. 范围查询.单分区维度：查询某时间段内的所有记录
explain analyze
select *
from readings
where '2016-11-17 21:00:00' <= time and time < '2016-11-17 21:30:00';



-- 4. 范围查询.多分区维度: 查询某时间段内某些设备的所有记录
explain analyze
select *
from readings
where
    '2016-11-17 20:00:00' <= time and time < '2016-11-17 20:30:00' and
    device_id in ('demo000001','demo000010','demo000100','demo001000');



-- 5. 范围查询.分区及非分区维度：查询某时间段内某些设备的特定记录
explain analyze
select *
from readings
where
    '2016-11-15 08:00:00' <= time and time < '2016-11-17 08:30:00' and
    device_id in ('demo000001','demo000010','demo000100','demo001000') and
    battery_level <= 10 and
    battery_status = 'discharging';



-- 6. 精度查询：查询各设备在每 5 min 内的内存使用量最大、最小值之差
explain analyze
select
    time_bucket('5 minutes', time) as five_minutes,
    max(mem_used) - min(mem_used)
from readings
group by five_minutes;



-- 7. 聚合查询.单分区维度.max：设备电池最高温度
explain analyze
select device_id, max(battery_temperature)
from readings
group by device_id;



-- 8. 聚合查询.多分区维度.avg：计算各时间段内设备电池平均温度
explain analyze
select
    device_id,
    date_trunc('hour', time) as one_hour,
    avg(battery_temperature)
from readings
group by device_id, one_hour;



-- 9. 对比查询：对比 10 个设备 24 小时中每个小时平均电量变化情况
explain analyze
select *
from crosstab('
    select
        to_char(one_hour, ''YYYY.MM.DD HH24''),
        device_id,
        battery
    from (
        select
            date_trunc(''hour'', time) as one_hour,
            device_id,
            avg(battery_level) as battery
        from readings
        where
            ''2016-11-15 12:00:00'' <= time and time <= ''2016-11-16 12:00:00'' and
            device_id < ''demo000010''
        group by one_hour, device_id
        order by 1, 2
    ) ct')
as (
    one_hour text,
    demo000000 numeric,
    demo000001 numeric,
    demo000002 numeric,
    demo000003 numeric,
    demo000004 numeric,
    demo000005 numeric,
    demo000006 numeric,
    demo000007 numeric,
    demo000008 numeric,
    demo000009 numeric
);



-- 10. 关联查询.等值连接：查询连接某个 WiFi 的所有设备的型号
explain analyze
select distinct model
from readings join device_info on readings.device_id = device_info.device_id
where ssid = 'demo-net';



-- 11. 关联查询.左连接：列出所有的 WiFi，及其连接设备的型号、系统版本，并去除重复条目
explain analyze
select distinct ssid, bssid, time, model, os_name
from readings left join device_info
    on readings.device_id = device_info.device_id
where '2016-11-15 12:00:00' <= time and time <= '2016-11-15 12:01:00'
order by ssid, time;



-- 12. 关联查询.笛卡尔积（cross join）
explain analyze
select *
from (select * from readings where '2016-11-15 12:00:00' <= time and time <= '2016-11-15 12:01:00') sub cross join device_info;



-- 13. 关联查询.全连接（full join）
explain analyze
select *
from readings full join device_info on readings.device_id = device_info.device_id;



-- 14. 经典查询：计算某时间段内高负载高电量设备的内存大小
explain analyze
select
    date_trunc('hour', time) one_hour,
    device_id,
    max(mem_free + mem_used) as mem_all
from readings
where
    time <= '2016-11-18 21:00:00' and
    battery_level >= 90 and
    cpu_avg_1min > 90
group by one_hour, device_id;



-- 15. 经典查询：统计连接不同网络的设备的平均电量和最大、最小电量，并按平均电量降序排列
explain analyze
select
    ssid,
    max(battery_level) max_battery,
    avg(battery_level) avg_battery,
    min(battery_level) min_battery
from readings
group by ssid
order by avg_battery desc;



-- 16. 经典查询：查找所有设备平均负载最高的时段，并按照负载降序排列、时间升序排列
explain analyze
select
    time_bucket('1 hour', time) as one_hour,
    floor(avg(cpu_avg_15min)) as load
from readings
where '2016-11-16 00:00:00' <= time and time <= '2016-11-18 00:00:00'
group by one_hour
order by load desc, one_hour asc;




-- 17. 经典查询：计算各个时间段内某些设备的总负载，并将时段按总负载降序排列
explain analyze
select
    time_bucket('1 hour', time) as one_hour,
    sum(cpu_avg_15min) sum_load
from readings
where
    '2016-11-15 12:00:00' <= time and time <= '2016-11-16 12:00:00' and
    device_id in ('demo000001','demo000010','demo000100','demo001000')
group by one_hour
order by sum_load desc;




-- 18. 经典查询：查询充电设备的最近 20 条电池温度记录
explain analyze
select
    time,
    device_id,
    battery_temperature
from readings
where battery_status = 'charging'
order by time desc
limit 20;



-- 19. 经典查询：未在充电的、电量小于 33% 的、平均 1 分钟内最高负载的 5 个设备
explain analyze
select
    readings.device_id,
    battery_level,
    battery_status,
    cpu_avg_1min
from readings join device_info on readings.device_id = device_info.device_id
where battery_level < 33 and battery_status = 'discharging'
order by cpu_avg_1min desc, time desc
limit 5;



-- 20. 经典查询：某两个型号的设备每小时最低电量的前 20 条数据
explain analyze
select
    date_trunc('hour', time) "hour",
    min(battery_level) min_battery_level
from readings
where device_id in (
    select distinct device_id
    from device_info
    where model = 'pinto' or model = 'focus'
    )
group by "hour"
order by "hour" asc
limit 20;









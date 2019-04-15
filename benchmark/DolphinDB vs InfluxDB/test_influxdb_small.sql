
show databases
drop database test
create database test

create retention policy one_day on test duration inf replication 1 shard duration 1d default

use test


show measurements
show tag keys
show field keys
show retention policies on test
show series limit 50
show diagnostics

SELECT * FROM /.*/ LIMIT 1


insert readings,device_id=demo00000,battery_status=discharging,bssid=A0:B1:C5:D2:E0:F3,ssid=stealth-net battery_level=96,battery_temperature=91.7,cpu_avg_1min=5.26,cpu_avg_5min=6.172,cpu_avg_15min=6.51066666666667,mem_free=650609585,mem_used=349390415,rssi=-42 1479211200
insert readings,device_id=demo00001,battery_status=discharging,bssid=A0:B1:C5:D2:E0:F3,ssid=stealth-net battery_level=96,battery_temperature=91.7,cpu_avg_1min=5.26,cpu_avg_5min=6.172,cpu_avg_15min=6.51066666666667,mem_free=650609585,mem_used=349390415,rssi=-42 1479211200
insert readings,device_id=demo00001,battery_status=charging,bssid=A0:B1:C5:D2:E0:F3,ssid=stealth-net battery_level=96,battery_temperature=91.7,cpu_avg_1min=5.26,cpu_avg_5min=6.172,cpu_avg_15min=6.51066666666667,mem_free=650609585,mem_used=349390415,rssi=-42 1479211200

> show tag keys
name: readings
tagKey
------
battery_status
bssid
device_id
ssid

> show field keys
name: readings
fieldKey            fieldType
--------            ---------
battery_level       float
battery_temperature float
cpu_avg_15min       float
cpu_avg_1min        float
cpu_avg_5min        float
mem_free            float
mem_used            float
rssi                float



SELECT mean("battery_level") AS "mean_battery_level", mean("cpu_avg_1min") AS "mean_cpu_avg_1min", mean("battery_temperature") AS "mean_battery_temperature" FROM "test"."one_day"."readings" WHERE time > :dashboardTime: AND "device_id"='demo000000' GROUP BY time(:interval:), "battery_status" FILL(null)


explain analyze select * from test.one_day.readings limit 50

select * from readings where '2016-11-18 00:00:00' <= time and time < '2016-11-19 00:00:00' limit 50


--------------------- 查询测试

use test



--------------------- 1. 查询总记录数
explain analyze select count(*) from readings
---------------
.
└── select
    ├── execution_time: 547.328385ms
    ├── planning_time: 6.132260878s
    ├── total_time: 6.679589263s



--------------------- 2. 点查询：按设备 ID 查询记录数
explain analyze select count(*) from readings where device_id = 'demo000101'
---------------
.
└── select
    ├── execution_time: 525.284µs
    ├── planning_time: 6.626826ms
    ├── total_time: 7.15211ms



--------------------- 3. 范围查询：查询某时间段内的所有记录
explain analyze select * from readings where '2016-11-17 21:00:00' <= time and time < '2016-11-17 21:30:00'
---------------
.
└── select
    ├── execution_time: 474.159215ms
    ├── planning_time: 115.071642ms
    ├── total_time: 589.230857ms



--------------------- 4. 范围查询.多维度: 查询某时间段内某些设备的所有记录
explain analyze select * from readings where '2016-11-17 20:00:00' <= time and time < '2016-11-17 20:30:00' and (device_id = 'demo000000' or device_id = 'demo000010' or device_id = 'demo000100' or device_id = 'demo001000' )
---------------
.
└── select
    ├── execution_time: 2.080127ms
    ├── planning_time: 1.846784ms
    ├── total_time: 3.926911ms




--------------------- 5. 范围查询.分区及非分区维度：查询某时间段内某些设备的特定记录
explain analyze select * from readings where '2016-11-15 08:00:00' <= time and time < '2016-11-17 08:30:00' and (device_id = 'demo000000' or device_id = 'demo000010' or device_id = 'demo000100' or device_id = 'demo001000') and battery_level <= 10 and battery_status = 'discharging'
---------------
.
└── select
    ├── execution_time: 11.195308ms
    ├── planning_time: 8.124784ms
    ├── total_time: 19.320092ms



--------------------- 6. 精度查询：查询各设备在每 5 min 内的内存使用量最大、最小值之差
explain analyze select max(mem_used) - min(mem_used) from readings group by time(5m) where '2016-11-15' <= time and time < '2016-11-19'
---------------
.
└── select
    ├── execution_time: 10.302680219s
    ├── planning_time: 258.327189ms
    ├── total_time: 10.561007408s


--------------------- 7. 聚合查询.单分区维度.max：设备电池最高温度
explain analyze select device_id, max(battery_temperature) from readings group by device_id where '2016-11-15' <= time and time < '2016-11-19'
.
└── select
    ├── execution_time: 195.71771ms
    ├── planning_time: 1.206235533s
    ├── total_time: 1.401953243s



--------------------- 8. 聚合查询.多分区维度.avg：计算各时间段内设备电池平均温度
explain analyze select mean(battery_temperature) from readings group by device_id, time(1h) where '2016-11-15' <= time and time < '2016-11-19'
---------------
.
└── select
    ├── execution_time: 23.877186301s
    ├── planning_time: 1.19952429s
    ├── total_time: 25.076710591s



--------------------- 14. 经典查询：计算某时间段内高负载高电量设备的内存大小
explain analyze select max(mem_total) from (select mem_free + mem_used as mem_total from readings where time <= '2016-11-18 21:00:00' and battery_level >= 90 and cpu_avg_1min > 90) where time <= '2016-11-18 21:00:00' group by time(1h), device_id;
在 InfluxDB 中函数的参数只能是某一个 field ，而不能是 field 的表达式，因此只能使用 subquery，非常繁琐
---------------
.
└── select
    ├── execution_time: 14.728465496s
    ├── planning_time: 1.295825983s
    ├── total_time: 16.024291479s
explain analyze select max(mem_free + mem_used) from readings where time <= '2016-11-18 21:00:00' and battery_level >= 90 and cpu_avg_1min > 90 group by time(1h), device_id;
-- ERR: expected field argument in max()



-- 15. 经典查询：统计连接不同网络的设备的平均电量和最大、最小电量，并按平均电量降序排列
explain analyze select ssid, max(battery_level) as max_battery, avg(battery_level) as avg_battery, min(battery_level) as min_battery from readings group by ssid order by avg_battery desc;
-- ERR: error parsing query: only ORDER BY time supported at this time
-- InfluxDB 不支持对除 time 以外的 tag, field 进行排序
-- https://github.com/influxdata/influxdb/issues/3954


-- 16. 经典查询：查找所有设备平均负载最高的时段，并按照负载降序排列、时间升序排列
-- 不支持


-- 17. 经典查询：计算各个时间段内某些设备的总负载，并将时段按总负载降序排列
-- 不支持



-- 18. 经典查询：查询充电设备的最近 20 条电池温度记录
explain analyze select time, device_id, battery_temperature from readings where battery_status = 'charging' order by time desc limit 20;
---------------
.
└── select
    ├── execution_time: 4.261435ms
    ├── planning_time: 22.813239ms
    ├── total_time: 27.074674ms



-- 19. 经典查询：未在充电的、电量小于 33% 的、平均 1 分钟内最高负载的 5 个设备
-- 不支持表连接




-- 20. 经典查询：某两个型号的设备每小时最低电量的前 20 条数据
-- InfluxDB 不支持 IN 关键字




































































































































































































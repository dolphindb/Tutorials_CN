# ------------ 安装 InfluxDB
wget https://dl.influxdata.com/influxdb/releases/influxdb_1.7.5_amd64.deb
dpkg -i influxdb_1.7.5_amd64.deb


# ------------ 程序控制
ps -elf | grep influx
ps -elf | grep chronograf

service influxdb start
service influxdb stop

influx

dstat -cmdnlgpy --socket


# ------------ 导入数据
cd /data/devices
aria2c -s 16 -x 16 http://shenhongfei.site/File/readings.zip
influx -import -path=/data/devices/readings.txt -precision=s -database=test



# ------------ 导出数据
# --- 非 CSV 格式
time influx_inspect export -database test -retention one_day -datadir /data/influxdb/data -waldir /data/influxdb/wal -out /data/devices/export.txt
# real    3m7.198s


# --- CSV 格式
time influx -database 'test' -execute 'SELECT * FROM readings where time ' -format csv > /data/devices/export.csv
# fatal error: runtime: out of memory

# time influx -database 'test' -format csv -execute "select * from readings where '2016-11-17 00:00:00' <= time and time < '2016-11-18 00:00:00'" > /data/devices/export_17.csv
for i in 1{5..8}; do
    time influx -database 'test' -format csv -execute "select * from readings where '2016-11-$i 00:00:00' <= time and time < '2016-11-$((i+1)) 00:00:00'" > /data/devices/export_$i.csv
done

# real    0m47.667s
# real    1m40.313s
# real    1m39.393s
# real    1m35.276s
# total 5 min 41 s



# ------------ 安装 Chronograf
aria2c  -s 16 -x 16 https://dl.influxdata.com/chronograf/releases/chronograf_1.7.9_amd64.deb
aria2c --min-split-size=1M -s 16 -x 16 http://shenhongfei.site/File/chronograf_1.7.9_amd64.deb
dpkg -i chronograf_1.7.9_amd64.deb



# ------------ 查看空间占用
du -sh /data/influxdb
# 1.2G

mv /var/lib/influxdb /data/influxdb

rm -rf /data/influxdb/*

ll /data/influxdb/




cd /data/
cd /data/TAQ
nohup node test_script_big_1.js 2>&1 > 1.log &
nohup node test_script_big_2.js 2>&1 > 2.log &
nohup node test_script_big_3.js 2>&1 > 3.log &
nohup node test_script_big_6.js 2>&1 > 6.log &
nohup node test_script_big_7.js 2>&1 > 7.log &
ll -h /data/TAQ/TAQ20070801.txt
ll -h /data/TAQ/TAQ20070802.txt
ll -h /data/TAQ/

ps -elf | grep node
kill 14981

tail /data/TAQ/TAQ20070801.txt
tail /data/TAQ/csv/TAQ20070801.csv

tail /data/TAQ/TAQ20070802.txt
tail /data/TAQ/csv/TAQ20070801.csv

tail -f /data/1.log

tail /data/TAQ/csv/TAQ20070801.csv

tail -f nohup.out

head /data/TAQ/TAQ20070801.txt

cd /data/TAQ


tail /data/TAQ/TAQ20070801.txt


dstat -cmdnlgpy --socket

nohup influx -import -path=/data/TAQ/TAQ20070801.txt -precision=ms -database=test2 2>&1 > import1.log &
nohup influx -import -path=/data/TAQ/TAQ20070802.txt -precision=ms -database=test2 2>&1 > import2.log &
nohup influx -import -path=/data/TAQ/TAQ20070803.txt -precision=ms -database=test2 2>&1 > import3.log &
nohup influx -import -path=/data/TAQ/TAQ20070806.txt -precision=ms -database=test2 2>&1 > import6.log &
nohup influx -import -path=/data/TAQ/TAQ20070807.txt -precision=ms -database=test2 2>&1 > import7.log &


tail -f import1.log

grep -C 20 'VNQ,' /data/TAQ/csv/TAQ20070801.csv


kill 15559


ps -elf | grep influx



nohup time influx -database 'test2' -execute "explain analyze select first(symbol), mean(tmp_spread) * 2 as spread from (select symbol, (ofr - bid) / (ofr + bid) as tmp_spread from taq where '2007-07-31 09:30:00' <= time and time < '2007-08-01 16:00:00' and bid > 0 and ofr > bid) where '2007-07-31 09:30:00' <= time and time < '2007-08-01 16:00:00' group by symbol, time(1m)" > query.log 2>&1 &






















































## 安装 TimescaleDB
# add PostgreSQL's third party repository
sh -c "echo 'deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -c -s`-pgdg main' >> /etc/apt/sources.list.d/pgdg.list"
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# Add our PPA
add-apt-repository ppa:timescale/timescaledb-ppa
apt-get update

# To install for PG 10.2+
apt install timescaledb-postgresql-10



# 移动数据目录
cp -rp /var/lib/postgresql /data/postgresql
rm -rf /var/lib/postgresql
ln -s /data/postgresql /var/lib/postgresql
chown -h postgres:postgres /var/lib/postgresql

ls -ld /var/lib/postgresql

# 编辑配置文件
/etc/postgresql/10/main/postgresql.conf

# 修改访问权限
/etc/postgresql/10/main/pg_hba.conf
# local   all             all                                     peer
# host    all             all             0.0.0.0/0               md5

# 控制
service postgresql start
service postgresql status
service postgresql restart
service postgresql stop

systemctl stop postgresql.service
systemctl status postgresql.service

ps -efl | grep postgres

free -h


# 修改 postgres 用户密码
su postgres
psql

postgres=# \password
Enter new password:
Enter it again:
postgres=#




# 卸载
apt remove --purge timescaledb-postgresql-10
apt remove --purge postgresql-10

apt remove timescaledb-postgresql-10
apt remove postgresql-10
apt autoremove


# 日志
tail -f /var/log/postgresql/postgresql-10-main.log


## 导入小数据集并计时
# 导入 devices
timescaledb-parallel-copy \
    --workers 12 \
    --reporting-period 5s \
    --copy-options "CSV" \
    --connection "host=localhost user=postgres password=postgres dbname=test sslmode=disable" \
    --db-name test \
    --table device_info \
    --file /data/devices/csv/devices_big_device_info.csv 

# 导入 readings
timescaledb-parallel-copy \
    --workers 12 \
    --reporting-period 5s \
    --copy-options "CSV" \
    --connection "host=localhost user=postgres password=postgres dbname=test sslmode=disable" \
    --db-name test \
    --table readings \
    --batch-size 10000 \
    --file /data/devices/csv/devices_big_readings.csv
# 6m 30s


# 导出数据并计时
chown postgres:postgres /data/devices
su postgres
cd ~
time psql -d test -c "\COPY (SELECT * FROM readings) TO /data/devices/devices_dump.csv DELIMITER ',' CSV"


# 占用空间
du -sh /mnt/data/postgresql/10/main
# 15 GB


## 导入大数据集并计时

for f in /data/TAQ/csv/*.csv ; do
    tail -n +2 $f | timescaledb-parallel-copy \
        --workers 12 \
        --reporting-period 1s \
        --copy-options "CSV" \
        --connection "host=localhost user=postgres password=postgres dbname=test sslmode=disable" \
        --db-name test \
        --table taq \
        --batch-size 200000
    
    echo "文件 $f 导入完成"
done






tail -n +2 /data/TAQ/csv/TAQ20070802.csv | timescaledb-parallel-copy --db-name test --table taq --copy-options "CSV" --workers 3 --reporting-period 1s --connection "host=localhost user=postgres password=postgres dbname=test sslmode=disable" --batch-size 200000

tail -n +2 /data/TAQ/csv/TAQ20070803.csv | timescaledb-parallel-copy --db-name test --table taq --copy-options "CSV" --workers 3 --reporting-period 1s --connection "host=localhost user=postgres password=postgres dbname=test sslmode=disable" --batch-size 200000

tail -n +2 /data/TAQ/csv/TAQ20070806.csv | timescaledb-parallel-copy --db-name test --table taq --copy-options "CSV" --workers 3 --reporting-period 1s --connection "host=localhost user=postgres password=postgres dbname=test sslmode=disable" --batch-size 200000

tail -n +2 /data/TAQ/csv/TAQ20070807.csv | timescaledb-parallel-copy --db-name test --table taq --copy-options "CSV" --workers 3 --reporting-period 1s --connection "host=localhost user=postgres password=postgres dbname=test sslmode=disable" --batch-size 200000


tail -n +2 $f | timescaledb-parallel-copy \
    --workers 4 \
    --reporting-period 5s \
    --copy-options "CSV" \
    --connection "host=localhost user=postgres password=postgres dbname=test sslmode=disable" \
    --db-name test \
    --table taq \
    --batch-size 15000


# at 17h14m38s, row rate 0.000000/sec (period), row rate 4813.130307/sec (overall), 2.987895E+08 total rows
# COPY 298789504

# at 20h32m9s, row rate 0.000000/sec (period), row rate 4462.411737/sec (overall), 3.299016E+08 total rows
# COPY 329901638

# at 20h40m27s, row rate 0.000000/sec (period), row rate 4525.943276/sec (overall), 3.368524E+08 total rows
# COPY 336852381

# at 20h35m51s, row rate 0.000000/sec (period), row rate 4427.001260/sec (overall), 3.282666E+08 total rows
# COPY 328266571

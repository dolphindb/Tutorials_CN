# ------------------------------------ InfluxDB 测试脚本
# ------------ readings 数据定义
cols = ["time", "device_id", "battery_level", "battery_status", "battery_temperature", "bssid", "cpu_avg_1min", "cpu_avg_5min", "cpu_avg_15min", "mem_free", "mem_used", "rssi", "ssid"]
tags = ["device_id", "battery_status", "bssid", "ssid"]
fields = ["battery_level", "battery_temperature", "cpu_avg_1min", "cpu_avg_5min", "cpu_avg_15min", "mem_free", "mem_used", "rssi"]


# ------------ 20 行数据
rs = fs.createReadStream 'D:/1/comp/timescaledb/readings.csv', 
    encoding: 'UTF-8'

ws = fs.createWriteStream 'D:/readings_small.txt',
    encoding: 'UTF-8'


# ------------ 所有行数据
rs = fs.createReadStream 'D:/devices/devices_big_readings.csv', 
    encoding: 'UTF-8'

ws = fs.createWriteStream 'D:/readings.txt',
    encoding: 'UTF-8'


# ------------ 小数据内存读写
csv = read('D:/1/comp/timescaledb/readings.csv')

lines = csv.split_lines()

write('D:/readings.txt', text)

# ------------ CSV -> Line Protocol
map_line= (l)->
    o = {}
    for col, i in l.split(',')
        o[cols[i]] = col
    
    line = 'readings,'
    line += tags.map (tag)->
            tag + '=' + o[tag]
        .join(',')
    line += ' '
    
    line += fields.map (field)->
            field + '=' + o[field]
        .join(',')
    
    line += ' ' + new Date(o.time).getTime() / 1000
    
# ------------ 流读写

ws.write '''
    # DDL
    CREATE DATABASE test
    CREATE RETENTION POLICY one_day ON test DURATION INF REPLICATION 1 SHARD DURATION 1d DEFAULT
    
    # DML
    # CONTEXT-DATABASE:test
    # CONTEXT-RETENTION-POLICY:one_day
    
    '''


buf = ''
cnt = 0

ts = new stream.Transform
    transform: (chunk, encoding, callback)->
        lines = chunk.split('\n')
        lines[0] = buf + lines[0]
        buf = lines.pop()
        cnt += lines.length
        callback(null, lines.map(map_line).join('\n') + '\n')
    
    flush: (callback)->
        if buf
            callback(null, buf + '\n')
        else
            callback(null)
    
    decodeStrings: false


await util.promisify(stream.pipeline)(rs, ts, ws)

stream.pipeline rs, ts, ws, (err)->
    log err

# ------------ InfluxDB NodeJS API
Influx = require 'influx'

influx.createDatabase 'test'

influx = new Influx.InfluxDB
    host: 'localhost'
    database: 'test'
    schema: [
        measurement: 'readings'
        tags: [
            'device_id'
            'battery_status'
            'bssid'
            'ssid'
        ]
        fields: 
            battery_level      : Influx.FieldType.INTEGER
            battery_temperature: Influx.FieldType.FLOAT
            cpu_avg_1min       : Influx.FieldType.FLOAT
            cpu_avg_5min       : Influx.FieldType.FLOAT
            cpu_avg_15min      : Influx.FieldType.FLOAT
            mem_free           : Influx.FieldType.INTEGER
            mem_used           : Influx.FieldType.INTEGER
            rssi               : Influx.FieldType.INTEGER
    ]
    
influx.getDatabaseNames()



influx.writePoints [
        measurement: 'readings'
        tags:
            device_id: 'demo000000'
        fields:
            battery_level: 96
        timestamp
    ,
        measurement: 'readings'
        tags:
            device_id: 'demo000001'
        fields:
            battery_level: 78
]





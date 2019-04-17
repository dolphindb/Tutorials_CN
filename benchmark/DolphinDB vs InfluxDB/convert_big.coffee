fs = require 'fs'
stream = require 'stream'
util = require 'util'

# ------------ TAQ 数据定义
cols = ['symbol', 'date', 'time', 'bid', 'ofr', 'bidsiz', 'ofrsiz', 'mode', 'ex', 'mmid']
tags = ["symbol", "mode", "ex", "mmid"]
fields = ["bid", "ofr", "bidsiz", "ofrsiz"]



# ------------ 所有行数据
# rs = fs.createReadStream 'D:/1/comp/influxdb/TAQ.csv', 
#     encoding: 'UTF-8'
#     start: 'symbol,date,time,bid,ofr,bidsiz,ofrsiz,mode,ex,mmid\n'.length

# ws = fs.createWriteStream 'D:/TAQ.txt',
#     encoding: 'UTF-8'



# ------------ CSV -> Line Protocol
map_line= (l)->
    o = {}
    for col, i in l.split(',')
        o[cols[i]] = col
    
    line = 'taq'
    for tag in tags
        if o[tag]
            line += ',' + tag + '=' + o[tag]
    
    line += ' '
    
    line += fields.map (field)->
            field + '=' + o[field]
        .join(',')
    
    line += ' ' + new Date(o.date[0...4] + '-' + o.date[4...6] + '-' + o.date[6..] + ' ' + o.time + '.' + Math.round(Math.random() * 1000)).getTime()


buf = ''
cnt = 0

main= ->
    for i in [1, 2, 3, 6, 7]
        name = 'TAQ2007080' + i
        rs = fs.createReadStream '/data/TAQ/csv/' + name + '.csv', 
            encoding: 'UTF-8'
            start: 'symbol,date,time,bid,ofr,bidsiz,ofrsiz,mode,ex,mmid\n'.length
        
        ws = fs.createWriteStream '/data/TAQ/' + name + '.txt',
            encoding: 'UTF-8'
        
        
        
        # rs = fs.createReadStream 'D:/1/comp/influxdb/TAQ.csv', 
        #     encoding: 'UTF-8'
        #     start: 'symbol,date,time,bid,ofr,bidsiz,ofrsiz,mode,ex,mmid\n'.length
        
        # ws = fs.createWriteStream 'D:/TAQ.txt',
        #     encoding: 'UTF-8'
        
        
        # ------------ 流读写
        ws.write '''
            # DML
            # CONTEXT-DATABASE:test2
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
                    callback(null, map_line(buf) + '\n')
                else
                    callback(null)
            
            decodeStrings: false
        
        
        console.log '--- ' + i + ' ---'
        await util.promisify(stream.pipeline)(rs, ts, ws)



main()

id = setInterval ->
        console.log new Date(), cnt
    , 10000





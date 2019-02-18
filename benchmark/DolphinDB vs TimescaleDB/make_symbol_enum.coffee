PG = require 'pg'

client = new PG.Client
    connectionString: 'postgresql://postgres:postgres@192.168.1.201:5432/test'

await client.connect()

# 测试连接
await client.query 'select now()'

symbols = fs.readFileSync('D:/symbols.txt', 'UTF-8').split('\n')[...-1]

symbol_cmd = 'create type Symbol as enum ' + '(' + symbols.map((e)-> "'" + e + "'").join(',') + ');'

await client.query symbol_cmd

fs.writeFileSync 'D:/make_symbol_enum.sql', symbol_cmd

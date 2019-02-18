# ------------ DolphinDB 测试结果处理
# 复制测试结果
text = new Text paste()
text.remove_empty_lines().replace /Time elapsed: (\d+)\.\d+ ms/, '$1'
copy text.to_string()

text.map (l)-> l.replace(/Time elapsed: (\d+)\.\d+ ms/, '$1').toNumber()


# ------------ 占用空间分析 结果处理
# 复制测试结果
text = new Text(paste())
text.replace ' MB', ''
text.remove_empty_lines()

sum = 0
text.each (l)-> sum += l.toNumber()
sum
# 5107 total -> 7430 total after create index
# 844  index -> 3167 index after create index
5107 - 844 == 4271
7430 - 3167 == 4274



# ------------ 加载测试结果
result0 = Text.load('D:/0/DB/testresult_timescaledb_small.txt')
result1 = Text.load('D:/0/DB/testresult_dolphindb_small.txt')

result0 = Text.load('D:/0/DB/testresult_timescaledb_big.txt')
result1 = Text.load('D:/0/DB/testresult_dolphindb_big.txt')

result0.remove_last_empty_line().map (l)-> l.toNumber()
result1.remove_last_empty_line().map (l)-> l.toNumber()


# ------------ 生成对比表格
# 复制所有测试用例
test_text = paste()

tests = test_text.replace(/\r\n/g, '\n').split('\n\n\n').map (x)-> x.trim()

tests.each (test, i)->
    log '| ' + 
        pad((i+1) + '. ', 4) + test.split('\n')[0].split('. ')[1] + ' | ' +
        result1[i] + ' | ' +
        result0[i] + ' | ' +
        Math.round(result0[i] / result1[i]) + ' | ' +
        (result0[i] - result1[i]) + ' | '
        


# ------------ explain analyze 计算总时间
text = paste()
[_, a, b] = text.match /.*?(\d+)\.[\s\S]*?(\d+)\..*/

a.toNumber() + b.toNumber()

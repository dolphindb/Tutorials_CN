import dolphindb as ddb

s = ddb.session()
sites = ['115.239.209.189:8851']
s.connect(host="115.239.209.189", port=8851, userid="admin", password="123456", highAvailability=True,
          highAvailabilitySites=sites)

def load_factor(factor_name):
    file_path = "D:\work\job\\factor_test\\{}.dos"
    f = open(file_path.format(factor_name))
    factor_file = f.readlines()

    factors_basic_info= eval( [sentense.split('=')[1] for sentense in factor_file if 'basic_info' in sentense][0])
    factor_func=''
    start_flag =0
    for line in factor_file:
        if 'def' in line:
            start_flag=1
        if start_flag==1:
            factor_func=factor_func+line

    s.run(factor_func)
    s.run("")
    return factors_basic_info

def calc_entry(factor_list, start_date, end_date,return_mode):

    start_date_dol = start_date[:4] + "." + start_date[4:6] + "." + start_date[6:]
    end_date_dol = end_date[:4] + "." + end_date[4:6] + "." + end_date[6:]

    factors_basic_info = {}
    # 加载因子方法
    for factor in factor_list:
        load_factor(factor)
        factors_basic_info[factor] = load_factor(factor)
    s.run("use FactorCalc")
    # run only on factor here
    if return_mode =="save":
        res = s.run(
            '''FactorCalc::calc_factor_single_and_savewide('{}',{},{},{})'''.format(factor_list[0],factors_basic_info[factor_list[0]], start_date_dol, end_date_dol))
        print(res)
    else:
        res = s.run(
            '''FactorCalc::calc_factor_single_and_return('{}',{},{},{})'''.format(factor_list[0],factors_basic_info[factor_list[0]], start_date_dol, end_date_dol))
        print(res)
# save data
# calc_entry(['fac2'],'20200105','20200205','save')
# return thedata
calc_entry(['fac2'],'20200105','20200205','return')

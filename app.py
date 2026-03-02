import urllib3  # Must append a third value to avoid error
from flask import Flask, render_template, request
if len(urllib3.__version__.split('.')) < 3:
    urllib3.__version__ = urllib3.__version__ + '.0'
import requests 
import pandas as pd 
import time
import random
import csv
import os
URL = "https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=html&date={}&stockNo={}"
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 500)

app = Flask(__name__)

"""import model, download stock list"""

table_settings = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines"
}
def extract_numbers_from_csv(file_path):
    numbers = []
    namedict={}
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        lastnum=False
        csv_reader = csv.reader(file)
        for row in csv_reader:
            for cell in row:
                try:
                    num = int(cell.strip())
                    if num > 0:
                        numbers.append(num)
                        lastnum=True
                except:
                    if lastnum:
                        namedict[numbers[-1]] = cell.replace("＃","").replace("＊","").replace(" ","").replace("　","").strip("　 \xa0")
                    lastnum=False
    return numbers,namedict
file_path = 'stocklist.csv'
result,stockname = extract_numbers_from_csv(file_path)

# 輸出所有從目前到目標時間之間的所有月分的1號 --> 20220501,20220401...,20200501
def hmy(nd,wd):    
    k=[]
    nm=int(nd[4:6]);ny=int(nd[0:4])
    wm=int(wd[4:6]);wy=int(wd[0:4])
    if ny>wy:
        while (ny>wy):
            while (nm>0):
                if nm<10:
                    k.append(int(str(ny)+'0'+str(nm)+'01'))
                elif nm>=10:
                    k.append(int(str(ny)+str(nm)+'01'))
                nm-=1
            nm=12
            ny-=1
    if ny==wy:
        while (nm>=wm):
            if nm<10:
                k.append(int(str(ny)+'0'+str(nm)+'01'))
            elif nm>=10:
                k.append(int(str(ny)+str(nm)+'01'))
            nm-=1
    return k


# 這是做出單日RSV的function
def RSV(spj,zgj,zdj, position):  
    sp=spj[position]
    z9g=max(zgj[position:position+9])
    z9d=min(zdj[position:position+9])
    return round(float(((sp-z9d)/(z9g-z9d))*100),2)


# 這是做出單日KD的function
def KD_turn(rsv,datte,kpj):  
    kd9=[]
    rsv = [x.strip() for x in rsv.strip('][').split(', ') if x.strip()]
    datte = [x.strip().replace("'", "") for x in datte.strip('][').split(', ') if x.strip()]
    kpj = [x.strip() for x in kpj.strip('][').split(', ') if x.strip()]
    
    if not rsv:
        return []
        
    kd9.append([round(float(50*2/3+float(rsv[0])/3),2),round(float(50*2/3+50/3),2)])
    k1=kd9[0][0]; d1=kd9[0][1]
    for i in range(1,len(rsv)):
        ktd=round(float(k1*2/3+float(rsv[i])/3),2)
        kd9.append([ktd,round(float(d1*2/3+ktd/3),2),datte[i+8],kpj[i+8]])
        k1=ktd; d1=round(float(d1*2/3+ktd/3),2)
    return kd9


# 這是KD的回測function，會輸出對應的報酬資料和勝率
def backtestkd(kdd,kl,kh):  
    record=[[0]]; mt=[]; mp=[]; st=[]; sp=[]; rr=[]; w=0; l=0
    for i in range(1,len(kdd)-1):
        if record[-1][0] != 'buy':
            if (kdd[i-1][0]>=kl) and (kdd[i][0]<kl):
                record.append(['buy',kdd[i+1][2],kdd[i+1][3]])
        elif record[-1][0] == 'buy':
            if (kdd[i-1][0]<=kh) and (kdd[i][0]>kh):
                record.append(['sell',kdd[i+1][2],kdd[i+1][3]])
    if record[-1][0] != 'sell':
        record=record[:-1]
    print(record)
    record=record[1:]
    for i in range(len(record)):
        if record[i][0]=='buy':
            mt.append(record[i][1])
            mp.append(record[i][2])
        elif record[i][0]=='sell':
            st.append(record[i][1])
            sp.append(record[i][2])
            r=((float(record[i][2])-float(record[i-1][2]))/(float(record[i-1][2])))
            rr.append(str((round(r*100,2)))+'%')
            if r>0:
                w+=1
            elif r<0:
                l+=1
    if w+l!=0:
        win_rate='勝率:'+str(round(w/(w+l)*100,2))+'%'
        backtest_outcome = pd.DataFrame((zip(mt,mp,st,sp,rr)), columns = ['買進時間', '買進價格', '賣出時間', '賣出價格', '報酬率'])
        return backtest_outcome, win_rate
    if w+l==0:
        return 'No corresponding information!!!','please try again...'  #如果都沒有勝或負也就是沒有對應情況，則告知使用者再試一次

# 這是做出單日威廉(採計14日)的function
def william14(spj,zgj,zdj,position):
    sp=spj[position]
    z14g=max(zgj[position:position+14])
    z14d=min(zdj[position:position+14])
    return round(float(((z14g-sp)/(z14g-z14d))*100),2)*(-1)


# 這是做出單日威廉(採計28日)的function
def william28(spj,zgj,zdj,position):
    sp=spj[position]
    z28g=max(zgj[position:position+28])
    z28d=min(zdj[position:position+28])
    return round(float(((z28g-sp)/(z28g-z28d))*100),2)*(-1)


 # 威廉的回測function
def backtestwil(wil,wl,wh): 
    record=[[0]]; mt=[]; mp=[]; st=[]; sp=[]; rr=[]; w=0; l=0
    for i in range(1,len(wil)-1):
        if record[-1][0] != 'buy':
            if (wil[i-1][0]<=wl) and (wil[i][0]>wl):
                record.append(['buy',wil[i][2],wil[i][4]])
        elif record[-1][0] == 'buy':
            if (wil[i-1][1]>=wh) and (wil[i][1]<wh):
                record.append(['sell',wil[i][2],wil[i][4]])
    if record[-1][0] != 'sell':
        record=record[:-1]
    record=record[1:]
    for i in range(len(record)):
        if record[i][0]=='buy':
            mt.append(record[i][1])
            mp.append(record[i][2])
        elif record[i][0]=='sell':
            st.append(record[i][1])
            sp.append(record[i][2])
            r=((record[i][2]-record[i-1][2])/(record[i-1][2]))
            rr.append(str((round(r*100,2)))+'%')
            if r>0:
                w+=1
            elif r<0:
                l+=1
    if w+l!=0:
        win_rate='勝率:'+str(round(w/(w+l)*100,2))+'%'
        backtest_outcome = pd.DataFrame((zip(mt,mp,st,sp,rr)), columns = ['買進時間', '買進價格', '賣出時間', '賣出價格', '報酬率'])
        return backtest_outcome, win_rate
    if w+l==0:
        return 'No corresponding information!!!','please try again...'


# 這是做出各天期MA的function
def ma(spj, position):  
    fivema=round(float(sum(spj[position:position+5])/5),2)
    tenma=round(float(sum(spj[position:position+10])/10),2)
    twentyma=round(float(sum(spj[position:position+20])/20),2)
    grb40ma=round(float(sum(spj[position:position+40])/40),2)
    a=[fivema,tenma,twentyma,grb40ma]
    return a


# MA策略的回測函式
def backtestma(ma,wk):  
    record=[[0]]; mt=[]; mp=[]; st=[]; sp=[]; rr=[]; w=0; l=0
    if wk=='A': #10ma and 20ma上揚且黃金交叉 死亡交叉賣
        for i in range(1,len(ma)-1):
            if record[-1][0] != 'buy':
                if (ma[i-1][1]<=ma[i][1]) and (ma[i-1][2]<=ma[i][2]) and (ma[i-1][1]<=ma[i-1][2]) and (ma[i][1]>ma[i][2]):
                    record.append(['buy',ma[i][4],ma[i][5]]) 
            elif record[-1][0] == 'buy':
                if (ma[i-1][2]<=ma[i][2]) and (ma[i-1][1]>=ma[i-1][2]) and (ma[i][1]<ma[i][2]):
                    record.append(['sell',ma[i][4],ma[i][5]])
    elif wk=='B': # 5ma and 10ma上揚且黃金交叉買 死亡交叉賣
        for i in range(1,len(ma)-1):
            if record[-1][0] != 'buy':
                if (ma[i-1][0]<=ma[i][0]) and (ma[i-1][1]<=ma[i][1]) and (ma[i-1][0]<=ma[i-1][1]) and (ma[i][0]>ma[i][1]):
                    record.append(['buy',ma[i][4],ma[i][5]]) 
            elif record[-1][0] == 'buy':
                if (ma[i-1][1]<=ma[i][1]) and (ma[i-1][0]>=ma[i-1][1]) and (ma[i][0]<ma[i][1]):
                    record.append(['sell',ma[i][4],ma[i][5]])
    elif wk=='C': #均線多頭排列買 5日線跌破10日且其餘均線仍上揚時賣
        for i in range(1,len(ma)-1):
            if record[-1][0] != 'buy':
                if (ma[i-1][0]<=ma[i][0]) and (ma[i-1][1]<=ma[i][1]) and (ma[i-1][2]<=ma[i-1][2]) and (ma[i][3]<=ma[i][3]) and (ma[i][0]>ma[i][1]>ma[i][2]>ma[i][3]):
                    record.append(['buy',ma[i][4],ma[i][5]]) 
            elif record[-1][0] == 'buy':
                if (ma[i-1][0]<ma[i][1]) and (ma[i-1][1]<=ma[i][1]) and (ma[i-1][2]<=ma[i-1][2]) and (ma[i][3]<=ma[i][3]) and (ma[i][0]>ma[i][1]>ma[i][2]>ma[i][3]):
                    record.append(['sell',ma[i][4],ma[i][5]])
    elif wk=='D': #格蘭必40MA 股價突破且均線上揚時買 均線下跌且股價跌破時賣
        for i in range(1,len(ma)-1):
            if record[-1][0] != 'buy':
                if (ma[i-1][3]<ma[i][3]) and (ma[i][3]<ma[i][5]) and (ma[i-1][3]>=ma[i-1][5]):
                    record.append(['buy',ma[i][4],ma[i][5]]) 
            elif record[-1][0] == 'buy':
                if (ma[i-1][3]>ma[i][3]) and (ma[i-1][5]>=ma[i-1][3]) and (ma[i][5]<ma[i][3]):
                    record.append(['sell',ma[i][4],ma[i][5]])
    if record[-1][0] != 'sell':
        record=record[:-1]
    record=record[1:]
    for i in range(len(record)):
        if record[i][0]=='buy':
            mt.append(record[i][1])
            mp.append(record[i][2])
        elif record[i][0]=='sell':
            st.append(record[i][1])
            sp.append(record[i][2])
            r=((record[i][2]-record[i-1][2])/(record[i-1][2]))
            rr.append(str((round(r*100,2)))+'%')
            if r>0:
                w+=1
            elif r<0:
                l+=1
    if w+l!=0:
        win_rate='勝率:'+str(round(w/(w+l)*100,2))+'%'
        backtest_outcome = pd.DataFrame((zip(mt,mp,st,sp,rr)), columns = ['買進時間', '買進價格', '賣出時間', '賣出價格', '報酬率'])
        return backtest_outcome, win_rate
    if w+l==0:
        return 'No corresponding information!!!','please try again...'

def stock_crawler(stockNo, dates):
    for date in dates :    # 爬蟲+把爬到的資料存檔到電腦(爬10年大概要30秒以上)
        url = URL.format(date, stockNo)
        file_name = "{}_{}.csv".format(stockNo, date)
        data = pd.read_html(requests.get(url).text)[0]
        data.columns = data.columns.droplevel(0)
        data.to_csv(file_name, index=False)
        time.sleep(random.uniform(2, 5))
    print("SUCCESS")

def csv_preprocessing(dates,stockNo):
    # 這邊把爬到的資料從儲存地點依序取出(由新到舊)，弄出一個只有收盤價的list，順序是從目前日期逆序回到目標當月1號
    # 這些收盤價就可以用來計算指標，同理可以更改row['']中的key，去蓋其他的資料的list
    # spj=so pan jia收盤價 :D
    spj=[] 
    zgj=[]
    zdj=[]
    kpj=[]
    datte=[]
    #這個迴圈會讀取CSV檔案中每一行資料，然後我們取出需要的素材
    for dat in dates:
        file_name = f"{stockNo}_{dat}.csv"
        if not os.path.exists(file_name):
            continue
        with open(file_name, newline='', encoding="utf-8") as csvfile:
            rows = csv.DictReader(csvfile)
            m=[]
            for row in (rows):
                m.append([row['收盤價'], row['最高價'], row['最低價'], row['日期'], row['開盤價']])
            mr=list(reversed(m))
            for i in range(len(mr)):
                spj.append(float(mr[i][0]))
                zgj.append(float(mr[i][1]))
                zdj.append(float(mr[i][2]))
                datte.append((mr[i][3]))
                kpj.append(float(mr[i][4]))
    datte.reverse() #對日期和開盤價做反轉，比較好配合後續列表整理
    kpj.reverse()
    rsv_data=[]
    wil_data=[]
    for i in range(len(spj)-8):
        rsv_data.append(RSV(spj,zgj,zdj,i))
    for i in range(len(spj)-13):
        wil_data.append([william14(spj,zgj,zdj,i)])
    for i in range(len(spj)-27):
        wil_data[i].append(william28(spj,zgj,zdj,i))
    rsv_data=list(reversed(rsv_data))
    wil_data=list(reversed(wil_data))
    spj_wil=list(reversed(spj))
    for i in range(len(spj)-13):
        wil_data[i].append(datte[i+13])
        wil_data[i].append(kpj[i+13])
        wil_data[i].append(spj_wil[i+13])
    wil_data=wil_data[14:]
    ma_data=[]
    for i in range(len(spj)-39):
        ma_data.append(ma(spj,i))
        ma_data[i].append(datte[-1-i])
        ma_data[i].append(spj[i])
    ma_data.reverse()
    return spj,zgj,zdj,kpj,datte,rsv_data, wil_data, ma_data

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print("POSTING")
        stockNo = request.form['stockNo']
        endDate = request.form['endDate']
        startDate = request.form['startDate']
        dates = hmy(endDate,startDate)
        stock_crawler(stockNo, dates)
        spj,zgj,zdj,kpj,datte,rsv_data, wil_data, ma_data = csv_preprocessing(dates,stockNo)
        analysisname = stockname.get(int(stockNo), stockNo)
        return render_template('index.html', kpj=kpj, datte=datte, rsv_data=rsv_data,wil_data=wil_data, ma_data = ma_data, stockNo=stockNo, endDate=endDate, startDate=startDate,analysisname=analysisname)
    refresh = request.args.get('refresh')
    if refresh == 'true':
        return render_template('index.html')
    return render_template('index.html')

@app.route('/KD', methods=['POST'])
def KD():
    rsv_data = request.form['rsv_data']
    datte = request.form['datte']
    kpj = request.form['kpj']
    if not rsv_data or rsv_data == '[]':
         return render_template('index.html', result=('No data available', 'Please try a wider date range'))
    kd_buy = int(request.form['kd_buy'])
    kd_sell = int(request.form['kd_sell'])
    kdstock=KD_turn(rsv_data,datte,kpj)  
    if not kdstock:
        return render_template('index.html', result=('No data available', 'Please try a wider date range'))
    del kdstock[:21]
    result = backtestkd(kdstock,kd_buy,kd_sell)
    return render_template('index.html',result=result)

@app.route('/william', methods=['POST'])
def william():
    wil_raw = request.form['wil_data'].strip()
    if not wil_raw or wil_raw == '[]':
        return render_template('index.html', result=('No data available', 'Please try a wider date range'))
        
    wil_data = wil_raw.replace("[[", "").replace("]]", "").split("], [")
    wil_parsed = []
    for item in wil_data:
        parts = [x.strip() for x in item.split(", ") if x.strip()]
        if len(parts) >= 5:
            try:
                wil_parsed.append([float(parts[0]), float(parts[1]), parts[2].replace("'", ""), float(parts[3]), float(parts[4])])
            except ValueError:
                continue
    
    if not wil_parsed:
        return render_template('index.html', result=('No valid data found', 'Please try again'))
        
    wil_buy = int(request.form['kd_buy']) if 'kd_buy' in request.form else int(request.form['wil_buy'])
    wil_sell = int(request.form['kd_sell']) if 'kd_sell' in request.form else int(request.form['wil_sell'])
    result = backtestwil(wil_parsed,wil_buy,wil_sell)
    return render_template('index.html',result=result)

def parse_ma_data(ma_str):
    ma_str = ma_str.strip()
    if not ma_str or ma_str == '[]':
        return []
    ma_data = ma_str.replace("[[", "").replace("]]", "").split("], [")
    ma_parsed = []
    for item in ma_data:
        parts = [x.strip() for x in item.split(", ") if x.strip()]
        if len(parts) >= 6:
            try:
                # [5ma, 10ma, 20ma, 40ma, 'date', spj]
                ma_parsed.append([float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), parts[4].replace("'", ""), float(parts[5])])
            except ValueError:
                continue
    return ma_parsed

@app.route('/MA_A', methods=['POST'])
def MA_A():
    ma_data = parse_ma_data(request.form['ma_data'])
    result = backtestma(ma_data,"A")
    return render_template('index.html',result=result)

@app.route('/MA_B', methods=['POST'])
def MA_B():
    ma_data = parse_ma_data(request.form['ma_data'])
    result = backtestma(ma_data,"B")
    return render_template('index.html',result=result)

@app.route('/MA_C', methods=['POST'])
def MA_C():
    ma_data = parse_ma_data(request.form['ma_data'])
    result = backtestma(ma_data,"C")
    return render_template('index.html',result=result)

@app.route('/MA_D', methods=['POST'])
def MA_D():
    ma_data = parse_ma_data(request.form['ma_data'])
    result = backtestma(ma_data,"D")
    return render_template('index.html',result=result)

@app.route('/discard', methods=['POST'])
def discard():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
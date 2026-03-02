def hmy(nd,wd):    # 這個用來輸出所有從目前到目標時間之間的所有月分的1號-->像這樣20220501,20220401...,20200501
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

import urllib3  # Must append a third value to avoid error
if len(urllib3.__version__.split('.')) < 3:
    urllib3.__version__ = urllib3.__version__ + '.0'

import requests  #爬蟲用
import pandas as pd  #資料編輯用
import time  #設定計時用
import random  #隨機生成數字用
import csv  #讀取檔案用
import os

# 使用者在這裡輸入想要的時間區段(以月為單位)，還有標的代號
#nd=input("請輸入目前日期ex.20220501:")
#wd=input("請輸入過去日期ex.20200501:")
nd=str(20220731)
wd=str(20220531)
dates = hmy(nd,wd)    # 剛剛寫的function就可以用在這邊，等等就能依照list中日期爬到所有年月份資料
stockNo = (input("請輸入股票代號ex.2330:"))
url_template = "https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=html&date={}&stockNo={}"
# 這區是輸入日期始末跟股票代碼，希望使用者一進來先顯示讓他輸入這個

print('下載股票資料中。。。。。。') #等他輸入完按確定，就顯示這個
for date in dates :    # 爬蟲+把爬到的資料存檔到電腦(爬10年大概要30秒以上)
    url = url_template.format(date, stockNo)
    file_name = "{}_{}.csv".format(stockNo, date)
    
    data = pd.read_html(requests.get(url).text)[0]
    data.columns = data.columns.droplevel(0)
    data.to_csv(file_name, index=False)
    time.sleep(random.uniform(2, 5))    # 要設置隨機迴圈間隔時間，不然會被BAN一段時間
print('Complete!Please continue~~') #跑完爬蟲顯示這個提醒使用者完成了
# 這區是儲存股價資料到電腦資料夾

# 這邊把爬到的資料從儲存地點依序取出(由新到舊)，弄出一個只有收盤價的list，順序是從目前日期逆序回到目標當月1號
# 這些收盤價就可以用來計算指標，同理可以更改row['']中的key，去蓋其他的資料的list
spj=[] # spj=so pan jia收盤價 :D
zgj=[]
zdj=[]
kpj=[]
datte=[]
for dat in dates:  # 這個迴圈會讀取CSV檔案中每一行資料，然後我們取出需要的素材
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

def RSV(spj,zgj,zdj):  # 這是做出單日RSV的function
    sp=spj[i]
    z9g=max(zgj[i:i+9])
    z9d=min(zdj[i:i+9])
    return round(float(((sp-z9d)/(z9g-z9d))*100),2)
def william14(spj,zgj,zdj):  # 這是做出單日威廉(採計14日)的function
    sp=spj[i]
    z14g=max(zgj[i:i+14])
    z14d=min(zdj[i:i+14])
    return round(float(((z14g-sp)/(z14g-z14d))*100),2)*(-1)
def william28(spj,zgj,zdj):  # 這是做出單日威廉(採計28日)的function
    sp=spj[i]
    z28g=max(zgj[i:i+28])
    z28d=min(zdj[i:i+28])
    return round(float(((z28g-sp)/(z28g-z28d))*100),2)*(-1)
rsv_data=[]
wil_data=[]
for i in range(len(spj)-8):
    rsv_data.append(RSV(spj,zgj,zdj))
for i in range(len(spj)-13):
    wil_data.append([william14(spj,zgj,zdj)])
for i in range(len(spj)-27):
    wil_data[i].append(william28(spj,zgj,zdj))
rsv_data=list(reversed(rsv_data))
wil_data=list(reversed(wil_data))
spj_wil=list(reversed(spj))
for i in range(len(spj)-13):
    wil_data[i].append(datte[i+13])
    wil_data[i].append(kpj[i+13])
    wil_data[i].append(spj_wil[i+13])
wil_data=wil_data[14:]
# 把上面的function帶入迴圈，製作出裝有對應日期、價格的指標list

def KD(rsv):  # 這是做出單日KD的function
    kd9=[]
    kd9.append([round(float(50*2/3+rsv[0]/3),2),round(float(50*2/3+50/3),2)])
    k1=kd9[0][0]; d1=kd9[0][1]
    for i in range(1,len(rsv)):
        ktd=round(float(k1*2/3+rsv[i]/3),2)
        kd9.append([ktd,round(float(d1*2/3+ktd/3),2),datte[i+8],kpj[i+8]])
        k1=ktd; d1=round(float(d1*2/3+ktd/3),2)
    return kd9

def backtestkd(kdd,kl,kh):  # 這是KD的回測function，會輸出對應的報酬資料和勝率
    record=[[0]]; mt=[]; mp=[]; st=[]; sp=[]; rr=[]; w=0; l=0
    for i in range(1,len(kdd)):
        if record[-1][0] != 'buy':
            if (kdd[i-1][0]>=kl) and (kdd[i][0]<kl):
                record.append(['buy',kdd[i+1][2],kdd[i+1][3]])
        elif record[-1][0] == 'buy':
            if (kdd[i-1][0]<=kh) and (kdd[i][0]>kh):
                record.append(['sell',kdd[i+1][2],kdd[i+1][3]])
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
        return 'No corresponding information!!!','please try again...'  #如果都沒有勝或負也就是沒有對應情況，則告知使用者再試一次

def ma(spj):  # 這是做出各天期MA的function
    fivema=round(float(sum(spj[i:i+5])/5),2)
    tenma=round(float(sum(spj[i:i+10])/10),2)
    twentyma=round(float(sum(spj[i:i+20])/20),2)
    grb40ma=round(float(sum(spj[i:i+40])/40),2)
    a=[fivema,tenma,twentyma,grb40ma]
    return a
ma_data=[]
for i in range(len(spj)-39):
    ma_data.append(ma(spj))
    ma_data[i].append(datte[-1-i])
    ma_data[i].append(spj[i])
ma_data.reverse()
#利用function，以迴圈製作出裝有所有日期的所有MA資料的list

def backtestma(ma,wk):  #MA策略的回測函式
    record=[[0]]; mt=[]; mp=[]; st=[]; sp=[]; rr=[]; w=0; l=0
    if wk=='A': #10ma and 20ma上揚且黃金交叉 死亡交叉賣
        for i in range(1,len(ma)):
            if record[-1][0] != 'buy':
                if (ma[i-1][1]<=ma[i][1]) and (ma[i-1][2]<=ma[i][2]) and (ma[i-1][1]<=ma[i-1][2]) and (ma[i][1]>ma[i][2]):
                    record.append(['buy',ma[i][4],ma[i][5]]) 
            elif record[-1][0] == 'buy':
                if (ma[i-1][2]<=ma[i][2]) and (ma[i-1][1]>=ma[i-1][2]) and (ma[i][1]<ma[i][2]):
                    record.append(['sell',ma[i][4],ma[i][5]])
    elif wk=='B': # 5ma and 10ma上揚且黃金交叉買 死亡交叉賣
        for i in range(1,len(ma)):
            if record[-1][0] != 'buy':
                if (ma[i-1][0]<=ma[i][0]) and (ma[i-1][1]<=ma[i][1]) and (ma[i-1][0]<=ma[i-1][1]) and (ma[i][0]>ma[i][1]):
                    record.append(['buy',ma[i][4],ma[i][5]]) 
            elif record[-1][0] == 'buy':
                if (ma[i-1][1]<=ma[i][1]) and (ma[i-1][0]>=ma[i-1][1]) and (ma[i][0]<ma[i][1]):
                    record.append(['sell',ma[i][4],ma[i][5]])
    elif wk=='C': #均線多頭排列買 5日線跌破10日且其餘均線仍上揚時賣
        for i in range(1,len(ma)):
            if record[-1][0] != 'buy':
                if (ma[i-1][0]<=ma[i][0]) and (ma[i-1][1]<=ma[i][1]) and (ma[i-1][2]<=ma[i-1][2]) and (ma[i][3]<=ma[i][3]) and (ma[i][0]>ma[i][1]>ma[i][2]>ma[i][3]):
                    record.append(['buy',ma[i][4],ma[i][5]]) 
            elif record[-1][0] == 'buy':
                if (ma[i-1][0]<ma[i][1]) and (ma[i-1][1]<=ma[i][1]) and (ma[i-1][2]<=ma[i-1][2]) and (ma[i][3]<=ma[i][3]) and (ma[i][0]>ma[i][1]>ma[i][2]>ma[i][3]):
                    record.append(['sell',ma[i][4],ma[i][5]])
    elif wk=='D': #格蘭必40MA 股價突破且均線上揚時買 均線下跌且股價跌破時賣
        for i in range(1,len(ma)):
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

def backtestwil(wil,wl,wh):  # 威廉的回測function
    record=[[0]]; mt=[]; mp=[]; st=[]; sp=[]; rr=[]; w=0; l=0
    for i in range(1,len(wil)):
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

tt='1' #隨便設一個變數，如果變數被更動，迴圈就會結束，也就是系統shutdown
while(tt=='1'):
    r=input('Please type in the ideal method:(kd、william、ma)')  #先讓使用者選特定指標，這個視窗只有這一個輸入選項，之後再依據他輸入的跳出三種對應的輸入介面
    if r=='kd':
        kdstock=KD(rsv_data)  # 這區是讓使用者輸入想要的指標數字後，得到整理過的表格
        del kdstock[:21]
        l='yes'
        while (l=='yes'):
            kd_buy=int(input('type in number 0~100:')) #如果他輸入kd，你們要做出這個視窗讓他們輸入這兩個input
            kd_sell=int(input('type in number 0~100:'))
            pd.set_option('display.unicode.ambiguous_as_wide', True)
            pd.set_option('display.unicode.east_asian_width', True)
            pd.set_option('display.width', 500)
            print(backtestkd(kdstock,kd_buy,kd_sell)[0], '\n'*2+backtestkd(kdstock,kd_buy,kd_sell)[1]) #輸入完列印這個東西
            l=input("Another try?(yes or no):")  #同時要顯示這個輸入選項
    elif r=='william':#(同kd之敘述)
        l='yes'
        while (l=='yes'):
            wil_buy=int(input('type in number -100~0:'))   # 這區是讓使用者輸入想要的指標數字後，得到整理過的表格
            wil_sell=int(input('type in number -100~0:'))
            pd.set_option('display.unicode.ambiguous_as_wide', True)
            pd.set_option('display.unicode.east_asian_width', True)
            pd.set_option('display.width', 500)
            print(backtestwil(wil_data,wil_buy,wil_sell)[0], '\n'*2+backtestwil(wil_data,wil_buy,wil_sell)[1])
            l=input("Another try?(yes or no):")
    elif r=='ma':#(同kd之敘述)
        print('A:10日均線和20日均線上揚，黃金交叉時買進，死亡交叉時賣出\nB:5日均線和10日均線上揚，黃金交叉時買進，死亡交叉時賣出\nC:均線多頭排列時買進，5日線以外均線仍上揚但5日線跌破10日線時賣\nD:葛蘭必40日均線上揚且股價突破均線時買，均線下跌且股價跌破均線時賣')
        l='yes'
        while (l=='yes'):
            wk=input('type in strategy A~D:')  # 這區是讓使用者輸入想要的均線策略後，得到整理過的表格
            pd.set_option('display.unicode.ambiguous_as_wide', True)
            pd.set_option('display.unicode.east_asian_width', True)
            pd.set_option('display.width', 500)
            print(backtestma(ma_data,wk)[0], '\n'*2+backtestma(ma_data,wk)[1])
            l=input("Another try?(yes or no):")
    ask=input("Do you want to end the system?(yes or no):")
    if ask=='yes': #回答yes，你們就要設計一個結束的介面；若回答no，你們要讓介面跳回一開始輸入指標選項的地方
        tt='0'
print('Thank you!')#如果使用者在l中輸入no，也就是跳出那個指標的測試介面，那就要顯示這個問句介面

print(os.getcwd())
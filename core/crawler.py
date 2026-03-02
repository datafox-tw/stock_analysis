import os
import requests
import pandas as pd
import time
import random

URL_TEMPLATE = "https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=html&date={}&stockNo={}"

def generate_date_list(end_date, start_date):
    """
    Generates a list of the 1st of each month between two dates.
    Format: YYYYMMDD
    """
    dates = []
    curr_m = int(end_date[4:6])
    curr_y = int(end_date[0:4])
    start_m = int(start_date[4:6])
    start_y = int(start_date[0:4])

    if curr_y > start_y:
        while curr_y > start_y:
            while curr_m > 0:
                dates.append(f"{curr_y}{curr_m:02d}01")
                curr_m -= 1
            curr_m = 12
            curr_y -= 1
    
    if curr_y == start_y:
        while curr_m >= start_m:
            dates.append(f"{curr_y}{curr_m:02d}01")
            curr_m -= 1
            
    return dates

def download_stock_data(stock_no, dates):
    """
    Downloads historical stock data from TWSE.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    for date in dates:
        url = URL_TEMPLATE.format(date, stock_no)
        file_name = f"{stock_no}_{date}.csv"
        if os.path.exists(file_name):
            print(f"Skipping {file_name}, already exists.")
            continue
            
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                # read_html returns a list of dataframes
                dfs = pd.read_html(response.text)
                if dfs:
                    data = dfs[0]
                    data.columns = data.columns.droplevel(0)
                    data.to_csv(file_name, index=False)
        except Exception as e:
            print(f"Error downloading {file_name}: {e}")
        
        # Random sleep to avoid being banned
        time.sleep(random.uniform(2, 5))

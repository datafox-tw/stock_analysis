import csv
import os
import pandas as pd
from .indicators import calculate_rsv, calculate_william14, calculate_william28, calculate_ma

def load_stock_names(file_path):
    """Parses the stocklist.csv to get names and numbers."""
    name_dict = {}
    if not os.path.exists(file_path):
        return name_dict
        
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        last_num = None
        for row in csv_reader:
            for cell in row:
                cell = cell.strip()
                try:
                    num = int(cell)
                    if num > 0:
                        last_num = num
                except ValueError:
                    if last_num is not None:
                        clean_name = cell.replace("＃","").replace("＊","").replace(" ","").replace("　","").replace("\xa0","").strip()
                        if clean_name:
                            name_dict[last_num] = clean_name
                        last_num = None
    return name_dict

def process_downloaded_data(dates, stock_no):
    """
    Reads the downloaded CSVs and prepares the data lists for analysis.
    """
    spj, zgj, zdj, kpj, datte = [], [], [], [], []
    
    for date in dates:
        file_path = f"stock_data/{stock_no}_{date}.csv"
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, newline='', encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            # Keep original reversed logic
            for row in reversed(rows):
                try:
                    spj.append(float(row['收盤價']))
                    zgj.append(float(row['最高價']))
                    zdj.append(float(row['最低價']))
                    datte.append(row['日期'])
                    kpj.append(float(row['開盤價']))
                except (ValueError, KeyError):
                    continue
                    
    # The original code had some reverse() calls. 
    # Let's match the original flow:
    # 1. csv_preprocessing reads CSVs by date.
    # 2. Inside each CSV, it reads rows and appends them to 'm'.
    # 3. It reverses 'm' into 'mr' and extracts to spj, zgj, etc.
    # 4. Then it reverses datte and kpj.
    
    datte.reverse()
    kpj.reverse()
    
    # Calculate indicators
    rsv_data = []
    for i in range(len(spj) - 8):
        rsv_data.append(calculate_rsv(spj, zgj, zdj, i))
        
    wil_data = []
    for i in range(len(spj) - 13):
        w14 = calculate_william14(spj, zgj, zdj, i)
        wil_data.append([w14])
    
    for i in range(len(spj) - 27):
        w28 = calculate_william28(spj, zgj, zdj, i)
        # Match indices
        if i < len(wil_data):
            wil_data[i].append(w28)
            
    # Reverse indicator data to match chronological order for UI
    rsv_data.reverse()
    wil_data.reverse()
    
    # Matching dates for Williams %R
    spj_reversed = list(reversed(spj))
    for i in range(len(wil_data)):
        if i + 13 < len(datte):
            wil_data[i].extend([datte[i+13], kpj[i+13], spj_reversed[i+13]])
    
    # Trim Williams data as per original
    if len(wil_data) > 14:
        wil_data = wil_data[14:]
        
    # Calculate MA data
    ma_data = []
    for i in range(len(spj) - 39):
        mv = calculate_ma(spj, i)
        ma_data.append(mv + [datte[-1-i], spj[i]])
    ma_data.reverse()
    
    return {
        'spj': spj, 'zgj': zgj, 'zdj': zdj, 'kpj': kpj, 'dates': datte,
        'rsv': rsv_data, 'wil': wil_data, 'ma': ma_data
    }

import os
import secrets
from flask import Flask, render_template, request, session, redirect, url_for
import pandas as pd
from core import (
    generate_date_list, 
    download_stock_data, 
    load_stock_names, 
    process_downloaded_data,
    calculate_kd,
    backtest_kd, 
    backtest_william, 
    backtest_ma
)

app = Flask(__name__)
# Professional secret key for sessions
app.secret_key = secrets.token_hex(16)

# Load stock names once at startup
STOCK_NAMES = load_stock_names('stocklist.csv')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        stock_no = request.form.get('stockNo')
        start_date = request.form.get('startDate')
        end_date = request.form.get('endDate')
        
        if not stock_no or not start_date or not end_date:
            return render_template('index.html', error="請填寫所有欄位")
            
        # 1. Download data
        dates = generate_date_list(end_date, start_date)
        download_stock_data(stock_no, dates)
        
        # 2. Store metadata in session
        session['stock_info'] = {
            'no': stock_no,
            'name': STOCK_NAMES.get(int(stock_no), stock_no),
            'start': start_date,
            'end': end_date,
            'dates': dates
        }
        
        return redirect(url_for('analysis'))
        
    return render_template('index.html')

@app.route('/analysis')
def analysis():
    stock_info = session.get('stock_info')
    if not stock_info:
        return redirect(url_for('index'))
    return render_template('analysis.html', stock_info=stock_info)

@app.route('/backtest/<strategy>', methods=['POST'])
def run_backtest(strategy):
    stock_info = session.get('stock_info')
    if not stock_info:
        return redirect(url_for('index'))
        
    # Re-process data from local CSVs (safer than storing in cookie-based session)
    data = process_downloaded_data(stock_info['dates'], stock_info['no'])
    
    result_df = None
    win_rate = ""
    
    if strategy == 'kd':
        buy_t = int(request.form.get('kd_buy', 20))
        sell_t = int(request.form.get('kd_sell', 80))
        # Need to calculate KD first from stored RSV
        kd_data = calculate_kd(data['rsv'], data['dates'], data['kpj'])
        # Trim KD data like original
        if len(kd_data) > 21:
            kd_data = kd_data[21:]
        result_df, win_rate = backtest_kd(kd_data, buy_t, sell_t)
        
    elif strategy == 'william':
        buy_t = int(request.form.get('wil_buy', -80))
        sell_t = int(request.form.get('wil_sell', -20))
        result_df, win_rate = backtest_william(data['wil'], buy_t, sell_t)
        
    elif strategy.startswith('ma_'):
        ma_type = strategy.split('_')[1].upper() # A, B, C, D
        result_df, win_rate = backtest_ma(data['ma'], ma_type)
        
    # Convert result to a list of dicts for easy display in template
    results = []
    if result_df is not None and not isinstance(result_df, str):
        results = result_df.to_dict('records')
    else:
        win_rate = result_df if isinstance(result_df, str) else win_rate

    return render_template('analysis.html', 
                           stock_info=session.get('stock_info'),
                           results=results, 
                           win_rate=win_rate,
                           active_tab=strategy)

@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Use environment variables if possible, or default to debug for now
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
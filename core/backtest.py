import pandas as pd

def backtest_kd(kd_data, buy_threshold, sell_threshold):
    """
    Backtests KD strategy.
    kd_data: List of [K, D, date, price]
    """
    record = []
    trade_state = "none"
    
    # record format: ['buy'/'sell', date, price]
    # Starting from 1 to check cross-over
    for i in range(1, len(kd_data) - 1):
        k_prev, d_prev = kd_data[i-1][0], kd_data[i-1][1]
        k_curr, d_curr = kd_data[i][0], kd_data[i][1]
        
        target_date = kd_data[i+1][2]
        target_price = kd_data[i+1][3]
        
        if trade_state != "buy":
            # Golden cross (K crosses above threshold) - keeping user's original logic
            if k_prev >= buy_threshold > k_curr: # wait, user's original logic was: (kdd[i-1][0]>=kl) and (kdd[i][0]<kl)
                # Actually original was: if (kdd[i-1][0]>=kl) and (kdd[i][0]<kl): buy
                # This looks like buying when K drops below threshold? Let's keep it as is.
                record.append(['buy', target_date, target_price])
                trade_state = "buy"
        elif trade_state == "buy":
            # Death cross (K crosses above threshold)
            if k_prev <= sell_threshold < k_curr:
                record.append(['sell', target_date, target_price])
                trade_state = "sell"
                
    if record and record[-1][0] == 'buy':
        record.pop()
        
    return _summarize_trades(record)

def backtest_william(wil_data, buy_threshold, sell_threshold):
    """
    Backtests Williams %R strategy.
    wil_data: List of [wil14, wil24, date, kpj, spj]
    """
    record = []
    trade_state = "none"
    
    for i in range(1, len(wil_data) - 1):
        # wil14 is at index 0, wil28 is at index 1
        # date is 2, kpj is 3, spj is 4
        wil14_prev = wil_data[i-1][0]
        wil14_curr = wil_data[i][0]
        wil28_prev = wil_data[i-1][1]
        wil28_curr = wil_data[i][1]
        
        target_date = wil_data[i][2]
        target_price = wil_data[i][4]
        
        if trade_state != "buy":
            if wil14_prev <= buy_threshold < wil14_curr:
                record.append(['buy', target_date, target_price])
                trade_state = "buy"
        elif trade_state == "buy":
            if wil28_prev >= sell_threshold > wil28_curr:
                record.append(['sell', target_date, target_price])
                trade_state = "sell"
                
    if record and record[-1][0] == 'buy':
        record.pop()
        
    return _summarize_trades(record)

def backtest_ma(ma_data, strategy_type):
    """
    Backtests MA strategies (A, B, C, D).
    ma_data: List of [ma5, ma10, ma20, ma40, date, spj]
    """
    record = []
    trade_state = "none"
    
    for i in range(1, len(ma_data) - 1):
        m = ma_data[i]
        m_prev = ma_data[i-1]
        
        date = m[4]
        price = m[5]
        
        if strategy_type == 'A': # 10ma and 20ma golden/death cross
            if trade_state != 'buy':
                if (m_prev[1] <= m[1]) and (m_prev[2] <= m[2]) and (m_prev[1] <= m_prev[2]) and (m[1] > m[2]):
                    record.append(['buy', date, price])
                    trade_state = 'buy'
            else:
                if (m_prev[2] <= m[2]) and (m_prev[1] >= m_prev[2]) and (m[1] < m[2]):
                    record.append(['sell', date, price])
                    trade_state = 'sell'
        elif strategy_type == 'B': # 5ma and 10ma golden/death cross
            if trade_state != 'buy':
                if (m_prev[0] <= m[0]) and (m_prev[1] <= m[1]) and (m_prev[0] <= m_prev[1]) and (m[0] > m[1]):
                    record.append(['buy', date, price])
                    trade_state = 'buy'
            else:
                if (m_prev[1] <= m[1]) and (m_prev[0] >= m_prev[1]) and (m[0] < m[1]):
                    record.append(['sell', date, price])
                    trade_state = 'sell'
        elif strategy_type == 'C': # Bullish alignment (5>10>20>40 and rising)
            if trade_state != 'buy':
                if (m_prev[0] <= m[0]) and (m_prev[1] <= m[1]) and (m_prev[2] <= m[2]) and (m_prev[3] <= m[3]) and (m[0] > m[1] > m[2] > m[3]):
                    record.append(['buy', date, price])
                    trade_state = 'buy'
            else:
                # Sell when 5MA falls below 10MA
                if (m_prev[0] >= m_prev[1]) and (m[0] < m[1]):
                    record.append(['sell', date, price])
                    trade_state = 'sell'
        elif strategy_type == 'D': # Granville 40MA
            if trade_state != 'buy':
                if (m_prev[3] < m[3]) and (m[3] < price) and (m_prev[3] >= m_prev[5]):
                    record.append(['buy', date, price])
                    trade_state = 'buy'
            else:
                if (m_prev[3] > m[3]) and (m_prev[5] >= m_prev[3]) and (price < m[3]):
                    record.append(['sell', date, price])
                    trade_state = 'sell'

    if record and record[-1][0] == 'buy':
        record.pop()
        
    return _summarize_trades(record)

def _summarize_trades(record):
    """Internal helper to convert trade record to DataFrame and win rate."""
    if not record:
        return None, "No trades executed."
        
    buy_dates, buy_prices = [], []
    sell_dates, sell_prices = [], []
    returns = []
    wins, losses = 0, 0
    
    for i in range(0, len(record), 2):
        b_date, b_price = record[i][1], record[i][2]
        s_date, s_price = record[i+1][1], record[i+1][2]
        
        buy_dates.append(b_date)
        buy_prices.append(b_price)
        sell_dates.append(s_date)
        sell_prices.append(s_price)
        
        ret = (s_price - b_price) / b_price
        returns.append(f"{round(ret * 100, 2)}%")
        
        if ret > 0: wins += 1
        elif ret < 0: losses += 1
        
    df = pd.DataFrame({
        '買進時間': buy_dates,
        '買進價格': buy_prices,
        '賣出時間': sell_dates,
        '賣出價格': sell_prices,
        '報酬率': returns
    })
    
    win_rate = f"勝率: {round(wins / (wins + losses) * 100, 2)}%" if (wins + losses) > 0 else "無完整交易"
    return df, win_rate

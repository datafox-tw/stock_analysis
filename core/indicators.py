def calculate_rsv(spj, zgj, zdj, position):
    """Calculates RSV for a single day based on 9-day range."""
    sp = spj[position]
    z9g = max(zgj[position:position+9])
    z9d = min(zdj[position:position+9])
    if z9g == z9d:
        return 50.0
    return round(float(((sp - z9d) / (z9g - z9d)) * 100), 2)

def calculate_kd(rsv_list, dates, k_prices):
    """
    Calculates KD values from a list of RSV values.
    Returns: List of [K, D, date, k_price]
    """
    kd = []
    if not rsv_list:
        return []
        
    # Initial value
    k0 = round(float(50 * 2/3 + float(rsv_list[0]) / 3), 2)
    d0 = round(float(50 * 2/3 + 50 / 3), 2)
    kd.append([k0, d0])
    
    k_prev = k0
    d_prev = d0
    
    for i in range(1, len(rsv_list)):
        k_curr = round(float(k_prev * 2/3 + float(rsv_list[i]) / 3), 2)
        d_curr = round(float(d_prev * 2/3 + k_curr / 3), 2)
        
        # Match with date and price (offset by 8 days because RSV uses 9-day window)
        kd.append([k_curr, d_curr, dates[i+8], k_prices[i+8]])
        
        k_prev = k_curr
        d_prev = d_curr
        
    return kd

def calculate_william14(spj, zgj, zdj, position):
    """Calculates 14-day Williams %R."""
    sp = spj[position]
    z14g = max(zgj[position:position+14])
    z14d = min(zdj[position:position+14])
    if z14g == z14d:
        return -50.0
    return round(float(((z14g - sp) / (z14g - z14d)) * 100), 2) * (-1)

def calculate_william28(spj, zgj, zdj, position):
    """Calculates 28-day Williams %R."""
    sp = spj[position]
    z28g = max(zgj[position:position+28])
    z28d = min(zdj[position:position+28])
    if z28g == z28d:
        return -50.0
    return round(float(((z28g - sp) / (z28g - z28d)) * 100), 2) * (-1)

def calculate_ma(spj, position):
    """Calculates 5, 10, 20, 40-day Moving Averages."""
    ma5 = round(sum(spj[position:position+5]) / 5, 2)
    ma10 = round(sum(spj[position:position+10]) / 10, 2)
    ma20 = round(sum(spj[position:position+20]) / 20, 2)
    ma40 = round(sum(spj[position:position+40]) / 40, 2)
    return [ma5, ma10, ma20, ma40]

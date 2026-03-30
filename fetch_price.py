import requests
import datetime
import os

# 文件路径配置
VERSION_FILE = "api_version.txt"
LOG_FILE = "price_log.txt"
DEFAULT_OKX_VERSION = 5

def get_current_okx_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            try: return int(f.read().strip())
            except: return DEFAULT_OKX_VERSION
    return DEFAULT_OKX_VERSION

def save_okx_version(version):
    with open(VERSION_FILE, "w") as f:
        f.write(str(version))

def write_log(source, price):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{now}] ({source}) TRX: {price}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)
    print(f"写入成功: {log_entry.strip()}")

def fetch_price():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # --- 策略 1: 欧意 (OKX) 自动探测逻辑 ---
    okx_v = get_current_okx_version()
    # 尝试当前版本及后续两个版本
    for v in range(okx_v, okx_v + 3):
        url = f"https://www.okx.com/api/v{v}/market/ticker?instId=TRX-USDT"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            res_json = response.json()
            # 校验你提供的 JSON 规律
            if res_json.get('code') == "0" and "data" in res_json and len(res_json['data']) > 0:
                price = res_json['data'][0]['last']
                if v != okx_v:
                    save_okx_version(v)
                write_log(f"OKX_v{v}", price)
                return
        except:
            continue

    # --- 策略 2: 火必 (HTX) 备用 ---
    try:
        url_htx = "https://api.huobi.pro/market/detail/merged?symbol=trxusdt"
        res_htx = requests.get(url_htx, headers=headers, timeout=10).json()
        if res_htx.get('status') == "ok":
            price = res_htx['tick']['close']
            write_log("HTX", price)
            return
    except:
        pass

    # --- 策略 3: Gate.io 备用 ---
    try:
        url_gate = "https://api.gateio.ws/api/v4/spot/tickers?currency_pair=TRX_USDT"
        res_gate = requests.get(url_gate, headers=headers, timeout=10).json()
        if isinstance(res_gate, list) and len(res_gate) > 0:
            price = res_gate[0]['last']
            write_log("Gate", price)
            return
    except:
        pass

    print("错误：所有监控平台均未返回有效数据。")

if __name__ == "__main__":
    fetch_price()

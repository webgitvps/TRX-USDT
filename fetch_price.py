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

def fetch_all_rates():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    usd_cny = 0.0
    trx_usdt = 0.0
    source = "Unknown"

    # --- 1. 获取 USDT/CNY 汇率 ---
    try:
        curr_url = "https://www.okx.com/api/v5/market/exchange-rate"
        curr_res = requests.get(curr_url, headers=headers, timeout=10).json()
        if curr_res.get('code') == "0" and len(curr_res.get('data', [])) > 0:
            # 按照你提供的格式解析 {"usdCny":"6.894"}
            usd_cny = float(curr_res['data'][0]['usdCny'])
    except Exception as e:
        print(f"汇率接口调用失败: {e}")
        usd_cny = 7.2  # 极端情况下的保底参考值

    # --- 2. 获取 TRX/USDT (OKX版本自适应 + 冗余备份) ---
    okx_v = get_current_okx_version()
    found_trx = False
    
    # 优先尝试 OKX
    for v in range(okx_v, okx_v + 3):
        try:
            url = f"https://www.okx.com/api/v{v}/market/ticker?instId=TRX-USDT"
            res = requests.get(url, headers=headers, timeout=10).json()
            if res.get('code') == "0" and len(res.get('data', [])) > 0:
                trx_usdt = float(res['data'][0]['last'])
                source = f"OKX_v{v}"
                if v != okx_v:
                    save_okx_version(v)
                found_trx = True
                break
        except:
            continue

    # 如果 OKX 失败，尝试火必 (HTX)
    if not found_trx:
        try:
            res_htx = requests.get("https://api.huobi.pro/market/detail/merged?symbol=trxusdt", timeout=10).json()
            if res_htx.get('status') == "ok":
                trx_usdt = float(res_htx['tick']['close'])
                source = "HTX"
                found_trx = True
        except:
            pass

    # --- 3. 计算并覆盖写入 ---
    if found_trx and usd_cny > 0:
        trx_cny = round(trx_usdt * usd_cny, 4)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构造单行输出：时间 | 来源 | USDT兑人民币 | TRX兑USDT | TRX兑人民币
        log_entry = f"[{now}] ({source}) USDT/CNY: {usd_cny} | TRX/USDT: {trx_usdt} | TRX/CNY: {trx_cny}"
        
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(log_entry)
        print(f"数据已更新: {log_entry}")
    else:
        print("错误：未能获取完整数据，未更新文件。")

if __name__ == "__main__":
    fetch_all_rates()

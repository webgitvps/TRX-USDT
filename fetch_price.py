import requests
import datetime
import os

# 本地记录文件
VERSION_FILE = "api_version.txt"
LOG_FILE = "price_log.txt"
DEFAULT_VERSION = 5

def get_current_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except:
                return DEFAULT_VERSION
    return DEFAULT_VERSION

def save_version(version):
    with open(VERSION_FILE, "w") as f:
        f.write(str(version))

def fetch_price():
    base_url = "https://www.okx.com/api/v{version}/market/ticker?instId=TRX-USDT"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    start_version = get_current_version()
    
    # 从记录的版本开始，向后探测 5 个版本号（防止跳跃式升级）
    for v in range(start_version, start_version + 6):
        url = base_url.format(version=v)
        try:
            response = requests.get(url, headers=headers, timeout=10)
            # 无论状态码是多少，直接解析 JSON 检查规律
            res_json = response.json()
            
            # 核心判断：必须符合你提供的 JSON 规律
            if res_json.get('code') == "0" and "data" in res_json and len(res_json['data']) > 0:
                ticker_data = res_json['data'][0]
                
                # 进一步确认关键字段存在
                if "last" in ticker_data and ticker_data.get("instId") == "TRX-USDT":
                    price = ticker_data['last']
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 写入价格日志
                    with open(LOG_FILE, "a", encoding="utf-8") as f:
                        f.write(f"[{now}] (v{v}) TRX: {price}\n")
                    
                    # 如果当前版本号大于记录的版本号，则更新
                    if v != start_version:
                        save_version(v)
                        print(f"检测到 API 升级，已更新版本记录为 v{v}")
                    
                    print(f"抓取成功: {price} (via v{v})")
                    return # 成功匹配规律，退出
                
            print(f"v{v} 返回数据不符合 TRX 规律，尝试下一版...")
            
        except Exception as e:
            print(f"请求 v{v} 失败: {e}")
            continue

    print("错误：无法在任何探测版本中找到符合规律的 OKX 数据。")

if __name__ == "__main__":
    fetch_price()

import requests
from bs4 import BeautifulSoup
import json
import datetime

# 設定要抓取的幣別與目標銀行
currencies = ['USD', 'EUR', 'CNY', 'JPY', 'AUD']
banks_of_interest = [
    '臺灣銀行', '兆豐銀行', '第一銀行', '中國信託', '國泰世華', 
    '玉山銀行', '台北富邦', '華南銀行', '台新銀行', '合作金庫'
]

def fetch_rates():
    # 建立一個乾淨的字典來存放銀行資料
    bank_data = {bank: {} for bank in banks_of_interest}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }

    for curr in currencies:
        url = f"https://www.findrate.tw/{curr}/"
        try:
            # 發送網頁請求
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 找到匯率表格
            table = soup.find('table')
            if not table:
                continue
                
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                # 確保表格欄位數量正確 (銀行名稱, 現鈔買入, 現鈔賣出, 即期買入, 即期賣出)
                if len(cols) >= 5:
                    bank_name_raw = cols[0].text.strip()
                    
                    # 比對是否為我們關注的 10 大銀行
                    matched_bank = next((b for b in banks_of_interest if b in bank_name_raw), None)
                    if matched_bank:
                        # 處理沒有報價的情況 (有些銀行網頁會顯示 --)
                        def parse_rate(text):
                            cleaned = text.replace('--', '0').strip()
                            try:
                                return float(cleaned)
                            except ValueError:
                                return 0.0

                        # Findrate 的欄位順序通常為：銀行, 現鈔買入, 現鈔賣出, 即期買入, 即期賣出
                        bank_data[matched_bank][curr] = {
                            "cash_buy": parse_rate(cols[1].text),
                            "cash_sell": parse_rate(cols[2].text),
                            "spot_buy": parse_rate(cols[3].text),
                            "spot_sell": parse_rate(cols[4].text)
                        }
        except Exception as e:
            print(f"抓取 {curr} 失敗: {e}")

    # 將字典轉換成前端需要的 JSON 陣列格式
    rates_list = []
    for bank, currencies_data in bank_data.items():
        if currencies_data: # 如果這家銀行有抓到資料才加入
            entry = {"bank": bank}
            entry.update(currencies_data)
            rates_list.append(entry)

    # 取得台灣當前時間 (UTC+8)
    tw_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    
    output = {
        "update_time": tw_time.strftime("%Y-%m-%d %H:%M:%S"),
        "rates": rates_list
    }

    # 存檔成 rates.json
    with open('rates.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"匯率資料更新成功！({tw_time.strftime('%Y-%m-%d %H:%M:%S')})")

if __name__ == "__main__":
    fetch_rates()

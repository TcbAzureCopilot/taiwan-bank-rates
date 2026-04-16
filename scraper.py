import cloudscraper
from bs4 import BeautifulSoup
import json
import datetime

currencies = ['USD', 'EUR', 'CNY', 'JPY', 'AUD']
banks_of_interest = [
    '臺灣銀行', '兆豐銀行', '第一銀行', '中國信託', '國泰世華', 
    '玉山銀行', '台北富邦', '華南銀行', '台新銀行', '合作金庫'
]

def fetch_rates():
    bank_data = {bank: {} for bank in banks_of_interest}
    
    # 建立 cloudscraper 物件，專門用來繞過網站的防機器人機制
    scraper = cloudscraper.create_scraper()

    for curr in currencies:
        url = f"https://www.findrate.tw/{curr}/"
        print(f"正在抓取 {curr}...")
        try:
            # 使用 scraper 代替傳統的 requests
            res = scraper.get(url, timeout=15)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            table = soup.find('table')
            if not table:
                print(f"  [警告] 找不到 {curr} 的表格，可能網站改版或又被擋下了！")
                continue
                
            rows = table.find_all('tr')
            success_count = 0
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 5:
                    bank_name_raw = cols[0].text.strip()
                    matched_bank = next((b for b in banks_of_interest if b in bank_name_raw), None)
                    if matched_bank:
                        def parse_rate(text):
                            cleaned = text.replace('--', '0').strip()
                            try:
                                return float(cleaned)
                            except ValueError:
                                return 0.0

                        bank_data[matched_bank][curr] = {
                            "cash_buy": parse_rate(cols[1].text),
                            "cash_sell": parse_rate(cols[2].text),
                            "spot_buy": parse_rate(cols[3].text),
                            "spot_sell": parse_rate(cols[4].text)
                        }
                        success_count += 1
            print(f"  成功抓取 {success_count} 家銀行的 {curr} 匯率。")
        except Exception as e:
            print(f"  抓取 {curr} 發生錯誤: {e}")

    rates_list = []
    for bank, currencies_data in bank_data.items():
        if currencies_data:
            entry = {"bank": bank}
            entry.update(currencies_data)
            rates_list.append(entry)

    tw_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    
    output = {
        "update_time": tw_time.strftime("%Y-%m-%d %H:%M:%S"),
        "rates": rates_list
    }

    with open('rates.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 匯率資料更新完畢！共取得 {len(rates_list)} 家銀行資料。")

if __name__ == "__main__":
    fetch_rates()

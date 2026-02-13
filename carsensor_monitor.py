import requests
from bs4 import BeautifulSoup

def get_carsensor_items(url):
    """カーセンサーから指定URLの車両情報を取得する関数"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers)
        res.encoding = res.apparent_encoding
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        
        items = []
        # 物件ごとのブロックを探す
        cassettes = soup.find_all("div", class_="cassetteMain")
        
        count = 0
        for cassette in cassettes:

            #　価格を取得し、リース車を除外
            price_content = cassette.find("p", class_="totalPrice__content")
            if price_content:
                price = price_content.get_text(strip=True)
            else:
                price = "価格不明"

            if "価格不明" in price or "月額" in price:
                continue


            # タイトルとリンクを取得
            link_tag = cassette.find("a", class_="cassetteMain__link")
            if link_tag:
                title = link_tag.get_text(strip=True)
                relative_url = link_tag.get("href")
                full_url = "https://www.carsensor.net" + relative_url
            
                # URLからID（例: CU12345678）を抽出
                item_id = relative_url.split("/")[-2] if "/" in relative_url else "no_id"
            else:
                continue

            count += 1

            items.append({
                "id": item_id,
                "title": title,
                "price": price,
                "url": full_url,
                "count": count
            })
            
        return items
    except Exception as e:
        print(f"エラー発生: {e}")
        return []

if __name__ == "__main__":
    TARGET_URL = "https://www.carsensor.net/usedcar/search.php?STID=CS210610&SORT=19&CARC=HO_S028&PMAX=500000&SLST=MT"
    results = get_carsensor_items(TARGET_URL)
    for item in results:
        print(f"{item['count']}台目 ID: {item['id']} | {item['title']} | 総額: {item['price']}")
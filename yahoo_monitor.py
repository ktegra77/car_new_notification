import requests
from bs4 import BeautifulSoup

def get_yahoo_items(url):
    """ヤフオクから指定URLの車両情報を取得する関数"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        
        items = []
        # ヤフオクの商品リストの各要素を探す（liタグのクラス名：Product）
        products = soup.find_all("div", class_="a cf")
        count = 0
        for product in products:
            # --- 1. タイトルとURLを取得 ---
            # h3タグの中のaタグを探す
            title_tag = product.find("h3").find("a") if product.find("h3") else None
            
            if not title_tag:
                continue
            
            title = title_tag.get_text(strip=True)
            full_url = title_tag.get("href")
            
            # IDを抽出 (URLの末尾がID)
            item_id = full_url.split("/")[-1]
            
            # --- 2. 価格情報を取得 ---
            # <dl class="pri1"> の中の <dd> を探す
            price_box = product.find("dl", class_="pri1")
            price = price_box.find("dd").get_text(strip=True) if price_box else "価格不明"

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
        print(f"ヤフオクでエラー発生: {e}")
        return []

if __name__ == "__main__":
    TARGET_URL = "https://auctions.yahoo.co.jp/category/list/26360/?select=22&auccat=26360&b=1&n=50&mode=1&brand_id=8185&spec=C_4%3A91%2C917%2C5379&slider="
    results = get_yahoo_items(TARGET_URL)
    for item in results:
        print(f"{item['count']}台目 ID: {item['id']} | {item['title']} | 価格: {item['price']}")
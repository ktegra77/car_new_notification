import logging
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import re

# ログ設定
logger = logging.getLogger(__name__)

# 定数
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HTTP_HEADERS = {"User-Agent": USER_AGENT}

def fetch_listings(search_url: str) -> List[Dict[str, str]]:
    """
    ヤフオクの検索結果ページから車両情報を取得します。

    Args:
        search_url (str): 取得対象のURL

    Returns:
        List[Dict[str, str]]: 車両情報（id, title, price, url）のリスト
    """
    vehicle_items: List[Dict[str, str]] = []
    seen_ids = set()

    try:
        response = requests.get(search_url, headers=HTTP_HEADERS, timeout=15)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except requests.RequestException as e:
        logger.error(f"HTTPリクエスト失敗 (Yahoo Auctions): {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    product_elements = soup.find_all("div", class_="a cf")
    for element in product_elements:
        try:
            item_id = "ID不明"
            # タイトルとURLの取得
            title_tag = element.find("h3").find("a") if element.find("h3") else None
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            full_url = title_tag.get("href", "")
            
            # IDの抽出 (URLから末尾のIDを取得)
            item_id = full_url.split("/")[-1] if "/" in full_url else "ID不明"
            if item_id in seen_ids:
                continue

            # 価格情報の取得
            price_tag = element.find("dl", class_="pri1")
            price = "価格不明"
            if price_tag:
                price_raw = price_tag.get_text(strip=True)
                # 数字のみを抽出してカンマ区切りに整形
                price_match = re.search(r"([\d,]+)", price_raw)
                if price_match:
                    price_num = price_match.group(1).replace(",", "")
                    price = f"{int(float(price_num)):,}円"

            vehicle_items.append({
                "id": item_id,
                "title": title,
                "price": price,
                "url": full_url
            })
            seen_ids.add(item_id)

        except Exception as e:
            logger.warning(f"ID:{item_id} ヤフオクの要素解析中にエラーが発生しました（スキップします）: {e}")
            continue

    return vehicle_items

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # テスト用：車両カテゴリの検索結果
    TEST_URL = "https://auctions.yahoo.co.jp/category/list/26360/?auccat=26360&spec=C_4%3A91%2C917%2C5379&brand_id=8185&price_type=currentprice&min=&max=600000&ei=UTF-8&oq=&tab_ex=commerce&select=22&mode=1&fr=auc_car_adv"
    results = fetch_listings(TEST_URL)
    
    print(f"取得件数: {len(results)}件")
    for i, item in enumerate(results, 1):
        print(f"{i}台目: ID: {item['id']} | {item['title']} | 価格：{item['price']}")
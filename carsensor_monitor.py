import logging
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import re

# ログ設定
logger = logging.getLogger(__name__)

# 定数の定義
BASE_URL = "https://www.carsensor.net"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HTTP_HEADERS = {"User-Agent": USER_AGENT}

def fetch_listings(search_url: str) -> List[Dict[str, str]]:
    """
    カーセンサーの検索結果ページから車両情報を取得し、リスト形式で返却します。

    Args:
        search_url (str): 取得対象の検索結果URL

    Returns:
        List[Dict[str, str]]: 車両情報の辞書（id, title, price, url）を含むリスト
    """
    vehicle_items: List[Dict[str, str]] = []

    try:
        response = requests.get(search_url, headers=HTTP_HEADERS, timeout=15)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except requests.RequestException as e:
        logger.error(f"HTTPリクエスト失敗 (カーセンサー): {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
   
    listing_elements = soup.find_all("div", class_="cassetteMain")

    for element in listing_elements:
        try:
            item_id = "ID不明"
            # 価格の取得とフィルタリング
            price = "価格不明"
            price_tag = element.find("p", class_="totalPrice__content")

            # リース車や価格不明を除外
            if not price_tag or any(exclude in price_tag.get_text() for exclude in ["価格不明", "月額"]): 
                continue

            price_match = re.search(r"([\d.]+)", price_tag.get_text(strip=True))
            if price_match:
                price = f"{float(price_match.group(1)):,}万円"


            # リンクとタイトルの取得
            link_tag = element.find("a", class_="cassetteMain__link")
            if not link_tag:
                continue

            title = link_tag.get_text(strip=True)
            relative_url = link_tag.get("href", "")
            full_url = f"{BASE_URL}{relative_url}"

            # IDの抽出
            url_parts = relative_url.split("/")
            item_id = url_parts[-2] if len(url_parts) >= 2 else "ID不明"

            vehicle_items.append({
                "id": item_id,
                "title": title,
                "price": price,
                "url": full_url
            })

        except Exception as e:
            logger.warning(f"ID:{item_id} カーセンサーの要素解析中にエラーが発生しました（スキップします）: {e}")
            continue

    return vehicle_items

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    TEST_URL = "https://www.carsensor.net/usedcar/search.php?STID=CS210610&SORT=19&CARC=HO_S028&PMAX=500000&SLST=MT"
    results = fetch_listings(TEST_URL)
    
    print(f"取得件数: {len(results)}件")
    for i, item in enumerate(results, 1):
        print(f"{i}台目: ID: {item['id']} | {item['title']} | 価格：{item['price']}")
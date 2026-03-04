import logging
import re
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

# ログ設定
logger = logging.getLogger(__name__)

# 定数
BASE_URL = "https://www.goo-net.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HTTP_HEADERS = {"User-Agent": USER_AGENT}

def fetch_listings(search_url: str) -> List[Dict[str, str]]:
    """
    グーネットの検索結果ページから車両情報を取得します。

    Args:
        search_url (str): 取得対象のURL

    Returns:
        List[Dict[str, str]]: 車両情報（id, title, price, url）のリスト
    """
    vehicle_items: List[Dict[str, str]] = []

    try:
        response = requests.get(search_url, headers=HTTP_HEADERS, timeout=15)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except requests.RequestException as e:
        logger.error(f"HTTPリクエスト失敗 (Goo-net): {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    
    cassettes = soup.find_all("div", class_=lambda x: x and ("search-cassette" in x or "importedCar" in x))

    for cassette in cassettes:
        try:
            item_id = "ID不明"
            # 詳細ページへのリンクを探す
            detail_link = cassette.find("a", href=lambda x: x and "spread/goo" in x)
            
            if detail_link:
                href = detail_link["href"]
                # URLから数字15桁以上のIDを抽出
                match = re.search(r'(\d{15,})', href)
                item_id = match.group(1) if match else href.split("/")[-1].replace(".html", "")
                full_url = f"{BASE_URL}{href}" if href.startswith("/") else href

            if not item_id:
                logger.warning("カセットは見つかりましたが、詳細リンク(spread/goo)が取得できませんでした。構造変化の可能性があります。")
                continue

            # タイトルの取得
            title = "車種不明"
            # タイトルはh2タグかdivタグのどちらかに入っていることが多い
            title_tag = cassette.find(["h2", "div"], class_=lambda x: x and "heading" in x)
            if title_tag:
                title = title_tag.get_text(strip=True) 

            # 価格の取得
            price = "価格不明"
            # 支払総額を優先
            total_price_tag = cassette.find("p", class_=lambda x: x and "num-red" in x)
            
            if total_price_tag:
                price_val = total_price_tag.find("em")
                if price_val:
                    sanitize_price = price_val.get_text(strip=True)
                    price = f"総額{float(sanitize_price):,}万円"
                else:
                    sanitize_price = total_price_tag.get_text(strip=True)
                    price = f"総額{float(sanitize_price):,}万円"
            else:
                # 総額がない場合は車両本体価格
                car_price_tag = cassette.find("p", class_="num")
                if car_price_tag:
                    price = car_price_tag.get_text(strip=True)
                    logger.error(f"ID:{item_id} 総額が見つかりませんでした。車両本体価格を使用します※str型: {price}")

            vehicle_items.append({
                "id": item_id,
                "title": title,
                "price": price,
                "url": full_url or ""
            })

        except Exception as e:
            logger.warning(f"ID:{item_id} goo-net解析中にエラーが発生しました: {e}")
            continue

    return vehicle_items

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # テスト用URL
    TEST_URL = "https://www.goo-net.com/php/search/summary.php?car_cd=10201029&maker_cd=1020&pref_c=01%2C02%2C03%2C04%2C05%2C06%2C07%2C08%2C09%2C10%2C11%2C12%2C13%2C14%2C15%2C16%2C17%2C18%2C19%2C20%2C21%2C22%2C23%2C24%2C25%2C26%2C27%2C28%2C29%2C30%2C31%2C32%2C33%2C34%2C35%2C36%2C37%2C38%2C39%2C40%2C41%2C42%2C43%2C44%2C45%2C46%2C47&price2=60&car_price=1&total_payment=1&mission=MT&baitai=goo&search_type=car_search&current=0&page=1&sort_value=desc&sort_flag=update_date_sort&disp_mode=detail_list&door_cd_flg=1&limit=50&car_list=10201029&integration_car_cd=10201029%7C&new_car_cds_list=10201029&search_flg=1&fancy_box=0&model_grade_name=%5B%5D&templates=0&area_nap_flg=1&custom_flg=0"
    results = fetch_listings(TEST_URL)
    
    print(f"取得件数: {len(results)}件")
    for i, item in enumerate(results, 1):
        print(f"{i}台目: ID: {item['id']} | {item['title']} | 価格：{item['price']}")
import logging
import re
import time
import random
from typing import List, Dict
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# ログ設定
logger = logging.getLogger(__name__)

BASE_URL = "https://jmty.jp"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch_listings(search_url: str) -> List[Dict[str, str]]:
    """
    ジモティーの検索結果ページから車両情報を取得します。
    ※Playwrightを使用して動的コンテンツに対応します。

    Args:
        search_url (str): 取得対象のURL

    Returns:
        List[Dict[str, str]]: 車両情報（id, title, price, url）のリスト
    """
    vehicle_items: List[Dict[str, str]] = []
    seen_ids = set()

    with sync_playwright() as p:
        try:
            # ブラウザ起動
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=USER_AGENT)
            page = context.new_page()

            # ページ遷移と待機
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            # aタグが表示されるまで待機
            page.wait_for_selector("a", timeout=15000)
            
            # 人間味のある待機
            time.sleep(random.uniform(2, 5))

            # HTMLを取得して解析
            content = page.content()
            soup = BeautifulSoup(content, "html.parser")

            # 抽出ロジック
            detail_links = soup.find_all("a", href=re.compile(r"/article"))

            for link in detail_links:
                item_id = "ID不明"
                href = link.get("href", "")
                if not href: continue
                
                # IDの抽出
                item_id = href.split("/")[-1]
                if item_id in seen_ids:
                    continue
                
                # 投稿の親要素（リスト項目）まで遡る
                parent = link.find_parent(["li", "article"])
                if not parent:
                    continue

                # タイトルの取得
                title = "タイトル不明"

                title_tag = parent.find(class_=lambda x: x and "title" in x)
                if title_tag:
                    title = title_tag.get_text(strip=True)
                else:
                    img_tag = parent.find("img", alt=True)
                    if img_tag:
                        title = img_tag["alt"]

                # 価格の取得
                price = "価格不明"

                important_field = parent.find(class_="p-item-most-important")
                if important_field:
                    price_raw = important_field.get_text(strip=True)
                    price_match = re.search(r"([\d,]+)円", price_raw)

                    if price_match:
                        price_num = re.sub(r"\D", "", price_match.group(1))
                        if price_num:
                            price = f"{int(float(price_num)):,}円"

                full_url = f"{BASE_URL}{href}" if href.startswith("/") else href

                vehicle_items.append({
                    "id": item_id,
                    "title": title,
                    "price": price,
                    "url": full_url
                })
                seen_ids.add(item_id)

        except Exception as e:
            logger.warning(f"ID:{item_id} ジモティー解析中にエラーが発生しました: {e}")
        
        finally:
            browser.close()
    
    return vehicle_items

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    TEST_URL = "https://jmty.jp/all/car-hon/g-2346?model_year%5Bmin%5D=&model_year%5Bmax%5D=&mileage%5Bmin%5D=&mileage%5Bmax%5D=&min=&max=600000&commit=%E6%A4%9C%E7%B4%A2"
    results = fetch_listings(TEST_URL)
    
    print(f"取得件数: {len(results)}件")
    for i, item in enumerate(results, 1):
        print(f"{i}台目: ID: {item['id']} | {item['title']} | 価格：{item['price']}")
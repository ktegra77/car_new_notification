import logging
import re
import time
import random
from typing import List, Dict
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://jp.mercari.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch_listings(search_url: str) -> List[Dict[str, str]]:
    """
    メルカリの検索結果ページから車両情報を取得し、リスト形式で返却します。
    ※Playwrightを使用して動的コンテンツに対応します。

    Args:
        search_url (str): 取得対象の検索結果URL

    Returns:
        List[Dict[str, str]]: 車両情報の辞書（id, title, price, url）を含むリスト
    """
        
    vehicle_items: List[Dict[str, str]] = []

    with sync_playwright() as p:
        try:
            item_id = "ID不明"
            # ブラウザ起動
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=USER_AGENT,
                # 縦に長い画面として認識させる
                viewport={'width': 1200, 'height': 2400}
            )
            page = context.new_page()

            # ページ遷移と待機
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(random.uniform(2, 5))

            # 最下部までスクロールして読み込ませる
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 5))

            # HTMLを取得して解析
            soup = BeautifulSoup(page.content(), "html.parser")
            products = soup.find_all("li", attrs={"data-testid": "item-cell"})

            for product in products:
                # 「売り切れ」や「PR」などの非商品を排除
                product_text = product.get_text(strip=True)
                if "売り切れ" in product_text or "PR" in product_text:
                    continue

                anchor = product.find("a")
                if not anchor: continue

                # 「似ている商品」などの関連枠を排除
                location = anchor.get("data-location", "")
                if "search_result:newest:body:item_list" not in location:
                    continue

                # タイトルと価格の抽出
                thumbnail_div = product.find("div", class_=lambda x: x and "merItemThumbnail" in x)
                label = thumbnail_div.get("aria-label", "") if thumbnail_div else ""
                
                if not label:
                    label = anchor.get("aria-label", "")

                if label and "の画像" in label:
                    title_part = label.split("の画像")[0].strip()
                    price_part = label.split("の画像")[-1].strip()
                    
                    # まず専用クラス merPrice から抜き出しを試み、補助的に label を使う
                    price_display = "価格不明"
                    price_tag = product.find("span", class_=lambda x: x and "merPrice" in x)
                    
                    if price_tag:
                        # 実際の価格表示部分から数字だけを抜く
                        price_val = re.sub(r"\D", "", price_tag.get_text(strip=True))
                        if price_val:
                            price_display = f"{int(float(price_val)):,}円"
                    
                    # 万が一 merPrice が取れなかった場合のみ、ラベルの後半から抽出
                    if price_display == "価格不明":
                        price_val = re.sub(r"\D", "", price_part)
                        if price_val:
                            price_display = f"{int(float(price_val)):,}円"

                    # IDとURL
                    relative_url = anchor.get("href")
                    item_id = relative_url.split("/")[-1]
                    full_url = relative_url if relative_url.startswith("http") else BASE_URL + relative_url

                    vehicle_items.append({
                        "id": item_id,
                        "title": title_part,
                        "price": price_display,
                        "url": full_url
                    })
                
                else:
                    logger.warning(f"ラベルの形式が想定外です（'の画像' が見つかりません）: {label}")
            
        except Exception as e:
            logger.warning(f"ID:{item_id} メルカリ解析中にエラーが発生しました: {e}")
        
        finally:
            browser.close()

    return vehicle_items

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    TEST_URL = "https://jp.mercari.com/search?keyword=%E3%83%95%E3%82%A3%E3%83%83%E3%83%88&category_id=10865&sort=created_time&order=desc"
    results = fetch_listings(TEST_URL)

    print(f"取得件数: {len(results)}件")
    for i, item in enumerate(results, 1):
        print(f"{i}台目 ID: {item['id']} | {item['title']} | 価格: {item['price']}")
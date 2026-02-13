import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import random

def get_mercari_items(url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--incognito') # シークレットモード
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    items = []
    try:
        driver.get(url)

        driver.set_window_size(1200, 2000) # 縦に長い画面として認識させる
        
        # 1. ページが安定するまで少し待つ
        time.sleep(random.uniform(5, 7))  # 5～7秒のランダム待機
        
        # 2. 最下部までスクロールして全件読み込ませる（31件程度ならこれで確実になります）
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 4))  # 2～4秒のランダム待機

        # 現在の画面で何個の商品が見えているかターミナルに表示する
        # visible_items = driver.find_elements(By.CSS_SELECTOR, "li[data-testid='item-cell']")
        # print(f"ブラウザ上で認識している商品数: {len(visible_items)}")

        # 3. HTML解析
        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.find_all("li", attrs={"data-testid": "item-cell"})
        
        for product in products:
            # --- 1. 徹底排除フィルタ ---
            
            # (A) 売り切れ除外
            if "売り切れ" in product.get_text():
                continue
            
            # (B) PR（広告）枠を排除
            if "PR" in product.get_text():
                continue

            anchor = product.find("a")
            if not anchor: continue

            # (C) 「似ている商品」などの関連枠を排除 (data-locationをチェック)
            location = anchor.get("data-location", "")
            # 検索結果（newest）かつ 商品リスト（item_list）に含まれるものだけを許可
            if "search_result:newest:body:item_list" not in location:
                continue

            # --- 2. タイトルと価格を抜き出し ---
            thumbnail_div = product.find("div", class_=lambda x: x and "merItemThumbnail" in x)
            label = thumbnail_div.get("aria-label", "") if thumbnail_div else ""
            
            if not label:
                label = anchor.get("aria-label", "")

            if label and "の画像" in label:
                title = label.split("の画像")[0].strip()
                price_part = label.split("の画像")[-1].strip()
                price = price_part.replace("¥", "").replace(",", "").replace("円", "").strip()
                
                # 数字以外のゴミ（「現在」など）が混じっている場合の最終掃除
                import re
                price_digits = re.sub(r"\D", "", price) 
                price = f"{price_digits}円"
            else:
                continue # ラベルが正しく取れないものはノイズとして捨てる

            # --- 3. URL/ID取得 ---
            relative_url = anchor.get("href")
            full_url = "https://jp.mercari.com" + relative_url
            item_id = relative_url.split("/")[-1]

            items.append({
                "id": item_id,
                "title": title,
                "price": price,
                "url": full_url
            })
            
    except Exception as e:
        print(f"メルカリでエラー発生: {e}")
    finally:
        driver.quit()
        
    return items

if __name__ == "__main__":
    TARGET_URL = "https://jp.mercari.com/search?keyword=%E3%83%95%E3%82%A3%E3%83%83%E3%83%88&category_id=10865&sort=created_time&order=desc"
    results = get_mercari_items(TARGET_URL)
    for i, item in enumerate(results, 1):
        print(f"{i}台目 ID: {item['id']} | {item['title']} | 価格: {item['price']}")
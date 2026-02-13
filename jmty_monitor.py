import time
import random
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def get_jmty_items(url):
    options = Options()
    options.add_argument('--headless')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    items = []
    try:
        driver.get(url)
        
        # 待機対象を「aタグ」など、より確実にあるものに変更
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "a")))

        time.sleep(random.uniform(2, 5)) # 描画完了を待つ

        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # --- 抽出戦略の変更 ---
        # 1. まず「中古車詳細」へのリンク（/articles/を含むaタグ）をすべて探す
        detail_links = soup.find_all("a", href=re.compile(r"/article"))
        # 重複を避けるためのセット
        seen_ids = set()

        for link in detail_links:
            href = link.get("href")
            if "adclick" in href or not href: continue
            
            item_id = href.split("/")[-1]
            if item_id in seen_ids: continue
            
            # --- 修正箇所：確実に「投稿の塊」まで遡る ---
            # リンク(a) から見て、リストの1項目(li) または 記事(article) を探す
            parent = link.find_parent(["li", "article"])
            if not parent: continue

            # タイトルの取得（parent全体から "title" を含むクラスを再検索）
            title_tag = parent.find(class_=lambda x: x and "title" in x)
            if not title_tag:
                # クラス名で見つからない場合、imgタグのalt属性から取る（ジモティーでは有効な手です）
                img_tag = parent.find("img", alt=True)
                title = img_tag["alt"] if img_tag else "タイトル不明"
            else:
                title = title_tag.get_text(strip=True)

            # 価格の取得
            price_tag = parent.find(class_=lambda x: x and "price" in x)
            if price_tag:
                price_raw = price_tag.get_text(strip=True)
                price_num = re.sub(r"\D", "", price_raw)
                price = f"{price_num}円" if price_num else price_raw
            else:
                price = "価格不明"

            items.append({
                "id": item_id,
                "title": title,
                "price": price,
                "url": "https://jmty.jp" + href if href.startswith("/") else href
            })
            seen_ids.add(item_id)

    except Exception as e:
        print(f"ジモティーでエラー発生: {e}")
    finally:
        driver.quit()
        
    return items

if __name__ == "__main__":
    TARGET_URL = "https://jmty.jp/all/car-hon/g-2346?model_year%5Bmin%5D=&model_year%5Bmax%5D=&mileage%5Bmin%5D=&mileage%5Bmax%5D=&min=&max=600000&commit=%E6%A4%9C%E7%B4%A2"
    results = get_jmty_items(TARGET_URL)
    for i, item in enumerate(results, 1):
        print(f"{i}台目 ID: {item['id']} | {item['title']} | 価格: {item['price']}")
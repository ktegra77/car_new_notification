import os
import time
import urllib.parse
from playwright.sync_api import sync_playwright

# 既存の自作モジュール（これらはそのまま使います）
from common_notifier import send_discord_message
from carsensor_monitor import get_carsensor_items
from yahoo_monitor import get_yahoo_items
from mercari_monitor import get_mercari_items
from goonet_monitor import get_goonet_items
from jmty_monitor import get_jmty_items

# --- 設定エリア ---
WEBHOOK_URL = "https://discord.com/api/webhooks/1471129979545977086/qR3Y6Z054rLxDffdqgoB6oQWuTZWmn6s0AZ5rkpGFIF49gp-VwSG9rQWQutqh333iEie"

# X(Twitter)用の検索キーワード（ここを調整してください）
X_KEYWORDS = ["フィット 売り", "フィット RS"]

SITES_CONFIG = [
    {
        "name": "カーセンサー",
        "url": "https://www.carsensor.net/usedcar/search.php?STID=CS210610&SORT=19&CARC=HO_S028&PMAX=500000&SLST=MT",
        "history": "history_carsensor.txt",
        "func": get_carsensor_items
    },
    {
        "name": "グーネット",
        "url": "https://www.goo-net.com/php/search/summary.php?car_cd=10201029&maker_cd=1020&pref_c=01%2C02%2C03%2C04%2C05%2C06%2C07%2C08%2C09%2C10%2C11%2C12%2C13%2C14%2C15%2C16%2C17%2C18%2C19%2C20%2C21%2C22%2C23%2C24%2C25%2C26%2C27%2C28%2C29%2C30%2C31%2C32%2C33%2C34%2C35%2C36%2C37%2C38%2C39%2C40%2C41%2C42%2C43%2C44%2C45%2C46%2C47&price2=60&car_price=1&total_payment=1&mission=MT&baitai=goo&search_type=car_search&current=0&page=1&sort_value=desc&sort_flag=update_date_sort&disp_mode=detail_list&door_cd_flg=1&limit=50&car_list=10201029&integration_car_cd=10201029%7C&new_car_cds_list=10201029&search_flg=1&fancy_box=0&model_grade_name=%5B%5D&templates=0&area_nap_flg=1&custom_flg=0",
        "history": "history_goonet.txt",
        "func": get_goonet_items
    },
    {
        "name": "ヤフオク",
        "url": "https://auctions.yahoo.co.jp/category/list/26360/?select=22&auccat=26360&b=1&n=50&mode=1&brand_id=8185&spec=C_4%3A91%2C917%2C5379&slider=",
        "history": "history_yahoo.txt",
        "func": get_yahoo_items
    },
    {
        "name": "ジモティー",
        "url": "https://jmty.jp/all/car-hon/g-2346?model_year%5Bmin%5D=&model_year%5Bmax%5D=&mileage%5Bmin%5D=&mileage%5Bmax%5D=&min=&max=600000&commit=%E6%A4%9C%E7%B4%A2",
        "history": "history_jmty.txt",
        "func": get_jmty_items
    },
    {
        "name": "メルカリ",
        "url": "https://jp.mercari.com/search?keyword=%E3%83%95%E3%82%A3%E3%83%83%E3%83%88&category_id=10865&sort=created_time&order=desc",
        "history": "history_mercari.txt",
        "func": get_mercari_items
    }
]

# --- X(Twitter/Nitter) 専用の取得関数 ---
def check_x_with_playwright(page):
    print(f"[X(Twitter)] チェック開始...")
    history_file = "history_x.txt"
    instances = ["https://nitter.poast.org", "https://nitter.privacydev.net", "https://nitter.perennialte.ch"]
    
    # 履歴読み込み
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            old_ids = set(line.strip() for line in f if line.strip())
    else:
        old_ids = set()

    all_new_x_items = []

    for kw in X_KEYWORDS:
        success = False
        for base_url in instances:
            search_url = f"{base_url}/search?f=tweets&q={urllib.parse.quote(kw)}"
            try:
                page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_selector(".timeline-item", timeout=7000)
                
                tweets = page.query_selector_all(".timeline-item")
                for tweet in tweets:
                    link_el = tweet.query_selector(".tweet-link")
                    if not link_el: continue
                    
                    item_id = link_el.get_attribute("href").split("/")[-1].split("#")[0]
                    
                    if item_id not in old_ids:
                        content_el = tweet.query_selector(".tweet-content")
                        title = content_el.inner_text() if content_el else "本文なし"
                        user_el = tweet.query_selector(".username")
                        username = user_el.inner_text() if user_el else "unknown"
                        
                        all_new_x_items.append({
                            "id": item_id,
                            "title": f"[{username}] {title[:60]}",
                            "price": "要確認(X)",
                            "url": f"https://x.com{link_el.get_attribute('href').split('#')[0]}"
                        })
                success = True
                break # 1つのインスタンスで成功したら次のキーワードへ
            except Exception:
                continue
        time.sleep(2)

    # 通知と履歴保存
    if all_new_x_items:
        print(f" -> ✨ Xで {len(all_new_x_items)}件の新着を発見！")
        for item in all_new_x_items:
            message = (
                f"🐦 【X(Twitter) 新着】\n"
                f"内容: {item['title']}\n"
                f"価格: {item['price']}\n"
                f"URL: {item['url']}"
            )
            send_discord_message(WEBHOOK_URL, message)
            with open(history_file, "a") as f:
                f.write(item["id"] + "\n")
            old_ids.add(item["id"])
    else:
        print(f" -> 新着なし")

# --- 既存サイトのチェック用 ---
def check_site(site):
    print(f"[{site['name']}] チェック開始...")
    if os.path.exists(site["history"]):
        with open(site["history"], "r") as f:
            old_ids = set(line.strip() for line in f if line.strip())
    else:
        old_ids = set()

    current_items = site["func"](site["url"])
    new_items = [item for item in current_items if item["id"] not in old_ids]

    if new_items:
        print(f" -> ✨ {len(new_items)}件の新着を発見！")
        for item in new_items:
            message = (
                f"🚗 【{site['name']} 新着】\n"
                f"車種: {item['title']}\n"
                f"価格: {item['price']}\n"
                f"URL: {item['url']}"
            )
            send_discord_message(WEBHOOK_URL, message)
            with open(site["history"], "a") as f:
                f.write(item["id"] + "\n")
    else:
        print(f" -> 新着なし")

def main():
    print("=== 車両監視システム 起動 ===")
    
    # 1. 既存のフリマ・中古車サイトをチェック
    for site in SITES_CONFIG:
        try:
            check_site(site)
        except Exception as e:
            print(f"❌ {site['name']} で予期せぬエラー: {e}")

    # 2. X(Twitter)をチェック (Playwright使用)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        try:
            check_x_with_playwright(page)
        except Exception as e:
            print(f"❌ X(Twitter) で予期せぬエラー: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()
    print(f"\n全工程完了 処理時間: {end - start:.2f}秒")
import os
import time
import logging
from typing import List, Dict

# 自作モジュールのインポート
from common_notifier import send_discord_notification
from carsensor_monitor import fetch_listings as fetch_carsensor
from goonet_monitor import fetch_listings as fetch_goonet
from yahoo_monitor import fetch_listings as fetch_yahoo
from mercari_monitor import fetch_listings as fetch_mercari
from jmty_monitor import fetch_listings as fetch_jmty
from x_monitor import fetch_listings as fetch_x

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Webhook URLは環境変数から取得
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

SITES_CONFIG = [
    {
        "name": "カーセンサー",
        "url": "https://www.carsensor.net/usedcar/search.php?STID=CS210610&SORT=19&CARC=HO_S028&PMAX=500000&SLST=MT",
        "history": "history_carsensor.txt",
        "fetcher": fetch_carsensor
    },
    {
        "name": "グーネット",
        "url": "https://www.goo-net.com/php/search/summary.php?car_cd=10201029&maker_cd=1020&pref_c=01%2C02%2C03%2C04%2C05%2C06%2C07%2C08%2C09%2C10%2C11%2C12%2C13%2C14%2C15%2C16%2C17%2C18%2C19%2C20%2C21%2C22%2C23%2C24%2C25%2C26%2C27%2C28%2C29%2C30%2C31%2C32%2C33%2C34%2C35%2C36%2C37%2C38%2C39%2C40%2C41%2C42%2C43%2C44%2C45%2C46%2C47&price2=60&car_price=1&total_payment=1&mission=MT&baitai=goo&search_type=car_search&current=0&page=1&sort_value=desc&sort_flag=update_date_sort&disp_mode=detail_list&door_cd_flg=1&limit=50&car_list=10201029&integration_car_cd=10201029%7C&new_car_cds_list=10201029&search_flg=1&fancy_box=0&model_grade_name=%5B%5D&templates=0&area_nap_flg=1&custom_flg=0",
        "history": "history_goonet.txt",
        "fetcher": fetch_goonet
    },
    {
        "name": "ヤフオク",
        "url": "https://auctions.yahoo.co.jp/category/list/26360/?auccat=26360&spec=C_4%3A91%2C917%2C5379&brand_id=8185&price_type=currentprice&min=&max=600000&ei=UTF-8&oq=&tab_ex=commerce&select=22&mode=1&fr=auc_car_adv",
        "history": "history_yahoo.txt",
        "fetcher": fetch_yahoo
    },
    {
        "name": "ジモティー",
        "url": "https://jmty.jp/all/car-hon/g-2346?model_year%5Bmin%5D=&model_year%5Bmax%5D=&mileage%5Bmin%5D=&mileage%5Bmax%5D=&min=&max=600000&commit=%E6%A4%9C%E7%B4%A2",
        "history": "history_jmty.txt",
        "fetcher": fetch_jmty
    },
    {
        "name": "メルカリ",
        "url": "https://jp.mercari.com/search?keyword=%E3%83%95%E3%82%A3%E3%83%83%E3%83%88&category_id=10865&sort=created_time&order=desc",
        "history": "history_mercari.txt",
        "fetcher": fetch_mercari
    },
    {
        "name": "X(Twitter)",
        "url": None,
        "history": "history_x.txt",
        "fetcher": fetch_x,
        "search_keywords": ["フィット 売り", "フィット RS"]
    },

]

def load_history(filepath: str) -> set:
    """履歴ファイルを読み込み、IDのセットを返します。"""
    if not os.path.exists(filepath):
        return set()
    with open(filepath, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def save_history(filepath: str, item_id: str):
    """新しいIDを履歴ファイルに追記します。"""
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{item_id}\n")

def process_site(site: Dict):
    """各サイトのチェック、新着判定、通知を行います。"""
    logger.info(f"--- {site['name']} チェック開始 ---")
    
    old_ids = load_history(site["history"])
    try:
        current_items = site["fetcher"](site["url"] if site["url"] else site.get("search_keywords", None))
    except Exception as e:
        logger.error(f"{site['name']} の取得中にエラーが発生しました: {e}")
        return

    new_items = [item for item in current_items if item["id"] not in old_ids]

    if not new_items:
        logger.info(f"{site['name']}: 新着なし")
        return

    logger.info(f"{site['name']}: ✨ {len(new_items)}件の新着を発見！")
    
    for item in new_items:
        message = (
            f"🔔 【{site['name']} 新着】\n"
            f"🚗 タイトル: {item['title']}\n"
            f"💰 価格: {item['price']}\n"
            f"URL: {item['url']}"
        )
        
        # 通知送信
        if send_discord_notification(message, WEBHOOK_URL):
            save_history(site["history"], item["id"]) # 送信に成功した時だけ履歴に保存する
            time.sleep(1)  # Discordのレート制限対策

def main():
    logger.info("=== 車両監視システム 起動 ===")
    
    for site in SITES_CONFIG:
        process_site(site)
        time.sleep(3) # サイト間アクセスにインターバルを設ける

if __name__ == "__main__":
    start_time = time.time()
    main()
    duration = time.time() - start_time
    logger.info(f"=== 全工程完了 (処理時間: {duration:.2f}秒) ===")
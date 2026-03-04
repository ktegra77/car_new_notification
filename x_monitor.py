import logging
import urllib.parse
import time
from typing import List, Dict, Set
from playwright.sync_api import sync_playwright
import random

# ログ設定
logger = logging.getLogger(__name__)

# 定数
NITTER_INSTANCES = ["https://nitter.poast.org","https://nitter.perennialte.ch","https://nitter.net"]
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def fetch_listings(keywords: List[str] = None) -> List[Dict[str, str]]:
    """
    X(Twitter)から複数のキーワードで投稿を検索し、結果を統合して返します。
    """
    if keywords is None:
        logger.error("検索キーワードが空です。処理を中断します。")
        return []
    combined_results: List[Dict[str, str]] = []
    seen_ids: Set[str] = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT, viewport={'width': 1280, 'height': 800})

        for keyword in keywords:
            logger.debug(f"X検索実行中: '{keyword}'")
            results = _fetch_from_nitter(context, keyword)
            
            for item in results:
                if item["id"] not in seen_ids:
                    combined_results.append(item)
                    seen_ids.add(item["id"])
            
            # 連続アクセスによるブロック回避
            time.sleep(random.uniform(2, 5))

        browser.close()
    
    return combined_results

def _fetch_from_nitter(context, keyword: str) -> List[Dict[str, str]]:
    """
    Nitterのインスタンスを巡回して特定のキーワードを検索します（内部用関数）。
    """
    items = []
    encoded_kw = urllib.parse.quote(keyword)

    for base_url in NITTER_INSTANCES:
        page = context.new_page()
        search_url = f"{base_url}/search?f=tweets&q={encoded_kw}"
        item_id = "ID不明"

        try:
            # ページ遷移
            page.goto(search_url, wait_until="domcontentloaded", timeout=10000)

            try:
                # 投稿が表示されるまで待機※投稿がない場合はタイムアウトする
                page.wait_for_selector(".timeline-item", timeout=5000)
            except:
                logger.info(f"キーワード '{keyword}' に対する投稿が見つかりませんでした（{base_url}）")
                continue
            
            tweet_elements = page.query_selector_all(".timeline-item")
            
            for tweet in tweet_elements:
                link_el = tweet.query_selector(".tweet-link")
                if not link_el:
                    logger.debug("ツイートリンクが見つからない要素をスキップしました（広告等の可能性があります）")
                    continue
                
                relative_url = link_el.get_attribute("href") or ""
                item_id = relative_url.split("/")[-1].split("#")[0] 

                content_el = tweet.query_selector(".tweet-content")
                body_text = content_el.inner_text() if content_el else "本文なし"
                
                user_el = tweet.query_selector(".username")
                username = user_el.inner_text() if user_el else "ユーザー名不明"
                
                tweet_id = relative_url.split("/")[-1].split("#")[0]
                items.append({
                    "id": item_id,
                    "title": f"[{username}] {body_text[:50]}...",
                    "price": "価格情報要確認(X)",
                    "url": f"https://twitter.com/i/web/status/{tweet_id}"
                })
            
            if items:
                break # 1つのインスタンスで取れたらそのキーワードは終了

        except Exception as e:
            logger.warning(f"ID:{item_id} X解析中にエラーが発生しました（スキップします）: {e}")
            continue # 失敗したら次のインスタンスへ

        finally:
            page.close()

    return items

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    search_keywords = ["フィット 売り", "フィット RS"]
    results = fetch_listings(search_keywords)

    print(f"取得件数: {len(results)}件")
    for i, item in enumerate(results, 1):
        print(f"{i}件目: {item['title']} -> {item['url']}")
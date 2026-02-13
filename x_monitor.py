import time
from playwright.sync_api import sync_playwright
import urllib.parse

def get_x_items_via_nitter_playwright(keyword):
    instances = [
        "https://nitter.poast.org",
        "https://nitter.privacydev.net",
        "https://nitter.perennialte.ch"
    ]
    
    items = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        
        for base_url in instances:
            page = context.new_page()
            search_url = f"{base_url}/search?f=tweets&q={urllib.parse.quote(keyword)}"
            
            try:
                print(f"   - {base_url} にアクセス中...")
                page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_selector(".timeline-item", timeout=7000)
                
                tweets = page.query_selector_all(".timeline-item")
                
                # --- ここから修正：全ツイートを回るように ---
                for tweet in tweets:   
                    link_el = tweet.query_selector(".tweet-link")
                    if not link_el: 
                        continue
                    
                    relative_url = link_el.get_attribute("href")
                    item_id = relative_url.split("/")[-1].split("#")[0]
                    
                    content_el = tweet.query_selector(".tweet-content")
                    title = content_el.inner_text() if content_el else "本文なし"
                    
                    user_el = tweet.query_selector(".username")
                    username = user_el.inner_text() if user_el else "unknown"
                    
                    items.append({
                        "id": item_id,
                        "title": f"[{username}] {title[:50]}...",
                        "price": "要確認(X)",
                        "url": f"https://x.com{relative_url.split('#')[0]}"
                    })
                
                # --- 修正：全ツイート回収し終わった後に中身があれば成功として終了 ---
                if items:
                    page.close()
                    break 
                    
            except Exception as e:
                print(f"   - {base_url} でエラーまたは投稿なし。次を試します...")
                page.close()
                continue
        
        browser.close()
    return items

# --- 以下、get_x_items と if __name__ はそのまま ---

def get_x_items(dummy_url_placeholder):
    keywords = ["フィット 売り", "フィット RS"]
    combined_results = []
    seen_ids = set()

    for kw in keywords:
        print(f" [X] ブラウザ自動操作で '{kw}' をチェック中...")
        results = get_x_items_via_nitter_playwright(kw)
        
        for item in results:
            if item["id"] not in seen_ids:
                combined_results.append(item)
                seen_ids.add(item["id"])
        
        time.sleep(2)
        
    return combined_results

if __name__ == "__main__":
    print("=== X(Twitter) Playwright監視テスト(インデント修正版) ===")
    results = get_x_items("")
    if results:
        print(f"\n✨ {len(results)} 件の投稿を発見しました！")
        for i, item in enumerate(results, 1):
            print(f"{i}: {item['title']}")
            print(f"   URL: {item['url']}")
    else:
        print("\n投稿が見つかりませんでした。")
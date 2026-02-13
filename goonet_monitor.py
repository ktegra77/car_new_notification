# import requests
# from bs4 import BeautifulSoup
# import re

# def get_goonet_items(url):
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#     }
    
#     try:
#         res = requests.get(url, headers=headers, timeout=15)
#         res.raise_for_status()
#         # グーネットはShift_JISの場合があるため、自動判定をセット
#         res.encoding = res.apparent_encoding
        
#         soup = BeautifulSoup(res.text, "html.parser")
        
#         items = []
#         # 車両1台ごとのブロックを取得
#         cassettes = soup.find_all("div", class_="importedCar")
#         print(f"グーネットで見つかった車両数: {len(cassettes)}")
        
#         for cassette in cassettes:
#             # --- 1. IDの取得 ---
#             # aタグのhrefからID（15桁程度の数字）を抽出
#             link_tag = cassette.find("a", href=True)
#             print(f"link_tag: {link_tag}")
#             exit()
#             if not link_tag: continue
#             href = link_tag["href"]
#             # 例: /usedcar/spread/goo/13/700055088730240107001.html
#             match = re.search(r'(\d{15,})', href)
#             item_id = match.group(1) if match else href.split("/")[-1]

#             # --- 2. タイトルの取得 ---
#             # メーカー名、車種名、グレード名を結合
#             title_tag = cassette.find("h3", class_="heading")
#             title = title_tag.get_text(strip=True).replace("ホンダフィット", "フィット ") if title_tag else "車種不明"

#             # --- 3. 価格の取得 ---
#             # 支払総額を優先的に探す
#             total_price_tag = cassette.find("div", class_="hontai-price")
#             if total_price_tag:
#                 price_val = total_price_tag.find("em", class_="num-red")
#                 price = f"総額{price_val.get_text(strip=True)}万円" if price_val else "価格不明"
#             else:
#                 # 総額がない場合は車両価格
#                 car_price_tag = cassette.find("div", class_="hontai-price")
#                 price = car_price_tag.get_text(strip=True) if car_price_tag else "価格不明"

#             items.append({
#                 "id": item_id,
#                 "title": title,
#                 "price": price,
#                 "url": "https://www.goo-net.com" + href if href.startswith("/") else href
#             })
            
#         return items

#     except Exception as e:
#         print(f"グーネットでエラー発生: {e}")
#         return []

# if __name__ == "__main__":
#     # 先ほど取得した長いURL
#     TARGET_URL = "https://www.goo-net.com/php/search/summary.php?car_cd=10201029&maker_cd=1020&pref_c=01%2C02%2C03%2C04%2C05%2C06%2C07%2C08%2C09%2C10%2C11%2C12%2C13%2C14%2C15%2C16%2C17%2C18%2C19%2C20%2C21%2C22%2C23%2C24%2C25%2C26%2C27%2C28%2C29%2C30%2C31%2C32%2C33%2C34%2C35%2C36%2C37%2C38%2C39%2C40%2C41%2C42%2C43%2C44%2C45%2C46%2C47&price2=60&car_price=1&total_payment=1&mission=MT&baitai=goo&search_type=car_search&current=0&page=1&sort_value=desc&sort_flag=update_date_sort&disp_mode=detail_list&door_cd_flg=1&limit=50&car_list=10201029&integration_car_cd=10201029%7C&new_car_cds_list=10201029&search_flg=1&fancy_box=0&model_grade_name=%5B%5D&templates=0&area_nap_flg=1&custom_flg=0" 
#     results = get_goonet_items(TARGET_URL)
#     for i, item in enumerate(results, 1):
#         print(f"{i}台目 ID: {item['id']} | {item['title']} | 価格: {item['price']}")


import requests
from bs4 import BeautifulSoup
import re

def get_goonet_items(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        res.encoding = res.apparent_encoding # 文字化け対策
        
        soup = BeautifulSoup(res.text, "html.parser")
        items = []

        # カセットを探す（クラス名は search-cassette や importedCar など複数あるため部分一致で）
        cassettes = soup.find_all("div", class_=lambda x: x and ("search-cassette" in x or "importedCar" in x))
        
        for cassette in cassettes:
            # --- 1. IDとURLの取得 ---
            # 「詳細を見る」ボタン、またはタイトルリンクを探す
            # aタグの中で、hrefに "spread/goo" が含まれるものが詳細ページ
            detail_link = cassette.find("a", href=lambda x: x and "spread/goo" in x)
            
            if not detail_link:
                # 予備：onclick属性の中に21桁のIDが隠れていることが多い
                onclick_tag = cassette.find(lambda tag: tag.has_attr('onclick') and 'changeCompareBtn' in tag['onclick'])
                if onclick_tag:
                    # onclick="changeCompareBtn('700050804230260209002', ..." から抽出
                    match = re.search(r"'(\d{15,})'", onclick_tag['onclick'])
                    item_id = match.group(1) if match else None
                else:
                    continue
            else:
                href = detail_link["href"]
                # URLからID（21桁前後の数字）を抽出
                match = re.search(r'(\d{15,})', href)
                item_id = match.group(1) if match else href.split("/")[-1].replace(".html", "")
                full_url = "https://www.goo-net.com" + href if href.startswith("/") else href

            if not item_id: continue

            # --- 2. タイトルの取得 ---
            # h2タグ、または class="heading" を探す
            title_tag = cassette.find(["h2", "div"], class_=lambda x: x and "heading" in x)
            title = title_tag.get_text(strip=True) if title_tag else "車種不明"

            # --- 3. 価格の取得 ---
            # 支払総額の数値が入っている <p class="num num-red"> を探す
            total_price_p = cassette.find("p", class_=lambda x: x and "num-red" in x)
            
            if total_price_p:
                # pタグの中にある em タグ（数字部分）を取得
                price_num = total_price_p.find("em")
                if price_num:
                    price = f"総額{price_num.get_text(strip=True)}万円"
                else:
                    # emが見つからない場合はpタグのテキストから取得
                    price = f"総額{total_price_p.get_text(strip=True)}"
            else:
                # 総額がない場合は車両本体価格を探す
                # HTML構造から p class="num"（num-redではない方）を探す
                car_price_p = cassette.find("p", class_="num")
                if car_price_p:
                    price = car_price_p.get_text(strip=True)
                else:
                    price = "価格不明"
            items.append({
                "id": item_id,
                "title": title,
                "price": price,
                "url": full_url if 'full_url' in locals() else f"https://www.goo-net.com/usedcar/spread/goo/xxxx/{item_id}.html"
            })
            
        return items

    except Exception as e:
        print(f"グーネットでエラー発生: {e}")
        return []

if __name__ == "__main__":
    # あなたの長いURLをここに
    TARGET_URL = "https://www.goo-net.com/php/search/summary.php?car_cd=10201029&maker_cd=1020&pref_c=01%2C02%2C03%2C04%2C05%2C06%2C07%2C08%2C09%2C10%2C11%2C12%2C13%2C14%2C15%2C16%2C17%2C18%2C19%2C20%2C21%2C22%2C23%2C24%2C25%2C26%2C27%2C28%2C29%2C30%2C31%2C32%2C33%2C34%2C35%2C36%2C37%2C38%2C39%2C40%2C41%2C42%2C43%2C44%2C45%2C46%2C47&price2=60&car_price=1&total_payment=1&mission=MT&baitai=goo&search_type=car_search&current=0&page=1&sort_value=desc&sort_flag=update_date_sort&disp_mode=detail_list&door_cd_flg=1&limit=50&car_list=10201029&integration_car_cd=10201029%7C&new_car_cds_list=10201029&search_flg=1&fancy_box=0&model_grade_name=%5B%5D&templates=0&area_nap_flg=1&custom_flg=0"
    results = get_goonet_items(TARGET_URL)
    for i, item in enumerate(results, 1):
        print(f"{i}台目 ID: {item['id']} | {item['title']} | 価格: {item['price']}")
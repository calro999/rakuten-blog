import os
import sys
import json
import random
import re
import time
import base64
import tempfile
import urllib.request
import urllib.parse
import urllib.error
import requests
from playwright.sync_api import sync_playwright
from article_generator import ArticleGenerator
from rakuten_blog_api import RakutenBlogAPI

CACHE_FILE = "posted_cache.txt"

# 雑貨・インテリア特化のキーワードリスト
INTERIOR_KEYWORDS = [
    "北欧インテリア",
    "収納ボックス",
    "アロマディフューザー",
    "クッションカバー",
    "間接照明LED",
    "観葉植物",
    "木製食器",
    "壁掛け時計",
    "フラワーベース",
    "スリッパ",
    "珪藻土バスマット",
    "北欧風ラグマット",
    "おしゃれなゴミ箱",
    "キッチンツール"
]

# 関連ジャンルID
# 100804: インテリア・寝具・収納
# 215787: 日用品雑貨・文房具・手芸
GENRE_IDS = ["100804", "215787"]

def load_cache() -> set:
    if not os.path.exists(CACHE_FILE):
        return set()
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def save_cache(item_number: str):
    with open(CACHE_FILE, "a", encoding="utf-8") as f:
        f.write(f"{item_number}\n")

def generate_keyword() -> str:
    """雑貨・インテリアのリストからランダムにキーワードを取得する。"""
    return random.choice(INTERIOR_KEYWORDS)

def fetch_rakuten_items(app_id: str, access_key: str, affiliate_id: str, keyword: str) -> list:
    """楽天市場の商品検索APIからインテリア・雑貨商品を取得。"""
    if not app_id or app_id.startswith("DUMMY"):
        print("Rakuten App ID not set. Using mock data for local dry-run.")
        return get_mock_items(keyword)

    print(f"Searching with Keyword: {keyword}")

    base_url = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260401"
    params = {
        "applicationId": app_id,
        "affiliateId": affiliate_id,
        "keyword": keyword,
        "sort": "standard",
        "hits": 10,
        "format": "json"
    }

    if access_key:
        params["accessKey"] = access_key

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
            items = []
            for entry in data.get("Items", []):
                item_data = entry.get("Item", {})
                if item_data:
                    image_url = ""
                    medium_images = item_data.get("mediumImageUrls", [])
                    if medium_images and isinstance(medium_images, list) and len(medium_images) > 0:
                        image_url = medium_images[0].get("imageUrl", "")
                    
                    items.append({
                        "title": item_data.get("itemName"),
                        "itemCaption": item_data.get("itemCaption", ""),
                        "affiliateUrl": item_data.get("affiliateUrl"),
                        "itemCode": item_data.get("itemCode"),
                        "price": f"{item_data.get('itemPrice', '')}円",
                        "imageUrl": image_url
                    })
            return items
    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode("utf-8")
            print(f"Failed to fetch from Rakuten Ichiba API (HTTPError): {e}")
            print(f"Error Response Body: {error_body}")
        except Exception:
            print(f"Failed to fetch from Rakuten Ichiba API (HTTPError): {e}")
        return []
    except Exception as e:
        print(f"Failed to fetch from Rakuten Ichiba API: {e}")
        return []

def get_mock_items(keyword: str) -> list:
    """ドライラン用のモックデータを生成。"""
    return [
        {
            "title": f"【北欧風】{keyword} ウッド調ナチュラルデザイン",
            "itemCaption": f"毎日の暮らしを豊かにするモダンな『{keyword}』です。温かみのある木目調デザインで、リビングや寝室に置くだけでQOLが向上し、上質な空間を演出してくれます。使いやすさにこだわり、シンプルでありながら飽きのこない美しいフォルムを実現しました。",
            "affiliateUrl": "https://r18.afl.rakuten.co.jp/mock_interior",
            "itemCode": "mock_interior_001",
            "price": "4,980円",
            "imageUrl": "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&auto=format&fit=crop&q=80"
        }
    ]

def generate_room_comment_with_llm(item) -> str:
    title = item.get("title")
    price = item.get("price")
    
    prompt = f"""以下の楽天のインテリア・雑貨商品情報を基にして、楽天ROOM用の紹介コメント（400文字以内）を生成してください。
【商品名】: {title}
【価格】: {price}

以下の要件を厳格に遵守してください：
1. 文字数は400文字以内（厳守。超えると投稿エラーになります）。
2. 親しみやすい話し言葉で、絵文字を5〜8個使用してください。
3. ハッシュタグを3〜5個（インテリア、雑貨、QOL向上など関連するもの）含め、末尾に「#楽天市場」を必ず含めること。
4. URLや疑似リンク、プレースホルダーは絶対に含めないでください。
5. 出力は紹介コメントのテキストのみとし、前置きやMarkdownの装飾コードブロック等は一切含めないでください。
"""

    system_message = "あなたは楽天ROOMでフォロワー急増中の北欧雑貨専門インフルエンサーです。暮らしを豊かにし、QOLをワンランクアップさせるアイテムの魅力を日本語のみで発信してください。"

    # 1. GitHub Models API
    github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if github_token:
        try:
            print("Attempting to generate ROOM comment with GitHub Models API...")
            headers = {
                "Authorization": f"Bearer {github_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            response = requests.post("https://models.inference.ai.azure.com/chat/completions", headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"GitHub Models API ROOM generation failed: {e}")

    # 2. Pollinations AI
    try:
        print("Attempting to generate ROOM comment with Pollinations AI...")
        response = requests.post(
            "https://text.pollinations.ai/",
            json={
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "model": "openai-fast"
            },
            timeout=45
        )
        if response.status_code == 200 and len(response.text.strip()) > 30:
            return response.text.strip()
    except Exception as e:
        print(f"Pollinations AI ROOM failed: {e}")

    # Fallback
    clean_title = title.replace("【", "").replace("】", "")[:50]
    return f"✨毎日の暮らしをハッピーにするお気に入りインテリア雑貨✨\nシンプルでとってもおしゃれなデザインが魅力のアイテムです🎀\n置くだけでQOLも雰囲気もアップしてお家時間がもっと楽しくなりますよ🥰\n\n{clean_title}...\n\n#インテリア #北欧インテリア #おしゃれ雑貨 #楽天市場"

def post_to_rakuten_room(item_code: str, comment: str, session_b64: str) -> bool:
    """楽天ROOMへの自動投稿 (コレ！)"""
    if not session_b64:
        print("No session b64 provided for Rakuten Room. Skipping.")
        return False
        
    session_file_path = None
    try:
        decoded_str = base64.b64decode(session_b64).decode('utf-8')
        json.loads(decoded_str)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".json") as temp_file:
            temp_file.write(decoded_str)
            session_file_path = temp_file.name
    except Exception as e:
        print(f"Session decode for Room failed: {e}")
        return False

    print(f"Posting to Rakuten Room (Item: {item_code}) using Playwright...")
    success = False
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                storage_state=session_file_path,
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            warp_url = f"https://room.rakuten.co.jp/mix?itemcode={item_code}&scid=we_room_upc60"
            page.goto(warp_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(4)

            if "login.rakuten.co.jp" in page.url or "login" in page.url.lower():
                print("Error: Session expired or invalid for Rakuten Room.")
                return False

            page_html = page.content()
            if any(term in page_html for term in ["すでにコレ", "すでに登録されています", "すでに登録"]):
                print("This item has already been posted to Rakuten Room. Skipping.")
                return True

            comment_area = page.locator('textarea[placeholder*="コメント"], textarea[placeholder*="オススメ"], textarea[placeholder*="魅力"], textarea').first
            comment_area.wait_for(state="visible", timeout=15000)
            comment_area.fill(comment)
            time.sleep(1)

            submit_btn = page.locator('button:has-text("投稿"), button:has-text("完了"), button:has-text("コレ！"), button[class*="submit"]').first
            submit_btn.scroll_into_view_if_needed()
            time.sleep(1)
            submit_btn.click(force=True)
            print("Clicked Rakuten Room submit button.")
            
            time.sleep(5)
            print("Successfully posted to Rakuten Room!")
            success = True
    except Exception as e:
        print(f"Error posting to Rakuten Room: {e}")
    finally:
        if session_file_path and os.path.exists(session_file_path):
            os.remove(session_file_path)
    return success

def main():
    print("=== Starting Rakuten Interior/Goods Blog & Room Poster ===")
    
    # ローカルの .env ファイルがあれば読み込む
    if os.path.exists(".env"):
        print("Loading environment variables from .env file...")
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")
    
    rakuten_app_id = os.environ.get("RAKUTEN_APP_ID", "DUMMY_APP_ID")
    rakuten_access_key = os.environ.get("RAKUTEN_ACCESS_KEY", "")
    rakuten_affiliate_id = os.environ.get("RAKUTEN_AFFILIATE_ID", "DUMMY_AFFILIATE_ID")
    
    rakuten_blog_id = os.environ.get("RAKUTEN_BLOG_ID", "")
    
    # 楽天ブログ・ROOM共有のセッション環境変数を取得
    session_b64 = (
        os.environ.get("RAKUTEN_BLOG_SESSION_B64") or 
        os.environ.get("ROOM_SESSION_B64") or 
        os.environ.get("HATENA_SESSION_B64")
    )

    # 1. 検索キーワード選定
    keyword = generate_keyword()
    print(f"Selected Keyword: {keyword}")

    # 2. キャッシュの読み込み
    posted_cache = load_cache()
    print(f"Loaded {len(posted_cache)} posted items from cache.")

    # 3. 楽天市場から商品を検索 (最大3回リトライ)
    items = []
    for attempt in range(3):
        if attempt > 0:
            time.sleep(2)
        items = fetch_rakuten_items(rakuten_app_id, rakuten_access_key, rakuten_affiliate_id, keyword)
        if items:
            break
        print(f"Warning: No items found for '{keyword}'. Retrying with another keyword...")
        keyword = generate_keyword()

    if not items:
        print("Error: No items found from Rakuten API after retries.")
        sys.exit(1)

    # 4. 未投稿の商品をフィルタリング
    target_item = None
    for item in items:
        if item["itemCode"] not in posted_cache:
            target_item = item
            break

    if not target_item:
        print("All fetched items are already posted. Finished.")
        sys.exit(0)

    print(f"Target Item: {target_item['title']} (Code: {target_item['itemCode']})")

    # アフィリエイトIDをURL内に強制適用して確実にする
    affiliate_url = target_item["affiliateUrl"]
    if rakuten_affiliate_id and not rakuten_affiliate_id.startswith("DUMMY"):
        # hb.afl.rakuten.co.jp/hgc/xxxx/ の xxxx 部分をご自身のIDに差し替える
        prefix = "hb.afl.rakuten.co.jp/hgc/"
        if prefix in affiliate_url:
            parts = affiliate_url.split(prefix)
            subparts = parts[1].split("/", 1)
            if len(subparts) == 2:
                affiliate_url = parts[0] + prefix + rakuten_affiliate_id + "/" + subparts[1]
                print(f"Surgically applied your Affiliate ID: {rakuten_affiliate_id}")

    # 5. LLMで紹介記事（HTML形式）を生成
    print("Generating Review Article...")
    article_gen = ArticleGenerator()
    article_gen.load_model()
    
    title_raw = target_item["title"]
    clean_title = re.sub(r'【[^】]+】|\[[^\]]+\]', '', title_raw).strip()
    
    generator_input_item = {
        "title": target_item["title"],
        "clean_title": clean_title,
        "price": target_item["price"],
        "caption": target_item["itemCaption"],
        "search_keyword": keyword
    }
    
    llm_section = article_gen.generate_review_article(generator_input_item)

    # APIの連続呼び出し（429エラー）を回避するため少し待機
    time.sleep(3)

    # 画像HTML、CTAアフィリエイトリンクボタンを追加して完成HTMLを作る
    product_image_url = target_item.get("imageUrl", "")
    if not product_image_url:
        product_image_url = "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&auto=format&fit=crop&q=80"

    img_html = f'<img src="{product_image_url}" alt="{clean_title}" style="max-width: 100%; height: auto; border-radius: 8px;">'
    
    cta_html = f'<p style="margin: 20px 0;"><a href="{affiliate_url}" target="_blank" rel="noopener noreferrer"><b>＼ 楽天市場で詳細をチェックする ／</b></a></p>'
    
    ad_tag = '<pointad pointad-id="div-plaza-point-ad" pointad-text="#ブロ活広告#" /><br /><br />'
    article_content = f"{img_html}\n{llm_section}\n{cta_html}\n{ad_tag}"
    
    # 記事タイトル（CTR重視の魅力的なタイトルを生成）
    print("Generating Blog Title...")
    blog_title = article_gen.generate_blog_title(generator_input_item)
    print(f"Generated Title: {blog_title}")

    # 6. 楽天ブログへ投稿
    print("Posting to Rakuten Blog...")
    blog_api = RakutenBlogAPI(blog_id=rakuten_blog_id, session_b64=session_b64)
    success = blog_api.post_entry(title=blog_title, html_content=article_content)

    if success:
        print("Successfully posted to Rakuten Blog!")
        save_cache(target_item["itemCode"])
    else:
        print("Failed to post entry to Rakuten Blog.")
        sys.exit(1)

    print("=== Auto Post Process Completed! ===")

if __name__ == "__main__":
    main()

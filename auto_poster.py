import os

# Force flush all prints for real-time logging in CI/GitHub Actions
import builtins
print = lambda *args, **kwargs: builtins.print(*args, flush=True, **kwargs)

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

# 1. 北欧インテリア・家具・雑貨キーワード (インテリア内の約70%)
NORDIC_INTERIOR_KEYWORDS = [
    # 家具・大型収納
    "北欧 木製 サイドテーブル", "北欧風 遮光カーテン", "北欧風 チェスト タンス",
    "ローテーブル 折りたたみ 北欧", "ハンガーラック スリム 木製", "スツール 木製 北欧",
    "座椅子 コンパクト 北欧", "キャスター付き ワゴン 北欧", "ウォールシェルフ 賃貸 北欧",
    "ウッドカーペット ナチュラル", "テレビ台 北欧 ローボード", "ダイニングチェア 北欧 木製",
    "ネストテーブル 北欧 木製", "マガジンラック 壁掛け 北欧", "シューズラック スリム 北欧",
    
    # 照明・時計
    "真鍮 ペンダントライト 北欧", "テーブルランプ 北欧 アンティーク", "LEDデスクライト 木目調",
    "間接照明 スタンド 北欧", "壁掛け時計 静音 北欧", "時計 デジタル 木目",
    "シーリングライト 北欧 木枠", "ブラケットライト 北欧 壁掛け", "ペンダントライト ガラス 北欧",
    
    # 玄関・リビング・生活雑貨
    "スリム 傘立て 北欧", "玄関マット 天然素材 北欧風", "キーフック 玄関 木製",
    "木製 ティッシュケース", "真鍮 アクセサリートレイ", "卓上 ミラー 木枠 北欧",
    "ジュエリーボックス 大容量", "アロマストーン 皿付き", "フェルト 収納バスケット",
    "珪藻土バスマット グレー", "ケーブルボックス 木目", "スマートゴミ箱 分別",
    "リードディフューザー 北欧風", "キャンドルホルダー ガラス 北欧", "ポスターフレーム 木製 B2",
    "北欧 アートパネル ウォールデコ", "ブランケット 北欧 大判", "クッションカバー 北欧 リネン",
    "陶器 フラワーベース 北欧", "木製 ウォールハンガー",
    
    # キッチン・ダイニング
    "ブレッドケース キッチン収納", "調味料ラック ステンレス", "珪藻土 コースター",
    "ウッドプレート 食器 北欧", "ガラス キャニスター", "セラミック コーヒーミル",
    "マグカップ 北欧 陶器", "カトラリーセット 北欧 木製", "キッチンマット 滑り止め 北欧"
]

# 2. 韓国インテリア・家具・雑貨キーワード (インテリア内の約30%)
KOREAN_INTERIOR_KEYWORDS = [
    "韓国インテリア サイドテーブル", "韓国風 ウェーブミラー", "韓国インテリア フラワーベース",
    "韓国風 マグカップ 陶器", "韓国インテリア アクリルシェルフ", "韓国風 卓上ライト",
    "韓国インテリア ファブリックポスター", "韓国風 丸型ラグ", "韓国インテリア キャンドル",
    "韓国風 壁掛け時計", "韓国インテリア ローテーブル", "韓国風 チューリップ 造花",
    "韓国インテリア ウッドトレイ", "韓国風 ビーンズミラー", "韓国インテリア スツール",
    "韓国風 ブランケット ひざ掛け", "韓国インテリア クッションチェアー", "韓国風 ディフューザー",
    "韓国インテリア ラック 透明", "韓国風 ジュエリーケース", "韓国風 レジンコースター",
    "韓国インテリア セラミックベース"
]

# 3. ふるさと納税＋スイーツ・お菓子特化キーワード (全体の約30%)
FURUSATO_SWEETS_KEYWORDS = [
    "ふるさと納税 バスクチーズケーキ", "ふるさと納税 濃厚ガトーショコラ",
    "ふるさと納税 抹茶バウムクーヘン", "ふるさと納税 高級プリン 詰め合わせ",
    "ふるさと納税 フィナンシェ ギフト", "ふるさと納税 マカロン セット",
    "ふるさと納税 とろける生チョコ", "ふるさと納税 和菓子 カステラ 老舗",
    "ふるさと納税 どら焼き 極上", "ふるさと納税 ロールケーキ 生クリーム",
    "ふるさと納税 アイス ジェラート 詰め合わせ", "ふるさと納税 シフォンケーキ",
    "ふるさと納税 フルーツタルト 冷凍", "ふるさと納税 アップルパイ 焼きたて",
    "ふるさと納税 ラスク ギフト チョコ", "ふるさと納税 フロランタン",
    "ふるさと納税 レーズンサンド 絶品", "ふるさと納税 本わらび餅",
    "ふるさと納税 クッキー缶 ギフト", "ふるさと納税 焼き菓子 詰め合わせ",
    "ふるさと納税 お菓子 個包装 ギフト", "ふるさと納税 スイーツ チョコ",
    "ふるさと納税 高級 和菓子 栗きんとん", "ふるさと納税 大福 詰め合わせ",
    "ふるさと納税 プレミアム チーズケーキ", "ふるさと納税 カヌレ セット",
    "ふるさと納税 パウンドケーキ ギフト"
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
    """
    全体の30%で「ふるさと納税スイーツ・お菓子」、
    残りの70%で「インテリア・家具雑貨（北欧70% : 韓国30%）」の比率でキーワードを選出する。
    """
    if random.random() < 0.30:
        # ふるさと納税スイーツ・お菓子 (30%)
        return random.choice(FURUSATO_SWEETS_KEYWORDS)
    else:
        # インテリア・家具雑貨 (70%)
        if random.random() < 0.70:
            # 北欧インテリア (インテリア中の70% = 全体の49%)
            return random.choice(NORDIC_INTERIOR_KEYWORDS)
        else:
            # 韓国インテリア (インテリア中の30% = 全体の21%)
            return random.choice(KOREAN_INTERIOR_KEYWORDS)

def fetch_rakuten_items(app_id: str, access_key: str, affiliate_id: str, keyword: str) -> list:
    """楽天市場の商品検索APIからインテリア・雑貨商品を取得。"""
    if not app_id or app_id.startswith("DUMMY"):
        raise ValueError("Error: RAKUTEN_APP_ID environment variable is not set. Please set a valid RAKUTEN_APP_ID in your environment or .env file.")

    print(f"Searching with Keyword: {keyword}")

    base_url = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260401"
    params = {
        "applicationId": app_id,
        "affiliateId": affiliate_id,
        "keyword": keyword,
        "sort": "standard",
        "hits": 30,
        "format": "json"
    }

    if access_key:
        params["accessKey"] = access_key

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
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
    mock_id = f"mock_{random.randint(100000, 999999)}"
    return [
        {
            "title": f"【北欧風】{keyword} ウッド調ナチュラルデザイン",
            "itemCaption": f"毎日の暮らしを豊かにするモダンな『{keyword}』です。温かみのある木目調デザインで、リビングや寝室に置くだけでQOLが向上し、上質な空間を演出してくれます。使いやすさにこだわり、シンプルでありながら飽きのこない美しいフォルムを実現しました。",
            "affiliateUrl": "https://r18.afl.rakuten.co.jp/mock_interior",
            "itemCode": mock_id,
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
3. ハッシュタグを3〜5個（お部屋作り、整理整頓、インテリア、雑貨など商品に直接関連するもの）含め、末尾に「#楽天市場」を必ず含めること。
4. URLや疑似リンク、プレースホルダーは絶対に含めないでください。
5. 出力は紹介コメントのテキストのみとし、前置きやMarkdownの装飾コードブロック等は一切含めないでください。
"""

    system_message = "あなたは楽天ROOMで大人気の『北欧・韓国インテリア＆家具・ご褒美スイーツ』専門インフルエンサーです。洗練されたお部屋作りや暮らしを素敵に彩るアイテム、至福のスイーツの魅力を親しみやすい日本語で発信してください。"

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
    return f"✨毎日の暮らしをハッピーにするお気に入りアイテム✨\nシンプルでとってもおしゃれなデザインが魅力です🎀\n置くだけでお部屋の雰囲気が素敵になり、おうち時間がもっと快適で楽しくなりますよ🥰\n\n{clean_title}...\n\n#北欧インテリア #韓国インテリア #おしゃれ家具 #楽天市場"

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

FORBIDDEN_TERMS = [
    "ランチョンマット", "クッションカバー", "サボテン", "多肉植物",
    "トイレットペーパー", "ティッシュペーパー", "みかん", "ミカン", "蜜柑"
]

def is_forbidden_item(title: str, caption: str = "") -> bool:
    """指定されたNG商品（ランチョンマット、クッションカバー、サボテン、トイレットペーパー、みかん等）を除外する。"""
    text = (title + " " + caption).lower()
    return any(term.lower() in text for term in FORBIDDEN_TERMS)

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

    # 3. 楽天市場から商品を検索し、未投稿かつNGでない商品を確実に探す（最大100回リトライで絶対止めない）
    target_item = None
    max_attempts = 100
    for attempt in range(max_attempts):
        if attempt > 0:
            time.sleep(1)
            keyword = generate_keyword()
        print(f"Attempt {attempt + 1}/{max_attempts}: Searching with keyword '{keyword}'...")
        items = fetch_rakuten_items(rakuten_app_id, rakuten_access_key, rakuten_affiliate_id, keyword)
        if items:
            for item in items:
                code = item["itemCode"]
                title = item.get("title", "")
                caption = item.get("itemCaption", "")
                
                # 重複チェック & NG商品チェック
                if code not in posted_cache and not is_forbidden_item(title, caption):
                    target_item = item
                    break
        if target_item:
            break
        print(f"No suitable unposted items found for '{keyword}'. Retrying with another keyword...")

    if not target_item:
        # 万が一見つからなかった場合の緊急フォールバック（ドライラン用モックではなく人気キーワード再試行）
        print("Warning: Standard search limit reached. Executing emergency fall-through keyword search...")
        fallback_kws = ["北欧 チェスト", "韓国インテリア サイドテーブル", "ふるさと納税 バスクチーズケーキ"]
        for fb_kw in fallback_kws:
            items = fetch_rakuten_items(rakuten_app_id, rakuten_access_key, rakuten_affiliate_id, fb_kw)
            for item in items:
                if item["itemCode"] not in posted_cache and not is_forbidden_item(item.get("title", "")):
                    target_item = item
                    break
            if target_item:
                break

    if not target_item:
        print("Error: Could not retrieve target item from API.")
        sys.exit(1)

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
    clean_title = article_gen.get_clean_product_name(title_raw, keyword)
    
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
    
    cta_html = article_gen.generate_dynamic_cta(
        clean_title=clean_title,
        search_keyword=keyword,
        caption=target_item.get("itemCaption", ""),
        affiliate_url=affiliate_url
    )
    
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
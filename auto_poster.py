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
RECENT_CATEGORIES_FILE = "recent_categories.json"
RECENT_KEYWORDS_FILE = "recent_keywords.json"
DAILY_POSTS_FILE = "daily_posts.json"
DAILY_MAX_PUBLIC_POSTS = 23

# 年末・冬の厳選7大カテゴリー（成約率CVR最大化＆完全比率配分）
# 1. 暖房家電・暖房器具（20%）: コタツ、ファンヒーター、石油ストーブ、パネルヒーター、電気毛布等
# 2. ブランケット・着る毛布・毛布（20%）: 着る毛布、極暖毛布、大判ブランケット、発熱マイクロファイバー等
# 3. 冬のご褒美スイーツ（20%）: 濃厚チョコケーキ、バスクチーズケーキ、極上プリン、シュトーレン等（フルーツ単体NG）
# 4. 名店・老舗のおせち（10%）: 割烹・名店・料亭監修おせち、ホテルおせち（重複時はスイーツへ自動振替）
# 5. 温まる入浴剤（10%）: 薬用重炭酸、温泉気分、発泡バスボム、天然クレイ等
# 6. 加湿器（10%）: ハイブリッド式、大容量超音波、スチーム式、卓上型等
# 7. 乾燥対策コスメ・ハンド・リップ（10%）: 高保湿ハンドクリーム、リップバーム、シアバター、セラミドクリーム等
EXPANDED_CATEGORIES = {
    # 1. 暖房器具・暖房家電（20%配分）
    "heating_appliances": [
        "セラミックファンヒーター 人感センサー 速暖", "デスク下 パネルヒーター 省エネ", "一人用 こたつ テーブル コンパクト",
        "フラットヒーター こたつ 正方形 北欧", "石油ストーブ レトロ 小型 キャンプ", "カーボンヒーター 首振り 省エネ 速暖",
        "電気ストーブ 省エネ 静音", "グラファイトヒーター 即暖 アラジン風", "オイルヒーター 省エネ タイマー 静音",
        "足元ヒーター デスク下 静音 タイマー", "電気ひざ掛け 洗える フランネル", "ホットカーペット 1.5畳 2畳 省エネ",
        "ガスファンヒーター 省エネ 速暖", "ファンヒーター ガード 安全", "着る こたつ 一人用 足元暖房"
    ],
    
    # 2. あったかブランケット・着る毛布・極暖毛布（20%配分）
    "blanket_fleece": [
        "着る毛布 ルームウェア もこもこ メンズ レディース", "着る毛布 ロング丈 フード付き 静電気防止",
        "西川 毛布 シングル 2枚合わせ 吸湿発熱", "極暖 マイクロファイバー 毛布 洗える 厚手",
        "大判 ブランケット 北欧 フリース ひざ掛け", "ボア ブランケット ふわふわ 暖かい 100 140",
        "掛け毛布 フランネル 蓄熱 保温 丸洗い", "シンサレート 掛け布団 毛布 ウルトラ 高密度",
        "発熱 コットン ブランケット 綿100% 洗える", "重い毛布 加重ブランケット 快眠 安眠",
        "電気ブランケット USB給電 丸洗い アウトドア", "ダウンブランケット 羽毛 洗える ひざ掛け"
    ],

    # 3. 冬のご褒美スイーツ（20%配分・フルーツ単体完全除外）
    "winter_sweets": [
        "濃厚 ガトーショコラ 熟成 チョコレートケーキ", "バスクチーズケーキ 濃厚 お取り寄せ スイーツ",
        "テリーヌショコラ 濃厚 生チョコ ギフト", "高級 プリン 詰め合わせ 濃厚 なめらか",
        "とろける生チョコ 専門店 ギフト ボックス", "抹茶バウムクーヘン 宇治抹茶 老舗 ギフト",
        "シュトーレン ドイツ 伝統菓子 クリスマス", "カヌレ ド ボルドー 6個入り フランス菓子",
        "フィナンシェ 焦がしバター 個包装 16個", "極上 どら焼き 粒あん 栗 どらやき 詰め合わせ",
        "和菓子 カステラ 長崎 老舗 個包装", "フォンダンショコラ とろける 温めて美味しい",
        "フロランタン 焼き菓子 アーモンド 大容量", "レーズンサンド 濃厚バタークリーム 10個入",
        "ブラウニー 濃厚 ナッツ チョコ 詰め合わせ"
    ],

    # 4. 名店・老舗おせち（10%配分）
    "famous_osechi": [
        "おせち 予約 2026 京都 割烹 料亭", "おせち 冷凍 老舗 和風 三段重",
        "名店監修 おせち 3人前 4人前", "銀座 ホテル おせち 和洋折衷 二段重",
        "金沢 料亭 おせち 伝統 厳選食材", "博多 和洋 おせち 特大 一段重 特生",
        "赤坂 料亭 おせち 高級食材 鮑 からすみ", "京都 祇園 おせち 三段重 予約"
    ],

    # 5. 温まる・リラックス入浴剤（10%配分）
    "bath_relax": [
        "薬用 重炭酸 入浴剤 ギフト 疲労回復", "エプソムソルト 国産 マグネシウム 入浴剤",
        "名湯 温泉 入浴剤 にごり湯 詰め合わせ", "アロマ バスミルク 高保湿 保湿入浴剤",
        "死海の塩 バスソルト 天然精油 リラックス", "生薬 漢方 薬湯 入浴剤 温活 冷え性",
        "発泡 炭酸ガス 入浴剤 バスボム 詰め合わせ", "クレイ 入浴剤 クレイバス 天然ミネラル"
    ],

    # 6. 加湿器（10%配分）
    "humidifier": [
        "ハイブリッド 加湿器 大容量 上部給水 静音", "超音波 加湿器 大容量 卓上 アロマ対応",
        "スチーム式 加湿器 衛生的 お手入れ簡単", "気化式 加湿器 省エネ 静音 リビング",
        "卓上 加湿器 USB コードレス 充電式", "タワー型 加湿器 大容量 次亜塩素酸水対応",
        "加湿器 アロマディフューザー 木目調 LEDライト"
    ],

    # 7. 乾燥対策コスメ・ハンド・リップ（10%配分）
    "winter_skincare": [
        "高保湿 ハンドクリーム シアバター ギフト", "薬用 リップバーム 高保湿 唇荒れ 乾燥",
        "セラミド 保湿クリーム フェイスクリーム 乾燥肌", "マルチバーム オーガニック シアバター 全身",
        "ネイルオイル ペンタイプ 保湿 指先ケア", "濃厚 ナイトリップマスク 唇用 美容液",
        "馬油 スキンクリーム 無香料 保湿 全身", "ヒアルロン酸 原液 美容液 高保湿 導入液"
    ]
}

CATEGORY_NAMES = {
    "heating_appliances": "暖房器具・暖房家電",
    "blanket_fleece": "ブランケット・着る毛布",
    "winter_sweets": "冬のご褒美スイーツ",
    "famous_osechi": "名店・老舗おせち",
    "bath_relax": "温まる・リラックス入浴剤",
    "humidifier": "加湿器・乾燥対策",
    "winter_skincare": "乾燥対策コスメ・ハンドケア"
}

CATEGORY_THEME_GENRES = {
    "heating_appliances": "200", # パソコン・家電
    "blanket_fleece": "600",     # 生活・インテリア
    "winter_sweets": "300",      # 料理・食べ物
    "famous_osechi": "300",      # 料理・食べ物
    "bath_relax": "710",         # 健康・ダイエット
    "humidifier": "200",         # パソコン・家電
    "winter_skincare": "700"     # 美容・コスメ
}

# 関連ジャンルID
GENRE_IDS = ["100804", "215787"]

def load_cache() -> set:
    if not os.path.exists(CACHE_FILE):
        return set()
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def save_cache(item_number: str):
    with open(CACHE_FILE, "a", encoding="utf-8") as f:
        f.write(f"{item_number}\n")

def load_json_history(filepath: str) -> list:
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_json_history(filepath: str, item: str, max_items: int = 5):
    history = load_json_history(filepath)
    if item in history:
        history.remove(item)
    history.append(item)
    if len(history) > max_items:
        history = history[-max_items:]
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Notice: Failed to save history to {filepath}: {e}")

def get_today_jst_str() -> str:
    """日本標準時（JST, UTC+9）の現在日付（YYYY-MM-DD）を取得する"""
    from datetime import datetime, timezone, timedelta
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).strftime("%Y-%m-%d")

def get_today_post_count() -> int:
    """
    本日の公開投稿数を取得する。
    1. daily_posts.json から本日の記録を取得
    2. daily_posts.json の日付が過去、または存在しない場合は本日は 0 件からスタート
    """
    today_str = get_today_jst_str()
    if os.path.exists(DAILY_POSTS_FILE):
        try:
            with open(DAILY_POSTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and data.get("date") == today_str:
                    return int(data.get("count", 0))
                else:
                    return 0
        except Exception as e:
            print(f"Notice: Could not read {DAILY_POSTS_FILE}: {e}")
    return 0

def increment_today_post_count() -> int:
    """本日の公開投稿数を1増やして保存する"""
    today_str = get_today_jst_str()
    count = get_today_post_count() + 1
    try:
        with open(DAILY_POSTS_FILE, "w", encoding="utf-8") as f:
            json.dump({"date": today_str, "count": count}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Notice: Failed to save {DAILY_POSTS_FILE}: {e}")
    return count

# 各カテゴリーの出現確率比率（ユーザー指定）
# 暖房家電 20%, ブランケット/毛布 20%, 冬スイーツ 20%, おせち 10%, 入浴剤 10%, 加湿器 10%, 乾燥コスメ 10%
CATEGORY_WEIGHTS = {
    "heating_appliances": 0.20,
    "blanket_fleece": 0.20,
    "winter_sweets": 0.20,
    "famous_osechi": 0.10,
    "bath_relax": 0.10,
    "humidifier": 0.10,
    "winter_skincare": 0.10
}

def generate_diverse_keyword(excluded_categories: list = None) -> tuple:
    """
    指定比率（暖房20%, 毛布20%, スイーツ20%, おせち10%, 入浴剤10%, 加湿器10%, コスメ10%）に基づき、
    直近のカテゴリー連続を回避しながら最適なジャンルとキーワードを選定する。
    戻り値: (category_id, keyword)
    """
    all_categories = list(EXPANDED_CATEGORIES.keys())
    recent_cats = load_json_history(RECENT_CATEGORIES_FILE)
    
    # 直近1〜2件のカテゴリーを除外対象とする（完全に同じジャンルが連続しないようにする）
    exclude_set = set(recent_cats[-2:]) if recent_cats else set()
    if excluded_categories:
        exclude_set.update(excluded_categories)
        
    candidates = [c for c in all_categories if c not in exclude_set]
    if not candidates:
        last_cat = recent_cats[-1] if recent_cats else ""
        candidates = [c for c in all_categories if c != last_cat]
        if not candidates:
            candidates = all_categories

    # 重み付け確率による選択
    weights = [CATEGORY_WEIGHTS.get(c, 0.1) for c in candidates]
    total_w = sum(weights)
    norm_weights = [w / total_w for w in weights]
    
    selected_cat = random.choices(candidates, weights=norm_weights, k=1)[0]
    
    # カテゴリー内のキーワードから、直近使われていないキーワードを優先選択
    recent_kws = load_json_history(RECENT_KEYWORDS_FILE)
    kw_candidates = [kw for kw in EXPANDED_CATEGORIES[selected_cat] if kw not in recent_kws[-15:]]
    if not kw_candidates:
        kw_candidates = EXPANDED_CATEGORIES[selected_cat]
        
    selected_kw = random.choice(kw_candidates)
    cat_label = CATEGORY_NAMES.get(selected_cat, selected_cat)
    print(f"Selected Genre: [{cat_label}] -> Keyword: '{selected_kw}'")
    return selected_cat, selected_kw

def generate_keyword() -> str:
    """後方互換用ラッパー"""
    _, kw = generate_diverse_keyword()
    return kw

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
                    # 高解像度画像URLの収集（?_ex=... を除去して原寸高解像度化）
                    api_images = []
                    for img_obj in item_data.get("mediumImageUrls", []):
                        u = img_obj.get("imageUrl", "")
                        if u:
                            clean_u = u.split("?")[0]
                            if clean_u not in api_images:
                                api_images.append(clean_u)
                    for img_obj in item_data.get("smallImageUrls", []):
                        u = img_obj.get("imageUrl", "")
                        if u:
                            clean_u = u.split("?")[0]
                            if clean_u not in api_images:
                                api_images.append(clean_u)
                    
                    items.append({
                        "title": item_data.get("itemName"),
                        "itemCaption": item_data.get("itemCaption", ""),
                        "affiliateUrl": item_data.get("affiliateUrl"),
                        "itemUrl": item_data.get("itemUrl", ""),
                        "itemCode": item_data.get("itemCode"),
                        "price": f"{item_data.get('itemPrice', '')}円",
                        "imageUrl": api_images[0] if api_images else "",
                        "imageUrls": api_images
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

def extract_rakuten_highres_images(item: dict, max_images: int = 6) -> list:
    """
    楽天APIおよび商品ページから高解像度の商品画像（3〜6枚）を確実に抽出する。
    バナー・ロゴ・アイコン等を除外し、クリーンな原寸画像URLのリストを返す。
    """
    images = []
    
    # 1. 楽天APIから取得済みの画像（?_ex=... を除去した原寸画像）
    for img in item.get("imageUrls", []):
        clean_img = img.split("?")[0]
        if clean_img and clean_img not in images:
            images.append(clean_img)
            
    # 2. 商品ページのURLを取得して詳細・スライダー画像を追加抽出
    item_url = item.get("itemUrl") or item.get("affiliateUrl") or ""
    pc_url = ""
    if "pc=" in item_url:
        try:
            parsed = urllib.parse.urlparse(item_url)
            qs = urllib.parse.parse_qs(parsed.query)
            if "pc" in qs and qs["pc"]:
                pc_url = qs["pc"][0]
        except Exception:
            pass
    elif "item.rakuten.co.jp" in item_url:
        pc_url = item_url

    if pc_url and len(images) < max_images:
        print(f"Scraping high-res slider images from product page: {pc_url}...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                page = browser.new_page(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page.goto(pc_url, timeout=20000, wait_until="domcontentloaded")
                time.sleep(2)
                
                img_elements = page.locator('img').all()
                for el in img_elements:
                    src = el.get_attribute("src") or ""
                    # 楽天のスライダー画像・キャビネット画像をターゲットにする
                    if any(domain in src for domain in ["tshop.r10s.jp", "thumbnail.image.rakuten.co.jp", "image.rakuten.co.jp"]):
                        clean_src = src.split("?")[0]
                        # 拡張子チェック（jpg, jpeg, png, webp のみ許可、gifや無拡張子は除外）
                        ext = clean_src.lower().split(".")[-1]
                        if ext not in ["jpg", "jpeg", "png", "webp"]:
                            continue
                        # バナー・ロゴ・キャンペーン・アイコン画像を除外
                        ignore_keywords = [
                            "logo", "banner", "campaign", "ranking", "eco_", "outlet",
                            "icon", "btn", "point", "coupon", "review",
                            "bn_", "bn.", "bntop", "ui1", "ui2", "ui3", "spacer",
                            "link_pro", "other/ui", "common", "header", "footer"
                        ]
                        if any(kw in clean_src.lower() for kw in ignore_keywords):
                            continue
                        if clean_src not in images:
                            images.append(clean_src)
                            if len(images) >= max_images:
                                break
                browser.close()
        except Exception as e:
            print(f"Notice: Product page high-res image extraction skipped or timed out: {e}")

    # 最低3枚、最大6枚に調整
    if not images:
        images = ["https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&auto=format&fit=crop&q=80"]
    while len(images) < 3:
        # 3枚未満の場合は既存画像を再利用
        images.append(images[len(images) % len(images)])

    print(f"Successfully prepared {len(images[:max_images])} high-resolution images for article.")
    return images[:max_images]

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
    
    prompt = f"""以下の楽天市場の商品情報を基にして、楽天ROOM用の紹介コメント（400文字以内）を生成してください。
【商品名】: {title}
【価格】: {price}

以下の要件を厳格に遵守してください：
1. 文字数は400文字以内（厳守。超えると投稿エラーになります）。
2. 親しみやすい話し言葉で、絵文字を5〜8個使用してください。
3. ハッシュタグを3〜5個（商品に直接関連するもの）含め、末尾に「#楽天市場」を必ず含めること。
4. URLや疑似リンク、プレースホルダーは絶対に含めないでください。
5. 出力は紹介コメントのテキストのみとし、前置きやMarkdownの装飾コードブロック等は一切含めないでください。
"""

    system_message = "あなたは楽天ROOMで大人気の暮らし・インテリア・便利家電・お取り寄せグルメ専門のインフルエンサーです。日々の暮らしを素敵に彩るアイテムや絶品グルメの魅力を親しみやすい日本語で発信してください。"

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
    "トイレットペーパー", "ティッシュペーパー", "みかん", "ミカン", "蜜柑",
    "リンゴ", "りんご", "林檎", "シャインマスカット", "ぶどう", "葡萄",
    "いちご", "イチゴ", "苺", "メロン", "スイカ", "桃", "もも", "フルーツ詰め合わせ", "果物"
]

def is_forbidden_item(title: str, caption: str = "") -> bool:
    """指定されたNG商品（ランチョンマット、クッションカバー、サボテン、トイレットペーパー、みかん等）を除外する。"""
    text = (title + " " + caption).lower()
    return any(term.lower() in text for term in FORBIDDEN_TERMS)

def post_single_article(rakuten_app_id: str, rakuten_access_key: str, rakuten_affiliate_id: str, rakuten_blog_id: str, session_b64: str, article_gen: ArticleGenerator, blog_api: RakutenBlogAPI, posted_cache: set, attempted_cats: list) -> bool:
    """
    1記事を検索・生成・投稿（または下書き保存）するコア処理関数。
    """
    selected_cat, keyword = generate_diverse_keyword(excluded_categories=attempted_cats)
    attempted_cats.append(selected_cat)
    if len(attempted_cats) >= len(EXPANDED_CATEGORIES):
        attempted_cats.clear()

    # 楽天市場から商品を検索
    target_item = None
    comparison_items = []
    
    # 家電系・コスメ系（暖房家電、加湿器、乾燥対策コスメ）の場合は似ているタイプの商品を4つ取得して比較記事にする
    is_comparison_cat = selected_cat in ["heating_appliances", "humidifier", "winter_skincare"]
    
    for attempt in range(15):
        if attempt > 0:
            time.sleep(1)
            selected_cat, keyword = generate_diverse_keyword(excluded_categories=attempted_cats)
            attempted_cats.append(selected_cat)
            if len(attempted_cats) >= len(EXPANDED_CATEGORIES):
                attempted_cats.clear()
            is_comparison_cat = selected_cat in ["heating_appliances", "humidifier", "winter_skincare"]
        
        items = fetch_rakuten_items(rakuten_app_id, rakuten_access_key, rakuten_affiliate_id, keyword)
        if items:
            for item in items:
                code = item["itemCode"]
                title = item.get("title", "")
                caption = item.get("itemCaption", "")
                if code not in posted_cache and not is_forbidden_item(title, caption):
                    if target_item is None:
                        target_item = item
                        if not is_comparison_cat:
                            break
                    elif is_comparison_cat and item not in comparison_items:
                        comparison_items.append(item)
                        if len(comparison_items) >= 3:
                            break
        if target_item:
            # おせち重複対策：もし過去におせちが投稿済みの場合はスイーツへ振替
            if selected_cat == "famous_osechi" and target_item["itemCode"] in posted_cache:
                print("Notice: Osechi duplicated. Redirecting to winter sweets...")
                selected_cat = "winter_sweets"
                keyword = random.choice(EXPANDED_CATEGORIES["winter_sweets"])
                target_item = None
                comparison_items = []
                continue
            break

    if not target_item:
        print("Warning: Standard search limit reached. Executing emergency diverse fall-through search...")
        fallback_kws = [
            ("heating_appliances", "セラミックファンヒーター 人感センサー 速暖"),
            ("blanket_fleece", "着る毛布 ルームウェア もこもこ メンズ レディース"),
            ("winter_sweets", "濃厚 ガトーショコラ 熟成 チョコレートケーキ"),
            ("bath_relax", "薬用 重炭酸 入浴剤 ギフト 疲労回復"),
            ("humidifier", "ハイブリッド 加湿器 大容量 上部給水 静音"),
            ("winter_skincare", "高保湿 ハンドクリーム シアバター ギフト"),
            ("famous_osechi", "おせち 予約 2026 京都 割烹 料亭")
        ]
        for fb_cat, fb_kw in fallback_kws:
            items = fetch_rakuten_items(rakuten_app_id, rakuten_access_key, rakuten_affiliate_id, fb_kw)
            for item in items:
                if item["itemCode"] not in posted_cache and not is_forbidden_item(item.get("title", "")):
                    target_item = item
                    selected_cat = fb_cat
                    keyword = fb_kw
                    break
            if target_item:
                break

    if not target_item:
        print("Error: Could not retrieve target item from API.")
        return False

    print(f"Target Item: {target_item['title']} (Code: {target_item['itemCode']})")

    cat_label = CATEGORY_NAMES.get(selected_cat, "暮らし・インテリア")
    
    # 暖房器具・加湿器・乾燥対策コスメで、比較用商品が揃っている場合は4商品比較形式で記事を生成
    if is_comparison_cat and len(comparison_items) >= 3:
        all_comp_items = [target_item] + comparison_items[:3]
        comp_aff_urls = []
        comp_imgs_list = []
        for it in all_comp_items:
            aff = it["affiliateUrl"]
            if rakuten_affiliate_id and not rakuten_affiliate_id.startswith("DUMMY"):
                prefix = "hb.afl.rakuten.co.jp/hgc/"
                if prefix in aff:
                    parts = aff.split(prefix)
                    subparts = parts[1].split("/", 1)
                    if len(subparts) == 2:
                        aff = parts[0] + prefix + rakuten_affiliate_id + "/" + subparts[1]
            comp_aff_urls.append(aff)
            comp_imgs_list.append(extract_rakuten_highres_images(it, max_images=1))
        
        article_content = article_gen.build_comparison_article(
            items=all_comp_items,
            affiliate_urls=comp_aff_urls,
            image_urls_list=comp_imgs_list,
            category_label=cat_label
        )
        time.sleep(2)
        blog_title = f"【徹底比較】冬を快適にする人気の{cat_label}おすすめ4選！"
        print(f"Generated Comparison Title: {blog_title}")
    else:
        # 通常の単一商品レビュー記事
        # アフィリエイトURL適用
        affiliate_url = target_item["affiliateUrl"]
        if rakuten_affiliate_id and not rakuten_affiliate_id.startswith("DUMMY"):
            prefix = "hb.afl.rakuten.co.jp/hgc/"
            if prefix in affiliate_url:
                parts = affiliate_url.split(prefix)
                subparts = parts[1].split("/", 1)
                if len(subparts) == 2:
                    affiliate_url = parts[0] + prefix + rakuten_affiliate_id + "/" + subparts[1]

        # 画像抽出
        highres_images = extract_rakuten_highres_images(target_item, max_images=3)

        # 記事・タイトル生成
        title_raw = target_item["title"]
        clean_title = article_gen.get_clean_product_name(title_raw, keyword)
        generator_input_item = {
            "title": target_item["title"],
            "clean_title": clean_title,
            "price": target_item["price"],
            "caption": target_item["itemCaption"],
            "search_keyword": keyword
        }
        
        article_content = article_gen.build_full_featured_article(
            item=generator_input_item,
            image_urls=highres_images,
            affiliate_url=affiliate_url
        )
        time.sleep(2)
        blog_title = article_gen.generate_blog_title(generator_input_item)
        print(f"Generated Title: {blog_title}")

    # 1日23件上限チェック ＆ 下書き50件上限判定
    today_posts = get_today_post_count()
    print(f"Daily Post Check: {today_posts}/{DAILY_MAX_PUBLIC_POSTS} posts made today ({get_today_jst_str()} JST).")

    if today_posts < DAILY_MAX_PUBLIC_POSTS:
        post_mode = "publish"
        allow_publish_fallback = True
        print(f"Daily post slot available ({today_posts+1}/{DAILY_MAX_PUBLIC_POSTS}). Mode: 【公開 (Publish)】")
    else:
        print(f"⚠️ 本日の公開上限（{DAILY_MAX_PUBLIC_POSTS}件）に到達済みです。下書き枠を確認します...")
        draft_count = blog_api.get_draft_count()
        if draft_count >= 50:
            print(f"🚫 下書き件数が{draft_count}件（上限50件以上）に達しているため、本日の追加処理を終了します。")
            return "DRAFT_LIMIT_REACHED"
        else:
            print(f"📝 下書き件数: {draft_count}/50件（50件未満のため、下書き保存モードで追加します）。")
            post_mode = "draft"
            allow_publish_fallback = False

    print(f"Posting to Rakuten Blog (Target Mode: {post_mode}, Allow Fallback: {allow_publish_fallback})...")
    cat_label = CATEGORY_NAMES.get(selected_cat, "暮らし・インテリア")
    theme_genre_id = CATEGORY_THEME_GENRES.get(selected_cat, "600")
    success = blog_api.post_entry(
        title=blog_title,
        html_content=article_content,
        post_mode=post_mode,
        category_name=cat_label,
        theme_keyword=keyword,
        genre_id=theme_genre_id,
        allow_publish_fallback=allow_publish_fallback
    )

    if success:
        print("Successfully posted/saved to Rakuten Blog!")
        if blog_api.last_post_type == "publish":
            new_count = increment_today_post_count()
            print(f"📈 Total public posts today updated to: {new_count}/{DAILY_MAX_PUBLIC_POSTS}")
        else:
            print(f"📝 Article safely saved as draft (Total public posts today remains: {get_today_post_count()})")

        save_cache(target_item["itemCode"])
        posted_cache.add(target_item["itemCode"])
        if is_comparison_cat and comparison_items:
            for ci in comparison_items:
                c_code = ci.get("itemCode")
                if c_code:
                    save_cache(c_code)
                    posted_cache.add(c_code)
        save_json_history(RECENT_CATEGORIES_FILE, selected_cat, max_items=5)
        save_json_history(RECENT_KEYWORDS_FILE, keyword, max_items=25)
        print(f"Updated genre rotation history: logged [{CATEGORY_NAMES.get(selected_cat, selected_cat)}]")
        return True
    else:
        print("Failed to post entry to Rakuten Blog.")
        return False

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
    
    session_b64 = (
        os.environ.get("RAKUTEN_BLOG_SESSION_B64") or 
        os.environ.get("ROOM_SESSION_B64") or 
        os.environ.get("HATENA_SESSION_B64")
    )

    posted_cache = load_cache()
    print(f"Loaded {len(posted_cache)} posted items from cache.")

    article_gen = ArticleGenerator()
    article_gen.load_model()
    blog_api = RakutenBlogAPI(blog_id=rakuten_blog_id, session_b64=session_b64)

    # 日本時間（JST）の現在時刻を取得
    from datetime import datetime, timezone, timedelta
    jst = timezone(timedelta(hours=9))
    now_jst = datetime.now(jst)
    print(f"Current JST Time: {now_jst.strftime('%Y-%m-%d %H:%M:%S')}")

    today_posts = get_today_post_count()
    print(f"Today's posted count: {today_posts}/{DAILY_MAX_PUBLIC_POSTS}")

    # 毎日0時台で今日の投稿が2本未満の場合は、確実に2本に達するまで連続投稿
    if now_jst.hour == 0 and today_posts < 2:
        target_articles_in_run = 2 - today_posts
        print(f" Midnight 00:00 JST schedule detected! Posting {target_articles_in_run} article(s) to reach 2 posts in hour 0.")
    else:
        target_articles_in_run = 1

    attempted_cats = []
    for art_idx in range(1, target_articles_in_run + 1):
        if target_articles_in_run > 1:
            print(f"\n--- Running Article {art_idx}/{target_articles_in_run} for this session ---")

        res = post_single_article(
            rakuten_app_id=rakuten_app_id,
            rakuten_access_key=rakuten_access_key,
            rakuten_affiliate_id=rakuten_affiliate_id,
            rakuten_blog_id=rakuten_blog_id,
            session_b64=session_b64,
            article_gen=article_gen,
            blog_api=blog_api,
            posted_cache=posted_cache,
            attempted_cats=attempted_cats
        )

        if res == "DRAFT_LIMIT_REACHED":
            print("Draft limit reached (>=50). Exiting gracefully.")
            break
        elif not res and art_idx == 1:
            sys.exit(1)

        if art_idx < target_articles_in_run:
            wait_sec = random.randint(15, 25)
            print(f"Waiting {wait_sec} seconds before next post in midnight run...")
            time.sleep(wait_sec)

    print("=== Auto Post Process Completed! ===")

if __name__ == "__main__":
    main()
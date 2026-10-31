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

# 8大カテゴリーの超厳選キーワード辞書（レパートリーの大幅拡大＆多様化）
EXPANDED_CATEGORIES = {
    # 1. 北欧・モダン家具＆大型収納
    "furniture_storage": [
        "北欧 木製 サイドテーブル", "北欧風 遮光カーテン", "北欧風 チェスト タンス",
        "ローテーブル 折りたたみ 北欧", "ハンガーラック スリム 木製", "スツール 木製 北欧",
        "座椅子 コンパクト 北欧", "キャスター付き ワゴン 北欧", "ウォールシェルフ 賃貸 北欧",
        "ウッドカーペット ナチュラル", "テレビ台 北欧 ローボード", "ダイニングチェア 北欧 木製",
        "ネストテーブル 北欧 木製", "マガジンラック 壁掛け 北欧", "シューズラック スリム 北欧",
        "本棚 スリム 大容量 木製", "ラダーラック 突っ張り 壁面収納", "コレクションケース ガラス 卓上",
        "パソコンデスク 幅80 北欧", "サイドチェスト キャスター付き 木目", "すのこベッド 折りたたみ シングル",
        "ドレッサー コンパクト 北欧 鏡台", "コートハンガー ポールスタンド 木製", "オープンラック 3段 木製",
        "キッチンラック ゴミ箱上 収納", "カウンター下収納 薄型 キャビネット", "ウッドラック 奥行30cm 北欧"
    ],
    
    # 2. 照明・インテリア雑貨・アート
    "lighting_decor": [
        "真鍮 ペンダントライト 北欧", "テーブルランプ 北欧 アンティーク", "LEDデスクライト 木目調",
        "間接照明 スタンド 北欧", "壁掛け時計 静音 北欧", "時計 デジタル 木目",
        "シーリングライト 北欧 木枠", "ブラケットライト 北欧 壁掛け", "ペンダントライト ガラス 北欧",
        "スリム 傘立て 北欧", "玄関マット 天然素材 北欧風", "キーフック 玄関 木製",
        "木製 ティッシュケース", "真鍮 アクセサリートレイ", "卓上 ミラー 木枠 北欧",
        "ジュエリーボックス 大容量 木製", "アロマストーン 皿付き", "フェルト 収納バスケット",
        "リードディフューザー 高級感 木", "キャンドルホルダー ガラス 北欧", "ポスターフレーム 木製 B2",
        "北欧 アートパネル ウォールデコ", "ブランケット 北欧 大判", "クッションカバー 北欧 リネン",
        "陶器 フラワーベース 北欧", "木製 ウォールハンガー 壁掛け", "韓国インテリア ウェーブミラー",
        "韓国インテリア アクリルシェルフ", "韓国風 卓上ライト 球体", "キャンドルウォーマー ランプ"
    ],

    # 3. キッチン家電・便利調理器具・テーブルウェア
    "kitchen_cooking": [
        "ブレッドケース パンケース おしゃれ", "調味料ラック ステンレス マグネット", "珪藻土 水切りマット ドライトレイ",
        "ウッドプレート 天然木 アカシア", "ガラス キャニスター 保存容器", "セラミック コーヒーミル 手動",
        "マグカップ 北欧 陶器 ペア", "カトラリーセット 北欧 クチポール風", "キッチンマット 滑り止め 北欧",
        "電気ケトル 温度調節 保温", "コンパクト ホットプレート 焼肉 たこ焼き", "自動調理鍋 電気圧力鍋 レシピ付き",
        "ノンフライヤー 大容量 卓上", "ミル付き 全自動 コーヒーメーカー", "スチーム オーブントースター 4枚焼き",
        "コードレス ハンドブレンダー 離乳食", "ヨーグルトメーカー 飲むヨーグルト 甘酒", "ホットサンドメーカー 電気 耳まで焼ける",
        "フードプロセッサー きざむ おろす", "真空パック機 フードシーラー", "ホーロー 鍋 キャセロール 蓋付き",
        "セラミック包丁 3点セット", "真空断熱 タンブラー 保冷 保温 蓋付き", "耐熱ガラス 密閉 保存容器 セット",
        "オイルポット ステンレス こし網付き", "水切りラック 伸縮 シンク上 ステンレス"
    ],

    # 4. スマート家電・生活家電・空調・掃除
    "appliances_cleaning": [
        "ロボット掃除機 水拭き 静音 自動充電", "コードレス掃除機 軽量 パワフル吸引", "サーキュレーター 静音 首振り 節電",
        "超音波加湿器 大容量 上部給水 木目", "ハイブリッド加湿器 静音 タイマー", "空気清浄機 コンパクト 静音 脱臭",
        "衣類スチーマー ハンディ スチームアイロン", "布団乾燥機 コンパクト 靴乾燥 アタッチメント", "デスク下 パネルヒーター 省エネ",
        "セラミックファンヒーター 人感センサー 速暖", "音波振動 電動歯ブラシ 充電式 防水", "マイナスイオン ヘアドライヤー 大風量 速乾",
        "LEDシーリングライト 調光調色 リモコン付き", "スマートリモコン SwitchBot ハブ", "卓上 加湿器 USB 静音 持ち運び",
        "コンパクト 除湿機 部屋干し 小型", "アロマディフューザー 超音波 タイマー付き", "毛玉取り器 コードレス 充電式 替刃付き"
    ],

    # 5. デスク周り・PC周辺・配線収納ガジェット
    "desk_gadget": [
        "木目調 ケーブルボックス 配線隠し", "モニタースタンド 木製 引き出し付き", "ノートパソコンスタンド アルミ 無段階調整",
        "3in1 ワイヤレス充電器 急速 スマホ 時計", "デスクマット 大型 レザー調 防水 滑り止め", "卓上 電源タップ USB急速充電 クランプ式",
        "木製 デスクオーガナイザー ペン立て", "デスクライト クランプ 目に優しい 無段階調光", "ケーブルクリップ マグネット 配線整理",
        "リストレスト 低反発 キーボード マウス", "ガジェットポーチ 大容量 トラベルポーチ 撥水", "折りたたみ式 タブレットスタンド アルミ",
        "ノートPC冷却ファン 静音 USB給電", "スマートゴミ箱 自動開閉 センサー 分別", "卓上 クリーナー ミニ掃除機 充電式"
    ],

    # 6. バス・ランドリー・快眠ヘルスケア
    "bath_sleep_relax": [
        "珪藻土バスマット グレー ソフト 丸洗い", "ランドリーバスケット キャスター付き 2段", "ホテル仕様 バスタオル 今治タオル 2枚組",
        "高反発 まくら 安眠 快眠 肩こり 首こり", "薬用 重炭酸 入浴剤 ギフト 疲労回復", "アロマスプレー ピローミスト 快眠 ラベンダー",
        "筋膜リリース マッサージガン 軽量 ミニ", "ネックマッサージャー 温熱 首 肩こり 充電式", "アイマッサージャー ホットアイマスク 充電式",
        "今治 タオルケット シングル 綿100% 日本製", "接触冷感 敷きパッド 丸洗い 吸水速乾", "シルク 枕カバー 絹100% 片面 洗える",
        "シャワーヘッド 節水 塩素除去 マイクロナノバブル", "ディスペンサー 自動 泡 ソープディスペンサー", "吸水ヘアキャップ マイクロファイバー 速乾"
    ],

    # 7. ご褒美スイーツ・和洋菓子・おうちカフェ
    "sweets_gift": [
        "バスクチーズケーキ 濃厚 お取り寄せ スイーツ", "濃厚 ガトーショコラ 熟成 チョコレートケーキ",
        "抹茶バウムクーヘン 宇治抹茶 老舗 ギフト", "高級 プリン 詰め合わせ 濃厚 なめらか",
        "マカロン ギフト 詰め合わせ 12個入り", "とろける生チョコ 専門店 ギフト ボックス",
        "和菓子 カステラ 長崎 老舗 個包装", "極上 どら焼き 粒あん 栗 どらやき 詰め合わせ",
        "北海道 ロールケーキ 純生クリーム ギフト", "フルーツタルト 宝石 冷凍便 ギフト",
        "カヌレ ド ボルドー 6個入り フランス菓子", "クッキー缶 ギフト 焼き菓子 詰め合わせ",
        "フィナンシェ 焦がしバター 個包装 16個", "高級 わらび餅 本わらび粉 抹茶 きなこ",
        "栗きんとん 中津川 老舗 国産栗 100%", "レーズンサンド 濃厚バタークリーム 10個入",
        "ジェラート 詰め合わせ イタリアン アイス 8個", "とろける シフォンケーキ 生クリーム プレーン",
        "アップルパイ 焼きたて 直送 青森りんご", "フロランタン 訳あり 焼き菓子 アーモンド 大容量"
    ],

    # 8. ふるさと納税＆極上お取り寄せグルメ
    "gourmet_furusato": [
        "ふるさと納税 黒毛和牛 ハンバーグ 10個以上", "ふるさと納税 国産 うなぎ 蒲焼 2尾以上 秘伝タレ",
        "ふるさと納税 オホーツク 特大ホタテ 1kg 刺身用", "ふるさと納税 熟成 牛タン 厚切り 焼肉用",
        "ふるさと納税 厳選 鮭 いくら 醤油漬け 200g以上", "ふるさと納税 博多 本場 もつ鍋 セット 3人前",
        "ふるさと納税 贅沢 クラフトビール 飲み比べ 詰め合わせ", "ふるさと納税 特選 シャインマスカット 1房以上",
        "ふるさと納税 プレミアム 白米 つや姫 10kg 新米", "ふるさと納税 宮崎牛 A5 等級 すき焼き しゃぶしゃぶ",
        "ふるさと納税 本まぐろ 中トロ 刺身用 柵どり", "ふるさと納税 もちもち 餃子 96個 冷凍 国産具材",
        "専門店の牛すじカレー レトルト 6食 贅沢", "本場 スペイン産 熟成 生ハム ハモンセラーノ 原木切り落とし",
        "ふるさと納税 ズワイガニ 棒肉 ポーション 殻剥き", "ふるさと納税 鹿児島県産 黒豚 しゃぶしゃぶ 食べ比べ"
    ]
}

CATEGORY_NAMES = {
    "furniture_storage": "家具・大型収納",
    "lighting_decor": "照明・インテリア雑貨",
    "kitchen_cooking": "キッチン・調理器具",
    "appliances_cleaning": "生活家電・スマート空調",
    "desk_gadget": "デスク周り・配線ガジェット",
    "bath_sleep_relax": "バス・快眠ヘルスケア",
    "sweets_gift": "ご褒美スイーツ・和洋菓子",
    "gourmet_furusato": "ふるさと納税・絶品グルメ"
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

def generate_diverse_keyword(excluded_categories: list = None) -> tuple:
    """
    直近に投稿されたカテゴリーを完全に除外して、毎回全く異なるジャンルから
    キーワードを選定する。（同じような商品の連続投稿を論理的に100%防止）
    戻り値: (category_id, keyword)
    """
    all_categories = list(EXPANDED_CATEGORIES.keys())
    recent_cats = load_json_history(RECENT_CATEGORIES_FILE)
    
    # 直近3〜4件のカテゴリーを除外対象とする
    exclude_set = set(recent_cats[-4:]) if recent_cats else set()
    if excluded_categories:
        exclude_set.update(excluded_categories)
        
    candidates = [c for c in all_categories if c not in exclude_set]
    if not candidates:
        # すべて除外された場合は直近1件のみ除外
        last_cat = recent_cats[-1] if recent_cats else ""
        candidates = [c for c in all_categories if c != last_cat]
        if not candidates:
            candidates = all_categories

    selected_cat = random.choice(candidates)
    
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

    # 1. 検索キーワード選定（直近ジャンルを自動除外して確実にバラケさせる）
    attempted_cats = []
    selected_cat, keyword = generate_diverse_keyword(excluded_categories=attempted_cats)
    attempted_cats.append(selected_cat)

    # 2. キャッシュの読み込み
    posted_cache = load_cache()
    print(f"Loaded {len(posted_cache)} posted items from cache.")

    # 3. 楽天市場から商品を検索し、未投稿かつNGでない商品を確実に探す（最大100回リトライで絶対止めない）
    target_item = None
    max_attempts = 100
    for attempt in range(max_attempts):
        if attempt > 0:
            time.sleep(1)
            # リトライ時は未投稿商品が見つからなかったカテゴリーを一旦除外し、別ジャンルから即座に選定
            selected_cat, keyword = generate_diverse_keyword(excluded_categories=attempted_cats)
            attempted_cats.append(selected_cat)
            if len(attempted_cats) >= len(EXPANDED_CATEGORIES):
                attempted_cats.clear()
        
        print(f"Attempt {attempt + 1}/{max_attempts}: Searching in [{CATEGORY_NAMES.get(selected_cat, selected_cat)}] with keyword '{keyword}'...")
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
        print(f"No suitable unposted items found for '{keyword}'. Switching to another diverse genre...")

    if not target_item:
        # 万が一見つからなかった場合の緊急フォールバック（8大ジャンルから1つずつ分散試行）
        print("Warning: Standard search limit reached. Executing emergency diverse fall-through search...")
        fallback_kws = [
            ("kitchen_cooking", "電気ケトル 温度調節 保温"),
            ("sweets_gift", "バスクチーズケーキ 濃厚 お取り寄せ スイーツ"),
            ("appliances_cleaning", "サーキュレーター 静音 首振り 節電"),
            ("gourmet_furusato", "ふるさと納税 黒毛和牛 ハンバーグ 10個以上"),
            ("desk_gadget", "木目調 ケーブルボックス 配線隠し"),
            ("bath_sleep_relax", "ホテル仕様 バスタオル 今治タオル 2枚組"),
            ("furniture_storage", "北欧 木製 サイドテーブル"),
            ("lighting_decor", "真鍮 ペンダントライト 北欧")
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

    # 5. LLMで超高品質なフル構成レビュー記事（HTML形式）を生成
    # 画像は多すぎて見づらくならないよう、厳選2〜3枚に設定
    print("Extracting high-resolution product images (2-3 images)...")
    highres_images = extract_rakuten_highres_images(target_item, max_images=3)

    print("Generating High-Quality Full Review Article...")
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
    
    article_content = article_gen.build_full_featured_article(
        item=generator_input_item,
        image_urls=highres_images,
        affiliate_url=affiliate_url
    )

    # APIの連続呼び出し（429エラー）を回避するため少し待機
    time.sleep(3)
    
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
        save_json_history(RECENT_CATEGORIES_FILE, selected_cat, max_items=5)
        save_json_history(RECENT_KEYWORDS_FILE, keyword, max_items=25)
        print(f"Updated genre rotation history: logged [{CATEGORY_NAMES.get(selected_cat, selected_cat)}]")
    else:
        print("Failed to post entry to Rakuten Blog.")
        sys.exit(1)

    print("=== Auto Post Process Completed! ===")

if __name__ == "__main__":
    main()
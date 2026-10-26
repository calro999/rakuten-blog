import os
import sys
import time
import json
import random
import builtins

print = lambda *args, **kwargs: builtins.print(*args, flush=True, **kwargs)

from auto_poster import (
    load_cache, save_cache, load_json_history, save_json_history,
    select_next_category_and_keyword, fetch_rakuten_items,
    is_forbidden_item, extract_rakuten_highres_images,
    CACHE_FILE, RECENT_CATEGORIES_FILE, RECENT_KEYWORDS_FILE,
    EXPANDED_CATEGORIES, CATEGORY_NAMES
)
from article_generator import ArticleGenerator
from rakuten_blog_api import RakutenBlogAPI

def run_batch():
    batch_count_str = os.getenv("BATCH_COUNT", "40")
    try:
        batch_count = int(batch_count_str)
    except ValueError:
        batch_count = 40

    post_mode = os.getenv("POST_MODE", "draft").strip().lower()
    print("=" * 60)
    print(f"🚀 Starting Rakuten Blog Batch Generation: Target {batch_count} Articles")
    print(f"📌 Mode: {'【下書き保存 (Draft)】' if post_mode == 'draft' else '【通常公開 (Publish)】'}")
    print("=" * 60)

    # 1. 認証情報の取得
    rakuten_app_id = os.getenv("RAKUTEN_APP_ID")
    rakuten_access_key = os.getenv("RAKUTEN_ACCESS_KEY")
    rakuten_affiliate_id = os.getenv("RAKUTEN_AFFILIATE_ID")
    rakuten_blog_id = os.getenv("RAKUTEN_BLOG_ID")
    session_b64 = os.getenv("RAKUTEN_BLOG_SESSION_B64")

    if not rakuten_app_id:
        print("Error: RAKUTEN_APP_ID environment variable is missing.")
        sys.exit(1)

    posted_cache = load_cache()
    recent_categories = load_json_history(RECENT_CATEGORIES_FILE)
    recent_keywords = load_json_history(RECENT_KEYWORDS_FILE)

    # Article Generatorの初期化（再利用して高速化）
    print("Initializing Article Generator models...")
    article_gen = ArticleGenerator()
    article_gen.load_model()

    # RakutenBlogAPIの初期化
    blog_api = RakutenBlogAPI(blog_id=rakuten_blog_id, session_b64=session_b64)

    success_count = 0
    fail_count = 0

    for i in range(1, batch_count + 1):
        print(f"\n==================== [記事 {i} / {batch_count}] 生成開始 ====================")
        
        target_item = None
        selected_cat = None
        keyword = None

        # 最大10回リトライして未投稿かつ規約に違反しない商品を探す
        for attempt in range(10):
            selected_cat, keyword = select_next_category_and_keyword(recent_categories, recent_keywords)
            cat_name = CATEGORY_NAMES.get(selected_cat, selected_cat)
            print(f"Attempt {attempt+1}: Category [{cat_name}], Keyword [{keyword}]")
            
            items = fetch_rakuten_items(rakuten_app_id, rakuten_access_key, rakuten_affiliate_id, keyword)
            for it in items:
                code = it.get("itemCode")
                title = it.get("title", "")
                if code and code not in posted_cache and not is_forbidden_item(title):
                    target_item = it
                    break
            
            if target_item:
                break
            time.sleep(1)

        # 見つからない場合のフォールバック
        if not target_item:
            print("Fallback to diverse search...")
            fallback_kws = [
                ("sweets_gift", "バスクチーズケーキ 濃厚 お取り寄せ スイーツ"),
                ("appliances_cleaning", "サーキュレーター 静音 首振り 節電"),
                ("bath_sleep_relax", "ホテル仕様 バスタオル 今治タオル 2枚組"),
                ("kitchen_cooking", "電気ケトル 温度調節 保温"),
                ("desk_gadget", "木目調 ケーブルボックス 配線隠し"),
                ("furniture_storage", "北欧 木製 サイドテーブル"),
                ("lighting_decor", "真鍮 ペンダントライト 北欧"),
                ("gourmet_furusato", "ふるさと納税 黒毛和牛 ハンバーグ 10個以上")
            ]
            for fb_cat, fb_kw in fallback_kws:
                items = fetch_rakuten_items(rakuten_app_id, rakuten_access_key, rakuten_affiliate_id, fb_kw)
                for it in items:
                    code = it.get("itemCode")
                    if code and code not in posted_cache and not is_forbidden_item(it.get("title", "")):
                        target_item = it
                        selected_cat = fb_cat
                        keyword = fb_kw
                        break
                if target_item:
                    break

        if not target_item:
            print(f"Skipping article {i}: Could not find any valid item.")
            fail_count += 1
            continue

        print(f"Selected: {target_item['title'][:50]}... ({target_item['itemCode']})")

        # アフィリエイトURLの構築
        affiliate_url = target_item["affiliateUrl"]
        if rakuten_affiliate_id and not rakuten_affiliate_id.startswith("DUMMY"):
            prefix = "hb.afl.rakuten.co.jp/hgc/"
            if prefix in affiliate_url:
                parts = affiliate_url.split(prefix)
                subparts = parts[1].split("/", 1)
                if len(subparts) == 2:
                    affiliate_url = parts[0] + prefix + rakuten_affiliate_id + "/" + subparts[1]

        # 高画質画像の抽出
        highres_images = extract_rakuten_highres_images(target_item, max_images=6)

        # タイトル・記事本文生成
        clean_title = article_gen.get_clean_product_name(target_item["title"], keyword)
        gen_input = {
            "title": target_item["title"],
            "clean_title": clean_title,
            "price": target_item["price"],
            "caption": target_item["itemCaption"],
            "search_keyword": keyword
        }

        article_html = article_gen.build_full_featured_article(
            item=gen_input,
            image_urls=highres_images,
            affiliate_url=affiliate_url
        )

        time.sleep(2)
        blog_title = article_gen.generate_blog_title(gen_input)
        print(f"Generated Title: {blog_title}")

        # 楽天ブログへの投稿
        try:
            success = blog_api.post_entry(title=blog_title, html_content=article_html)
            if success:
                print(f"✅ Article {i} saved/posted successfully!")
                success_count += 1
                
                # キャッシュと履歴更新
                item_code = target_item["itemCode"]
                save_cache(item_code)
                posted_cache.add(item_code)
                
                recent_categories = save_json_history(RECENT_CATEGORIES_FILE, selected_cat, max_items=5)
                recent_keywords = save_json_history(RECENT_KEYWORDS_FILE, keyword, max_items=25)
            else:
                print(f"❌ Article {i} failed to post.")
                fail_count += 1
        except Exception as e:
            print(f"❌ Article {i} encountered exception: {e}")
            fail_count += 1

        # 連続投稿による負荷・ブロック防止のためインターバルを置く
        if i < batch_count:
            wait_sec = random.randint(15, 25)
            print(f"Waiting {wait_sec} seconds before next post to ensure stability...")
            time.sleep(wait_sec)

    print("\n" + "=" * 60)
    print(f"🎉 Batch Process Finished! Total Target: {batch_count}")
    print(f"✅ Success: {success_count} / ❌ Failed: {fail_count}")
    print("=" * 60)

if __name__ == "__main__":
    run_batch()

import os
import sys

# プロジェクトルートをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from article_generator import ArticleGenerator

def test_generation():
    print("=== Testing Post Generation (Dry-run with Clean Product Names) ===")
    
    # 楽天市場にありがちなノイズの多いリアルな商品データをテスト用に用意
    test_items = [
        {
            "title": "ゴミ箱 分別 スリム おしゃれ キッチン 縦型 ペダル ペール ダストボックス キャスター付き 収納 45リットル 45L シンプル ホワイト ブラック",
            "itemCaption": "キッチンの隙間にスッキリ収まるスリムで縦型の分別ゴミ箱。ペダル式なので調理中でも手を汚さずに開閉できます。キャスター付きでゴミ出しや掃除の際の移動もラクラク。スタイリッシュなモノトーンデザインです。",
            "price": "4,980円",
            "search_keyword": "分別ゴミ箱"
        },
        {
            "title": "傘立て おしゃれ 北欧 スリム アイアン コンパクト アンブレラスタンド レトロ シンプル アンティーク 玄関収納 傘たて 水受け皿付き ホワイト",
            "itemCaption": "玄関の限られたスペースにすっきり置ける、スリムでコンパクトなアイアン傘立て。レトロでアンティーク調のデザインが、エントランスをシックに演出します。取り外し可能な水受け皿付きで、お手入れも簡単です。",
            "price": "2,980円",
            "search_keyword": "傘立て"
        }
    ]
    
    generator = ArticleGenerator()
    generator.load_model()
    
    for idx, item in enumerate(test_items):
        print(f"\n--- Item {idx+1}: {item['search_keyword']} ---")
        print(f"Original Title: {item['title']}")
        
        # 1. クリーンな商品名の抽出テスト
        clean_name = generator.get_clean_product_name(item["title"], item["search_keyword"])
        print(f"Extracted Clean Name: {clean_name}")
        
        # モックの入力形式に合わせる
        item_data = {
            "title": item["title"],
            "clean_title": clean_name,
            "price": item["price"],
            "caption": item["itemCaption"],
            "search_keyword": item["search_keyword"]
        }
        
        # 2. 楽天ブログのタイトル生成テスト
        print("\n[Generated Blog Title]")
        title = generator.generate_blog_title(item_data)
        print(title)
        
        # 3. 楽天ブログの記事本文生成テスト
        print("\n[Generated Blog Article]")
        article = generator.generate_review_article(item_data)
        print(article)

if __name__ == "__main__":
    test_generation()

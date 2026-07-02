import os
import sys

# プロジェクトルートをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from article_generator import ArticleGenerator

def test_generation():
    print("=== Testing Post Generation (Furusato Carbonated Water Test) ===")
    
    test_items = [
        {
            "title": "【ふるさと納税】＼35本カートン／ふるさと納税限定 ガイアの夜明けで紹介 すぐ届く VOX 強炭酸水 35本 500ml ラベルレス 選べる ストレート レモン 1箱 2箱 3箱 大容量 炭酸水 ハイボール 割り材 ソーダ 高評価 防災 ふるさと納税 ランキング 6000円以内 まとめ買 炭酸飲料",
            "itemCaption": "磨き抜かれた純水と炭酸のみを使用した、強炭酸水の35本セット。ラベルレスでエコに配慮し、そのまま飲むのはもちろん、ハイボールや割り材としても最適です。すっきりとしたクリアな喉ごしをお楽しみください。",
            "price": "6,000円",
            "search_keyword": "ふるさと納税 炭酸水 ストレート"
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
        print(article[:1000] + "\n... (truncated for display)")

if __name__ == "__main__":
    test_generation()

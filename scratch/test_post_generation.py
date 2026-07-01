import os
import sys

# プロジェクトルートをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from article_generator import ArticleGenerator
from auto_poster import generate_room_comment_with_llm

def test_generation():
    print("=== Testing Post Generation (Dry-run) ===")
    
    # テスト用の商品データ
    test_items = [
        {
            "title": "【北欧風】天然木 サイドテーブル 丸型 直径40cm",
            "itemCaption": "ソファーサイドやベッドサイドにぴったりのコンパクトな天然木サイドテーブル。温かみのあるオーク材を使用し、お部屋にナチュラルな優しさをプラスします。引き出し付きでリモコンや小物もすっきり収納可能。組み立て不要の完成品でお届けします。",
            "price": "5,980円"
        },
        {
            "title": "珪藻土バスマット ノンアスベスト 速乾吸水 抗菌消臭 Lサイズ",
            "itemCaption": "お風呂上がりの水分を瞬時に吸収する、天然素材の珪藻土バスマット。驚きの速乾性で、家族が続けて使っても常にサラサラで快適です。ノンアスベスト検査済みで安心安全。モダンなグレーカラーで、どんなサニタリー空間にもおしゃれに調和します。",
            "price": "3,480円"
        }
    ]
    
    generator = ArticleGenerator()
    generator.load_model()
    
    for idx, item in enumerate(test_items):
        print(f"\n--- Item {idx+1}: {item['title']} ---")
        
        # モックの入力形式に合わせる
        item_data = {
            "title": item["title"],
            "clean_title": item["title"].replace("【", "").replace("】", ""),
            "price": item["price"],
            "caption": item["itemCaption"],
            "search_keyword": "サイドテーブル" if idx == 0 else "バスマット"
        }
        
        print("\n[Generated Blog Title]")
        title = generator.generate_blog_title(item_data)
        print(title)
        
        print("\n[Generated Blog Article]")
        article = generator.generate_review_article(item_data)
        print(article)
        
        print("\n[Generated ROOM Comment]")
        room_comment = generate_room_comment_with_llm(item)
        print(room_comment)

if __name__ == "__main__":
    test_generation()

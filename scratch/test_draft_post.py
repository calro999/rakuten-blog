import os
import sys

# パスを追加してモジュールをインポートできるようにする
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rakuten_blog_api import RakutenBlogAPI

def main():
    print("Testing post draft using modified API...")
    title = "おうちカフェが叶う！おしゃれなアカシアプレート"
    content = """
    <p>テスト投稿です。おしゃれなアカシアプレートでおうちカフェが楽しめます。</p>
    <p>ウッド調のナチュラルなデザインが素敵です！</p>
    """
    
    # RAKUTEN_BLOG_SESSION_B64環境変数を無効化し、ローカルの session.json を強制的に使うようにする
    if "RAKUTEN_BLOG_SESSION_B64" in os.environ:
        del os.environ["RAKUTEN_BLOG_SESSION_B64"]
        
    api = RakutenBlogAPI(session_file="session.json")
    success = api.post_entry(title=title, html_content=content)
    
    if success:
        print("Success! Draft posted and confirmed via UI.")
    else:
        print("Failed! Draft posting could not be verified.")

if __name__ == "__main__":
    main()

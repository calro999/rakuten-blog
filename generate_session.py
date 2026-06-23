import json
import base64
from playwright.sync_api import sync_playwright

def main():
    print("楽天にログインしてセッション情報（session.json）を保存します...")
    with sync_playwright() as p:
        # ユーザーが操作できるよう、ブラウザを画面に表示して（headless=False）起動します
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # 楽天ROOM・楽天ブログ共通のログイン画面へ
        print("楽天のトップページへ移動します。")
        page.goto("https://plaza.rakuten.co.jp/")
        
        print("\n=========================================================")
        print("【ログイン手順】")
        print("1. 開いたブラウザ画面右上にある「ログイン」ボタンからログインしてください。")
        print("2. ログインが完了し、楽天ブログの管理画面やブログトップページが表示されたら")
        print("   このターミナル（コマンドライン）に戻り、Enter キーを押してください。")
        print("=========================================================\n")
        
        input("ログイン完了後、Enter キーを押してください...")
        
        # セッションの取得と保存
        state = context.storage_state()
        
        # 不要なサードパーティCookieを削除し、ローカルストレージ情報(origins)をクリアして軽量化します
        # (GitHub Secrets の 64KB 制限を回避するため)
        cleaned_cookies = [c for c in state.get("cookies", []) if "rakuten" in c.get("domain", "").lower()]
        cleaned_state = {
            "cookies": cleaned_cookies,
            "origins": []
        }
        
        # 1. ローカルファイルとして保存
        with open("session.json", "w", encoding="utf-8") as f:
            json.dump(cleaned_state, f)
            
        print("\n✅ session.json を作成し、現在のディレクトリに保存しました。")
        
        # 2. Base64エンコード文字列の生成
        session_str = json.dumps(cleaned_state)
        b64_str = base64.b64encode(session_str.encode('utf-8')).decode('utf-8')
        
        # 3. テキストファイルとしても保存（見切れ防止用）
        with open("session_base64.txt", "w", encoding="utf-8") as f_b64:
            f_b64.write(b64_str)
            
        print("✅ session_base64.txt に軽量化したBase64文字列を保存しました。")
        print("\n================== RAKUTEN_BLOG_SESSION_B64 (コピー用) ==================")
        print(b64_str[:100] + "... (以下略、詳細は session_base64.txt を開いてコピーしてください) ...")
        print("=========================================================================\n")
        print("同ディレクトリに生成された `session_base64.txt` を開き、中身をすべてコピーして")
        print("GitHub Actions の Secrets や環境変数設定（RAKUTEN_BLOG_SESSION_B64）にご使用ください。")

        browser.close()

if __name__ == "__main__":
    main()

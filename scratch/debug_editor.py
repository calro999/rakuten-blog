import os
import json
import base64
from playwright.sync_api import sync_playwright

def main():
    session_file = "session.json"
    if not os.path.exists(session_file):
        # session_base64.txt からデコード
        if os.path.exists("session_base64.txt"):
            with open("session_base64.txt", "r") as f:
                b64 = f.read().strip()
                decoded = base64.b64decode(b64).decode("utf-8")
                with open(session_file, "w") as sf:
                    sf.write(decoded)
        else:
            print("No session data found.")
            return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=session_file)
        page = context.new_page()
        
        # ログイン後の日記投稿画面へ
        url = "https://my.plaza.rakuten.co.jp/diary/write/"
        print(f"Navigating to {url}...")
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        
        print("Page Title:", page.title())
        print("Page URL:", page.url)
        
        # textarea要素を探す
        print("--- Textareas ---")
        textareas = page.locator("textarea").all()
        if textareas:
            ta = textareas[0]
            print(f"[0] id={ta.get_attribute('id')}, name={ta.get_attribute('name')}, visible={ta.is_visible()}")
            outer_html = page.evaluate("el => el.outerHTML", ta.element_handle())
            print("HTML:", outer_html[:400])

        # input checkboxを探す
        print("--- Checkboxes ---")
        checkboxes = page.locator("input[type='checkbox']").all()
        for idx, cb in enumerate(checkboxes):
            print(f"[{idx}] id={cb.get_attribute('id')}, name={cb.get_attribute('name')}, checked={cb.is_checked()}, visible={cb.is_visible()}")

        # 「見たまま編集」を含む要素を検索
        print("--- '見たまま編集' elements ---")
        elements = page.locator("*:has-text('見たまま編集')").all()
        for idx, el in enumerate(elements):
            try:
                tag = page.evaluate("el => el.tagName", el.element_handle())
                html = page.evaluate("el => el.outerHTML", el.element_handle())
                print(f"[{idx}] tag={tag}, html={html[:200]}")
            except Exception:
                continue

        # iframeを探す
        print("--- IFrames ---")
        frames = page.frames
        for idx, fr in enumerate(frames):
            print(f"[{idx}] name={fr.name}, url={fr.url}")

        browser.close()

if __name__ == "__main__":
    main()

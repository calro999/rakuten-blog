import os
import time
from playwright.sync_api import sync_playwright

def main():
    session_file_path = "session.json"
    if not os.path.exists(session_file_path):
        print(f"Error: {session_file_path} not found.")
        return

    print("Navigating to write page...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            storage_state=session_file_path,
            viewport={"width": 1280, "height": 1200}, # 高さ広めに設定
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        write_url = "https://my.plaza.rakuten.co.jp/diary/write/"
        page.goto(write_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(5)
        
        # Take a screenshot
        page.screenshot(path="scratch/write_page_full.png", full_page=True)
        print("Saved full page screenshot to scratch/write_page_full.png")
        
        # Save page source
        with open("scratch/write_page_source.html", "w", encoding="utf-8") as f:
            f.write(page.content())
            
        print("Page URL:", page.url)
        print("Page Title:", page.title())
        
        # Find all inputs and buttons
        buttons = page.locator('input[type="submit"], input[type="button"], button').all()
        print(f"\nFound {len(buttons)} button-like elements:")
        for idx, btn in enumerate(buttons):
            try:
                name = btn.get_attribute('name') or ""
                id_attr = btn.get_attribute('id') or ""
                value = btn.get_attribute('value') or btn.text_content().strip() or ""
                type_attr = btn.get_attribute('type') or ""
                print(f"[{idx}] Tag: {btn.evaluate('el => el.tagName')} | ID: {id_attr} | Name: {name} | Value/Text: {value} | Type: {type_attr}")
            except Exception as e:
                print(f"[{idx}] Error reading element: {e}")
                
        browser.close()

if __name__ == "__main__":
    main()

import os
import base64
import json
import time
from playwright.sync_api import sync_playwright

def main():
    session_file_path = "session.json"
    if not os.path.exists(session_file_path):
        print(f"Error: {session_file_path} not found.")
        return

    print("Checking Rakuten Blog DRAFTS list using session.json...")
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
        
        # Go to diary draft list page
        draft_url = "https://my.plaza.rakuten.co.jp/diary/list/draft/"
        print(f"Navigating to: {draft_url}")
        page.goto(draft_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(5)
        
        # Take a screenshot of the draft list
        screenshot_path = "scratch/draft_list_only.png"
        page.screenshot(path=screenshot_path)
        print(f"Saved screenshot to {screenshot_path}")
        
        # Extract titles from the list
        page_content = page.content()
        with open("scratch/draft_list_only_page.html", "w", encoding="utf-8") as f_html:
            f_html.write(page_content)
            
        print("Page title:", page.title())
        print("Page URL:", page.url)
        
        # Try to find list items
        links = page.locator('a').all()
        print(f"Found {len(links)} links on the page.")
        
        print("\n--- Listing visible links containing 'diary' or potentially titles in DRAFTS ---")
        for link in links:
            try:
                href = link.get_attribute('href') or ""
                text = link.text_content().strip()
                if "diary" in href or (text and len(text) > 3):
                    print(f"Link: {text} | Href: {href}")
            except Exception:
                pass

        browser.close()

if __name__ == "__main__":
    main()

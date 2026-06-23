import os
import time
import base64
import tempfile
import json
from playwright.sync_api import sync_playwright

class RakutenBlogAPI:
    def __init__(self, blog_id: str = "", session_b64: str = None, session_file: str = "session.json"):
        # Clean blog_id (extract username from URL if necessary)
        cleaned_id = blog_id.strip() if blog_id else ""
        if "/" in cleaned_id:
            # e.g. https://plaza.rakuten.co.jp/jack555/ -> jack555
            cleaned_id = cleaned_id.replace("https://", "").replace("http://", "")
            parts = [p for p in cleaned_id.split("/") if p]
            if len(parts) >= 2 and parts[0] == "plaza.rakuten.co.jp":
                cleaned_id = parts[1]
            elif parts:
                cleaned_id = parts[0]
        self.blog_id = cleaned_id
        self.session_b64 = session_b64
        self.session_file = session_file

    def _prepare_session_file(self) -> str:
        """Decodes base64 session or checks local session.json and returns the path to a valid session file."""
        if self.session_b64 and self.session_b64.strip():
            print("Using RAKUTEN_BLOG_SESSION_B64 from environment variable.")
            try:
                decoded_str = base64.b64decode(self.session_b64).decode('utf-8')
                json.loads(decoded_str)  # Verify valid JSON
                temp_file = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".json")
                temp_file.write(decoded_str)
                temp_file.close()
                return temp_file.name
            except Exception as e:
                print(f"Error decoding RAKUTEN_BLOG_SESSION_B64: {e}")
        
        if os.path.exists(self.session_file):
            print(f"Using local session file: {self.session_file}")
            return self.session_file
            
        print("Warning: No valid session data provided. Will attempt running without saved session state.")
        return None

    def _safe_screenshot(self, page, path):
        """Helper to take screenshots safely without crashing the script on timeouts."""
        try:
            page.screenshot(path=path, timeout=5000)
            print(f"Saved screenshot: {path}")
        except Exception as e:
            print(f"Warning: Failed to save screenshot {path}: {e}")

    def post_entry(self, title: str, html_content: str) -> bool:
        """Posts a blog entry to Rakuten Blog using Playwright."""
        session_path = self._prepare_session_file()
        success = False

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                
                # Context options
                context_args = {
                    "viewport": {"width": 1280, "height": 800},
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                if session_path:
                    context_args["storage_state"] = session_path

                context = browser.new_context(**context_args)
                page = context.new_page()
                page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

                write_url = ""
                if self.blog_id:
                    write_url = f"https://plaza.rakuten.co.jp/{self.blog_id}/diary/write/"
                    print(f"Attempting direct navigation to: {write_url}")
                    page.goto(write_url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(5)
                
                # If direct page was not successful, or if blog_id was empty, try to resolve via homepage
                current_url = page.url
                if not write_url or "login" in current_url.lower() or "404" in page.title() or page.locator("text=404 Not Found").first.is_visible(timeout=2000):
                    print("Direct URL failed, empty, or redirected. Trying dynamic link resolution via Rakuten Blog homepage...")
                    page.goto("https://plaza.rakuten.co.jp/", wait_until="domcontentloaded", timeout=30000)
                    time.sleep(5)
                    
                    # Check if login button is present (indicates we're not logged in)
                    login_btn = page.locator('a:has-text("ログイン"), .login').first
                    if login_btn.is_visible(timeout=2000) and not page.locator('a:has-text("ログアウト")').first.is_visible(timeout=1000):
                        print("Error: Session has expired or is invalid. Login button is visible on the homepage.")
                        self._safe_screenshot(page, "login_required_error.png")
                        return False

                    # Try to find a link to "日記を書く" or "管理ページ"
                    write_link = page.locator('a[href*="diary/write"], a:has-text("日記を書く")').first
                    if write_link.is_visible(timeout=3000):
                        print("Found '日記を書く' link. Clicking...")
                        write_link.click()
                        time.sleep(5)
                    else:
                        manage_link = page.locator('a[href*="main"], a:has-text("管理ページ"), a:has-text("ブログ管理")').first
                        if manage_link.is_visible(timeout=3000):
                            print("Found 'ブログ管理' link. Clicking...")
                            manage_link.click()
                            time.sleep(5)
                            # Now try to find "日記を書く" on the manage page
                            sub_write_link = page.locator('a[href*="diary/write"], a:has-text("日記を書く")').first
                            if sub_write_link.is_visible(timeout=3000):
                                sub_write_link.click()
                                time.sleep(5)

                current_url = page.url
                print(f"Current URL before filling editor: {current_url}")
                if "login" in current_url.lower() or "404" in page.title():
                    print("Error: Failed to reach the diary write page.")
                    self._safe_screenshot(page, "navigation_error.png")
                    return False

                print("Filling title...")
                title_filled = False
                title_selectors = [
                    'input[name="title"]',
                    'input#diaryTitle',
                    'input[id*="title"]',
                    'input[type="text"][placeholder*="タイトル"]'
                ]
                for selector in title_selectors:
                    try:
                        element = page.locator(selector).first
                        if element.is_visible(timeout=2000):
                            element.fill(title)
                            title_filled = True
                            print(f"Filled title using selector: {selector}")
                            break
                    except Exception:
                        continue

                if not title_filled:
                    print("Warning: Could not find title input with standard selectors. Attempting fallback input field...")
                    inputs = page.locator('input[type="text"]')
                    count = inputs.count()
                    for i in range(count):
                        inp = inputs.nth(i)
                        if inp.is_visible():
                            inp.fill(title)
                            title_filled = True
                            print("Filled title in the first visible text input.")
                            break

                print("Filling body content...")
                body_filled = False
                body_selectors = [
                    'textarea[name="body"]',
                    'textarea#diaryBody',
                    'textarea[id*="body"]',
                    'textarea[placeholder*="本文"]',
                    'textarea'
                ]
                for selector in body_selectors:
                    try:
                        element = page.locator(selector).first
                        if element.is_visible(timeout=2000):
                            element.fill(html_content)
                            body_filled = True
                            print(f"Filled body using selector: {selector}")
                            break
                    except Exception:
                        continue

                if not body_filled:
                    print("Searching for rich editor frames...")
                    frames = page.frames
                    for frame in frames:
                        try:
                            body_el = frame.locator('body')
                            if body_el.is_visible(timeout=2000):
                                body_el.fill(html_content)
                                body_filled = True
                                print("Filled body inside iframe.")
                                break
                        except Exception:
                            continue

                if not body_filled:
                    print("Error: Could not fill blog body text.")
                    self._safe_screenshot(page, "body_fill_error.png")
                    return False

                # Take screenshot of filled state
                self._safe_screenshot(page, "filled_post_draft.png")

                # Submit the post
                print("Clicking submit/preview button...")
                submit_selectors = [
                    'input[type="submit"][value*="確認"]',
                    'input[type="submit"][value*="登録"]',
                    'input[type="submit"][value*="掲載"]',
                    'button:has-text("確認")',
                    'button:has-text("登録")',
                    'button:has-text("掲載")',
                    'input[type="submit"]',
                    'button[type="submit"]'
                ]
                
                submitted = False
                for selector in submit_selectors:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible(timeout=2000):
                            btn.scroll_into_view_if_needed()
                            time.sleep(1)
                            btn.click()
                            print(f"Clicked submit button with selector: {selector}")
                            submitted = True
                            break
                    except Exception:
                        continue

                if not submitted:
                    print("Error: Could not locate submit/preview button.")
                    return False

                time.sleep(5)
                self._safe_screenshot(page, "after_first_click.png")

                # Handle confirmation step if applicable
                current_url = page.url
                print(f"Current page URL after click: {current_url}")
                
                confirm_selectors = [
                    'input[type="submit"][value*="掲載"]',
                    'input[type="submit"][value*="登録"]',
                    'button:has-text("掲載")',
                    'button:has-text("登録")',
                    'input[value*="決定"]',
                    'input[value*="公開"]'
                ]
                
                for selector in confirm_selectors:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible(timeout=2000):
                            print(f"Found confirmation button: {selector}. Clicking to publish...")
                            btn.scroll_into_view_if_needed()
                            time.sleep(1)
                            btn.click()
                            time.sleep(5)
                            break
                    except Exception:
                        continue

                self._safe_screenshot(page, "publish_result.png")
                
                success = True
                print("Diary post completed successfully!")

        except Exception as e:
            print(f"Exception during Playwright posting: {e}")
            success = False
        finally:
            if session_path and session_path != self.session_file and os.path.exists(session_path):
                os.remove(session_path)

        return success

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
        self.last_post_type = None

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

    def _remove_overlays(self, page):
        """Removes common popups/ad overlays that might block clicking other elements."""
        try:
            page.evaluate('''() => {
                const selectors = ["#interstitial-popup", ".popup", "[id*='popup']", "[class*='popup']", ".modal", ".overlay", ".interstitial"];
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => el.remove());
                });
            }''')
            print("Removed popup/ad overlays if present.")
        except Exception as e:
            print(f"Warning: Failed to remove overlays: {e}")

    def get_draft_count(self) -> int:
        """
        楽天ブログの下書き一覧ページ（/diary/list/draft/）から現在の下書き件数を取得する。
        取得失敗時は安全のため -1 を返す。
        """
        session_path = self._prepare_session_file()
        count = -1
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-gpu"]
                )
                context_args = {
                    "viewport": {"width": 1280, "height": 800},
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                if session_path:
                    context_args["storage_state"] = session_path
                context = browser.new_context(**context_args)
                page = context.new_page()
                page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

                draft_url = "https://my.plaza.rakuten.co.jp/diary/list/draft/"
                print(f"Checking draft count from: {draft_url}")
                page.goto(draft_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)

                page_html = page.content()
                import re
                # ページャー表示（例: "1-10 / 47件" または "0件"）を抽出
                m = re.search(r'/\s*(\d+)\s*件', page_html)
                if m:
                    count = int(m.group(1))
                    print(f"Current total drafts count: {count}件")
                elif "下書き日記はありません" in page_html or "0件" in page_html:
                    count = 0
                    print("Current total drafts count: 0件")
                else:
                    # 簡易件数カウント（リスト内のアイテム数）
                    items = page.locator('ul.modList01 li').count()
                    if items > 0:
                        count = items
                        print(f"Fallback draft count (visible list items): {count}")
                browser.close()
        except Exception as e:
            print(f"Warning: Failed to fetch draft count: {e}")
        finally:
            if session_path and session_path != self.session_file and os.path.exists(session_path):
                os.remove(session_path)
        return count

    def _select_category_and_theme(self, page, category_name: str = None, theme_keyword: str = None, genre_id: str = "600"):
        """
        楽天ブログ投稿画面で「カテゴリ」と「クチコミテーマ」を適切に自動設定・選択する。
        1. カテゴリがまだ存在しない場合は /_api/category/add.json 経由で自動作成して選択。
        2. クチコミテーマは /_api/theme/list.json から関連テーマを検索して設定（見つからない場合は既存候補または代表テーマを設定）。
        """
        try:
            # --- 1. カテゴリの自動選択・追加 ---
            if category_name:
                cat_result = page.evaluate('''(catName) => {
                    try {
                        const links = Array.from(document.querySelectorAll('#ulcategorylist a.categorylist'));
                        for (const a of links) {
                            const title = (a.getAttribute('data-title') || a.textContent || '').trim();
                            if (title === catName || title.includes(catName)) {
                                const cid = a.getAttribute('data-id');
                                document.getElementById('diary_write_d_category_id').value = cid;
                                const btn = document.querySelector('.editorBlogTitle .select .btn');
                                if (btn) btn.textContent = a.getAttribute('data-title') || catName;
                                return { status: 'selected_existing', id: cid, title: title };
                            }
                        }
                        // 見つからない場合は新規カテゴリ追加APIを呼び出す
                        if (typeof window.$ !== 'undefined' && typeof token !== 'undefined') {
                            let createdId = null;
                            window.$.ajax({
                                type: "GET",
                                async: false,
                                dataType: "json",
                                contentType: "application/json",
                                url: "/_api/category/add.json",
                                headers: { "X-CSRF-Token": token },
                                data: { categoryname: catName }
                            }).done(function(res) {
                                if (res && res.response && res.response[1] && res.response[1].result) {
                                    createdId = String(res.response[1].result);
                                }
                            });
                            if (createdId) {
                                document.getElementById('diary_write_d_category_id').value = createdId;
                                const btn = document.querySelector('.editorBlogTitle .select .btn');
                                if (btn) btn.textContent = catName;
                                return { status: 'created_new', id: createdId, title: catName };
                            }
                        }
                        // フォールバック：カテゴリ未分類以外の既存カテゴリがあればそれを選択
                        for (const a of links) {
                            const cid = a.getAttribute('data-id');
                            if (cid && cid !== '0') {
                                document.getElementById('diary_write_d_category_id').value = cid;
                                const btn = document.querySelector('.editorBlogTitle .select .btn');
                                if (btn) btn.textContent = a.getAttribute('data-title');
                                return { status: 'fallback_existing', id: cid, title: a.getAttribute('data-title') };
                            }
                        }
                        return { status: 'kept_default' };
                    } catch (err) {
                        return { status: 'error', message: String(err) };
                    }
                }''', category_name)
                print(f"Category selection result: {cat_result}")

            # --- 2. クチコミテーマの自動検索・選択 ---
            search_kw = (theme_keyword or "インテリア").split()[0]
            theme_result = page.evaluate('''([kw, gId]) => {
                try {
                    // まず /_api/theme/list.json でキーワード検索を試みる
                    if (typeof window.$ !== 'undefined' && typeof token !== 'undefined') {
                        let foundTheme = null;
                        // 1回目: 指定キーワードで検索
                        window.$.ajax({
                            type: "GET",
                            async: false,
                            url: "/_api/theme/list.json",
                            dataType: "json",
                            contentType: "application/json",
                            headers: { "X-CSRF-Token": token },
                            data: { title: kw, genre: "0", page: 1 }
                        }).done(function(res) {
                            if (res && res.response && res.response[1] && res.response[1].result) {
                                const results = res.response[1].result;
                                const keys = Object.keys(results);
                                if (keys.length > 0) {
                                    foundTheme = results[keys[0]];
                                }
                            }
                        });

                        // 見つからなかった場合、ジャンル代表ワードで再検索
                        if (!foundTheme) {
                            const fallbackWord = gId === "300" ? "お取り寄せ" : (gId === "200" ? "家電" : "インテリア");
                            window.$.ajax({
                                type: "GET",
                                async: false,
                                url: "/_api/theme/list.json",
                                dataType: "json",
                                contentType: "application/json",
                                headers: { "X-CSRF-Token": token },
                                data: { title: fallbackWord, genre: "0", page: 1 }
                            }).done(function(res) {
                                if (res && res.response && res.response[1] && res.response[1].result) {
                                    const results = res.response[1].result;
                                    const keys = Object.keys(results);
                                    if (keys.length > 0) {
                                        foundTheme = results[keys[0]];
                                    }
                                }
                            });
                        }

                        if (foundTheme && foundTheme.theme_id) {
                            document.getElementById('diary_write_d_theme_id').value = String(foundTheme.theme_id);
                            document.getElementById('diary_write_d_theme_name').value = foundTheme.theme_title;
                            const wrap = document.getElementById('wrapSelectTheme');
                            if (wrap) wrap.style.display = '';
                            const tTitle = document.getElementById('theme_title');
                            if (tTitle) tTitle.textContent = foundTheme.theme_title;
                            return { status: 'selected_via_api', id: foundTheme.theme_id, title: foundTheme.theme_title };
                        }
                    }

                    // フォールバック: 画面上の theme_select_1〜4 に一致または先頭があればクリック
                    const themeLinks = Array.from(document.querySelectorAll('[id^="theme_select_"]'));
                    if (themeLinks.length > 0) {
                        for (const a of themeLinks) {
                            const tName = (a.getAttribute('data-title') || a.textContent || '').trim();
                            if (tName.includes(kw)) {
                                a.click();
                                return { status: 'clicked_preset_match', id: a.getAttribute('data-id'), title: tName };
                            }
                        }
                        // 先頭（素敵なデザインインテリア・雑貨♪ 等）を選択
                        themeLinks[0].click();
                        return {
                            status: 'clicked_first_preset',
                            id: themeLinks[0].getAttribute('data-id'),
                            title: themeLinks[0].getAttribute('data-title') || themeLinks[0].textContent
                        };
                    }

                    // 最終フォールバック: 定番テーマ「素敵なデザインインテリア・雑貨♪ (219504)」をセット
                    document.getElementById('diary_write_d_theme_id').value = '219504';
                    document.getElementById('diary_write_d_theme_name').value = '素敵なデザインインテリア・雑貨♪';
                    return { status: 'hardcoded_fallback', id: '219504', title: '素敵なデザインインテリア・雑貨♪' };
                } catch (err) {
                    return { status: 'error', message: String(err) };
                }
            }''', [search_kw, genre_id])
            print(f"Kuchikomi Theme selection result: {theme_result}")
        except Exception as e:
            print(f"Warning: Failed to set category or kuchikomi theme: {e}")

    def post_entry(self, title: str, html_content: str, post_mode: str = "draft", category_name: str = None, theme_keyword: str = None, genre_id: str = "600", allow_publish_fallback: bool = True) -> bool:
        """
        Posts a blog entry to Rakuten Blog using Playwright.
        post_mode: 'draft' (下書き保存) or 'publish' (即時公開)
        allow_publish_fallback: 下書き上限（50件）時に公開投稿へのフォールバックを許可するかどうか（1日の公開上限達成時はFalse）
        """
        session_path = self._prepare_session_file()
        success = False
        self.last_post_type = None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-gpu"]
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

                write_url = "https://my.plaza.rakuten.co.jp/diary/write/"
                print(f"Attempting direct navigation to: {write_url}")
                page.goto(write_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(5)
                
                # If direct page was not successful, or if blog_id was empty, try to resolve via homepage
                current_url = page.url
                if not write_url or "login" in current_url.lower() or "404" in page.title() or page.locator("text=404 Not Found").first.is_visible(timeout=2000):
                    print("Direct URL failed, empty, or redirected. Trying dynamic link resolution via Rakuten Blog homepage...")
                    page.goto("https://plaza.rakuten.co.jp/", wait_until="domcontentloaded", timeout=30000)
                    time.sleep(5)
                    self._remove_overlays(page)
                    
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
                        write_link.click(force=True)
                        time.sleep(5)
                    else:
                        manage_link = page.locator('a[href*="main"], a:has-text("管理ページ"), a:has-text("ブログ管理")').first
                        if manage_link.is_visible(timeout=3000):
                            print("Found 'ブログ管理' link. Clicking...")
                            manage_link.click(force=True)
                            time.sleep(5)
                            self._remove_overlays(page)
                            # Now try to find "日記を書く" on the manage page
                            sub_write_link = page.locator('a[href*="diary/write"], a:has-text("日記を書く")').first
                            if sub_write_link.is_visible(timeout=3000):
                                sub_write_link.click(force=True)
                                time.sleep(5)

                current_url = page.url
                print(f"Current URL before filling editor: {current_url}")
                if "login" in current_url.lower() or "404" in page.title():
                    print("Error: Failed to reach the diary write page.")
                    self._safe_screenshot(page, "navigation_error.png")
                    return False

                print("Checking current editor mode...")
                textarea = page.locator('textarea#diary_write_d_text, textarea[name="diary_write[d_text]"], textarea#diaryBody, textarea[name="body"]').first
                
                if textarea.is_visible(timeout=3000):
                    print("HTML editor textarea is already visible. Skipping mode toggle.")
                else:
                    print("Ensuring HTML editor mode (unchecking '見たまま編集')...")
                    try:
                        result = page.evaluate('''() => {
                            window.confirm = () => true;
                            window.alert = () => true;
                            
                            // Try finding checkbox by name/id
                            const cb = document.querySelector('input[name="mitamama"], input#mitamama, input[type="checkbox"]');
                            if (cb) {
                                if (cb.checked) {
                                    cb.checked = false;
                                    cb.dispatchEvent(new Event('click', { bubbles: true }));
                                    cb.dispatchEvent(new Event('change', { bubbles: true }));
                                    return "checkbox_unchecked_via_js";
                                }
                                return "checkbox_already_unchecked";
                            }
                            
                            // Fallback toggle via elements
                            const elements = document.querySelectorAll('button, a, span, label, input[type="button"]');
                            for (let el of elements) {
                                const text = el.textContent || el.value || "";
                                if (text.includes("見たまま") || text.includes("HTML編集")) {
                                    el.click();
                                    return "element_clicked";
                                }
                            }
                            return "not_found";
                        }''')
                        print(f"Editor mode toggle result: {result}")
                        if "unchecked" in result or "clicked" in result:
                            time.sleep(3)
                    except Exception as e:
                        print(f"Warning: Failed to toggle editor mode: {e}")

                # Wait for textarea to be visible
                try:
                    textarea.wait_for(state="visible", timeout=10000)
                    print("HTML editor textarea is now visible.")
                except Exception as e:
                    print(f"Warning: HTML editor textarea did not become visible: {e}")

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

                # 1. TinyMCE API (setContent)
                body_filled = False
                try:
                    tinymce_active = page.evaluate('''() => {
                        if (window.tinymce && window.tinymce.activeEditor) {
                            return true;
                        }
                        return false;
                    }''')
                    if tinymce_active:
                        print("TinyMCE active editor found. Setting content via TinyMCE API...")
                        page.evaluate('''(html) => {
                            window.tinymce.activeEditor.setContent(html);
                            if (typeof window.tinymce.triggerSave === 'function') {
                                window.tinymce.triggerSave();
                            } else if (window.tinymce.activeEditor.save) {
                                window.tinymce.activeEditor.save();
                            }
                        }''', html_content)
                        body_filled = True
                        print("Successfully set content via TinyMCE API and triggered save.")
                except Exception as e:
                    print(f"Warning: Failed to set content via TinyMCE API: {e}")

                # 2. Direct textarea value injection (even if hidden)
                # We always try to sync with the textareas just in case
                try:
                    textarea_selectors = [
                        'textarea#diary_write_d_text',
                        'textarea[name="diary_write[d_text]"]',
                        'textarea[name="body"]',
                        'textarea#diaryBody',
                        'textarea'
                    ]
                    for selector in textarea_selectors:
                        if page.locator(selector).count() > 0:
                            page.evaluate('''([sel, html]) => {
                                const el = document.querySelector(sel);
                                if (el) {
                                    el.value = html;
                                    el.dispatchEvent(new Event('change', { bubbles: true }));
                                    el.dispatchEvent(new Event('input', { bubbles: true }));
                                    return true;
                                }
                                return false;
                            }''', [selector, html_content])

                            print(f"Synced/filled textarea directly using selector: {selector}")
                            body_filled = True
                except Exception as e:
                    print(f"Warning: Failed to fill/sync textarea directly: {e}")

                if not body_filled:
                    print("Error: HTML editor textarea is not visible or editable. Cannot fill body.")
                    self._safe_screenshot(page, "body_fill_error.png")
                    return False

                # カテゴリとクチコミテーマを自動選択・設定
                print(f"Setting Category ({category_name}) and Kuchikomi Theme ({theme_keyword})...")
                self._select_category_and_theme(page, category_name=category_name, theme_keyword=theme_keyword, genre_id=genre_id)

                # Take screenshot of filled state
                self._safe_screenshot(page, "filled_post_draft.png")

                # Submit the post
                print(f"Submitting post (Requested Mode: {post_mode})...")
                self._remove_overlays(page)
                
                # ボタンの選択（draftモードかpublishモードか）
                draft_btn = page.locator('button#diary_write_draft_submit, input#diary_write_draft_submit, button:has-text("下書き保存")').first
                public_btn = page.locator('button#diary_write_public_submit, input#diary_write_public_submit, button:has-text("公開する")').first
                
                submit_selectors = []
                if post_mode == "publish":
                    if public_btn.is_visible(timeout=2000):
                        submit_selectors.append('button#diary_write_public_submit')
                        print("Direct '公開する' button found. Prioritizing publish.")
                else:
                    if draft_btn.is_visible(timeout=2000):
                        submit_selectors.append('button#diary_write_draft_submit')
                        print("Explicit '下書き保存' button found. Prioritizing draft save.")
                    if public_btn.is_visible(timeout=2000):
                        submit_selectors.append('button#diary_write_public_submit')
                
                submit_selectors.extend([
                    'input[type="submit"][value*="確認"]',
                    'input[type="submit"][value*="登録"]',
                    'input[type="submit"][value*="掲載"]',
                    'button:has-text("確認")',
                    'button:has-text("登録")',
                    'button:has-text("掲載")',
                    'input[type="submit"]',
                    'button[type="submit"]'
                ])
                
                submitted = False
                for selector in submit_selectors:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible(timeout=2000):
                            btn.scroll_into_view_if_needed()
                            time.sleep(1)
                            btn.click(force=True)
                            print(f"Clicked submit button with selector: {selector}")
                            submitted = True
                            break
                    except Exception:
                        continue

                if not submitted:
                    print("Error: Could not locate submit/preview button.")
                    return False

                # フォーム送信・画面遷移が落ち着くまで待機
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                except Exception:
                    pass
                time.sleep(6)
                self._safe_screenshot(page, "after_first_click.png")

                # Handle confirmation step if applicable
                current_url = page.url
                print(f"Current page URL after click: {current_url}")
                self._remove_overlays(page)
                
                # 下書き上限エラーの検知と公開への自動フォールバック
                page_text = page.locator('body').inner_text()
                if "保存できる下書きの件数は50件までです" in page_text:
                    if allow_publish_fallback:
                        print("⚠️ 楽天ブログの下書き上限（50件）に到達したため、自動的に「公開する」ボタンを押して投稿を完遂します...")
                        fallback_public_btn = page.locator('button#diary_write_public_submit, input#diary_write_public_submit, button:has-text("公開する")').first
                        if fallback_public_btn.is_visible(timeout=3000):
                            fallback_public_btn.scroll_into_view_if_needed()
                            time.sleep(1)
                            fallback_public_btn.click(force=True)
                            print("Clicked '公開する' button as draft limit fallback.")
                            self.last_post_type = "publish"
                            try:
                                page.wait_for_load_state("domcontentloaded", timeout=15000)
                            except Exception:
                                pass
                            time.sleep(6)
                            current_url = page.url
                    else:
                        print("⚠️ 下書き上限（50件）に到達しましたが、本日の公開上限（23件）に達しているため公開へのフォールバックは停止します。")
                        return False
                elif post_mode == "publish":
                    self.last_post_type = "publish"
                else:
                    self.last_post_type = "draft"
                
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
                            btn.click(force=True)
                            try:
                                page.wait_for_load_state("domcontentloaded", timeout=15000)
                            except Exception:
                                pass
                            time.sleep(6)
                            break
                    except Exception:
                        continue

                self._safe_screenshot(page, "publish_result.png")
                
                # STRICT VALIDATION: Check if save or publish succeeded
                # The page should show success messages like "下書き保存が完了しました" or "日記の投稿が完了しました" or "公開しました"
                page_content = page.content()
                success_keywords = ["完了しました", "保存しました", "公開しました", "投稿しました", "続けて下書きを修正する", "下書き一覧", "日記一覧"]
                
                if any(kw in page_content for kw in success_keywords):
                    success = True
                    print("Diary post completed successfully (confirmed by UI message)!")
                else:
                    # Look for potential error messages on the page
                    error_msg = page.locator('.error, .error-msg, .alert-danger, .err_msg').first
                    if error_msg.is_visible(timeout=2000):
                        print(f"Error detected on page: {error_msg.text_content().strip()}")
                    else:
                        # ページ内のテキストを一部ログ出力してデバッグしやすくする
                        body_snippet = page.locator('body').inner_text()[:400].replace('\n', ' ')
                        print(f"Notice: Success keyword not explicitly matched. Page body snippet: {body_snippet}")
                        # URLが変わっているか、あるいはフォーム送信後にエラーが表示されていなければ成功と判定
                        if "write" not in current_url or "success" in current_url.lower():
                            success = True
                            print("Diary post treated as successful based on navigation change.")
                        else:
                            success = False

        except Exception as e:
            print(f"Exception during Playwright posting: {e}")
            success = False
        finally:
            if session_path and session_path != self.session_file and os.path.exists(session_path):
                os.remove(session_path)

        return success


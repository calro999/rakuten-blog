import os
import re
import requests
import json
import time
import urllib.parse
from typing import Dict, Any, Optional

class ArticleGenerator:
    def __init__(self, model_id: str = ""):
        pass

    def load_model(self):
        print("ArticleGenerator: Initialized using online APIs (Gemini / fallback).")

    def generate_review_article(self, item: Dict[str, Any]) -> str:
        title = item.get("title", "")
        clean_title = item.get("clean_title", title)
        price = item.get("price", "")
        caption = item.get("caption", "")

        prompt = f"""あなたは「日々の暮らしを整え、日常をワンランク快適にするインテリア・生活雑貨」を紹介する大人気の女性ライフスタイルブロガーです。
以下の楽天市場の商品情報を元に、読者（お部屋をおしゃれにしたい、QOLを上げたい方）に向けて親しみやすく魅力的なブログ記事を執筆してください。

【商品名】: {title}
【価格】: {price}
【商品の説明】: {caption}

【出力の構成ルール（厳格遵守）】:
① 記事のタイトルを <h2> タグで囲んで出力してください。（例：【QOL爆上がり】置くだけでお部屋がおしゃれになる「○○」が凄すぎる…！ など、ブログ読者が思わずクリックしたくなるタイトル）
② 冒頭のあいさつと導入（「こんにちは！おしゃれな暮らしに憧れるブロガーのjackです♪」から始め、この商品を取り入れることで「毎日の生活がどう便利になるか」「日々のQOL（生活の質）がどう向上するか」を、読者に語りかけるように優しく2〜3行で書いてください）。
③ 「### お部屋に馴染むデザインと確かな実用性」といったブログの見出し（<h3>タグ）を書き、その下に商品の特徴やデザインの良さ、実際の使い心地を200〜300文字程度で語りかけるように詳しく書いてください。
④ 「### 読者が特に注目すべき3つのポイント」という見出し（<h3>タグ）を書き、その下に必ず <ul> と <li> タグを使った【3つの魅力的な箇条書き】を書いてください。
⑤ 最後に「毎日の暮らしをちょっと特別にしてくれる素敵なアイテムです。人気商品なのでぜひ早めにチェックしてみてくださいね！」といった、ブログの結びの挨拶と購入を後押しする言葉を書いてください。

【執筆の厳格なルール】:
1. 出力はブログの【本文HTMLのみ】にしてください。余計な挨拶（「はい、以下が記事です」など）は絶対に1文字も含めないでください。
2. ブログらしい親しみやすい語り口調（「〜ですね！」「〜です♪」など）で統一してください。
3. スマホで読みやすいように、重要な部分やアピールポイントは適宜 <b> タグで囲んで太字に強調してください。
4. すべてHTMLタグを使用して整形した状態で出力してください（Markdown記法ではなく直接HTMLタグを使用すること）。
"""

        generators = [
            ("Gemini API (Free Tier)", self._generate_with_gemini),
            ("GitHub Models API (Free for Actions/PAT)", self._generate_with_github_models),
            ("OpenRouter Free API", self._generate_with_openrouter),
            ("Hugging Face API (Free Tier)", self._generate_with_huggingface),
            ("Pollinations AI Free (No Key Required)", self._generate_with_pollinations),
        ]

        raw_article = None
        for name, gen_fn in generators:
            try:
                print(f"Attempting article generation with {name}...")
                res = gen_fn(prompt)
                if res and len(res.strip()) > 150:
                    raw_article = res.strip()
                    print(f"Successfully generated article using {name}!")
                    break
                else:
                    print(f"{name} returned empty or too short response. Trying next fallback...")
            except Exception as e:
                print(f"Error calling {name}: {e}. Trying next fallback...")

        if not raw_article:
            print("WARNING: All LLM APIs failed or are rate-limited. Generating fallback HTML review text.")
            raw_article = f"""<h2>【QOL爆上がり】お部屋に置くだけでおしゃれ空間に♪毎日の暮らしが楽しくなる「{clean_title}」が素敵すぎる！</h2>
<p>こんにちは！おしゃれな暮らしに憧れるライフスタイルブロガーのjackです♪ 忙しい毎日の中で、おうち時間を少しでも快適で心地よいものにしたいって思いますよね。今回ご紹介する<b>{clean_title}</b>は、そんな日々の暮らしをワンランク贅沢にしてくれて、あなたの<b>QOL（生活の質）を劇的に向上させてくれる</b>こと間違いなしの大注目アイテムです！</p>
<h3>お部屋に馴染むデザインと確かな実用性</h3>
<p>このアイテムは、洗練されたナチュラルなデザインと実用性を兼ね備えていて、お部屋のインテリアにしっくり馴染んでくれます。置いておくだけで空間全体の雰囲気をモダンかつ温かみのあるものに引き上げてくれるんです。使い心地の良さはもちろん、細部の仕上げまでこだわり抜かれていて、毎日使うのが本当に嬉しくなりますね！</p>
<h3>読者が特に注目すべき3つのポイント</h3>
<ul>
  <li><b>洗練されたモダンデザイン</b>：置くだけでお部屋がおしゃれカフェのような空間に早変わりする美しいビジュアル♪</li>
  <li><b>圧倒的な使い心地の良さ</b>：日常使いにストレスを感じさせない、機能的で優れたデザイン！</li>
  <li><b>長く愛せる確かな品質</b>：厳選された素材を使用し、耐久性と安全性をしっかり両立しています。</li>
</ul>
<p>毎日の暮らしをちょっと特別にしてくれる素敵なアイテムです。人気商品なのでぜひ早めにお買い物カゴへ入れてチェックしてみてくださいね！</p>"""

        # メタ文言のクリーニング
        raw_article = re.sub(r"^(はい、|承知いたしました。|以下が商品紹介記事です。|以下に記事を出力します。|以下が執筆した記事です。)\s*", "", raw_article)
        meta_markers = ["以上のように", "このように、", "アフィリエイトリンクへの"]
        for marker in meta_markers:
            if marker in raw_article:
                raw_article = raw_article.split(marker)[0].rstrip()

        def add_target_blank(match):
            tag = match.group(0)
            if 'target=' not in tag:
                tag = tag.replace('<a ', '<a target="_blank" rel="noopener noreferrer" ')
            return tag
            
        html_output = re.sub(r'<a\s+[^>]*>', add_target_blank, raw_article)
        return html_output

    def _generate_with_gemini(self, prompt: str) -> Optional[str]:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{
                    "text": "あなたはライフスタイルブログのプロ編集者です。指示された厳格なルールを遵守し、余計な挨拶や解説を一切含まないHTML本文のみを出力します。\n\n" + prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2000
            }
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except KeyError:
                return None
        return None

    def _generate_with_github_models(self, prompt: str) -> Optional[str]:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token:
            return None
        
        url = "https://models.inference.ai.azure.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "あなたはライフスタイルブログのプロ編集者です。指示されたルールを厳格に守り、日本語で前置き・後書きなしでHTML本文のみを出力してください。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            try:
                return resp.json()["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                return None
        return None

    def _generate_with_openrouter(self, prompt: str) -> Optional[str]:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return None
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "google/gemma-2-9b-it:free",
            "messages": [
                {"role": "system", "content": "あなたはライフスタイルブログのプロ編集者です。指示された厳格なルールを守り、余計な解説を一切含まない日本語のHTML本文のみを出力します。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            try:
                return data["choices"][0]["message"]["content"]
            except KeyError:
                return None
        return None

    def _generate_with_huggingface(self, prompt: str) -> Optional[str]:
        api_key = os.environ.get("HF_API_KEY") or os.environ.get("HF_TOKEN")
        if not api_key:
            return None
        
        model_id = "Qwen/Qwen2.5-72B-Instruct"
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": f"<|im_start|>system\nあなたはライフスタイルブログのプロ編集者です。日本語で余計な前置きや後書きなしに、HTML本文のみを出力します。<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n",
            "parameters": {
                "max_new_tokens": 1500,
                "temperature": 0.7
            }
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=45)
        if resp.status_code == 200:
            data = resp.json()
            try:
                text = data[0]["generated_text"]
                if "assistant\n" in text:
                    return text.split("assistant\n")[-1]
                return text
            except (KeyError, IndexError):
                return None
        return None

    def _generate_with_pollinations(self, prompt: str) -> Optional[str]:
        url = "https://text.pollinations.ai/"
        models = ["openai", "qwen", "mistral"]
        
        for attempt, model in enumerate(models):
            payload = {
                "messages": [
                    {"role": "system", "content": "あなたはライフスタイルブログのプロ編集者です。指示されたルールを厳格に守り、日本語で前置き・後書きなしでHTML本文のみを出力してください。"},
                    {"role": "user", "content": prompt}
                ],
                "model": model
            }
            try:
                resp = requests.post(url, json=payload, timeout=25)
                if resp.status_code == 200 and len(resp.text.strip()) > 150:
                    return resp.text
                elif resp.status_code == 429:
                    time.sleep(attempt+2)
            except Exception:
                pass
            
        return None

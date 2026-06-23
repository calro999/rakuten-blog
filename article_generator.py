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

        prompt = f"""以下の楽天市場の商品情報を元に、その商品の魅力、どう生活に影響を与えるか、QOL（生活の質）をどう高めるかを強力に売り込むための紹介テキストを作成してください。
【商品名】: {title}
【価格】: {price}
【商品の説明】: {caption}

【出力ルール（厳格遵守）】:
1. 余計なタグ（<div>, <h3>, <ul>, <li>など）は一切使用しないでください。
2. 構成は、見出しを使わず、数個のシンプルな段落（<p>タグ）のみで記述してください。
3. 冒頭の「こんにちは！ブロガーの・・・」のような自己紹介や挨拶は完全に排除し、最初から商品のメリットや生活への好影響をアピールする文章から始めてください。
4. スマホで読みやすいように、重要な部分やアピールポイントは適宜 <b> タグで囲んで太字に強調してください。
5. 出力は紹介テキストの【本文HTMLのみ】にし、前置きやMarkdown（```html など）は一切含めないでください。
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
            raw_article = f"""<p>毎日の暮らしを整え、日常をワンランク快適にする<b>{clean_title}</b>のご紹介です。このアイテムを取り入れることで、おうち時間が劇的に快適になり、日々のQOL（生活の質）が向上します。</p>
<p>洗練されたデザインと優れた実用性を兼ね備えており、お部屋の雰囲気を引き上げながら日常の利便性を高めてくれます。使い心地の良さはもちろん、細部までこだわり抜かれているため、毎日の生活に欠かせないお気に入りのアイテムになること間違いなしです。</p>"""

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

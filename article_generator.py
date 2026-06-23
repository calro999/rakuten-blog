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

        prompt = f"""あなたは「日常を豊かにするインテリア・生活雑貨」を提案する、プロのライフスタイルブロガー・紹介記事編集者です。
以下の楽天市場の商品情報を元に、読者に向けた詳細で魅力的な紹介ブログ記事を執筆してください。

【商品名】: {title}
【価格】: {price}
【商品の説明】: {caption}

【出力の構成ルール（厳格遵守）】:
① 記事のタイトル（【QOL向上】や【インテリア】などの魅力的なフック＋商品名）を <h2> タグで囲んで出力してください。
② 記事の導入（冒頭）として、この商品を使うことで「日々の暮らしがどう便利になるか」「どんな風にQOL（生活の質）が向上するのか」を、さりげなく、かつ魅力的に2〜3行（150文字程度）で書いてください。
③ 商品の詳しい特徴や使い心地、デザインの魅力について、200〜300文字程度で詳細な解説を書いてください。
④ コレクターや愛好家、購入検討者が特に注目すべきポイントを、必ず <ul> と <li> タグを使った【3つの箇条書き】にして説明してください。
⑤ 最後に「毎日の暮らしをワンランク引き上げてくれる人気アイテムですので、完売する前にお早めにチェックしてみてください！」といった、購入を後押しする結びの言葉を書いてください。

【執筆の厳格なルール】:
1. 出力はブログの【本文HTMLのみ】にしてください。余計な挨拶や解説（「はい、以下が記事です」など）は絶対に1文字も含めないでください。
2. スマホで読みやすいように、重要な部分やアピールポイントは適宜 <b> タグで囲んで太字に強調してください。
3. すべてHTMLタグを使用して整形した状態で出力してください（Markdown記法ではなく直接HTMLタグを使用すること）。
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
            raw_article = f"""<h2>【QOL向上】毎日の暮らしを豊かに彩る「{clean_title}」をご紹介！</h2>
<p>忙しい毎日の中で、ふと心が安らぐ瞬間や、家事がスムーズに進む便利さを感じたことはありませんか？今回ご紹介する<b>{clean_title}</b>は、そんな日常のちょっとした瞬間をワンランク贅沢にし、あなたの<b>QOL（生活の質）を劇的に向上させてくれる</b>大注目のアイテムです。</p>
<p>このアイテムは、洗練されたデザインと実用性を兼ね備えており、お部屋のインテリアにしっくりと馴染みながら、生活空間全体の雰囲気をモダンかつ温かみのあるものにクラスアップしてくれます。使い心地の良さはもちろん、細部の仕上げまでこだわり抜かれており、所有する喜びを感じさせてくれる逸品です。</p>
<ul>
  <li><b>洗練されたモダンデザイン</b>：置くだけでお部屋がおしゃれ空間に早変わりする美しいビジュアル！</li>
  <li><b>圧倒的な使いやすさ</b>：日常使いにストレスを感じさせない、人間工学に基づいた優れた機能性！</li>
  <li><b>安心のハイクオリティ</b>：長く愛用できる厳選された素材を使用し、高い耐久性を実現！</li>
</ul>
<p><b>毎日の暮らしをワンランク引き上げてくれる人気アイテムですので、完売する前にお早めにチェックしてみてください！</b></p>"""

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

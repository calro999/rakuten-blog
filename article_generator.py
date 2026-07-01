import os
import re
import requests
import json
import time
import random
import urllib.parse
from typing import Dict, Any, Optional

class ArticleGenerator:
    def __init__(self, model_id: str = ""):
        pass

    def load_model(self):
        print("ArticleGenerator: Initialized using online APIs (Gemini / fallback).")

    def generate_review_article(self, item: Dict[str, Any]) -> str:
        title = item.get("title", "")
        search_keyword = item.get("search_keyword", "")
        clean_title = self.get_clean_product_name(title, search_keyword)
        price = item.get("price", "")
        caption = item.get("caption", "")

        prompt = f"""以下の楽天市場の商品情報を元に、その商品の具体的な特徴、デザインの魅力、そして暮らしの中でどのように活躍するかを自然かつ魅力的に紹介するブログ用テキストを作成してください。
【商品名】: {title}
【価格】: {price}
【商品の説明】: {caption}

【出力ルール（厳格遵守）】:
1. 余計なタグ（<div>, <h3>, <ul>, <li>など）は一切使用しないでください。
2. 構成は、見出しを使わず、数個のシンプルな段落（<p>タグ）のみで記述してください。
3. 冒頭の「こんにちは！ブロガーの・・・」のような自己紹介や挨拶は完全に排除し、最初から商品のメリットや生活への好影響をアピールする文章から始めてください。
4. スマホで読みやすいように、重要な部分やアピールポイントは適宜 <b> タグで囲んで太字に強調してください。
5. 出力は紹介テキストの【本文HTMLのみ】にし、前置きやMarkdown（```html など）は一切含めないでください。
6. 「QOL爆上がり」「生活の質」などの誇張した表現や定型表現は避け、商品の素材感や使い心地、デザイン性を具体的に掘り下げて自然な日本語で表現してください。
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
            raw_article = f"""<p>毎日の暮らしにそっと寄り添い、日常をワンランク快適にしてくれる<b>{clean_title}</b>のご紹介です。このアイテムをお部屋に取り入れることで、おうち時間がグッと心地よくなり、日々の暮らしに嬉しいゆとりが生まれます。</p>
<p>洗練された佇まいと実用性を兼ね備えており、空間の雰囲気を引き締めながら日常の利便性をしっかりサポート。デザインの美しさはもちろん、細部まで使い勝手を考慮して作られているため、毎日の定番アイテムとして長く愛用できる仕上がりとなっています。</p>"""

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

    def generate_blog_title(self, item: Dict[str, Any]) -> str:
        title = item.get("title", "")
        search_keyword = item.get("search_keyword", "")
        clean_title = self.get_clean_product_name(title, search_keyword)
        caption = item.get("caption", "")

        system_prompt = "あなたは読者の目を引き、クリック率（CTR）を最大化するブログ記事タイトルを作成するプロのコピーライターです。日本語で、余計な説明や前置きなしにタイトルテキストのみを出力してください。"

        prompt = f"""以下の商品情報を元に、クリック率（CTR）が高く、読者が思わずクリックしたくなるような魅力的なブログ記事タイトルを1つだけ生成してください。

【商品名】: {clean_title}
【商品説明】: {caption}

【生成ルール（厳格遵守）】:
1. 最も伝えたい商品の具体的なメリットやデザインの魅力（例：お部屋がおしゃれに片付く、温もりを感じる天然木、すっきりスマートに収納、など）をタイトルの一番最初に書いてください。
2. 紹介する「具体的な商品名（例：珪藻土バスマット、壁掛け時計、アロマディフューザーなど、何を紹介しているのかがはっきりわかる言葉）」を必ずタイトルに含めてください。商品名が抜けているタイトルは絶対にNGです。
3. 文字数は30文字以内とし、長くなりすぎないようにしてください。
4. 「QOL爆上がり」「生活の質」「QOL向上」などの定型表現や過度な売り込み言葉は絶対に使わないでください。自然で上品な表現を心がけてください。
5. HTMLタグ（<h2>など）やマークダウン記法、引用符（「」や【】、" など）は一切含めず、プレーンテキストのみで出力してください。
6. 出力はタイトルのみとし、前置きや解説などは一切含めないでください。
"""
        generators = [
            ("Gemini API (Free Tier)", self._generate_with_gemini),
            ("GitHub Models API (Free for Actions/PAT)", self._generate_with_github_models),
            ("OpenRouter Free API", self._generate_with_openrouter),
            ("Hugging Face API (Free Tier)", self._generate_with_huggingface),
            ("Pollinations AI Free (No Key Required)", self._generate_with_pollinations),
        ]

        for name, gen_fn in generators:
            try:
                res = gen_fn(prompt, system_prompt=system_prompt)
                if res and len(res.strip()) > 3:
                    clean_res = re.sub(r'<[^>]+>|[\"\'「」『』【】]', '', res).strip()
                    if clean_res:
                        return clean_res[:40]
            except Exception as e:
                print(f"Error in {name} during title generation: {e}")
                continue

        # --- フォールバックロジック (LLMが全滅した場合) ---
        # 1. 検索キーワードから修飾語（北欧、おしゃれ等）を取り除き、クリーンなカテゴリ名を作る
        clean_keyword = search_keyword
        for modifier in [
            "北欧", "おしゃれ", "モダン", "静音", "洗える", "来客用", "分別", 
            "LED", "木製", "ガラス", "フェイク", "グリーン", "収納", "インテリア", "雑貨"
        ]:
            clean_keyword = clean_keyword.replace(modifier, "")
        clean_keyword = re.sub(r'\s+', ' ', clean_keyword).strip()

        # 2. 商品タイトルから記号・ノイズを徹底的に除去し、商品名らしき部分を切り出す
        short_title = clean_title
        short_title = re.sub(r'【[^】]+】|\[[^\]]+\]|（[^）]+）|\([^\)]+\)', '', short_title)
        
        noise_words = [
            "送料無料", "ポイント消化", "マラソン開催中", "マラソン", "全11種類", "日本製", "国産", 
            "公式", "限定", "あす楽", "即納", "スーパーSALE", "お買い物マラソン", "最大1000円OFF", "クーポン",
            "プチプラ", "新生活", "おしゃれ", "かわいい", "シンプル", "北欧", "モダン", "レトロ", "デザイン",
            "おすすめ", "人気", "大容量", "便利", "実用性", "機能的", "軽量", "静音", "洗える", "来客用",
            "光触媒", "CT触媒", "消臭", "抗菌", "防臭", "全20種", "20種"
        ]
        for noise in noise_words:
            short_title = short_title.replace(noise, "")
            
        short_title = re.sub(r'\s+', ' ', short_title).strip()
        
        # スペースで分割して最初の2単語を結合（具体的な商品名を狙う）
        words = [w for w in short_title.split(' ') if w]
        selected_words = []
        char_count = 0
        for w in words:
            # 記号や短いサイズ表記・型番などをスキップ
            if re.match(r'^[a-zA-Z0-9_\-\.\/]+$', w) and len(w) <= 3:
                continue
            if len(selected_words) >= 2 or char_count + len(w) > 20:
                break
            selected_words.append(w)
            char_count += len(w) + 1
            
        product_name = " ".join(selected_words).strip()
        
        # 3. 抽出した製品名に販促用ノイズ（「倍」「%」「OFF」「割引」「円」「エントリー」「対象」など）や
        # 数字と記号の組み合わせが含まれている場合は、その抽出結果を捨てて、クリーンな検索キーワードを商品名とする
        promo_patterns = [
            r'倍', r'%', r'％', r'OFF', r'off', r'割引', r'円', r'エントリー', r'対象', 
            r'\+', r'\d+L', r'\d+l', r'\d+リットル', r'\d+分別', r'\d+種', r'最大'
        ]
        is_invalid_product = False
        if product_name:
            for pattern in promo_patterns:
                if re.search(pattern, product_name):
                    is_invalid_product = True
                    break
        
        if is_invalid_product or not product_name:
            product_name = clean_keyword or "おすすめアイテム"

        # 4. 嘘のレビュー（「使ってみた感想」など）を含まない、事実ベースの自然なタイトル
        fallback_patterns = [
            f"おうち時間を快適にする「{product_name}」の魅力と機能性のまとめ",
            f"暮らしをもっと心地よく！「{product_name}」を取り入れたお部屋作りのアイデア",
            f"実用性と美しさを備えた「{product_name}」の注目ポイントを解説",
            f"お部屋の雰囲気を整える「{product_name}」の上手な取り入れ方"
        ]
        return random.choice(fallback_patterns)

    def get_clean_product_name(self, title: str, search_keyword: str) -> str:
        """楽天市場のノイズが多い商品名から、具体的でシンプルな商品名（15文字以内）を抽出する。"""
        system_prompt = "あなたは入力されたテキストから無駄な修飾語を取り除き、商品名そのもの（名詞）のみを抽出する優秀なアシスタントです。"
        prompt = f"""以下の楽天市場の商品名から、送料無料、サイズ、型番、アピール用の形容詞（おしゃれ、大人気など）をすべて排除し、その商品が「何であるか」を示す具体的でクリーンな商品名（例：『木枠ウォールミラー』『珪藻土バスマット』『分別ゴミ箱』など）を日本語で15文字以内で抽出してください。
余計な解説や括弧、引用符、Markdown等は一切含めず、抽出した商品名テキストのみを出力してください。

【楽天市場の商品名】: {title}
【検索時のキーワード】: {search_keyword}
"""
        generators = [
            ("Gemini API (Free Tier)", self._generate_with_gemini),
            ("GitHub Models API (Free for Actions/PAT)", self._generate_with_github_models),
            ("OpenRouter Free API", self._generate_with_openrouter),
            ("Hugging Face API (Free Tier)", self._generate_with_huggingface),
            ("Pollinations AI Free (No Key Required)", self._generate_with_pollinations),
        ]

        for name, gen_fn in generators:
            try:
                res = gen_fn(prompt, system_prompt=system_prompt)
                if res and len(res.strip()) > 1:
                    cleaned = re.sub(r'<[^>]+>|[\"\'「」『』【】]', '', res).strip()
                    if cleaned and len(cleaned) <= 18:
                        return cleaned
            except Exception:
                continue

        # --- フォールバック (LLMが全滅した場合のルールベース抽出) ---
        clean_title = title
        clean_title = re.sub(r'【[^】]+】|\[[^\]]+\]|（[^）]+）|\([^\)]+\)', '', clean_title)
        
        noise_words = [
            "送料無料", "ポイント", "マラソン", "セール", "あす楽", "即納", "公式", "限定", 
            "国産", "日本製", "新生活", "おしゃれ", "かわいい", "シンプル", "北欧", "モダン", 
            "おすすめ", "人気", "大容量", "便利", "軽量", "防臭", "抗菌", "消臭", "プチプラ",
            "スーパーSALE", "お買い物マラソン", "割引", "クーポン", "対象", "％OFF"
        ]
        for noise in noise_words:
            clean_title = clean_title.replace(noise, "")
            
        clean_title = re.sub(r'[^a-zA-Z0-9あ-んア-ン一-龠\s\-]', '', clean_title)
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        
        words = [w for w in clean_title.split(' ') if w]
        selected_words = []
        char_count = 0
        for w in words:
            if re.match(r'^[a-zA-Z0-9_\-\.\/]+$', w) and len(w) <= 3:
                continue
            if len(selected_words) >= 2 or char_count + len(w) > 15:
                break
            selected_words.append(w)
            char_count += len(w) + 1
            
        product_name = " ".join(selected_words).strip()
        if not product_name or len(product_name) < 2:
            product_name = search_keyword or "インテリア雑貨"
            
        return product_name[:15]

    def _generate_with_gemini(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        
        sys_msg = system_prompt or "あなたはライフスタイルブログのプロ編集者です。指示された厳格なルールを遵守し、余計な挨拶や解説を一切含まないHTML本文のみを出力します。"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{
                    "text": sys_msg + "\n\n" + prompt
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

    def _generate_with_github_models(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token:
            return None
        
        sys_msg = system_prompt or "あなたはライフスタイルブログのプロ編集者です。指示されたルールを厳格に守り、日本語で前置き・後書きなしでHTML本文のみを出力してください。"
        url = "https://models.inference.ai.azure.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": sys_msg},
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

    def _generate_with_openrouter(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return None
        
        sys_msg = system_prompt or "あなたはライフスタイルブログのプロ編集者です。指示された厳格なルールを守り、余計な解説を一切含まない日本語のHTML本文のみを出力します。"
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "google/gemma-2-9b-it:free",
            "messages": [
                {"role": "system", "content": sys_msg},
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

    def _generate_with_huggingface(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        api_key = os.environ.get("HF_API_KEY") or os.environ.get("HF_TOKEN")
        if not api_key:
            return None
        
        sys_msg = system_prompt or "あなたはライフスタイルブログのプロ編集者です。日本語で余計な前置きや後書きなしに、HTML本文のみを出力します。"
        model_id = "Qwen/Qwen2.5-72B-Instruct"
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": f"<|im_start|>system\n{sys_msg}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n",
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

    def _generate_with_pollinations(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        url = "https://text.pollinations.ai/"
        models = ["openai", "qwen", "mistral"]
        
        sys_msg = system_prompt or "あなたはライフスタイルブログのプロ編集者です。指示されたルールを厳格に守り、日本語で前置き・後書きなしでHTML本文のみを出力してください。"
        for attempt, model in enumerate(models):
            payload = {
                "messages": [
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": prompt}
                ],
                "model": model
            }
            try:
                resp = requests.post(url, json=payload, timeout=25)
                if resp.status_code == 200 and len(resp.text.strip()) > 5:
                    return resp.text
                elif resp.status_code == 429:
                    time.sleep(attempt+2)
            except Exception:
                pass
            
        return None

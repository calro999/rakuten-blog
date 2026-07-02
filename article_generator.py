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

    def _detect_genre(self, title: str, search_keyword: str) -> str:
        text = (title + " " + search_keyword).lower()
        if "ふるさと納税" in text:
            return "furusato"
        if any(w in text for w in ["スイーツ", "菓子", "プリン", "ケーキ", "チョコ", "クッキー", "バウムクーヘン", "大福", "どら焼き", "カステラ", "マカロン", "ジェラート", "アイス"]):
            return "sweets"
        if any(w in text for w in ["食器", "プレート", "急須", "コップ", "マグカップ", "グラス", "皿", "箸", "カトラリー", "キャニスター", "ボウル"]):
            return "tableware"
        if any(w in text for w in ["ラグ", "カーテン", "クッション", "テーブル", "ライト", "ランプ", "ミラー", "鏡", "時計", "収納", "スツール", "棚", "ソファー", "照明", "傘立て", "ハンガー"]):
            return "interior"
        return "general"

    def _generate_fallback_article(self, clean_title: str, search_keyword: str, caption: str) -> str:
        genre = self._detect_genre(clean_title, search_keyword)
        
        # 各ジャンルごとに3パターンの自然な文章テンプレートを用意（AI臭さを排除）
        templates = {
            "furusato": [
                f"""<p>地域の魅力やこだわりがぎゅっと詰まった、ふるさと納税の返礼品<b>{clean_title}</b>のご紹介です。丹精込めて作られた特別な一品を、ご自宅で贅沢に楽しむことができます。</p>
<p>寄付を通じてその土地を応援しながら、普段の生活にちょっとしたご褒美やワクワク感をプラスできるのが嬉しいポイント。実用的なアイテムから美味しいグルメまで、地域の想いを感じられる確かな品質の仕上がりです。</p>""",
                f"""<p>ふるさと納税の返礼品として高い支持を集める<b>{clean_title}</b>。地域の職人や生産者のこだわりが細部まで行き届いた、非常に完成度の高いアイテムです。</p>
<p>寄付の返礼として受け取れるだけでなく、長く愛用したくなる実用性と品質をしっかり備えています。ご家族みんなで楽しむのにも、自分への特別なご褒美としても、自信を持っておすすめできる一品です。</p>""",
                f"""<p>日常の食卓や暮らしに嬉しい彩りを与えてくれる、ふるさと納税の返礼品<b>{clean_title}</b>。その地域ならではの素材や技術がふんだんに使われています。</p>
<p>ふるさと納税をきっかけに、知らなかった地域の魅力に出会えるのも醍醐味の一つ。毎日の定番として重宝する使い勝手の良さがあり、寄付先との温かい繋がりを感じさせてくれる仕上がりです。</p>"""
            ],
            "sweets": [
                f"""<p>ひとくち食べれば心がふっと軽くなるような、贅沢な味わいの<b>{clean_title}</b>のご紹介です。厳選された素材を贅沢に使い、丁寧な製法で上品に仕上げられています。</p>
<p>おやつの時間やお茶の席に添えるだけで、テーブルの上が一気に華やぐ魅力的な一品。自分へのご褒美にはもちろん、お世話になっている方へのギフトや手土産としても喜ばれること間違いなしの上質な仕上がりです。</p>""",
                f"""<p>素材の持ち味や香りを存分に引き出した、極上の<b>{clean_title}</b>。濃厚な味わいと口溶けの良さが際立っており、一口ごとに満足感が広がります。</p>
<p>お好みのコーヒーや紅茶と一緒にいただくことで、ゆったりとした贅沢なティータイムを演出。見た目にも美しく仕上がっており、日常のちょっとしたひとときを特別に変えてくれるデザートです。</p>""",
                f"""<p>甘い香りと優しい食感で、大人から子どもまでみんなを笑顔にしてくれる<b>{clean_title}</b>。丁寧な手仕事が感じられる、こだわりのスイーツです。</p>
<p>甘さのバランスが絶妙でしつこくなく、ついついもう一口と手が伸びてしまう美味しさ。個包装やパッケージのデザインにもこだわっているため、贈り物としても非常に人気のある逸品です。</p>"""
            ],
            "tableware": [
                f"""<p>お料理をいっそう美味しそうに引き立ててくれる、美しい佇まいの器<b>{clean_title}</b>のご紹介です。手になじむ質感と、料理が映える絶妙な色彩が魅力です。</p>
<p>和食にも洋食にも合わせやすい万能なデザインで、朝食からディナーまで幅広いシーンの食卓で大活躍。見た目の美しさだけでなく、洗いやすさや収納のしやすさといった実用面もしっかり考慮されています。</p>""",
                f"""<p>食卓の雰囲気を優しく整えてくれる、上品なデザインの<b>{clean_title}</b>。シンプルながらも職人の丁寧な仕事が光る仕上がりとなっています。</p>
<p>普段使いにはもちろん、大切な来客時のおもてなしにもぴったりな上品さを兼ね備えています。乗せる料理を選ばず、いつものメニューがまるでお店のワンプレートのように上品に仕上がります。</p>""",
                f"""<p>毎日の食事の時間をより豊かで楽しいものにしてくれる、こだわりの器<b>{clean_title}</b>。しっかりとした厚みと程よい重みがあり、使い勝手は抜群です。</p>
<p>手作りならではの温かみのある表情があり、使うほどに愛着がわいていく魅力があります。電子レンジや食洗機に対応しているなど、現代のライフスタイルに寄り添った設計も大きなポイントです。</p>"""
            ],
            "interior": [
                f"""<p>空間の雰囲気をすっきりと整え、居心地の良いお部屋づくりをサポートしてくれる<b>{clean_title}</b>のご紹介です。洗練されたフォルムで、どんなインテリアにもしっくり馴染みます。</p>
<p>目立ちすぎず主張しすぎない程よい存在感があり、置くだけでその場所がおしゃれにまとまるのが特徴。素材の風合いを生かした美しい質感で、お気に入りの空間をより素敵に見せてくれるアイテムです。</p>""",
                f"""<p>無駄のないスマートなフォルムと、高い実用性を兼ね備えた<b>{clean_title}</b>。毎日の整理整頓や収納を、よりスムーズで快適なものにしてくれます。</p>
<p>お部屋のテイストを問わず合わせやすいナチュラルな色合いで、インテリアの統一感を損ないません。細部のパーツまで丁寧に加工されており、長く安心して愛用できるしっかりとした頑丈なつくりです。</p>""",
                f"""<p>温かみのある佇まいで、お部屋に優しいニュアンスをプラスしてくれる<b>{clean_title}</b>。機能性と意匠性を高いレベルで両立させた注目のアイテムです。</p>
<p>限られたスペースでもすっきりと収まるサイズ設計になっており、玄関やリビング、寝室など様々な場所で使えます。日々の暮らしの動線に優しく溶け込み、お家の中を整然としたクリーンな印象に仕上げます。</p>"""
            ],
            "general": [
                f"""<p>使い手のことを考えて細部まで丁寧に作り込まれた<b>{clean_title}</b>のご紹介です。使い勝手の良いシンプルな形状と、飽きのこないニュートラルな質感が特徴です。</p>
<p>毎日の何気ない作業や暮らしのワンシーンにそっと寄り添い、確実な機能性でしっかり支えてくれます。どんな環境にも自然と溶け込むため、ご自身の定番アイテムとして長く活躍してくれる仕上がりです。</p>""",
                f"""<p>機能性と美しいフォルムを兼ね備え、実用的なツールとして非常に優秀な<b>{clean_title}</b>。軽やかな使い心地と扱いやすさが大きな魅力です。</p>
<p>実際に手に取ってみると、つくりの良さや素材のこだわりが随所に感じられ、確かな安心感があります。面倒な手間を減らし、日々の生活をより軽快でスムーズにするための工夫が凝らされた製品です。</p>""",
                f"""<p>シンプルでありながら存在感があり、道具としての美しさが光る<b>{clean_title}</b>。無駄な装飾を削ぎ落としたスタイリッシュなデザインです。</p>
<p>頑丈なつくりで日々のハードな使用にも十分に耐えうる仕様になっており、実用性重視の方にも自信を持っておすすめできます。毎日の暮らしをそっと支えてくれる頼もしい相棒のような存在です。</p>"""
            ]
        }
        
        # 選択されたジャンルのテンプレートからランダムで1つ選ぶ
        selected_template = random.choice(templates.get(genre, templates["general"]))
        return selected_template

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
            for retry_count in range(2):
                try:
                    print(f"Attempting article generation with {name} (Attempt {retry_count + 1})...")
                    res = gen_fn(prompt)
                    if res and len(res.strip()) > 150:
                        raw_article = res.strip()
                        print(f"Successfully generated article using {name}!")
                        break
                    else:
                        print(f"{name} returned empty or too short response.")
                except Exception as e:
                    print(f"Error calling {name}: {e}.")
                
                if retry_count == 0:
                    time.sleep(2)
            if raw_article:
                break
            else:
                print(f"{name} failed after retries. Trying next fallback...")

        if not raw_article:
            print("WARNING: All LLM APIs failed or are rate-limited. Generating fallback HTML review text.")
            raw_article = self._generate_fallback_article(clean_title, search_keyword, caption)

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

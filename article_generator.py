import os

# Force flush all prints for real-time logging in CI/GitHub Actions
import builtins
print = lambda *args, **kwargs: builtins.print(*args, flush=True, **kwargs)

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
        """
        LLMが一時的に利用できない場合でも、固定テンプレートやキーワード決め打ち（アートパネルに鍵が出る等の誤爆）を
        完全に排除し、実際の商品説明（caption）とタイトルから固有の文章・スペックを抽出して自然なレビューを構築する。
        """
        # 商品説明（caption）からノイズを除去し、意味のある文を抽出
        clean_cap = re.sub(r'https?://\S+|【[^】]*】|\[[^\]]*\]', '', caption)
        sentences = [s.strip() for s in re.split(r'[。！!？?\n\r]+', clean_cap) if len(s.strip()) >= 8]
        
        # 商品説明から抽出できた特徴文（最大3つ）
        useful_sentences = []
        for s in sentences:
            if not any(ban in s for ban in ["送料無料", "あす楽", "レビュー", "クーポン", "ポイント", "ショップ", "問い合わせ", "返品", "交換"]):
                useful_sentences.append(s)
            if len(useful_sentences) >= 3:
                break

        # 1. 冒頭の導入（商品名に完全に合わせた自然な語り口・「ます」連続を回避）
        openers = [
            f"<p>お部屋の模様替えや日々の暮らしのちょっとした見直しに、手軽に取り入れられると人気を集めている<b>{clean_title}</b>。実際に使ってみると、写真以上に満足度が高くて驚くアイテムの一つ。</p>",
            f"<p>「ずっと気になっていたけれど、もっと早く買えばよかった…！」と思わせてくれるのが、今回ご紹介する<b>{clean_title}</b>。日々の暮らしにしっくり馴染んでくれます。</p>",
            f"<p>普段の暮らしの中で、ちょっとした不便を感じたり、空間の雰囲気をガラリと変えたいときにぴったりな<b>{clean_title}</b>。使い勝手とデザインのバランスが絶妙な一品。</p>"
        ]
        p1 = random.choice(openers)

        # 2. 商品説明から抽出したリアルな特徴・スペック
        spec_bullets = []
        if useful_sentences:
            for s in useful_sentences:
                spec_bullets.append(f"・{s}")
            specs_text = "<br>".join(spec_bullets)
            p2 = f"<p><b>■ 実際にチェックしておきたい推しポイント</b><br>{specs_text}</p>"
        else:
            p2 = f"<p><b>■ 実際に使って感じた魅力</b><br>・無駄のない洗練されたデザインで、どんなお部屋のテイストにも自然にマッチ<br>・日々の扱いやすさやお手入れのしやすさもしっかり考慮された親切設計<br>・届いたその日からすぐに活躍してくれる実用性の高さ</p>"

        # 3. 本音の注意点と生活の変化（体言止めや自然な口調を織り交ぜる）
        closers = [
            f"<p>事前に設置スペースやサイズの確認だけはおすすめしますが、日々の使いやすさは抜群。お気に入りのアイテムが一つ加わるだけで、毎日過ごす空間がぐっと愛おしく感じられるようになりますよ。</p>",
            f"<p>購入前にサイズ感やお部屋のレイアウトをイメージしておくと失敗知らず。いつもの生活動線にすっきり溶け込み、心地よい暮らしのリズムを整えてくれる心強い味方です。</p>",
            f"<p>使う場所の寸法はあらかじめ測っておくのが安心ですが、実用性の高さと見た目の良さは文句なし。日々の暮らしのクオリティをさりげなく引き上げてくれる優秀なアイテム。</p>"
        ]
        p3 = random.choice(closers)

        return f"{p1}\n{p2}\n{p3}"

    def generate_dynamic_cta(self, clean_title: str, search_keyword: str, caption: str, affiliate_url: str) -> str:
        """
        商品のジャンルや特性（食品・インテリア・家電・ふるさと納税など）に合わせて
        読者が思わずタップしたくなる最適な訴求文言（サイズ/カラー/賞味期限/仕様等）を動的に生成する。
        """
        text_corpus = (clean_title + " " + search_keyword + " " + caption).lower()

        if "ふるさと納税" in text_corpus:
            sub_text = "＼ 寄附金額・お届け時期・口コミをチェック ／"
            btn_text = f"【楽天市場】{clean_title}（ふるさと納税）の詳細を見る"
        elif any(w in text_corpus for w in ["スイーツ", "ケーキ", "チョコ", "プリン", "菓子", "食品", "グルメ", "肉", "米", "フルーツ"]):
            sub_text = "＼ 内容量・賞味期限・ギフト包装対応をチェック ／"
            btn_text = f"【楽天市場】{clean_title}の口コミ・詳細を見る"
        elif any(w in text_corpus for w in ["家電", "ライト", "照明", "ランプ", "時計", "加湿器", "コードレス", "扇風機", "ヒーター"]):
            sub_text = "＼ スペック詳細・電気代・保証内容をチェック ／"
            btn_text = f"【楽天市場】{clean_title}の仕様・詳細を見る"
        elif any(w in text_corpus for w in ["食器", "マグカップ", "プレート", "グラス", "ポット", "フライパン", "包丁"]):
            sub_text = "＼ 食洗機対応・サイズ・セット内容をチェック ／"
            btn_text = f"【楽天市場】{clean_title}の詳細・レビューを見る"
        elif any(w in text_corpus for w in ["家具", "テーブル", "チェスト", "ラック", "ワゴン", "ソファー", "チェア", "ラグ", "カーテン", "収納"]):
            sub_text = "＼ 詳しいサイズ展開・カラーバリエーションをチェック ／"
            btn_text = f"【楽天市場】{clean_title}の詳細・在庫を見る"
        else:
            sub_text = "＼ セール情報・詳しい仕様・カラー展開をチェック ／"
            btn_text = f"【楽天市場】{clean_title}の詳細・レビューを見る"

        return (
            f'<p style="margin: 24px 0 16px 0; text-align: center;">\n'
            f'  <span style="font-size: 0.95em; color: #555;">{sub_text}</span><br>\n'
            f'  <a href="{affiliate_url}" target="_blank" rel="noopener noreferrer" style="display: inline-block; margin-top: 6px; font-weight: bold; font-size: 1.05em; color: #bf0000; text-decoration: underline;">\n'
            f'    {btn_text}\n'
            f'  </a>\n'
            f'</p>'
        )

    def generate_review_article(self, item: Dict[str, Any]) -> str:
        title = item.get("title", "")
        search_keyword = item.get("search_keyword", "")
        clean_title = self.get_clean_product_name(title, search_keyword)
        price = item.get("price", "")
        caption = item.get("caption", "")

        prompt = f"""あなたは「本当に良いものを自分の言葉で本音レビューする人気の暮らしブロガー」です。
以下の楽天市場の商品情報を徹底的に読み込み、定型文や使い回しのテンプレート感を完全に排除して、この商品「だけ」にしかない魅力・スペック・使い勝手を熱量たっぷりに語るオリジナルのレビュー記事（HTML本文のみ）を作成してください。

【商品名】: {title}
【クリーン商品名】: {clean_title}
【価格】: {price}
【商品の説明】: {caption}
【検索キーワード】: {search_keyword}

【最重要執筆ルール（成約率CVR最大化＆完全脱テンプレ）】:
1. 【「〜〜です」「〜〜ます」の連続を禁止（自然なブログのリズム）】:
   語尾がすべて「〜〜です」「〜〜ます」で終わる機械的なAI文章は厳禁です。
   「〜〜なのが嬉しいポイント」「〜〜のも助かります」「〜〜な使い心地」「〜〜ですよね」「〜〜してみてほしい一品」など、適度に体言止めや共感・感想を織り交ぜ、血の通った自然な日本語で執筆してください。

2. 【テンプレ構文・定型句の完全禁止】:
   「そんな日常のプチストレスを解消してくれるのが〜」「実際に使って便利だと感じるポイントは〜」「日々の暮らしをより快適に整えたい方は〜」「いかがでしょうか」などの決まりきったAI構文・テンプレート表現は絶対に禁止です。
   記事ごとに冒頭の切り口、語り口、展開を商品に合わせてガラリと変えてください。

3. 【商品説明（caption）にある「その商品固有の情報」を必ず3つ以上深掘り】:
   商品タイトルや説明文から、その商品固有のディテール（寸法・素材名・耐荷重・カラー・取り付け方法・個包装・賞味期限・静音性など）を具体的に取り上げてください。
   ※アートパネルなら壁の雰囲気やサイズ・飾りやすさ、スイーツなら味や食感・日持ち、家具なら配置場所や収納力など、商品に100%合致した内容のみを書いてください。他の商品の特徴（アートパネルに鍵など）を絶対に混ぜないでください。

4. 【本音の注意点やリアルな使用感（1点）】:
   メリットばかりを並べず、「サイズは事前に測っておくのがおすすめ」「重いものは下段に入れると安定する」「賞味期限は短めなので注意」など、購入前に知っておきたいリアルなポイントに触れることで、読者からの強い信頼を得てください。

5. 【フォーマット】:
   ・シンプルな段落（<p>タグ）3〜4つで構成してください。
   ・スマホで流し読みしても重要なスペックやメリットが目に飛び込んでくるよう、要所を <b> タグで太字にしてください。
   ・見出しタグ（<h1>〜<h3>）や <div>, <ul>, <li> は使わず、<p>タグのみの本文HTMLを出力してください。
"""

        # 呼び出しフロー: 各種APIをフォールバックとして順に実行
        api_flow = [
            ("Gemini API (Free Tier) - 1回目", self._generate_with_gemini),
            ("OpenRouter Free API - 1回目", self._generate_with_openrouter),
            ("GitHub Models API - 1回目", self._generate_with_github_models),
            ("HuggingFace API - 1回目", self._generate_with_huggingface),
            ("Pollinations AI (ポリゴンGPT) - 1回目", self._generate_with_pollinations),
            ("Gemini API (Free Tier) - 2回目", self._generate_with_gemini),
            ("OpenRouter Free API - 2回目", self._generate_with_openrouter),
            ("Pollinations AI (ポリゴンGPT) - 2回目", self._generate_with_pollinations),
        ]

        raw_article = None
        error_logs = []
        
        for name, gen_fn in api_flow:
            try:
                print(f"Attempting article generation with {name}...")
                res = gen_fn(prompt)
                if res and len(res.strip()) > 150:
                    raw_article = res.strip()
                    print(f"Successfully generated article using {name}!")
                    break
                else:
                    msg = f"【{name}】空の応答、または150文字未満の短い文章が返されました。"
                    print(msg)
                    error_logs.append(msg)
            except Exception as e:
                msg = f"【{name}】呼び出し処理中にエラーが発生しました: {str(e)}"
                print(msg)
                error_logs.append(msg)
            
            # APIの連続アクセスによる拒否を避けるために待機
            # time.sleep(2)
            pass

        if not raw_article:
            print("Warning: All online LLM APIs failed. Falling back to rich local template generation.")
            clean_title = item.get("clean_title") or self.get_clean_product_name(title, search_keyword)
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

        system_prompt = "あなたは読者の目を引き、クリック率（CTR）と検索流入（SEO）を最大化するブログ記事タイトルを作成するプロのコピーライターです。読者の日常の悩み解決や具体的なベネフィットを伝え、日本語で余計な説明なしにタイトルテキストのみを出力してください。"

        prompt = f"""以下の商品情報を元に、読者の悩み解決や生活の変化がひと目でわかり、思わずクリックしたくなる魅力的なブログ記事タイトルを1つだけ生成してください。

【商品名】: {clean_title}
【商品説明】: {caption}
【検索キーワード】: {search_keyword}

【タイトル作成ルール（厳格遵守）】:
1. 【悩み解決・ベネフィット】: 「朝の鍵探しがゼロに」「賃貸でも壁を傷つけない」「玄関がすっきり片付く」「カフェ風のおしゃれ空間に」など、読者の日常の困りごとを解決する具体的なメリットや変化をタイトルに盛り込んでください。
2. 【商品名の明記】: 検索流入（SEO）のため、「{clean_title}」または「{search_keyword}」に含まれる主要名詞（例：木製キーフック、珪藻土バスマット等）を必ずタイトルに含めてください。
3. 【文字数】: スマホ画面で一目で読めるよう、25〜35文字程度に収めてください。
4. 【禁止事項】: 「QOL爆上がり」「生活の質」「おすすめ商品」などの陳腐な表現、記号の多用（【】や『』、「」など）は避け、自然で魅力的な日本語にしてください。
5. 【出力フォーマット】: 余計な前置きや解説は一切含めず、タイトル文字列のみを出力してください。
"""
        # 呼び出しフロー: 各種APIをフォールバックとして順に実行
        api_flow = [
            ("Gemini API (Free Tier) - 1回目", self._generate_with_gemini),
            ("OpenRouter Free API - 1回目", self._generate_with_openrouter),
            ("GitHub Models API - 1回目", self._generate_with_github_models),
            ("HuggingFace API - 1回目", self._generate_with_huggingface),
            ("Pollinations AI (ポリゴンGPT) - 1回目", self._generate_with_pollinations),
            ("Gemini API (Free Tier) - 2回目", self._generate_with_gemini),
            ("OpenRouter Free API - 2回目", self._generate_with_openrouter),
            ("Pollinations AI (ポリゴンGPT) - 2回目", self._generate_with_pollinations),
        ]

        error_logs = []
        for name, gen_fn in api_flow:
            try:
                print(f"Attempting title generation with {name}...")
                res = gen_fn(prompt, system_prompt=system_prompt)
                if res and len(res.strip()) > 3:
                    clean_res = re.sub(r'<[^>]+>|[\"\'「」『』【】]', '', res).strip()
                    if clean_res:
                        return clean_res[:40]
                else:
                    msg = f"【{name}】空または3文字未満の短いタイトルが返されました。"
                    print(msg)
                    error_logs.append(msg)
            except Exception as e:
                msg = f"【{name}】タイトル生成中にエラーが発生しました: {str(e)}"
                print(msg)
                error_logs.append(msg)
            
            # time.sleep(2)
            pass

        print("Warning: All online LLM APIs failed for title. Falling back to local title generation.")
        fallback_titles = [
            f"朝のバタバタ解消！賃貸でも使える {clean_title}",
            f"散らかる悩みをスッキリ解決！注目の {clean_title}",
            f"置くだけでお部屋が垢抜ける！実力派 {clean_title}",
            f"毎日のプチストレスがゼロに！大満足の {clean_title}"
        ]
        return random.choice(fallback_titles)[:35]

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
        # 1. 検索キーワードから「ふるさと納税」や「ストレート」等のノイズを除去して優先的に商品名として採用する
        clean_keyword = search_keyword or ""
        for term in ["ふるさと納税", "ふるさと", "ストレート", "通販", "人気", "おすすめ", "ギフト", "訳あり", "ランキング", "おしゃれ", "北欧", "分別", "スリム"]:
            clean_keyword = clean_keyword.replace(term, "")
        clean_keyword = re.sub(r'\s+', ' ', clean_keyword).strip()

        if clean_keyword and len(clean_keyword) >= 2:
            return clean_keyword[:15]

        # 2. キーワードが使えない場合のみ、タイトルから抽出を試みる
        clean_title = title
        clean_title = re.sub(r'【[^】]+】|\[[^\]]+\]|（[^）]+）|\([^\)]+\)', '', clean_title)
        
        noise_words = [
            "送料無料", "ポイント", "マラソン", "セール", "あす楽", "即納", "公式", "限定", 
            "国産", "日本製", "新生活", "おしゃれ", "かわいい", "シンプル", "北欧", "モダン", 
            "おすすめ", "人気", "大容量", "便利", "軽量", "防臭", "抗菌", "消臭", "プチプラ",
            "スーパーSALE", "お買い物マラソン", "割引", "クーポン", "対象", "％OFF",
            "ふるさと納税", "ふるさと", "カートン", "カトン", "ガイアの夜明け", "で紹介", "すぐ届く"
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
            product_name = clean_keyword or "おすすめアイテム"
            
        return product_name[:15]

    def _translate_error_message(self, name: str, status_code: int, response_text: str) -> str:
        """APIのエラーレスポンスを分かりやすい日本語に翻訳・解説する"""
        if status_code == 401:
            if "models" in response_text:
                return f"【{name}】認証エラー(401): GITHUB_TOKEN のモデル使用権限（models permission）が不足しています。明示的に作成したパーソナルアクセストークン（PAT）が必要です。"
            return f"【{name}】認証エラー(401): APIキーが無効であるか、正しく設定されていません。環境変数（GEMINI_API_KEYなど）の値を確認してください。"
        elif status_code == 403:
            return f"【{name}】アクセス拒否エラー(403): サービスへのアクセスが拒否されました。APIキーの権限やプラン制限を確認してください。"
        elif status_code == 429:
            return f"【{name}】リクエスト上限エラー(429): 無料枠または利用制限（レートリミット）に達しました。しばらく時間（数十秒〜数分）をおいてからタスクを再実行してください。"
        elif status_code in [500, 502, 503]:
            return f"【{name}】サーバーエラー({status_code}): AI服务側のサーバーが混雑しているか、メンテナンス中です。時間をおいて再実行してください。"
        else:
            return f"【{name}】通信エラー({status_code}): レスポンス内容: {response_text}"

    def _generate_with_gemini(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("DEBUG: 【Gemini API】GEMINI_API_KEY が環境変数に設定されていません。")
            return None
        
        sys_msg = system_prompt or "あなたは読者の日常の悩みに寄り添い、商品のリアルな使い心地・具体的なメリット・注意点を本音で伝える凄腕の暮らしブロガーです。AI特有の抽象的な美辞麗句（「彫刻のような〜」「暮らしを豊かに」等）や説明書のような機械的表現は完全に排除し、自然で説得力のある日本語のHTML本文のみを出力します。"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
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
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except KeyError:
                    print("DEBUG: 【Gemini API】ステータスは200ですが、想定外のレスポンス形式が返されました。")
                    return None
            else:
                err_msg = self._translate_error_message("Gemini API", resp.status_code, resp.text)
                print(f"DEBUG: {err_msg}")
        except Exception as e:
            print(f"DEBUG: 【Gemini API】呼び出し中に通信エラーが発生しました: {e}")
        return None

    def _generate_with_github_models(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token:
            print("DEBUG: GITHUB_TOKEN or GH_TOKEN is not set in environment variables.")
            return None
        print(f"DEBUG: GITHUB_TOKEN/GH_TOKEN is set (length: {len(token)}).")
        
        sys_msg = system_prompt or "あなたは読者の日常の悩みに寄り添い、商品のリアルな使い心地・具体的なメリット・注意点を本音で伝える凄腕の暮らしブロガーです。AI特有の抽象的な美辞麗句や説明書のような機械的表現は完全に排除し、自然で説得力のある日本語のHTML本文のみを出力します。"
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
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                try:
                    return resp.json()["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    print("DEBUG: GitHub Models API returned status 200 but response format was unexpected.")
                    return None
            else:
                print(f"DEBUG: GitHub Models API HTTP error. status_code={resp.status_code}, response={resp.text}")
        except Exception as e:
            print(f"DEBUG: Exception during GitHub Models API call: {e}")
        return None

    def _generate_with_openrouter(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print("DEBUG: 【OpenRouter API】OPENROUTER_API_KEY が環境変数に設定されていません。")
            return None
        
        sys_msg = system_prompt or "あなたは読者の日常の悩みに寄り添い、商品のリアルな使い心地・具体的なメリット・注意点を本音で伝える凄腕の暮らしブロガーです。AI特有の抽象的な美辞麗句や説明書のような機械的表現は完全に排除し、自然で説得力のある日本語のHTML本文のみを出力します。"
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        models = [
            "meta-llama/llama-3.3-70b-instruct:free",
            "qwen/qwen-2.5-72b-instruct:free",
            "openrouter/free"
        ]
        
        for model in models:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            try:
                print(f"DEBUG: 【OpenRouter API】Using model: {model}")
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        content = data["choices"][0]["message"]["content"]
                        if content and len(content.strip()) > 5:
                            return content
                    except KeyError:
                        print(f"DEBUG: 【OpenRouter API】Model {model} returned status 200 but response format was unexpected.")
                else:
                    err_msg = self._translate_error_message(f"OpenRouter API ({model})", resp.status_code, resp.text)
                    print(f"DEBUG: {err_msg}")
            except Exception as e:
                print(f"DEBUG: 【OpenRouter API ({model})】呼び出し中に通信エラーが発生しました: {e}")
        return None


    def _generate_with_huggingface(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        api_key = os.environ.get("HF_API_KEY") or os.environ.get("HF_TOKEN")
        if not api_key:
            return None
        
        sys_msg = system_prompt or "あなたは読者の日常の悩みに寄り添い、商品のリアルな使い心地・具体的なメリット・注意点を本音で伝える凄腕の暮らしブロガーです。AI特有の抽象的な美辞麗句や説明書のような機械的表現は完全に排除し、自然で説得力のある日本語のHTML本文のみを出力します。"
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
        return None
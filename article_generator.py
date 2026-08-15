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
        LLMが一時的に利用できない場合でも、固定テンプレートの使い回しを完全に排除し、
        商品のキーワード・説明文・特徴から動的にリアルなレビュー文を構築する。
        """
        text_corpus = (clean_title + " " + search_keyword + " " + caption).lower()
        
        # 1. アイテム特性の判定と日常の悩み（あるある）の動的選定
        hook_text = ""
        benefit_text = ""
        concern_text = ""
        
        if any(w in text_corpus for w in ["キーフック", "鍵", "玄関"]):
            hook_text = "出かける直前の忙しい時間に「あれ？ 家の鍵どこ置いたっけ…」と玄関で焦って探し回った経験はありませんか？ 靴を履いてから鍵がないことに気づいてリビングに戻るバタバタは、朝の大きなストレスになりますよね。"
            benefit_text = "帰宅した瞬間に「鍵を戻す定位置」が決まるだけで、朝の探し物ストレスがゼロになり、玄関周りもすっきりと垢抜けた印象に整います。"
            concern_text = "重すぎるバッグなどをかけるのには向きませんが、車のスマートキーや家の鍵、折りたたみ傘程度ならしっかりと安定して支えてくれます。"
        elif any(w in text_corpus for w in ["バスマット", "珪藻土"]):
            hook_text = "お風呂上がりにビチャビチャに濡れたバスマットを踏んで、冷やっとした不快感を覚えたことはありませんか？ 家族が続けて入浴するとマットが乾かず、洗濯の手間もかかってプチストレスになりがちです。"
            benefit_text = "濡れた足裏を乗せた瞬間にスーッと水分を吸い取ってくれるため、いつでもサラサラで清潔な使い心地をキープでき、毎日の洗濯の手間からも解放されます。"
            concern_text = "定期的に陰干しやお手入れをする必要がありますが、普段は立てかけておくだけでカビやニオイを防げるので管理はとても手軽です。"
        elif any(w in text_corpus for w in ["ゴミ箱", "ダストボックス", "分別"]):
            hook_text = "お部屋の中でゴミ箱が生活感丸出しになっていたり、分別用のゴミ箱でキッチンの動線が狭くなってイライラした経験はありませんか？"
            benefit_text = "限られたスペースを有効活用しながらスマートに分別でき、お部屋の生活感をすっきりと隠して清潔感のある空間をつくれます。"
            concern_text = "容量には限りがあるため大量のゴミを溜め込む用途には向きませんが、日々の生活ゴミをこまめにまとめて清潔を保つのに最適なサイズ感です。"
        elif any(w in text_corpus for w in ["ミラー", "鏡"]):
            hook_text = "お出かけ前の身だしなみチェックで、部屋の照明や角度のせいでメイクや服装のバランスが確認しづらいと感じたことはありませんか？"
            benefit_text = "自然な光を取り込みながら顔周りや全体のシルエットをクリアに映し出し、毎朝のスタイリングやメイクの時間がぐっとスムーズになります。"
            concern_text = "ガラス製品のため設置場所の選定や取り扱いには少し配慮が必要ですが、フレームのしっかりとした構造で安定感があります。"
        elif any(w in text_corpus for w in ["時計", "クロック"]):
            hook_text = "ふと時間を確認したいときに文字盤が見づらかったり、寝室で時計の秒針の「カチカチ音」が気になって眠れなくなった経験はありませんか？"
            benefit_text = "静音設計でリラックスした時間を邪魔せず、視認性の高い美しい文字盤がインテリアの程よいアクセントとして空間を引き締めてくれます。"
            concern_text = "電池交換などの定期的なメンテナンスは必要ですが、無駄な装飾がないためどんなお部屋にも自然に馴染みます。"
        elif any(w in text_corpus for w in ["照明", "ライト", "ランプ"]):
            hook_text = "夜のリラックスタイムに、部屋のメイン照明が明るすぎて目が冴えてしまったり、なんとなく落ち着かないと感じることはありませんか？"
            benefit_text = "柔らかく温かみのある灯りが空間全体を優しく包み込み、一日の終わりにほっと一息つける極上のリラックス空間を演出してくれます。"
            concern_text = "メインの作業用照明としては少し光量が控えめですが、間接照明やベッドサイドのムード作りにはこれ以上ない心地よさです。"
        elif any(w in text_corpus for w in ["スイーツ", "ケーキ", "チョコ", "プリン", "菓子", "焼き菓子"]):
            hook_text = "仕事や家事で疲れた日の終わりに、「今日はおいしいものを食べて自分を労いたい…」と思う瞬間はありませんか？"
            benefit_text = "ひとくち食べるだけで素材本来の豊かな風味と上品な甘みが口いっぱいに広がり、頑張った自分への最高のご褒美時間を楽しめます。"
            concern_text = "賞味期限や保存方法（要冷蔵・要冷凍など）には気をつける必要がありますが、個包装で少しずつ大切に味わえるのも魅力です。"
        else:
            hook_text = f"日々の暮らしの中で「もっとここがスッキリ片付けばいいのに」「お部屋の雰囲気を手軽に変えたい」と感じる場面はありませんか？"
            benefit_text = f"毎日の生活動線に無理なく溶け込みながら、使いやすさと見た目の美しさを両立し、心地よい暮らしのリズムを整えてくれます。"
            concern_text = "設置場所や用途に合わせたサイズ確認は事前におすすめしますが、日々の実用性とデザイン性のバランスは抜群です。"

        # 2. 設置方法・素材・スペックの動的抽出
        features = []
        if any(w in text_corpus for w in ["マグネット", "磁石"]):
            features.append("<b>マグネット式</b>で玄関ドアやスチール面にピタッと貼るだけなので、賃貸でも壁を傷つけず工具不要で届いたその日から使えます。")
        elif any(w in text_corpus for w in ["ピン", "画鋲", "穴が目立たない"]):
            features.append("細いピンで固定できる仕様のため、<b>賃貸の壁でも穴が目立ちにくく</b>安心して取り付けられます。")
        elif any(w in text_corpus for w in ["完成品", "組み立て不要"]):
            features.append("面倒な組み立て作業が不要な<b>完成品</b>で届くため、箱を開けてすぐに設置できるのも嬉しいポイントです。")

        if any(w in text_corpus for w in ["天然木", "ウッド", "ウォールナット", "オーク", "無垢"]):
            features.append("安っぽいプラスチック製とは異なり、<b>天然木の温もりある質感</b>がお部屋の雰囲気をぐっと上品に格上げしてくれます。")
        elif any(w in text_corpus for w in ["真鍮", "ブラス"]):
            features.append("使うほどに味わいが増す<b>真鍮の上品な輝き</b>が、お部屋に洗練された大人のアクセントを加えてくれます。")
        elif any(w in text_corpus for w in ["陶器", "セラミック"]):
            features.append("職人の手仕事を感じさせる<b>陶器ならではの柔らかな表情</b>が、食卓や空間に優しい温もりを添えてくれます。")

        if any(w in text_corpus for w in ["トレイ", "トレー", "小物置き", "印鑑", "ペン"]):
            features.append("小物を置ける<b>専用トレイ</b>が付いているため、宅配便用の印鑑やペン、サングラスなども一緒にまとめてすっきり管理できます。")
        elif any(w in text_corpus for w in ["スリム", "省スペース", "コンパクト"]):
            features.append("場所を取らない<b>省スペース設計</b>なので、一人暮らしのワンルームや限られたスペースにもすっきりと収まります。")

        # 抽出できた特徴文を結合（最低でも2つの特徴を確保）
        if not features:
            features.append(f"無駄を削ぎ落としたシンプルなデザインで、どんなテイストのインテリアにも自然に馴染む<b>高い汎用性と実用性</b>を備えています。")
            features.append("毎日の扱いやすさを考慮した丁寧な設計で、お手入れもサッと拭くだけで簡単です。")
        elif len(features) == 1:
            features.append("シンプルで落ち着いたデザインなので、飽きが来ず長く愛用できる仕上がりになっています。")

        feature_html = " ".join(features)

        # 3. 記事本文の段落組み立て
        p1 = f"<p>{hook_text} そんな日常のプチストレスをすっきりと解消してくれるのが、今回ご紹介する<b>{clean_title}</b>です。</p>"
        p2 = f"<p>実際に注目したいポイントは、{feature_html}</p>"
        p3 = f"<p>{concern_text} {benefit_text}</p>"
        p4 = f"<p>日々の暮らしをより快適に整えたい方は、ぜひチェックしてみてはいかがでしょうか。</p>"

        return f"{p1}\n{p2}\n{p3}\n{p4}"

    def generate_review_article(self, item: Dict[str, Any]) -> str:
        title = item.get("title", "")
        search_keyword = item.get("search_keyword", "")
        clean_title = self.get_clean_product_name(title, search_keyword)
        price = item.get("price", "")
        caption = item.get("caption", "")

        prompt = f"""以下の楽天市場の商品情報（タイトル・価格・商品説明）を徹底的に読み込み、読者が「まさにこれが欲しかった！」と購入したくなる、リアルで説得力のあるブログレビュー記事（HTML本文のみ）を作成してください。

【商品名】: {title}
【クリーン商品名】: {clean_title}
【価格】: {price}
【商品の説明】: {caption}
【検索キーワード】: {search_keyword}

【記事の構成ルール（必ずこの流れで執筆してください）】:
1. 【共感導入（日常のあるある・お悩み）から開始】:
   冒頭の挨拶（「こんにちは」など）や自己紹介は一切不要です。いきなり読者の日常の悩みや「あるある」の困りごとから始めてください。
   （例：「出かける直前、鍵がどこにもなくて遅刻しそうになった経験はありませんか？」「賃貸だから壁に穴を開けられないと諦めていませんか？」など、商品に応じたリアルな悩み）
2. 【不安の先回り解消＆具体的なスペック・特徴】:
   商品説明から「取り付け方法（マグネット式/ピン/両面テープ/完成品など）」「素材（天然木/オーク/スチール/陶器など）」「機能（フック数、小物置きトレイ、印鑑・ペン置き、コード穴、静音など）」を具体的に取り上げ、賃貸でも使えるか、組み立ては簡単かなどの購入前の不安を解消してください。
3. 【本音感を生むデメリット・注意点（あえて1点記載）】:
   「重すぎる荷物には向かないが鍵や小物ならびくともしない」「サイズがコンパクトなため大型アイテムは置けないが玄関にはジャストサイズ」など、リアルな注意点を1点書くことでレビューの信頼性を高めてください。
4. 【買った後の快適な未来（具体的な生活の変化）】:
   「帰宅した瞬間に定位置へ戻すだけで朝の探し物ストレスがゼロになった」「荷物の受け取りがスムーズになった」など、手に入れた後の快適な暮らしを具体的に見せて締めくくってください。

【表現・出力ルール（厳格遵守）】:
・抽象的な美辞麗句（「彫刻のような佇まい」「日々の生活をより豊かで丁寧なものへ」「至福のひととき」など）は禁止。
・「QOL爆上がり」「生活の質向上」などの陳腐な定型句は避け、自分の言葉で体験したかのような自然な日本語で書いてください。
・見出しタグ（<h1>〜<h3>）や <div>, <ul>, <li> などの複雑なタグは使わず、シンプルな段落（<p>タグ）のみで構成してください。
・読者がスマホで流し読みしても要点が伝わるよう、重要なポイントやメリットは適宜 <b> タグで太字強調してください。
・出力は紹介テキストの【<p>タグで構成された本文HTMLのみ】とし、前置きやMarkdown（```html など）は一切含めないでください。
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
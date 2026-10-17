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

    def _detect_genre(self, title: str, search_keyword: str, caption: str = "") -> str:
        text = (title + " " + search_keyword + " " + caption).lower()
        if "ふるさと納税" in text:
            return "furusato"
        if any(w in text for w in ["スイーツ", "和菓子", "洋菓子", "菓子", "プリン", "ケーキ", "チョコ", "クッキー", "バウムクーヘン", "大福", "どら焼き", "カステラ", "マカロン", "ジェラート", "アイス", "パイ", "饅頭", "タルト", "ロールケーキ"]):
            return "sweets"
        if any(w in text for w in ["肉", "牛", "豚", "鶏", "米", "フルーツ", "果物", "海鮮", "カニ", "エビ", "魚", "グルメ", "惣菜", "ハンバーグ", "餃子", "うどん", "ラーメン"]):
            return "food"
        if any(w in text for w in ["家電", "ライト", "照明", "ランプ", "時計", "加湿器", "コードレス", "扇風機", "ヒーター", "ドライヤー", "スピーカー"]):
            return "appliance"
        if any(w in text for w in ["食器", "プレート", "急須", "コップ", "マグカップ", "グラス", "皿", "箸", "カトラリー", "キャニスター", "ボウル", "フライパン", "鍋", "包丁"]):
            return "kitchen"
        if any(w in text for w in ["家具", "テーブル", "チェスト", "ラック", "ワゴン", "ソファー", "チェア", "ラグ", "カーテン", "収納", "棚", "スツール", "ミラー", "鏡", "アートパネル", "ポスター", "ハンガー", "傘立て"]):
            return "interior"
        return "general"



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

    def _call_llm_with_retries(self, prompt: str, system_prompt: Optional[str] = None, min_length: int = 100, task_name: str = "Generation", item_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Gemini（動的自動検出モデル）、OpenRouter（最新無料モデル群）、GitHub Models、HuggingFaceの
        複数のAIプロバイダを順次自動切替しながら、成功するまで粘り強く再試行する。
        """
        api_flow = [
            ("Gemini API (Auto-Discovered)", lambda p, s: self._generate_with_gemini(p, s)),
            ("OpenRouter (qwen-2.5-coder-32b:free)", lambda p, s: self._generate_with_openrouter(p, s, model_name="qwen/qwen-2.5-coder-32b-instruct:free")),
            ("OpenRouter (mistral-7b:free)", lambda p, s: self._generate_with_openrouter(p, s, model_name="mistralai/mistral-7b-instruct:free")),
            ("OpenRouter (gemma-2-9b:free)", lambda p, s: self._generate_with_openrouter(p, s, model_name="google/gemma-2-9b-it:free")),
            ("OpenRouter (llama-3-8b:free)", lambda p, s: self._generate_with_openrouter(p, s, model_name="meta-llama/llama-3-8b-instruct:free")),
            ("OpenRouter (zephyr-7b:free)", lambda p, s: self._generate_with_openrouter(p, s, model_name="huggingfaceh4/zephyr-7b-beta:free")),
            ("GitHub Models (gpt-4o-mini)", lambda p, s: self._generate_with_github_models(p, s, model_name="gpt-4o-mini")),
            ("GitHub Models (gpt-4o)", lambda p, s: self._generate_with_github_models(p, s, model_name="gpt-4o")),
            ("GitHub Models (Phi-3.5-mini)", lambda p, s: self._generate_with_github_models(p, s, model_name="Phi-3.5-mini-instruct")),
            ("HuggingFace (Qwen-2.5-72B)", self._generate_with_huggingface),
            ("Pollinations AI (Fast)", self._generate_with_pollinations),
        ]

        # 最大3ラウンド試行（モデル切替＋待機）
        for attempt_round in range(1, 4):
            print(f"--- 【{task_name}】LLM生成ラウンド {attempt_round}/3 開始 ---")
            for model_label, fn in api_flow:
                try:
                    res = fn(prompt, system_prompt)
                    if res and len(res.strip()) >= min_length:
                        print(f"SUCCESS: Generated {task_name} using [{model_label}] ({len(res.strip())} chars)")
                        return res.strip()
                except Exception as e:
                    print(f"DEBUG: Error with [{model_label}]: {e}")
            
            if attempt_round < 3:
                wait_time = attempt_round * 3
                print(f"Warning: All models in round {attempt_round} were rate-limited or unavailable. Waiting {wait_time}s before next round...")
                time.sleep(wait_time)

        # 万一すべてのLLM接続が全滅した場合でもActionsを落とさず（クラッシュ防止）、ジャンル完全適合の安全レビューを生成
        print(f"Warning: Online LLM APIs unavailable for {task_name}. Building safe genre-adapted content.")
        if item_context and task_name in ["Article Content", "Full Review Article"]:
            return self._build_safe_genre_article(item_context)
        elif item_context and task_name == "Blog Title":
            return self._build_safe_genre_title(item_context)
        elif item_context and task_name == "Clean Product Name":
            kw = item_context.get("search_keyword", "")
            return kw[:15] if kw else item_context.get("title", "")[:15]
            
        return "おすすめのアイテムをご紹介します。"

    def _build_safe_genre_article(self, item: Dict[str, Any]) -> str:
        clean_title = item.get("clean_title", "おすすめ商品")
        caption = item.get("caption", "")
        keyword = item.get("search_keyword", "")
        genre = self._detect_genre(clean_title, keyword, caption)

        if genre in ["sweets", "food", "furusato"]:
            p1 = f"<p>仕事や家事の合間に、ほっと一息つけるおいしいスイーツがあると気分転換にもぴったり。今回手にとってみた<b>{clean_title}</b>は、そんな贅沢なカフェタイムや手土産の候補として大人の部屋にもしっくり馴染む佇まいを持っています。</p>"
            p2 = f"<p>素材本来の自然な風味と豊かなコクを存分に生かした製法で、余計な雑味がなく<b>ひとくち目から広がる贅沢な香り</b>が印象的。職人のこだわりが詰まった上品な仕立てです。</p>"
            p3 = f"<p>しっとりなめらかな舌触りと濃厚な甘みのバランスが絶妙で、<b>コーヒーや紅茶はもちろん、緑茶との相性も抜群</b>。ひと息つきたいリラックスタイムに、何気ない日常を贅沢な時間へと変えてくれます。</p>"
            p4 = f"<p>パッケージデザインも上品で落ち着きがあり、<b>個包装で扱いやすい設計</b>なのも好印象。来客時のおもてなしや、大切な方への季節の贈り物としても安心して選べる安心感があります。</p>"
            p5 = f"<p>賞味期限や保存方法もお届け時に確認しておくと安心ですが、日持ちや温度管理に配慮された親切な仕様。<b>自分へのささやかなご褒美</b>としても心から満たされる仕上がりです。</p>"
            p6 = f"<p>「日常にちょっとした上質さをプラスしたい」「間違いのない美味しいスイーツを手元に置いておきたい」という方にぜひ手にとってほしい逸品。家族での団らんにも笑顔が広がる完成度の高い逸品です。</p>"
        elif genre == "kitchen":
            p1 = f"<p>毎日の料理や食卓の時間を、もっとスムーズで心地よいものに整えたい——そんな思いに自然と応えてくれるのが、この<b>{clean_title}</b>。無駄な装飾のないスマートな佇まいで、キッチンにすっきり溶け込みます。</p>"
            p2 = f"<p>実際に手に取ってみて実感するのが、<b>ストレスなく使える直感的な扱いやすさ</b>。日々の作業動線を邪魔せず、必要な時にサッと手に取れる絶妙なサイズ感と軽やかさを備えています。</p>"
            p3 = f"<p>日々のデイリーユースに耐えられる<b>丈夫な素材感と丁寧な作り込み</b>が頼もしく、細部まで使い手の視点に立った機能設計。料理の手際が良くなり、毎日の台所仕事が軽やかになります。</p>"
            p4 = f"<p>限られた作業スペースやカウンターに置いても視界を遮らない<b>コンパクトでスリムなプロポーション</b>。圧迫感を与えず、食卓の景観を美しく引き締めてくれます。</p>"
            p5 = f"<p>汚れがサッと落ちやすく<b>お手入れが簡単なメンテナンス性の高さ</b>も大きなメリット。清潔さを長く保ちやすく、後片付けの手間を最小限に抑えてくれる嬉しい工夫が光ります。</p>"
            p6 = f"<p>「道具をシンプルに整えて、暮らしのリズムを整えたい」というミニマル派にもぴったり。実用性とデザイン性を両立し、毎日の食卓を心地よく支えてくれる名脇役です。</p>"
        elif genre == "appliance":
            p1 = f"<p>日々の暮らしの手間を減らし、部屋の居心地を格段に引き上げてくれる<b>{clean_title}</b>。無駄を削ぎ落としたスタイリッシュな外観が、空間をモダンに引き締めてくれます。</p>"
            p2 = f"<p>届いてすぐに使える<b>直感的な操作性とストレスフリーな取り回し</b>が魅力。機械が苦手な方でも迷わず扱える親切な設計で、毎日の生活に自然と馴染んでくれます。</p>"
            p3 = f"<p>静音性や省エネ性にもしっかり配慮されており、<b>時間帯を気にせず快適に使える実力派スペック</b>。暮らしの利便性をぐっと底上げしてくれる頼もしい機能が凝縮されています。</p>"
            p4 = f"<p>すっきりとしたフォルムで<b>省スペースに収まる絶妙なサイズ感</b>。リビングや寝室の壁際に置いても視界を邪魔せず、空間を広々と開放的に保てます。</p>"
            p5 = f"<p>耐久性のある上質なマテリアルとさらりとした質感で、<b>ホコリや指紋が目立ちにくく手入れもスムーズ</b>。長く愛用できる信頼感のある仕上がりです。</p>"
            p6 = f"<p>「暮らしの質をシンプルにアップデートしたい」という方に自信を持っておすすめできるアイテム。毎日の生活にゆとりを生み出し、快適な暮らしのリズムを整えてくれます。</p>"
        else:
            p1 = f"<p>「部屋をすっきり片付けたいけれど、重たくて圧迫感のある大型家具は置きたくない…」そんなこだわり派の理想にピタッとハマるのが、この<b>{clean_title}</b>。洗練されたシンプルな佇まいが空間をスマートに引き締め、どんな部屋のテイストにも自然に溶け込みます。</p>"
            p2 = f"<p>実際に扱ってみて驚くのが、<b>道具いらずで誰でもスムーズに形にできる組み立てやすさ</b>。本体も驚くほど軽量に仕上げられており、模様替えや床の掃除機がけの際も片手でヒョイと持ち上げて移動できる身軽さがありながら、しっかりとした頼もしい安定感を誇ります。</p>"
            p3 = f"<p>オープンシェルフと便利な収納スペースが見事に両立されており、<b>「よく使うアイテムはサッと取れる上段へ」「隠したい小物はスッキリ収納へ」</b>と、メリハリのある使い分けが1台で完結。日常の整理整頓が劇的にスムーズになります。</p>"
            p4 = f"<p>寸法も非常にスマートに設計されており、<b>奥行きを抑えたスリムなロータイプ設計</b>。ワンルームやベッドサイド、壁際に沿わせて置いても視線を遮らず、空間を広く見せてくれる絶妙なバランスです。</p>"
            p5 = f"<p>通気性に配慮されたさらりとした素材感が採用されており、<b>湿気やホコリがこもりにくく衣類や小物を優しく保護</b>。日常のお手入れも簡単で、長く清潔に使い続けられる安心設計です。</p>"
            p6 = f"<p>「家具をできるだけ重厚にしたくない」「機能的でミニマルな部屋づくりを楽しみたい」というニーズに完璧に応えてくれる逸品。実用性とデザインのバランスに優れた名作アイテムです。</p>"
        return f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}\n\n{p5}\n\n{p6}"

    def _build_safe_genre_title(self, item: Dict[str, Any]) -> str:
        clean_title = item.get("clean_title", "おすすめ商品")
        caption = item.get("caption", "")
        keyword = item.get("search_keyword", "")
        genre = self._detect_genre(clean_title, keyword, caption)

        if genre in ["sweets", "food"]:
            titles = [
                f"自分へのご褒美やギフトに大人気！絶品 {clean_title}",
                f"贅沢なひとときに！濃厚で美味しい {clean_title}",
                f"おうちカフェが至福の時間に！老舗の {clean_title}"
            ]
        elif genre == "furusato":
            titles = [
                f"リピーター続出！大満足の返礼品 {clean_title}",
                f"贅沢な味わいをおうちで！注目の {clean_title}"
            ]
        elif genre == "kitchen":
            titles = [
                f"毎日の料理がもっと楽しくなる！実力派 {clean_title}",
                f"使い勝手とデザインを両立！注目の {clean_title}"
            ]
        elif genre == "appliance":
            titles = [
                f"暮らしの手間をグッと減らす！優秀な {clean_title}",
                f"毎日の生活を快適に！大注目の {clean_title}"
            ]
        else:
            titles = [
                f"置くだけで部屋が垢抜ける！人気の {clean_title}",
                f"暮らしにしっくり馴染む！上質な {clean_title}"
            ]
        return random.choice(titles)[:35]

    def generate_review_article(self, item: Dict[str, Any]) -> str:
        title = item.get("title", "")
        search_keyword = item.get("search_keyword", "")
        clean_title = item.get("clean_title") or self.get_clean_product_name(title, search_keyword)
        price = item.get("price", "")
        caption = item.get("caption", "")

        prompt = f"""あなたは「本当に良いものを自分の言葉で本音レビューする人気の暮らしブロガー」です。
以下の楽天市場の商品情報を徹底的に読み込み、定型文や使い回しのテンプレート感を完全に排除して、この商品「だけ」にしかない魅力・スペック・使い勝手を熱量たっぷりに語るオリジナルのレビュー記事（HTML本文のみ）を作成してください。

【商品名】: {title}
【クリーン商品名】: {clean_title}
【価格】: {price}
【商品の説明】: {caption}
【検索キーワード】: {search_keyword}

【最重要執筆ルール（口調・成約率CVR・完全脱テンプレ）】:
1. 【中性的（ジェンダーレス）かつ少しフレンドリーな口調】:
   ・「私」「あたし」「僕」などの一人称は一切使わないでください（主語は自然に省略）。
   ・「〜なの」「〜かしら」「〜わ」「〜よね」などの女性的な語尾や、「〜だぜ」「〜ぜ」などの男性的すぎる語尾は完全に禁止です。
   ・「〜ですね」「〜な点も便利」「〜なところも助かります」「〜な使い勝手」「〜してみるのもおすすめ」など、性別を感じさせないフラットで中性的、かつ親しみやすいフレンドリーなブログ口調で執筆してください。
   ・語尾がすべて「〜〜です」「〜〜ます」で終わる機械的なAI文章は厳禁です。適度に体言止めや共感・感想を織り交ぜてください。

2. 【テンプレ構文・定型句の完全禁止】:
   「そんな日常のプチストレスを解消してくれるのが〜」「実際に使って便利だと感じるポイントは〜」「日々の暮らしをより快適に整えたい方は〜」「いかがでしょうか」などの決まりきったAI構文・テンプレート表現は絶対に禁止です。
   記事ごとに冒頭の切り口、語り口、展開を商品に合わせてガラリと変えてください。

3. 【商品説明（caption）にある「その商品固有の情報」を必ず3つ以上深掘り】:
   商品タイトルや説明文から、その商品固有のディテール（寸法・素材名・耐荷重・カラー・取り付け方法・個包装・賞味期限・静音性など）を具体的に取り上げてください。
   ※アートパネルなら壁の雰囲気やサイズ・飾りやすさ、スイーツなら味や食感・日持ち、家具なら配置場所や収納力など、商品に100%合致した内容のみを書いてください。他の商品の特徴を絶対に混ぜないでください。

4. 【本音の注意点やリアルな使用感（1点）】:
   メリットばかりを並べず、「サイズは事前に測っておくのが安心」「重いものは下段に入れると安定しやすい」「賞味期限は短めなので早めの消費がおすすめ」など、購入前に知っておきたいリアルなポイントに触れることで、読者からの強い信頼を得てください。

5. 【フォーマット】:
   ・シンプルな段落（<p>タグ）3〜4つで構成してください。
   ・スマホで流し読みしても重要なスペックやメリットが目に飛び込んでくるよう、要所を <b> タグで太字にしてください。
   ・見出しタグ（<h1>〜<h3>）や <div>, <ul>, <li> は使わず、<p>タグのみの本文HTMLを出力してください。
"""
        raw_article = self._call_llm_with_retries(prompt, min_length=150, task_name="Article Content", item_context={**item, "clean_title": clean_title})

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

    def build_full_featured_article(self, item: Dict[str, Any], image_urls: list, affiliate_url: str) -> str:
        """
        Amazon高品質記事と同等以上の完成度を実現するフル構成レビュー記事ビルダー。
        3〜6枚の高解像度画像と各段落を交互に美しくサンドイッチし、
        中盤・終盤に洗練されたCTAリンクボタンを配置、末尾にブロ活タグを挿入する。
        """
        title = item.get("title", "")
        search_keyword = item.get("search_keyword", "")
        clean_title = item.get("clean_title") or self.get_clean_product_name(title, search_keyword)
        price = item.get("price", "")
        caption = item.get("caption", "")
        
        # 使用する画像の枚数（最低3枚、最大6枚）
        num_images = max(3, min(len(image_urls), 6))
        
        prompt = f"""あなたは「本当に良いものを自分の言葉で本音レビューする大人気の暮らしブロガー」です。
以下の楽天市場の商品情報を徹底的に読み込み、定型文や使い回しのテンプレート感を完全に排除して、この商品「だけ」にしかない魅力・スペック・使い勝手を熱量たっぷりに語る超高品質な長文レビュー記事を作成してください。

【商品名】: {title}
【クリーン商品名】: {clean_title}
【価格】: {price}
【商品の説明】: {caption}
【検索キーワード】: {search_keyword}
【希望段落数】: ちょうど{num_images}個の段落（<p>...</p>）

【超重要執筆ルール（完全脱テンプレ・高成約率CVR）】:
1. 【中性的（ジェンダーレス）かつ少しフレンドリーな本音レビュー口調】:
   ・「私」「あたし」「僕」などの一人称は一切使わないでください（主語は自然に省略）。
   ・「〜なの」「〜かしら」「〜わ」「〜よね」などの女性的な語尾や、「〜だぜ」「〜ぜ」などの男性的すぎる語尾は完全に禁止です。
   ・「〜ですね」「〜な点も便利」「〜なところも助かります」「〜な使い勝手」「〜してみるのもおすすめ」など、性別を感じさせないフラットで中性的、かつ親しみやすいフレンドリーなブログ口調で執筆してください。
   ・語尾がすべて「〜〜です」「〜〜ます」で終わる機械的なAI文章は厳禁です。適度に体言止めや共感・感想を織り交ぜてください。
   ・「そんな日常のプチストレスを解消してくれるのが〜」「実際に使って便利だと感じるポイントは〜」「いかがでしょうか」などの決まりきったAI構文・テンプレート表現は絶対に禁止です。

2. 【段落構成（必ず{num_images}個の<p>段落を出力すること）】:
   各段落は独立した充実した文章（各段落120〜200文字程度）とし、重要なポイントや数値・素材を <b> タグで太字にしてください。
   各段落のテーマ目安：
   ・段落1: 【導入・空間の佇まい】部屋の片付けや収納・生活感の悩み、大掛かりな家具を置きたくない心理、商品の第一印象やシンプルモダンな佇まい・部屋にすっと溶け込むデザイン性。
   ・段落2: 【組み立て・重量・扱いやすさ】ネジや工具の有無（工具不要や直感組み立て）、本体の軽さ（約○kg、掃除や模様替えの身軽さ）、骨組みの剛性感・安定感。
   ・段落3: 【機能・収納力・耐荷重】棚の段数や引き出しの仕様、見せる収納と隠す収納の使い分け、耐荷重や日常の洋服・タオルの収まりやすさ。
   ・段落4: 【サイズ感・レイアウト】詳しい寸法（幅・奥行・高さ）、腰高やスリム設計による圧迫感のなさ、ワンルームや寝室・クローゼットへの配置感。
   ・段落5: 【素材・通気性・使い心地】ファブリックや素材の質感、通気性や湿気対策、衣類を傷めない配慮、毎朝の服選びがスムーズになる使いやすさ。
   ・段落6: 【総括・おすすめ層・コスパ】どんな人に向いているか（引っ越しが多い人、ミニマリスト、家具を重くしたくない人等）、コスパと実用性の高さ。
   ※商品がスイーツ・食品の場合は、【1:出会いと見た目の贅沢さ】【2:素材のこだわり・製法・香り】【3:食感や濃厚な味わい】【4:内容量・個包装・日持ちの安心感】【5:おすすめの食べ方・ペアリング】【6:ご褒美やギフトへの総括】としてください。

3. 【フォーマット】:
   ・出力は <p>...</p> タグで囲まれた段落のみを出力してください（見出しタグ、divタグ、ボタン、リストは含めないでください）。
"""
        raw_article = self._call_llm_with_retries(prompt, min_length=300, task_name="Full Review Article", item_context={**item, "clean_title": clean_title})
        
        # メタ文言のクリーニング
        raw_article = re.sub(r"^(はい、|承知いたしました。|以下が商品紹介記事です。|以下に記事を出力します。|以下が執筆した記事です。)\s*", "", raw_article)
        
        # 段落（<p>タグ）を抽出
        paragraphs = re.findall(r'<p>(.*?)</p>', raw_article, flags=re.DOTALL)
        if not paragraphs:
            # <p>タグがない場合は改行で分割
            raw_blocks = [b.strip() for b in raw_article.split("\n\n") if b.strip()]
            paragraphs = [b for b in raw_blocks if not b.startswith("<")]
            if not paragraphs:
                paragraphs = [raw_article]

        # 画像リストの整備
        clean_images = []
        for img in image_urls:
            if img and img not in clean_images:
                clean_images.append(img)
        
        # 足りない場合はフォールバック
        if not clean_images:
            clean_images = ["https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&auto=format&fit=crop&q=80"]
        while len(clean_images) < len(paragraphs):
            clean_images.append(clean_images[-1])

        # CTAボタンのスタイル定義（見本記事の上品なボタンデザイン）
        cta_btn_mid = (
            f'<div style="text-align: center; margin: 28px 0;">\n'
            f'<a href="{affiliate_url}" target="_blank" rel="noopener noreferrer" style="display: inline-block; width: 85%; max-width: 320px; padding: 13px 0; background-color: #f4f2ee; color: #333333; border: 1px solid #e0ded9; border-radius: 20px; font-size: 14px; font-weight: bold; text-align: center; text-decoration: none;"><span style="text-decoration: none;">楽天市場で見る</span>\n'
            f'</a></div>'
        )
        cta_btn_end = (
            f'<div style="text-align: center; margin: 28px 0;">\n'
            f'<a href="{affiliate_url}" target="_blank" rel="noopener noreferrer" style="display: inline-block; width: 85%; max-width: 320px; padding: 13px 0; background-color: #f4f2ee; color: #333333; border: 1px solid #e0ded9; border-radius: 20px; font-size: 14px; font-weight: bold; text-align: center; text-decoration: none;"><span style="text-decoration: none;">楽天市場で詳細をチェック</span>\n'
            f'</a></div>'
        )

        alt_suffixes = [
            "全体像", "収納イメージ・利用風景", "引き出しと棚の仕様・ディテール",
            "側面ディテール・サイズ感", "素材感と質感", "活用シーン・おすすめポイント"
        ]

        full_html_parts = []
        mid_point = max(2, len(paragraphs) // 2)

        for i, p_text in enumerate(paragraphs):
            # 画像の挿入
            img_url = clean_images[i % len(clean_images)]
            alt_suffix = alt_suffixes[i % len(alt_suffixes)]
            alt_text = f"{clean_title} {alt_suffix}"
            img_html = f'<div><img style="max-width: 100%; height: auto; border-radius: 8px; display: block; margin-left: auto; margin-right: auto;" src="{img_url}" border="0" alt="{alt_text}" /></div>'
            
            full_html_parts.append(img_html)
            full_html_parts.append(f"\n\n<p>{p_text.strip()}</p>\n\n")

            # 中盤のCTAボタン
            if i == (mid_point - 1):
                full_html_parts.append(f"{cta_btn_mid}\n")

        # 終盤のCTAボタン
        full_html_parts.append(f"{cta_btn_end}\n\n")

        # ブロ活広告タグ
        ad_tag = '<pointad pointad-id="div-plaza-point-ad" pointad-text="#ブロ活広告#" />'
        full_html_parts.append(ad_tag)

        return "".join(full_html_parts)

    def generate_blog_title(self, item: Dict[str, Any]) -> str:
        title = item.get("title", "")
        search_keyword = item.get("search_keyword", "")
        clean_title = item.get("clean_title") or self.get_clean_product_name(title, search_keyword)
        caption = item.get("caption", "")

        system_prompt = "あなたは読者の目を引き、クリック率（CTR）と検索流入（SEO）を最大化するブログ記事タイトルを作成するプロのコピーライターです。読者の日常の悩み解決や具体的なベネフィットを伝え、日本語で余計な説明なしにタイトルテキストのみを出力してください。"

        prompt = f"""以下の商品情報を元に、読者の悩み解決や生活の変化がひと目でわかり、思わずクリックしたくなる魅力的なブログ記事タイトルを1つだけ生成してください。
フォールバックや定型テンプレートは一切使わず、この商品固有の魅力・ベネフィットを捉えたオリジナルのタイトルにしてください。

【商品名】: {clean_title}
【商品説明】: {caption}
【検索キーワード】: {search_keyword}

【タイトル作成ルール（厳格遵守）】:
1. 【悩み解決・ベネフィット】: 「朝の鍵探しがゼロに」「賃貸でも壁を傷つけない」「絶品おうちカフェ」「老舗の本格的な味わい」など、その商品固有のメリットや変化をタイトルに盛り込んでください。
2. 【商品名の明記】: 検索流入（SEO）のため、「{clean_title}」または「{search_keyword}」に含まれる主要名詞（例：木製キーフック、和菓子 カステラ 老舗等）を必ずタイトルに含めてください。
3. 【文字数】: スマホ画面で一目で読めるよう、25〜35文字程度に収めてください。
4. 【禁止事項】: 「QOL爆上がり」「生活の質」「おすすめ商品」などの陳腐な表現、記号の多用（【】や『』、「」など）は避け、自然で魅力的な日本語にしてください。
5. 【出力フォーマット】: 余計な前置きや解説は一切含めず、タイトル文字列のみを出力してください。
"""
        raw_title = self._call_llm_with_retries(prompt, system_prompt=system_prompt, min_length=5, task_name="Blog Title", item_context={**item, "clean_title": clean_title})
        clean_res = re.sub(r'<[^>]+>|[\"\'「」『』【】\n\r]', '', raw_title).strip()
        return clean_res[:40]

    def get_clean_product_name(self, title: str, search_keyword: str) -> str:
        """楽天市場のノイズが多い商品名から、具体的でシンプルな商品名（15文字以内）を抽出する。"""
        system_prompt = "あなたは入力されたテキストから無駄な修飾語を取り除き、商品名そのもの（名詞）のみを抽出する優秀なアシスタントです。"
        prompt = f"""以下の楽天市場の商品名から、送料無料、サイズ、型番、アピール用の形容詞（おしゃれ、大人気など）をすべて排除し、その商品が「何であるか」を示す具体的でクリーンな商品名（例：『木枠ウォールミラー』『珪藻土バスマット』『分別ゴミ箱』など）を日本語で15文字以内で抽出してください。
余計な解説や括弧、引用符、Markdown等は一切含めず、抽出した商品名テキストのみを出力してください。

【楽天市場の商品名】: {title}
【検索時のキーワード】: {search_keyword}
"""
        raw_name = self._call_llm_with_retries(prompt, system_prompt=system_prompt, min_length=2, task_name="Clean Product Name", item_context={"title": title, "search_keyword": search_keyword})
        cleaned = re.sub(r'<[^>]+>|[\"\'「」『』【】\n\r]', '', raw_name).strip()
        if cleaned and len(cleaned) <= 20:
            return cleaned[:18]
        return search_keyword[:15] if search_keyword else title[:15]

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

    def _discover_gemini_models(self, api_key: str) -> list:
        """Gemini APIキーを使って利用可能な最新モデル一覧を動的に取得する（1.5系は完全除外）"""
        valid_models = []
        for ver in ["v1beta", "v1"]:
            try:
                url = f"https://generativelanguage.googleapis.com/{ver}/models?key={api_key}"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for m in data.get("models", []):
                        if "generateContent" in m.get("supportedGenerationMethods", []):
                            m_name = m.get("name", "").replace("models/", "")
                            # 1.5系は完全廃止済みのため絶対に使用禁止
                            if "1.5" in m_name:
                                continue
                            if m_name and m_name not in valid_models:
                                valid_models.append((ver, m_name))
            except Exception:
                pass
        return valid_models

    def _generate_with_gemini(self, prompt: str, system_prompt: Optional[str] = None, specific_model: Optional[str] = None) -> Optional[str]:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        
        sys_msg = system_prompt or "あなたは読者の日常の悩みに寄り添い、商品のリアルな使い心地・具体的なメリット・注意点を本音で伝える凄腕の暮らしブロガーです。AI特有の抽象的な美辞麗句や説明書のような機械的表現は完全に排除し、自然で説得力のある日本語のHTML本文のみを出力します。"
        
        # 動的に利用可能なモデルを取得（1.5系除外）
        discovered = self._discover_gemini_models(api_key)
        if specific_model:
            model_candidates = [("v1beta", specific_model), ("v1", specific_model)]
        elif discovered:
            model_candidates = discovered
        else:
            # 最新対応モデルのローテーション
            model_candidates = [
                ("v1beta", "gemini-2.5-flash"),
                ("v1beta", "gemini-2.0-flash"),
                ("v1beta", "gemini-2.0-flash-lite"),
                ("v1beta", "gemini-2.5-flash-lite"),
                ("v1beta", "gemini-2.5-pro"),
                ("v1beta", "gemini-3-flash"),
                ("v1beta", "gemini-3.1-pro"),
                ("v1beta", "gemini-3.1-flash-lite"),
                ("v1beta", "gemini-3.5-flash-lite"),
                ("v1beta", "gemini-3.5-flash"),
                ("v1beta", "gemini-3.6-flash"),
                ("v1beta", "gemini-3.7-flash"),
            ]
        
        for ver, model in model_candidates:
            url = f"https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [{
                        "text": sys_msg + "\n\n" + prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            }
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        if text and len(text.strip()) > 5:
                            return text
                    except KeyError:
                        pass
                else:
                    err_msg = self._translate_error_message(f"Gemini API ({ver}/{model})", resp.status_code, resp.text)
                    print(f"DEBUG: {err_msg}")
            except Exception as e:
                print(f"DEBUG: 【Gemini API ({ver}/{model})】通信エラー: {e}")
        return None

    def _generate_with_openrouter(self, prompt: str, system_prompt: Optional[str] = None, model_name: Optional[str] = None) -> Optional[str]:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return None
        
        sys_msg = system_prompt or "あなたは読者の日常の悩みに寄り添い、商品のリアルな使い心地・具体的なメリット・注意点を本音で伝える凄腕の暮らしブロガーです。AI特有の抽象的な美辞麗句や説明書のような機械的表現は完全に排除し、自然で説得力のある日本語のHTML本文のみを出力します。"
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        models = [model_name] if model_name else [
            "qwen/qwen-2.5-coder-32b-instruct:free",
            "mistralai/mistral-7b-instruct:free",
            "google/gemma-2-9b-it:free",
            "meta-llama/llama-3-8b-instruct:free",
            "huggingfaceh4/zephyr-7b-beta:free"
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
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        content = data["choices"][0]["message"]["content"]
                        if content and len(content.strip()) > 5:
                            return content
                    except KeyError:
                        pass
                else:
                    err_msg = self._translate_error_message(f"OpenRouter ({model})", resp.status_code, resp.text)
                    print(f"DEBUG: {err_msg}")
            except Exception as e:
                print(f"DEBUG: OpenRouter ({model}) 通信エラー: {e}")
        return None

    def _generate_with_github_models(self, prompt: str, system_prompt: Optional[str] = None, model_name: str = "gpt-4o-mini") -> Optional[str]:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token:
            return None
        
        sys_msg = system_prompt or "あなたは読者の日常の悩みに寄り添い、商品のリアルな使い心地・具体的なメリット・注意点を本音で伝える凄腕の暮らしブロガーです。AI特有の抽象的な美辞麗句や説明書のような機械的表現は完全に排除し、自然で説得力のある日本語のHTML本文のみを出力します。"
        url = "https://models.inference.ai.azure.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
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
                    return None
            else:
                err_msg = self._translate_error_message(f"GitHub Models ({model_name})", resp.status_code, resp.text)
                print(f"DEBUG: {err_msg}")
        except Exception as e:
            print(f"DEBUG: GitHub Models ({model_name}) 通信エラー: {e}")
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
        try:
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
        except Exception:
            pass
        return None

    def _generate_with_pollinations(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        sys_msg = system_prompt or "あなたは読者の日常の悩みに寄り添い、商品のリアルな使い心地・具体的なメリット・注意点を本音で伝える凄腕の暮らしブロガーです。AI特有の抽象的な美辞麗句や説明書のような機械的表現は完全に排除し、自然で説得力のある日本語のHTML本文のみを出力します。"
        url = "https://text.pollinations.ai/"
        payload = {
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": prompt}
            ],
            "model": "openai-fast"
        }
        try:
            resp = requests.post(url, json=payload, timeout=40)
            if resp.status_code == 200:
                text = resp.text.strip()
                if text and len(text) > 10:
                    return text
        except Exception as e:
            print(f"DEBUG: Pollinations AI failed: {e}")
        return None
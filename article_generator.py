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
        # ローカルの .env ファイルがあれば読み込む
        if os.path.exists(".env"):
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip().strip('"').strip("'")

    def load_model(self):
        print("ArticleGenerator: Initialized using online APIs (Gemini / fallback).")

    def _detect_genre(self, title: str, search_keyword: str, caption: str = "") -> str:
        text = (title + " " + search_keyword + " " + caption).lower()
        if "おせち" in text or "御節" in text:
            return "osechi"
        if any(w in text for w in ["ハンドクリーム", "リップ", "バーム", "保湿クリーム", "シアバター", "セラミド", "スキンケア", "乾燥肌", "ネイルオイル", "馬油"]):
            return "skincare"
        if any(w in text for w in ["加湿器", "スチーム式", "超音波加湿器", "ハイブリッド加湿器", "気化式"]):
            return "humidifier"
        if any(w in text for w in ["ヒーター", "こたつ", "コタツ", "ストーブ", "暖房", "ホットカーペット", "電気毛布", "電気ひざ掛け"]):
            return "heating"
        if any(w in text for w in ["着る毛布", "ブランケット", "毛布", "ひざ掛け", "ボア", "フリース"]):
            return "blanket"
        if any(w in text for w in ["入浴剤", "バスソルト", "重炭酸", "エプソムソルト", "温泉", "バスボム", "薬湯", "クレイバス", "シャワーヘッド", "シャワー"]):
            return "bath"
        if any(w in text for w in ["スイーツ", "和菓子", "洋菓子", "お菓子", "プリン", "ケーキ", "チョコ", "ガトーショコラ", "シュトーレン", "クッキー", "バウムクーヘン", "大福", "どら焼き", "カステラ", "マカロン", "ジェラート", "アイス", "タルト", "ロールケーキ", "カヌレ", "フィナンシェ"]):
            return "sweets"
        if "ふるさと納税" in text:
            return "furusato"
        if any(w in text for w in ["枕", "まくら", "ピロー", "マットレス", "布団", "敷きパッド", "快眠", "安眠"]):
            return "sleep"
        if any(w in text for w in ["肉", "牛", "豚", "鶏", "米", "海鮮", "カニ", "エビ", "魚", "グルメ", "惣菜", "ハンバーグ", "餃子", "うどん", "ラーメン"]):
            return "food"
        if any(w in text for w in ["掃除機", "除湿機", "扇風機", "サーキュレーター", "ドライヤー", "空気清浄機"]):
            return "appliance"
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
            ("OpenRouter (nemotron-3.5-lightning:free)", lambda p, s: self._generate_with_openrouter(p, s, model_name="nvidia/nemotron-3.5-lightning:free")),
            ("OpenRouter (gemma-4-26b-a4b-it:free)", lambda p, s: self._generate_with_openrouter(p, s, model_name="google/gemma-4-26b-a4b-it:free")),
            ("OpenRouter (gemma-4-31b-it:free)", lambda p, s: self._generate_with_openrouter(p, s, model_name="google/gemma-4-31b-it:free")),
            ("OpenRouter (liquid-lfm-2.5:free)", lambda p, s: self._generate_with_openrouter(p, s, model_name="liquid/lfm-2.5-2.6b:free")),
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

    def _format_sentence_linebreaks(self, paragraph_html: str) -> str:
        """
        段落内の文章を読みやすくするため、文の区切り（。！？）の後に
        適切に1改行（<br /><br />）を挟み、スマホでもスッと頭に入る行間を作る。
        """
        # 既存の過剰なbrや改行を一旦正規化
        text = re.sub(r'(<br\s*/?>\s*)+', '<br /><br />', paragraph_html.strip())
        text = re.sub(r'\n{2,}', '<br /><br />', text)
        text = re.sub(r'\n', '', text)

        # すでに適度な <br /><br /> が含まれている場合はそのまま整形して返す
        if text.count('<br /><br />') >= 1:
            return text

        # 句点「。」や「！」「？」の直後（ただし閉じ括弧「」』）の後を除く）で文を分割
        sentences = re.split(r'(?<=[。！？])(?![」』）\)])', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) <= 1:
            return text

        # 1〜2文ごと（話題の切り替わりや約45文字以上のまとまりごと）に1改行（<br /><br />）を挟む
        blocks = []
        current = ""
        for s in sentences:
            if not current:
                current = s
            else:
                # 前の文が短い導入でなく、話題が切り替わる場合は1改行挟む
                clean_curr_len = len(re.sub(r'<[^>]+>', '', current))
                if clean_curr_len >= 35:
                    blocks.append(current)
                    current = s
                else:
                    current += s
        if current:
            blocks.append(current)

        return "<br /><br />".join(blocks)

    def _validate_and_polish_paragraphs(self, paragraphs: list, item: Dict[str, Any]) -> list:
        """
        投稿前の厳格な品質・AI臭さ・整合性チェック。
        1. AI特有のメタ発言・定型句・不自然な翻訳調の除去
        2. 商品ジャンルと無関係な誤情報（枕なのに壁掛け・工具・大型家具など）の混入チェック
        3. 同一スペック（保証期間など）の重複記載の排除
        4. 文ごとの適切な1改行（<br /><br />）フォーマット適用
        """
        clean_title = item.get("clean_title", "おすすめ商品")
        caption = item.get("caption", "")
        keyword = item.get("search_keyword", "")
        genre = self._detect_genre(clean_title, keyword, caption)

        # 1. ジャンル不適合ワードの検査（混入していたら即座に該当段落または全体を安全記事に差し替え）
        forbidden_by_genre = {
            "bath": ["壁に取り付け", "壁掛け", "組み立て", "大型家具", "ネジ", "棚板", "沈み込み", "寝姿勢", "寝具", "枕", "マットレス", "敷きパッド"],
            "sleep": ["壁に取り付け", "壁掛け", "組み立て", "大型家具", "ネジ", "棚板", "水圧", "シャワー", "節水", "入浴"],
            "sweets": ["壁に取り付け", "組み立て", "大型家具", "配線", "ネジ", "インテリアに馴染む", "水圧", "沈み込み"],
            "food": ["壁に取り付け", "組み立て", "大型家具", "配線", "ネジ", "水圧", "沈み込み"],
            "furusato": ["壁に取り付け", "組み立て", "大型家具", "配線", "ネジ", "水圧", "沈み込み"],
            "appliance": ["賞味期限", "口どけ", "ザラメ", "美味しい", "食感", "沈み込み"],
            "desk_gadget": ["賞味期限", "口どけ", "ザラメ", "美味しい", "食感", "沈み込み", "水圧"],
        }
        ng_words = forbidden_by_genre.get(genre, [])

        # AI臭いフレーズ・硬い表現を自然で親しみやすい表現へ自動補正
        ai_cliche_replacements = [
            (r"^[〜～\-\s]+と出会ったのが[、\s]*", "そこで出会ったのが、"),
            (r"[〜～]\s*と出会ったのが", "出会ったのが"),
            (r"――これが<b>.*?</b>の味方でした[。]?", ""),
            (r"毛穴の奥にまで届くことなく[、\s]*", "毛穴の奥までしっかり届き、"),
            (r"心配もいまいち[。]?", "心配もありません。"),
            (r"ホットスポットに[。]?", "癒やしの空間に。"),
            (r"洗面所の神秘のよう[。]?", "至福の心地よさです。"),
            (r"いかがでしょうか[。？]?", ""),
            (r"いかがでしたでしょうか[。？]?", ""),
            (r"この記事では[^。]+解説します[。]?", ""),
            (r"今回は[^。]+ご紹介します[。]?", ""),
            (r"まさに理想的な選択肢と言えるでしょう[。]?", "本当に頼もしい存在です。"),
            (r"特筆すべきは、?", "特に嬉しいのが、"),
            (r"過言ではありません[。]?", "言えます。"),
            (r"実感させられます[。]?", "実感します。"),
            (r"優位性があります[。]?", "魅力です。"),
            (r"一助となります[。]?", "助かります。"),
            (r"一価[。]?", "逸品です。"),
            (r"呼吸を促進する", "ふわっと広がり、思わず深呼吸したくなります"),
            (r"カップ麺のつまみごとに", "ちょっとした休憩時間に"),
        ]

        polished = []
        seen_warranty = False

        for p in paragraphs:
            text = p.strip()
            # ジャンルNGワードが含まれていたら安全フォールバックへ切り替え
            if any(ng in text for ng in ng_words):
                print(f" Quality Check Notice: Detected genre mismatch word in paragraph. Using verified genre paragraphs.")
                return [self._format_sentence_linebreaks(sp) for sp in self._build_safe_genre_paragraphs(item)]

            for pattern, repl in ai_cliche_replacements:
                text = re.sub(pattern, repl, text)

            # 保証期間などの話が複数の段落で重複していたら2回目以降の文をカット
            if "保証" in text and ("延長" in text or "メーカー保証" in text or "1年" in text or "2年" in text):
                if seen_warranty:
                    # 2回目以降の保証の文を除去
                    sents = re.split(r'(?<=[。！？])', text)
                    sents = [s for s in sents if not ("保証" in s and ("延長" in s or "1年" in s or "2年" in s))]
                    text = "".join(sents).strip()
                else:
                    seen_warranty = True

            # 1文ごとの話題切り替えに1改行を挟む
            formatted_text = self._format_sentence_linebreaks(text)
            if formatted_text:
                polished.append(formatted_text)

        return polished

    def _build_safe_genre_article(self, item: Dict[str, Any]) -> str:
        clean_title = item.get("clean_title", "おすすめ商品")
        caption = item.get("caption", "")
        keyword = item.get("search_keyword", "")
        genre = self._detect_genre(clean_title, keyword, caption)

        if genre == "bath":
            p1 = f"<p>毎日のバスタイムやシャワーの時間、水圧の物足りなさや水道代の負担、肌や髪のパサつきに悩んでいませんか。お風呂場の設備をまるごとリフォームするのは大変ですが、毎日のバスタイムをもっと贅沢で快適な癒やしの時間に変えたいと本気で探していたところに出会ったのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>実際に自宅のシャワーに取り付けて使ってみた瞬間、肌当たりの極上な柔らかさと心地よさにまず感動しました。<b>毛穴の奥まで届くきめ細やかな微細バブル</b>が肌をやさしく包み込み、浴びるだけで日々の皮脂汚れや毛穴の汚れをスッキリと洗い流してくれます。水圧を落とすことなく肌当たりがなめらかになるため、シャワーを浴びる時間が毎日の至福のリフレッシュになります。</p>"
            p3 = f"<p>さらに家計に直結する節水効果や使い勝手の良さも抜群です。手元のストップボタンでこまめに止水できるため無駄な流水を抑えられ、<b>確かな節水性能で毎月の水道代やガス代の節約にも貢献</b>してくれます。主要メーカー対応のアダプターが付属しているため工具不要で届いたその日にすぐ取り付けられ、握りやすく軽量な設計なので家族みんながストレスなく快適に使えます。</p>"
            p4 = f"<p>使い始めてからというもの、<b>お風呂上がりの肌のしっとり感や髪の指通りの良さを実感</b>し、毎日のシャワータイムが待ち遠しくなりました。「自宅のお風呂で手軽に極上のスパ体験を味わいながら、家計にも優しく暮らしたい」と願うすべての方に、自信を持っておすすめできる大満足のバスアイテムです。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}"

        elif genre == "sleep":
            p1 = f"<p>朝目が覚めたときに首や肩へずっしりと重みが残っていたり、しっかり寝たはずなのに頭が重くて疲れが抜けきらなかったり……そんな睡眠のプチ不調にため息をついてしまうことってありませんか。寝具を一から買い替えるのはハードルが高いものの、毎日の睡眠環境をもっと心地よく整えて朝の目覚めを変えたいと本気で探していたところに出会ったのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>届いて実際に頭を預けて横になってみた瞬間、一般的な枕との圧倒的な違いにまず驚かされました。<b>頭部から首筋の隙間に吸い付くようにフィット</b>し、余計な緊張がすっとほどけていく感覚がとにかく心地よく、首や肩への負担がふわりと軽くなります。沈み込みすぎず適度な反発力で頭をしっかり支えてくれるため、横向き寝になっても肩が圧迫されず、無理のない自然な寝姿勢をキープできます。</p>"
            p3 = f"<p>さらに毎日使っていて実感するのが、寝返りの打ちやすさと通気性の素晴らしさです。寝返りを打っても頭が落ちにくく、夜中に何度もポジションを探して目が冴えてしまうストレスから完全に解放されました。<b>熱がこもりにくい立体構造と肌触りの良いカバー</b>のおかげで、汗ばむ季節でも朝まで蒸れずにサラサラとした爽快感が続きます。カバーはサッと外して洗濯機で丸洗いできるため、いつでも清潔な状態を保てるのも日常使いに嬉しいポイントです。</p>"
            p4 = f"<p>実際に使い始めてからというもの、<b>朝起きたときの首や肩の軽やかさが劇的に変わり</b>、目覚ましが鳴った瞬間にスッと起き上がれる日が増えて毎日の活力が段違いになりました。「ぐっすり深く眠って、毎朝気持ちよく一日をスタートさせたい」と願うすべての方に、自信を持っておすすめできる快眠の頼れる相棒です。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}"

        elif genre == "sweets":
            p1 = f"<p>仕事や家事の合間に、温かいお茶や淹れたての珈琲を片手にほっと一息つける時間があると、それだけで張り詰めていた気持ちがふわりとほぐれていきますよね。でも、近所のスーパーやコンビニで手軽に済ませるおやつではなんだか味気ないし、たまには自分へのとっておきのご褒美として、あるいは大切な人を喜ばせる手土産として、心から満足できる本物の甘味を味わいたい……そんな願いにぴったり寄り添ってくれたのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>届いて丁寧に包まれた箱を開けた瞬間、素材の良さを物語るふくよかな香りがふわっと立ちのぼり、食べる前から思わずうっとり。ひとくち口に運ぶとしっとりと濃密なコクが広がり、<b>舌の上でゆっくりとほどけていく贅沢な口どけ</b>がたまりません。余計な添加物に頼らず、選び抜かれた上質な素材と熟練の職人が手間暇を惜しまず丁寧に仕立てているからこそ出せる、奥深く上品な甘みが日常のティータイムを一瞬で特別なひとときに変えてくれます。</p>"
            p3 = f"<p>味わいの上品さはもちろんのこと、<b>珈琲の豊かな苦味や緑茶の渋み、紅茶の香りとも相性抜群</b>で、合わせる飲み物によって異なる豊かな表情を見せてくれるのも大きな魅力です。ひとつひとつ丁寧に個包装やカットが施されているため、包丁やまな板を汚す手間も一切なく、食べたいときにサッと極上の味を楽しめる手軽さが本当に重宝します。日持ちや保存のしやすさまで計算されており、来客時のおもてなしにも慌てずスマートに出せるのが助かります。</p>"
            p4 = f"<p>頑張った自分への最高のご褒美としてはもちろん、<b>大切な方へのギフトやお祝い・手土産に選んでも絶対に外さない安心感</b>があります。「美味しいものを口にした瞬間の、あの思わず笑顔がこぼれる幸せな時間」を自宅で心ゆくまで堪能したい方に、心からおすすめしたい絶品のスイーツです。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}"

        elif genre in ["food", "furusato"]:
            p1 = f"<p>毎日忙しく過ごしているからこそ、一日の終わりの食卓や週末の家族団らんには、思わず笑顔がこぼれるような本当に美味しいものが欲しくなりますよね。外食に出かける時間や手間は取れないけれど、自宅にいながら専門店や名産地ならではの贅沢で本格的な味をゆっくり堪能したい……そんな食のこだわりを満たしてくれたのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>届いて梱包を開いた瞬間から伝わってくる上質さと鮮度の良さに、調理する前から家族みんなの期待が一気に高まります。実際に火を通して味わってみると、スーパーで手に入る一般的なものとは格が違い、<b>噛みしめるたびにあふれ出す濃厚な旨味と香ばしさ</b>が口いっぱいに広がって感動。素材本来が持つ力強いコクと絶妙な味付けが調和し、いつもの自宅の食卓が一瞬にして専門店の特等席へとグレードアップします。</p>"
            p3 = f"<p>調理の手順も驚くほどシンプルで、忙しい日の夕食作りでもパパッと短時間で本格的な一皿が完成するのが本当にありがたいところ。<b>小分けパックや冷凍保存にもしっかり配慮された使い勝手の良さ</b>のおかげで、食べたい分だけ解凍していつでも作りたての美味しさを味わえます。冷凍庫にストックしておくだけで、「今日はあのご馳走が待っている」と仕事帰りやおうち時間が一段と楽しみになります。</p>"
            p4 = f"<p>普段の食事の幸福度をグッと底上げしてくれるのはもちろん、<b>家族のお祝い事や特別な日のおもてなし料理としても大絶賛されること間違いなし</b>のクオリティ。自宅で手軽に極上のごちそう体験を味わいたい方に、自信を持っておすすめしたい大満足の逸品です。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}"

        elif genre == "kitchen":
            p1 = f"<p>毎日の料理や後片付けのたびに、ちょっとした使いにくさや生活感の溢れる台所周りにモヤモヤしてしまうことってありませんか。かといって大掛かりな台所リフォームや高価な器具の総入れ替えをするほどでもないし……と悩んでいたところに出会ったのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>実際にキッチンに迎えてみたとき、無駄な凹凸や生活感をそぎ落とした洗練された佇まいとお部屋に馴染む美しい質感にまず惚れ惚れしました。毎日自然と手に取りたくなる手馴染みの良さがあり、<b>調理中のわずらわしい動線や手間をスッと軽くしてくれる機能美</b>が随所に光ります。カウンターやシンク周りに置いたままでもインテリアを邪魔せず、むしろ台所全体をすっきりとおしゃれに見せてくれます。</p>"
            p3 = f"<p>毎日ハードに使う調理道具だからこそ、耐久性とメンテナンス性の高さは絶対に譲れないポイントです。<b>汚れがサッと落ちて常に清潔をキープできるタフな素材構造</b>で作られており、使った後の後片付けも水で流すだけでツルンと綺麗になる手軽さが忙しい毎日の大きな味方になってくれます。扱いやすさと実用性を高い次元で両立しており、料理初心者からこだわり派までストレスなく使いこなせます。</p>"
            p4 = f"<p>このアイテムを迎えてからというもの、<b>億劫に感じていた台所仕事が驚くほどスムーズで心地よい時間へと早変わり</b>し、料理をするモチベーションが自然と湧いてくるのを実感しています。キッチンの生活感を上手に減らし、日々の食卓作りをもっと楽しく快適にしたい方に、心からおすすめしたい実力派アイテムです。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}"

        elif genre == "appliance":
            p1 = f"<p>日々の暮らしや家事の手間が増えて、部屋で過ごす時間にもっと心と時間のゆとりが欲しいと感じることってありますよね。かといって部屋の雰囲気を壊すような無骨な家電や、置き場所に困るような大型のものは増やしたくない……と探していたところに出会ったのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>お部屋に配置してみた瞬間、空間に自然と溶け込む洗練されたミニマルなデザインにまず感動。スイッチを入れてみると直感的な操作性で迷わず扱える上、<b>静音性や省エネ性にも細やかに配慮された確かな性能</b>で、生活の邪魔を一切せず快適な環境を作り出してくれます。コンパクトな設計でありながら実力は本格派で、日々の暮らしのクオリティを底上げしてくれます。</p>"
            p3 = f"<p>実際に使い続けてみて実感するのが、メンテナンスの手軽さと生活動線の快適さです。パーツの取り外しやお手入れが簡単でホコリや汚れを溜め込まず、常に衛生的に使い続けられる安心感があります。<b>暮らしの細かなプチストレスを先回りして解消してくれるスマートな機能性</b>が詰まっており、時間やエネルギーの無駄を確実に省いてくれます。</p>"
            p4 = f"<p>暮らしに迎えてからというもの、<b>日々の家事や生活のリズムが軽やかに整い、自分時間やリラックスできる時間がグッと増えた</b>のを実感しています。デザイン性と実用性を両立し、毎日の生活に心地よいゆとりを生み出したい方に、自信を持っておすすめできる名品です。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}"

        elif genre == "desk_gadget":
            p1 = f"<p>デスク周りや作業スペースを見るたびに、黒いコードが複雑に絡み合ったり小物が散乱したりして、なんだかそれだけで集中力が途切れてしまうことってありませんか。作業効率を上げつつ、スマートで美しいデスク環境を作りたいと悩んでいたところに出会ったのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>実際に机の上に置いてみても余計な圧迫感がなく、チープさを感じさせない落ち着いた質感がお部屋のトーンにすっとマッチ。<b>ごちゃつきがちな配線や小物をひとまとめに整頓できる機能性</b>のおかげで、デスク上が一瞬で見違えるほどクリーンに生まれ変わります。必要なものに迷わず手が届く快適さがあり、机に向かった瞬間の視覚ノイズが一気に消え去ります。</p>"
            p3 = f"<p>手狭になりがちなデスク上の有効スペースを最大限に広げてくれる合理的な設計で、ノートPCやモニターとの相性も抜群です。耐久性に優れたしっかりとした造りなので、ガタつきや頼りなさを感じることもなく、毎日安心して使い倒せるタフさを兼ね備えています。<b>配線処理や整理整頓のストレスから根本的に解放される快適さ</b>は、一度味わうともう以前の環境には戻れません。</p>"
            p4 = f"<p>作業動線が劇的にスムーズになり、<b>視界に入る余計なノイズが消えるだけでこんなにも集中力とモチベーションが高まるのかと実感</b>しています。リモートワークや毎日のデスクワークをより快適で洗練された空間に仕立て直したい方に、自信を持っておすすめできる相棒です。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}"

        elif genre == "decor":
            p1 = f"<p>お部屋の雰囲気をガラリと変えて垢抜けさせたいけれど、大掛かりな家具の買い替えや壁の工事は大掛かりでためらってしまう……そんな模様替えの悩みを抱えていませんか。手軽にお部屋のセンスをワンランク引き上げてくれる上質なインテリアアイテムを探していたところに出会ったのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>実際に手にとって飾ってみた瞬間、空間を優しく引き締める洗練された色味と素材の温もりに感動。<b>置くだけ・飾るだけで見慣れたお部屋に心地よいメリハリが生まれ</b>、まるでセレクトショップやカフェのような洗練された雰囲気が広がります。光の当たり方によって表情を変える質感の美しさがあり、殺風景だった一角が温もりある特別なスペースに変わります。</p>"
            p3 = f"<p>主張しすぎず既存の家具や壁紙にすっと馴染む絶妙なバランス感で、賃貸のお部屋でも気兼ねなく取り入れられる手軽さが嬉しいところ。軽量で移動やレイアウト変更も簡単に行えるため、季節や気分に合わせて飾る場所を変えながら長く愛用できる頼もしさがあります。<b>目に入るたびにふっと心がほぐれるような上質な癒やし</b>を日常に運んでくれます。</p>"
            p4 = f"<p>お部屋の空気が一新され、<b>家に帰って部屋のドアを開けるのが毎日楽しみになるような素敵な空間作り</b>を叶えてくれました。暮らしにさりげない彩りをプラスして、自分らしく心地よいお部屋を作りたい方に、心からおすすめしたいインテリアアイテムです。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}"

        else:
            p1 = f"<p>お部屋の散らかりや生活感をなんとか整えたいけれど、重たくて圧迫感のある大型家具は置きたくない……と悩んでいたところに出会ったのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>届いて実際に配置してみた瞬間、空間を邪魔しないスリムな佇まいと落ち着いた質感がお部屋のインテリアにすっと溶け込み、嬉しい驚きがありました。<b>軽量で取り回しが良いのにしっかりとした頼れる構造</b>で、散らかりがちな日用品や小物を気持ちよく一箇所に整理整頓できます。リビングや寝室の隅に置いても視界を遮らず、お部屋の開放感をしっかりとキープしてくれます。</p>"
            p3 = f"<p>出し入れのしやすさや使い勝手の良さまで計算し尽くされており、必要なものを迷わずサッと手に取れる快適さが毎日の生活を劇的にスムーズにしてくれます。工具不要や簡単な組み立てで届いたその日からすぐに使い始められる手軽さもあり、模様替えや掃除の際の移動もストレスなく行える身軽さが頼もしいところです。</p>"
            p4 = f"<p>生活感を上手に抑えながら空間を美しく有効活用できるようになり、<b>部屋がスッキリ片付くだけで日々の気分まで軽やかに整うのを実感</b>しています。無駄なスペースを作らず快適で心地よいお部屋を手に入れたい方に、心からおすすめしたい収納アイテムです。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}"

    def _build_safe_genre_paragraphs(self, item: Dict[str, Any]) -> list:
        article_text = self._build_safe_genre_article(item)
        paras = re.findall(r'<p>(.*?)</p>', article_text, flags=re.DOTALL)
        return [p.strip() for p in paras if p.strip()]

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
        caption = item.get("caption", "")

        prompt = f"""あなたは「本当に良いものを自分の言葉で本音レビューする人気の暮らしブロガー」です。
以下の楽天市場の商品情報を徹底的に読み込み、定型文や使い回しのテンプレート感を完全に排除して、この商品「だけ」にしかない魅力・スペック・使い勝手を熱量たっぷりに語るオリジナルのレビュー記事（HTML本文のみ）を作成してください。

【商品特徴・説明】: {caption}
【検索キーワード】: {search_keyword}
【カテゴリー・ジャンル名】: {clean_title}

【最重要執筆ルール（離脱防止・CVR最大化・完全脱テンプレ）】:
1. 【「アプリで検索し直される」スキを与えない（最重要）】:
   ・記事内で具体的な「商品名」「価格」「特典内容（ポイント倍率・プレゼント等）」をすべて書ききってしまうと、読者は「あとでいつものアプリで検索して買おう」と離脱してしまいます。
   ・具体的な商品名や価格・セール特典はあえて本文中に書かず、製品の「圧倒的な魅力・使い心地・生活の変化・スペックの凄さ」のみを熱量高く伝えてください（※型番や品番、一般的なカテゴリー名・機能名は記載して問題ありません）。
   ・読者に「いまの在庫や最新価格、限定特典はどうなっているんだろう？」とリンク先を確認したくなる動機（理由）を残してください。

2. 【中性的（ジェンダーレス）かつ少しフレンドリーな口調】:
   ・「私」「あたし」「僕」などの一人称は一切使わないでください（主語は自然に省略）。
   ・「〜なの」「〜かしら」「〜わ」「〜よね」などの女性的な語尾や、「〜だぜ」「〜ぜ」などの男性的すぎる語尾は完全に禁止です。
   ・「〜ですね」「〜な点も便利」「〜なところも助かります」「〜な使い勝手」「〜してみるのもおすすめ」など、性別を感じさせないフラットで中性的、かつ親しみやすいフレンドリーなブログ口調で執筆してください。
   ・語尾がすべて「〜〜です」「〜〜ます」で終わる機械的なAI文章は厳禁です。適度に体言止めや共感・感想を織り交ぜてください。

3. 【テンプレ構文・定型句の完全禁止】:
   「そんな日常のプチストレスを解消してくれるのが〜」「実際に使って便利だと感じるポイントは〜」「日々の暮らしをより快適に整えたい方は〜」「いかがでしょうか」などの決まりきったAI構文・テンプレート表現は絶対に禁止です。
   記事ごとに冒頭の切り口、語り口、展開を商品に合わせてガラリと変えてください。

4. 【商品説明（caption）にある「その商品固有の情報」を必ず3つ以上深掘り】:
   商品情報や説明文から、その商品固有のディテール（寸法・素材名・耐荷重・カラー・取り付け方法・個包装・賞味期限・静音性など）を具体的に取り上げてください。
   ※アートパネルなら壁の雰囲気やサイズ・飾りやすさ、スイーツなら味や食感・日持ち、家具なら配置場所や収納力など、商品に100%合致した内容のみを書いてください。他の商品の特徴を絶対に混ぜないでください。

5. 【顧客が買わない理由を先回りしてさりげなく解消するセールス技法】:
   ・お客様が購入を迷う10の理由（場所をとる、部屋に合わない、設定や手入れが面倒、耐久性が不安、値段に見合うか、使いこなせるか、家族に反対されないか、音や匂い、後悔しないか等）を先回りして考え、記事内に「買わない理由」「デメリット」といった否定的な言葉は一切使わずに、魅力的なトーンの中で自然に安心感を与えて解消してください。

6. 【フォーマット】:
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

    def build_comparison_article(self, items: list, affiliate_urls: list, image_urls_list: list, category_label: str) -> str:
        """
        暖房器具・暖房家電・加湿器・乾燥対策コスメ向け：似ている人気4商品を比較する特集記事ビルダー。
        デメリットではなく「どっちがどう優れているのか・それぞれの独自の強み」をポジティブに比較して読者の購買意欲を刺激する。
        """
        if not items:
            return ""

        # クリーンタイトルの取得
        clean_items = []
        for i, it in enumerate(items[:4]):
            t = it.get("title", "")
            kw = it.get("search_keyword", "")
            ct = it.get("clean_title") or self.get_clean_product_name(t, kw)
            p = it.get("price", "")
            c = it.get("caption") or it.get("itemCaption", "")
            aff = affiliate_urls[i] if i < len(affiliate_urls) else it.get("affiliateUrl", "")
            imgs = image_urls_list[i] if i < len(image_urls_list) else []
            clean_items.append({
                "raw_title": t,
                "clean_title": ct,
                "price": p,
                "caption": c,
                "affiliate_url": aff,
                "image_url": imgs[0] if imgs else (it.get("imageUrl") or "")
            })

        items_info_text = ""
        for idx, ci in enumerate(clean_items, 1):
            items_info_text += f"\n【アイテム{idx}】: {ci['clean_title']}\n特徴・スペック: {ci['caption'][:140]}...\n"

        prompt = f"""あなたは「読者に『どれも魅力的！自分のライフスタイルにはこれがぴったり！』と納得して選ばせる人気ブロガー」です。
以下の{category_label}に関する人気アイテムを徹底比較する記事を執筆してください。

【対象商品群】:
{items_info_text}

【最重要執筆ルール（徹底的なポジティブ比較・アプリ検索離脱防止）】:
1. 【「アプリで検索し直される」スキを与えない（最重要）】:
   ・記事内で具体的な「商品名」「価格」「特典内容」をすべて書ききってしまうと、読者は「なるほど、あとでいつものアプリで検索して買おう」と離脱してしまいます。
   ・具体的な商品名や価格・セール特典はあえて本文中に書かず、製品の「圧倒的な魅力・使い心地・生活の変化・スペックの強み」のみを熱量高く伝えてください（※型番や品番、一般的な機能名・カテゴリー名は記載して問題ありません）。
   ・読者に「いまの在庫や最新価格、限定特典はどうなっているんだろう？」とリンク先を確認したくなる動機（理由）を残してください。
2. 【デメリットは書かず、各商品の『ここが圧倒的に優れている』という強みを明確に】:
   ・「〇〇はここが惜しい」といった欠点探し・ネガティブな減点方式は完全に禁止です。
   ・「速暖性ならコレ」「静音性と省エネならコレ」「持ち運びやすさとコンパクトさならコレ」「デザインと質感ならコレ」のように、どっちがどう優れていて、どんな人にベストマッチするのかを熱量たっぷりに比較してください。
3. 【段落構成（全体で4つの段落 <p>...</p>）】:
   ・段落1: 【冬の悩み共感と実力派アイテムの比較導入】（寒さや乾燥に悩む読者へ向け、どれを選んでも失敗しない注目アイテムを徹底比較するワクワクする導入）
   ・段落2: 【前半2アイテムの比較（アイテム1 vs アイテム2）】（それぞれの独自の特徴や、どっちがどんなシーンでどう優れているのかを具体的に紹介）
   ・段落3: 【後半2アイテムの比較（アイテム3 vs アイテム4）】（それぞれの強みや、どんな使い方で力を発揮するのかを深掘り）
   ・段落4: 【選び方の総括と今すぐ欲しくなる結び】（あなたの部屋や生活スタイルに合わせたおすすめの選び方を後押しする温かい結び）
4. 【フォーマット】:
   ・出力は <p>...</p> タグで囲まれた4つの段落のみを出力してください。
   ・段落内で文の区切りには <br /><br /> を挟んで読みやすくしてください。
"""
        raw_article = self._call_llm_with_retries(prompt, min_length=400, task_name="Comparison Review Article")
        
        # クリーニング
        raw_article = re.sub(r'<think>.*?</think>', '', raw_article, flags=re.DOTALL)
        raw_article = re.sub(r"^(はい、|承知いたしました。|以下が比較記事です。|以下に記事を出力します。)\s*", "", raw_article)
        
        raw_paras = re.findall(r'<p>(.*?)</p>', raw_article, flags=re.DOTALL)
        paragraphs = []
        for p in raw_paras:
            p_clean = p.strip()
            if len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', p_clean)) >= 20:
                paragraphs.append(p_clean)

        if len(paragraphs) < 4:
            # 万一の場合は整形
            blocks = [b.strip() for b in raw_article.split("\n\n") if b.strip() and not b.startswith("<")]
            paragraphs = blocks[:4] if len(blocks) >= 4 else [
                f"冬の寒さや乾燥が本格化するこの季節、快適なお部屋環境を整えるために絶対に妥協したくないのが{category_label}選びですよね。<br /><br />今回は楽天で圧倒的な人気を誇る実力派アイテムの中から、特に評価の高い注目モデルを徹底比較。それぞれの魅力や独自の強みを分かりやすくお届けします。",
                f"まず速暖性と省スペース性で抜群の支持を集めるモデルと、インテリアに美しく溶け込む上質デザインモデルの比較。<br /><br />前者はスイッチを入れて数秒で温もりや潤いを届けてくれる立ち上がりの早さが素晴らしく、後者はリビングや寝室に置いても生活感を一切感じさせない美しい佇まいが大きな魅力です。",
                f"続いて家計に優しい省エネ性能を極めたモデルと、扱いやすさ・メンテナンス性を追求したモデルの比較。<br /><br />前者は毎日長時間使っても電気代を気にせずぬくぬく過ごせる安心感があり、後者はお手入れや給水が驚くほど簡単でストレスフリーに使い倒せる実用性が光ります。",
                f"どれも確かな性能と優れた使い心地を兼ね備えており、設置場所やお好みのライフスタイルに合わせて選べば今年の冬が劇的に快適になること間違いなし。<br /><br />本格的な寒さが到来する前に、ぜひお気に入りの一台を手に入れて心温まる快適な冬をお過ごしください。"
            ]

        # 4つの商品をカード型風に綺麗に並べるHTMLを構築
        full_html_parts = []
        
        # 導入段落
        full_html_parts.append(f"<p>{paragraphs[0]}</p>\n")
        
        # 4商品の紹介ブロック（各商品画像＋型番・特徴＋現在の在庫・最新価格の確認ボタン）
        items_grid_html = '<div style="margin: 20px 0; padding: 10px; background-color: #faf8f5; border-radius: 12px; border: 1px solid #eee;">\n'
        items_grid_html += f'<h3 style="font-size: 15px; color: #333; margin: 4px 0 14px 4px; text-align: center; font-weight: bold;">＼ 編集部厳選！注目の人気4選 ／</h3>\n'
        for idx, ci in enumerate(clean_items, 1):
            items_grid_html += (
                f'<div style="margin-bottom: 16px; padding: 12px; background-color: #ffffff; border-radius: 8px; border: 1px solid #f0f0f0;">\n'
                f'  <div style="font-weight: bold; font-size: 14px; color: #ff6f00; margin-bottom: 6px;">エントリーNo.{idx}: {ci["clean_title"]}</div>\n'
                f'  <div style="text-align: center; margin: 8px 0;">\n'
                f'    <a href="{ci["affiliate_url"]}" target="_blank" rel="noopener noreferrer">\n'
                f'      <img src="{ci["image_url"]}" alt="{ci["clean_title"]} 比較" style="max-width: 80%; height: auto; border-radius: 6px; display: block; margin: 0 auto;" />\n'
                f'    </a>\n'
                f'  </div>\n'
                f'  <div style="text-align: center; font-size: 12px; color: #666; margin: 6px 0;">※現在の在庫状況・最新価格・特典の有無は下記よりご確認ください</div>\n'
                f'  <div style="text-align: center; margin-top: 8px;">\n'
                f'    <a href="{ci["affiliate_url"]}" target="_blank" rel="noopener noreferrer" style="display: inline-block; padding: 9px 24px; background-color: #ff6f00; color: #ffffff; border-radius: 18px; font-size: 13px; font-weight: bold; text-decoration: none;">現在の在庫・最新の価格・特典の有無はこちら</a>\n'
                f'  </div>\n'
                f'</div>\n'
            )
        items_grid_html += '</div>\n'
        full_html_parts.append(items_grid_html)

        # 比較段落2〜4
        for p in paragraphs[1:]:
            full_html_parts.append(f"<p>{p}</p>\n")

        # ブロ活広告タグ
        full_html_parts.append('<pointad pointad-id="div-plaza-point-ad" pointad-text="#ブロ活広告#" />')
        return "".join(full_html_parts)

    def build_full_featured_article(self, item: Dict[str, Any], image_urls: list, affiliate_url: str) -> str:
        """
        ユーザー見本記事（木目調ケーブルボックス・Amazonラック）と同等の高い完成度と情報密度を実現するレビュー記事ビルダー。
        ・必ず4つの充実した段落（各段落150〜230文字、全体で700〜900文字の読み応えある文章）
        ・画像は2〜3枚に厳選し、必ず「段落1（商品紹介）の直後に1枚目画像」が来る美しいサンドイッチ配置
        ・レイアウト構成:
          段落1（日常の悩み・共感 → 出会い → アイテムの魅力紹介）
          画像1（全体像）
          CTAボタン（現在の在庫・最新の価格・特典の有無はこちら）
          段落2（届いた瞬間の印象・佇まい・部屋や食卓への馴染みやすさ）
          画像2（収納イメージ・利用風景）
          段落3（手軽さ・素材感・サイズ・機能性・固有スペックの深掘り）
          画像3（仕様・ディテール、画像が2枚の場合は段落3のみ）
          段落4（実際の使い心地・生活の変化・誰におすすめか・今すぐ試したくなる強い推奨）
          末尾CTAボタン（現在の在庫・最新の価格・特典の有無はこちら）
          ブロ活広告タグ
        """
        title = item.get("title", "")
        search_keyword = item.get("search_keyword", "")
        clean_title = item.get("clean_title") or self.get_clean_product_name(title, search_keyword)
        caption = item.get("caption", "")
        
        # 使用する画像の枚数（2〜3枚に厳選）
        num_images = max(2, min(len(image_urls), 3))
        
        # 商品ジャンルを正確に判定
        genre = self._detect_genre(clean_title, search_keyword, caption)

        # ジャンル別の4段落ガイドライン（他ジャンルの特徴の混入を完全防止）
        if genre == "heating":
            genre_guide = f"""
   ・段落1（約130〜180文字）: 【冬の寒さ悩みと出会い】「朝起き抜けの冷え込みや足元の底冷えが辛い」という切実な悩みと、「スイッチを入れて数秒で足先からポカポカと温まる極上の快適さ」をズバッと提示し、「真冬の寒さを乗り切るために迎えたのが、この注目アイテムです。」と紹介。
   ・段落2（約140〜190文字）: 【省スペース性・デザイン・速暖性の優位性】お部屋のインテリアを邪魔しないスリムで洗練された佇まい。他の暖房器具と比べても立ち上がりが驚くほど早く、場所を取らずに置ける利便性を描写。
   ・段落3（約140〜190文字）: 【電気代・安全性・静音性の深掘り】省エネ設計による家計への優しさ、チャイルドロックや転倒時自動オフなどの安全機能、就寝時や仕事中も気にならない静音性など、安心・実用スペックを深掘り。
   ・段落4（約130〜180文字）: 【生活の変化・心温まる結び】寒さに震えることなく家族や自分が快適に冬を過ごせる喜び。「手軽に確かな暖かさを手に入れたい」と願う読者へ向けて、自信を持った熱い推薦。
   ※デメリットの羅列は避け、どこがどう優れているのか魅力を伝えてください。"""
        elif genre == "blanket":
            genre_guide = f"""
   ・段落1（約130〜180文字）: 【圧倒的な暖かさ＆出会い】「冬の朝晩の冷え込みでリラックスできない」という悩みを語りつつ、「羽織った瞬間、まるで体温を逃さず閉じ込める魔法のようなぬくもり」という最高の暖かさを提示し、「冬のおうち時間を至福に変えてくれたのが、この極上アイテムです。」と紹介。
   ・段落2（約140〜190文字）: 【肌触りの心地よさ・どれくらい暖かいかの実感】指先が埋もれるような極上のふわとろ質感、冷気をシャットアウトしてじんわり熱がこもる圧倒的な保温力を五感に訴える表現で描写。
   ・段落3（約140〜190文字）: 【軽さ・動きやすさ・丸洗いの清潔さ】しっかり暖かいのに肩が凝らない軽やかさ、着たまま動ける便利さ、自宅の洗濯機でネットに入れて丸洗いできる手入れのラクさを深掘り。
   ・段落4（約130〜180文字）: 【冬のくつろぎ・今すぐ欲しくなる結び】暖房の温度を上げすぎずエコにぬくぬく過ごせる幸せ。「一度くるまったらもう手放せない暖かさ」を求める読者へ、背中を押す自然な推薦。
   ※デメリットは不要で、どれだけ暖かく心地よいかを伝えてください。"""
        elif genre == "humidifier":
            genre_guide = f"""
   ・段落1（約130〜180文字）: 【冬の乾燥悩みと出会い】「朝起きると喉や肌がカサカサする」「暖房による乾燥が気になる」という悩みと、「お部屋の空気が一瞬でしっとり潤い、呼吸がスッとラクになる」という変化を提示し、「冬の乾燥対策に選んだのが、この注目アイテムです。」と紹介。
   ・段落2（約140〜190文字）: 【加湿スピード・ミストの細かさ・インテリアへの調和】床や家具を濡らさない微細なミスト、生活感を感じさせないスタイリッシュな佇まいを生き生きと描写。
   ・段落3（約140〜190文字）: 【給水の手軽さ・静音性・省エネ性能】上から注ぐだけで簡単な給水設計、夜間でも全く気にならない静音動作、電気代を抑えながら長時間連続運転できるタフな実用性を深掘り。
   ・段落4（約130〜180文字）: 【潤いのある暮らし・強い推奨】喉やお肌の潤いが保たれ、風邪予防にも心強い充実感。「乾燥する冬を心地よく健康に過ごしたい」と願う読者へ向けて熱く推薦。
   ※他のタイプと比べてどう優れているのか（上部給水の手軽さや静音性など）を前向きに伝えてください。"""
        elif genre == "skincare":
            genre_guide = f"""
   ・段落1（約130〜180文字）: 【冬の乾燥肌・手荒れ悩みと出会い】「アルコール消毒や冬の寒風で手肌や唇がカサつく」という切実な悩みと、「塗った瞬間からしっとりとした潤いのヴェールに包まれる感動」を冒頭で提示し、「乾燥知らずの肌を叶えてくれたのが、この実力派アイテムです。」と紹介。
   ・段落2（約140〜190文字）: 【テクスチャー・密着感・ベタつかない使い心地】スーッと肌に馴染んで角質層まで浸透する心地よさ、ベタつかずすぐにスマホやパソコンに触れられる上質な使用感を描写。
   ・段落3（約140〜190文字）: 【高保湿成分・持続力・上品な香りや無香料の安心感】シアバターやセラミドなどの厳選保湿成分、水仕事をしても落ちにくい密着保護力、持ち歩きたくなる洗練されたパッケージを深掘り。
   ・段落4（約130〜180文字）: 【潤いのある自信・心温まる結び】指先や唇がしっとり整うだけで気分まで明るくなる変化。「冬の乾燥から肌を優しく守り抜きたい」と願う読者へ、心からの推薦。
   ※デメリットではなく、保湿力や使用感の優れたポイントをスマートに伝えてください。"""
        elif genre == "osechi":
            genre_guide = f"""
   ・段落1（約130〜180文字）: 【お正月の特別な食卓＆出会い】「家族で迎える新年の始まりには、誰もが笑顔になれる本物の味を囲みたい」という思いと、「名店・老舗の匠の技が詰まった極上の祝膳」という最高のおもてなし価値を提示し、「お正月を贅沢に彩るために選んだのが、この逸品です。」と紹介。
   ・段落2（約140〜190文字）: 【重箱を開けた瞬間の豪華絢爛な佇まい・シズル感】蓋を開けた瞬間に歓声が上がる美しい盛り付け、厳選された山海の幸が放つ華やかな色彩と豊かな香りを五感に訴える表現で描写。
   ・段落3（約140〜190文字）: 【素材へのこだわり・解凍の手軽さ・安心品質】伝統的な縁起物から現代風の逸品まで飽きずに楽しめるバランス、冷凍技術の進化による出来立ての美味しさ、年末に届いてそのまま食卓に出せる手軽さを深掘り。
   ・段落4（約130〜180文字）: 【家族の笑顔・予約推奨の結び】お正月の準備に追われることなく、家族みんなでゆったり贅沢な時間を堪能できる満足感。「ハズさない名店のおせちで最高の一年をスタートさせたい」と願う読者へ自信を持った推薦。"""
        elif genre == "bath":
            genre_guide = f"""
   ・段落1（約130〜180文字）: 【冬の冷え・疲労と出会い】「真冬の寒さで体の芯まで冷え切ってしまう」「一日の疲れをじんわりほぐしたい」という悩みと、「お湯に溶かした瞬間、温泉宿に来たような濃厚な温まり」という核心のベネフィットを提示し、「冷えた体を至福のぬくもりで満たしてくれたのが、このアイテムです。」と紹介。
   ・段落2（約140〜190文字）: 【お湯の肌当たり・豊かな香り・リラックス感】とろりとなめらかに変わるお湯の質感、浴室いっぱいに広がる心地よい香り、強張った体がふわりとほぐれていくリラックスタイムを描写。
   ・段落3（約140〜190文字）: 【有効成分・温浴効果・湯冷めしにくさ】重炭酸や天然ミネラルによる確かな温浴効果、お風呂から上がった後もポカポカが長く続く保温力、肌がしっとり潤うスキンケア効果を深掘り。
   ・段落4（約130〜180文字）: 【極上の睡眠・心温まる結び】体の芯から温まることで夜もぐっすり心地よく眠れる充実感。「毎日のバスタイムをご褒美の時間に変えたい」と願う読者へ向けて熱く推薦。"""
        elif genre == "sweets":
            genre_guide = f"""
   ・段落1（約130〜180文字）: 【冬の贅沢スイーツ＆出会い】「寒い冬のティータイムには、一口で心が満たされる濃厚で特別なスイーツが食べたい」という思いと、「おうちカフェが一瞬で高級専門店の特等席に変わる」という最高の感動を提示し、「冬の特別な時間を届けてくれたのが、この極上スイーツです。」と紹介。
   ・段落2（約140〜190文字）: 【開封のシズル感・香り・極上の口どけ】箱を開けた瞬間に立ちのぼる芳醇な香り、舌の上でゆっくり溶けていく濃厚なコクや、贅沢な口どけを五感に訴える表現で描写。
   ・段落3（約140〜190文字）: 【厳選素材・珈琲や紅茶との相性・個包装の便利さ】選び抜かれた上質な素材のこだわり、温かい飲み物と合わせた時のマリアージュ、手土産やギフトにも恥ずかしくない上質な仕様を深掘り。
   ・段落4（約130〜180文字）: 【日常のご褒美・自信の推薦】一年頑張った自分へのご褒美としてはもちろん、大切な人と囲んでも絶対に喜ばれる安心感。「一口で笑顔になれる特別な美味しさ」を味わいたい読者へ、自信を持ってお勧め。
   ※フルーツ単体の話や無関係な家具等の話は完全禁止。"""
        else:
            genre_guide = f"""
   ・段落1（約130〜180文字）: 【快適な暮らし＆出会い】暮らしのちょっとしたストレスや悩みを語りつつ、「生活が驚くほど快適に整った」という核心のメリットを提示し、「そんな悩みを解消してくれたのが、このアイテムです。」と紹介。
   ・段落2（約140〜190文字）: 【佇まい・サイズ感・インテリアへの調和】お部屋の雰囲気を壊さない上質なデザイン、扱いやすいサイズ感や素材の質感を生き生きと描写。
   ・段落3（約140〜190文字）: 【実用スペック・使い勝手の良さ】日常の使いやすさ、サッと使える手軽さ、日々のストレスを減らす嬉しい工夫を深掘り。
   ・段落4（約130〜180文字）: 【心地よい暮らし・背中を押す結び】おうち時間がもっと好きになる変化、「居心地のいいお部屋を作りたい」と願う読者へ熱く推薦。"""

        prompt = f"""あなたは「本当に良いものを自分の言葉で本音レビューし、読者に『今すぐ欲しい！』と思わせる大人気の暮らしブロガー」です。
以下の商品情報を徹底的に読み込み、定型文や使い回しのテンプレート感を完全に排除して、この製品「だけ」にしかない魅力・スペック・使い勝手を、テンポよく歯切れの良い魅力的な文章で執筆してください。

【商品特徴・説明】: {caption}
【検索キーワード】: {search_keyword}
【カテゴリー・ジャンル名】: {clean_title}
【希望段落数】: 必ず4つの段落（<p>...</p>）を出力してください。文字数は全体で600〜750文字の最も読みやすいボリュームにしてください。

【プロブロガー直伝・極上の執筆ルール（離脱防止・脱・AI調・テンポ重視・重複排除）】:
1. 【「アプリで検索し直される」スキを与えない（最重要・厳格遵守）】:
   ・記事の中で具体的な「商品名」「価格」「特典内容（ポイント倍率・プレゼント等）」をすべて書ききってしまうと、読者は「なるほど、あとでいつものアプリで検索して買おう」とページを離脱してしまいます。
   ・そのため、具体的な商品名や正確な販売価格、セール特典の詳細はあえて本文中に書かず、製品の「圧倒的な魅力・使い心地・生活の変化・優れたスペック」のみを熱量高く伝えてください。
   ・ただし、型番や品番（例: BR-01, KN-HW24Gなど）や一般的なカテゴリー名（例: セラミックファンヒーター、木製キーフック）は記載して構いません。
   ・読者に「いまの在庫や最新価格、限定特典はどうなっているんだろう？」とリンク先を確認したくなる動機（理由）を残してください。

2. 【冒頭から「一番伝えたいこと（Before/After）」をズバッと語る】:
   ・前置きが長くて回りくどい文章は読者が離脱します。段落1の冒頭から、「何に悩み、このアイテムのおかげで生活がどう劇的に変わったのか（床がピカピカになった、朝の目覚めが軽くなった、おうちカフェが至福になった等）」という核心のベネフィットを真っ先に伝えてください。
   ・その流れで自然に「そんな悩みを解消してくれたのが、このアイテムでした」「そこで出会ったのが、この頼もしい逸品です」のように紹介し、読者を一気に引き込んでください。文頭に「〜と出会ったのが」のような記号（〜）や途切れた文章を絶対に出力しないでください。

3. 【同じ情報の重複を徹底排除（保証期間やスペックを2回以上言わない）】:
   ・「保証期間が2年」「静音性」「水拭き」など、同じセールスポイントを別の段落で何度も繰り返すのは素人っぽく見えるため厳禁です。
   ・各段落で語る役割（段落1: 核心の悩み解決と出会い / 段落2: 届いた時の佇まい・サイズ感・第一印象 / 段落3: 実際の機能・使い勝手・お手入れ / 段落4: 手に入れた生活のゆとりと強い推奨）を明確に分担し、一度書いた情報は他の段落では触れないでください。

4. 【硬い説明調・回りくどい表現を捨て、軽快で心地よい文リズムに】:
   ・「〜であることを実感させられます」「〜といった点において優位性があります」といった硬いレビュー調や取扱説明書の要約は禁止です。
   ・「〜なのが本当に助かる」「〜で一気にストレスが消えた」「〜な佇まいがお気に入り」など、中性的でセンスの良いブロガーが友人に熱く語りかけるような、自然で感情の乗った軽快なトーンにしてください。
   ・「です」「ます」の単調な繰り返しを避け、体言止めや感嘆を織り交ぜて心地よいリズムを作ってください（一人称「私」「僕」は使わない）。

5. 【顧客が買わない理由を先回りしてさりげなく解消する極上セールス技法】:
   ・お客様が購入を迷ったり見送ったりする「買わない理由」の代表的な懸念（「場所を取る・大きすぎないか」「部屋のインテリアから浮かないか・安っぽくないか」「組み立てや設定が難しくないか」「お手入れや掃除が面倒ではないか」「耐久性や品質は大丈夫か」「使いこなせず無駄にならないか」「家族や同居人に反対されないか」「音がうるさくないか・匂いがきつくないか」「買って後悔しないか」等）を心の中で10個想定してください。
   ・【絶対禁止ルール】: 記事内に「買わない理由」「デメリット」「懸念点」「購入を見送る理由」「〜という不安があるかもしれませんが」といったネガティブな直接的見出しや語句は一切出さないでください。
   ・【必須ルール】: 魅力やメリットを伝える自然な文章の中で、それらの不安や迷いを先回りして優しく払拭してください（例：「コンパクトで圧迫感がない」「水洗いできてお手入れが一瞬」「届いてすぐ迷わず使える」「どんなお部屋にもスッと溶け込む上質な質感」など、読者が読むだけで知らず知らずのうちに不安が消え、安心して『欲しい！』と思えるスマートで綺麗なセールス文章に昇華させてください）。

6. 【ジャンルに100%合致した段落構成】:
   段落テーマ目安：{genre_guide}

7. 【フォーマット（読みやすい改行の徹底）】:
   ・出力は <p>...</p> タグで囲まれた4つの段落のみを出力してください（見出しタグ、divタグ、ボタン、リストは含めないでください）。
   ・段落内で1つの文章が終わって違う話題や視点に移る時は、詰まりすぎないよう文の区切りに <br /><br /> を挟んで、スマホでもスッと頭に入る読みやすい行間にしてください。
"""
        raw_article = self._call_llm_with_retries(prompt, min_length=400, task_name="Full Review Article", item_context={**item, "clean_title": clean_title})
        
        # メタ文言・JSONラッパー・思考タグのクリーニング
        if raw_article.strip().startswith("{") and "content" in raw_article:
            try:
                parsed = json.loads(raw_article, strict=False)
                if isinstance(parsed, dict) and "content" in parsed:
                    raw_article = str(parsed["content"])
            except Exception:
                pass
        raw_article = re.sub(r'<think>.*?</think>', '', raw_article, flags=re.DOTALL)
        raw_article = re.sub(r"^(はい、|承知いたしました。|以下が商品紹介記事です。|以下に記事を出力します。|以下が執筆した記事です。)\s*", "", raw_article)
        
        # 段落（<p>タグ）を抽出
        raw_paras = re.findall(r'<p>(.*?)</p>', raw_article, flags=re.DOTALL)
        paragraphs = []
        for p in raw_paras:
            p_clean = p.strip()
            # 思考メモやJSONキーを含む段落を除外
            if any(term in p_clean for term in ['"role":', '"reasoning":', 'assistant', 'We need to']):
                continue
            # 日本語（ひらがな・カタカナ・漢字）がしっかり含まれる文章のみ採用
            if len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', p_clean)) >= 20:
                paragraphs.append(p_clean)

        if not paragraphs:
            # <p>タグがない場合は改行で分割
            raw_blocks = [b.strip() for b in raw_article.split("\n\n") if b.strip()]
            for b in raw_blocks:
                if not b.startswith("<") and len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', b)) >= 20:
                    paragraphs.append(b)

        # 4段落未満、または総文字数が500文字未満の場合はリッチな安全4段落フォールバックを使用
        total_chars = sum(len(p) for p in paragraphs)
        if len(paragraphs) < 4 or total_chars < 500:
            paragraphs = self._build_safe_genre_paragraphs(item)

        # 投稿前の品質・AI臭さ・ジャンル整合性チェック＆1文ごとの話題切り替え改行（<br /><br />）整形
        paragraphs = self._validate_and_polish_paragraphs(paragraphs, {**item, "clean_title": clean_title})

        # 画像リストの整備（2〜3枚に厳選）
        clean_images = []
        for img in image_urls:
            if img and img not in clean_images:
                clean_images.append(img)
                if len(clean_images) >= 3:
                    break
        
        # 足りない場合はフォールバック
        if not clean_images:
            clean_images = ["https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&auto=format&fit=crop&q=80"]
        while len(clean_images) < 2:
            clean_images.append(clean_images[-1])

        # CTAボタンのスタイル定義（アプリ検索離脱を防ぎ、確認動機を与えるクリック導線）
        cta_btn = (
            f'<div style="text-align: center; margin: 18px 0 14px 0;">'
            f'<div style="font-size: 12px; color: #666; margin-bottom: 6px;">※現在の在庫状況・最新価格・限定特典の有無はこちらから確認できます</div>'
            f'<a href="{affiliate_url}" target="_blank" rel="noopener noreferrer" style="display: inline-block; width: 90%; max-width: 360px; padding: 13px 0; background-color: #ff6f00; color: #ffffff; border: 1px solid #ff6f00; border-radius: 20px; font-size: 14px; font-weight: bold; text-align: center; text-decoration: none; box-shadow: 0 2px 6px rgba(255,111,0,0.25);"><span style="text-decoration: none;">現在の在庫・最新の価格・特典の有無はこちら</span></a>'
            f'</div>'
        )

        # ジャンル別の画像alt文言（家具以外のジャンルに棚や引き出しを絶対に出さない）
        if genre == "heating":
            alt_suffixes = ["全体像・デザイン", "お部屋の設置イメージ", "操作パネル・スイッチ詳細", "サイズ感・スリムさ", "暖房性能・速暖イメージ", "活用シーン"]
        elif genre == "blanket":
            alt_suffixes = ["全体像", "もこもこ肌触り・素材感", "着用・利用イメージ", "厚み・保温構造", "カラー・サイズ感", "くつろぎシーン"]
        elif genre == "humidifier":
            alt_suffixes = ["本体デザイン・全体像", "お部屋設置イメージ", "給水口・ミスト吹き出し口", "操作部・タイマー表示", "サイズ感", "加湿シーン"]
        elif genre == "skincare":
            alt_suffixes = ["パッケージ・全体像", "テクスチャー・伸びの良さ", "容器・キャップ詳細", "サイズ・持ち運び感", "成分・こだわり", "ケアシーン"]
        elif genre == "osechi":
            alt_suffixes = ["重箱全体像・盛り付け", "一の重・伝統祝膳", "二の重・山海の幸", "三の重・名店の味", "お重パッケージ・風呂敷", "お正月の食卓イメージ"]
        elif genre == "bath":
            alt_suffixes = ["全体像・パッケージ", "お湯の溶け方・にごり感", "有効成分・バスソルト詳細", "サイズ・内容量", "香りと癒やしイメージ", "活用シーン"]
        elif genre == "sweets":
            alt_suffixes = ["商品パッケージ・全体像", "断面・濃厚なシズル感", "盛り付け・ティータイム", "個包装・内容量", "厳選素材・こだわり", "ギフト・お届け状態"]
        else:
            alt_suffixes = ["全体像", "利用風景・使用イメージ", "仕様・ディテール", "側面・サイズ感", "素材感と質感", "活用シーン"]

        # ユーザー見本＆ご要望に100%合致するレイアウト構成（画像・CTA上下の改行を1行に統一）:
        # 段落1（商品紹介）
        # → 画像1（クリックで商品ページへ遷移）
        # → 冒頭写真直下のCTAボタン
        # → 段落2
        # → 画像2（クリックで商品ページへ遷移）
        # → 段落3
        # → 画像3（存在する場合・クリックで商品ページへ遷移）
        # → 段落4（生活の変化・おすすめ結び）
        # → 末尾CTAボタン
        # → ブロ活広告タグ
        full_html_parts = []
        for i, p_text in enumerate(paragraphs):
            # 段落（テキスト）
            full_html_parts.append(f"<p>{p_text.strip()}</p>\n")

            # 画像の挿入（段落の直後、画像の枚数分だけ配置。aタグでラップして画像クリックで商品ページへ遷移可能に）
            if i < len(clean_images):
                img_url = clean_images[i]
                alt_suffix = alt_suffixes[i % len(alt_suffixes)]
                alt_text = f"{clean_title} {alt_suffix}"
                img_html = (
                    f'<div><a href="{affiliate_url}" target="_blank" rel="noopener noreferrer">'
                    f'<img style="max-width: 100%; height: auto; border-radius: 8px; display: block; margin: 12px auto;" src="{img_url}" border="0" alt="{alt_text}" />'
                    f'</a></div>\n'
                )
                full_html_parts.append(img_html)

                # 冒頭の写真（画像1枚目）の直下にCTAボタンを配置
                if i == 0:
                    full_html_parts.append(f"{cta_btn}\n")

        # 記事末尾のCTAボタン
        full_html_parts.append(f"{cta_btn}\n")

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
        """楽天市場のノイズが多い商品名から、具体的でシンプルな商品名（名詞のみ・15文字以内）を抽出する。"""
        system_prompt = "あなたは入力されたテキストから無駄な修飾語を取り除き、商品名そのもの（名詞）のみを抽出する優秀なアシスタントです。解説は一切含めず、商品名のみを1行で出力してください。"
        prompt = f"""以下の楽天市場の商品名から、送料無料、サイズ、型番、アピール用の形容詞（おしゃれ、大人気など）、機能名（静音、USB、急速充電、省エネなど）をすべて排除し、その商品が「何であるか」を示す具体的でクリーンな商品名（例：『木枠ウォールミラー』『珪藻土バスマット』『分別ゴミ箱』『ノートPC冷却ファン』『ケーブルボックス』など）を日本語で15文字以内で抽出してください。
末尾が不自然に途切れたり（例:「〜 静音 U」などの途切れ）、不要な修飾語が残らないように、自然な名詞のみを抽出してください。
余計な解説や括弧、引用符、Markdown等は一切含めず、抽出した商品名テキストのみを出力してください。

【楽天市場の商品名】: {title}
【検索時のキーワード】: {search_keyword}
"""
        raw_name = self._call_llm_with_retries(prompt, system_prompt=system_prompt, min_length=2, task_name="Clean Product Name", item_context={"title": title, "search_keyword": search_keyword})
        
        # 思考タグやマークダウン、引用符を除去
        raw_name = re.sub(r'<think>.*?</think>', '', raw_name, flags=re.DOTALL)
        # 改行がある場合は先頭行を採用
        lines = [line.strip() for line in raw_name.split('\n') if line.strip()]
        first_line = lines[0] if lines else ""
        cleaned = re.sub(r'<[^>]+>|[\"\'「」『』【】\n\r*`]', '', first_line).strip()
        cleaned = re.sub(r'^(商品名[:：]|クリーン商品名[:：]|抽出結果[:：])\s*', '', cleaned)
        
        # 末尾の不自然な途切れ文字（孤立した英数字や記号）を除去（例: "ノートPC冷却ファン 静音 U" -> "ノートPC冷却ファン 静音"）
        cleaned = re.sub(r'[\s　]+[A-Za-z0-9]$', '', cleaned).strip()
        # 末尾に残った不要な機能名・修飾語を除去
        cleaned = re.sub(r'[\s　]+(静音|小型|軽量|急速|省エネ|大容量|北欧|おしゃれ|人気|おすすめ|用|式)$', '', cleaned).strip()
        # 再度末尾の孤立英字をチェック
        cleaned = re.sub(r'[\s　]+[A-Za-z0-9]$', '', cleaned).strip()

        if cleaned and 2 <= len(cleaned) <= 20:
            return cleaned[:18]

        # フォールバック時もキーワードから修飾語をカット
        kw_clean = re.sub(r'[\s　]+(静音|小型|軽量|急速|省エネ|大容量|北欧|おしゃれ|人気|おすすめ|用|式|[A-Za-z0-9])$', '', search_keyword).strip()
        return kw_clean[:15] if kw_clean else search_keyword[:15]

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
        """Gemini APIキーを使って利用可能な最新モデル一覧を動的に取得する（1.5系除外、画像生成・TTS除外）"""
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
                            # TTSや画像モデルなどテキスト生成に不適なモデルを除外
                            if any(ex in m_name.lower() for ex in ["tts", "image", "embedding", "aqa"]):
                                continue
                            if m_name and (ver, m_name) not in valid_models:
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
                ("v1beta", "gemini-2.0-flash"),
                ("v1beta", "gemini-2.0-flash-lite"),
                ("v1beta", "gemini-2.5-flash"),
                ("v1beta", "gemini-2.5-flash-lite"),
                ("v1beta", "gemini-3.1-pro-preview"),
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
            "nvidia/nemotron-3.5-lightning:free",
            "liquid/lfm-2.5-2.6b:free",
            "google/gemma-4-26b-a4b-it:free",
            "google/gemma-4-31b-it:free",
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
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
                # JSONラッパーやreasoningが含まれる場合のクレンジング
                if text.startswith("{") and "content" in text:
                    try:
                        parsed = json.loads(text, strict=False)
                        if isinstance(parsed, dict) and "content" in parsed:
                            text = str(parsed["content"]).strip()
                    except Exception:
                        m = re.search(r'"content"\s*:\s*"(.*?)"(?:\s*,\s*"[a-zA-Z_]+":|\s*})', text, flags=re.DOTALL)
                        if m:
                            text = m.group(1).replace(r'\"', '"').replace(r'\n', '\n')
                # 思考タグの除去
                text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
                if text and len(text) > 10:
                    return text
        except Exception as e:
            print(f"DEBUG: Pollinations AI failed: {e}")
        return None
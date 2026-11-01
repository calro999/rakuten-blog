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
        if any(w in text for w in ["枕", "まくら", "ピロー", "マットレス", "布団", "毛布", "タオルケット", "敷きパッド", "快眠", "安眠", "首こり", "肩こり", "いびき", "バスタオル", "タオル", "入浴剤", "バスボム", "シャワーヘッド", "マッサージ", "アイマスク"]):
            return "bath_sleep"
        if any(w in text for w in ["スイーツ", "和菓子", "洋菓子", "お菓子", "プリン", "ケーキ", "チョコ", "クッキー", "バウムクーヘン", "大福", "どら焼き", "カステラ", "マカロン", "ジェラート", "アイス", "アップルパイ", "饅頭", "タルト", "ロールケーキ", "カヌレ", "フィナンシェ"]):
            return "sweets"
        if any(w in text for w in ["肉", "牛", "豚", "鶏", "米", "フルーツ", "果物", "海鮮", "カニ", "エビ", "魚", "グルメ", "惣菜", "ハンバーグ", "餃子", "うどん", "ラーメン"]):
            return "food"
        if any(w in text for w in ["食器", "プレート", "急須", "コップ", "マグカップ", "グラス", "皿", "箸", "カトラリー", "キャニスター", "ボウル", "フライパン", "鍋", "包丁", "ブレッドケース", "水切り", "ケトル", "キッチンマット"]):
            return "kitchen"
        if any(w in text for w in ["掃除機", "加湿器", "除湿機", "扇風機", "サーキュレーター", "ヒーター", "ドライヤー", "スピーカー", "電動歯ブラシ", "アイロン", "スチーマー", "空気清浄機"]):
            return "appliance"
        if any(w in text for w in ["ケーブルボックス", "配線", "モニタースタンド", "ノートパソコンスタンド", "充電器", "電源タップ", "デスクマット", "マウスパッド", "ガジェット"]):
            return "desk_gadget"
        if any(w in text for w in ["ライト", "照明", "ランプ", "キャンドル", "時計", "ミラー", "鏡", "アートパネル", "ポスター", "花瓶", "ディフューザー", "アロマ"]):
            return "decor"
        if any(w in text for w in ["家具", "テーブル", "チェスト", "ラック", "ワゴン", "ソファー", "チェア", "ラグ", "カーテン", "収納", "棚", "スツール", "ハンガー", "傘立て", "ボックス", "ケース", "ベッド"]):
            return "furniture"
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

    def _build_safe_genre_article(self, item: Dict[str, Any]) -> str:
        clean_title = item.get("clean_title", "おすすめ商品")
        caption = item.get("caption", "")
        keyword = item.get("search_keyword", "")
        genre = self._detect_genre(clean_title, keyword, caption)

        if genre == "bath_sleep":
            p1 = f"<p>朝目が覚めたときに首や肩へずっしりと重みが残っていたり、しっかり寝たはずなのに疲れが抜けきらなかったり……そんな睡眠のプチ不調、地味に日々の活力を奪っていきますよね。寝具を一から買い替えるのはハードルが高いものの、毎日の睡眠環境をもっと心地よく整えたいと本気で探していたところに出会ったのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>実際に頭を預けて横になってみた瞬間、<b>頭部から首筋の隙間に吸い付くようにフィット</b>し、余計な緊張がすっとほどけていく感覚に驚かされます。寝返りを打っても頭が落ちにくく、理想的な寝姿勢を自然な形でサポートしてくれるため、夜中に何度もポジションを探して目が冴えてしまうストレスから解放されました。</p>"
            p3 = f"<p>生地の肌触りや通気性にもしっかりと配慮されており、<b>熱がこもらず朝までさらりと快適な使い心地</b>が続くのも嬉しいところ。カバーの手入れも簡単で毎日気持ちよく清潔を保てる頼もしさがあり、毎朝すっきりと軽やかに一日をスタートさせたい方に心からおすすめしたい快眠アイテムです。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}"

        elif genre == "sweets":
            p1 = f"<p>仕事や家事の合間に、温かいお茶や淹れたての珈琲を片手にほっと一息つける時間があると、それだけで張り詰めていた気持ちがふわりとほぐれていきますよね。たまには自分へのとっておきのご褒美として、あるいは大切な人を喜ばせる手土産として、心から満足できる本物の甘味を味わいたい……そんな願いにぴったり寄り添ってくれたのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>届いて丁寧に包まれた箱を開けた瞬間、素材の良さを物語るふくよかな香りが立ちのぼり、思わずうっとり。ひとくち口に運ぶとしっとりと濃密なコクが広がり、<b>舌の上でゆっくりとほどけていく贅沢な口どけ</b>がたまりません。熟練の職人が手間暇を惜しまず丁寧に焼き上げているからこそ出せる、上品で奥深い甘みが日常を特別なひとときに変えてくれます。</p>"
            p3 = f"<p>素材本来の風味が見事に引き出されており、<b>珈琲の豊かな苦味や緑茶の渋みとも相性抜群</b>。個包装やカット済みの配慮も行き届いているため、包丁を汚す手間もなくいつでも気軽に極上の味を楽しめるのが本当に重宝します。自分へのとっておきのご褒美としてはもちろん、贈り物としても自信を持って手渡せる大満足の逸品です。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}"

        elif genre in ["food", "furusato"]:
            p1 = f"<p>毎日忙しく過ごしているからこそ、一日の終わりの食卓や休日のごはんには、思わず笑顔がこぼれるような本当に美味しいものが欲しくなりますよね。外食に出かける時間はないけれど、自宅で手軽に専門店や名産地ならではの贅沢な味を堪能したい……そんな食のこだわりを満たしてくれたのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>届いて梱包を開いた瞬間から伝わってくる上質さと鮮度の良さに、食べる前から期待が一気に高まります。実際に火を通して味わってみると、<b>噛みしめるたびにあふれ出す豊かな旨味と香ばしさ</b>が口いっぱいに広がり、普段の食卓が一瞬にして専門店の特等席へとグレードアップするような贅沢感を噛み締められます。</p>"
            p3 = f"<p>調理の手順もシンプルで扱いやすく、<b>冷凍ストックや日持ちの良さまで計算された頼もしい仕上がり</b>。忙しい日の「あと一品」にも、家族や友人が集まる特別な日のおもてなしにも大活躍してくれて、一度知ってしまうと冷凍庫や常備品に欠かせなくなる逸品です。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}"

        elif genre == "kitchen":
            p1 = f"<p>毎日の料理や後片付けのたびに、ちょっとした使いにくさや生活感の溢れる佇まいにモヤモヤしてしまうことってありませんか。かといって大掛かりな台所リフォームや高価な器具の総入れ替えをするほどでもないし……と悩んでいたところに出会ったのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>実際にキッチンに迎えてみたとき、無駄な凹凸や装飾をそぎ落とした洗練された佇まいとお部屋に馴染む質感にまず惚れ惚れしました。毎日自然と手に取りたくなる手馴染みの良さがあり、<b>調理中のわずらわしい動線や手間をスッと軽くしてくれる機能美</b>が随所に光ります。</p>"
            p3 = f"<p>耐久性のあるタフな素材選びとお手入れのしやすさも抜群で、<b>汚れがサッと落ちて常に清潔をキープできる安心感</b>は忙しい毎日の大きな味方。キッチンに立つ時間を億劫な家事から心地よいリフレッシュタイムへと変えてくれる、頼もしい実力派アイテムです。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}"

        elif genre == "appliance":
            p1 = f"<p>日々の暮らしや家事の手間が増えて、部屋で過ごす時間にもっと心と時間のゆとりが欲しいと感じることってありますよね。かといって部屋の雰囲気を壊すような無骨な家電や、置き場所に困るような大型のものは増やしたくない……と探していたところに出会ったのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>お部屋に置いてみた瞬間、インテリアに自然と溶け込む洗練されたミニマルなデザインにまず感動。スイッチを入れてみると直感的な操作性で迷わず扱える上、<b>静音性や省エネ性にも細やかに配慮された確かな性能</b>で、生活の邪魔を一切せず快適な環境を作り出してくれます。</p>"
            p3 = f"<p>日々のルーティンにすっと馴染んで手間を確実に減らしてくれるため、<b>一度暮らしに取り入れるともう手放せなくなる快適さ</b>。生活のリズムを軽やかに整え、おうち時間を一段と居心地の良いものにしてくれる頼れる名品です。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}"

        elif genre == "desk_gadget":
            p1 = f"<p>デスク周りや作業スペースを見るたびに、黒いコードが複雑に絡み合ったり小物が散乱したりして、なんだかそれだけで集中力が途切れてしまうことってありませんか。作業効率を上げつつ、スマートで美しいデスク環境を作りたいと悩んでいたところに出会ったのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>実際に机の上に置いてみても余計な圧迫感がなく、チープさを感じさせない落ち着いた質感がお部屋のトーンにすっとマッチ。<b>ごちゃつきがちな配線や小物をひとまとめに整頓できる機能性</b>のおかげで、デスク上が一瞬で見違えるほどクリーンに生まれ変わります。</p>"
            p3 = f"<p>日々の作業動線が劇的にスムーズになり、<b>視界に入るノイズが消えるだけでこんなにも集中力が高まるのかと実感</b>。リモートワークや毎日のデスクワークを快適でモチベーションの上がる空間に仕立て直したい方に、自信を持っておすすめできる相棒です。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}"

        elif genre == "decor":
            p1 = f"<p>お部屋の雰囲気をガラリと変えて垢抜けさせたいけれど、大掛かりな家具の買い替えや壁の工事は大掛かりでためらってしまう……そんな模様替えの悩みを抱えていませんか。手軽にお部屋のセンスをワンランク引き上げてくれる上質なインテリアアイテムを探していたところに出会ったのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>実際に手にとって飾ってみた瞬間、空間を優しく引き締める洗練された色味と素材の温もりに感動。<b>置くだけ・飾るだけで見慣れたお部屋に心地よいメリハリが生まれ</b>、カフェやセレクトショップのような洗練された雰囲気が広がります。</p>"
            p3 = f"<p>主張しすぎず既存の家具や壁紙にすっと馴染む絶妙なバランス感で、<b>ふと視線が合うたびに気持ちが満たされる心地よさ</b>。日々の暮らしにささやかで上質な彩りを添え、家に帰るのが楽しみになるような空間を作ってくれる優秀なアイテムです。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}"

        else:
            p1 = f"<p>お部屋の散らかりや生活感をなんとか整えたいけれど、重たくて圧迫感のある大型家具は置きたくない……と悩んでいたところに出会ったのが、この<b>{clean_title}</b>です。</p>"
            p2 = f"<p>届いて実際に配置してみた瞬間、空間を邪魔しないスリムな佇まいと落ち着いた質感がお部屋のインテリアにすっと溶け込み、嬉しい驚きがありました。<b>軽量で取り回しが良いのにしっかりとした頼れる構造</b>で、散らかりがちな日用品を気持ちよく整理できます。</p>"
            p3 = f"<p>使い勝手の良さと空間の開放感を見事に両立し、<b>毎日の片付けや物の出し入れが驚くほどスムーズになる頼もしさ</b>。生活感を上手に抑えながら心地よい広々とした空間を作りたい方に、心からおすすめしたい収納アイテムです。</p>"
            return f"{p1}\n\n{p2}\n\n{p3}"

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
        
        # 使用する画像の枚数（2〜3枚に厳選し、見やすく読みやすい長さに最適化）
        num_images = max(2, min(len(image_urls), 3))
        
        # 商品ジャンルを正確に判定
        genre = self._detect_genre(clean_title, search_keyword, caption)

        # ジャンル別の段落ガイドライン（他ジャンルの特徴の混入を完全防止）
        if genre == "bath_sleep":
            genre_guide = """
   ・段落1: 【悩みと出会い・商品紹介】日常の睡眠の質や首こり・肩こり、寝起きのすっきり感への悩みを語り、直後に「〜と悩んでいたところに出会ったのが、この<b>{clean_title}</b>です。」と自然に紹介（直後に1枚目画像）。
   ・段落2: 【使い心地・フィット感・シズル感】横になった瞬間に首や頭部へ隙間なく吸い付くようなフィット感、無理のない寝姿勢のサポート、肌触りや素材の上質さ。
   ・段落3: 【機能・清潔さ・生活の変化】通気性やカバー洗濯の手軽さ、朝起きたときの体の軽やかさ、「毎朝すっきり目覚めたい」と願う読者への購入の後押し。
   ※家具の組み立てや壁掛け、工具などの言葉は絶対に含めないでください。"""
        elif genre in ["sweets", "food", "furusato"]:
            genre_guide = """
   ・段落1: 【ひと息・出会い・商品紹介】日々の食卓や仕事の合間のご褒美への思いを語り、直後に「〜と探していたところに出会ったのが、この<b>{clean_title}</b>です。」と自然に紹介（直後に1枚目画像）。
   ・段落2: 【シズル感・香り・食感・味わい】届いて開けた瞬間の立ちのぼるふくよかな香り、口に含んだ瞬間の濃厚なコクや舌触り（しっとり感、ザラメのシャリ感、肉のあふれる肉汁など）、職人や産地の手間暇。
   ・段落3: 【楽しみ方・保存・購入の後押し】おすすめのペアリング（珈琲や緑茶、お酒など）、個包装や保存の便利さ、自分へのご褒美やギフトとして「思わず今すぐ欲しくなる」熱量の高いおすすめ。
   ※家具や組み立て、寸法などの言葉は絶対に含めないでください。"""
        elif genre == "kitchen":
            genre_guide = """
   ・段落1: 【台所の悩み・出会い・商品紹介】毎日の料理や後片付けのプチストレスを語り、直後に「〜と悩んでいたところに出会ったのが、この<b>{clean_title}</b>です。」と自然に紹介（直後に1枚目画像）。
   ・段落2: 【佇まい・使い心地・機能美】キッチンの生活感を抑える洗練された佇まい、手になじむ取り回しの良さ、調理や後片付けのわずらわしさを軽くする工夫。
   ・段落3: 【耐久性・お手入れ・生活の変化】汚れ落ちやお手入れの手軽さ、長く清潔に使える安心感、台所仕事を心地よくしたい読者への熱いおすすめ。"""
        elif genre == "appliance":
            genre_guide = """
   ・段落1: 【生活の手間・出会い・商品紹介】日々の家事負担や暮らしをシンプルにしたい思いを語り、直後に「〜と探していたところに出会ったのが、この<b>{clean_title}</b>です。」と自然に紹介（直後に1枚目画像）。
   ・段落2: 【デザイン・操作感・静音性】お部屋に馴染む洗練されたデザイン、直感的な操作性とストレスフリーな取り回し、暮らしの邪魔をしない性能。
   ・段落3: 【スペック・生活の変化・総括】省エネ性やお手入れ、暮らしの手間を減らしてくれる頼もしさ、生活にゆとりを作りたい読者への熱いおすすめ。"""
        elif genre == "desk_gadget":
            genre_guide = """
   ・段落1: 【デスクの悩み・出会い・商品紹介】机周りのごちゃつきや配線の乱れへの悩みを語り、直後に「〜と悩んでいたところに出会ったのが、この<b>{clean_title}</b>です。」と自然に紹介（直後に1枚目画像）。
   ・段落2: 【質感・整理機能・スマートさ】コンパクトで圧迫感のないデザイン、配線や小物をすっきり美しくまとめる機能美。
   ・段落3: 【作業環境の変化・総括】デスクワークの集中力アップ、スマートでモチベーションの上がる空間作りへの本音のおすすめ。"""
        else:
            genre_guide = """
   ・段落1: 【生活感の悩み・出会い・商品紹介】部屋の散らかりや生活感を整えたい思いを語り、直後に「〜と悩んでいたところに出会ったのが、この<b>{clean_title}</b>です。」と自然に紹介（直後に1枚目画像）。
   ・段落2: 【佇まい・サイズ感・質感】お部屋にすっと溶け込むシンプルなデザイン、圧迫感のない絶妙なサイズ感や素材の質感。
   ・段落3: 【使い勝手・生活の変化・総括】整理整頓のしやすさ、日々の暮らしが心地よく整う変化、空間をスマートに使いたい読者への熱いおすすめ。"""

        prompt = f"""あなたは「本当に良いものを自分の言葉で本音レビューし、読者に『今すぐ欲しい！』と思わせる大人気の暮らしブロガー」です。
以下の楽天市場の商品情報を徹底的に読み込み、定型文や使い回しのテンプレート感を完全に排除して、この商品「だけ」にしかない魅力・スペック・使い勝手を熱量たっぷりに語る超高品質なレビュー記事を作成してください。

【商品名】: {title}
【クリーン商品名】: {clean_title}
【価格】: {price}
【商品の説明】: {caption}
【検索キーワード】: {search_keyword}
【希望段落数】: ちょうど{num_images}個の段落（<p>...</p>）

【超重要執筆ルール（脱「です・ます」連続、豊かな文リズム、シズル感・情景描写）】:
1. 【「です」「ます」の単調な連続を厳禁・滑らかで心地よい日本語リズム】:
   ・「〜です」「〜ます」が3文以上連続して続く機械的なAI調は絶対に禁止です。
   ・単文を短くぶつ切り（〜です。〜ます。〜です。）にするのではなく、複文（〜と、〜ながら、〜ため、〜ところ）を適度に用い、1文あたり40〜70文字程度の滑らかで流れるような文章を組み立ててください。
   ・体言止め（〜の質感、〜の贅沢感）、感嘆（〜がたまりません、〜なのが嬉しいところ）、問いかけ、共感などを自然に織り交ぜ、血の通った人間らしい文章にしてください。
   ・「私」「あたし」「僕」などの一人称は使わず、中性的で親しみやすい語り口にしてください。

2. 【読者の五感を刺激し「実際に買いたい！」と思わせる情景・シズル感描写】:
   ・説明書のスペック要約ではなく、実際に商品を手にして生活や食卓に取り入れた瞬間の「感動・手触り・香り・食感・味わい・生活の変化」を生き生きと具体的に描写してください。
   ・スイーツ・食品なら：箱を開けた瞬間の香り、口に含んだときの濃厚さや口どけ、ザラメのシャリッとした食感、珈琲や緑茶との相性など、思わず唾液が出るようなシズル感を語る。
   ・寝具・家具・家電なら：触れた瞬間の質感、吸い付くようなフィット感、部屋に置いたときの垢抜け感、翌朝目覚めたときの体の軽やかさなど、読者が自分の部屋で使っているシーンを想像できるように語る。

3. 【商品ジャンルに100%合致した段落構成（必ず{num_images}個の<p>段落を出力すること）】:
   各段落は独立した充実した文章（各段落140〜200文字程度）とし、重要なポイントや数値・素材を <b> タグで太字にしてください。
   ※関係のない商品の特徴（枕なのに「壁に取り付ける」「組み立て」「大型家具」など）は絶対に書かないでください！
   段落テーマ目安：{genre_guide}

4. 【フォーマット】:
   ・出力は <p>...</p> タグで囲まれた段落のみを出力してください（見出しタグ、divタグ、ボタン、リストは含めないでください）。
"""
        raw_article = self._call_llm_with_retries(prompt, min_length=300, task_name="Full Review Article", item_context={**item, "clean_title": clean_title})
        
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
            if len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', p_clean)) >= 15:
                paragraphs.append(p_clean)

        if not paragraphs:
            # <p>タグがない場合は改行で分割
            raw_blocks = [b.strip() for b in raw_article.split("\n\n") if b.strip()]
            for b in raw_blocks:
                if not b.startswith("<") and len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', b)) >= 15:
                    paragraphs.append(b)

        if len(paragraphs) < 3:
            paragraphs = self._build_safe_genre_paragraphs(item)

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
        # 中盤CTAの挿入位置（第3〜4段落のあたり）
        mid_point = max(2, min(4, len(paragraphs) // 2 + 1))

        # 必ず【商品紹介テキスト】から開始し、その直後に1枚目の画像が来るレイアウト
        for i, p_text in enumerate(paragraphs):
            # 1. 段落（テキスト）を追加
            full_html_parts.append(f"<p>{p_text.strip()}</p>\n\n")

            # 2. 中盤CTAボタン（指定段落の直後）
            if i == (mid_point - 1):
                full_html_parts.append(f"{cta_btn_mid}\n")

            # 3. 段落の後に対応する画像を挿入
            if i < len(clean_images):
                img_url = clean_images[i]
                alt_suffix = alt_suffixes[i % len(alt_suffixes)]
                alt_text = f"{clean_title} {alt_suffix}"
                img_html = f'<div><img style="max-width: 100%; height: auto; border-radius: 8px; display: block; margin-left: auto; margin-right: auto;" src="{img_url}" border="0" alt="{alt_text}" /></div>\n\n'
                full_html_parts.append(img_html)

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
        system_prompt = "あなたは入力されたテキストから無駄な修飾語を取り除き、商品名そのもの（名詞）のみを抽出する優秀なアシスタントです。解説は一切含めず、商品名のみを1行で出力してください。"
        prompt = f"""以下の楽天市場の商品名から、送料無料、サイズ、型番、アピール用の形容詞（おしゃれ、大人気など）をすべて排除し、その商品が「何であるか」を示す具体的でクリーンな商品名（例：『木枠ウォールミラー』『珪藻土バスマット』『分別ゴミ箱』など）を日本語で15文字以内で抽出してください。
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
        if cleaned and 2 <= len(cleaned) <= 20:
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
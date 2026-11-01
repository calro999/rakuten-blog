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
        ユーザー見本記事（木目調ケーブルボックス・Amazonラック）と同等の高い完成度と情報密度を実現するレビュー記事ビルダー。
        ・必ず4つの充実した段落（各段落150〜230文字、全体で700〜900文字の読み応えある文章）
        ・画像は2〜3枚に厳選し、必ず「段落1（商品紹介）の直後に1枚目画像」が来る美しいサンドイッチ配置
        ・レイアウト構成:
          段落1（日常の悩み・共感 → 出会い → 商品紹介 <b>商品名</b>）
          画像1（全体像）
          段落2（届いた瞬間の印象・佇まい・部屋や食卓への馴染みやすさ）
          画像2（収納イメージ・利用風景）
          段落3（手軽さ・素材感・サイズ・機能性・固有スペックの深掘り）
          画像3（仕様・ディテール、画像が2枚の場合は段落3のみ）
          段落4（実際の使い心地・生活の変化・誰におすすめか・今すぐ買いたくなる強い推奨）
          CTAボタン（楽天市場で見る）
          ブロ活広告タグ
        """
        title = item.get("title", "")
        search_keyword = item.get("search_keyword", "")
        clean_title = item.get("clean_title") or self.get_clean_product_name(title, search_keyword)
        price = item.get("price", "")
        caption = item.get("caption", "")
        
        # 使用する画像の枚数（2〜3枚に厳選）
        num_images = max(2, min(len(image_urls), 3))
        
        # 商品ジャンルを正確に判定
        genre = self._detect_genre(clean_title, search_keyword, caption)

        # ジャンル別の4段落ガイドライン（他ジャンルの特徴の混入を完全防止）
        if genre == "bath_sleep":
            genre_guide = f"""
   ・段落1（約150〜200文字）: 【悩みと出会い・商品紹介】朝起きたときの首や肩の重み、寝ても取れない疲労感など睡眠のプチ不調に触れ、「〜と悩んでいたところに出会ったのが、この<b>{clean_title}</b>です。」と自然に紹介。
   ・段落2（約150〜200文字）: 【届いた時の印象・フィット感】届いて実際に横になってみた瞬間の感動。頭部から首筋の隙間に吸い付くようにフィットする感覚、余計な緊張がほどけていく心地よさ、自然な寝姿勢の維持。
   ・段落3（約160〜220文字）: 【スペック・通気性・お手入れ】寝返りの打ちやすさ、熱がこもりにくい立体構造や通気性、肌触りの良いカバー、丸洗いできる清潔さなどの機能的魅力を具体的に深掘り。
   ・段落4（約150〜200文字）: 【生活の変化・強い推奨】朝起きたときの体の軽やかさ、目覚ましでスッと起きられる変化、「毎朝気持ちよく一日をスタートさせたい」と願う読者への熱量ある購入の後押し。
   ※家具の組み立てや壁掛け、工具などの言葉は絶対に含めないでください。"""
        elif genre in ["sweets", "food", "furusato"]:
            genre_guide = f"""
   ・段落1（約150〜200文字）: 【ひと息・出会い・商品紹介】日々の仕事や家事の合間にほっと一息つける時間の尊さや、自分へのご褒美・大切な人への手土産への思いを語り、「〜と探していたところに出会ったのが、この<b>{clean_title}</b>です。」と紹介。
   ・段落2（約150〜200文字）: 【開封の瞬間・シズル感・味わい】届いて箱を開けた瞬間に立ちのぼるふくよかな香り、口に含んだ瞬間の濃厚なコクや舌触り（しっとり感、口どけ、素材の自然な風味）を五感を刺激する言葉で生き生きと描写。
   ・段落3（約160〜220文字）: 【こだわり・保存・ペアリング】職人の手間暇や厳選素材、淹れたての珈琲や緑茶との極上の相性、個包装や常温保存の扱いやすさなど具体的なスペックと気配りを深掘り。
   ・段落4（約150〜200文字）: 【日常の贅沢・強い推奨】日常のティータイムが特別な癒やしの時間に変わる贅沢さ、「心から満足できる本物の美味しさを味わいたい」と願う読者へ思わず買いたくなる熱いおすすめ。
   ※家具や組み立て、寸法などの言葉は絶対に含めないでください。"""
        elif genre == "kitchen":
            genre_guide = f"""
   ・段落1（約150〜200文字）: 【台所の悩み・出会い・商品紹介】毎日の料理や後片付けのプチストレス、生活感が出やすいキッチンへの悩みを語り、「〜と悩んでいたところに出会ったのが、この<b>{clean_title}</b>です。」と紹介。
   ・段落2（約150〜200文字）: 【佇まい・第一印象・デザイン美】届いてキッチンに置いた瞬間の洗練された佇まい、無駄のない美しいフォルム、空間がカフェのように引き締まる心地よさを描写。
   ・段落3（約160〜220文字）: 【使い心地・素材・お手入れ】手になじむ取り回しの良さ、汚れ落ちの良さや食洗機対応などの扱いやすさ、長く愛用できる頑丈な素材感を具体的に深掘り。
   ・段落4（約150〜200文字）: 【料理の楽しさ・強い推奨】台所に立つ時間そのものが楽しくなる変化、「使い勝手とデザインの両方にこだわりたい」と願う読者へ自信を持っておすすめ。"""
        elif genre == "appliance":
            genre_guide = f"""
   ・段落1（約150〜200文字）: 【生活の手間・出会い・商品紹介】日々の家事負担や暮らしをシンプルに整えたい思いを語り、「〜と探していたところに出会ったのが、この<b>{clean_title}</b>です。」と紹介。
   ・段落2（約150〜200文字）: 【第一印象・デザイン・操作感】生活家電特有の無骨さを感じさせない洗練されたデザイン、直感的に使える操作性、お部屋のインテリアを邪魔しないスマートさを描写。
   ・段落3（約160〜220文字）: 【機能・静音性・省エネ】毎日の暮らしをラクにしてくれる独自の機能性、静音性、コンパクトさやお手入れの手軽さなど具体的な数値を交えて深掘り。
   ・段落4（約150〜200文字）: 【生活のゆとり・強い推奨】家事の手間が激減して自分の時間が増える生活の変化、「毎日の暮らしにゆとりを作りたい」と願う読者へ熱量あるおすすめ。"""
        elif genre == "desk_gadget":
            genre_guide = f"""
   ・段落1（約150〜200文字）: 【デスクの悩み・出会い・商品紹介】机周りのごちゃつきや配線の乱れ、作業スペースの圧迫感への悩みを語り、「〜と悩んでいたところに出会ったのが、この<b>{clean_title}</b>です。」と紹介。
   ・段落2（約150〜200文字）: 【第一印象・スマートな佇まい】届いて設置した瞬間にデスク周りがすっきり引き締まる心地よさ、主張しすぎず作業環境に馴染む落ち着いた質感を描写。
   ・段落3（約160〜220文字）: 【機能性・整理力・取り回し】配線や小物をひとまとめにできる実用性、軽量ながらしっかりした造り、日々の使いやすさを具体的に深掘り。
   ・段落4（約150〜200文字）: 【作業環境の変化・強い推奨】視界がクリアになって仕事や作業のモチベーションが高まる変化、「デスクを機能的かつスマートに整えたい」と願う読者へ熱いおすすめ。"""
        else:
            genre_guide = f"""
   ・段落1（約150〜200文字）: 【生活感の悩み・出会い・商品紹介】部屋の散らかりや生活感を整えたい思い、大型家具を置きたくない悩みを語り、「〜と悩んでいたところに出会ったのが、この<b>{clean_title}</b>です。」と紹介。
   ・段落2（約150〜200文字）: 【第一印象・佇まい・サイズ感】お部屋にすっと溶け込むシンプルなデザイン、圧迫感のない絶妙なサイズ感や素材の質感を生き生きと描写。
   ・段落3（約160〜220文字）: 【使い勝手・扱いやすさ・機能】手軽に使える身軽さ、整理整頓のしやすさ、頑丈さやお手入れの手軽さなど具体的なスペックを深掘り。
   ・段落4（約150〜200文字）: 【心地よい空間・強い推奨】部屋がスッキリ片付いて日々の気分まで軽やかに整う生活の変化、「快適で心地よい空間を手に入れたい」と願う読者へ自信を持っておすすめ。"""

        prompt = f"""あなたは「本当に良いものを自分の言葉で本音レビューし、読者に『今すぐ欲しい！』と思わせる大人気の暮らしブロガー」です。
以下の楽天市場の商品情報を徹底的に読み込み、定型文や使い回しのテンプレート感を完全に排除して、この商品「だけ」にしかない魅力・スペック・使い勝手を熱量たっぷりに語る、読み応えのある長文レビュー記事を作成してください。

【商品名】: {title}
【クリーン商品名】: {clean_title}
【価格】: {price}
【商品の説明】: {caption}
【検索キーワード】: {search_keyword}
【希望段落数】: 必ず4つの段落（<p>...</p>）を出力してください。文字数は全体で700〜900文字の骨太で充実した内容にしてください。

【最重要執筆ルール（文字量・脱「です・ます」連続・シズル感・情景描写）】:
1. 【文字数と段落構成の厳守（少なすぎる文章は不可）】:
   ・各段落は150〜230文字程度の充実した長さを担保し、全体で700〜900文字の読み応えのある記事にしてください。
   ・必ず4つの独立した段落（<p>タグ）で構成してください。
   ・重要なスペック、素材名、数値、魅力的なキーワードは適度に <b> タグで太字にしてください。

2. 【「です」「ます」の単調な連続を厳禁・滑らかで心地よい日本語リズム】:
   ・「〜です」「〜ます」が連続して短くぶつ切りになる機械的なAI文章は絶対に禁止です。
   ・複文（〜と、〜ながら、〜ため、〜ところ）を適度に用い、1文あたり40〜70文字程度の滑らかで流れるような文章を組み立ててください。
   ・体言止め、感嘆（〜がたまりません、〜なのが嬉しいところ）、問いかけ、共感などを自然に織り交ぜ、人間味あふれる魅力的な文章にしてください。
   ・「私」「あたし」「僕」などの一人称は使わず、中性的で親しみやすい語り口にしてください。

3. 【読者の五感を刺激し「実際に買いたい！」と思わせる情景・シズル感描写】:
   ・説明書のスペック要約ではなく、実際に商品を手にして生活や食卓に取り入れた瞬間の「感動・手触り・香り・食感・味わい・生活の変化」を生き生きと具体的に描写してください。
   ・何を伝えたいのか（Before/Afterと生活の変化、得られる心地よさ）を明確に語ってください。
   ・商品説明（caption）にある固有の情報（素材、寸法、製法、フレーバー、手入れ方法など）を必ず3つ以上具体的に拾い上げてください。

4. 【商品ジャンルに100%合致した段落テーマ（必ず4つの<p>段落を出力）】:
   ※関係のない商品の特徴（枕なのに「壁に取り付ける」「組み立て」「大型家具」など）は絶対に書かないでください！
   段落テーマ目安：{genre_guide}

5. 【フォーマット】:
   ・出力は <p>...</p> タグで囲まれた4つの段落のみを出力してください（見出しタグ、divタグ、ボタン、リストは含めないでください）。
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

        # CTAボタンのスタイル定義（見本記事の上品なボタンデザイン）
        cta_btn_end = (
            f'<div style="text-align: center; margin: 28px 0;">\n'
            f'<a href="{affiliate_url}" target="_blank" rel="noopener noreferrer" style="display: inline-block; width: 85%; max-width: 320px; padding: 13px 0; background-color: #f4f2ee; color: #333333; border: 1px solid #e0ded9; border-radius: 20px; font-size: 14px; font-weight: bold; text-align: center; text-decoration: none;"><span style="text-decoration: none;">楽天市場で見る</span>\n'
            f'</a></div>'
        )

        alt_suffixes = [
            "全体像", "収納イメージ・利用風景", "引き出しと棚の仕様・ディテール",
            "側面ディテール・サイズ感", "素材感と質感", "活用シーン・おすすめポイント"
        ]

        # ユーザー見本に100%合致するレイアウト構成:
        # 段落1 → 画像1 → 段落2 → 画像2 → 段落3 → 画像3（存在する場合） → 段落4 → CTAボタン → ブロ活広告
        full_html_parts = []
        for i, p_text in enumerate(paragraphs):
            # 段落（テキスト）
            full_html_parts.append(f"<p>{p_text.strip()}</p>\n\n")

            # 画像の挿入（段落の直後、画像の枚数分だけ配置）
            if i < len(clean_images):
                img_url = clean_images[i]
                alt_suffix = alt_suffixes[i % len(alt_suffixes)]
                alt_text = f"{clean_title} {alt_suffix}"
                img_html = f'<div><img style="max-width: 100%; height: auto; border-radius: 8px; display: block; margin-left: auto; margin-right: auto;" src="{img_url}" border="0" alt="{alt_text}" /></div>\n\n'
                full_html_parts.append(img_html)

        # 記事末尾のCTAボタン
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
import os
import sys

# パスを追加してモジュールをインポートできるようにする
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rakuten_blog_api import RakutenBlogAPI

def main():
    print("Testing post draft using provided content...")
    title = "{role:assistant,reasoning:We need to pro"
    content = """<img style="max-width: 100%; height: auto; border-radius: 8px;" src="https://thumbnail.image.rakuten.co.jp/@0_mall/hanko-online/cabinet/07/6501gy-1_main.jpg?_ex=128x128" border="0" alt="★6/24~25限定 5%OFFクーポン配布中★フラワーベース ガラス 北欧 大きい 枝物 Lサイズ：約20cm丸×28cm（口径:約8cm) グレー クリア 花瓶 ガラス カラー おしゃれ シック モダン 人気 円形 ホワイトデー お返し 円柱 大きい 母の日 PORTA" />
<p>日々の暮らしに、まるでアート作品のような美しさを添えてみませんか？ ただ花を飾るだけでなく、その空間全体を格上げしてくれるのが、このフラワーベース「PORTA」です。<b>北欧、モダン、シック</b>といった多様なインテリアスタイルに違和感なく溶け込み, 置くだけで洗練された雰囲気を演出します。</p>

<p>Lサイズ（約20cm丸×28cm）という存在感のある大きさは、<b>枝物もダイナミックに活けられる</b>のが最大の魅力。お部屋にグリーンや花を飾る習慣は、想像以上に私たちのQOL（生活の質）を高めてくれます。視覚的な癒しはもちろん、季節の移ろいを感じることで、日々の忙しさの中に心のゆとりと彩りをもたらしてくれるでしょう。</p>

<p>定番のクリアガラスに加え、人気の<b>シックなグレー</b>もラインナップ。どちらのカラーも、光の加減で表情を変え、見るたびに新たな発見を与えてくれます。裾広がりの形状は、お花を挿しやすく、不器用さんでも簡単に美しく生けることが可能です。また、<b>どっしりとした底部と厚みのあるガラス</b>は、安定感と高級感を両立。品質の高さが、飾る花や枝物を一層引き立てます。</p>

<p>花がない時でも、その<b>美しいフォルム自体がオブジェ</b>として空間を彩ります。生活に溶け込むアートピースとして、毎日の気分を明るくしてくれることでしょう。自分へのご褒美としてはもちろん、大切な方への<b>ホワイトデーや母の日のギフト</b>としても、きっと喜ばれるはずです。このフラワーベースが、あなたの暮らしをより豊かに、より美しく変えてくれることでしょう。</p>
<p style="margin: 20px 0;"><a href="https://hb.afl.rakuten.co.jp/hgc/54d2a438.4bc4abc2.54d2a439.aa1be583/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Fhanko-online%2F07-6501%2F&m=http%3A%2F%2Fm.rakuten.co.jp%2Fhanko-online%2Fi%2F10002638%2F&rafcid=wsc_i_is_1a3cdfd9-2aec-4b42-8290-1c53603b0012" target="_blank" rel="noopener noreferrer"><b>＼ 楽天市場で詳細をチェックする ／</b></a></p>
<pointad pointad-id="div-plaza-point-ad" pointad-text="#ブロ活広告#" />"""
    
    # RAKUTEN_BLOG_SESSION_B64環境変数を無効化し、ローカルの session.json を優先的に使う
    if "RAKUTEN_BLOG_SESSION_B64" in os.environ:
        del os.environ["RAKUTEN_BLOG_SESSION_B64"]
        
    api = RakutenBlogAPI(session_file="session.json")
    success = api.post_entry(title=title, html_content=content)
    
    if success:
        print("Success! Draft posted and confirmed via UI.")
    else:
        print("Failed! Draft posting could not be verified.")

if __name__ == "__main__":
    main()

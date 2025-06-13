このプロジェクトは、カーナベル https://www.ka-nabell.com/ のページ URL 一覧をテキストファイルから受け取り、
それぞれのページからカードの画像をダウンロードすると共にカードの情報を抽出して.ts ファイルを出力する Python を用いたスクレイピングツールを作成することを目的としています。

スクレイピングを開始する時点で、対象のページが何の種別のカードかわからないため、判別して行う処理を判断してください。
何のカードか区別できなかった場合は、その旨を表示してプログラムを終了してください。
.html ファイルの例と出力する.ts ファイルの例を与えますが、出力するカードと.html に表示しているカードは異なるため、注意してください。

-   罠カード

    -   DOM 構造の例 => trap_card.html
    -   出力するファイルの例 => trap_card.json

-   魔法カード

    -   DOM 構造の例 => magic_card.html
    -   出力ファイルの例　=> magic_card.ts

-   通常モンスター/効果モンスターカード

    -   DOM 構造の例 => monster_card.html
    -   出力ファイルの例　=> mosnter_card.ts

-   エクシーズモンスターカード

    -   DOM 構造の例 => xyz_card.html
    -   出力ファイルの例　=> xyz_card.ts

-   融合モンスターカード

    -   DOM 構造の例 => fusion_monster_card.html
    -   出力ファイルの例　=> fusion_monster_card.ts

-   シンクロモンスターカード

    -   DOM 構造の例 => synchro_monster_card.html
    -   出力ファイルの例　=> synchro_monster_card.ts

-   リンクモンスターカード
    -   DOM 構造の例 => link_monster_card.html
    -   出力ファイルの例　=> link_monster_card.ts

出力ファイルの保存先 - ./output/ 以下
出力画像ファイルの保存先 - ./image/ 以下 - 出力する.ts ファイルにパスの情報は必要なく、画像のファイル名のみでよい

# 遊戯王カード情報スクレイパー

このツールは、カーナベル（https://www.ka-nabell.com/）から遊戯王カードの情報を抽出し、TypeScriptファイルとして出力するPythonスクレイパーです。

## 機能

- URLリストからカード情報を自動取得
- カード種別の自動判定
- カード画像のダウンロード
- TypeScript形式でのカード情報出力

## 対応カード種別

- 罠カード
- 魔法カード
- 通常モンスター/効果モンスターカード
- エクシーズモンスターカード
- 融合モンスターカード
- シンクロモンスターカード
- リンクモンスターカード

## 必要な環境

- Python 3.x
- pip

## インストール

```bash
pip install -r requirements.txt
```

## 使い方

1. スクレイピングしたいカードのURLをテキストファイルに記載（1行1URL）
2. 以下のコマンドを実行：

```bash
python scraper.py <URLリストファイル>
```

例：
```bash
python scraper.py test_urls.txt
```

## 出力

- `./output/` - TypeScriptファイル（カード情報）
- `./image/` - ダウンロードしたカード画像

## URLリストファイルの例

```
https://www.ka-nabell.com/?act=sell_detail&id=100004564&genre=1
https://www.ka-nabell.com/?act=sell_detail&id=100214871&genre=1
https://www.ka-nabell.com/?act=sell_detail&id=73712603&genre=1
```

## 注意事項

- サーバーに負荷をかけないよう、適切な間隔でアクセスしてください
- スクレイピングは利用規約を確認の上、適切に行ってください
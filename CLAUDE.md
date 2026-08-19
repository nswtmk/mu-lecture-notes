# CLAUDE.md

このリポジトリで作業するときの共通ルール。

## Gmail下書きを作るとき(必須)

**必ず `htmlBody` を指定する。プレーンテキスト(`body`)だけで下書きを作らない。**

理由: Gmailコネクタ経由でプレーンテキストのみの下書きを作ると、本文中のURLが
`https://www.google.com/url?q=...&source=gmail&ust=...&sa=E` という
Googleのリダイレクト形式に書き換えられて表示される。

対策:
- `htmlBody` に `<a href="https://example.com/">https://example.com/</a>` の形で書く
  (アンカーの表示テキストを素のURLにすれば、hrefが書き換えられても見た目は素のURLのまま)
- `body` は同じ内容のプレーンテキスト版として併せて渡す
- 改行は `<br>`、見出しは `<b>` で表現する(凝ったCSSは不要)
- URLは必ず直リンクで書く。`https://www.google.com/url?q=` で始まるURLを
  そのまま貼らない(受信メールからコピーしたリンクは素のURLに戻してから使う)

## 役員向け活動報告メール

構成のルールは `crf-discord/README.md` の「役員向け活動報告メールの定型」を参照。
末尾に必ず「■ 今後のスケジュール」を入れる(Googleカレンダー2つから作成)。
送信元は info@technel.world(nswtmk@ のエイリアス)。送信前に七沢さんの確認を得る。

## Discordへの投稿

`crf-discord/outbox/` にMarkdownを追加してコミット&プッシュすると、
ボットが3分以内に該当チャンネルへ投稿する(詳細は `crf-discord/README.md`)。

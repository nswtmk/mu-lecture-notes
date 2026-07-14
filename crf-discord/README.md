# CRF Discord サーバー セットアップキット

意識研究財団(Consciousness Research Foundation / **CRF**)の Discord サーバーを立ち上げるための一式です。

- **CRFボット**: サーバー構造を自動構築し、財団についての質問に答えるボット
- **入場フォーム**: 「紹介者」「関わるプロジェクト」のアンケートに回答すると入場できる仕組み(フォームを通さない入場経路もあり)
- **ルール掲示**: サーバーのルール(`rules.md`)を自動掲示

## 構築されるサーバー構造

```
INFO
├── #welcome        入場受付(アンケートフォームのボタン)※未入場者にも見える
├── #rules          ルール ※未入場者にも見える
├── #announcements  お知らせ(閲覧専用)
└── #events         イベント・研究会情報
COMMUNITY
├── #introductions  自己紹介
├── #general        一般
├── #random         何でも投稿できるチャンネル
└── #research-info  リサーチ関係の情報
PROJECTS
├── #technology     テクノロジー
├── #satoyama       里山
├── #buddhism       仏教
└── #forest         フォレスト(森)
CONFERENCE
└── #conference     カンファレンス
OFFICE
└── #office         事務関係(財務情報・定款・理事情報を公開/閲覧専用)
```

- 未入場者(`@everyone`)に見えるのは `#welcome` と `#rules` のみ
- アンケートに回答すると `Member` ロールが付与され、全チャンネルが見えるようになります

## セットアップ手順

### 1. Discord サーバーを作成

Discord アプリで「サーバーを追加」→「オリジナルの作成」→ サーバー名を
**Consciousness Research Foundation (CRF)** にします。チャンネルは作らなくてOK(ボットが作ります)。

### 2. ボットを作成して招待

1. [Discord Developer Portal](https://discord.com/developers/applications) → **New Application** → 名前を「CRF Bot」に
2. **Bot** タブ → **Reset Token** でトークンを取得(後で使います)
3. 同じ Bot タブで **Privileged Gateway Intents** の
   `SERVER MEMBERS INTENT` と `MESSAGE CONTENT INTENT` を **ON** にする
4. **OAuth2 → URL Generator** で
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Administrator`(または Manage Roles / Manage Channels / Send Messages / Read Message History)
   を選び、生成されたURLを開いて手順1のサーバーに招待

### 3. ボットを起動

```bash
cd crf-discord
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # .env にトークンを記入
export $(grep -v '^#' .env | xargs)

python bot.py
```

常時稼働させる場合は、VPS・Railway・Fly.io などにデプロイしてください。

### 4. サーバー構造を構築

Discord サーバー内の任意のチャンネルで、管理者が次のスラッシュコマンドを実行します:

```
/crf-setup
```

これでロール・カテゴリ・チャンネルの作成、権限設定、`#rules` へのルール掲示、
`#welcome` への入場フォーム設置がすべて自動で行われます。
(何度実行しても安全です。既存チャンネルは作り直さず設定だけ更新します)

## 入場の流れ

| 経路 | 方法 |
|---|---|
| **アンケートフォーム(標準)** | 新規参加者が `#welcome` の「📝 アンケートに回答して入場する」ボタンを押す → 紹介者・関わるプロジェクト・自己紹介を入力 → 自動で `Member` ロール付与。回答内容は `#introductions` に掲示されます |
| **フォームを通さない経路** | 管理者が `/admit @ユーザー` を実行すると、フォームなしで入場できます |

## CRFボットに質問する

- **メンション**: 任意のチャンネルで `@CRF Bot 財団にはどんなプロジェクトがありますか?` のように質問
- **スラッシュコマンド**: `/crf question:森のプロジェクトについて教えて`

ボットは `knowledge/crf.md` のナレッジベースをもとに Claude(`claude-opus-4-8`)が回答します。
財団の情報が増えたら `knowledge/crf.md` を編集してボットを再起動するだけで回答も更新されます。
`ANTHROPIC_API_KEY` が未設定の場合も、ナレッジベースの抜粋で簡易回答します。

## 事務情報の公開

財務情報・定款・理事の情報などは `#office` チャンネルに投稿してください(管理者のみ投稿可、メンバーは閲覧可)。

## 今後の連携(ロードマップ)

- **ウェブサイト連携**: 財団ウェブサイトの更新を `#announcements` に自動投稿(RSS/Webhook で実装可能)
- **Peatix 連携**: Peatix のイベント情報を `#events` に自動投稿
  - Peatix には公開APIがないため、主催者アカウントのイベントページを定期チェックして新着を通知する方式、
    または Zapier/IFTTT 経由の Webhook 連携が現実的です
- どちらも Discord の **Webhook**(チャンネル設定 → 連携サービス → Webhook)を使えば、外部から `#announcements` / `#events` に直接投稿できます

## ファイル構成

```
crf-discord/
├── bot.py             ボット本体(セットアップ・入場フォーム・Q&A)
├── rules.md           サーバーのルール(#rules に掲示される)
├── knowledge/crf.md   CRFボットのナレッジベース
├── requirements.txt   依存パッケージ
└── .env.example       環境変数のテンプレート
```

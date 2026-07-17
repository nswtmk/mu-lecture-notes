# CRF Discord サーバー セットアップキット

意識研究財団(Consciousness Research Foundation / **CRF**)の Discord サーバーを立ち上げるための一式です。

- **CRFボット**: サーバー構造を自動構築し、財団についての質問に答えるボット
- **入場審査**: Discord公式の「参加申請(Server Member Applications)」を使用。招待リンクを開くと質問フォーム(紹介者・関わるプロジェクト)が表示され、運営の承認で入場
- **ルール掲示**: サーバーのルール(`rules.md`)を自動掲示

## 構築されるサーバー構造

```
INFO
├── #welcome        歓迎・最初の案内
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

- 入場審査はDiscord公式の参加申請で行うため、サーバーに入れた人=承認済みの人です
- チャンネルはすべて通常の公開チャンネルです(welcome / rules / announcements / office のみ投稿は管理者に限定)

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
`#welcome` への歓迎メッセージ掲示がすべて自動で行われます。
(何度実行しても安全です。既存チャンネルは作り直さず設定だけ更新します)

## 入場の流れ

| 経路 | 方法 |
|---|---|
| **参加申請** | サーバー設定 → 安全設定 で「参加には申請が必要」を有効にし、カスタム質問(紹介者・関わるプロジェクト)を設定。招待リンクを開いた人に質問フォームが表示され、運営が承認すると入場。入場した時点で全チャンネルが利用できます |

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
├── bot.py             ボット本体(セットアップ・自動ロール付与・Q&A)
├── rules.md           サーバーのルール(#rules に掲示される)
├── knowledge/crf.md   CRFボットのナレッジベース
├── requirements.txt   依存パッケージ
└── .env.example       環境変数のテンプレート
```

## 運用TODO

- [ ] **Gmailの差出人エイリアス設定**: nswtmk@gmail.com に info@technel.world を「別のアドレスから送信」として追加し、差出人ドロップダウンで切り替えられるようにする(現状は別ログインが必要)。手順: Gmail設定 → アカウントとインポート → 「他のメールアドレスを追加」→ info@technel.world のSMTP情報で認証。役員向け一斉メールはinfo@technel.worldから送る運用のため
- [ ] 週次サマリーの自動化。運用フロー確定: ①ボットが週次でDiscordログを書き出し ②AIがサマリーPDFを生成 ③**まず七沢さんにプッシュ通知で確認を求める** ④承認後に役員へメール送付(宛先: 役員一斉、送信元: info@technel.world)。発行曜日・時刻は未確定

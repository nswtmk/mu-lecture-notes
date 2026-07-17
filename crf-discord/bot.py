"""CRF Discord Bot — 意識研究財団(Consciousness Research Foundation)

入場審査は Discord 公式の「参加申請(Server Member Applications)」で行う前提。
(サーバー設定 → 安全設定 → 「参加には申請が必要」+ カスタム質問で紹介者・プロジェクトを質問)

サーバーに入れた人=承認済みの人なので、チャンネルはすべて通常の公開チャンネル。
(お知らせ系のみ書き込みを管理者に制限)

機能:
  1. /crf-setup : サーバー構造(カテゴリ・チャンネル・ルール掲示)を自動構築
  2. Q&A        : ボットにメンションすると、ナレッジベースをもとに財団について回答(Claude API 使用)

必要な環境変数:
  DISCORD_BOT_TOKEN  : Discord ボットのトークン(必須)
  ANTHROPIC_API_KEY  : Claude API キー(任意。未設定時はナレッジベースの抜粋で回答)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("crf-bot")

BASE_DIR = Path(__file__).parent
KNOWLEDGE = (BASE_DIR / "knowledge" / "crf.md").read_text(encoding="utf-8")
RULES = (BASE_DIR / "rules.md").read_text(encoding="utf-8")

# サーバー構造の定義。/crf-setup がこの通りに構築する。
# (カテゴリ名, [(チャンネル名, トピック, 種別), ...])
# 種別: "open"=誰でも閲覧・投稿可 / "readonly"=誰でも閲覧可・投稿は管理者のみ
SERVER_STRUCTURE = [
    ("INFO", [
        ("welcome", "ようこそCRFへ! まずは #rules をどうぞ", "readonly"),
        ("rules", "このサーバーのルール", "readonly"),
        ("announcements", "お知らせ", "readonly"),
        ("events", "イベント・研究会の情報", "open"),
    ]),
    ("COMMUNITY", [
        ("introductions", "自己紹介 / Introduce yourself", "open"),
        ("general", "一般・雑談", "open"),
        ("random", "何でも好きなことを投稿できるチャンネル", "open"),
        ("research-info", "リサーチ関係の情報共有", "open"),
    ]),
    ("PROJECTS", [
        ("technology", "意識とテクノロジー(責任者: 鈴木啓介)", "open"),
        ("buddhism", "仏教と意識(責任者: 藤野正寛)", "open"),
        ("satoyama", "意識と里山(責任者: 信原幸弘) — 里山・宮沢賢治読書会・ベルクソン読書会", "open"),
        ("origins-planning", "意識の根源探求(責任者: 七沢智樹)(計画中)", "open"),
        ("hard-problem-planning", "意識のハードプロブレム(責任者: 渡邉正峰)(計画中)", "open"),
        ("jomon-planning", "実験意識考古学(責任者: 未定)(計画中)", "open"),
        ("natural-computation-planning", "自然計算AI(責任者: 未定)(計画中)", "open"),
        ("forest", "森(広域北杜の森)プロジェクト — 実験フィールド", "open"),
    ]),
    ("CONFERENCE", [
        ("conference", "カンファレンス関係", "open"),
    ]),
    ("OFFICE", [
        ("office", "事務関係。財務情報・定款・理事の情報などを公開", "readonly"),
        ("website", "財団Webサイトの検討・リニューアル", "open"),
    ]),
]

# チャンネル名の変更(旧名→新名)。既存チャンネルは削除せず名前を変える
CHANNEL_RENAMES = {
    "origins": "origins-planning",
    "jomon": "jomon-planning",
    "hard-problem": "hard-problem-planning",
}

QA_SYSTEM_PROMPT = f"""あなたは意識研究財団(Consciousness Research Foundation / CRF)の \
Discordサーバーの案内ボット「CRFボット」です。以下のナレッジベースの内容に基づいて、\
財団やこのサーバーについての質問に日本語で簡潔に、親しみやすく答えてください。\
ナレッジベースにない事柄を聞かれた場合は、推測で答えず「その情報はまだ登録されていません。\
#office や運営メンバーに確認してください」と案内してください。

# ナレッジベース
{KNOWLEDGE}
"""


# ---------------------------------------------------------------------------
# ボット本体
# ---------------------------------------------------------------------------

class CRFBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()


bot = CRFBot()


def _channel_overwrites(guild: discord.Guild, kind: str):
    everyone = guild.default_role
    bot_member = guild.me
    if kind == "readonly":
        # 誰でも閲覧可。投稿は管理者とボットのみ(welcome / rules / announcements / office)
        return {
            everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False),
            bot_member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
    # "open": 通常の公開チャンネル(鍵なし)
    return {
        everyone: discord.PermissionOverwrite(view_channel=True, send_messages=True),
    }


async def run_setup(guild: discord.Guild) -> list[str]:
    """サーバー構造を構築する。何度実行しても安全(冪等)。"""
    # チャンネル名の変更(履歴を保持したままリネーム)
    for old_name, new_name in CHANNEL_RENAMES.items():
        old_ch = discord.utils.get(guild.text_channels, name=old_name)
        if old_ch and discord.utils.get(guild.text_channels, name=new_name) is None:
            await old_ch.edit(name=new_name)
            log.info("チャンネル #%s を #%s に改名しました", old_name, new_name)

    created = []
    for category_name, channels in SERVER_STRUCTURE:
        category = discord.utils.get(guild.categories, name=category_name)
        if category is None:
            category = await guild.create_category(category_name)
        for ch_name, topic, kind in channels:
            channel = discord.utils.get(guild.text_channels, name=ch_name)
            overwrites = _channel_overwrites(guild, kind)
            if channel is None:
                channel = await guild.create_text_channel(
                    ch_name, category=category, topic=topic, overwrites=overwrites
                )
                created.append(ch_name)
            else:
                await channel.edit(category=category, topic=topic, overwrites=overwrites)

    # ルールを掲示(rules.md の内容が前回から変わったときだけ、貼り直す)
    rules_ch = discord.utils.get(guild.text_channels, name="rules")
    if rules_ch:
        import hashlib

        rules_hash = hashlib.sha256(RULES.encode()).hexdigest()
        hash_file = BASE_DIR / ".rules_hash"
        if not hash_file.exists() or hash_file.read_text() != rules_hash:
            await rules_ch.purge(limit=None, reason="ルールを最新版に更新")
            # Discordの1メッセージ上限(2000字)に合わせて分割投稿
            for chunk in _split_message(RULES):
                await rules_ch.send(chunk)
            hash_file.write_text(rules_hash)

    # 旧方式の運営用チャンネルが残っていれば削除
    old_apps = discord.utils.get(guild.text_channels, name="applications")
    if old_apps:
        await old_apps.delete(reason="Discord公式の参加申請に移行したため")

    # kenji チャンネルは意識里山プロジェクト(#satoyama)に集約したため削除
    old_kenji = discord.utils.get(guild.text_channels, name="kenji")
    if old_kenji:
        await old_kenji.delete(reason="読書会を #satoyama に集約したため")

    # 歓迎メッセージを掲示(チャンネルが空のときだけ)
    welcome_ch = discord.utils.get(guild.text_channels, name="welcome")
    if welcome_ch and not [m async for m in welcome_ch.history(limit=1)]:
        embed = discord.Embed(
            title="意識研究財団(CRF)Discord へようこそ",
            description=(
                "参加申請の承認、おめでとうございます!🎉\n"
                "このサーバーは意識研究財団の関係者がどなたでも参加できるサーバーです。\n\n"
                "まずは #rules に目を通して、#introductions で自己紹介をどうぞ。\n"
                "財団について知りたいことがあれば、私(@CRF Bot)にメンションで質問してください。"
            ),
            color=discord.Color.blurple(),
        )
        await welcome_ch.send(embed=embed)

    # 旧方式の Member ロールが残っていれば削除(全チャンネル公開化に伴い不要)
    old_role = discord.utils.get(guild.roles, name="Member")
    if old_role:
        try:
            await old_role.delete(reason="全チャンネル公開化に伴い不要")
        except discord.Forbidden:
            log.warning("Memberロールを削除できません。ボットのロールをMemberより上にしてください。")

    return created


@bot.tree.command(name="crf-setup", description="CRFサーバーの構造(チャンネル・ルール)を構築します(管理者のみ)")
@app_commands.checks.has_permissions(administrator=True)
async def crf_setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True, thinking=True)
    created = await run_setup(interaction.guild)
    await interaction.followup.send(
        f"セットアップ完了 ✅ 新規作成チャンネル: "
        f"{', '.join(created) if created else 'なし(既存を更新)'}",
        ephemeral=True,
    )


# ---------------------------------------------------------------------------
# 投稿キュー(outbox): outbox/*.md を指定チャンネルに投稿する
# リモート(Claude Code)からGitHub経由でDiscordに投稿を届けるための仕組み。
# ファイル形式:
#   channel: チャンネル名
#   category: カテゴリ名(チャンネルがない場合の作成先。省略可)
#   topic: チャンネルトピック(省略可)
#   ---
#   本文(Markdown)
# ---------------------------------------------------------------------------

OUTBOX_DIR = BASE_DIR / "outbox"
OUTBOX_STATE = BASE_DIR / ".outbox_posted.json"


async def process_outbox(guild: discord.Guild):
    if not OUTBOX_DIR.exists():
        return
    posted = json.loads(OUTBOX_STATE.read_text()) if OUTBOX_STATE.exists() else []
    for path in sorted(OUTBOX_DIR.glob("*.md")):
        if path.name in posted:
            continue
        raw = path.read_text(encoding="utf-8")
        headers, _, body = raw.partition("\n---\n")
        meta = {}
        for line in headers.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        ch_name = meta.get("channel")
        if not ch_name or not body.strip():
            log.warning("outbox %s: channel指定または本文がありません", path.name)
            continue
        channel = discord.utils.get(guild.text_channels, name=ch_name)
        if channel is None and meta.get("category"):
            category = discord.utils.get(guild.categories, name=meta["category"])
            if category is None:
                category = await guild.create_category(meta["category"])
            channel = await guild.create_text_channel(ch_name, category=category)
            log.info("outbox: チャンネル #%s を作成しました", ch_name)
        if channel is None:
            log.warning("outbox %s: チャンネル #%s が見つかりません", path.name, ch_name)
            continue
        if meta.get("replace") == "bot":
            # ボット自身の過去の投稿を削除してから貼り直す(訂正用)
            async for m in channel.history(limit=100):
                if m.author == guild.me:
                    await m.delete()
        if meta.get("topic"):
            await channel.edit(topic=meta["topic"][:1024])
        for chunk in _split_message(body.strip()):
            await channel.send(chunk)
        posted.append(path.name)
        OUTBOX_STATE.write_text(json.dumps(posted, ensure_ascii=False, indent=1))
        log.info("outbox: %s を #%s に投稿しました", path.name, ch_name)


_auto_update_started = False


async def _auto_update_loop():
    """3分ごとにGitHubの更新を確認し、新しいコードがあれば取り込んで自動再起動する。"""
    repo_dir = str(BASE_DIR.parent)
    while True:
        await asyncio.sleep(180)
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["git", "-C", repo_dir, "pull", "--ff-only"],
                capture_output=True, text=True, timeout=60,
            )
            out = (result.stdout + result.stderr).strip()
            if result.returncode == 0 and "Already up to date" not in out:
                log.info("更新を検出、再起動します: %s", out)
                os.execv(sys.executable, [sys.executable, str(BASE_DIR / "bot.py")])
        except Exception:
            log.exception("auto-update check failed")


@bot.event
async def on_ready():
    global _auto_update_started
    log.info("Logged in as %s (%s)", bot.user, bot.user.id)
    # CRF_AUTO_SETUP=1 のときは、起動しただけで全サーバーにセットアップを実行
    if os.environ.get("CRF_AUTO_SETUP") == "1":
        for guild in bot.guilds:
            log.info("Auto setup: %s", guild.name)
            created = await run_setup(guild)
            log.info("Auto setup done for %s (created: %s)", guild.name, created or "none")
    # 投稿キューの処理(未投稿の outbox/*.md を投稿)
    for guild in bot.guilds:
        try:
            await process_outbox(guild)
        except Exception:
            log.exception("outbox processing failed for %s", guild.name)
    # 自動アップデート(CRF_AUTO_UPDATE=0 で無効化)
    if not _auto_update_started and os.environ.get("CRF_AUTO_UPDATE") != "0":
        _auto_update_started = True
        asyncio.create_task(_auto_update_loop())
        log.info("自動アップデートを有効化(3分間隔でGitHubを確認)")


# ---------------------------------------------------------------------------
# Q&A: 財団についての質問に答える
# ---------------------------------------------------------------------------

_anthropic_client = None


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None and os.environ.get("ANTHROPIC_API_KEY"):
        from anthropic import AsyncAnthropic

        _anthropic_client = AsyncAnthropic()
    return _anthropic_client


async def answer_question(question: str) -> str:
    client = _get_anthropic()
    if client is None:
        return _fallback_answer(question)
    try:
        response = await client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1024,
            system=[{
                "type": "text",
                "text": QA_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": question}],
        )
        return next((b.text for b in response.content if b.type == "text"), "(回答を生成できませんでした)")
    except Exception:
        log.exception("Claude API call failed")
        return _fallback_answer(question)


# ---------------------------------------------------------------------------
# 管理者指示モード: 管理者がDM/メンションで指示すると、サーバーを実際に操作する
# ---------------------------------------------------------------------------

ADMIN_TOOLS = [
    {
        "name": "list_channels",
        "description": "サーバーの全テキストチャンネルの名前・カテゴリ・トピックの一覧を取得する。操作の前に現状把握のために使う。",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "read_recent_messages",
        "description": "指定チャンネルの直近のメッセージを読む(新しい順)。",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_name": {"type": "string", "description": "チャンネル名(#は不要)"},
                "limit": {"type": "integer", "description": "取得件数(最大30)"},
            },
            "required": ["channel_name"],
        },
    },
    {
        "name": "send_message",
        "description": "指定チャンネルにメッセージを投稿する。",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_name": {"type": "string", "description": "チャンネル名(#は不要)"},
                "content": {"type": "string", "description": "投稿する本文(Markdown可、2000字以内)"},
            },
            "required": ["channel_name", "content"],
        },
    },
    {
        "name": "edit_channel_topic",
        "description": "指定チャンネルのトピック(説明文)を変更する。",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_name": {"type": "string", "description": "チャンネル名(#は不要)"},
                "topic": {"type": "string", "description": "新しいトピック(1024字以内)"},
            },
            "required": ["channel_name", "topic"],
        },
    },
    {
        "name": "pin_last_message",
        "description": "指定チャンネルでボットが直近に投稿したメッセージをピン留めする。",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_name": {"type": "string", "description": "チャンネル名(#は不要)"},
            },
            "required": ["channel_name"],
        },
    },
]

ADMIN_SYSTEM_PROMPT = f"""あなたは意識研究財団(CRF)のDiscordサーバーを管理するボット「CRFボット」です。\
いま話しかけているのはサーバーの管理者です。管理者の指示に従って、ツールを使って実際にサーバーを操作してください。

方針:
- 指示が明確なら、確認を求めずに実行して結果を報告する
- チャンネル名が曖昧なときは list_channels で確認してから操作する
- 投稿文はCRFのコミュニティに合う、丁寧で親しみやすい日本語で書く
- 破壊的な操作(削除など)のツールはないので、できない指示には「できない」と正直に答える
- 完了したら、何をどのチャンネルにしたかを簡潔に報告する

# 財団についてのナレッジベース
{KNOWLEDGE}
"""


async def _execute_admin_tool(guild: discord.Guild, name: str, args: dict) -> str:
    def _find(ch_name: str):
        return discord.utils.get(guild.text_channels, name=ch_name.lstrip("#"))

    try:
        if name == "list_channels":
            lines = [
                f"#{c.name} (カテゴリ: {c.category.name if c.category else 'なし'}) — {c.topic or 'トピックなし'}"
                for c in guild.text_channels
            ]
            return "\n".join(lines)
        channel = _find(args["channel_name"])
        if channel is None:
            return f"エラー: チャンネル #{args['channel_name']} が見つかりません"
        if name == "read_recent_messages":
            limit = min(int(args.get("limit", 10)), 30)
            msgs = [m async for m in channel.history(limit=limit)]
            return "\n".join(
                f"[{m.created_at:%Y-%m-%d %H:%M}] {m.author.display_name}: {m.content[:200]}"
                for m in msgs
            ) or "(メッセージなし)"
        if name == "send_message":
            sent = await channel.send(args["content"][:2000])
            return f"投稿しました: {sent.jump_url}"
        if name == "edit_channel_topic":
            await channel.edit(topic=args["topic"][:1024])
            return f"#{channel.name} のトピックを変更しました"
        if name == "pin_last_message":
            async for m in channel.history(limit=20):
                if m.author == guild.me:
                    await m.pin()
                    return f"ピン留めしました: {m.jump_url}"
            return "ボットの直近の投稿が見つかりません"
        return f"エラー: 不明なツール {name}"
    except Exception as e:  # ツール失敗はエラー文字列で返し、AIに対処させる
        log.exception("admin tool failed")
        return f"エラー: {e}"


async def run_admin_agent(guild: discord.Guild, instruction: str) -> str:
    """管理者の指示をClaudeが解釈し、ツールでサーバーを操作する。"""
    client = _get_anthropic()
    if client is None:
        return "管理者指示モードには ANTHROPIC_API_KEY の設定が必要です。"

    messages = [{"role": "user", "content": instruction}]
    for _ in range(8):
        response = await client.messages.create(
            model="claude-opus-4-8",
            max_tokens=2048,
            system=[{
                "type": "text",
                "text": ADMIN_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            tools=ADMIN_TOOLS,
            messages=messages,
        )
        if response.stop_reason != "tool_use":
            return next(
                (b.text for b in response.content if b.type == "text"),
                "完了しました。",
            )
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type == "tool_use":
                log.info("admin tool: %s %s", block.name, block.input)
                output = await _execute_admin_tool(guild, block.name, block.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
        messages.append({"role": "user", "content": results})
    return "手順が多すぎたため途中で停止しました。指示を分けて試してください。"


def _fallback_answer(question: str) -> str:
    """API キー未設定・API 障害時: ナレッジベースから関連セクションを抜粋して返す。"""
    sections = KNOWLEDGE.split("\n## ")
    words = [w for w in question.replace("?", " ").replace("?", " ").split() if len(w) > 1]
    best = max(
        sections[1:],
        key=lambda s: sum(1 for w in words if w in s),
        default="",
    )
    header = "(現在AI回答は利用できないため、ナレッジベースからの抜粋です)\n\n"
    text = "## " + best if best else KNOWLEDGE
    return (header + text)[:1900]


def _split_message(text: str, limit: int = 1990) -> list[str]:
    chunks, current = [], ""
    for line in text.splitlines(keepends=True):
        if len(current) + len(line) > limit:
            chunks.append(current)
            current = ""
        current += line
    if current:
        chunks.append(current)
    return chunks


@bot.tree.command(name="crf", description="意識研究財団について質問する")
@app_commands.describe(question="聞きたいこと")
async def crf_question(interaction: discord.Interaction, question: str):
    await interaction.response.defer(thinking=True)
    answer = await answer_question(question)
    for chunk in _split_message(answer):
        await interaction.followup.send(chunk)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    is_dm = message.guild is None
    mentioned = bot.user in message.mentions
    if not (is_dm or mentioned):
        await bot.process_commands(message)
        return

    text = message.content.replace(f"<@{bot.user.id}>", "").strip()
    if not text:
        await bot.process_commands(message)
        return

    # 対象サーバーと発言者の権限を特定(DMの場合は共通サーバーから)
    guild = message.guild or next(
        (g for g in bot.guilds if g.get_member(message.author.id)), None
    )
    member = guild.get_member(message.author.id) if guild else None
    is_admin = bool(member and member.guild_permissions.administrator)

    async with message.channel.typing():
        if is_admin and guild and _get_anthropic():
            # 管理者: サーバー操作もできる指示モード
            reply = await run_admin_agent(guild, text)
        else:
            # 一般メンバー: 財団についてのQ&A
            reply = await answer_question(text)
    for chunk in _split_message(reply):
        await message.reply(chunk)
    await bot.process_commands(message)


if __name__ == "__main__":
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise SystemExit("環境変数 DISCORD_BOT_TOKEN を設定してください(.env.example を参照)")
    bot.run(token)

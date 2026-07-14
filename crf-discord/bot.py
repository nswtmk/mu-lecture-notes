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

import logging
import os
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
        ("technology", "テクノロジー・プロジェクト", "open"),
        ("satoyama", "里山プロジェクト", "open"),
        ("buddhism", "仏教プロジェクト", "open"),
        ("forest", "フォレスト(森)プロジェクト — これから注力していく領域", "open"),
    ]),
    ("CONFERENCE", [
        ("conference", "カンファレンス関係", "open"),
    ]),
    ("OFFICE", [
        ("office", "事務関係。財務情報・定款・理事の情報などを公開", "readonly"),
    ]),
]

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

    # ルールを掲示(チャンネルが空のときだけ。再実行での重複投稿を防ぐ)
    rules_ch = discord.utils.get(guild.text_channels, name="rules")
    if rules_ch and not [m async for m in rules_ch.history(limit=1)]:
        # Discordの1メッセージ上限(2000字)に合わせて分割投稿
        for chunk in _split_message(RULES):
            await rules_ch.send(chunk)

    # 旧方式の運営用チャンネルが残っていれば削除
    old_apps = discord.utils.get(guild.text_channels, name="applications")
    if old_apps:
        await old_apps.delete(reason="Discord公式の参加申請に移行したため")

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


@bot.event
async def on_ready():
    log.info("Logged in as %s (%s)", bot.user, bot.user.id)
    # CRF_AUTO_SETUP=1 のときは、起動しただけで全サーバーにセットアップを実行
    if os.environ.get("CRF_AUTO_SETUP") == "1":
        for guild in bot.guilds:
            log.info("Auto setup: %s", guild.name)
            created = await run_setup(guild)
            log.info("Auto setup done for %s (created: %s)", guild.name, created or "none")


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
    # ボットへのメンションで質問に答える
    if bot.user in message.mentions:
        question = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if question:
            async with message.channel.typing():
                answer = await answer_question(question)
            for chunk in _split_message(answer):
                await message.reply(chunk)
    await bot.process_commands(message)


if __name__ == "__main__":
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise SystemExit("環境変数 DISCORD_BOT_TOKEN を設定してください(.env.example を参照)")
    bot.run(token)

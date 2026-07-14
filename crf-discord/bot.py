"""CRF Discord Bot — 意識研究財団(Consciousness Research Foundation)

機能:
  1. /crf-setup  : サーバー構造(ロール・カテゴリ・チャンネル・ルール掲示・入場フォーム)を自動構築
  2. 入場フォーム : #welcome のボタン → アンケートモーダル(紹介者・関わるプロジェクト)→ Member ロール付与
  3. /admit      : フォームを通さない入場経路(管理者がメンバーを直接承認)
  4. Q&A         : ボットにメンションすると、ナレッジベースをもとに財団について回答(Claude API 使用)

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

MEMBER_ROLE = "Member"

# サーバー構造の定義。/crf-setup がこの通りに構築する。
# (カテゴリ名, [(チャンネル名, トピック, 種別), ...])
# 種別: "open"=@everyone可視 / "member"=Memberのみ / "readonly"=Memberは閲覧のみ
SERVER_STRUCTURE = [
    ("INFO", [
        ("welcome", "入場受付。アンケートに回答して入場してください / Entry point", "open"),
        ("rules", "このサーバーのルール", "open_readonly"),
        ("announcements", "お知らせ", "readonly"),
        ("events", "イベント・研究会の情報", "member"),
    ]),
    ("COMMUNITY", [
        ("introductions", "自己紹介 / Introduce yourself", "member"),
        ("general", "一般・雑談", "member"),
        ("random", "何でも好きなことを投稿できるチャンネル", "member"),
        ("research-info", "リサーチ関係の情報共有", "member"),
    ]),
    ("PROJECTS", [
        ("technology", "テクノロジー・プロジェクト", "member"),
        ("satoyama", "里山プロジェクト", "member"),
        ("buddhism", "仏教プロジェクト", "member"),
        ("forest", "フォレスト(森)プロジェクト — これから注力していく領域", "member"),
    ]),
    ("CONFERENCE", [
        ("conference", "カンファレンス関係", "member"),
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
# 入場アンケート(フォーム)
# ---------------------------------------------------------------------------

class OnboardingModal(discord.ui.Modal, title="CRF 入場アンケート"):
    referrer = discord.ui.TextInput(
        label="紹介者(あなたを紹介してくれた方)",
        placeholder="例: 山田太郎さん",
        max_length=100,
    )
    project = discord.ui.TextInput(
        label="関わるプロジェクト",
        placeholder="例: テクノロジー / 里山 / 仏教 / 森 / カンファレンス など",
        max_length=200,
    )
    intro = discord.ui.TextInput(
        label="ひとこと自己紹介(任意)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=MEMBER_ROLE)
        if role is None:
            await interaction.response.send_message(
                "セットアップが完了していません。管理者に連絡してください。", ephemeral=True
            )
            return

        await interaction.user.add_roles(role, reason="入場アンケートに回答")
        await interaction.response.send_message(
            "ようこそ CRF へ! 🎉 すべてのチャンネルが見えるようになりました。"
            "まずは #introductions で自己紹介をどうぞ。",
            ephemeral=True,
        )

        intro_ch = discord.utils.get(guild.text_channels, name="introductions")
        if intro_ch:
            embed = discord.Embed(
                title="新しいメンバーが参加しました",
                color=discord.Color.green(),
            )
            embed.add_field(name="メンバー", value=interaction.user.mention, inline=False)
            embed.add_field(name="紹介者", value=str(self.referrer), inline=True)
            embed.add_field(name="関わるプロジェクト", value=str(self.project), inline=True)
            if self.intro.value:
                embed.add_field(name="自己紹介", value=self.intro.value, inline=False)
            await intro_ch.send(embed=embed)


class WelcomeView(discord.ui.View):
    """#welcome に掲示する永続ボタン。再起動後も動作する。"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="アンケートに回答して入場する",
        style=discord.ButtonStyle.primary,
        emoji="📝",
        custom_id="crf:onboarding",
    )
    async def onboarding(self, interaction: discord.Interaction, _button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=MEMBER_ROLE)
        if role and role in interaction.user.roles:
            await interaction.response.send_message("すでに入場済みです。", ephemeral=True)
            return
        await interaction.response.send_modal(OnboardingModal())


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
        self.add_view(WelcomeView())  # 永続ビューの再登録
        await self.tree.sync()


bot = CRFBot()


def _channel_overwrites(guild: discord.Guild, kind: str, member_role: discord.Role):
    everyone = guild.default_role
    bot_member = guild.me
    if kind == "open":
        # 未入場者も見える(welcome)。書き込みは不可、ボタン操作のみ。
        return {
            everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False),
            member_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
            bot_member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
    if kind == "open_readonly":
        # 未入場者も読める(rules)。
        return {
            everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False),
            bot_member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
    if kind == "readonly":
        # Member は閲覧のみ(announcements / office)。投稿は管理者とボット。
        return {
            everyone: discord.PermissionOverwrite(view_channel=False),
            member_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
            bot_member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
    # "member": Member のみ閲覧・投稿可
    return {
        everyone: discord.PermissionOverwrite(view_channel=False),
        member_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        bot_member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
    }


@bot.tree.command(name="crf-setup", description="CRFサーバーの構造(ロール・チャンネル・ルール)を構築します(管理者のみ)")
@app_commands.checks.has_permissions(administrator=True)
async def crf_setup(interaction: discord.Interaction):
    guild = interaction.guild
    await interaction.response.defer(ephemeral=True, thinking=True)

    member_role = discord.utils.get(guild.roles, name=MEMBER_ROLE)
    if member_role is None:
        member_role = await guild.create_role(
            name=MEMBER_ROLE, colour=discord.Colour.teal(), reason="CRF setup"
        )

    created = []
    for category_name, channels in SERVER_STRUCTURE:
        category = discord.utils.get(guild.categories, name=category_name)
        if category is None:
            category = await guild.create_category(category_name)
        for ch_name, topic, kind in channels:
            channel = discord.utils.get(guild.text_channels, name=ch_name)
            overwrites = _channel_overwrites(guild, kind, member_role)
            if channel is None:
                channel = await guild.create_text_channel(
                    ch_name, category=category, topic=topic, overwrites=overwrites
                )
                created.append(ch_name)
            else:
                await channel.edit(category=category, topic=topic, overwrites=overwrites)

    # ルールを掲示
    rules_ch = discord.utils.get(guild.text_channels, name="rules")
    if rules_ch:
        # Discordの1メッセージ上限(2000字)に合わせて分割投稿
        for chunk in _split_message(RULES):
            await rules_ch.send(chunk)

    # 入場フォームを掲示
    welcome_ch = discord.utils.get(guild.text_channels, name="welcome")
    if welcome_ch:
        embed = discord.Embed(
            title="意識研究財団(CRF)Discord へようこそ",
            description=(
                "このサーバーは意識研究財団の関係者がどなたでも参加できるサーバーです。\n\n"
                "下のボタンから **紹介者** と **関わるプロジェクト** についての"
                "アンケートに回答すると入場できます。\n\n"
                "フォームでの入場が難しい場合は、管理者が `/admit` コマンドで"
                "直接入場を承認することもできます。"
            ),
            color=discord.Color.blurple(),
        )
        await welcome_ch.send(embed=embed, view=WelcomeView())

    await interaction.followup.send(
        f"セットアップ完了 ✅ 新規作成チャンネル: {', '.join(created) if created else 'なし(既存を更新)'}",
        ephemeral=True,
    )


@bot.tree.command(name="admit", description="アンケートフォームを通さずにメンバーを入場させます(管理者のみ)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(user="入場させるメンバー")
async def admit(interaction: discord.Interaction, user: discord.Member):
    role = discord.utils.get(interaction.guild.roles, name=MEMBER_ROLE)
    if role is None:
        await interaction.response.send_message("先に /crf-setup を実行してください。", ephemeral=True)
        return
    await user.add_roles(role, reason=f"/admit by {interaction.user}")
    await interaction.response.send_message(f"{user.mention} を入場させました。", ephemeral=True)


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

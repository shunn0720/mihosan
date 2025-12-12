=== BEGIN discordbot.py ===
# -*- coding: utf-8 -*-
import os
import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Button

# =========================
# 環境変数
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_USER_ID = 1258186353405984841  # Mu~𖤐さんのID

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN が設定されていません")

# =========================
# Intents
# =========================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# Persistent View
# =========================
class MuteTimerView(View):
    def __init__(self):
        super().__init__(timeout=None)
        for i in range(1, 10):
            row = 0 if i <= 5 else 1
            self.add_item(MuteButton(label=str(i), hours=i, row=row))
        self.add_item(UnmuteButton(row=2))


class MuteButton(Button):
    def __init__(self, label: str, hours: int, row: int = 0):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
            row=row,
            custom_id=f"mute_timer_{hours}",
        )
        self.hours = hours

    async def callback(self, interaction: discord.Interaction):
        # Interaction Failed 防止（最重要）
        await interaction.response.defer_update()

        member = interaction.guild.get_member(TARGET_USER_ID)
        if not member or not member.voice:
            await interaction.channel.send(
                "❌ Mu~𖤐さんがVCに居ないので設定できませんでした。",
                delete_after=10,
            )
            return

        # 古いメッセージ削除（失敗しても止めない）
        try:
            await interaction.message.delete()
        except discord.NotFound:
            pass

        embed = discord.Embed(
            title="タイマー",
            description=(
                f"{self.hours}時間後にミュートタイマーをセットしました。\n"
                "押した数字の時間後にミュートされます。\n"
                "解除したいときは解除ボタンを押してください。"
            ),
            color=discord.Color.blue(),
        )

        await interaction.channel.send(embed=embed, view=MuteTimerView())
        await interaction.channel.send(
            f"⏳ {self.hours}時間後にMu~𖤐さんをミュートします（※自動解除なし）"
        )

        asyncio.create_task(self.mute_after_delay(interaction.guild, interaction.channel))

    async def mute_after_delay(self, guild: discord.Guild, channel: discord.TextChannel):
        await asyncio.sleep(self.hours * 3600)
        member = guild.get_member(TARGET_USER_ID)
        if member and member.voice and not member.voice.mute:
            try:
                await member.edit(mute=True)
                await channel.send(
                    f"🔇 {member.display_name} を{self.hours}時間後にミュートしました。"
                )
            except Exception as e:
                await channel.send(f"⚠️ ミュートに失敗しました：{e}")
        else:
            await channel.send(
                "⚠️ ミュートできませんでした（VC不在 or 既にミュート）"
            )


class UnmuteButton(Button):
    def __init__(self, row: int = 2):
        super().__init__(
            label="🔊 ミュート解除",
            style=discord.ButtonStyle.success,
            row=row,
            custom_id="mute_timer_unmute",
        )

    async def callback(self, interaction: discord.Interaction):
        # Interaction Failed 防止
        await interaction.response.defer_update()

        member = interaction.guild.get_member(TARGET_USER_ID)

        try:
            await interaction.message.delete()
        except discord.NotFound:
            pass

        embed = discord.Embed(
            title="タイマー",
            description=(
                "ミュート解除の操作が行われました。\n"
                "再度タイマーをセットできます。"
            ),
            color=discord.Color.blue(),
        )

        await interaction.channel.send(embed=embed, view=MuteTimerView())

        if member and member.voice and member.voice.mute:
            try:
                await member.edit(mute=False)
                await interaction.channel.send(
                    f"🔊 {member.display_name} のミュートを解除しました。"
                )
            except Exception as e:
                await interaction.channel.send(f"⚠️ 解除に失敗しました：{e}")
        else:
            await interaction.channel.send(
                "❗ ミュートされていないか、VCにいません。"
            )


# =========================
# Command
# =========================
@bot.command(name="タイマー")
async def timer(ctx: commands.Context):
    embed = discord.Embed(
        title="タイマー",
        description=(
            "押した数字の時間後にミュートされます。\n"
            "解除したくなったら解除ボタンを押してください。"
        ),
        color=discord.Color.blue(),
    )
    await ctx.send(embed=embed, view=MuteTimerView())


# =========================
# Events
# =========================
@bot.event
async def on_ready():
    bot.add_view(MuteTimerView())
    print(f"{bot.user} is ready.")


# =========================
# Run
# =========================
bot.run(TOKEN)
=== END discordbot.py ===

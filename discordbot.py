# main.py
# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio
import os

TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_USER_ID = 1258186353405984841  # Mu~𖤐さんのID

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

class MuteTimerView(View):
    def __init__(self):
        super().__init__(timeout=None)
        for i in range(1, 10):
            self.add_item(MuteButton(label=str(i), hours=i, row=0))
        self.add_item(UnmuteButton(row=1))

class MuteButton(Button):
    def __init__(self, label: str, hours: int, row: int = 0):
        super().__init__(label=label, style=discord.ButtonStyle.primary, row=row)
        self.hours = hours

    async def callback(self, interaction: discord.Interaction):
        member = interaction.guild.get_member(TARGET_USER_ID)

        if not member or not member.voice:
            await interaction.response.send_message(
                "❌ Mu~𖤐さんがVCに居ないので設定できませんでした。",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"⏳ {self.hours}時間後にMu~𖤐さんをミュートします（※自動解除はされません）",
            ephemeral=True
        )

        asyncio.create_task(self.mute_after_delay(interaction, member))

    async def mute_after_delay(self, interaction: discord.Interaction, member: discord.Member):
        await asyncio.sleep(self.hours * 3600)

        member = interaction.guild.get_member(TARGET_USER_ID)
        if member and member.voice and not member.voice.mute:
            try:
                await member.edit(mute=True)
                await interaction.channel.send(f"🔇 {member.display_name} を{self.hours}時間後にミュートしました。")
            except Exception as e:
                await interaction.channel.send(f"⚠️ ミュートに失敗しました：{e}")
        else:
            await interaction.channel.send("⚠️ ミュートできませんでした（VC不在か既にミュート済み）")

class UnmuteButton(Button):
    def __init__(self, row: int = 1):
        super().__init__(label="🔊 ミュート解除", style=discord.ButtonStyle.success, row=row)

    async def callback(self, interaction: discord.Interaction):
        member = interaction.guild.get_member(TARGET_USER_ID)
        if member and member.voice and member.voice.mute:
            try:
                await member.edit(mute=False)
                await interaction.response.send_message(f"🔊 {member.display_name} のミュートを解除しました。", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"⚠️ 解除に失敗しました：{e}", ephemeral=True)
        else:
            await interaction.response.send_message("❗ ミュートされていないか、VCにいません。", ephemeral=True)

@bot.command()
async def タイマー(ctx):
    embed = discord.Embed(
        title="タイマー",
        description="押した数字の時間後にミュートなります。\n解除したくなったら解除ボタン押してください。",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=MuteTimerView())

@bot.event
async def on_ready():
    print(f"{bot.user} is ready.")

bot.run(TOKEN)

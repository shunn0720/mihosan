import discord
from discord.ext import commands
from datetime import datetime, timedelta
import os
import random
import logging
import asyncio
from pytz import timezone

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Botの設定
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 定数設定
target_channel_ids = [1282323693502070826, 1300417181690892288]
restricted_user_id = 398305854836965399
monitored_users = [
    302778094320615425, 785158429379395634, 351806034882592792,
    789472552383676418, 692704796364505088, 780189567747489794,
    824970594465480716, 1136514267085021244, 787775223326834699,
]
ignored_channel_ids = [
    1282941830744510514, 1282968954884591648, 1282952456120303709,
]
JST = timezone('Asia/Tokyo')
farewell_messages = [
    "{mention} いい夢見なっつ！",
    "{mention} 夢で会おうなっつ！",
    "{mention} ちゃんと布団で寝なっつ！",
    "{mention} また起きたら来てくれよなっつ！",
]

# Bot起動時
@bot.event
async def on_ready():
    logger.info(f"Botがログインしました: {bot.user.name}")

# ボイスチャンネルの状態を監視
@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    restricted_user = guild.get_member(restricted_user_id)
    now = datetime.now(JST)

    # 夜23:00〜翌3:00のみ処理
    if not (23 <= now.hour or now.hour < 3):
        return

    for channel in {before.channel, after.channel}:
        if channel and channel.id not in ignored_channel_ids:
            if any(user.id in monitored_users for user in channel.members):
                # 監視対象者がいる場合、Dさんにチャンネルを非表示
                if restricted_user:
                    try:
                        await channel.set_permissions(restricted_user, view_channel=False)
                        logger.info(f"Dさんからチャンネル {channel.name} を非表示にしました。")
                    except discord.Forbidden:
                        logger.warning(f"Dさんの権限変更に失敗しました: {channel.name}")
            elif restricted_user:
                # 監視対象者がいなくなった場合、Dさんの権限をリセット
                try:
                    await channel.set_permissions(restricted_user, overwrite=None)
                    logger.info(f"Dさんにチャンネル {channel.name} を再表示しました。")
                except discord.Forbidden:
                    logger.warning(f"Dさんの権限リセットに失敗しました: {channel.name}")

# メッセージが送信された際の処理
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content == "バルス":
        now = datetime.utcnow()
        deleted_count = 0
        async for msg in message.channel.history(limit=None, after=now - timedelta(hours=1)):
            if msg.author.id == message.author.id:
                try:
                    await msg.delete()
                    deleted_count += 1
                    if deleted_count % 10 == 0:
                        await asyncio.sleep(0.5)
                except (discord.Forbidden, discord.HTTPException) as e:
                    logger.error(f"メッセージ削除中にエラー: {e}")
                    return

        await message.channel.send(
            f"過去1時間以内にあなたが送信したメッセージを{deleted_count}件削除しました。", delete_after=2
        )
        logger.info(f"{deleted_count}件のメッセージを削除しました。")

    if message.channel.id in target_channel_ids and message.mentions:
        for user in message.mentions:
            if user.voice and user.voice.channel:
                try:
                    await user.move_to(None)
                    farewell_message = random.choice(farewell_messages).format(mention=user.mention)
                    await message.channel.send(farewell_message)
                except discord.Forbidden:
                    logger.warning(f"{user.mention}の切断権限がありません。")
                except discord.HTTPException as e:
                    logger.error(f"切断エラー: {e}")

# Botトークンを環境変数から取得して起動
try:
    bot.run(os.getenv("DISCORD_TOKEN"))
except discord.LoginFailure:
    logger.error("Discordトークンが無効です。環境変数を確認してください。")
except Exception as e:
    logger.error(f"予期しないエラーでBotが停止しました: {e}")

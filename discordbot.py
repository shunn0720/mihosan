import discord
from discord.ext import commands
from datetime import datetime, timedelta
import os
import random
import logging
import asyncio

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Botの設定
intents = discord.Intents.default()
intents.messages = True  # メッセージ関連のイベントを監視
intents.message_content = True  # メッセージの内容を取得
intents.guilds = True  # サーバー情報にアクセス
intents.members = True  # メンバー情報にアクセス
intents.voice_states = True  # ボイス状態の取得
bot = commands.Bot(command_prefix="!", intents=intents)

# ログ削除の対象チャンネルID
target_channel_ids = [1282323693502070826, 1300417181690892288]

# 制限対象のユーザー（Dさん）
restricted_user_id = 398305854836965399

# 監視対象のユーザーリスト
monitored_users = [
    302778094320615425,
    785158429379395634,
    351806034882592792,
    789472552383676418,
    692704796364505088,
]

# ランダムメッセージのリスト
farewell_messages = [
    "{mention} いい夢見なっつ！",
    "{mention} 夢で会おうなっつ！",
    "{mention} ちゃんと布団で寝なっつ！",
    "{mention} また起きたら来てくれよなっつ！"
]

# メッセージが送信された際のイベント処理
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 1. メンションが飛ばされた際にボイスチャンネルから切断
    if message.channel.id in target_channel_ids and message.mentions:
        for user in message.mentions:
            if user.voice and user.voice.channel:
                try:
                    # ユーザーをボイスチャンネルから切断
                    await user.move_to(None)
                    
                    # ランダムでメッセージを送信
                    farewell_message = random.choice(farewell_messages).format(mention=user.mention)
                    await message.channel.send(farewell_message)
                except discord.Forbidden:
                    await message.channel.send(f"{user.mention}を切断する権限がありません。")
                except discord.HTTPException as e:
                    await message.channel.send(f"エラーが発生しました: {e}")

    # 2. 「バルス」と入力した人の過去1時間のメッセージを削除
    if message.content == "バルス":
        now = datetime.utcnow()
        deleted_count = 0
        async for msg in message.channel.history(limit=None, after=now - timedelta(hours=1)):
            if msg.author.id == message.author.id:
                try:
                    await msg.delete()
                    deleted_count += 1

                    if deleted_count % 10 == 0:
                        await asyncio.sleep(0.5)  # 0.5秒の遅延を挟む

                except (discord.Forbidden, discord.HTTPException) as e:
                    await message.channel.send(f"メッセージ削除中にエラーが発生しました: {e}")
                    logger.error(f"エラー発生: {e}")
                    return

        confirmation_message = await message.channel.send(f"過去1時間以内にあなたが送信したメッセージを{deleted_count}件削除しました。", delete_after=2)
        logger.info(f"{deleted_count}件のメッセージを削除しました。")

# ボイスチャンネルの状態を監視してDさんに見えなくする
@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    restricted_user = guild.get_member(restricted_user_id)

    # ボイスチャンネルが変更された場合
    if after.channel or before.channel:
        # 現在のチャンネルを確認
        if after.channel:
            channel = after.channel

            # チャンネルに監視対象のユーザーがいる場合
            if any(user.id in monitored_users for user in channel.members):
                if restricted_user:
                    try:
                        await channel.set_permissions(restricted_user, view_channel=False)
                        logger.info(f"Dさんからチャンネル {channel.name} を非表示にしました（監視対象者がいるため）。")
                    except discord.Forbidden:
                        logger.warning(f"Dさんの権限変更に失敗しました: {channel.name}")

        # 退出したチャンネルを確認
        if before.channel:
            channel = before.channel

            # チャンネルに監視対象のユーザーがいない場合
            if not any(user.id in monitored_users for user in channel.members):
                if restricted_user:
                    try:
                        await channel.set_permissions(restricted_user, overwrite=None)
                        logger.info(f"Dさんにチャンネル {channel.name} を再び表示可能にしました（監視対象者がいなくなったため）。")
                    except discord.Forbidden:
                        logger.warning(f"Dさんの権限リセットに失敗しました: {channel.name}")

# Botトークンを環境変数から取得
try:
    bot.run(os.getenv("DISCORD_TOKEN"))
except discord.LoginFailure:
    logger.error("Discordトークンが無効です。環境変数を確認してください。")
except Exception as e:
    logger.error(f"予期しないエラーでBotが停止しました: {e}")

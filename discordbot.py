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

# ランダムメッセージのリスト
farewell_messages = [
    "{mention} いい夢見なっつ！",
    "{mention} 夢で会おうなっつ！",
    "{mention} ちゃんと布団で寝なっつ！",
    "{mention} また起きたら来てくれよなっつ！"
]

# Botが準備完了時に呼び出されるイベント
@bot.event
async def on_ready():
    logger.info(f"Botがログインしました: {bot.user.name}")
    
    # 特定のチャンネルで特定のユーザーの権限を更新
    guild = discord.utils.get(bot.guilds)  # 最初に見つかったサーバー
    if guild:
        user = guild.get_member(398305854836965399)  # ユーザーIDからメンバーを取得
        channel = guild.get_channel(1282968954884591648)  # チャンネルIDからチャンネルを取得
        
        if user and channel:
            try:
                # 特定ユーザーに「表示」権限を付与
                overwrite = channel.overwrites_for(user)
                overwrite.view_channel = True
                await channel.set_permissions(user, overwrite=overwrite)
                logger.info(f"{user.display_name} が {channel.name} を見えるようにしました。")
            except Exception as e:
                logger.error(f"チャンネル権限の更新に失敗しました: {e}")

# メッセージが送信された際のイベント処理
@bot.event
async def on_message(message):
    # Bot自身のメッセージには反応しない
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
            # 「バルス」と入力した人のメッセージだけ削除
            if msg.author.id == message.author.id:
                try:
                    await msg.delete()
                    deleted_count += 1

                    # 一定量の削除後に遅延を挟む
                    if deleted_count % 10 == 0:
                        await asyncio.sleep(0.5)  # 0.5秒の遅延を挟む

                except (discord.Forbidden, discord.HTTPException) as e:
                    await message.channel.send(f"メッセージ削除中にエラーが発生しました: {e}")
                    logger.error(f"エラー発生: {e}")
                    return

        # 削除完了メッセージを送信し、2秒後に自動削除
        confirmation_message = await message.channel.send(f"過去1時間以内にあなたが送信したメッセージを{deleted_count}件削除しました。", delete_after=2)
        logger.info(f"{deleted_count}件のメッセージを削除しました。")

# Botトークンを環境変数から取得
try:
    bot.run(os.getenv("DISCORD_TOKEN"))
except discord.LoginFailure:
    logger.error("Discordトークンが無効です。環境変数を確認してください。")
except Exception as e:
    logger.error(f"予期しないエラーでBotが停止しました: {e}")

import discord
from discord.ext import commands
from datetime import datetime, timedelta
import os
import logging
import asyncio
from pytz import timezone

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
    780189567747489794,
    824970594465480716,
    1136514267085021244,
    787775223326834699,
]

# 無視するチャンネルIDリスト
ignored_channel_ids = [
    1282941830744510514,
    1282968954884591648,
    1282952456120303709,
]

# 日本時間の指定
JST = timezone('Asia/Tokyo')

# ランダムメッセージのリスト
farewell_messages = [
    "{mention} いい夢見なっつ！",
    "{mention} 夢で会おうなっつ！",
    "{mention} ちゃんと布団で寝なっつ！",
    "{mention} また起きたら来てくれよなっつ！"
]

# 再接続間隔の調整
from discord.gateway import DiscordWebSocket
DiscordWebSocket.MAX_RECONNECT_DELAY = 60  # 最大60秒
DiscordWebSocket.MIN_RECONNECT_DELAY = 1   # 最小1秒

@bot.event
async def on_ready():
    logger.info(f"Botがログインしました: {bot.user.name}")

    # 特定のチャンネルで特定のユーザーの権限を更新
    guild = discord.utils.get(bot.guilds)  # 最初に見つかったサーバー
    if guild:
        user = guild.get_member(restricted_user_id)  # ユーザーIDからメンバーを取得
        channel = guild.get_channel(1282968954884591648)  # チャンネルIDからチャンネルを取得

        if user and channel:
            try:
                overwrite = channel.overwrites_for(user)
                overwrite.view_channel = True
                await channel.set_permissions(user, overwrite=overwrite)
                logger.info(f"{user.display_name} が {channel.name} を見えるようにしました。")
            except Exception as e:
                logger.error(f"チャンネル権限の更新に失敗しました: {e}")

@bot.event
async def on_message(message):
    # Bot自身のメッセージには反応しない
    if message.author == bot.user:
        return

    # 「バルス」と入力した人の過去1時間のメッセージを削除
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

        await message.channel.send(f"過去1時間以内にあなたが送信したメッセージを{deleted_count}件削除しました。", delete_after=2)
        logger.info(f"{deleted_count}件のメッセージを削除しました。")

@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    restricted_user = guild.get_member(restricted_user_id)

    # 現在の時間を日本時間で取得
    now = datetime.now(JST)
    if not (23 <= now.hour or now.hour < 5):
        logger.info("現在の時間は制限時間外のため処理をスキップします。")
        return

    # チャンネルが変更された場合
    if after.channel or before.channel:
        # チャンネルの権限変更
        for channel in {before.channel, after.channel}:
            if channel and channel.id not in ignored_channel_ids:
                # チャンネルに監視対象のユーザーがいる場合
                if any(user.id in monitored_users for user in channel.members):
                    if restricted_user:
                        try:
                            await channel.set_permissions(restricted_user, view_channel=False)
                            logger.info(f"Dさんからチャンネル {channel.name} を非表示にしました（監視対象者がいるため）。")
                        except discord.Forbidden:
                            logger.warning(f"Dさんの権限変更に失敗しました: {channel.name}")
                else:
                    # 監視対象がいない場合は権限をリセット
                    if restricted_user:
                        try:
                            await channel.set_permissions(restricted_user, overwrite=None)
                            logger.info(f"Dさんにチャンネル {channel.name} を再び表示可能にしました。")
                        except discord.Forbidden:
                            logger.warning(f"Dさんの権限リセットに失敗しました: {channel.name}")

# Botトークンを環境変数から取得
try:
    bot.run(os.getenv("DISCORD_TOKEN"))
except discord.LoginFailure:
    logger.error("Discordトークンが無効です。環境変数を確認してください。")
except Exception as e:
    logger.error(f"予期しないエラーでBotが停止しました: {e}")

import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
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

# 無視するチャンネル（権限変更を適用しない）
ignored_channel_ids = [
    1282941830744510514,
    1282968954884591648,
    1282952456120303709,
]

# 日本標準時（JST）のタイムゾーン
JST = timezone(timedelta(hours=9))

# ランダムメッセージのリスト
farewell_messages = [
    "{mention} いい夢見なっつ！",
    "{mention} 夢で会おうなっつ！",
    "{mention} ちゃんと布団で寝なっつ！",
    "{mention} また起きたら来てくれよなっつ！"
]

def is_restricted_time():
    """現在が日本時間の夜11時～朝3時かを判定する"""
    now = datetime.now(JST).time()
    restricted_start = datetime.strptime("23:00", "%H:%M").time()
    restricted_end = datetime.strptime("03:00", "%H:%M").time()
    
    # 夜11時から日付を跨いで朝3時まで
    return restricted_start <= now or now <= restricted_end

@bot.event
async def on_voice_state_update(member, before, after):
    """ボイスチャンネルの状態を監視し、Dさんに非表示にする処理"""
    guild = member.guild
    restricted_user = guild.get_member(restricted_user_id)

    if not restricted_user:
        logger.warning(f"Restricted user with ID {restricted_user_id} not found in guild {guild.name}")
        return

    # ボイスチャンネルが変更された場合
    if after.channel or before.channel:
        # 現在のチャンネルを確認
        if after.channel:
            channel = after.channel

            # 無視するチャンネルの場合はスキップ
            if channel.id in ignored_channel_ids:
                logger.info(f"チャンネル {channel.name} は除外対象のため処理をスキップします。")
            elif is_restricted_time():  # 日本時間の制限時間帯のみ適用
                # チャンネルに監視対象のユーザーがいる場合
                if any(user.id in monitored_users for user in channel.members):
                    try:
                        await channel.set_permissions(restricted_user, view_channel=False)
                        logger.info(f"Dさんからチャンネル {channel.name} を非表示にしました（監視対象者がいるため）。")
                    except discord.Forbidden:
                        logger.warning(f"Dさんの権限変更に失敗しました: {channel.name}")
            else:
                logger.info(f"現在は制限時間外です。Dさんのチャンネル権限は変更されません。")

        # 退出したチャンネルを確認
        if before.channel:
            channel = before.channel

            # 無視するチャンネルの場合はスキップ
            if channel.id in ignored_channel_ids:
                logger.info(f"チャンネル {channel.name} は除外対象のため処理をスキップします。")
            elif is_restricted_time():  # 日本時間の制限時間帯のみ適用
                # チャンネルに監視対象のユーザーがいない場合
                if not any(user.id in monitored_users for user in channel.members):
                    try:
                        await channel.set_permissions(restricted_user, overwrite=None)
                        logger.info(f"Dさんにチャンネル {channel.name} を再び表示可能にしました（監視対象者がいなくなったため）。")
                    except discord.Forbidden:
                        logger.warning(f"Dさんの権限リセットに失敗しました: {channel.name}")

@bot.event
async def on_ready():
    logger.info(f"Botがログインしました: {bot.user.name}")

@bot.event
async def on_message(message):
    """メッセージイベントの処理"""
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

# Botトークンを環境変数から取得
try:
    bot.run(os.getenv("DISCORD_TOKEN"))
except discord.LoginFailure:
    logger.error("Discordトークンが無効です。環境変数を確認してください。")
except Exception as e:
    logger.error(f"予期しないエラーでBotが停止しました: {e}")

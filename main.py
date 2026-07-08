import json
import discord
from datetime import datetime
from discord import app_commands
from discord.ext import commands, tasks

import os

try:
    TOKEN = os.environ["DISCORD_TOKEN"]
except KeyError:
    with open("config.json", "r", encoding="utf-8") as f:
        TOKEN = json.load(f)["token"]

with open("settings.json", "r", encoding="utf-8") as f:
    settings = json.load(f)

BIRTHDAY_CHANNEL_ID = settings["birthday_channel_id"]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def load_birthdays():
    try:
        with open("birthdays.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_birthdays(data):
    with open("birthdays.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def is_admin(member: discord.Member):
    return member.guild_permissions.administrator


def get_target_member(interaction: discord.Interaction, member: discord.Member | None):
    if member is None:
        return interaction.user

    if not is_admin(interaction.user):
        return None

    return member


@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    print(f"{bot.user} でログインしました！")
    print(f"{len(synced)}個のスラッシュコマンドを同期しました！")

    if not birthday_loop.is_running():
        birthday_loop.start()


@bot.tree.command(name="birthday_register", description="誕生日を登録します")
@app_commands.describe(month="誕生月", day="誕生日", member="管理者だけ指定できます")
async def birthday_register(
    interaction: discord.Interaction,
    month: int,
    day: int,
    member: discord.Member | None = None
):
    target = get_target_member(interaction, member)

    if target is None:
        await interaction.response.send_message("他の人の誕生日を登録できるのは管理者だけです。", ephemeral=True)
        return

    if month < 1 or month > 12:
        await interaction.response.send_message("月は1〜12で入力してね。", ephemeral=True)
        return

    if day < 1 or day > 31:
        await interaction.response.send_message("日は1〜31で入力してね。", ephemeral=True)
        return

    data = load_birthdays()
    user_id = str(target.id)

    data[user_id] = {
        "month": month,
        "day": day,
        "name": target.display_name
    }

    save_birthdays(data)

    await interaction.response.send_message(
        f"🎂 {target.mention} の誕生日を **{month}月{day}日** で登録したよ！",
        ephemeral=True
    )


@bot.tree.command(name="birthday_check", description="誕生日を確認します")
@app_commands.describe(member="管理者だけ指定できます")
async def birthday_check(
    interaction: discord.Interaction,
    member: discord.Member | None = None
):
    target = get_target_member(interaction, member)

    if target is None:
        await interaction.response.send_message("他の人の誕生日を確認できるのは管理者だけです。", ephemeral=True)
        return

    data = load_birthdays()
    user_id = str(target.id)

    if user_id not in data:
        await interaction.response.send_message("まだ誕生日が登録されてないよ。", ephemeral=True)
        return

    birthday = data[user_id]

    await interaction.response.send_message(
        f"{target.mention} の誕生日は **{birthday['month']}月{birthday['day']}日** だよ🎂",
        ephemeral=True
    )


@bot.tree.command(name="birthday_delete", description="誕生日登録を削除します")
@app_commands.describe(member="管理者だけ指定できます")
async def birthday_delete(
    interaction: discord.Interaction,
    member: discord.Member | None = None
):
    target = get_target_member(interaction, member)

    if target is None:
        await interaction.response.send_message("他の人の誕生日を削除できるのは管理者だけです。", ephemeral=True)
        return

    data = load_birthdays()
    user_id = str(target.id)

    if user_id not in data:
        await interaction.response.send_message("削除する誕生日が登録されてないよ。", ephemeral=True)
        return

    del data[user_id]
    save_birthdays(data)

    await interaction.response.send_message(
        f"{target.mention} の誕生日登録を削除したよ。",
        ephemeral=True
    )


@bot.tree.command(name="birthday_list", description="登録されている誕生日一覧を表示します")
async def birthday_list(interaction: discord.Interaction):
    data = load_birthdays()

    if not data:
        await interaction.response.send_message("まだ誰も登録していません。")
        return

    birthdays = []

    for user_id, user in data.items():
        birthdays.append((user["month"], user["day"], user["name"], user_id))

    birthdays.sort()

    text = "🎂 **誕生日一覧**\n\n"

    for month, day, name, user_id in birthdays:
        text += f"**{month}月{day}日**　<@{user_id}>（{name}）\n"

    await interaction.response.send_message(text)


@bot.tree.command(name="birthday_test", description="誕生日通知のテストをします")
async def birthday_test(interaction: discord.Interaction):
    channel = bot.get_channel(BIRTHDAY_CHANNEL_ID)

    if channel is None:
        await interaction.response.send_message("通知チャンネルが見つかりません。", ephemeral=True)
        return

    await channel.send(
        f"🎉🎂 テスト通知です！\n"
        f"{interaction.user.mention} さん、お誕生日おめでとうございます！！🎂🎉"
    )

    await interaction.response.send_message("テスト通知を送信しました！", ephemeral=True)


@tasks.loop(minutes=1)
async def birthday_loop():
    now = datetime.now()

    if now.hour != 0 or now.minute != 0:
        return

    channel = bot.get_channel(BIRTHDAY_CHANNEL_ID)
    if channel is None:
        return

    data = load_birthdays()

    for user_id, birthday in data.items():
        if birthday["month"] == now.month and birthday["day"] == now.day:
            await channel.send(
                f"🎉🎂 <@{user_id}> さん、お誕生日おめでとうございます！！🎂🎉"
            )


@birthday_loop.before_loop
async def before_birthday_loop():
    await bot.wait_until_ready()


bot.run(TOKEN)
import json
from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands


def load_data():
    try:
        with open("birthdays.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if "guilds" not in data:
                data = {"guilds": {}}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"guilds": {}}


def save_data(data):
    with open("birthdays.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_guild_data(data, guild_id):
    guild_id = str(guild_id)
    if guild_id not in data["guilds"]:
        data["guilds"][guild_id] = {}
    return data["guilds"][guild_id]


def valid_date(month, day):
    try:
        datetime(2024, month, day)
        return True
    except ValueError:
        return False


class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, interaction):
        return interaction.user.guild_permissions.administrator

    def get_target(self, interaction, member):
        if member is None:
            return interaction.user
        if not self.is_admin(interaction):
            return None
        return member

    @app_commands.command(name="birthday_register", description="誕生日を登録します")
    @app_commands.describe(month="月", day="日", member="管理者のみ指定できます")
    async def birthday_register(self, interaction: discord.Interaction, month: int, day: int, member: discord.Member | None = None):
        target = self.get_target(interaction, member)

        if target is None:
            await interaction.response.send_message("他の人の誕生日を登録できるのは管理者だけです。", ephemeral=True)
            return

        if not valid_date(month, day):
            await interaction.response.send_message("正しい日付を入力してね。", ephemeral=True)
            return

        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)

        guild_data[str(target.id)] = {
            "month": month,
            "day": day,
            "name": target.display_name
        }

        save_data(data)

        await interaction.response.send_message(
            f"🎂 {target.mention} の誕生日を **{month}月{day}日** で登録したよ！",
            ephemeral=True
        )

    @app_commands.command(name="birthday_check", description="誕生日を確認します")
    @app_commands.describe(member="管理者のみ指定できます")
    async def birthday_check(self, interaction: discord.Interaction, member: discord.Member | None = None):
        target = self.get_target(interaction, member)

        if target is None:
            await interaction.response.send_message("他の人の誕生日を確認できるのは管理者だけです。", ephemeral=True)
            return

        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)
        user_id = str(target.id)

        if user_id not in guild_data:
            await interaction.response.send_message("まだ誕生日が登録されていません。", ephemeral=True)
            return

        birthday = guild_data[user_id]

        await interaction.response.send_message(
            f"🎂 {target.mention} の誕生日は **{birthday['month']}月{birthday['day']}日** だよ！",
            ephemeral=True
        )

    @app_commands.command(name="birthday_edit", description="誕生日を変更します")
    @app_commands.describe(month="月", day="日", member="管理者のみ指定できます")
    async def birthday_edit(self, interaction: discord.Interaction, month: int, day: int, member: discord.Member | None = None):
        target = self.get_target(interaction, member)

        if target is None:
            await interaction.response.send_message("他の人の誕生日を変更できるのは管理者だけです。", ephemeral=True)
            return

        if not valid_date(month, day):
            await interaction.response.send_message("正しい日付を入力してね。", ephemeral=True)
            return

        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)
        user_id = str(target.id)

        if user_id not in guild_data:
            await interaction.response.send_message("まだ登録されていません。", ephemeral=True)
            return

        guild_data[user_id]["month"] = month
        guild_data[user_id]["day"] = day
        guild_data[user_id]["name"] = target.display_name

        save_data(data)

        await interaction.response.send_message(
            f"✏️ {target.mention} の誕生日を **{month}月{day}日** に変更したよ！",
            ephemeral=True
        )

    @app_commands.command(name="birthday_delete", description="誕生日を削除します")
    @app_commands.describe(member="管理者のみ指定できます")
    async def birthday_delete(self, interaction: discord.Interaction, member: discord.Member | None = None):
        target = self.get_target(interaction, member)

        if target is None:
            await interaction.response.send_message("他の人の誕生日を削除できるのは管理者だけです。", ephemeral=True)
            return

        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)
        user_id = str(target.id)

        if user_id not in guild_data:
            await interaction.response.send_message("登録されていません。", ephemeral=True)
            return

        del guild_data[user_id]
        save_data(data)

        await interaction.response.send_message(
            f"🗑️ {target.mention} の誕生日を削除したよ！",
            ephemeral=True
        )
    @app_commands.command(name="birthday_list", description="誕生日一覧を表示します")
    async def birthday_list(self, interaction: discord.Interaction):
        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)

        if not guild_data:
            await interaction.response.send_message("まだ誰も登録されていません。")
            return

        birthdays = []

        for user_id, birthday in guild_data.items():
            birthdays.append((birthday["month"], birthday["day"], user_id, birthday["name"]))

        birthdays.sort()

        text = "🎂 **誕生日一覧**\n\n"

        for month, day, user_id, name in birthdays:
            text += f"**{month}月{day}日**　<@{user_id}>（{name}）\n"

        await interaction.response.send_message(text)

    @app_commands.command(name="birthday_today", description="今日が誕生日の人を表示します")
    async def birthday_today(self, interaction: discord.Interaction):
        now = datetime.now()
        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)

        today = []

        for user_id, birthday in guild_data.items():
            if birthday["month"] == now.month and birthday["day"] == now.day:
                today.append(f"<@{user_id}>")

        if not today:
            await interaction.response.send_message("今日は誕生日の人はいません🎂")
            return

        await interaction.response.send_message("🎉 今日の誕生日 🎉\n\n" + "\n".join(today))

    @app_commands.command(name="birthday_month", description="今月の誕生日一覧を表示します")
    async def birthday_month(self, interaction: discord.Interaction):
        now = datetime.now()
        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)

        month_birthdays = []

        for user_id, birthday in guild_data.items():
            if birthday["month"] == now.month:
                month_birthdays.append((birthday["day"], user_id, birthday["name"]))

        if not month_birthdays:
            await interaction.response.send_message("今月の誕生日はありません🎂")
            return

        month_birthdays.sort()

        text = f"🎂 **{now.month}月の誕生日**\n\n"

        for day, user_id, name in month_birthdays:
            text += f"**{now.month}月{day}日**　<@{user_id}>（{name}）\n"

        await interaction.response.send_message(text)

    @app_commands.command(name="birthday_next", description="次の誕生日を表示します")
    async def birthday_next(self, interaction: discord.Interaction):
        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)

        if not guild_data:
            await interaction.response.send_message("まだ誰も登録されていません。")
            return

        now = datetime.now()
        next_person = None
        next_date = None

        for user_id, birthday in guild_data.items():
            birthday_date = datetime(now.year, birthday["month"], birthday["day"])

            if birthday_date < now:
                birthday_date = datetime(now.year + 1, birthday["month"], birthday["day"])

            if next_date is None or birthday_date < next_date:
                next_date = birthday_date
                next_person = (user_id, birthday)

        user_id, birthday = next_person

        await interaction.response.send_message(
            f"🎂 次の誕生日は <@{user_id}> さん！\n"
            f"📅 {birthday['month']}月{birthday['day']}日"
        )


async def setup(bot):
    await bot.add_cog(Birthday(bot))
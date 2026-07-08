import json
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands


def load_birthdays():
    try:
        with open("birthdays.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_birthdays(data):
    with open("birthdays.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def valid_date(month: int, day: int):
    if not (1 <= month <= 12):
        return False

    if not (1 <= day <= 31):
        return False

    try:
        datetime(2024, month, day)
        return True
    except ValueError:
        return False


class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, member: discord.Member):
        return member.guild_permissions.administrator

    def get_target(self, interaction: discord.Interaction, member: discord.Member | None):
        if member is None:
            return interaction.user

        if not self.is_admin(interaction.user):
            return None

        return member

    @app_commands.command(name="birthday_register", description="誕生日を登録します")
    @app_commands.describe(month="月", day="日", member="管理者のみ指定できます")
    async def birthday_register(
        self,
        interaction: discord.Interaction,
        month: int,
        day: int,
        member: discord.Member | None = None
    ):
        target = self.get_target(interaction, member)

        if target is None:
            await interaction.response.send_message("他の人の誕生日を登録できるのは管理者だけです。", ephemeral=True)
            return

        if not valid_date(month, day):
            await interaction.response.send_message("正しい日付を入力してね。", ephemeral=True)
            return

        data = load_birthdays()

        data[str(target.id)] = {
            "month": month,
            "day": day,
            "name": target.display_name
        }

        save_birthdays(data)

        await interaction.response.send_message(
            f"🎂 {target.mention} の誕生日を **{month}月{day}日** で登録したよ！",
            ephemeral=True
        )

    @app_commands.command(name="birthday_check", description="誕生日を確認します")
    @app_commands.describe(member="管理者のみ指定できます")
    async def birthday_check(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None
    ):
        target = self.get_target(interaction, member)

        if target is None:
            await interaction.response.send_message("他の人の誕生日を確認できるのは管理者だけです。", ephemeral=True)
            return

        data = load_birthdays()
        user_id = str(target.id)

        if user_id not in data:
            await interaction.response.send_message("まだ誕生日が登録されていません。", ephemeral=True)
            return

        birthday = data[user_id]

        await interaction.response.send_message(
            f"🎂 {target.mention} の誕生日は **{birthday['month']}月{birthday['day']}日** だよ！",
            ephemeral=True
        )
    @app_commands.command(name="birthday_edit", description="誕生日を変更します")
    @app_commands.describe(
        month="月",
        day="日",
        member="管理者のみ指定できます"
    )
    async def birthday_edit(
        self,
        interaction: discord.Interaction,
        month: int,
        day: int,
        member: discord.Member | None = None
    ):
        target = self.get_target(interaction, member)

        if target is None:
            await interaction.response.send_message(
                "他の人の誕生日は変更できません。",
                ephemeral=True
            )
            return

        if not valid_date(month, day):
            await interaction.response.send_message(
                "正しい日付を入力してください。",
                ephemeral=True
            )
            return

        data = load_birthdays()

        if str(target.id) not in data:
            await interaction.response.send_message(
                "まだ登録されていません。",
                ephemeral=True
            )
            return

        data[str(target.id)]["month"] = month
        data[str(target.id)]["day"] = day
        data[str(target.id)]["name"] = target.display_name

        save_birthdays(data)

        await interaction.response.send_message(
            f"✅ {target.mention} の誕生日を **{month}月{day}日** に変更しました！",
            ephemeral=True
        )

    @app_commands.command(name="birthday_delete", description="誕生日登録を削除します")
    @app_commands.describe(member="管理者のみ指定できます")
    async def birthday_delete(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None
    ):
        target = self.get_target(interaction, member)

        if target is None:
            await interaction.response.send_message(
                "他の人の誕生日は削除できません。",
                ephemeral=True
            )
            return

        data = load_birthdays()

        if str(target.id) not in data:
            await interaction.response.send_message(
                "登録されていません。",
                ephemeral=True
            )
            return

        del data[str(target.id)]
        save_birthdays(data)

        await interaction.response.send_message(
            f"🗑️ {target.mention} の誕生日を削除しました！",
            ephemeral=True
        )
        @app_commands.command(name="birthday_list", description="登録されている誕生日一覧を表示します")
        async def birthday_list(self, interaction: discord.Interaction):
            data = load_birthdays()

        if not data:
            await interaction.response.send_message(
                "まだ誰も登録されていません。"
            )
            return

        birthdays = []

        for user_id, birthday in data.items():
            birthdays.append(
                (
                    birthday["month"],
                    birthday["day"],
                    user_id,
                    birthday["name"]
                )
            )

        birthdays.sort()

        text = "🎂 **誕生日一覧**\n\n"

        for month, day, user_id, name in birthdays:
            text += f"**{month}月{day}日**　<@{user_id}>（{name}）\n"

        await interaction.response.send_message(text)

    @app_commands.command(name="birthday_today", description="今日が誕生日の人を表示します")
    async def birthday_today(self, interaction: discord.Interaction):
        now = datetime.now()

        data = load_birthdays()

        today = []

        for user_id, birthday in data.items():
            if birthday["month"] == now.month and birthday["day"] == now.day:
                today.append(f"<@{user_id}>")

        if not today:
            await interaction.response.send_message("今日は誕生日の人はいません🎂")
            return

        await interaction.response.send_message(
            "🎉 今日の誕生日 🎉\n\n" + "\n".join(today)
        )

    @app_commands.command(name="birthday_next", description="次に来る誕生日を表示します")
    async def birthday_next(self, interaction: discord.Interaction):
        data = load_birthdays()

        if not data:
            await interaction.response.send_message("まだ誰も登録されていません。")
            return

        now = datetime.now()

        next_person = None
        next_date = None

        for user_id, birthday in data.items():
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
    @app_commands.command(name="birthday_month", description="今月の誕生日一覧を表示します")
    async def birthday_month(self, interaction: discord.Interaction):
        data = load_birthdays()

        if not data:
            await interaction.response.send_message("まだ誰も登録されていません。")
            return

        now = datetime.now()
        month_birthdays = []

        for user_id, birthday in data.items():
            if birthday["month"] == now.month:
                month_birthdays.append(
                    (
                        birthday["day"],
                        user_id,
                        birthday["name"]
                    )
                )

        if not month_birthdays:
            await interaction.response.send_message("今月の誕生日はありません🎂")
            return

        month_birthdays.sort()

        text = f"🎂 **{now.month}月の誕生日**\n\n"

        for day, user_id, name in month_birthdays:
            text += f"**{now.month}月{day}日**　<@{user_id}>（{name}）\n"

        await interaction.response.send_message(text)


async def setup(bot):
    await bot.add_cog(Birthday(bot))
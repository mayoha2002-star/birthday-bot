import json
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands


OWNER_ID = 616286137341837314
DATA_FILE = "birthdays.json"


def load_data() -> dict:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"guilds": {}}

    if not isinstance(data, dict):
        return {"guilds": {}}

    guilds = data.get("guilds")
    if not isinstance(guilds, dict):
        data = {"guilds": {}}

    return data


def save_data(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def get_guild_data(data: dict, guild_id: int) -> dict:
    guilds = data.setdefault("guilds", {})
    return guilds.setdefault(str(guild_id), {})


def valid_date(month: int, day: int) -> bool:
    try:
        datetime(2024, month, day)
        return True
    except ValueError:
        return False


class Birthday(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_admin(self, interaction: discord.Interaction) -> bool:
        user = interaction.user
        return (
            user.id == OWNER_ID
            or (
                isinstance(user, discord.Member)
                and user.guild_permissions.administrator
            )
        )

    def get_target(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None,
    ) -> discord.Member | discord.User | None:
        if member is None:
            return interaction.user

        if not self.is_admin(interaction):
            return None

        return member

    async def require_guild(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is not None:
            return True

        await interaction.response.send_message(
            "このコマンドはサーバー内で使ってね。",
            ephemeral=True,
        )
        return False

    @app_commands.command(name="birthday_register", description="誕生日を登録します")
    @app_commands.describe(
        month="月",
        day="日",
        member="管理者またはBot所有者のみ指定できます",
    )
    async def birthday_register(
        self,
        interaction: discord.Interaction,
        month: int,
        day: int,
        member: discord.Member | None = None,
    ) -> None:
        if not await self.require_guild(interaction):
            return

        target = self.get_target(interaction, member)
        if target is None:
            await interaction.response.send_message(
                "他の人の誕生日を登録できるのは管理者だけです。",
                ephemeral=True,
            )
            return

        if not valid_date(month, day):
            await interaction.response.send_message(
                "正しい日付を入力してね。",
                ephemeral=True,
            )
            return

        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)
        guild_data[str(target.id)] = {
            "month": month,
            "day": day,
            "name": target.display_name,
        }
        save_data(data)

        await interaction.response.send_message(
            f"🎂 {target.mention} の誕生日を **{month}月{day}日** で登録したよ！",
            ephemeral=True,
        )

    @app_commands.command(name="birthday_check", description="誕生日を確認します")
    @app_commands.describe(member="管理者またはBot所有者のみ指定できます")
    async def birthday_check(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None,
    ) -> None:
        if not await self.require_guild(interaction):
            return

        target = self.get_target(interaction, member)
        if target is None:
            await interaction.response.send_message(
                "他の人の誕生日を確認できるのは管理者だけです。",
                ephemeral=True,
            )
            return

        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)
        birthday = guild_data.get(str(target.id))

        if birthday is None:
            await interaction.response.send_message(
                "まだ誕生日が登録されていません。",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"🎂 {target.mention} の誕生日は "
            f"**{birthday['month']}月{birthday['day']}日** だよ！",
            ephemeral=True,
        )

    @app_commands.command(name="birthday_edit", description="誕生日を変更します")
    @app_commands.describe(
        month="月",
        day="日",
        member="管理者またはBot所有者のみ指定できます",
    )
    async def birthday_edit(
        self,
        interaction: discord.Interaction,
        month: int,
        day: int,
        member: discord.Member | None = None,
    ) -> None:
        if not await self.require_guild(interaction):
            return

        target = self.get_target(interaction, member)
        if target is None:
            await interaction.response.send_message(
                "他の人の誕生日を変更できるのは管理者だけです。",
                ephemeral=True,
            )
            return

        if not valid_date(month, day):
            await interaction.response.send_message(
                "正しい日付を入力してね。",
                ephemeral=True,
            )
            return

        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)
        user_id = str(target.id)

        if user_id not in guild_data:
            await interaction.response.send_message(
                "まだ登録されていません。先に `/birthday_register` を使ってね。",
                ephemeral=True,
            )
            return

        guild_data[user_id] = {
            "month": month,
            "day": day,
            "name": target.display_name,
        }
        save_data(data)

        await interaction.response.send_message(
            f"✏️ {target.mention} の誕生日を "
            f"**{month}月{day}日** に変更したよ！",
            ephemeral=True,
        )

    @app_commands.command(name="birthday_delete", description="誕生日を削除します")
    @app_commands.describe(member="管理者またはBot所有者のみ指定できます")
    async def birthday_delete(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None,
    ) -> None:
        if not await self.require_guild(interaction):
            return

        target = self.get_target(interaction, member)
        if target is None:
            await interaction.response.send_message(
                "他の人の誕生日を削除できるのは管理者だけです。",
                ephemeral=True,
            )
            return

        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)
        user_id = str(target.id)

        if user_id not in guild_data:
            await interaction.response.send_message(
                "登録されていません。",
                ephemeral=True,
            )
            return

        del guild_data[user_id]
        save_data(data)

        await interaction.response.send_message(
            f"🗑️ {target.mention} の誕生日を削除したよ！",
            ephemeral=True,
        )

    @app_commands.command(name="birthday_list", description="誕生日一覧を表示します")
    async def birthday_list(self, interaction: discord.Interaction) -> None:
        if not await self.require_guild(interaction):
            return

        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)

        if not guild_data:
            await interaction.response.send_message("まだ誰も登録されていません。")
            return

        birthdays = sorted(
            (
                birthday["month"],
                birthday["day"],
                user_id,
                birthday.get("name", "名前不明"),
            )
            for user_id, birthday in guild_data.items()
        )

        lines = ["🎂 **誕生日一覧**", ""]
        for month, day, user_id, name in birthdays:
            lines.append(f"**{month}月{day}日**　<@{user_id}>（{name}）")

        await interaction.response.send_message("\n".join(lines))

    @app_commands.command(name="birthday_today", description="今日が誕生日の人を表示します")
    async def birthday_today(self, interaction: discord.Interaction) -> None:
        if not await self.require_guild(interaction):
            return

        now = datetime.now()
        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)

        today = [
            f"<@{user_id}>"
            for user_id, birthday in guild_data.items()
            if birthday["month"] == now.month and birthday["day"] == now.day
        ]

        if not today:
            await interaction.response.send_message("今日は誕生日の人はいません🎂")
            return

        await interaction.response.send_message(
            "🎉 **今日の誕生日** 🎉\n\n" + "\n".join(today)
        )

    @app_commands.command(name="birthday_month", description="今月の誕生日一覧を表示します")
    async def birthday_month(self, interaction: discord.Interaction) -> None:
        if not await self.require_guild(interaction):
            return

        now = datetime.now()
        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)

        month_birthdays = sorted(
            (
                birthday["day"],
                user_id,
                birthday.get("name", "名前不明"),
            )
            for user_id, birthday in guild_data.items()
            if birthday["month"] == now.month
        )

        if not month_birthdays:
            await interaction.response.send_message("今月の誕生日はありません🎂")
            return

        lines = [f"🎂 **{now.month}月の誕生日**", ""]
        for day, user_id, name in month_birthdays:
            lines.append(f"**{now.month}月{day}日**　<@{user_id}>（{name}）")

        await interaction.response.send_message("\n".join(lines))

    @app_commands.command(name="birthday_next", description="次の誕生日を表示します")
    async def birthday_next(self, interaction: discord.Interaction) -> None:
        if not await self.require_guild(interaction):
            return

        data = load_data()
        guild_data = get_guild_data(data, interaction.guild.id)

        if not guild_data:
            await interaction.response.send_message("まだ誰も登録されていません。")
            return

        now = datetime.now()
        candidates = []

        for user_id, birthday in guild_data.items():
            birthday_date = datetime(now.year, birthday["month"], birthday["day"])
            if birthday_date.date() < now.date():
                birthday_date = datetime(
                    now.year + 1,
                    birthday["month"],
                    birthday["day"],
                )

            candidates.append((birthday_date, user_id, birthday))

        next_date, user_id, birthday = min(candidates, key=lambda item: item[0])
        days_left = (next_date.date() - now.date()).days

        await interaction.response.send_message(
            f"🎂 次の誕生日は <@{user_id}> さん！\n"
            f"📅 {birthday['month']}月{birthday['day']}日"
            f"（あと{days_left}日）"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Birthday(bot))

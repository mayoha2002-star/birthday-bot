import json
from datetime import datetime
from zoneinfo import ZoneInfo

from discord.ext import commands, tasks


JJST = ZoneInfo("Asia/Tokyo")
BIRTHDAYS_FILE = "/app/data/birthdays.json"


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


class BirthdayTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_processed_date = {}
        self.birthday_loop.start()

    def cog_unload(self):
        self.birthday_loop.cancel()

    @tasks.loop(minutes=1)
    async def birthday_loop(self):
        now = datetime.now(JST)
        today_key = now.strftime("%Y-%m-%d")

        birthday_data = load_json("birthdays.json", {"guilds": {}})
        settings = load_json("settings.json", {"guilds": {}})

        all_guild_birthdays = birthday_data.get("guilds", {})
        all_guild_settings = settings.get("guilds", {})

        for guild in self.bot.guilds:
            guild_id = str(guild.id)

            # 今日すでにこのサーバーで処理済みなら何もしない
            if self.last_processed_date.get(guild_id) == today_key:
                continue

            guild_setting = all_guild_settings.get(guild_id, {})
            channel_id = guild_setting.get("birthday_channel_id")

            if channel_id is None:
                continue

            channel = guild.get_channel(channel_id)

            if channel is None:
                continue

            guild_birthdays = all_guild_birthdays.get(guild_id, {})
            birthday_mentions = []

            for user_id, birthday in guild_birthdays.items():
                if (
                    birthday.get("month") == now.month
                    and birthday.get("day") == now.day
                ):
                    member = guild.get_member(int(user_id))

                    if member is not None:
                        birthday_mentions.append(member.mention)

            if birthday_mentions:
                mentions = "\n".join(birthday_mentions)

                await channel.send(
                    "🎉🎂 **Happy Birthday!!** 🎂🎉\n\n"
                    f"{mentions}\n\n"
                    "お誕生日おめでとうございます！！\n"
                    "素敵な一年になりますように🥳✨"
                )

            # 誕生日の人がいない日も処理済みにする
            self.last_processed_date[guild_id] = today_key

    @birthday_loop.before_loop
    async def before_birthday_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(BirthdayTasks(bot))
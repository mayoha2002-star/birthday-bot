import json
from datetime import datetime
from zoneinfo import ZoneInfo

from discord.ext import commands, tasks


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


class BirthdayTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthday_loop.start()

    def cog_unload(self):
        self.birthday_loop.cancel()

    @tasks.loop(minutes=1)
    async def birthday_loop(self):
        now = datetime.now(ZoneInfo("Asia/Tokyo"))

        if now.hour != 0 or now.minute != 0:
            return

        birthdays = load_json("birthdays.json", {})
        settings = load_json("settings.json", {})

        guilds = settings.get("guilds", {})

        for guild in self.bot.guilds:
            guild_setting = guilds.get(str(guild.id))

            if guild_setting is None:
                continue

            channel = guild.get_channel(guild_setting["birthday_channel_id"])

            if channel is None:
                continue

            for user_id, birthday in birthdays.items():
                if (
                    birthday["month"] == now.month
                    and birthday["day"] == now.day
                ):
                    member = guild.get_member(int(user_id))

                    if member:
                        await channel.send(
                            f"🎉🎂 {member.mention} さん、お誕生日おめでとうございます！！ 🎂🎉"
                        )

    @birthday_loop.before_loop
    async def before_birthday_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(BirthdayTasks(bot))
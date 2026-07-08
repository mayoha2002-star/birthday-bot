import json
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks


JST = ZoneInfo("Asia/Tokyo")
ROLE_NAME = "🎂誕生日"


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class BirthdayTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthday_loop.start()

    def cog_unload(self):
        self.birthday_loop.cancel()

    @tasks.loop(minutes=1)
    async def birthday_loop(self):
        now = datetime.now(JST)

        if now.hour != 0 or now.minute != 0:
            return

        settings = load_json("settings.json", {})
        birthdays = load_json("birthdays.json", {})
        state = load_json("birthday_state.json", {})

        today_key = now.strftime("%Y-%m-%d")

        if state.get("last_run_date") == today_key:
            return

        channel_id = settings.get("birthday_channel_id")
        channel = self.bot.get_channel(channel_id)

        if channel is None:
            return

        guild = channel.guild
        active = state.get("active", {})

        for user_id, info in active.items():
            member = guild.get_member(int(user_id))
            if member is None:
                continue

            role_id = info.get("role_id")
            role = guild.get_role(role_id) if role_id else None

            if role and role in member.roles:
                try:
                    await member.remove_roles(role, reason="誕生日終了")
                except discord.Forbidden:
                    pass

            old_nick = info.get("old_nick")

            try:
                await member.edit(nick=old_nick, reason="誕生日終了")
            except discord.Forbidden:
                pass

        state["active"] = {}

        role = discord.utils.get(guild.roles, name=ROLE_NAME)

        today_members = []

        for user_id, birthday in birthdays.items():
            if birthday["month"] == now.month and birthday["day"] == now.day:
                member = guild.get_member(int(user_id))

                if member is None:
                    continue

                today_members.append(member)

                if role:
                    try:
                        await member.add_roles(role, reason="誕生日")
                    except discord.Forbidden:
                        pass

                old_nick = member.nick

                if not member.display_name.startswith("🎂"):
                    try:
                        await member.edit(
                            nick=f"🎂 {member.display_name}",
                            reason="誕生日"
                        )
                    except discord.Forbidden:
                        pass

                state["active"][str(member.id)] = {
                    "role_id": role.id if role else None,
                    "old_nick": old_nick
                }

        if today_members:
            mentions = "\n".join(member.mention for member in today_members)

            await channel.send(
                "🎉🎂 **Happy Birthday!!** 🎂🎉\n\n"
                f"{mentions}\n\n"
                "お誕生日おめでとうございます！！\n"
                "素敵な一年になりますように🥳✨"
            )

        state["last_run_date"] = today_key
        save_json("birthday_state.json", state)

    @birthday_loop.before_loop
    async def before_birthday_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(BirthdayTasks(bot))
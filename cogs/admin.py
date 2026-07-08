import json
import discord
from discord import app_commands
from discord.ext import commands


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, interaction):
        return interaction.user.guild_permissions.administrator

    @app_commands.command(name="birthday_set_channel", description="このサーバーの誕生日通知チャンネルを設定します")
    @app_commands.describe(channel="通知するチャンネル")
    async def birthday_set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not self.is_admin(interaction):
            await interaction.response.send_message("管理者だけ使えます。", ephemeral=True)
            return

        settings = load_json("settings.json", {})
        guild_id = str(interaction.guild.id)

        if "guilds" not in settings:
            settings["guilds"] = {}

        settings["guilds"][guild_id] = {
            "birthday_channel_id": channel.id
        }

        save_json("settings.json", settings)

        await interaction.response.send_message(
            f"このサーバーの通知チャンネルを {channel.mention} に設定したよ！",
            ephemeral=True
        )

    @app_commands.command(name="birthday_test", description="誕生日通知のテストをします")
    async def birthday_test(self, interaction: discord.Interaction):
        if not self.is_admin(interaction):
            await interaction.response.send_message("管理者だけ使えます。", ephemeral=True)
            return

        settings = load_json("settings.json", {})
        guild_id = str(interaction.guild.id)

        channel_id = settings.get("guilds", {}).get(guild_id, {}).get("birthday_channel_id")

        if channel_id is None:
            await interaction.response.send_message(
                "先に /birthday_set_channel で通知チャンネルを設定してね。",
                ephemeral=True
            )
            return

        channel = self.bot.get_channel(channel_id)

        if channel is None:
            await interaction.response.send_message("通知チャンネルが見つかりません。", ephemeral=True)
            return

        await channel.send(
            "🎉🎂 **Happy Birthday!!** 🎂🎉\n\n"
            f"{interaction.user.mention}\n\n"
            "テスト通知です！"
        )

        await interaction.response.send_message("テスト通知を送ったよ！", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Admin(bot))
import json
import os
import discord
from discord.ext import commands

try:
    TOKEN = os.environ["DISCORD_TOKEN"]
except KeyError:
    with open("config.json", "r", encoding="utf-8") as f:
        TOKEN = json.load(f)["token"]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user} でログインしました！")

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

    synced = await bot.tree.sync()
    print(f"{len(synced)}個のスラッシュコマンドを同期しました！")


bot.run(TOKEN)
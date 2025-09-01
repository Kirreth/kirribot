import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from utils import database as db

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot ist online als {bot.user}")
    # Lade Cogs
    for cog in ["cogs.leveling", "cogs.info", "cogs.moderation", "cogs.quote", "cogs.bumps"]:
        try:
            await bot.load_extension(cog)
            print(f"✅ Cog geladen: {cog}")
        except Exception as e:
            print(f"❌ Fehler beim Laden von {cog}: {e}")

# Datenbank aufsetzen
db.setup_database()

bot.run(TOKEN)

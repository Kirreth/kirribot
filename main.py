import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils import database as db
from typing import List

# .env laden
load_dotenv()
TOKEN: str | None = os.getenv("TOKEN")

intents: discord.Intents = discord.Intents.all()
bot: commands.Bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready() -> None:
    """Wird aufgerufen, wenn der Bot erfolgreich gestartet ist."""
    print(f"Bot ist online als {bot.user}")

    cogs: List[str] = [
        "cogs.leveling",
        "cogs.info",
        "cogs.moderation",
        "cogs.quote",
        "cogs.bumps",
    ]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Cog geladen: {cog}")
        except Exception as e:
            print(f"❌ Fehler beim Laden von {cog}: {e}")

db.setup_database()

if TOKEN:
    bot.run(TOKEN)
else:
    raise ValueError("❌ Kein TOKEN in .env gefunden")

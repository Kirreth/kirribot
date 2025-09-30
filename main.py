import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils import database as db
from typing import List, Optional

load_dotenv()
TOKEN: Optional[str] = os.getenv("TOKEN")  

intents: discord.Intents = discord.Intents.all()

bot: commands.Bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None  
)


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
        "cogs.help",
        "cogs.roles",
        "cogs.activitytracker"
    ]

    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Cog geladen: {cog}")
        except Exception as e:
            print(f"❌ Fehler beim Laden von {cog}: {e}")

    await bot.tree.sync()

    db.setup_database()

if TOKEN:
    bot.run(TOKEN)
else:
    raise ValueError("❌ Kein TOKEN in .env gefunden")

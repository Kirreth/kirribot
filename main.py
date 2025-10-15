import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.database import setup_database
from typing import List, Optional

load_dotenv()
TOKEN: Optional[str] = os.getenv("TOKEN")

intents: discord.Intents = discord.Intents.all()

bot: commands.Bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

setup_database()


@bot.event
async def on_ready() -> None:
    print(f"Bot ist online als {bot.user}")

    cogs: List[str] = [
        "cogs.leveling",
        "cogs.info",
        "cogs.moderation",
        "cogs.bumps",
        "cogs.help",
        "cogs.roles",
        "cogs.activitytracker",
        "cogs.joinleft",
        "cogs.birthday",
        "cogs.quiz"
    ]

    # ------------------------------------------------------------
    # Cogs laden
    # ------------------------------------------------------------
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Cog geladen: {cog}")
        except Exception as e:
            print(f"❌ Fehler beim Laden von {cog}: {e}")

    # ------------------------------------------------------------
    # Slash-/Hybrid-Commands synchronisieren
    # ------------------------------------------------------------
    synced = await bot.tree.sync()
    print(f"🔄 {len(synced)} Befehle erfolgreich synchronisiert.")

    print("✅ Alle Cogs geladen und Commands synchronisiert.")


if TOKEN:
    bot.run(TOKEN)
else:
    raise ValueError("❌ Kein TOKEN in .env gefunden")

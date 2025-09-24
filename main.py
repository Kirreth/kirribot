import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils import database as db
from typing import List, Optional

# .env laden
load_dotenv()
TOKEN: Optional[str] = os.getenv("TOKEN")  # Sicherstellen, dass der Typ korrekt ist

# Discord Intents konfigurieren
intents: discord.Intents = discord.Intents.all()

# Bot-Initialisierung
bot: commands.Bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None  # <- Standard-HelpCommand deaktivieren
)


@bot.event
async def on_ready() -> None:
    """Wird aufgerufen, wenn der Bot erfolgreich gestartet ist."""
    print(f"Bot ist online als {bot.user}")

    # Liste der Cogs, die geladen werden sollen
    cogs: List[str] = [
        "cogs.leveling",
        "cogs.info",
        "cogs.moderation",
        "cogs.quote",
        "cogs.bumps",
        "cogs.help"
    ]

    # Laden der Cogs
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Cog geladen: {cog}")
        except Exception as e:
            print(f"❌ Fehler beim Laden von {cog}: {e}")

    # Slash-Befehle synchronisieren
    await bot.tree.sync()

    # Setup der Datenbank (falls noch nicht geschehen)
    db.setup_database()

if TOKEN:
    # Starte den Bot mit dem Token aus der .env-Datei
    bot.run(TOKEN)
else:
    raise ValueError("❌ Kein TOKEN in .env gefunden")

import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.database import setup_database
from typing import List, Optional
import time
import mysql.connector
import watchgod

load_dotenv()
TOKEN: Optional[str] = os.getenv("TOKEN")

intents: discord.Intents = discord.Intents.all()
bot: commands.Bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# ------------------------------------------------------------
# Funktion: auf MySQL warten
# ------------------------------------------------------------
def wait_for_mysql(host: str, port: int, user: str, password: str, database: str, retries: int = 10, delay: int = 3):
    for attempt in range(1, retries + 1):
        try:
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            conn.close()
            print(f"✅ MySQL ist erreichbar (Versuch {attempt})")
            return
        except mysql.connector.Error:
            print(f"⏳ MySQL nicht erreichbar, warte {delay}s... (Versuch {attempt})")
            time.sleep(delay)
    raise RuntimeError("❌ MySQL konnte nach mehreren Versuchen nicht erreicht werden.")

wait_for_mysql(
    host=os.getenv("DB_HOST", "mysql_db"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER", "pythonbot"),
    password=os.getenv("DB_PASS", ""),
    database=os.getenv("DB_NAME", "kirribot")
)

# Datenbank initialisieren
setup_database()

# ------------------------------------------------------------
# Async-Funktion für Bot-Start
# ------------------------------------------------------------
async def run_bot():
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
            "cogs.quiz",
            "cogs.selfinfo",
            "cogs.metafrage",
            "cogs.partyquiz",
            "cogs.codeextractor"
        ]

        for cog in cogs:
            try:
                await bot.load_extension(cog)
                print(f"✅ Cog geladen: {cog}")
            except Exception as e:
                print(f"❌ Fehler beim Laden von {cog}: {e}")

        synced = await bot.tree.sync()
        print(f"🔄 {len(synced)} Befehle erfolgreich synchronisiert.")
        print("✅ Alle Cogs geladen und Commands synchronisiert.")

    if TOKEN:
        await bot.start(TOKEN)
    else:
        raise ValueError("❌ Kein TOKEN in .env gefunden")

# ------------------------------------------------------------
# Funktion für Watchgod (muss "picklable" sein)
# ------------------------------------------------------------
def start_bot_process():
    asyncio.run(run_bot())

# ------------------------------------------------------------
# Hot-Reload mit Watchgod
# ------------------------------------------------------------
if __name__ == "__main__":
    try:
        import watchgod
    except ImportError:
        print("⚠️ Watchgod nicht installiert. Bitte pip install watchgod")
        asyncio.run(run_bot())
    else:
        # Jetzt keine Lambda mehr, sondern richtige Funktion
        watchgod.run_process(".", start_bot_process)

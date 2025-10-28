import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.database import setup_database
from typing import List, Optional
import time
import mysql.connector
import logging
import watchgod

# ------------------------------------------------------------
# Logging konfigurieren
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Env & Token laden
# ------------------------------------------------------------
load_dotenv()
TOKEN: Optional[str] = os.getenv("TOKEN")

# ------------------------------------------------------------
# Discord Bot initialisieren
# ------------------------------------------------------------
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
            logger.info(f"✅ MySQL ist erreichbar (Versuch {attempt})")
            return
        except mysql.connector.Error:
            logger.warning(f"⏳ MySQL nicht erreichbar, warte {delay}s... (Versuch {attempt})")
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
        logger.info(f"Bot ist online als {bot.user}")

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
            "cogs.codeextractor",
            "cogs.fakt",
            "cogs.setup"
        ]

        for cog in cogs:
            try:
                await bot.load_extension(cog)
                logger.info(f"✅ Cog geladen: {cog}")
            except Exception as e:
                logger.error(f"❌ Fehler beim Laden von {cog}: {e}", exc_info=True)

        synced = await bot.tree.sync()
        logger.info(f"🔄 {len(synced)} Befehle erfolgreich synchronisiert.")
        logger.info("✅ Alle Cogs geladen und Commands synchronisiert.")

    if TOKEN:
        await bot.start(TOKEN)
    else:
        raise ValueError("❌ Kein TOKEN in .env gefunden")

# ------------------------------------------------------------
# Funktion für Watchgod (muss picklable sein)
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
        logger.warning("⚠️ Watchgod nicht installiert. Bitte pip install watchgod")
        asyncio.run(run_bot())
    else:
        watchgod.run_process(".", start_bot_process)
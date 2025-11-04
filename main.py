import os
import asyncio
import discord
from discord.ext import commands, tasks 
from dotenv import load_dotenv
from utils.database import setup_database
from utils.database import guilds as db_guilds 
from typing import List, Optional
import time
import mysql.connector
import logging
import watchgod
from datetime import datetime, timedelta 

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
# Funktion: Server-spezifisches Präfix abrufen
# ------------------------------------------------------------
async def get_prefix(bot: commands.Bot, message: discord.Message) -> List[str]:
    """Ruft das Präfix für die Gilde ab oder verwendet den Standard."""
    default_prefix = "!" # Der Fallback, falls DB fehlschlägt oder DM
    
    # Für DMs oder wenn die Gilde nicht existiert
    if not message.guild:
        return [default_prefix]
    
    # Präfix aus der zentralen DB abrufen
    guild_id = str(message.guild.id)
    prefix = db_guilds.get_prefix(guild_id) 
    
    return [prefix, default_prefix] if prefix else [default_prefix]


# ------------------------------------------------------------
# Discord Bot initialisieren
# ------------------------------------------------------------
intents: discord.Intents = discord.Intents.all()
bot: commands.Bot = commands.Bot(
    command_prefix=get_prefix, 
    intents=intents,
    help_command=None
)

ADVENTSKALENDER_COG = "cogs.adventskalender"


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
# Tägliche Überprüfung der Advent-Periode (Loop)
# ------------------------------------------------------------
"""
@tasks.loop(hours=24) 
async def check_advent_cog():
    current_month = datetime.now().month
    
    if current_month == 12:
        if ADVENTSKALENDER_COG not in bot.extensions:
            try:
                await bot.load_extension(ADVENTSKALENDER_COG)
                logger.info(f"✅ HINTERGRUND: {ADVENTSKALENDER_COG} wurde geladen (Dezember-Start).")
            except Exception as e:
                logger.error(f"❌ HINTERGRUND: Fehler beim Laden von {ADVENTSKALENDER_COG}: {e}", exc_info=True)
                
    elif current_month == 1:
        if ADVENTSKALENDER_COG in bot.extensions:
            try:
                await bot.unload_extension(ADVENTSKALENDER_COG)
                logger.info(f"✅ HINTERGRUND: {ADVENTSKALENDER_COG} wurde entladen (Januar-Start).")
            except Exception as e:
                logger.error(f"❌ HINTERGRUND: Fehler beim Entladen von {ADVENTSKALENDER_COG}: {e}", exc_info=True)

async def check_advent_cog_start_delay():
    now = datetime.now()
    next_run = now.replace(hour=0, minute=1, second=0, microsecond=0)
    
    if now > next_run:
        next_run += timedelta(days=1)
        
    delta = (next_run - now).total_seconds()
    
    logger.info(f"⌛ Starte Advent-Check-Loop in {delta:.0f} Sekunden (nächster Lauf: {next_run.strftime('%Y-%m-%d %H:%M:%S')}).")
    
    await asyncio.sleep(delta)
    check_advent_cog.start()
"""
# ------------------------------------------------------------
# Async-Funktion für Bot-Start
# ------------------------------------------------------------
async def run_bot():
    @bot.event
    async def on_ready() -> None:
        logger.info(f"Bot ist online als {bot.user}")

        cogs_to_load = []

        # Standard-Cogs
        cogs_to_load.extend([
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
            "cogs.setup",
            "cogs.dynamicvoice",
            "cogs.musicconverter"
        ])
        
        # Lade alle Cogs
        for cog in cogs_to_load:
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
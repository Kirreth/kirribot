import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.database import setup_database, guilds as db_guilds
import mysql.connector
import logging
from dashboard import create_dashboard
from uvicorn import Config, Server

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Env & Token
# ------------------------------------------------------------
load_dotenv()
TOKEN = os.getenv("TOKEN")

# ------------------------------------------------------------
# Funktion: Serverpräfix
# ------------------------------------------------------------
async def get_prefix(bot: commands.Bot, message: discord.Message):
    default_prefix = "!"
    if not message.guild:
        return [default_prefix]
    prefix = db_guilds.get_prefix(str(message.guild.id))
    return [prefix, default_prefix] if prefix else [default_prefix]

# ------------------------------------------------------------
# Discord Bot initialisieren
# ------------------------------------------------------------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# ------------------------------------------------------------
# MySQL warten
# ------------------------------------------------------------
def wait_for_mysql():
    import time
    retries = 10
    for attempt in range(1, retries + 1):
        try:
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT", 3306)),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASS"),
                database=os.getenv("DB_NAME")
            )
            conn.close()
            logger.info(f"MySQL erreichbar (Versuch {attempt})")
            return
        except mysql.connector.Error:
            logger.warning(f"MySQL nicht erreichbar, warte 3s (Versuch {attempt})")
            time.sleep(3)
    raise RuntimeError("MySQL nicht erreichbar nach mehreren Versuchen.")

wait_for_mysql()
setup_database()

# ------------------------------------------------------------
# Bot starten
# ------------------------------------------------------------
async def run_bot():
    @bot.event
    async def on_ready():
        logger.info(f"Bot online als {bot.user}")

        # Alle Cogs laden
        cogs = [
            "cogs.leveling",
            "cogs.info",
            "cogs.moderation",
            "cogs.birthday",
            "cogs.setup",
            "cogs.dynamicvoice",
            "cogs.musicconverter",
            "cogs.bumps",
            "cogs.roles",
            "cogs.activitytracker",
            "cogs.joinleft",
            "cogs.quiz",
            "cogs.selfinfo",
            "cogs.metafrage",
            "cogs.partyquiz",
            "cogs.codeextractor",
            "cogs.fakt",
            "cogs.help",
            "cogs.weather"
        ]
        for cog in cogs:
            try:
                await bot.load_extension(cog)
                logger.info(f"✅ Cog geladen: {cog}")
            except Exception as e:
                logger.error(f"❌ Fehler beim Laden: {cog} -> {e}", exc_info=True)

        synced = await bot.tree.sync()
        logger.info(f"🔄 {len(synced)} Commands synchronisiert")

    if TOKEN:
        await bot.start(TOKEN)
    else:
        raise ValueError("Kein TOKEN in .env gefunden")

# ------------------------------------------------------------
# Dashboard erstellen
# ------------------------------------------------------------
dashboard_app = create_dashboard(bot)

# ------------------------------------------------------------
# Bot + Dashboard parallel starten
# ------------------------------------------------------------
async def main():
    bot_task = asyncio.create_task(run_bot())

    config = Config(
        dashboard_app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        loop="asyncio"
    )
    server = Server(config)
    api_task = asyncio.create_task(server.serve())

    await asyncio.gather(bot_task, api_task)

if __name__ == "__main__":
    asyncio.run(main())

import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.database import setup_database, guilds as db_guilds
import mysql.connector
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from typing import List

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
# Setzt den Logger auf INFO-Level und ein sauberes Format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Load environment
# ------------------------------------------------------------
load_dotenv()
TOKEN = os.getenv("TOKEN")
BOT_API_HOST = os.getenv("BOT_API_HOST", "0.0.0.0")
BOT_API_PORT = int(os.getenv("BOT_API_PORT", 8001))

# ------------------------------------------------------------
# Discord Bot Initialisierung
# ------------------------------------------------------------
async def get_prefix(bot: commands.Bot, message: discord.Message) -> List[str]:
    """Holt den Gilden-spezifischen Präfix oder nutzt den Standard."""
    default_prefix = "!"
    if not message.guild:
        return [default_prefix]
    
    # Annahme: db_guilds.get_prefix kann None zurückgeben
    try:
        prefix = db_guilds.get_prefix(str(message.guild.id))
        return [prefix, default_prefix] if prefix else [default_prefix]
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Präfixes: {e}")
        return [default_prefix]

# Intents setzen: Alle Intents sind für die Hybrid Commands und Leveling notwendig
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# Definiert die Liste aller Cogs
COGS = [
    "cogs.leveling", "cogs.info", "cogs.moderation", "cogs.birthday", "cogs.setup", 
    "cogs.dynamicvoice", "cogs.musicconverter", "cogs.bumps", "cogs.roles", 
    "cogs.activitytracker", "cogs.joinleft", "cogs.quiz", "cogs.selfinfo", 
    "cogs.metafrage", "cogs.partyquiz", "cogs.codeextractor", "cogs.fakt", 
    "cogs.help", "cogs.weather", "cogs.customcommands", "cogs.docu_search", 
    "cogs.userposts", "cogs.about", "cogs.counter", "cogs.antispam"
]

# ------------------------------------------------------------
# Interne API für Bot-Daten (FastAPI)
# ------------------------------------------------------------
internal_api = FastAPI(title="Bot Internal Guild API")

@internal_api.get("/api/guilds")
async def get_bot_guild_ids():
    """Gibt eine Liste aller Gilden-IDs des Bots zurück."""
    if not bot.is_ready():
        return {"guild_ids": []}
    return {"guild_ids": [str(g.id) for g in bot.guilds]}

@internal_api.get("/api/guild/{guild_id}")
async def get_bot_guild_details(guild_id: str):
    """Gibt Details zu einer spezifischen Gilde zurück."""
    if not bot.is_ready():
        raise HTTPException(status_code=503, detail="Bot ist noch nicht bereit.")
    
    guild = bot.get_guild(int(guild_id))
    if not guild:
        raise HTTPException(status_code=404, detail="Gilde nicht gefunden")

    return {
        "id": str(guild.id),
        "name": guild.name,
        "icon": str(guild.icon.url) if guild.icon else None,
        "owner_id": str(guild.owner_id),
        # Filtern für Text- und Voice-Channels ist hier optional, aber beibehalten
        "text_channels": [{"id": str(c.id), "name": c.name} for c in guild.text_channels],
        "voice_channels": [{"id": str(c.id), "name": c.name} for c in guild.voice_channels],
        # Rollen-Filterung beibehalten
        "roles": [{"id": str(r.id), "name": r.name} for r in guild.roles if not r.managed and r.name != "@everyone"],
    }

async def start_internal_api_background():
    """Startet den Uvicorn-Server für die interne API."""
    config = uvicorn.Config(
        internal_api,
        host=BOT_API_HOST,
        port=BOT_API_PORT,
        log_level="warning", # Reduziert API-Output, um Discord-Logs sauber zu halten
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    await server.serve()

# ------------------------------------------------------------
# MySQL-Prüfung
# ------------------------------------------------------------
def wait_for_mysql():
    """Wartet, bis die MySQL-Datenbank erreichbar ist."""
    import time
    retries = 10
    db_host = os.getenv("DB_HOST")
    db_port = int(os.getenv("DB_PORT", 3306))
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_name = os.getenv("DB_NAME")
    
    for attempt in range(1, retries + 1):
        try:
            conn = mysql.connector.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_pass,
                database=db_name
            )
            conn.close()
            logger.info(f"MySQL erreichbar (Versuch {attempt})")
            return
        except mysql.connector.Error:
            logger.warning(f"MySQL nicht erreichbar, warte 3s (Versuch {attempt})")
            time.sleep(3)
    raise RuntimeError("MySQL nach mehreren Versuchen nicht erreichbar.")

# ------------------------------------------------------------
# Bot Ready Event
# ------------------------------------------------------------
@bot.event
async def on_ready():
    """Wird einmalig ausgelöst, wenn der Bot vollständig initialisiert wurde."""
    logger.info(f"Bot online als {bot.user} ({bot.user.id})")

    # Cogs laden
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            logger.info(f"Cog geladen: {cog}")
        except Exception as e:
            # Statt exc_info=True, das oft sehr lange Tracebacks liefert, 
            # loggen wir den Fehler direkt.
            logger.error(f"Fehler beim Laden: {cog}: {e}") 

    # ------------------------------------------------------------
    # ✅ Slash Command Synchronisation (EINMALIGER Aufruf)
    # ------------------------------------------------------------
    logger.info("Starte globale Synchronisierung der Slash Commands...")
    
    try:
        # Führt die Synchronisierung der Commands global aus
        synced_commands = await bot.tree.sync(guild=None) 
        
        logger.info(f"✅ {len(synced_commands)} Slash Commands erfolgreich synchronisiert.")
        
    except discord.app_commands.errors.CommandSyncFailure as e:
        # Fängt Fehler ab, wie z.B. HTTP 400 (50035) oder Timeouts
        logger.error(f"❌ Schwerer Command Sync-Fehler (Prüfen Sie App-Konfig/Rate-Limits): {e}")
        
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler bei der Synchronisierung: {e}")


# ------------------------------------------------------------
# Hauptfunktion: Bot + interne API parallel starten
# ------------------------------------------------------------
async def start_bot_and_api():
    """Startet den Bot und die interne API asynchron."""
    # API-Task im Hintergrund starten
    api_task = asyncio.create_task(start_internal_api_background())
    
    # Bot-Start abwarten
    try:
        await bot.start(TOKEN)
    finally:
        # Stellt sicher, dass der API-Task abbricht, wenn der Bot stoppt
        api_task.cancel()
        logger.info("Interne API gestoppt.")

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("Kein TOKEN in .env gefunden")
    
    # Warten auf die Datenbank vor dem Bot-Start
    wait_for_mysql()
    setup_database() # Stellt sicher, dass Tabellen existieren

    try:
        asyncio.run(start_bot_and_api())
    except KeyboardInterrupt:
        logger.info("Bot durch Benutzer gestoppt.")
    except Exception as e:
        logger.critical(f"Ein kritischer Fehler ist aufgetreten: {e}", exc_info=True)
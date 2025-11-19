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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("TOKEN")
BOT_API_HOST = os.getenv("BOT_API_HOST", "0.0.0.0")
BOT_API_PORT = int(os.getenv("BOT_API_PORT", 8001))

async def get_prefix(bot: commands.Bot, message: discord.Message):
    default_prefix = "!"
    if not message.guild:
        return [default_prefix]
    prefix = db_guilds.get_prefix(str(message.guild.id))
    return [prefix, default_prefix] if prefix else [default_prefix]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

internal_api = FastAPI(title="Bot Internal Guild API")

@internal_api.get("/api/guilds")
async def get_bot_guild_ids():
    if not bot.is_ready():
        raise HTTPException(status_code=503, detail="Bot ist nicht bereit.")
    return {"guild_ids": [str(g.id) for g in bot.guilds]}

@internal_api.get("/api/guild/{guild_id}")
async def get_bot_guild_details(guild_id: str):
    if not bot.is_ready():
        raise HTTPException(status_code=503, detail="Bot ist nicht bereit.")
    
    guild = bot.get_guild(int(guild_id))
    if not guild:
        raise HTTPException(status_code=404, detail="Gilde nicht gefunden")

    return {
        "id": str(guild.id),
        "name": guild.name,
        "icon": str(guild.icon.url) if guild.icon else None,
        "owner_id": str(guild.owner_id),
        "text_channels": [{"id": str(c.id), "name": c.name} for c in guild.text_channels],
        "voice_channels": [{"id": str(c.id), "name": c.name} for c in guild.voice_channels],
        "roles": [{"id": str(r.id), "name": r.name} for r in guild.roles if not r.managed and r.name != "@everyone"],
    }

async def start_internal_api_background():
    config = uvicorn.Config(
        internal_api,
        host=BOT_API_HOST,
        port=BOT_API_PORT,
        log_level="warning",
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    await server.serve()

def wait_for_mysql():
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

@bot.event
async def on_ready():
    logger.info(f"Bot online als {bot.user} ({bot.user.id})")

    cogs = [
        "cogs.leveling", "cogs.info", "cogs.moderation", "cogs.birthday", "cogs.setup", 
        "cogs.dynamicvoice", "cogs.musicconverter", "cogs.bumps", "cogs.roles", 
        "cogs.activitytracker", "cogs.joinleft", "cogs.quiz", "cogs.selfinfo", 
        "cogs.metafrage", "cogs.partyquiz", "cogs.codeextractor", "cogs.fakt", 
        "cogs.help", "cogs.weather", "cogs.customcommands", "cogs.docu_search", 
        "cogs.userposts"
    ]

    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f"Cog geladen: {cog}")
        except Exception as e:
            logger.error(f"Fehler beim Laden: {cog}: {e}", exc_info=True)

    synced = await bot.tree.sync()
    logger.info(f"{len(synced)} Slash Commands synchronisiert")

    asyncio.create_task(start_internal_api_background())
    logger.info("Interne API gestartet.")

async def main():
    wait_for_mysql()
    setup_database()

    await bot.start(TOKEN)

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("Kein TOKEN in .env gefunden")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot gestoppt.")
    except Exception as e:
        logger.error(f"Ein kritischer Fehler ist aufgetreten: {e}", exc_info=True)

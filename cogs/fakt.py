import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import json
import random # Wird für zufällige Auswahl benötigt
from datetime import datetime, time, timedelta, timezone


# ------------------------------------------------------------
# Daten-Pfad
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 
FACT_FILE = os.path.join(BASE_DIR, "data", "fakten.json")


# ------------------------------------------------------------
# Hilfsfunktionen für JSON
# ------------------------------------------------------------
def ensure_fact_file():
    data_dir = os.path.dirname(FACT_FILE)
    os.makedirs(data_dir, exist_ok=True)
    if not os.path.exists(FACT_FILE):
        with open(FACT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)

def load_facts():
    ensure_fact_file()
    with open(FACT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_facts(facts):
    ensure_fact_file()
    with open(FACT_FILE, "w", encoding="utf-8") as f:
        json.dump(facts, f, indent=4, ensure_ascii=False)

# ------------------------------------------------------------
# Cog
# ------------------------------------------------------------
class Fakt(commands.Cog):
    """Verwaltet tägliche Fakten und zugehörige Befehle"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_fact.start()

    def cog_unload(self):
        self.daily_fact.cancel()

    # ------------------------------------------------------------
    # /fakt Command - Fakt hinzufügen
    # ------------------------------------------------------------
    @commands.hybrid_command(name="faktadd", description="Füge einen Fakt zur globalen Liste hinzu (Admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_fact(self, ctx: commands.Context, *, content: str):
        facts = load_facts()
        facts.append(content)
        save_facts(facts)
        await ctx.send(f"✅ Fakt hinzugefügt: {content}", ephemeral=True)

    # ------------------------------------------------------------
    # Command: Channel setzen (Wichtig für Multi-Server)
    # ------------------------------------------------------------
    @commands.hybrid_command(name="faktchannel", description="Setzt den Channel für tägliche Fakten (Admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_fact_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        
        print(f"DB ACTION: Channel {channel.id} für Guild {ctx.guild.id} gespeichert.")
        await ctx.send(f"✅ Tägliche Fakten werden nun in {channel.mention} gepostet.", ephemeral=True)
        
    # ------------------------------------------------------------
    # Täglicher Task
    # ------------------------------------------------------------
    @tasks.loop(hours=24)
    async def daily_fact(self):
        await self.bot.wait_until_ready()
        all_facts = load_facts()
        
        if not all_facts:
            print("INFO: Keine Fakten zum Posten in der JSON-Datei vorhanden.")
            return

        fact_to_post = random.choice(all_facts)

        for guild in self.bot.guilds:
            channel = self.bot.get_channel(1429882849334530192) 
            if channel is None or channel.guild.id != guild.id: 
                 continue
            try:
                embed = discord.Embed(
                    title="📌 Fakt des Tages",
                    description=fact_to_post,
                    color=discord.Color.green()
                )
                await channel.send(embed=embed)
            except discord.Forbidden:
                print(f"WARNUNG: Kann in Channel {channel.id} in Guild {guild.id} nicht senden (Forbidden).")
            except Exception as e:
                print(f"FEHLER beim Senden des Fakts in Guild {guild.id}: {e}")
                

    @daily_fact.before_loop
    async def before_daily_fact(self):
        await self.bot.wait_until_ready()
        now = datetime.utcnow()
        target = datetime.combine(now.date(), time(hour=20), tzinfo=timezone.utc) 
        
        if now.replace(tzinfo=timezone.utc) >= target:
            target += timedelta(days=1)
            
        await discord.utils.sleep_until(target)

# ------------------------------------------------------------
# Setup
# ------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Fakt(bot))
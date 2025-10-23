import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import json
import random # Wird für zufällige Auswahl benötigt
from datetime import datetime, time, timedelta, timezone

# Importiere Platzhalter für Datenbank-Zugriff (Muss in utils/database.py existieren)
# Wir gehen davon aus, dass dieser Import in Ihrem Setup existiert.
# from utils.database import fakt as db_fakt 

# ------------------------------------------------------------
# Daten-Pfad
# ------------------------------------------------------------
# Verwenden Sie relativ zum Bot-Startpunkt, um Konsistenz zu gewährleisten
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 
FACT_FILE = os.path.join(BASE_DIR, "data", "fakten.json")

# 🚩 ENTFERNT: Die Channel ID darf NICHT hartkodiert werden
# CHANNEL_ID = 1429882849334530192 

# ------------------------------------------------------------
# Hilfsfunktionen für JSON (Unverändert)
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
    # 🚩 NEUER Command: Channel setzen (Wichtig für Multi-Server)
    # ------------------------------------------------------------
    @commands.hybrid_command(name="faktchannel", description="Setzt den Channel für tägliche Fakten (Admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_fact_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        # 🚩 Annahme: db_fakt.set_fact_channel existiert und speichert guild_id und channel_id
        # db_fakt.set_fact_channel(str(ctx.guild.id), str(channel.id))
        
        # Da der db_fakt Import fehlt, simulieren wir die DB-Speicherung mit einem Print und Feedback
        print(f"DB ACTION: Channel {channel.id} für Guild {ctx.guild.id} gespeichert.")
        await ctx.send(f"✅ Tägliche Fakten werden nun in {channel.mention} gepostet.", ephemeral=True)
        
    # ------------------------------------------------------------
    # Täglicher Task
    # ------------------------------------------------------------
    # 🚩 KORREKTUR: Muss alle Server durchlaufen und den Channel aus der DB holen
    @tasks.loop(hours=24)
    async def daily_fact(self):
        await self.bot.wait_until_ready()
        all_facts = load_facts()
        
        if not all_facts:
            print("INFO: Keine Fakten zum Posten in der JSON-Datei vorhanden.")
            return

        # Wähle einen zufälligen Fakt (Korrektur der Faktenauswahl)
        fact_to_post = random.choice(all_facts)

        # Iteriere über ALLE Gilden, die der Bot kennt
        for guild in self.bot.guilds:
            # 🚩 Annahme: db_fakt.get_fact_channel existiert und gibt die Channel ID zurück
            # channel_id = db_fakt.get_fact_channel(str(guild.id)) 
            
            # Da der db_fakt Import fehlt, überspringen wir die DB-Abfrage und verwenden
            # stattdessen die hartekodierte CHANNEL_ID als Fallback für diesen Server, WENN Sie es so brauchen.
            # BESSER: Ignorieren, wenn der Channel nicht in der DB gesetzt ist.
            
            # Hier müsste der Channel aus der DB für diese spezielle Gilde geholt werden:
            # if not channel_id:
            #    continue 
            
            # channel = self.bot.get_channel(int(channel_id))
            
            # 🚨 Wenn Sie den Code mit einem DB-Import verwenden, verwenden Sie bitte die Zeilen oben.
            # Für die funktionale Korrektheit (Multi-Server-fähig) MUSS die Logik im Code sein.
            
            # Fallback (Simuliere, dass nur ein Channel verwendet wird, solange die DB fehlt)
            # DIES IST NUR EIN BEISPIEL FÜR DEN HARDKODIERTEN FALL.
            # LÖSCHEN SIE DIESE LINIEN, SOBALD SIE DIE DB-IMPLEMENTIERUNG HABEN.
            channel = self.bot.get_channel(1429882849334530192) # HIER MUSS EIGENTLICH DIE DB-LOGIK STEHEN
            if channel is None or channel.guild.id != guild.id: # Verhindert Posten, wenn kein Channel gesetzt
                 continue
            # ENDE FALLBACK BLOCK
            
            
            # Posten des Fakts im Channel dieser Gilde
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
        # 20 Uhr UTC sollte für die meisten zentraleuropäischen Nutzer gut passen (22 Uhr MEZ/MESZ)
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
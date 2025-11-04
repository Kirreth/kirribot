import os
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from datetime import datetime, date, time, timedelta
from typing import Optional
import pytz 
from utils.database import adventscalendar as db_adventscalendar
import csv

# ------------------------------------------------------------
# Pfad zur CSV-Datei
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ADVENT_FILE = os.path.join(BASE_DIR, "data", "Adventskalender.csv")

# ------------------------------------------------------------
# Hilfsfunktion zum Laden der Adventskalender-Daten aus der CSV-Datei
# ------------------------------------------------------------

def load_advent_calendar():
    advent_data = {}
    if not os.path.exists(ADVENT_FILE):
        return advent_data

    with open(ADVENT_FILE, mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) >= 2:
                day = int(row[0])
                surprise = row[1]
                advent_data[day] = surprise
    return advent_data

class AdventsCalendar(commands.Cog):
    """Verwaltet den Adventskalender und tägliche Überraschungen im Dezember"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    # ------------------------------------------------------------
    # Command: Adventskalender öffnen
    # ------------------------------------------------------------
    @commands.hybrid_command(name="advent", description="Öffnet das heutige Türchen des Adventskalenders")
    async def open_advent_door(self, ctx: Context):
        """Öffnet das Türchen für den aktuellen Tag im Dezember"""
        if ctx.guild is None:
            await ctx.send("❌ Dieser Befehl kann nur in einem Server verwendet werden.", ephemeral=True)
            return
             
        today = datetime.now().date()
        if today.month != 12:
            await ctx.send("❌ Der Adventskalender ist nur im Dezember verfügbar.", ephemeral=True)
            return

        door_number = today.day
        surprise = db_adventscalendar.get_surprise_for_day(door_number)

        if surprise is None:
            await ctx.send(f"❌ Für den {door_number}. Dezember wurde noch keine Überraschung festgelegt.", ephemeral=True)
            return

        await ctx.send(f"🎄 Türchen {door_number} geöffnet! Deine Überraschung: {surprise}", ephemeral=True)
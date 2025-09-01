import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from utils import database as db

DISBOARD_ID = 302050872383242240  # Disboard Bot ID

class Bumps(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Nur Disboard-Nachrichten abfangen
        if message.author.id != DISBOARD_ID:
            return

        # Prüfen, ob eine Bump-Bestätigung drin ist
        if "Bump done" in message.content or "Bump erfolgreich" in message.content:
            if message.interaction and message.interaction.user:
                bumper = message.interaction.user
            else:
                return  # Falls kein User ermittelt werden konnte

            db.log_bump(bumper.id, datetime.utcnow())
            print(f"✅ Bump von {bumper} gespeichert")

    @app_commands.command(name="topb", description="Zeigt deine gesamte Anzahl an Bumps")
    async def topb(self, interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        count = db.get_bumps_total(user.id)
        await interaction.response.send_message(f"📈 {user.mention} hat insgesamt **{count} Bumps** gemacht.")

    @app_commands.command(name="topmb", description="Zeigt deine Anzahl an Bumps der letzten 30 Tage")
    async def topmb(self, interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        count = db.get_bumps_30d(user.id)
        await interaction.response.send_message(f"⏳ {user.mention} hat in den letzten 30 Tagen **{count} Bumps** gemacht.")

async def setup(bot):
    await bot.add_cog(Bumps(bot))

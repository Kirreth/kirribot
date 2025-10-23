import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from datetime import datetime, date
from typing import Optional

from utils.database import birthday as db_birthday


class Birthday(commands.Cog):
    """Verwaltet Geburtstage und sendet Glückwünsche"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_birthdays.start()  # tägliche Überprüfung starten

    # ------------------------------------------------------------
    # Command: Geburtstag setzen
    # ------------------------------------------------------------
    @commands.hybrid_command(name="birthday", description="Setze deinen Geburtstag (Format: TT.MM.JJJJ)")
    async def set_birthday(self, ctx: Context, datum: str):
        """Speichert den Geburtstag eines Users"""
        if ctx.guild is None:
             await ctx.send("❌ Dieser Befehl kann nur in einem Server verwendet werden.", ephemeral=True)
             return
             
        try:
            parsed_date = datetime.strptime(datum, "%d.%m.%Y").date()
        except ValueError:
            await ctx.send("❌ Bitte verwende das Format **TT.MM.JJJJ** – Beispiel: `01.04.1998`")
            return

        db_birthday.set_birthday(str(ctx.author.id), str(ctx.guild.id), parsed_date)
        await ctx.send(f"🎂 Dein Geburtstag wurde gespeichert: **{parsed_date.strftime('%d.%m.%Y')}**", ephemeral=True)

    # ------------------------------------------------------------
    # Command: Channel für Geburtstage setzen
    # ------------------------------------------------------------
    @commands.hybrid_command(name="birthdaychannel", description="Setzt den Channel für Geburtstagsnachrichten")
    @commands.has_permissions(manage_guild=True)
    async def set_birthday_channel(self, ctx: Context, channel: Optional[discord.TextChannel] = None):
        """Legt fest, in welchem Channel Geburtstagsgrüße gepostet werden"""
        if ctx.guild is None:
             await ctx.send("❌ Dieser Befehl kann nur in einem Server verwendet werden.", ephemeral=True)
             return
             
        if channel is None:
            channel = ctx.channel

        db_birthday.set_birthday_channel(str(ctx.guild.id), str(channel.id))
        await ctx.send(f"✅ Geburtstagsnachrichten werden nun in {channel.mention} gepostet.", ephemeral=True)

    # ------------------------------------------------------------
    # Hintergrund-Task: Geburtstage prüfen
    # ------------------------------------------------------------
    @tasks.loop(hours=24)
    async def check_birthdays(self):
        """Wird täglich ausgeführt und gratuliert automatisch"""
        today = date.today()
        # Annahme: get_today_birthdays() liefert (user_id, guild_id, birthday_date, last_congratulated)
        birthdays = db_birthday.get_today_birthdays()

        for user_id, guild_id, birthday_date, last_congratulated in birthdays:
            # Stelle sicher, dass an diesem Tag noch nicht gratuliert wurde
            if last_congratulated and last_congratulated == today:
                continue

            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue

            channel_id = db_birthday.get_birthday_channel(guild_id)
            if not channel_id:
                continue

            channel = guild.get_channel(int(channel_id))
            if not channel:
                continue

            member = guild.get_member(int(user_id))
            if not member:
                continue

            age = today.year - birthday_date.year
            msg = f"🎉 Alles Gute zum **{age}. Geburtstag**, {member.mention}! 🥳"
            
            try:
                await channel.send(msg)
            except discord.Forbidden:
                 print(f"WARNUNG: Keine Sendeberechtigung in Channel {channel.id} in Guild {guild.id}")
                 continue

            # 🚩 KORREKTUR: Muss user_id UND guild_id übergeben, um den richtigen Eintrag zu markieren.
            db_birthday.mark_congratulated(user_id, guild_id) 

    # ------------------------------------------------------------
    # Task starten
    # ------------------------------------------------------------
    @check_birthdays.before_loop
    async def before_check_birthdays(self):
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------
    # Command: Geburtstag entfernen
    # ------------------------------------------------------------
    @commands.hybrid_command(name="removebirthday", description="Entfernt deinen gespeicherten Geburtstag")
    async def remove_birthday(self, ctx: Context):
        """Löscht den gespeicherten Geburtstag eines Users"""
        if ctx.guild is None:
             await ctx.send("❌ Dieser Befehl kann nur in einem Server verwendet werden.", ephemeral=True)
             return
             
        db_birthday.remove_birthday(str(ctx.author.id), str(ctx.guild.id))
        await ctx.send("✅ Dein Geburtstag wurde entfernt.", ephemeral=True)


# ------------------------------------------------------------
# Cog Setup
# ------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Birthday(bot))
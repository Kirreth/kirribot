import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from datetime import datetime, date, time, timedelta
from typing import Optional
import pytz # Wichtig: Für die Zeitzonen-Steuerung

# Hier müssen Sie Ihre Datenbank-Imports beibehalten
from utils.database import birthday as db_birthday 

# Zeitzone für Deutschland definieren
GERMANY_TIMEZONE = pytz.timezone('Europe/Berlin')


class Birthday(commands.Cog):
    """Verwaltet Geburtstage und sendet Glückwünsche pünktlich um 00:00 Uhr deutscher Zeit"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Starte die tägliche Überprüfung (der Start wird durch before_check_birthdays verzögert)
        self.check_birthdays.start() 

    # Beim Entladen des Cogs die Schleife stoppen
    def cog_unload(self):
        self.check_birthdays.cancel()

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
            await ctx.send("❌ Bitte verwende das Format **TT.MM.JJJJ** – Beispiel: `01.04.1998`", ephemeral=True)
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
    # Hintergrund-Task: Geburtstage prüfen (Ablauf um 00:00 DE-Zeit)
    # ------------------------------------------------------------
    @tasks.loop(hours=24)
    async def check_birthdays(self):
        """Wird täglich um 00:00 Uhr DE-Zeit ausgeführt und gratuliert automatisch"""
        
        # Die Zeit ist nun 00:00 Uhr DE-Zeit. Wir verwenden das heutige Datum
        # basierend auf dem Server-Datum, da der Bot gerade um Mitternacht startet.
        # Um ganz sicher zu gehen, können wir die Zeitzone verwenden:
        today_germany = datetime.now(GERMANY_TIMEZONE).date()
        
        # Annahme: get_today_birthdays() liefert (user_id, guild_id, birthday_date, last_congratulated)
        birthdays = db_birthday.get_today_birthdays()

        for user_id, guild_id, birthday_date, last_congratulated in birthdays:
            # Stelle sicher, dass an diesem Tag noch nicht gratuliert wurde
            if last_congratulated and last_congratulated == today_germany:
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

            # Alter berechnen
            age = today_germany.year - birthday_date.year - ((today_germany.month, today_germany.day) < (birthday_date.month, birthday_date.day))
            if age < 0:
                age = today_germany.year - birthday_date.year
            
            msg = f"🎉 Alles Gute zum **{age}. Geburtstag**, {member.mention}! 🥳"
            
            try:
                await channel.send(msg)
            except discord.Forbidden:
                print(f"WARNUNG: Keine Sendeberechtigung in Channel {channel.id} in Guild {guild.id}")
                continue

            # Markiert den Eintrag in der DB als gratuliert für heute
            db_birthday.mark_congratulated(user_id, guild_id) 

    # ------------------------------------------------------------
    # Task starten: Verzögert den Start auf 00:00 Uhr deutscher Zeit
    # ------------------------------------------------------------
    @check_birthdays.before_loop
    async def before_check_birthdays(self):
        await self.bot.wait_until_ready()
        
        # 1. Definiere die Zielzeit: Mitternacht (00:00 Uhr) in deutscher Zeit
        target_time = time(hour=0, minute=0, second=0)
        
        # 2. Hole die aktuelle Zeit in der deutschen Zeitzone
        now_germany = datetime.now(GERMANY_TIMEZONE)
        
        # 3. Kombiniere das Datum mit der Zielzeit und der korrekten Zeitzone
        target_datetime_germany = datetime.combine(now_germany.date(), target_time, tzinfo=GERMANY_TIMEZONE)

        # 4. Wenn die Zielzeit bereits verstrichen ist (Bot wurde nach 00:00 Uhr gestartet), 
        #    verschiebe das Ziel auf Mitternacht des nächsten Tages.
        if target_datetime_germany < now_germany:
            next_day = now_germany.date() + timedelta(days=1)
            target_datetime_germany = datetime.combine(next_day, target_time, tzinfo=GERMANY_TIMEZONE)

        # 5. Konvertiere die deutsche Zielzeit in die UTC-Zeit (pfenniggenaue Zeit)
        #    Dies ist notwendig, da discord.utils.sleep_until() Timezone-Aware-Objekte benötigt,
        #    und UTC der Goldstandard ist.
        target_datetime_utc = target_datetime_germany.astimezone(pytz.utc)

        # 6. Berechne die Wartezeit vom aktuellen UTC-Moment bis zur UTC-Zielzeit
        now_utc = datetime.now(pytz.utc)
        wait_seconds = (target_datetime_utc - now_utc).total_seconds()
        
        # 7. Debug-Log (zeigt, wie lange gewartet wird)
        print(f"[{now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}] DEBUG: Warte {wait_seconds:.2f} Sekunden bis zur nächsten Mitternacht (DE-Zeit: {target_datetime_germany.strftime('%H:%M:%S %Z')}).")

        # 8. Warte, bis die Mitternachtszeit erreicht ist
        await discord.utils.sleep_until(target_datetime_utc)

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
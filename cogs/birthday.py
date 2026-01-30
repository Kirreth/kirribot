import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from datetime import datetime, time
import pytz
from typing import Optional

# Annahme: Dein Datenbank-Modul ist so strukturiert
from utils.database import birthday as db_birthday 

# Konfiguration der Zeitzone und Zeit
GERMANY_TIMEZONE = pytz.timezone('Europe/Berlin')
# Die Zeit, zu der die Prüfung täglich stattfinden soll
CELEBRATION_TIME = time(hour=0, minute=0, second=0, tzinfo=GERMANY_TIMEZONE)

class Birthday(commands.Cog):
    """Verwaltet Geburtstage und sendet Glückwünsche pünktlich um 00:00 Uhr deutscher Zeit"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Der Loop startet hier
        self.check_birthdays.start() 

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
    # Hintergrund-Task: Geburtstage prüfen (Automatisch gesteuert durch time=)
    # ------------------------------------------------------------
    @tasks.loop(time=CELEBRATION_TIME)
    async def check_birthdays(self):
        """Wird täglich um 00:00 Uhr DE-Zeit ausgeführt"""
        
        # Aktuelles Datum in Deutschland
        today_germany = datetime.now(GERMANY_TIMEZONE).date()
        
        # Hole alle heutigen Geburtstagskinder aus der DB
        # Erwartet: Liste von Tuples (user_id, guild_id, birthday_date, last_congratulated)
        birthdays = db_birthday.get_today_birthdays()

        for user_id, guild_id, birthday_date, last_congratulated in birthdays:
            # 1. Dubletten-Check: Wurde heute schon gratuliert?
            if last_congratulated and last_congratulated == today_germany:
                continue

            # 2. Guild laden
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue

            # 3. Channel laden
            channel_id = db_birthday.get_birthday_channel(guild_id)
            if not channel_id:
                continue

            channel = guild.get_channel(int(channel_id))
            if not channel:
                continue

            # 4. Member laden (fetch_member ist sicherer als get_member)
            try:
                member = await guild.fetch_member(int(user_id))
            except discord.NotFound:
                # User nicht mehr auf dem Server
                continue
            except discord.HTTPException:
                continue

            # 5. Alter berechnen
            age = today_germany.year - birthday_date.year - (
                (today_germany.month, today_germany.day) < (birthday_date.month, birthday_date.day)
            )
            
            # Falls jemand heute geboren wurde oder Datenfehler vorliegen
            if age < 0: age = 0
            
            msg = f"🎉 Alles Gute zum **{age}. Geburtstag**, {member.mention}! 🥳"
            
            # 6. Nachricht senden
            try:
                await channel.send(msg)
                # In der DB markieren, dass gratuliert wurde
                db_birthday.mark_congratulated(user_id, guild_id)
            except discord.Forbidden:
                print(f"WARNUNG: Keine Sendeberechtigung in Channel {channel.id} (Server: {guild.name})")
            except Exception as e:
                print(f"Fehler beim Senden der Nachricht: {e}")

    @check_birthdays.before_loop
    async def before_check_birthdays(self):
        """Wartet, bis der Bot bereit ist, bevor der Loop startet"""
        await self.bot.wait_until_ready()
        print(f"Birthday-Loop aktiv: Nächster Check geplant für {CELEBRATION_TIME.strftime('%H:%M:%S')} (Berliner Zeit).")

    # ------------------------------------------------------------
    # Command: Geburtstag entfernen
    # ------------------------------------------------------------
    @commands.hybrid_command(name="removebirthday", description="Entfernt deinen gespeicherten Geburtstag")
    async def remove_birthday(self, ctx: Context):
        if ctx.guild is None:
            await ctx.send("❌ Dieser Befehl kann nur in einem Server verwendet werden.", ephemeral=True)
            return
             
        db_birthday.remove_birthday(str(ctx.author.id), str(ctx.guild.id))
        await ctx.send("✅ Dein Geburtstag wurde entfernt.", ephemeral=True)

# Setup-Funktion für den Bot
async def setup(bot: commands.Bot):
    await bot.add_cog(Birthday(bot))
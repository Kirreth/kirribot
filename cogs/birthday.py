import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from datetime import datetime, date, time, timedelta
from typing import Optional
import pytz 
from utils.database import birthday as db_birthday 

GERMANY_TIMEZONE = pytz.timezone('Europe/Berlin')

class Birthday(commands.Cog):
    """Verwaltet Geburtstage und sendet Glückwünsche pünktlich um 00:00 Uhr deutscher Zeit"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
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
    # Hintergrund-Task: Geburtstage prüfen (Ablauf um 00:00 DE-Zeit)
    # ------------------------------------------------------------
    @tasks.loop(hours=24)
    async def check_birthdays(self):
        """Wird täglich um 00:00 Uhr DE-Zeit ausgeführt und gratuliert automatisch"""
        
        today_germany = datetime.now(GERMANY_TIMEZONE).date()
        birthdays = db_birthday.get_today_birthdays()

        for user_id, guild_id, birthday_date, last_congratulated in birthdays:
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

            age = today_germany.year - birthday_date.year - ((today_germany.month, today_germany.day) < (birthday_date.month, birthday_date.day))
            if age < 0:
                age = today_germany.year - birthday_date.year
            
            msg = f"🎉 Alles Gute zum **{age}. Geburtstag**, {member.mention}! 🥳"
            
            try:
                await channel.send(msg)
            except discord.Forbidden:
                print(f"WARNUNG: Keine Sendeberechtigung in Channel {channel.id} in Guild {guild.id}")
                continue

            db_birthday.mark_congratulated(user_id, guild_id)

    @check_birthdays.before_loop
    async def before_check_birthdays(self):
        await self.bot.wait_until_ready()
        target_time = time(hour=0, minute=0, second=0)
        now_germany = datetime.now(GERMANY_TIMEZONE)
        target_datetime_germany = datetime.combine(now_germany.date(), target_time, tzinfo=GERMANY_TIMEZONE)

        if target_datetime_germany < now_germany:
            next_day = now_germany.date() + timedelta(days=1)
            target_datetime_germany = datetime.combine(next_day, target_time, tzinfo=GERMANY_TIMEZONE)

        target_datetime_utc = target_datetime_germany.astimezone(pytz.utc)
        now_utc = datetime.now(pytz.utc)
        wait_seconds = (target_datetime_utc - now_utc).total_seconds()
        
        print(f"[{now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}] DEBUG: Warte {wait_seconds:.2f} Sekunden bis zur nächsten Mitternacht (DE-Zeit: {target_datetime_germany.strftime('%H:%M:%S %Z')}).")

        await discord.utils.sleep_until(target_datetime_utc)

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

# ------------------------------------------------------------
# Cog Setup
# ------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Birthday(bot))

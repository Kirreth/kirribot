# cogs/bumps.py
import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from utils.database import bumps as db_bumps
from typing import Union, Optional

# Disboard's User ID
DISBOARD_ID: int = 302050872383242240
# Disboard Cooldown (2 Stunden)
BUMP_COOLDOWN: timedelta = timedelta(hours=2)

class Bumps(commands.Cog):
    """Verwaltet Disboard Bumps und zugehörige Befehle"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

# ------------------------------------------------------------
# Bump registrieren
# ------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.id != DISBOARD_ID or not message.guild:
            return

        # Prüfe auf Erfolgsmeldung (Sprachunabhängig)
        is_success_message: bool = ("Bump done" in message.content or "Bump erfolgreich" in message.content)
        
        if is_success_message:
            bumper: Optional[Union[discord.User, discord.Member]]
            
            # Bei Slash Commands (Discord Bot-Interaktion)
            if message.interaction and message.interaction.user:
                bumper = message.interaction.user
            # Fallback (weniger zuverlässig)
            elif message.mentions: 
                bumper = message.mentions[0] if message.mentions[0].id != DISBOARD_ID else None
            else:
                return 

            if not bumper:
                return

            user_id: str = str(bumper.id)
            guild_id: str = str(message.guild.id)
            current_time: datetime = datetime.utcnow() # UTC-Zeit verwenden

            # Datenbank-Aktionen: Loggen, Zähler erhöhen, Cooldown-Zeit speichern
            db_bumps.log_bump(user_id, guild_id, current_time)
            db_bumps.increment_total_bumps(user_id, guild_id)
            db_bumps.set_last_bump_time(guild_id, current_time) 
            
            print(f"✅ Bump von {bumper} gespeichert und Cooldown-Zeit aktualisiert")

# ------------------------------------------------------------
# Nächster Bump Befehl (/nextbump)
# ------------------------------------------------------------

    @commands.hybrid_command(
        name="nextbump",
        description="Zeigt an, wann der nächste Disboard Bump möglich ist."
    )
    async def nextbump(self, ctx: commands.Context) -> None:
        await ctx.defer()
        
        guild_id: str = str(ctx.guild.id) if ctx.guild else "0"
        
        # Ruft den letzten Bump-Zeitstempel (datetime.datetime, UTC) ab oder None
        last_bump_time: Optional[datetime] = db_bumps.get_last_bump_time(guild_id)
        
        embed: discord.Embed
        
        if last_bump_time is None:
            embed = discord.Embed(
                title="⏳ Nächster Bump",
                description="Der Server wurde noch nicht gebumpt. **Du kannst sofort bumpen!**",
                color=discord.Color.green()
            )
        else:
            # Stelle sicher, dass last_bump_time als UTC behandelt wird
            if last_bump_time.tzinfo is None:
                last_bump_time = last_bump_time.replace(tzinfo=timezone.utc)
            
            next_bump_time: datetime = last_bump_time + BUMP_COOLDOWN
            now_utc: datetime = datetime.utcnow().replace(tzinfo=timezone.utc)
            
            if now_utc >= next_bump_time:
                embed = discord.Embed(
                    title="✅ Nächster Bump",
                    description="**Der Cooldown ist abgelaufen!** Du kannst jetzt sofort `/bump` nutzen.",
                    color=discord.Color.green()
                )
            else:
                time_remaining: timedelta = next_bump_time - now_utc
                
                # Formatierung der verbleibenden Zeit
                total_seconds = int(time_remaining.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                
                time_str: str = f"{hours} Stunden und {minutes} Minuten"
                
                # Discord Timestamp
                timestamp_str: str = f"<t:{int(next_bump_time.timestamp())}:R>"
                
                embed = discord.Embed(
                    title="⏳ Nächster Bump",
                    description=f"Der nächste Bump ist in **{time_str}** möglich.\n\n"
                                f"Das ist {timestamp_str}.",
                    color=discord.Color.orange()
                )
                
        await ctx.send(embed=embed)

# ------------------------------------------------------------
# Top Bumper (Hybrid Command)
# ------------------------------------------------------------

    @commands.hybrid_command(
        name="topb",
        description="Zeigt die Top 3 mit den meisten Bumps insgesamt"
    )
    async def topb(self, ctx: commands.Context) -> None:
        await ctx.defer()
        guild_id: str = str(ctx.guild.id) if ctx.guild else "0"
        top_users = db_bumps.get_bump_top(guild_id, days=None, limit=3)

        if not top_users:
            await ctx.send("📊 Es gibt noch keine Bumps in diesem Server.")
            return

        description = ""
        for index, (user_id, count) in enumerate(top_users, start=1):
            user = ctx.guild.get_member(int(user_id)) if ctx.guild else None
            if not user:
                try:
                    user = await self.bot.fetch_user(int(user_id))
                except discord.NotFound:
                    user = None

            username = user.mention if user else f"Unbekannt ({user_id})"
            description += f"**#{index}** {username} – **{count} Bumps**\n"

        embed = discord.Embed(
            title="🏆 Top 3 Bumper (Gesamt)",
            description=description,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

# ------------------------------------------------------------
# Top monatliche Bumper (Hybrid Command)
# ------------------------------------------------------------

    @commands.hybrid_command(
        name="topmb",
        description="Zeigt die Top 3 mit den meisten Bumps in den letzten 30 Tagen"
    )
    async def topmb(self, ctx: commands.Context) -> None:
        await ctx.defer()
        guild_id: str = str(ctx.guild.id) if ctx.guild else "0"
        top_users = db_bumps.get_bump_top(guild_id, days=30, limit=3)

        if not top_users:
            await ctx.send("📊 Es gibt noch keine Bumps in den letzten 30 Tagen.")
            return

        description = ""
        for index, (user_id, count) in enumerate(top_users, start=1):
            user = ctx.guild.get_member(int(user_id)) if ctx.guild else None
            if not user:
                try:
                    user = await self.bot.fetch_user(int(user_id))
                except discord.NotFound:
                    user = None

            username = user.mention if user else f"Unbekannt ({user_id})"
            description += f"**#{index}** {username} – **{count} Bumps**\n"

        embed = discord.Embed(
            title="⏳ Top 3 Bumper (Letzte 30 Tage)",
            description=description,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bumps(bot))
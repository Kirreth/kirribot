# cogs/bumps.py
import discord
from discord.ext import commands, tasks # Import tasks für Hintergrundaufgaben
from discord.utils import utcnow
from datetime import datetime, timedelta, timezone
from typing import Union, Optional, List, Tuple
from utils.database import bumps as db_bumps
from utils.database import roles as db_roles

DISBOARD_ID: int = 302050872383242240
BUMP_COOLDOWN: timedelta = timedelta(hours=2)
REMINDER_BUFFER: timedelta = timedelta(minutes=5)
REMINDER_CHECK_INTERVAL: timedelta = timedelta(minutes=5)

class Bumps(commands.Cog):
    """Verwaltet Disboard Bumps, Rollenbefehle und Statistiken und sendet Bump-Erinnerungen"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not self.bump_reminder_check.is_running():
            self.bump_reminder_check.start()
    
    def cog_unload(self) -> None:
        """Stoppt die Hintergrundaufgabe beim Entladen des Cogs"""
        self.bump_reminder_check.cancel()

    # ------------------------------------------------------------
    # HINTERGRUNDAUFGABE: Cooldown-Prüfung und Erinnerung
    # ------------------------------------------------------------
    @tasks.loop(minutes=REMINDER_CHECK_INTERVAL.total_seconds() / 60)
    async def bump_reminder_check(self) -> None:
        """Prüft, ob der Cooldown abgelaufen ist, und sendet eine Erinnerung."""

        guild_settings: List[Tuple[str, str, str]] = db_roles.get_all_guild_settings() 

        for guild_id_str, role_id_str, channel_id_str in guild_settings:
            guild_id = int(guild_id_str)
            
            bump_data: Optional[Tuple[datetime, bool]] = db_bumps.get_last_bump_time_and_notified_status(guild_id_str)
            
            if bump_data is None:
                continue 

            last_bump_time, already_notified = bump_data
            
            if last_bump_time.tzinfo is None:
                last_bump_time = last_bump_time.replace(tzinfo=timezone.utc)
            
            next_bump_time = last_bump_time + BUMP_COOLDOWN
            reminder_time = next_bump_time + REMINDER_BUFFER
            now_utc = utcnow()
            
            if now_utc >= reminder_time and not already_notified:
                guild = self.bot.get_guild(guild_id)
                role = guild.get_role(int(role_id_str)) if guild and role_id_str else None
                channel = guild.get_channel(int(channel_id_str)) if guild and channel_id_str else None
                
                if not guild or not role or not channel:
                    print(f"[WARN] Erinnerung konnte nicht gesendet werden (Guild/Role/Channel fehlt) für {guild_id_str}")
                    continue

                try:
                    await channel.send(
                        f"⏰ **Bump-Zeit!** Der 2-stündige Cooldown ist abgelaufen. "
                        f"Jemand von {role.mention} kann jetzt `/bump` nutzen! <t:{int(next_bump_time.timestamp())}:R>"
                    )
                    
                    db_bumps.set_notified_status(guild_id_str, True)
                    print(f"✅ Erinnerung erfolgreich gesendet für Guild {guild_id_str}.")
                    
                except discord.Forbidden:
                    print(f"[ERROR] Keine Berechtigung, in Channel {channel_id_str} zu schreiben.")
                except Exception as e:
                    print(f"[ERROR] Fehler beim Senden der Erinnerung: {e}")

    @bump_reminder_check.before_loop
    async def before_bump_reminder_check(self) -> None:
        """Wartet, bis der Bot vollständig bereit ist."""
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------
    # Bump registrieren
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        print(f"[DEBUG] Nachricht empfangen: author={message.author}, content='{message.content}'")

        if message.author.id != DISBOARD_ID or not message.guild:
            return
        
        is_success_message = False

        if "Bump done" in message.content or "Bump erfolgreich" in message.content:
            is_success_message = True

        if not is_success_message and message.embeds:
            embed = message.embeds[0]
            embed_text = (embed.title or "") + (embed.description or "")
            
            if "Bump done" in embed_text or "Bump erfolgreich" in embed_text:
                is_success_message = True
        
        if not is_success_message:
            return
        
        print(f"[DEBUG] Bump-Erfolg erkannt! Content: '{message.content}', Embeds: {len(message.embeds) > 0}")
        
        bumper: Optional[Union[discord.User, discord.Member]] = None

        if message.interaction and message.interaction.user:
            bumper = message.interaction.user
        elif message.mentions:
            bumper = message.mentions[0]
        else:
            print("[DEBUG] Kein Bumper erkannt!")
            return

        user_id = str(bumper.id)
        guild_id = str(message.guild.id)
        current_time = utcnow()

        print(f"[DEBUG] Versuche Bump zu loggen: user={user_id}, guild={guild_id}, timestamp={current_time}")
        db_bumps.log_bump(user_id, guild_id, current_time)
        db_bumps.increment_total_bumps(user_id, guild_id)
        db_bumps.set_last_bump_time(guild_id, current_time)
        db_bumps.set_notified_status(guild_id, False) 
        print(f"✅ Bump von {bumper} ({user_id}) in Guild {guild_id} gespeichert und Erinnerung zurückgesetzt.")

    # ------------------------------------------------------------
    # Nächster Bump
    # ------------------------------------------------------------
    @commands.hybrid_command(
        name="nextbump",
        description="Zeigt an, wann der nächste Disboard Bump möglich ist."
    )
    async def nextbump(self, ctx: commands.Context) -> None:
        if not ctx.guild:
            return await ctx.send("Dieser Befehl kann nur auf einem Server ausgeführt werden.", ephemeral=True)
        await ctx.defer()

        guild_id = str(ctx.guild.id)
        last_bump_time: Optional[datetime] = db_bumps.get_last_bump_time(guild_id)

        if last_bump_time is None:
            embed = discord.Embed(
                title="⏳ Nächster Bump",
                description="Der Server wurde noch nicht gebumpt. **Du kannst sofort bumpen!**",
                color=discord.Color.green()
            )
        else:
            if last_bump_time.tzinfo is None:
                last_bump_time = last_bump_time.replace(tzinfo=timezone.utc)
            next_bump_time = last_bump_time + BUMP_COOLDOWN
            now_utc = utcnow()

            if now_utc >= next_bump_time:
                embed = discord.Embed(
                    title="✅ Nächster Bump",
                    description="**Der Cooldown ist abgelaufen!** Du kannst jetzt sofort `/bump` nutzen.",
                    color=discord.Color.green()
                )
            else:
                time_remaining = next_bump_time - now_utc
                total_seconds = int(time_remaining.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                timestamp_str = f"<t:{int(next_bump_time.timestamp())}:R>"

                embed = discord.Embed(
                    title="⏳ Nächster Bump",
                    description=f"Der nächste Bump ist in **{hours} Stunden und {minutes} Minuten** möglich.\n\n"
                                f"Das ist {timestamp_str}.",
                    color=discord.Color.orange()
                )

        await ctx.send(embed=embed)

    # ------------------------------------------------------------
    # Top Bumper (Gesamt) 
    # ------------------------------------------------------------
    @commands.hybrid_command(
        name="topb",
        description="Zeigt die Top 3 mit den meisten Bumps insgesamt"
    )
    async def topb(self, ctx: commands.Context) -> None:
        if not ctx.guild:
            return await ctx.send("Dieser Befehl kann nur auf einem Server ausgeführt werden.", ephemeral=True)
        await ctx.defer()

        guild_id = str(ctx.guild.id)
        top_users = db_bumps.get_bump_top(guild_id, days=None, limit=3)

        if not top_users:
            await ctx.send("📊 Es gibt noch keine Bumps in diesem Server.")
            return

        description = ""
        for index, (user_id, count) in enumerate(top_users, start=1):
            try:
                user = ctx.guild.get_member(int(user_id)) or await self.bot.fetch_user(int(user_id))
            except Exception:
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
    # Top monatliche Bumper
    # ------------------------------------------------------------
    @commands.hybrid_command(
        name="topmb",
        description="Zeigt die Top 3 mit den meisten Bumps in den letzten 30 Tagen"
    )
    async def topmb(self, ctx: commands.Context) -> None:
        if not ctx.guild:
            return await ctx.send("Dieser Befehl kann nur auf einem Server ausgeführt werden.", ephemeral=True)
        await ctx.defer()

        guild_id = str(ctx.guild.id)
        top_users = db_bumps.get_bump_top(guild_id, days=30, limit=3)

        if not top_users:
            await ctx.send("📊 Es gibt noch keine Bumps in den letzten 30 Tagen.")
            return

        description = ""
        for index, (user_id, count) in enumerate(top_users, start=1):
            try:
                user = ctx.guild.get_member(int(user_id)) or await self.bot.fetch_user(int(user_id))
            except Exception:
                user = None
            username = user.mention if user else f"Unbekannt ({user_id})"
            description += f"**#{index}** {username} – **{count} Bumps**\n"

        embed = discord.Embed(
            title="⏳ Top 3 Bumper (Letzte 30 Tage)",
            description=description,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    # ------------------------------------------------------------
    # Rollen selbst zuweisen / entfernen
    # ------------------------------------------------------------
    @commands.hybrid_command(
        name="getbumprole",
        description="Weise dir die Bumper-Rolle selbst zu."
    )
    async def getbumprole(self, ctx: commands.Context) -> None:
        guild_id = str(ctx.guild.id)
        role_id = db_roles.get_bumper_role(guild_id)
        if not role_id:
            return await ctx.send("❌ Keine Bumper-Rolle für diesen Server festgelegt.", ephemeral=True)

        role = ctx.guild.get_role(int(role_id))
        if not role:
            return await ctx.send("⚠️ Die gespeicherte Bumper-Rolle existiert nicht mehr.", ephemeral=True)

        member = ctx.author
        if role in member.roles:
            await ctx.send("✅ Du hast die Bumper-Rolle bereits!", ephemeral=True)
        else:
            try:
                await member.add_roles(role, reason="Selbst zugewiesene Bumper-Rolle")
                await ctx.send(f"🎉 Du hast die Rolle {role.mention} erhalten!", ephemeral=True)
            except discord.Forbidden:
                await ctx.send("⚠️ Ich habe keine Berechtigung, dir die Rolle zu geben.", ephemeral=True)

    @commands.hybrid_command(
        name="delbumprole",
        description="Entfernt die Bumper-Rolle von dir selbst."
    )
    async def delbumprole(self, ctx: commands.Context) -> None:
        guild_id = str(ctx.guild.id)
        role_id = db_roles.get_bumper_role(guild_id)
        if not role_id:
            return await ctx.send("❌ Keine Bumper-Rolle für diesen Server festgelegt.", ephemeral=True)

        role = ctx.guild.get_role(int(role_id))
        if not role:
            return await ctx.send("⚠️ Die gespeicherte Bumper-Rolle existiert nicht mehr.", ephemeral=True)

        member = ctx.author
        if role not in member.roles:
            await ctx.send("ℹ️ Du hast die Bumper-Rolle nicht.", ephemeral=True)
        else:
            try:
                await member.remove_roles(role, reason="Selbst entfernt")
                await ctx.send(f"❌ Die Rolle {role.mention} wurde entfernt.", ephemeral=True)
            except discord.Forbidden:
                await ctx.send("⚠️ Ich habe keine Berechtigung, die Rolle zu entfernen.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bumps(bot))
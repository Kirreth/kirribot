import discord
from discord.ext import commands, tasks
from discord.utils import utcnow
from datetime import datetime, timedelta, timezone
from typing import Union, Optional, List, Tuple
from utils.database import bumps as db_bumps
from utils.database import guilds as db_guilds

DISBOARD_ID: int = 302050872383242240
BUMP_COOLDOWN: timedelta = timedelta(hours=2)

class Bumps(commands.Cog):
    """Verwaltet Disboard Bumps, Rollenbefehle und Statistiken und sendet Bump-Erinnerungen"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # DIESE ZUWEISUNG IST JETZT KORREKT, DA DIE FUNKTION TEIL DER KLASSE IST
        if not self.bump_reminder_check.is_running():
            self.bump_reminder_check.start()

    def cog_unload(self) -> None:
        """Stoppt die Hintergrundaufgabe beim Entladen des Cogs"""
        self.bump_reminder_check.cancel()

    # ------------------------------------------------------------
    # HINTERGRUNDAUFGABE: Cooldown-Prüfung und Erinnerung (sekundengenau)
    # ------------------------------------------------------------
    @tasks.loop(seconds=1)
    async def bump_reminder_check(self) -> None:
        """Prüft jede Sekunde, ob der Cooldown abgelaufen ist, und sendet eine Erinnerung."""
        try:
            # Holt alle Gilden mit Reminder-Channel + Bumper-Rolle aus guild_settings
            guild_settings = db_guilds.get_all_bump_settings()
            # Erwartetes Format: [(guild_id, reminder_channel_id, bumper_role_id), ...]
        except Exception as e:
            print(f"[ERROR] Fehler beim Abrufen aller Guild-Einstellungen: {e}")
            return

        now_utc = utcnow()

        for guild_id_str, reminder_channel_id, bumper_role_id in guild_settings:
            if not reminder_channel_id:
                continue

            last_bump_time: Optional[datetime] = db_bumps.get_last_bump_time(guild_id_str)
            if last_bump_time is None:
                continue

            if last_bump_time.tzinfo is None:
                last_bump_time = last_bump_time.replace(tzinfo=timezone.utc)

            next_bump_time = last_bump_time + BUMP_COOLDOWN
            if now_utc < next_bump_time:
                continue  # Cooldown läuft noch

            reminded = db_bumps.get_notified_status(guild_id_str)
            if reminded:
                continue  # Schon erinnert

            # Channel & Rolle abrufen
            channel = self.bot.get_channel(reminder_channel_id)
            if not channel:
                continue

            bumper_role_mention = ""
            guild = self.bot.get_guild(int(guild_id_str))
            
            # Die Rolle wird erwähnt, wenn eine ID aus der DB vorhanden ist
            if guild and bumper_role_id:
                role = guild.get_role(int(bumper_role_id))
                if role:
                    bumper_role_mention = role.mention

            try:
                await channel.send(
                    f"⏰ **Bump-Zeit!** Der 2-stündige Cooldown ist abgelaufen.\n"
                    f"{bumper_role_mention} – jemand kann jetzt `/bump` nutzen! "
                    f"<t:{int(next_bump_time.timestamp())}:R>"
                )
                db_bumps.set_notified_status(guild_id_str, True)
            except discord.Forbidden:
                print(f"[ERROR] Keine Berechtigung, in Channel {reminder_channel_id} zu schreiben.")
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
        if message.author.id != DISBOARD_ID or not message.guild:
            return
        
        is_success_message = "Bump done" in message.content or "Bump erfolgreich" in message.content
        if not is_success_message and message.embeds:
            embed = message.embeds[0]
            embed_text = (embed.title or "") + (embed.description or "")
            if "Bump done" in embed_text or "Bump erfolgreich" in embed_text:
                is_success_message = True
        
        if not is_success_message:
            return
        
        bumper: Optional[Union[discord.User, discord.Member]] = None
        if message.interaction_metadata and message.interaction_metadata.user:
            bumper = message.interaction_metadata.user
        elif message.mentions:
            bumper = message.mentions[0]
        else:
            return

        user_id = str(bumper.id)
        guild_id = str(message.guild.id)
        current_time = utcnow()

        db_bumps.log_bump(user_id, guild_id, current_time)
        db_bumps.increment_total_bumps(user_id, guild_id)
        db_bumps.set_last_bump_time(guild_id, current_time)
        db_bumps.set_notified_status(guild_id, False) # Setze Benachrichtigungs-Status zurück

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
                color=discord.Color(int("24B8B8", 16))
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
                    color=discord.Color(int("24B8B8", 16))
                )
            else:
                time_remaining = next_bump_time - now_utc
                total_seconds = int(time_remaining.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                if hours > 1:
                    time_str = f"{hours} Stunden und {minutes} Minuten"
                elif hours == 1:
                    time_str = f"1 Stunde und {minutes} Minuten"
                else:
                    time_str = f"{minutes} Minuten"

                embed = discord.Embed(
                    title="⏳ Nächster Bump",
                    description=f"Der nächste Bump ist **<t:{int(next_bump_time.timestamp())}:R>** möglich.\n\n",
                    color=discord.Color(int("24B8B8", 16))
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
            color=discord.Color(int("24B8B8", 16))
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
            color=discord.Color(int("24B8B8", 16))
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
        role_id = db_guilds.get_bumper_role(guild_id)
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
        # ANNAHME: db_roles.get_bumper_role holt die ID aus guild_settings.bumper_role_id
        role_id = db_guilds.get_bumper_role(guild_id)
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
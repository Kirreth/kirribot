import discord
from discord.ext import commands
from discord.ext.commands import Context
from datetime import timedelta, datetime
from utils.database import moderation as db_mod
from typing import Optional 

class Moderation(commands.Cog):
    """Bietet Moderationsbefehle wie Clear, Mute, Warn, Ban und Sanctions"""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Definiere die erlaubte Channel ID
        self.ALLOWED_CHANNEL_ID = 1428357460506443926

    # ------------------------------------------------------------
    # Cog-weit: Nur Moderatoren/Admins dürfen Commands ausführen
    # ------------------------------------------------------------
    async def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            return False
        perms = ctx.author.guild_permissions
        return perms.administrator or perms.manage_guild or perms.moderate_members

    # ------------------------------------------------------------
    # Clear Befehl
    # ------------------------------------------------------------
    @commands.hybrid_command(name="clear", description="Löscht Nachrichten im Channel")
    async def clear(self, ctx: commands.Context, anzahl: int) -> None:
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)

        if anzahl < 1:
            msg = "⚠️ Bitte gib eine Zahl größer als 0 an."
            await (ctx.interaction.followup.send(msg, ephemeral=True)
                           if ctx.interaction else ctx.send(msg, delete_after=5))
            return

        if not isinstance(ctx.channel, discord.TextChannel):
            msg = "❌ Dieser Befehl funktioniert nur in Text-Channels."
            await (ctx.interaction.followup.send(msg, ephemeral=True)
                           if ctx.interaction else ctx.send(msg, delete_after=5))
            return

        deleted = await ctx.channel.purge(limit=anzahl)
        msg = f"🧹 Es wurden {len(deleted)} Nachrichten gelöscht."
        await (ctx.interaction.followup.send(msg, ephemeral=True)
               if ctx.interaction else ctx.send(msg, delete_after=5))

    @clear.error
    async def clear_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        msg = "🚫 Du hast keine Berechtigung oder es ist ein Fehler aufgetreten."
        if ctx.interaction:
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.send_message(msg, ephemeral=True)
            else:
                await ctx.interaction.followup.send(msg, ephemeral=True)
        else:
            await ctx.send(msg, delete_after=5)

    # ------------------------------------------------------------
    # User muten
    # ------------------------------------------------------------
    @commands.hybrid_command(name="mute", description="Setzt einen Benutzer auf Timeout")
    async def mute(self, ctx: commands.Context, member: discord.Member, minuten: int, *, reason: str) -> None:
        guild = ctx.guild
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            await ctx.send("❌ Du kannst keine Moderatoren/Admins muten.", ephemeral=True)
            return

        try:
            until = discord.utils.utcnow() + timedelta(minutes=minuten)
            await member.timeout(until, reason=reason)
            db_mod.add_timeout(str(member.id), str(guild.id), minuten, reason)
            await ctx.send(f"🔇 {member.mention} wurde für {minuten} Minuten gemutet.\nGrund: {reason}")
        except discord.Forbidden:
            await ctx.send("❌ Ich habe keine Berechtigung, diesen User zu muten.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.send(f"⚠️ Fehler beim Muten: {e}", ephemeral=True)

    # ------------------------------------------------------------
    # User verwarnen
    # ------------------------------------------------------------
    @commands.hybrid_command(name="warn", description="Verwarnt einen Benutzer")
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str) -> None:
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            await ctx.send("❌ Du kannst keine Moderatoren/Admins verwarnen.", ephemeral=True)
            return

        db_mod.add_warn(str(member.id), str(ctx.guild.id), reason)
        warns = db_mod.get_warns(str(member.id), str(ctx.guild.id), within_hours=24)

        await ctx.send(
            f"⚠️ {member.mention} wurde verwarnt.\nGrund: {reason}\n👉 Warnungen in 24h: **{len(warns)}**"
        )

        if len(warns) >= 2:
            try:
                until = discord.utils.utcnow() + timedelta(hours=24)
                await member.timeout(until, reason="Automatischer Timeout nach 2 Warnungen")
                db_mod.add_timeout(str(member.id), str(ctx.guild.id), 1440, "Automatischer Timeout nach 2 Warnungen")
                await ctx.send(f"🔇 {member.mention} wurde automatisch für 24 Stunden gemutet.")
            except discord.Forbidden:
                await ctx.send("❌ Keine Berechtigung für automatischen Timeout.", ephemeral=True)
            except discord.HTTPException as e:
                await ctx.send(f"⚠️ Fehler beim automatischen Timeout: {e}", ephemeral=True)

    # ------------------------------------------------------------
    # Verwarnungen des Users anzeigen
    # ------------------------------------------------------------
#-------------
# Sanktionen des Users anzeigen
#-------------
    @commands.hybrid_command(name="sanctions", description="Zeigt alle Sanktionen (Warns, Mutes, Bans) eines Benutzers an")
    @commands.check(lambda ctx: ctx.channel.id == 1428357460506443926) # Korrigierter Inline-Check
    async def sanctions(self, ctx: commands.Context, member: discord.Member) -> None:
        guild_id = str(ctx.guild.id)
        member_id = str(member.id)
        
        # 1. Daten abrufen (Annahme: Funktionen existieren und liefern [(timestamp, reason, info...), ...])
        warns = db_mod.get_warns(member_id, guild_id, within_hours=24) 
        timeouts = db_mod.get_timeouts(member_id, guild_id)
        bans = db_mod.get_bans(member_id, guild_id)
        
        all_sanctions = []

        # 2. Daten formatieren
        for timestamp, reason in warns:
            all_sanctions.append(
                (timestamp, "⚠️ Warn", reason)
            )
        
        for timestamp, duration, reason in timeouts:
            duration_str = str(timedelta(minutes=duration))
            all_sanctions.append(
                (timestamp, "🔇 Timeout", f"{reason} ({duration_str})")
            )
            
        for timestamp, reason in bans:
            all_sanctions.append(
                (timestamp, "🔨 Ban", reason)
            )

        # 3. Nach Zeitstempel sortieren
        all_sanctions.sort(key=lambda x: x[0], reverse=True)
        
        if not all_sanctions:
            await ctx.send(f"✅ {member.mention} hat keine aktiven Sanktionen.")
            return

        description = ""
        count_warns = 0
        
        for idx, (timestamp, type_emoji, reason_text) in enumerate(all_sanctions, start=1):
            dt = datetime.fromtimestamp(timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
            description += f"**{idx}.** {time_str} **{type_emoji}** - {reason_text}\n"
            
            if "Warn" in type_emoji:
                count_warns += 1


        embed = discord.Embed(
            title=f"🚨 Sanktionen für {member}",
            description=description,
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Gesamt-Warnungen (letzte 24h): {len(warns)}")
        await ctx.send(embed=embed)
        
    @sanctions.error
    async def sanctions_error(self, ctx: commands.Context, error: commands.CommandError):
        # Behandelt den Fehler, wenn der Check fehlschlägt (Commands.CheckFailure)
        if isinstance(error, commands.CheckFailure):
            # ID ist hier hartkodiert, um den Fehler zu vermeiden
            allowed_id = 1428357460506443926 
            msg = f"❌ Dieser Befehl kann nur im dafür vorgesehenen Channel (<#{allowed_id}>) ausgeführt werden."
        else:
            # Bei anderen Fehlern (z.B. fehlende Argumente)
            msg = f"🚫 Ein Fehler ist aufgetreten: {error}"
            
        if ctx.interaction:
            # Stellt sicher, dass die Interaction beantwortet wird
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.send_message(msg, ephemeral=True)
            else:
                await ctx.interaction.followup.send(msg, ephemeral=True)
        else:
            await ctx.send(msg, delete_after=5)


    # ------------------------------------------------------------
    # Verwarnungen des Users löschen
    # ------------------------------------------------------------
#-------------
# Verwarnungen des Users löschen
#-------------
    @commands.hybrid_command(name="clearwarns", description="Löscht alle Warnungen eines Benutzers")
    async def clearwarns(self, ctx: commands.Context, member: discord.Member) -> None:
        db_mod.clear_warns(str(member.id), str(ctx.guild.id))
        await ctx.send(f"🧹 Alle Warnungen für {member.mention} wurden gelöscht.")

    # ------------------------------------------------------------
    # User bannen
    # ------------------------------------------------------------
#-------------
# User bannen
#-------------
    @commands.hybrid_command(name="ban", description="Bannt einen Benutzer")
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str) -> None:
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            await ctx.send("❌ Du kannst keine Moderatoren/Admins bannen.", ephemeral=True)
            return

        try:
            await member.ban(reason=reason)
            db_mod.add_ban(str(member.id), str(ctx.guild.id), reason)
            await ctx.send(f"🔨 {member.mention} wurde gebannt.\nGrund: {reason}")
        except discord.Forbidden:
            await ctx.send("❌ Ich habe keine Berechtigung, diesen User zu bannen.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.send(f"⚠️ Fehler beim Bannen: {e}", ephemeral=True)

    # ------------------------------------------------------------
    # User entbannen
    # ------------------------------------------------------------
#-------------
# User entbannen
#-------------
    @commands.hybrid_command(name="unban", description="Entbannt einen Benutzer")
    async def unban(self, ctx: commands.Context, user: discord.User) -> None:
        try:
            await ctx.guild.unban(user)
            await ctx.send(f"✅ {user.mention} wurde entbannt.")
        except discord.Forbidden:
            await ctx.send("❌ Ich habe keine Berechtigung, diesen User zu entbannen.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.send(f"⚠️ Fehler beim Entbannen: {e}", ephemeral=True)


# ------------------------------------------------------------
# Setup Cog
# ------------------------------------------------------------
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))
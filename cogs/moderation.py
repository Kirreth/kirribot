import discord
from discord.ext import commands
from discord.ext.commands import Context
from datetime import timedelta, datetime
from utils.database import moderation as db_mod
from utils.database import guilds as db_guilds
from typing import Optional, Dict, Tuple, List

class Moderation(commands.Cog):
    """Bietet Moderationsbefehle wie Clear, Mute, Warn, Ban und Sanctions"""
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.sanction_channels: Dict[int, int] = {}

    async def cog_load(self) -> None:
        """Beim Laden die Sanctions-Channel-ID aus der DB holen"""
        for guild in self.bot.guilds:
            channel_id_str = db_mod.get_sanctions_channel(str(guild.id))
            if channel_id_str:
                self.ALLOWED_CHANNEL_ID = int(channel_id_str)
            else:
                print(f"❌ WARNUNG: Kein Sanctions-Channel für Server {guild.id} gefunden.")

    # ------------------------------------------------------------
    # Cog-weit: Nur Moderatoren/Admins dürfen Commands ausführen
    # ------------------------------------------------------------
    async def cog_check(self, ctx: Context):
        if not ctx.guild:
            return False
        perms = ctx.author.guild_permissions
        return perms.administrator or perms.manage_guild or perms.moderate_members

    # ------------------------------------------------------------
    # Clear Befehl
    # ------------------------------------------------------------
    @commands.hybrid_command(name="clear", description="Löscht Nachrichten im Channel")
    async def clear(self, ctx: Context, anzahl: int) -> None:
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
    async def clear_error(self, ctx: Context, error: commands.CommandError) -> None:
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
    async def mute(self, ctx: Context, member: discord.Member, minuten: int, *, reason: str) -> None:
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
    async def warn(self, ctx: Context, member: discord.Member, *, reason: str) -> None:
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
    # Sanktionen des Users anzeigen
    # ------------------------------------------------------------
    @commands.hybrid_command(name="sanctions", description="Zeigt alle Sanktionen eines Benutzers an")
    async def sanctions(self, ctx: Context, member: discord.Member) -> None:
        # Prüfen, ob der Befehl im erlaubten Channel ausgeführt wird
        if ctx.channel.id != self.ALLOWED_CHANNEL_ID:
            await ctx.send(f"❌ Dieser Befehl kann nur im Sanctions-Channel (<#{self.ALLOWED_CHANNEL_ID}>) verwendet werden.", ephemeral=True)
            return

        guild_id = str(ctx.guild.id)
        member_id = str(member.id)
        
        warns = db_mod.get_warns(member_id, guild_id, within_hours=24) 
        timeouts = db_mod.get_timeouts(member_id, guild_id)
        bans = db_mod.get_bans(member_id, guild_id)
        
        all_sanctions = []

        for timestamp, reason in warns:
            all_sanctions.append((timestamp, "⚠️ Warn", reason))
        
        for timestamp, duration, reason in timeouts:
            duration_str = str(timedelta(minutes=int(duration))) 
            all_sanctions.append((timestamp, "🔇 Timeout", f"{reason} ({duration_str})"))
            
        for timestamp, reason in bans:
            all_sanctions.append((timestamp, "🔨 Ban", reason))

        all_sanctions.sort(key=lambda x: x[0], reverse=True)
        
        if not all_sanctions:
            await ctx.send(f"✅ {member.mention} hat keine aktiven Sanktionen.")
            return

        description = ""
        for idx, (timestamp, type_emoji, reason_text) in enumerate(all_sanctions[:10], start=1):
            dt = datetime.fromtimestamp(timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
            description += f"**{idx}.** {time_str} **{type_emoji}** - {reason_text}\n"

        embed = discord.Embed(
            title=f"🚨 Letzte Sanktionen für {member}",
            description=description,
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Gesamt-Warnungen (letzte 24h): {len(warns)}")
        await ctx.send(embed=embed)

    # ------------------------------------------------------------
    # Setup Cog
    # ------------------------------------------------------------
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))

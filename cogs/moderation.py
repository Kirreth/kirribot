import discord
from discord.ext import commands
from datetime import timedelta
from utils import database as db

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="clear", description="Löscht Nachrichten im Channel")
    @commands.has_permissions(manage_messages=True)
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

        deleted = await ctx.channel.purge(limit=anzahl + 1)
        msg = f"🧹 Es wurden {len(deleted)} Nachrichten gelöscht."
        await (ctx.interaction.followup.send(msg, ephemeral=True)
               if ctx.interaction else ctx.send(msg, delete_after=5))

    @clear.error
    async def clear_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingPermissions):
            msg = "🚫 Du hast keine Berechtigung, Nachrichten zu löschen."
        else:
            msg = "⚠️ Es ist ein Fehler beim Ausführen von `clear` aufgetreten."

        if ctx.interaction:
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.send_message(msg, ephemeral=True)
            else:
                await ctx.interaction.followup.send(msg, ephemeral=True)
        else:
            await ctx.send(msg, delete_after=5)

    @commands.hybrid_command(name="mute", description="Setzt einen Benutzer auf Timeout")
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, minuten: int, *, reason: str) -> None:
        guild = ctx.guild
        if not guild:
            await ctx.send("❌ Fehler: Kein Guild-Context.", ephemeral=True)
            return

        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            await ctx.send("❌ Du kannst keine Moderatoren/Admins muten.", ephemeral=True)
            return

        try:
            until = discord.utils.utcnow() + timedelta(minutes=minuten)
            await member.timeout(until, reason=reason)
            db.add_timeout(str(member.id), str(guild.id), minuten, reason)
            await ctx.send(f"🔇 {member.mention} wurde für {minuten} Minuten gemutet.\nGrund: {reason}")
        except discord.Forbidden:
            await ctx.send("❌ Ich habe keine Berechtigung, diesen User zu muten.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.send(f"⚠️ Fehler beim Muten: {e}", ephemeral=True)

    @commands.hybrid_command(name="warn", description="Verwarnt einen Benutzer")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str) -> None:
        guild = ctx.guild
        if not guild:
            await ctx.send("❌ Fehler: Kein Guild-Context.", ephemeral=True)
            return

        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            await ctx.send("❌ Du kannst keine Moderatoren/Admins verwarnen.", ephemeral=True)
            return

        db.add_warn(str(member.id), str(guild.id), reason)
        warns = db.get_warns(str(member.id), str(guild.id), within_hours=24)

        await ctx.send(
            f"⚠️ {member.mention} wurde verwarnt.\nGrund: {reason}\n👉 Warnungen in 24h: **{len(warns)}**"
        )

        if len(warns) >= 2:
            try:
                until = discord.utils.utcnow() + timedelta(hours=24)
                await member.timeout(until, reason="Automatischer Timeout nach 2 Warnungen")
                db.add_timeout(str(member.id), str(guild.id), 1440, "Automatischer Timeout nach 2 Warnungen")
                await ctx.send(f"🔇 {member.mention} wurde automatisch für 24 Stunden gemutet.")
            except discord.Forbidden:
                await ctx.send("❌ Keine Berechtigung für automatischen Timeout.", ephemeral=True)
            except discord.HTTPException as e:
                await ctx.send(f"⚠️ Fehler beim automatischen Timeout: {e}", ephemeral=True)

    @commands.hybrid_command(name="ban", description="Bannt einen Benutzer")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str) -> None:
        guild = ctx.guild
        if not guild:
            await ctx.send("❌ Fehler: Kein Guild-Context.", ephemeral=True)
            return

        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            await ctx.send("❌ Du kannst keine Moderatoren/Admins bannen.", ephemeral=True)
            return

        try:
            await member.ban(reason=reason)
            db.add_ban(str(member.id), str(guild.id), reason)
            await ctx.send(f"🔨 {member.mention} wurde gebannt.\nGrund: {reason}")
        except discord.Forbidden:
            await ctx.send("❌ Ich habe keine Berechtigung, diesen User zu bannen.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.send(f"⚠️ Fehler beim Bannen: {e}", ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))

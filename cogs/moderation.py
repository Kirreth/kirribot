import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from datetime import timedelta
from utils import database as db
from typing import Optional


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------ CLEAR ------------------
    @commands.hybrid_command(
        name="clear",
        description="Löscht die angegebene Anzahl an Nachrichten im aktuellen Kanal"
    )
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: Context, anzahl: int) -> None:
        if anzahl <= 0:
            await ctx.send("❌ Bitte gib eine gültige Anzahl größer als 0 an.", ephemeral=True)
            return

        deleted = await ctx.channel.purge(limit=anzahl + 1)
        await ctx.send(f"🧹 Es wurden {len(deleted) - 1} Nachrichten gelöscht.", delete_after=5)

    @clear.error
    async def clear_error(self, ctx: Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Du hast keine Berechtigung, Nachrichten zu löschen.", ephemeral=True)
        else:
            await ctx.send("⚠️ Es ist ein Fehler beim Ausführen von `clear` aufgetreten.", ephemeral=True)

    # ------------------ MUTE ------------------
    @app_commands.command(name="mute", description="Setzt einen Benutzer auf Timeout")
    @app_commands.describe(
        member="Der Benutzer, der gemutet werden soll",
        minuten="Dauer in Minuten",
        reason="Grund"
    )
    async def mute(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        minuten: int,
        reason: str
    ) -> None:
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("❌ Fehler: Kein Guild-Context.", ephemeral=True)
            return

        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ Du kannst keine Moderatoren/Admins muten.", ephemeral=True)
            return

        try:
            until = discord.utils.utcnow() + timedelta(minutes=minuten)
            await member.timeout(until, reason=reason)
            db.add_timeout(str(member.id), str(guild.id), minuten, reason)
            await interaction.response.send_message(
                f"🔇 {member.mention} wurde für {minuten} Minuten gemutet.\nGrund: {reason}"
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ Ich habe keine Berechtigung, diesen User zu muten.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"⚠️ Fehler beim Muten: {e}", ephemeral=True)

    # ------------------ WARN ------------------
    @app_commands.command(name="warn", description="Verwarnt einen Benutzer")
    @app_commands.describe(member="Der Benutzer, der verwarnt werden soll", reason="Grund")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("❌ Fehler: Kein Guild-Context.", ephemeral=True)
            return

        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ Du kannst keine Moderatoren/Admins verwarnen.", ephemeral=True)
            return

        db.add_warn(str(member.id), str(guild.id), reason)
        warns = db.get_warns(str(member.id), str(guild.id), within_hours=24)
        await interaction.response.send_message(
            f"⚠️ {member.mention} wurde verwarnt.\nGrund: {reason}\n👉 Warnungen in 24h: **{len(warns)}**"
        )

        if len(warns) >= 2:
            try:
                until = discord.utils.utcnow() + timedelta(hours=24)
                await member.timeout(until, reason="Automatischer Timeout nach 2 Warnungen")
                db.add_timeout(str(member.id), str(guild.id), 1440, "Automatischer Timeout nach 2 Warnungen")
                await interaction.followup.send(f"🔇 {member.mention} wurde automatisch für 24 Stunden gemutet.")
            except discord.Forbidden:
                await interaction.followup.send("❌ Keine Berechtigung für automatischen Timeout.", ephemeral=True)
            except discord.HTTPException as e:
                await interaction.followup.send(f"⚠️ Fehler beim automatischen Timeout: {e}", ephemeral=True)

    # ------------------ BAN ------------------
    @app_commands.command(name="ban", description="Bannt einen Benutzer")
    @app_commands.describe(member="Der Benutzer, der gebannt werden soll", reason="Grund")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("❌ Fehler: Kein Guild-Context.", ephemeral=True)
            return

        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ Du kannst keine Moderatoren/Admins bannen.", ephemeral=True)
            return

        try:
            await member.ban(reason=reason)
            db.add_ban(str(member.id), str(guild.id), reason)
            await interaction.response.send_message(f"🔨 {member.mention} wurde gebannt.\nGrund: {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ Ich habe keine Berechtigung, diesen User zu bannen.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"⚠️ Fehler beim Bannen: {e}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))

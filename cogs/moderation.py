import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
from utils import database as db
from typing import Optional

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="mute", description="Setzt einen Benutzer auf Timeout")
    @app_commands.describe(member="Der Benutzer, der gemutet werden soll", minuten="Dauer in Minuten", reason="Grund")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, minuten: int, reason: str) -> None:
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Fehler: Kein Guild-Context.", ephemeral=True)
            return

        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            await interaction.response.send_message("Du kannst keine Moderatoren/Admins muten.", ephemeral=True)
            return

        try:
            await member.timeout(discord.utils.utcnow() + timedelta(minutes=minuten), reason=reason)
            db.add_timeout(str(member.id), str(guild.id), minuten, reason)
            await interaction.response.send_message(f"{member.mention} wurde für {minuten} Minuten gemutet. Grund: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"Fehler beim Muten: {e}", ephemeral=True)

    @app_commands.command(name="warn", description="Verwarnt einen Benutzer")
    @app_commands.describe(member="Der Benutzer, der verwarnt werden soll", reason="Grund")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Fehler: Kein Guild-Context.", ephemeral=True)
            return

        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            await interaction.response.send_message("Du kannst keine Moderatoren/Admins verwarnen.", ephemeral=True)
            return

        db.add_warn(str(member.id), str(guild.id), reason)
        warns = db.get_warns(str(member.id), str(guild.id), within_hours=24)
        await interaction.response.send_message(
            f"{member.mention} wurde verwarnt. Grund: {reason} (Warnungen in 24h: {len(warns)})"
        )

        if len(warns) >= 2:
            try:
                await member.timeout(discord.utils.utcnow() + timedelta(hours=24), reason="Automatischer Timeout nach 2 Warnungen")
                db.add_timeout(str(member.id), str(guild.id), 1440, "Automatischer Timeout nach 2 Warnungen")
                await interaction.followup.send(f"{member.mention} wurde automatisch für 24 Stunden gemutet.")
            except Exception as e:
                await interaction.followup.send(f"Fehler beim automatischen Timeout: {e}", ephemeral=True)

    @app_commands.command(name="ban", description="Bannt einen Benutzer")
    @app_commands.describe(member="Der Benutzer, der gebannt werden soll", reason="Grund")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Fehler: Kein Guild-Context.", ephemeral=True)
            return

        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            await interaction.response.send_message("Du kannst keine Moderatoren/Admins bannen.", ephemeral=True)
            return

        try:
            await member.ban(reason=reason)
            db.add_ban(str(member.id), str(guild.id), reason)
            await interaction.response.send_message(f"{member.mention} wurde gebannt. Grund: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"Fehler beim Bannen: {e}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))

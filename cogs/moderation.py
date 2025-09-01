import discord
from discord.ext import commands
from discord import app_commands
from utils import database
from typing import Any


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    # --- Mute / Timeout ---
    @app_commands.command(name="mute", description="Setzt einen Benutzer auf Timeout")
    @app_commands.describe(
        member="Der Benutzer, der gemutet werden soll",
        minuten="Dauer in Minuten",
        reason="Grund",
    )
    async def mute(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        minuten: int,
        reason: str,
    ) -> None:
        """Setzt einen Benutzer in den Timeout (Mute)."""
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "Du kannst keine Moderatoren/Admins muten.", ephemeral=True
            )
            return

        try:
            await member.timeout(
                discord.utils.utcnow() + discord.timedelta(minutes=minuten),
                reason=reason,
            )
            database.add_timeout(member.id, interaction.guild.id, minuten, reason)
            await interaction.response.send_message(
                f"{member.mention} wurde für {minuten} Minuten gemutet. Grund: {reason}"
            )
        except Exception as e:
            await interaction.response.send_message(
                f"Fehler beim Muten: {e}", ephemeral=True
            )

    # --- Warn ---
    @app_commands.command(name="warn", description="Verwarnt einen Benutzer")
    @app_commands.describe(
        member="Der Benutzer, der verwarnt werden soll", reason="Grund"
    )
    async def warn(
        self, interaction: discord.Interaction, member: discord.Member, reason: str
    ) -> None:
        """Verwarnt einen Benutzer. 2 Verwarnungen in 24h -> automatischer Timeout."""
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "Du kannst keine Moderatoren/Admins verwarnen.", ephemeral=True
            )
            return

        database.add_warn(member.id, interaction.guild.id, reason)
        warns = database.get_warns(member.id, interaction.guild.id, within_hours=24)

        await interaction.response.send_message(
            f"{member.mention} wurde verwarnt. Grund: {reason} (Warnungen in 24h: {len(warns)})"
        )

        if len(warns) >= 2:
            try:
                await member.timeout(
                    discord.utils.utcnow() + discord.timedelta(hours=24),
                    reason="Automatischer Timeout nach 2 Warnungen",
                )
                database.add_timeout(
                    member.id,
                    interaction.guild.id,
                    1440,
                    "Automatischer Timeout nach 2 Warnungen",
                )
                await interaction.followup.send(
                    f"{member.mention} wurde automatisch für 24 Stunden gemutet wegen 2 Warnungen innerhalb von 24 Stunden."
                )
            except Exception as e:
                await interaction.followup.send(
                    f"Fehler beim automatischen Timeout: {e}", ephemeral=True
                )

    # --- Ban ---
    @app_commands.command(name="ban", description="Bannt einen Benutzer")
    @app_commands.describe(member="Der Benutzer, der gebannt werden soll", reason="Grund")
    async def ban(
        self, interaction: discord.Interaction, member: discord.Member, reason: str
    ) -> None:
        """Bannt einen Benutzer."""
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "Du kannst keine Moderatoren/Admins bannen.", ephemeral=True
            )
            return

        try:
            await member.ban(reason=reason)
            database.add_ban(member.id, interaction.guild.id, reason)
            await interaction.response.send_message(
                f"{member.mention} wurde gebannt. Grund: {reason}"
            )
        except Exception as e:
            await interaction.response.send_message(
                f"Fehler beim Bannen: {e}", ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    """Registriert das Moderation-Cog beim Bot."""
    await bot.add_cog(Moderation(bot))

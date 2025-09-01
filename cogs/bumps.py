import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from utils import database as db
from typing import Optional

# Feste ID des Disboard-Bots
DISBOARD_ID: int = 302050872383242240


class Bumps(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Lauscht auf Disboard-Bot-Nachrichten und speichert Bumps."""
        if message.author.id != DISBOARD_ID:
            return

        if "Bump done" in message.content or "Bump erfolgreich" in message.content:
            if message.interaction and message.interaction.user:
                bumper: discord.User = message.interaction.user
            else:
                return

            db.log_bump(bumper.id, datetime.utcnow())
            print(f"✅ Bump von {bumper} gespeichert")

    @app_commands.command(name="topb", description="Zeigt die gesamte Anzahl an Bumps eines Users")
    async def topb(
        self, interaction: discord.Interaction, user: Optional[discord.User] = None
    ) -> None:
        """Zeigt die gesamte Anzahl an Bumps eines Users."""
        user = user or interaction.user
        count: int = db.get_bumps_total(user.id)
        await interaction.response.send_message(
            f"📈 {user.mention} hat insgesamt **{count} Bumps** gemacht."
        )

    @app_commands.command(
        name="topmb", description="Zeigt die Anzahl an Bumps der letzten 30 Tage"
    )
    async def topmb(
        self, interaction: discord.Interaction, user: Optional[discord.User] = None
    ) -> None:
        """Zeigt die Anzahl an Bumps eines Users innerhalb der letzten 30 Tage."""
        user = user or interaction.user
        count: int = db.get_bumps_30d(user.id)
        await interaction.response.send_message(
            f"⏳ {user.mention} hat in den letzten 30 Tagen **{count} Bumps** gemacht."
        )


async def setup(bot: commands.Bot) -> None:
    """Registriert das Bumps-Cog beim Bot."""
    await bot.add_cog(Bumps(bot))

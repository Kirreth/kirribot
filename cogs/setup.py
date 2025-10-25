# cogs/setup.py
import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Union
from utils.database import birthday as birthday_db
from utils.database import roles as roles_db

class Setup(commands.Cog):
    """Bietet eine zentrale Oberfläche, um alle wichtigen Channel und Rollen zu konfigurieren."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------
    # Hauptbefehlsgruppe: /setup
    # ------------------------------------------------------------
    
    @commands.hybrid_group(
        name="setup", 
        description="Konfiguriere alle wichtigen Channel und Rollen des Bots."
    )
    @commands.guild_only() 
    @commands.has_permissions(administrator=True) 
    async def setup(self, ctx: Context) -> None:
        """Der Hauptbefehl, der bei Aufruf ohne Subcommand eine kurze Hilfe anzeigt."""
        
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="⚙️ Bot-Konfiguration",
                description=(
                    "Bitte verwende einen der folgenden Unterbefehle, um Einstellungen vorzunehmen:\n\n"
                    "• `/setup channel` - Konfiguriert Channels (Geburtstage etc.)\n"
                    "• `/setup role` - Konfiguriert spezielle Rollen (Bumper-Rolle etc.)\n"
                ),
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed, ephemeral=True)


    # ------------------------------------------------------------
    # Untergruppe: /setup channel
    # ------------------------------------------------------------
    
    @setup.group(
        name="channel", 
        description="Konfiguriert Kanäle für Geburtstage, Logs etc."
    )
    async def setup_channel(self, ctx: Context) -> None:
        """Gruppenbefehl für Channel-Setups."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Bitte verwende `/setup channel <birthday/log>`", ephemeral=True)


    @setup_channel.command(
        name="birthday", 
        description="Setzt den Channel für Geburtstagsnachrichten."
    )
    async def channel_birthday(self, ctx: Context, channel: Union[discord.TextChannel, None]) -> None:
        """Setzt den Kanal, in dem Geburtstagsglückwünsche gepostet werden."""
        
        if channel is None:
            birthday_db.set_birthday_channel(str(ctx.guild.id), None)
            await ctx.send("✅ Der **Geburtstags-Channel** wurde erfolgreich entfernt.", ephemeral=True)
        else:
            birthday_db.set_birthday_channel(str(ctx.guild.id), str(channel.id))
            await ctx.send(f"✅ Der **Geburtstags-Channel** wurde auf {channel.mention} gesetzt.", ephemeral=True)


    # ------------------------------------------------------------
    # Untergruppe: /setup role
    # ------------------------------------------------------------

    @setup.group(
        name="role", 
        description="Konfiguriert Rollen wie die Bumper-Rolle."
    )
    async def setup_role(self, ctx: Context) -> None:
        """Gruppenbefehl für Rollen-Setups."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Bitte verwende `/setup role <bumper>`", ephemeral=True)


    @setup_role.command(
        name="bumper", 
        description="Setzt die Rolle, die nach einem Bump zugewiesen wird (oder entfernt sie)."
    )
    async def role_bumper(self, ctx: Context, role: Union[discord.Role, None]) -> None:
        """Setzt die Bumper-Rolle für den Server."""
        
        if role is None:
            roles_db.set_bumper_role(str(ctx.guild.id), None)
            await ctx.send("✅ Die **Bumper-Rolle** wurde erfolgreich entfernt.", ephemeral=True)
        else:
            roles_db.set_bumper_role(str(ctx.guild.id), str(role.id))
            await ctx.send(f"✅ Die **Bumper-Rolle** wurde auf {role.mention} gesetzt.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Setup(bot))
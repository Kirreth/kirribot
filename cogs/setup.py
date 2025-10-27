# cogs/setup.py
import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Union
from utils.database import birthday as birthday_db
from utils.database import moderation as mod_db
from utils.database import roles as roles_db
from utils.database import bumps as db_bumps

class Setup(commands.Cog):
    """Zentrale Oberfläche für die Konfiguration von Channels und Rollen."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------
    # Hauptbefehlsgruppe
    # ------------------------------------------------------------
    
    @commands.hybrid_group(
        name="setup", 
        description="Konfiguriere alle wichtigen Channel und Rollen des Bots."
    )
    @commands.guild_only() 
    @commands.has_permissions(administrator=True) 
    async def setup(self, ctx: Context) -> None:
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="⚙️ Bot-Konfiguration",
                description=(
                    "Bitte verwende einen Unterbefehl:\n\n"
                    "• `/setup channel` - Konfiguriert Channels (Birthday, Sanctions)\n"
                    "• `/setup role` - Konfiguriert spezielle Rollen (Bumper-Rolle)"
                ),
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed, ephemeral=True)

    # ------------------------------------------------------------
    # Channels
    # ------------------------------------------------------------
    
    @setup.group(
        name="channel", 
        description="Konfiguriert Channels für Geburtstage und Moderation."
    )
    async def setup_channel(self, ctx: Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send("Bitte verwende `/setup channel <birthday/sanctions>`", ephemeral=True)

    # Birthday-Channel
    @setup_channel.command(
        name="birthday",
        description="Setzt den Channel für Geburtstagsnachrichten."
    )
    async def channel_birthday(self, ctx: Context, channel: Union[discord.TextChannel, None]) -> None:
        if channel is None:
            birthday_db.set_birthday_channel(str(ctx.guild.id), None)
            await ctx.send("✅ Der Geburtstags-Channel wurde entfernt.", ephemeral=True)
        else:
            birthday_db.set_birthday_channel(str(ctx.guild.id), str(channel.id))
            await ctx.send(f"✅ Geburtstags-Channel gesetzt auf {channel.mention}", ephemeral=True)

    # Sanctions-Channel
    @setup_channel.command(
        name="sanctions",
        description="Setzt den Channel für Sanctions/Mod-Logs."
    )
    async def channel_sanctions(self, ctx: Context, channel: Union[discord.TextChannel, None]) -> None:
        if channel is None:
            mod_db.set_sanctions_channel(str(ctx.guild.id), None)
            await ctx.send("✅ Der Sanctions-Channel wurde entfernt.", ephemeral=True)
        else:
            mod_db.set_sanctions_channel(str(ctx.guild.id), str(channel.id))
            await ctx.send(f"✅ Sanctions-Channel gesetzt auf {channel.mention}", ephemeral=True)

    # Bump-Reminder-Channel
    @setup_channel.command(
        name="reminder",
        description="Setzt den Channel für Bump-Erinnerungen."
    )
    async def channel_reminder(self, ctx: Context, channel: Union[discord.TextChannel, None]) -> None:
        if channel is None:
            db_bumps.set_reminder_channel(str(ctx.guild.id), None)
            await ctx.send("✅ Bump-Reminder-Channel entfernt.", ephemeral=True)
        else:
            db_bumps.set_reminder_channel(str(ctx.guild.id), str(channel.id))
            await ctx.send(f"✅ Bump-Reminder-Channel gesetzt auf {channel.mention}", ephemeral=True)


    # ------------------------------------------------------------
    # Rollen
    # ------------------------------------------------------------
    
    @setup.group(
        name="role",
        description="Konfiguriert Rollen wie die Bumper-Rolle."
    )
    async def setup_role(self, ctx: Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send("Bitte verwende `/setup role <bumper>`", ephemeral=True)

    @setup_role.command(
        name="bumper",
        description="Setzt die Rolle, die nach einem Bump vergeben wird."
    )
    async def role_bumper(self, ctx: Context, role: Union[discord.Role, None]) -> None:
        if role is None:
            roles_db.set_bumper_role(str(ctx.guild.id), None)
            await ctx.send("✅ Bumper-Rolle entfernt.", ephemeral=True)
        else:
            roles_db.set_bumper_role(str(ctx.guild.id), str(role.id))
            await ctx.send(f"✅ Bumper-Rolle gesetzt auf {role.mention}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Setup(bot))

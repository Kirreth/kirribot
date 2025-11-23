import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Optional
from utils.database import custom_commands as db_commands  # DB-Handler für dynamische Commands
from utils.database import guilds as db_guilds


class CustomCommands(commands.Cog):
    """Ermöglicht Admins, eigene Commands für den Server zu erstellen und zu verwalten."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------------------------------------------------
    # Command: Eigenen Custom Command hinzufügen
    # ------------------------------------------------------------
    @commands.hybrid_command(
        name="addcommand",
        description="Erstellt einen eigenen Server-Command",
        with_app_command=True
    )
    async def add_command(self, ctx: Context, command_name: str, *, response: str):
        """Speichert einen neuen Custom Command für den Server"""
        if ctx.guild is None:
            await ctx.send("❌ Dieser Befehl kann nur in einem Server verwendet werden.", ephemeral=True)
            return
        
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Nur Admins können eigene Commands erstellen.", ephemeral=True)
            return
        
        if not command_name.isalnum():
            await ctx.send("❌ Der Command darf nur aus Buchstaben und Zahlen bestehen.", ephemeral=True)
            return
        
        db_commands.add_command(str(ctx.guild.id), command_name.lower(), response)
        await ctx.send(f"✅ Custom Command `{command_name}` wurde hinzugefügt!", ephemeral=True)

    # ------------------------------------------------------------
    # Command: Eigenen Custom Command entfernen
    # ------------------------------------------------------------
    @commands.hybrid_command(
        name="removecommand",
        description="Entfernt einen eigenen Server-Command",
        with_app_command=True
    )
    async def remove_command(self, ctx: Context, command_name: str):
        if ctx.guild is None:
            await ctx.send("❌ Dieser Befehl kann nur in einem Server verwendet werden.", ephemeral=True)
            return

        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Nur Admins können Commands entfernen.", ephemeral=True)
            return
        
        removed = db_commands.remove_command(str(ctx.guild.id), command_name.lower())
        if removed:
            await ctx.send(f"✅ Custom Command `!{command_name}` wurde entfernt!", ephemeral=True)
        else:
            await ctx.send(f"❌ Custom Command `!{command_name}` existiert nicht.", ephemeral=True)

    # ------------------------------------------------------------
    # Message Listener: Dynamische Commands ausführen
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        guild_id = str(message.guild.id)
        prefix = db_guilds.get_prefix(guild_id) or "!"  # Fallback

        # Damit andere Commands weiterhin funktionieren
        await self.bot.process_commands(message)

        content = message.content.strip()
        if not content.startswith(prefix):
            return

        cmd_name = content[len(prefix):].split()[0].lower()

        cmd_data = db_commands.get_command(guild_id, cmd_name)
        if cmd_data:
            response = cmd_data["response"].replace("{user}", message.author.mention)
            await message.channel.send(response)



# ------------------------------------------------------------
# Cog Setup
# ------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(CustomCommands(bot))

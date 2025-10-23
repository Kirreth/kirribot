# cogs/roles.py
import discord
from discord.ext import commands
from discord.ext.commands import Context
from utils import database as db
from typing import Optional

class Roles(commands.Cog):
    """Verwaltet Rollenbefehle wie das Setzen und Entfernen der Bumper-Rolle"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

# ------------------------------------------------------------
# Bumper Rolle setzen (und entfernen)
# ------------------------------------------------------------

    @commands.hybrid_command(
        name="setbumber", 
        description="Setzt die Bumper-Rolle für den Server. Lasse die Rolle weg, um sie zu entfernen."
    )
    @commands.has_permissions(administrator=True)
    async def setbumber(self, ctx: Context[commands.Bot], role: Optional[discord.Role] = None) -> None:
        
        # 🚩 KORREKTUR 1: Blockiere Ausführung in DMs, da ctx.guild benötigt wird.
        if ctx.guild is None:
            await ctx.send("Dieser Befehl kann nur auf einem Server ausgeführt werden.", ephemeral=True)
            return
            
        guild_id: str = str(ctx.guild.id)
        role_id: Optional[str] = str(role.id) if role else None

        # Die Datenbankfunktion db.set_bumper_role übernimmt die Speicherung
        # der guild_id und der optionalen role_id.
        db.set_bumper_role(guild_id, role_id)

        if role:
            await ctx.send(f"✅ Die Bumper-Rolle wurde auf {role.mention} gesetzt.")
        else:
            await ctx.send("✅ Die Bumper-Rolle wurde entfernt.")

# ------------------------------------------------------------
# 🚩 ENTFERNT: Der delbumber Befehl ist redundant, da setbumber(role=None) 
# denselben Zweck erfüllt.
# ------------------------------------------------------------

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Roles(bot))
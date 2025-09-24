import discord
from discord.ext import commands
from discord.ext.commands import Context
from utils import database as db
from typing import Optional

class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="setbumber", description="Setzt die Bumper-Rolle für den Server")
    @commands.has_permissions(administrator=True)
    async def setbumber(self, ctx: Context[commands.Bot], role: Optional[discord.Role] = None) -> None:
        """Setzt die Rolle, die für das Bumpen vergeben wird. Ohne Angabe wird die Rolle entfernt."""
        guild_id: str = str(ctx.guild.id) if ctx.guild else "0"
        role_id: Optional[str] = str(role.id) if role else None

        db.set_bumper_role(guild_id, role_id)

        if role:
            await ctx.send(f"✅ Die Bumper-Rolle wurde auf {role.mention} gesetzt.")
        else:
            await ctx.send("✅ Die Bumper-Rolle wurde entfernt.")

    @commands.hybrid_command(name="delbumber", description="Entfernt die Bumper-Rolle für den Server")
    @commands.has_permissions(administrator=True)
    async def delbumber(self, ctx: Context[commands.Bot]) -> None:
        """Entfernt die aktuell gesetzte Bumper-Rolle."""
        guild_id: str = str(ctx.guild.id) if ctx.guild else "0"

        db.set_bumper_role(guild_id, None)
        await ctx.send("✅ Die Bumper-Rolle wurde entfernt.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Roles(bot))
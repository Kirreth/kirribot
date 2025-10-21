import discord
from discord.ext import commands
import random

class Metafrage(commands.Cog):
    """Metafrage Command"""

    DEFINITIONS = [
        "Eine Metafrage ist eine Frage über Fragen, die hilft, das eigentliche Problem besser zu verstehen.",
        "Metafragen analysieren die Art der gestellten Fragen und deren Ziel.",
        "Mit einer Metafrage kann man Klarheit über unklare oder komplexe Fragestellungen gewinnen.",
        "Metafragen zeigen auf, warum eine Frage gestellt wird und was genau gesucht wird."
    ]

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="metafrage", description="Zeigt eine zufällige Definition einer Metafrage")
    async def metafrage(self, ctx: commands.Context):
        definition = random.choice(self.DEFINITIONS)
        embed = discord.Embed(
            title="ℹ️ Metafrage",
            description=definition,
            color=discord.Color.blurple()
        )
        embed.add_field(name="Mehr Infos", value="[Metafrage.de](https://metafrage.de/)", inline=False)
        embed.set_footer(text="ℹ️ Jede Definition stammt aus verschiedenen Quellen über Metafragen.")

        await ctx.send(embed=embed)

# Cog Setup
async def setup(bot: commands.Bot):
    await bot.add_cog(Metafrage(bot))

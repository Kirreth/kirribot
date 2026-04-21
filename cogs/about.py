# cogs/help.py
import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Optional

class About(commands.Cog):
    """Zeigt Informationen über das Bot-System an"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

# ------------------------------------------------------------
# Über Kirribot 
# ------------------------------------------------------------

    @commands.hybrid_command(
        name="about",
        description="Zeigt Informationen über das Bot-System an."
    )
    async def about(
        self,
        ctx: Context[commands.Bot]
    ) -> None:
        embed = discord.Embed(
            title="Über Kirribot",
            description=(
                "Kirribot ist ein vielseitiger Discord-Bot, der entwickelt wurde, um Servern mit einer Vielzahl von Funktionen zu helfen. "
                "Von der Verwaltung von Geburtstagen bis hin zur Bereitstellung von Informationen über Benutzer – Kirribot ist hier, um deinen Server zu unterstützen!"
            ),
            color=discord.Color.green()
        )
        embed.add_field(name="Entwickler", value="Kirreth", inline=False)
        embed.add_field(name="Version", value="0.9.78", inline=False)
        embed.add_field(name="Funktionen", value=(
            "- Geburtstagsverwaltung\n"
            "- Benutzerinformationen\n"
            "- Levelsystem\n"
            "- Quizspiele\n"
            "- Bump- und Begrüßungsnachrichten\n"
            "- Selfcommand-Unterstützung\n"
            "- Links zu nützlichen Ressourcen\n"
            "- Umwandlung von Musiklinks\n"
            "- Und vieles mehr!"
        ), inline=False)
        embed.add_field(name="Support", value=(
            "Bei Fragen oder Problemen kannst du dich gerne an den Entwickler wenden:\n"
            "Besuche das [Dashboard](https://kirribot.kirreth.de)"), inline=False)
        embed.set_footer(text="Vielen Dank, dass du Kirribot verwendest!")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(About(bot))
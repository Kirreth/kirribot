# cogs/help.py
import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Optional

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="help",
        description="Zeigt alle Kategorien oder die Befehle einer Kategorie an."
    )
    async def help(
        self,
        ctx: Context[commands.Bot],
        category: Optional[str] = None
    ) -> None:
        """
        /help           -> zeigt nur Kategorien
        /help user      -> Befehle aus Info & Leveling
        /help staff     -> Befehle aus Moderation
        /help roles     -> Befehle aus Rollen-Management
        """
        category = category.lower() if category else None
        embed = discord.Embed(color=discord.Color.green())

        if category is None:
            embed.title = "Hilfe – Kategorien"
            embed.description = (
                "Verwende `/help <kategorie>` für Details.\n\n"
                "**user** – Befehle aus Info & Leveling\n"
                "**staff** – Befehle aus Moderation\n"
                "**roles** – Befehle für Rollenverwaltung"
            )

        elif category == "user":
            embed.title = "User-Befehle"
            for cmd in self.bot.commands:
                if cmd.cog_name in {"Info", "Leveling"}:
                    embed.add_field(
                        name=f"/{cmd.name}",
                        value=cmd.help or "Keine Beschreibung",
                        inline=False
                    )

        elif category == "staff":
            embed.title = "Staff-Befehle"
            for cmd in self.bot.commands:
                if cmd.cog_name == "Moderation":
                    embed.add_field(
                        name=f"/{cmd.name}",
                        value=cmd.help or "Keine Beschreibung",
                        inline=False
                    )

        elif category == "roles":
            embed.title = "Rollen-Befehle"
            for cmd in self.bot.commands:
                if cmd.cog_name == "Roles":
                    embed.add_field(
                        name=f"/{cmd.name}",
                        value=cmd.help or "Keine Beschreibung",
                        inline=False
                    )

        else:
            embed.title = "Unbekannte Kategorie"
            embed.description = "Verfügbare Kategorien: **user**, **staff**, **roles**"

        # Antwort senden
        if ctx.interaction:
            await ctx.reply(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))

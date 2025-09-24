import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Optional, Union

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Hybrid-Befehl: !help und /help in einem
    @commands.hybrid_command(
        name="help",
        description="Zeigt eine Übersicht aller Befehle oder Details zu einem bestimmten Befehl."
    )
    async def help(
        self,
        ctx: Context[commands.Bot],
        command_name: Optional[str] = None
    ) -> None:
        """
        Zeigt alle Befehle an oder Infos zu einem einzelnen Befehl.
        Funktioniert als Prefix-Command (!help) und Slash-Command (/help).
        """
        if command_name:
            command = self.bot.get_command(command_name)
            if command:
                embed = discord.Embed(
                    title=f"Hilfe: {command_name}",
                    description=command.help or "Keine Beschreibung verfügbar.",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="Fehler",
                    description="Befehl nicht gefunden.",
                    color=discord.Color.red()
                )
        else:
            embed = discord.Embed(
                title="Hilfe Übersicht",
                description="Liste aller Befehle:",
                color=discord.Color.green()
            )
            for cmd in self.bot.commands:
                if not cmd.hidden:
                    embed.add_field(
                        name=cmd.name,
                        value=cmd.help or "Keine Beschreibung",
                        inline=False
                    )

        # ctx.reply funktioniert für Prefix & Slash gleichermaßen
        await ctx.reply(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))

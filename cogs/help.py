import discord
from discord.ext import commands

class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, command_name=None):
        if command_name:
            command = self.bot.get_command(command_name)
            if command:
                embed = discord.Embed(
                    title=f"Hilfe: {command_name}",
                    description=command.help or "Keine Beschreibung verfügbar",
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
            for command in self.bot.commands:
                embed.add_field(name=command.name, value=command.help or "Keine Beschreibung", inline=False)

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(HelpCommands(bot))

import os
import discord
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv


load_dotenv()

class MessageLogger(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Channel-ID aus der .env laden
        self.log_channel_id = int(os.getenv("LOG_CHANNEL_ID", 0))

    def get_log_channel(self, guild: discord.Guild):
        return guild.get_channel(self.log_channel_id)

# ------------------------------------------------------------
# Bearbeitete Nachrichten prüfen
# ------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return  # Bots ignorieren

        if before.content == after.content:
            return  # Kein Text geändert

        log_channel = self.get_log_channel(before.guild)
        if not log_channel:
            return

        embed = discord.Embed(
            title="✏️ Nachricht bearbeitet",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Autor", value=before.author.mention, inline=True)
        embed.add_field(name="Kanal", value=before.channel.mention, inline=True)
        embed.add_field(name="Vorher", value=before.content or "*leer*", inline=False)
        embed.add_field(name="Nachher", value=after.content or "*leer*", inline=False)
        embed.timestamp = discord.utils.utcnow()

        await log_channel.send(embed=embed)

# ------------------------------------------------------------
# Gelöschte Nachrichten prüfen
# ------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        log_channel = self.get_log_channel(message.guild)
        if not log_channel:
            return

        embed = discord.Embed(
            title="🗑️ Nachricht gelöscht",
            color=discord.Color.red()
        )
        embed.add_field(name="Autor", value=message.author.mention, inline=True)
        embed.add_field(name="Kanal", value=message.channel.mention, inline=True)
        embed.add_field(name="Nachricht", value=message.content or "*leer*", inline=False)
        embed.timestamp = discord.utils.utcnow()

        await log_channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(MessageLogger(bot))

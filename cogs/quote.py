# cogs/quotes.py
import discord
from discord.ext import commands
from typing import Optional

class Quote(commands.Cog):
    """Cog für das Zitieren von Nachrichten, wenn der Bot in einer Antwort erwähnt wird."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # Ignoriere Nachrichten von Bots
        if message.author.bot:
            return

        # Prüfe, ob die Nachricht eine Antwort ist und den Bot erwähnt
        if message.reference and self.bot.user in message.mentions:
            referenced_raw = message.reference.resolved
            if not isinstance(referenced_raw, discord.Message):
                return
            referenced: discord.Message = referenced_raw

            # Embed erstellen
            embed = discord.Embed(
                description=referenced.content or "*[Keine Nachricht]*",
                color=discord.Color.blurple(),
                timestamp=referenced.created_at
            )
            embed.set_author(
                name=referenced.author.display_name,
                icon_url=referenced.author.display_avatar.url
            )

            # Channelname im Footer
            channel_name: str = getattr(referenced.channel, "name", "Direktnachricht")
            embed.set_footer(text=f"In #{channel_name}")

            # Zeige erstes Bild, falls vorhanden
            if referenced.attachments:
                first_attachment = referenced.attachments[0]
                if first_attachment.content_type and first_attachment.content_type.startswith("image/"):
                    embed.set_image(url=first_attachment.url)

            await message.channel.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Quote(bot))

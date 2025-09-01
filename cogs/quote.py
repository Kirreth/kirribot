import discord
from discord.ext import commands
from typing import Optional

class Quote(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        if message.reference and self.bot.user in message.mentions:
            referenced_raw = message.reference.resolved
            # Nur echte Nachrichten akzeptieren, keine gelöschten Referenzen
            if not isinstance(referenced_raw, discord.Message):
                return
            referenced: discord.Message = referenced_raw

            embed = discord.Embed(
                description=referenced.content or "*[Keine Nachricht]*",
                color=discord.Color.blurple(),
                timestamp=referenced.created_at
            )
            embed.set_author(
                name=referenced.author.display_name,
                icon_url=referenced.author.display_avatar.url
            )

            # channel.name existiert nicht bei DMChannel, daher getattr mit Default
            channel_name: str = getattr(referenced.channel, "name", "Direktnachricht")
            embed.set_footer(text=f"In #{channel_name}")

            if referenced.attachments:
                first_attachment = referenced.attachments[0]
                if first_attachment.content_type and first_attachment.content_type.startswith("image/"):
                    embed.set_image(url=first_attachment.url)

            await message.channel.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Quote(bot))

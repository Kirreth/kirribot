import discord
from discord.ext import commands
from typing import Optional


class Quote(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        if message.reference and self.bot.user in message.mentions:
            referenced: Optional[discord.Message] = (
                message.reference.resolved
                if isinstance(message.reference.resolved, discord.Message)
                else None
            )

            if not referenced:
                return

            embed: discord.Embed = discord.Embed(
                description=referenced.content or "*[Keine Nachricht]*",
                color=discord.Color.blurple(),
                timestamp=referenced.created_at,
            )
            embed.set_author(
                name=referenced.author.display_name,
                icon_url=referenced.author.display_avatar.url,
            )
            embed.set_footer(text=f"In #{referenced.channel.name}")

            if referenced.attachments:
                first_attachment: discord.Attachment = referenced.attachments[0]
                if (
                    first_attachment.content_type
                    and first_attachment.content_type.startswith("image/")
                ):
                    embed.set_image(url=first_attachment.url)

            await message.channel.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Quote(bot))

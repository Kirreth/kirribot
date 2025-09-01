import discord
from discord.ext import commands

class Quote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.reference and self.bot.user in message.mentions:
            referenced = message.reference.resolved
            if not isinstance(referenced, discord.Message):
                return

            embed = discord.Embed(
                description=referenced.content or "*[Keine Nachricht]*",
                color=discord.Color.blurple(),
                timestamp=referenced.created_at
            )
            embed.set_author(
                name=referenced.author.display_name,
                icon_url=referenced.author.display_avatar.url
            )
            embed.set_footer(text=f"In #{referenced.channel.name}")

            if referenced.attachments:
                first_attachment = referenced.attachments[0]
                if first_attachment.content_type and first_attachment.content_type.startswith("image/"):
                    embed.set_image(url=first_attachment.url)

            await message.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Quote(bot))

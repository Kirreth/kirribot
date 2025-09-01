import discord
from discord.ext import commands
from utils import database as db
from typing import Optional


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="userinfo",
        description="Zeigt Infos über einen Benutzer"
    )
    async def userinfo(self, ctx: commands.Context, user: discord.Member) -> None:
        embed = discord.Embed(
            title=f"Infos über {user.display_name}",
            color=discord.Color.blurple()
        )

        # Avatar
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        else:
            embed.set_thumbnail(url=user.default_avatar.url)

        # Grunddaten
        embed.add_field(name="Name", value=f"{user} (`{user.id}`)", inline=False)
        embed.add_field(name="Bot?", value="✅ Ja" if user.bot else "❌ Nein", inline=True)
        embed.add_field(
            name="Account erstellt",
            value=user.created_at.strftime("%d.%m.%Y %H:%M:%S"),
            inline=False
        )

        # Gilde-Beitritt
        if user.joined_at:
            embed.add_field(
                name="Beigetreten",
                value=user.joined_at.strftime("%d.%m.%Y %H:%M:%S"),
                inline=False
            )

        # Rollen
        roles: list[str] = [role.mention for role in user.roles if role != ctx.guild.default_role]
        embed.add_field(
            name="Rollen",
            value=", ".join(roles) if roles else "Keine Rollen",
            inline=False
        )

        # DB-Abfrage: Counter & Level
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT counter, level FROM user WHERE id = ?", (str(user.id),))
        result: Optional[tuple[int, int]] = cursor.fetchone()
        conn.close()

        if result:
            counter: int
            level: int
            counter, level = result
            embed.add_field(name="Nachrichten", value=f"{counter} Nachrichten", inline=True)
            embed.add_field(name="Level", value=f"🆙 Level {level}", inline=True)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Info(bot))

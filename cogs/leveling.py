import discord
from discord.ext import commands
from utils import database as db
from typing import Optional


class Leveling(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        uid: str = str(message.author.id)
        uname: str = message.author.name

        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT counter FROM user WHERE id = ?", (uid,))
        result: Optional[tuple[int]] = cursor.fetchone()

        if result is None:
            counter: int = 1
            level: int = db.berechne_level(counter)
            cursor.execute(
                "INSERT INTO user (name, id, counter, level) VALUES (?, ?, ?, ?)",
                (uname, uid, counter, level),
            )
        else:
            counter: int = result[0] + 1
            level: int = db.berechne_level(counter)
            cursor.execute(
                "UPDATE user SET counter = ?, level = ? WHERE id = ?",
                (counter, level, uid),
            )

        conn.commit()
        conn.close()

    @commands.hybrid_command(
        name="hau",
        description="Zeigt den Nachrichten-Counter eines Users"
    )
    async def hau(self, ctx: commands.Context, user: discord.User) -> None:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT counter FROM user WHERE id = ?", (str(user.id),))
        result: Optional[tuple[int]] = cursor.fetchone()
        conn.close()

        if result is None:
            await ctx.send(f"{user.mention} hat noch keine Nachrichten geschrieben.")
        else:
            counter: int = result[0]
            level, progress = db.berechne_level_und_progress(counter)
            await ctx.send(
                f"{user.mention} hat **{counter} Nachrichten** geschrieben und ist "
                f"Level **{level}** ({progress*100:.1f}% zum nächsten Level)."
            )

    @commands.hybrid_command(
        name="top10",
        description="Zeigt die Top 10 User nach Nachrichten-Counter"
    )
    async def top10(self, ctx: commands.Context) -> None:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, counter, level FROM user ORDER BY counter DESC LIMIT 10")
        results: list[tuple[str, int, int]] = cursor.fetchall()
        conn.close()

        if not results:
            await ctx.send("Es gibt noch keine Einträge in der Bestenliste.")
            return

        embed = discord.Embed(title="🏆 Top 10 User", color=discord.Color.gold())
        for idx, (name, counter, level) in enumerate(results, start=1):
            embed.add_field(
                name=f"{idx}. {name}",
                value=f"📨 {counter} Nachrichten | ⭐ Level {level}",
                inline=False
            )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Leveling(bot))

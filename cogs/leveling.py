import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Union
from utils import database as db

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
        result = cursor.fetchone()

        if result is None:
            counter = 1  # Typ nicht erneut deklarieren
            level = db.berechne_level(counter)
            cursor.execute(
                "INSERT INTO user (name, id, counter, level) VALUES (?, ?, ?, ?)",
                (uname, uid, counter, level)
            )
        else:
            counter = result[0] + 1  # Typ nicht erneut deklarieren
            level = db.berechne_level(counter)
            cursor.execute(
                "UPDATE user SET counter = ?, level = ? WHERE id = ?",
                (counter, level, uid)
            )

        conn.commit()
        conn.close()

    @commands.hybrid_command(name="hau", description="Zeigt den Nachrichten-Counter eines Users")  # type: ignore[arg-type]
    async def hau(
        self,
        ctx: Context[commands.Bot],
        user: Union[discord.User, discord.Member]
    ) -> None:
        uid: str = str(user.id)
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT counter FROM user WHERE id = ?", (uid,))
        result = cursor.fetchone()
        conn.close()

        if result is None:
            await ctx.send(f"{user.mention} hat noch keine Nachrichten geschrieben.")
            return

        counter = result[0]  # Typ nicht erneut deklarieren
        level, progress = db.berechne_level_und_progress(counter)
        await ctx.send(
            f"{user.mention} hat **{counter} Nachrichten** geschrieben "
            f"und ist Level **{level}** ({progress*100:.1f}% zum nächsten Level)."
        )

    @commands.hybrid_command(name="top10", description="Zeigt die Top 10 User nach Nachrichten-Counter")  # type: ignore[arg-type]
    async def top10(self, ctx: Context[commands.Bot]) -> None:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, counter, level FROM user ORDER BY counter DESC LIMIT 10")
        results = cursor.fetchall()
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

import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Union
from utils.database import connection as db
from utils.database import leveling as db_leveling  # Level-Funktionen
from utils.database import messages as db_messages


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
            counter = 1
            level = db_leveling.berechne_level(counter)
            cursor.execute(
                "INSERT INTO user (name, id, counter, level) VALUES (?, ?, ?, ?)",
                (uname, uid, counter, level)
            )
        else:
            counter = result[0] + 1
            level = db_leveling.berechne_level(counter)
            cursor.execute(
                "UPDATE user SET counter = ?, level = ? WHERE id = ?",
                (counter, level, uid)
            )

        conn.commit()
        conn.close()

    @commands.hybrid_command(
        name="hau",
        description="Zeigt den Nachrichten-Counter eines Users"
    )
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

        counter = result[0]
        level, rest = db_leveling.berechne_level_und_rest(counter)

        await ctx.send(
            f"{user.mention} hat **{counter} Nachrichten** geschrieben "
            f"und ist Level **{level}**.\n"
            f"Es fehlen **{rest} Nachrichten** bis zum nächsten Level."
        )

    @commands.hybrid_command(
        name="top10",
        description="Zeigt die Top 10 User nach Nachrichten-Counter"
    )
    async def top10(self, ctx: Context[commands.Bot]) -> None:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, counter, level FROM user ORDER BY counter DESC LIMIT 10"
        )
        results = cursor.fetchall()
        conn.close()

        if not results:
            await ctx.send("Es gibt noch keine Einträge in der Bestenliste.")
            return

        embed = discord.Embed(title="🏆 Top 10 User", color=discord.Color.gold())
        for idx, (uid, counter, level) in enumerate(results, start=1):
            # Member oder User abrufen, um zu pingen
            user = ctx.guild.get_member(int(uid)) if ctx.guild else None
            if not user:
                try:
                    user = await self.bot.fetch_user(int(uid))
                except:
                    user = None
            mention = user.mention if user else f"Unbekannt ({uid})"

            embed.add_field(
                name=f"{idx}. {mention}",
                value=f"📨 {counter} Nachrichten | ⭐ Level {level}",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="topmf",
        description="Zeigt die Top 3 Flooder (meiste Nachrichten in den letzten 30 Tagen)"
    )
    async def topmf(self, ctx: commands.Context) -> None:
        guild_id: str = str(ctx.guild.id) if ctx.guild else "0"
        top_users = db_messages.get_top_messages(guild_id, days=30, limit=3)

        if not top_users:
            await ctx.send("📊 Es gibt noch keine Nachrichten in den letzten 30 Tagen.")
            return

        description = ""
        for index, (user_id, count) in enumerate(top_users, start=1):
            user = ctx.guild.get_member(int(user_id)) if ctx.guild else None
            if not user:
                try:
                    user = await self.bot.fetch_user(int(user_id))
                except:
                    user = None
            mention = user.mention if user else f"Unbekannt ({user_id})"

            description += f"**#{index}** {mention} – **{count} Nachrichten**\n"

        embed = discord.Embed(
            title="💬 Top 3 Monthly Flooder (Letzte 30 Tage)",
            description=description,
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Leveling(bot))

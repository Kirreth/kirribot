import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Union, Optional
from utils.database import connection as db
from utils.database import leveling as db_leveling  # Level-Funktionen
from utils.database import messages as db_messages


class Leveling(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return

        uid: str = str(message.author.id)
        uname: str = message.author.name
        guild_id: str = str(message.guild.id)
        channel_id: str = str(message.channel.id)

        # Nachricht loggen
        db_messages.log_message(guild_id, uid, channel_id)

        # Counter und Level updaten
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT counter FROM user WHERE id = %s", (uid,))
        result = cursor.fetchone()

        if result is None:
            counter = 1
            level = db_leveling.berechne_level(counter)
            cursor.execute(
                "INSERT INTO user (id, name, counter, level) VALUES (%s, %s, %s, %s)",
                (uid, uname, counter, level)
            )
        else:
            counter = result[0] + 1
            level = db_leveling.berechne_level(counter)
            cursor.execute(
                "UPDATE user SET counter = %s, level = %s WHERE id = %s",
                (counter, level, uid)
            )

        conn.commit()
        cursor.close()
        conn.close()

    @commands.hybrid_command(
        name="rank",
        description="Zeigt den Nachrichten-Counter, Level und den nächsten User, den man einholen könnte"
    )
    async def rank(
        self,
        ctx: Context[commands.Bot],
        user: Optional[Union[discord.User, discord.Member]] = None
    ) -> None:
        user = user or ctx.author
        uid: str = str(user.id)

        conn = db.get_connection()
        cursor = conn.cursor()

        # Counter abrufen
        cursor.execute("SELECT counter FROM user WHERE id = %s", (uid,))
        result = cursor.fetchone()
        if not result:
            await ctx.send(f"{user.mention} hat noch keine Nachrichten geschrieben.")
            cursor.close()
            conn.close()
            return

        counter = result[0]
        level, rest = db_leveling.berechne_level_und_rest(counter)

        # Nächsten User finden
        cursor.execute(
            "SELECT name, counter FROM user WHERE counter > %s ORDER BY counter ASC LIMIT 1",
            (counter,)
        )
        next_user = cursor.fetchone()
        cursor.close()
        conn.close()

        if next_user:
            next_name, next_counter = next_user
            next_info = f"\n{user.name} ist hinter dem User {next_name} mit {next_counter} Nachrichten."
        else:
            next_info = f"\n{user.name} ist aktuell der aktivste User! 🎉"

        await ctx.send(
            f"{user.mention} - Level {level}\n"
            f"Nachrichten: {counter}\n"
            f"Nachrichten bis zum nächsten Level: {rest}"
            f"{next_info}"
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
        cursor.close()
        conn.close()

        if not results:
            await ctx.send("Es gibt noch keine Einträge in der Bestenliste.")
            return

        embed = discord.Embed(title="🏆 Top 10 User", color=discord.Color.gold())
        for idx, (uid, counter, level) in enumerate(results, start=1):
            user_obj = ctx.guild.get_member(int(uid)) if ctx.guild else None
            if not user_obj:
                try:
                    user_obj = await self.bot.fetch_user(int(uid))
                except:
                    user_obj = None
            mention = user_obj.mention if user_obj else f"Unbekannt ({uid})"

            embed.add_field(
                name=f"{idx}. {mention}",
                value=f"📨 {counter} Nachrichten | ⭐ Level {level}",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="topf",
        description="Zeigt die aktivsten User in den letzten X Tagen (optional, Standard: 30)"
    )
    async def topf(
        self,
        ctx: commands.Context,
        days: Optional[int] = 30
    ) -> None:
        if days <= 0:
            await ctx.send("Die Anzahl der Tage muss größer als 0 sein.")
            return

        guild_id: str = str(ctx.guild.id)
        top_users = db_messages.get_top_messages(guild_id, days=days, limit=5)

        if not top_users:
            await ctx.send(f"📊 Es gibt noch keine Nachrichten in den letzten {days} Tagen.")
            return

        description = ""
        for idx, (user_id, count) in enumerate(top_users, start=1):
            user_obj = ctx.guild.get_member(int(user_id)) if ctx.guild else None
            if not user_obj:
                try:
                    user_obj = await self.bot.fetch_user(int(user_id))
                except:
                    user_obj = None
            mention = user_obj.mention if user_obj else f"Unbekannt ({user_id})"
            description += f"**#{idx}** {mention} – **{count} Nachrichten**\n"

        embed = discord.Embed(
            title=f"💬 Top Flooder der letzten {days} Tage",
            description=description,
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Leveling(bot))

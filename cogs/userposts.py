import discord
from discord.ext import commands
from discord import ui, Interaction
from utils.database import posts as db_posts
import logging

class PostCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -----------------------------
    # Post erstellen Command (Hybrid)
    # -----------------------------
    @commands.hybrid_command(name="create_post", description="Erstelle einen neuen Post")
    async def create_post(self, ctx: commands.Context):
        # Interaction aus Hybrid Command abrufen
        interaction = ctx.interaction
        if not interaction:
            await ctx.send("❌ Dieser Command funktioniert nur als Slash Command.", ephemeral=True)
            return

        check_channel_id = db_posts.get_check_channel(str(ctx.guild.id))
        if not check_channel_id:
            await interaction.response.send_message(
                "❌ Kein Checkpost-Channel gesetzt. Admin muss dies über die Setup-Befehle tun.",
                ephemeral=True
            )
            return

        modal = ReminderModal(interaction, self.bot.get_channel(int(check_channel_id)), self.bot)
        await interaction.response.send_modal(modal)


# -----------------------------
# Modal für Post-Erstellung
# -----------------------------
class ReminderModal(ui.Modal, title="Erstelle deinen Post"):
    def __init__(self, interaction: Interaction, channel: discord.TextChannel, bot):
        super().__init__()
        self.interaction = interaction
        self.channel = channel
        self.bot = bot

        self.name = ui.TextInput(label="Post-Name", placeholder="Name deines Posts", required=True, max_length=50)
        self.content = ui.TextInput(label="Inhalt", style=discord.TextStyle.paragraph, placeholder="Inhalt des Posts", required=True, max_length=1500)
        self.link = ui.TextInput(label="Link", style=discord.TextStyle.short, placeholder="Link zum Post", required=True, max_length=200)

        self.add_item(self.name)
        self.add_item(self.content)
        self.add_item(self.link)

    async def on_submit(self, interaction: Interaction):
        try:
            # Post in DB speichern
            post_id = db_posts.add_post(
                guild_id=str(interaction.guild.id),
                name=self.name.value.strip(),
                content=self.content.value.strip(),
                link=self.link.value.strip(),
                author_id=str(interaction.user.id)
            )

            # Buttons für Checkpost-Channel
            buttons = PostCheckButtons(post_id, interaction.guild.id)
            embed = discord.Embed(
                title=self.name.value.strip(),
                description=self.content.value.strip(),
                color=discord.Color.blue()
            )
            embed.add_field(name="Link", value=self.link.value.strip(), inline=False)
            embed.set_footer(text=f"Eingereicht von {interaction.user}", icon_url=interaction.user.display_avatar.url)

            await self.channel.send(embed=embed, view=buttons)
            await interaction.response.send_message(
                f"✅ Post **{self.name.value}** erfolgreich zur Prüfung eingereicht!",
                ephemeral=True
            )
        except Exception as e:
            logging.error(f"Failed to save post: {e}")
            await interaction.response.send_message("❌ Fehler bei der Einreichung.", ephemeral=True)


# -----------------------------
# Buttons für Checkpost
# -----------------------------
class PostCheckButtons(ui.View):
    def __init__(self, post_id, guild_id):
        super().__init__(timeout=None)
        self.post_id = post_id
        self.guild_id = guild_id

    @ui.button(label="Genehmigen", style=discord.ButtonStyle.green)
    async def approve(self, interaction: Interaction, button: ui.Button):
        post = db_posts.get_post(self.post_id)
        if not post:
            await interaction.response.send_message("❌ Post nicht gefunden.", ephemeral=True)
            return

        post_channel_id = db_posts.get_post_channel(str(interaction.guild.id))
        if not post_channel_id:
            await interaction.response.send_message("❌ Kein Post-Channel gesetzt.", ephemeral=True)
            return

        channel = interaction.guild.get_channel(int(post_channel_id))
        if not channel:
            await interaction.response.send_message("❌ Post-Channel existiert nicht.", ephemeral=True)
            return

        embed = discord.Embed(title=post['name'], description=post['content'], color=discord.Color.green())
        embed.add_field(name="Link", value=post['link'], inline=False)
        author = interaction.guild.get_member(int(post['author_id']))
        if author:
            embed.set_footer(text=f"Eingereicht von {author}", icon_url=author.display_avatar.url)

        await channel.send(embed=embed)
        db_posts.set_post_status(self.post_id, "approved")
        await interaction.message.delete()
        await interaction.response.send_message("✅ Post genehmigt!", ephemeral=True)

    @ui.button(label="Verwerfen", style=discord.ButtonStyle.red)
    async def deny(self, interaction: Interaction, button: ui.Button):
        db_posts.set_post_status(self.post_id, "denied")
        await interaction.message.delete()
        await interaction.response.send_message("❌ Post verworfen.", ephemeral=True)


# -----------------------------
# Setup Cog
# -----------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(PostCog(bot))

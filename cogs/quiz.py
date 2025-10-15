import discord
from discord.ext import commands
from discord.ui import View, Button
import random
from utils.database import quiz as db_quiz

class Quiz(commands.Cog):
    """IT/Programmier-Quiz"""

    def __init__(self, bot):
        self.bot = bot

    # ------------------------------------------------------------
    # Fragenpool 
    # ------------------------------------------------------------
    QUESTIONS = [
        {
            "question": "Was bedeutet HTML?",
            "options": ["Hyper Text Markup Language", "High Text Machine Learning", "Hyper Transfer Main Logic", "Home Tool Management Level"],
            "answer": "Hyper Text Markup Language"
        },
        {
            "question": "Welche Programmiersprache läuft im Browser?",
            "options": ["Python", "C#", "JavaScript", "Rust"],
            "answer": "JavaScript"
        },
        {
            "question": "Was ist eine Datenbank?",
            "options": ["Eine Website", "Ein Speicher für strukturierte Daten", "Ein Textdokument", "Ein Webserver"],
            "answer": "Ein Speicher für strukturierte Daten"
        },
        {
            "question": "Was ist Git?",
            "options": ["Ein Texteditor", "Ein Versionskontrollsystem", "Ein Betriebssystem", "Ein Webbrowser"],
            "answer": "Ein Versionskontrollsystem"
        },
        {
            "question": "Welche Sprache wird hauptsächlich für maschinelles Lernen verwendet?",
            "options": ["Java", "Python", "C++", "Ruby"],
            "answer": "Python"
        },
        {
            "question": "Was ist ein API?",
            "options": ["Application Programming Interface", "Automated Process Integration", "Advanced Programming Instruction", "Application Performance Index"],
            "answer": "Application Programming Interface"
        },
        {
            "question": "Welches dieser ist kein Frontend-Framework?",
            "options": ["React", "Angular", "Django", "Vue.js"],
            "answer": "Django"
        },
        {
            "question": "Was macht CSS?",
            "options": ["Strukturiert Inhalte", "Stylt Webseiten", "Programmiert Logik", "Verbindet Datenbanken"],
            "answer": "Stylt Webseiten"
        },
        {
            "question": "Was ist Docker?",
            "options": ["Ein Cloud-Service", "Eine Containerisierungsplattform", "Ein Datenbankmanagementsystem", "Ein Texteditor"],
            "answer": "Eine Containerisierungsplattform"
        },
        {
            "question": "Welche Sprache wird hauptsächlich für iOS-Entwicklung verwendet?",
            "options": ["Swift", "Kotlin", "JavaScript", "C#"],
            "answer": "Swift"
        }
    ]

    # ------------------------------------------------------------
    # Command: /quiz
    # ------------------------------------------------------------
    @commands.hybrid_command(name="quiz", description="Starte ein IT-Quiz mit 10 Fragen!")
    async def start_quiz(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)

        questions = random.sample(self.QUESTIONS, k=min(10, len(self.QUESTIONS)))
        score = 0

        for q in questions:
            view = QuizView(q["options"], q["answer"])
            embed = discord.Embed(title="🧠 IT-Quiz", description=q["question"], color=discord.Color.blurple())
            msg = await ctx.send(embed=embed, view=view, ephemeral=True)
            await view.wait()

            if view.chosen == q["answer"]:
                score += 1

            await msg.edit(view=None)

        db_quiz.save_quiz_result(str(ctx.author.id), str(ctx.guild.id), score)

        result_text = f"Du hast **{score}/10** Fragen richtig beantwortet!"
        if score >= 8:
            role = discord.utils.get(ctx.guild.roles, name="Code-Champion")
            if not role:
                role = await ctx.guild.create_role(name="Code-Champion", color=discord.Color.gold())
            await ctx.author.add_roles(role)
            result_text += f"\n🏆 Glückwunsch! Du hast die Rolle {role.mention} erhalten!"

        await ctx.send(embed=discord.Embed(title="Quiz beendet!", description=result_text, color=discord.Color.green()), ephemeral=True)


class QuizView(View):
    def __init__(self, options, correct_answer):
        super().__init__(timeout=30)
        self.correct_answer = correct_answer
        self.chosen = None
        for opt in options:
            self.add_item(QuizButton(label=opt, correct_answer=correct_answer))

    async def on_timeout(self):
        self.stop()


class QuizButton(Button):
    def __init__(self, label, correct_answer):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.correct_answer = correct_answer

    async def callback(self, interaction: discord.Interaction):
        if self.label == self.correct_answer:
            self.style = discord.ButtonStyle.success
        else:
            self.style = discord.ButtonStyle.danger
        self.view.chosen = self.label
        await interaction.response.edit_message(view=self.view)
        self.view.stop()


async def setup(bot: commands.Bot):
    await bot.add_cog(Quiz(bot))

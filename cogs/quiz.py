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
        },
        {
            "question": "Was ist der Zweck von HTTP?",
            "options": ["Datenübertragung im Web", "Datenbankverwaltung", "Dateikomprimierung", "Betriebssystemsteuerung"],
            "answer": "Datenübertragung im Web"
        },
        {
            "question": "Was ist ein Framework?",
            "options": ["Ein Texteditor", "Eine Sammlung von Bibliotheken und Tools", "Ein Betriebssystem", "Ein Webserver"],
            "answer": "Eine Sammlung von Bibliotheken und Tools"
        },
        {
            "question": "Welche dieser Sprachen ist typisiert?",
            "options": ["JavaScript", "Python", "TypeScript", "PHP"],
            "answer": "TypeScript"
        },
        {
            "question": "Was ist Cloud Computing?",
            "options": ["Lokale Datenspeicherung", "Rechnen über das Internet", "Ein Webbrowser", "Ein Texteditor"],
            "answer": "Rechnen über das Internet"
        },
        {
            "question": "Was ist ein Algorithmus?",
            "options": ["Ein Programm", "Eine Schritt-für-Schritt-Anleitung zur Problemlösung", "Ein Datenbanktyp", "Ein Webserver"],
            "answer": "Eine Schritt-für-Schritt-Anleitung zur Problemlösung"
        },
        {
            "question": "Welche dieser ist keine Programmiersprache?",
            "options": ["Python", "HTML", "Java", "C++"],
            "answer": "HTML"
        },
        {
            "question": "Was ist ein Compiler?",
            "options": ["Ein Texteditor", "Ein Programm, das Quellcode in Maschinencode übersetzt", "Ein Webbrowser", "Ein Betriebssystem"],
            "answer": "Ein Programm, das Quellcode in Maschinencode übersetzt"
        },
        {
            "question": "Was bedeutet 'Open Source'?",
            "options": ["Kostenlose Software", "Software mit offenem Quellcode", "Software für Unternehmen", "Software für mobile Geräte"],
            "answer": "Software mit offenem Quellcode"
        },
        {
            "question": "Was ist ein Bug in der Programmierung?",
            "options": ["Ein Feature", "Ein Fehler im Code", "Ein Datenbanktyp", "Ein Webserver"],
            "answer": "Ein Fehler im Code"
        },
        {
            "question": "Welche dieser Technologien wird hauptsächlich für die Backend-Entwicklung verwendet?",
            "options": ["React", "Node.js", "CSS", "HTML"],
            "answer": "Node.js"
        },
        {
            "question": "Was ist eine IDE?",
            "options": ["Integrated Development Environment", "Internet Data Exchange", "Internal Database Engine", "Interactive Design Editor"],
            "answer": "Integrated Development Environment"
        },
        {
            "question": "Was ist der Zweck von SQL?",
            "options": ["Webentwicklung", "Datenbankabfragen und -verwaltung", "Textverarbeitung", "Betriebssystemsteuerung"],
            "answer": "Datenbankabfragen und -verwaltung"
        },
        {
            "question": "Welche dieser Sprachen wird hauptsächlich für Systemprogrammierung verwendet?",
            "options": ["JavaScript", "C", "HTML", "PHP"],
            "answer": "C"
        },
        {
            "question": "Was ist ein Framework für maschinelles Lernen?",
            "options": ["Django", "TensorFlow", "React", "Laravel"],
            "answer": "TensorFlow"
        },
        {
            "question": "Was ist der Unterschied zwischen '==' und '===' in JavaScript?",
            "options": ["Kein Unterschied", "'==' vergleicht Werte, '===' vergleicht Werte und Typen", "'==' vergleicht Typen, '===' vergleicht Werte", "'==' ist für Zahlen, '===' ist für Strings"],
            "answer": "'==' vergleicht Werte, '===' vergleicht Werte und Typen"
        },
        {
            "question": "Was ist ein NoSQL-Datenbank?",
            "options": ["Eine relationale Datenbank", "Eine nicht-relationale Datenbank", "Ein Webserver", "Ein Texteditor"],
            "answer": "Eine nicht-relationale Datenbank"
        },
        {
            "question": "Welche dieser ist keine Cloud-Plattform?",
            "options": ["AWS", "Azure", "Google Cloud", "Linux"],
            "answer": "Linux"
        },
        {
            "question": "Was ist der Zweck von JWT (JSON Web Token)?",
            "options": ["Datenkomprimierung", "Authentifizierung und Informationsaustausch", "Dateiverwaltung", "Webentwicklung"],
            "answer": "Authentifizierung und Informationsaustausch"
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
            role = discord.utils.get(ctx.guild.roles, name="Coder")
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

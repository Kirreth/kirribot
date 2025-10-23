import os
import json
import random
import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import app_commands
from utils.database import quiz as db_quiz


# ------------------------------------------------------------
# Pfad zur JSON-Datei
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
QUIZ_FILE = os.path.join(BASE_DIR, "data", "quiz_questions.json")


# ------------------------------------------------------------
# Hilfsfunktionen für JSON (Unverändert)
# ------------------------------------------------------------
def ensure_quiz_file():
    """Stellt sicher, dass der data-Ordner und die quiz_questions.json existieren."""
    data_dir = os.path.join(BASE_DIR, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    if not os.path.exists(QUIZ_FILE):
        with open(QUIZ_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)


def load_questions():
    """Lädt alle Fragen aus der JSON-Datei."""
    ensure_quiz_file()
    with open(QUIZ_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_questions(questions):
    """Speichert Fragen in die JSON-Datei."""
    ensure_quiz_file()
    with open(QUIZ_FILE, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=4, ensure_ascii=False)


# ------------------------------------------------------------
# Haupt-Cog
# ------------------------------------------------------------
class Quiz(commands.Cog):
    """IT/Programmier-Quiz"""

    __cog_name__ = "Quiz"

    def __init__(self, bot):
        self.bot = bot

    # ------------------------------------------------------------
    # /quizadd – Neue Frage hinzufügen (Admin-only)
    # ------------------------------------------------------------
    @commands.hybrid_command(name="quizadd", description="Füge eine neue Quizfrage hinzu (nur Admins).")
    @app_commands.describe(
        question="Die Quizfrage",
        answer1="Antwort 1",
        answer2="Antwort 2",
        answer3="Antwort 3",
        answer4="Antwort 4",
        correct="Nummer der richtigen Antwort (1–4)"
    )

    @app_commands.checks.has_permissions(administrator=True) 
    async def quizadd(
        self,
        ctx: commands.Context, 
        question: str,
        answer1: str,
        answer2: str,
        answer3: str,
        answer4: str,
        correct: int
    ):
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
            
        if correct not in [1, 2, 3, 4]:
            await ctx.send("❌ Die richtige Antwort muss 1–4 sein.", ephemeral=True) 
            return

        questions = load_questions()
        new_question = {
            "question": question,
            "options": [answer1, answer2, answer3, answer4],
            "answer": [answer1, answer2, answer3, answer4][correct - 1]
        }

        questions.append(new_question)
        save_questions(questions)

        await ctx.send(
            f"✅ Neue Frage hinzugefügt:\n**{question}**\n**Richtige Antwort:** {new_question['answer']}",
            ephemeral=True
        )

    # ------------------------------------------------------------
    # /quiz – Starte das IT-Quiz
    # ------------------------------------------------------------
    @commands.hybrid_command(name="quiz", description="Starte ein IT-Quiz mit 10 Fragen!")
    async def start_quiz(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)

        questions = load_questions()
        if not questions:
            await ctx.send("❌ Es sind noch keine Fragen im Quiz vorhanden.", ephemeral=True)
            return

        selected_questions = random.sample(questions, k=min(10, len(questions)))
        total_questions = len(selected_questions) 
        score = 0

        
        for index, q in enumerate(selected_questions):
            current_question_number = index + 1 
            
            view = QuizView(q["options"], q["answer"])
            
            embed = discord.Embed(
                title=f"🧠 IT-Quiz ({current_question_number}/{total_questions})", 
                description=q["question"], 
                color=discord.Color.blurple()
            )
            
            msg = await ctx.send(embed=embed, view=view, ephemeral=True)
            await view.wait()

            if view.chosen == q["answer"]:
                score += 1

            await msg.edit(view=None) # Löscht die Buttons nach Beantwortung/Timeout

        # Die Guild ID ist wichtig für die Multi-Server-Fähigkeit der Datenbank.
        db_quiz.save_quiz_result(str(ctx.author.id), str(ctx.guild.id) if ctx.guild else "0", score)


        # ------------------------------------------------------------
        # Auswertung & Belohnung (Mit korrigierter Fragenanzahl)
        # ------------------------------------------------------------
        result_text = f"Du hast **{score}/{total_questions}** Fragen richtig beantwortet!" # total_questions verwenden

        if score >= 8:
            role_name = "Coder"
            role = discord.utils.get(ctx.guild.roles, name=role_name)

            if not role:
                try:
                    role = await ctx.guild.create_role(name=role_name, color=discord.Color.gold())
                except discord.Forbidden:
                    # Falls Rolle nicht erstellt werden kann, trotzdem weitermachen
                    pass


            if role:
                try:
                    await ctx.author.add_roles(role)
                    result_text += f"\n🏆 Glückwunsch! Du hast die Rolle {role.mention} erhalten!"
                except discord.Forbidden:
                    result_text += "\n⚠️ Ich konnte die Rolle nicht vergeben (fehlende Berechtigung)."

        await ctx.send(
            embed=discord.Embed(
                title="📊 Quiz beendet!",
                description=result_text,
                color=discord.Color.green()
            ),
            ephemeral=True
        )


# ------------------------------------------------------------
# View & Button für das Quiz
# ------------------------------------------------------------
class QuizView(View):
    def __init__(self, options, correct_answer):
        super().__init__(timeout=30)
        self.correct_answer = correct_answer
        self.chosen = None
        for opt in options:
            # Stellt sicher, dass die Button-Labels nicht länger als 80 Zeichen sind
            btn_label = opt[:80]
            self.add_item(QuizButton(label=btn_label, correct_answer=correct_answer))

    async def on_timeout(self):
        # Deaktiviere die Buttons nach Timeout
        for item in self.children:
             if isinstance(item, Button):
                 item.disabled = True
        self.stop()


class QuizButton(Button):
    def __init__(self, label, correct_answer):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.correct_answer = correct_answer

    async def callback(self, interaction: discord.Interaction):
        # 🚩 KORRIGIERTE LOGIK: SOFORT AUF INTERAKTION ANTWORTEN, UM FEHLER ZU VERMEIDEN
        await interaction.response.defer() 
        
        # Prüfen, ob der Nutzer bereits geantwortet hat
        if self.view.chosen is not None:
             return

        # Logik zur Bestimmung der korrekten/falschen Antwort
        if self.label == self.correct_answer:
            self.style = discord.ButtonStyle.success
        else:
            self.style = discord.ButtonStyle.danger
            
        self.view.chosen = self.label
        
        # Alle Buttons deaktivieren
        for item in self.view.children:
            if isinstance(item, Button):
                item.disabled = True
        
        # Nachricht bearbeiten, da zuvor defer() gesendet wurde
        await interaction.edit_original_response(view=self.view)
        
        # Beendet die View, damit die nächste Frage geladen wird
        self.view.stop()


# ------------------------------------------------------------
# Cog Setup 
# ------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Quiz(bot))
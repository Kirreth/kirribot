import os
import json
import random
import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Button

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
QUIZ_FILE = os.path.join(BASE_DIR, "data", "quiz_questions.json")

def ensure_quiz_file():
    data_dir = os.path.join(BASE_DIR, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    if not os.path.exists(QUIZ_FILE):
        with open(QUIZ_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)

def load_questions():
    ensure_quiz_file()
    with open(QUIZ_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

class PartyQuiz(commands.Cog):
    """Quiz-Spiel für alle Teilnehmer gleichzeitig"""

    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # guild_id -> QuizGame

    @commands.hybrid_command(name="partyquiz", description="Starte ein Party-Quiz für alle!")
    async def partyquiz(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        if guild_id in self.active_games:
            await ctx.send("❌ Ein Quiz läuft bereits in diesem Server!")
            return

        questions = load_questions()
        if len(questions) < 5:
            await ctx.send("❌ Es sind noch nicht genügend Fragen vorhanden (mind. 5).")
            return

        selected_questions = random.sample(questions, k=min(20, len(questions)))
        game = QuizGame(ctx, selected_questions)
        self.active_games[guild_id] = game
        await game.start()
        del self.active_games[guild_id]

class QuizGame:
    """Verwaltet ein einzelnes Party-Quiz"""

    def __init__(self, ctx: commands.Context, questions):
        self.ctx = ctx
        self.questions = questions
        self.scores = {}  # user_id -> score
        self.current_index = 0
        self.message = None

    async def start(self):
        await self.ctx.send("🎉 Das Party-Quiz startet jetzt! Jeder kann teilnehmen und Punkte sammeln!")
        await self.next_question()

    async def next_question(self):
        if self.current_index >= len(self.questions):
            await self.finish()
            return

        question = self.questions[self.current_index]
        view = PartyQuizView(question["options"], question["answer"], self)
        embed = discord.Embed(
            title=f"🧠 Frage {self.current_index + 1}/{len(self.questions)}",
            description=question["question"],
            color=discord.Color.blurple()
        )
        self.message = await self.ctx.send(embed=embed, view=view)
        await view.wait()  # wartet bis eine Antwort gegeben wurde

        # kurze Pause, damit jeder die Antwort sehen kann
        await asyncio.sleep(3)

        self.current_index += 1
        await self.next_question()

    async def register_answer(self, user: discord.User, answer: str, correct_answer: str):
        if user.id not in self.scores:
            self.scores[user.id] = 0
        if answer == correct_answer:
            self.scores[user.id] += 1

    async def finish(self):
        if not self.scores:
            await self.ctx.send("⚠️ Niemand hat am Quiz teilgenommen.")
            return

        # Top Spieler sortieren
        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        description = ""
        for idx, (user_id, score) in enumerate(sorted_scores, start=1):
            member = self.ctx.guild.get_member(user_id)
            if member:
                description += f"**{idx}.** {member.display_name} – {score} Punkte\n"

        winner_id, winner_score = sorted_scores[0]
        winner = self.ctx.guild.get_member(winner_id)
        await self.ctx.send(
            embed=discord.Embed(
                title="🏆 Party-Quiz beendet!",
                description=f"🎉 Sieger: {winner.display_name} mit {winner_score} Punkten!\n\nRangliste:\n{description}",
                color=discord.Color.gold()
            )
        )

class PartyQuizView(View):
    def __init__(self, options, correct_answer, game: QuizGame):
        super().__init__(timeout=30)
        self.correct_answer = correct_answer
        self.game = game
        self.answered = False
        for opt in options:
            self.add_item(PartyQuizButton(label=opt, correct_answer=correct_answer, game=game, view=self))

    async def on_timeout(self):
        self.stop()

class PartyQuizButton(Button):
    def __init__(self, label, correct_answer, game: QuizGame, view: PartyQuizView):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.correct_answer = correct_answer
        self.game = game
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if self.view_ref.answered:
            await interaction.response.defer()
            return

        self.view_ref.answered = True
        await self.game.register_answer(interaction.user, self.label, self.correct_answer)

        # alle Buttons deaktivieren & markieren
        for item in self.view_ref.children:
            if isinstance(item, Button):
                item.disabled = True
                if item.label == self.correct_answer:
                    item.style = discord.ButtonStyle.success
                elif item.label == self.label:
                    item.style = discord.ButtonStyle.danger

        await interaction.response.edit_message(view=self.view_ref)
        self.view_ref.stop()

async def setup(bot: commands.Bot):
    await bot.add_cog(PartyQuiz(bot))

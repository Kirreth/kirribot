import os
import json
import random
import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Button

# Pfad-Setup
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# Stellen Sie sicher, dass "data" und die JSON-Datei vorhanden sind.
QUIZ_FILE = os.path.join(BASE_DIR, "data", "general_knowledge_questions.json")

def ensure_quiz_file():
    """Stellt sicher, dass das Datenverzeichnis und die Quiz-Datei existieren."""
    data_dir = os.path.join(BASE_DIR, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    if not os.path.exists(QUIZ_FILE):
        with open(QUIZ_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)

def load_questions():
    """Lädt die Fragen aus der JSON-Datei."""
    ensure_quiz_file()
    try:
        with open(QUIZ_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("Fehler: general_knowledge_questions.json ist keine gültige JSON-Datei oder ist leer.")
        return []

class PartyQuiz(commands.Cog):
    """Quiz-Spiel für alle zugelassenen Teilnehmer"""

    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # guild_id -> QuizGame

    @commands.hybrid_command(name="partyquiz", description="Starte ein Party-Quiz mit ausgewählten Spielern!")
    async def partyquiz(self, ctx: commands.Context, spieler: commands.Greedy[discord.Member]):
        """Startet ein Quiz und nimmt eine Liste von Spielern an."""
        guild_id = ctx.guild.id
        
        if guild_id in self.active_games:
            await ctx.send("❌ Ein Quiz läuft bereits in diesem Server!")
            return
            
        if not spieler:
            # Sendet eine Fehlermeldung, wenn keine Spieler gementioned wurden
            await ctx.send("❌ Du musst mindestens einen Spieler mit `@mention` angeben, z.B. `/partyquiz @Spieler1 @Spieler2`.")
            return

        questions = load_questions()
        if len(questions) < 5:
            await ctx.send("❌ Es sind noch nicht genügend Fragen vorhanden (mind. 5).")
            return

        # Wählt eine feste Anzahl an Fragen aus
        selected_questions = random.sample(questions, k=min(20, len(questions)))
        
        # Übergibt die IDs der erlaubten Spieler an das Spiel
        allowed_player_ids = [p.id for p in spieler]
        game = QuizGame(ctx, selected_questions, allowed_player_ids)
        self.active_games[guild_id] = game
        
        await game.start()
        
        # Spiel beendet, aus aktiven Spielen entfernen
        if guild_id in self.active_games:
            del self.active_games[guild_id]

class QuizGame:
    """Verwaltet ein einzelnes Party-Quiz"""
    
    TIME_PER_QUESTION = 15  # 15 Sekunden Zeit pro Frage

    def __init__(self, ctx: commands.Context, questions, allowed_players: list):
        self.ctx = ctx
        self.questions = questions
        self.scores = {}  # user_id -> score
        self.current_index = 0
        self.message = None
        self.allowed_players = set(allowed_players) # Zugelassene Spieler-IDs

    async def start(self):
        player_mentions = ", ".join(f"<@{p_id}>" for p_id in self.allowed_players)
        await self.ctx.send(f"🎉 Das Party-Quiz startet jetzt mit {len(self.allowed_players)} Spielern: {player_mentions}")
        await self.next_question()

    async def next_question(self):
        if self.current_index >= len(self.questions):
            await self.finish()
            return

        question = self.questions[self.current_index]
        view = PartyQuizView(question["options"], question["answer"], self)
        
        # Erstellt die Embed-Nachricht
        embed = discord.Embed(
            title=f"🧠 Frage {self.current_index + 1}/{len(self.questions)} (Zeit: {self.TIME_PER_QUESTION}s)",
            description=f"**{question['question']}**",
            color=discord.Color.blurple()
        )
        
        self.message = await self.ctx.send(embed=embed, view=view)
        
        # Warte die feste Zeit, in der Spieler antworten können
        await asyncio.sleep(self.TIME_PER_QUESTION)

        # Deaktivieren der Buttons und anzeigen der richtigen Antwort nach Timeout
        for item in view.children:
            if isinstance(item, Button):
                item.disabled = True
                if item.label == question["answer"]:
                    item.style = discord.ButtonStyle.success # Grüne Markierung für die richtige Antwort

        # Aktualisiert die Nachricht mit der Lösung und deaktivierten Buttons
        await self.message.edit(
            content=f"⏱️ Zeit abgelaufen! Die richtige Antwort war: **{question['answer']}**", 
            embed=embed, 
            view=view
        )
        
        self.current_index += 1
        await self.next_question()

    async def register_answer(self, user: discord.User, answer: str, correct_answer: str):
        """Registriert die Antwort eines Spielers und aktualisiert den Score."""
        # Da der PartyQuizButton bereits auf die Berechtigung prüft, muss hier nur das Scoring erfolgen.
        if user.id not in self.scores:
            self.scores[user.id] = 0
            
        if answer == correct_answer:
            self.scores[user.id] += 1

    async def finish(self):
        if not self.scores:
            await self.ctx.send("⚠️ Niemand von den zugelassenen Spielern hat am Quiz teilgenommen.")
            return

        # Top Spieler sortieren
        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        description = ""
        
        # Nur zugelassene Spieler im Ranking anzeigen, auch wenn sie 0 Punkte haben
        final_ranking_data = []
        for player_id in self.allowed_players:
            score = self.scores.get(player_id, 0)
            final_ranking_data.append((player_id, score))
            
        # Sortieren nach Punkten
        final_ranking_data.sort(key=lambda x: x[1], reverse=True)


        for idx, (user_id, score) in enumerate(final_ranking_data, start=1):
            member = self.ctx.guild.get_member(user_id)
            # Stellt sicher, dass der Benutzer noch im Server ist
            name = member.display_name if member else f"Unbekannter Spieler ({user_id})"
            
            # Emoji für die Top 3
            if idx == 1:
                emoji = "🥇"
            elif idx == 2:
                emoji = "🥈"
            elif idx == 3:
                emoji = "🥉"
            else:
                emoji = f"{idx}."
                
            description += f"{emoji} **{name}** – **{score}** Punkte\n"

        winner_id, winner_score = final_ranking_data[0]
        winner = self.ctx.guild.get_member(winner_id)
        winner_name = winner.display_name if winner else f"Unbekannter Spieler ({winner_id})"
        
        await self.ctx.send(
            embed=discord.Embed(
                title="🏆 Party-Quiz beendet!",
                description=f"🎉 Der Sieger ist **{winner_name}** mit **{winner_score}** Punkten!\n\n**Endgültige Rangliste:**\n{description}",
                color=discord.Color.gold()
            )
        )

class PartyQuizView(View):
    def __init__(self, options, correct_answer, game: QuizGame):
        # Setzt das Timeout der View auf die Fragezeit des Spiels
        super().__init__(timeout=game.TIME_PER_QUESTION)
        self.correct_answer = correct_answer
        self.game = game
        self.already_answered = set() # Speichert die IDs der Spieler, die bereits geantwortet haben
        
        # Fügt die Buttons hinzu
        for opt in options:
            self.add_item(PartyQuizButton(label=opt, correct_answer=correct_answer, game=game, view=self))

    async def on_timeout(self):
        # Stoppt die Interaktion, wenn die Zeit abgelaufen ist
        self.stop()

class PartyQuizButton(Button):
    def __init__(self, label, correct_answer, game: QuizGame, view: PartyQuizView):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.correct_answer = correct_answer
        self.game = game
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        # 1. Spieler-Autorisierungsprüfung (Ephemerer Fehler)
        if user_id not in self.game.allowed_players:
            await interaction.response.send_message("❌ Du bist nicht als Teilnehmer dieses Quiz zugelassen.", ephemeral=True)
            return
        
        # 2. Mehrfachklick-Prüfung (Ephemerer Fehler)
        if user_id in self.view_ref.already_answered:
            await interaction.response.send_message("❌ Du hast diese Frage bereits beantwortet.", ephemeral=True)
            return

        # Spieler zur Liste der Geantworteten hinzufügen
        self.view_ref.already_answered.add(user_id)
        
        # Antwort registrieren und Score aktualisieren
        is_correct = self.label == self.correct_answer
        await self.game.register_answer(interaction.user, self.label, self.correct_answer)
        
        # 3. Ephemeral Feedback an den Benutzer senden
        result_text = "richtig" if is_correct else "falsch"
        emoji = "✅" if is_correct else "❌"
        
        await interaction.response.send_message(
            f"{emoji} Deine Antwort **{self.label}** wurde registriert. Das war **{result_text}**! Warte auf die nächste Frage.", 
            ephemeral=True
        )

# Die Setup-Funktion für den Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(PartyQuiz(bot))
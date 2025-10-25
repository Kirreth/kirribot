import os
import json
import random
import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Button

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
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

# --- Haupt-Cog für den Bot ---

class PartyQuiz(commands.Cog):
    """Quiz-Spiel mit dynamischer Spieler-Registrierung."""
    
    REGISTRATION_TIME = 30 
    MIN_PLAYERS = 1    

    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  

    @commands.hybrid_command(name="partyquiz", description="Starte ein Quiz und öffne die Anmeldung!")
    async def partyquiz(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        
        if guild_id in self.active_games:
            await ctx.send("❌ Ein Quiz läuft bereits in diesem Server!")
            return

        questions = load_questions()
        if len(questions) < 5:
            await ctx.send("❌ Es sind noch nicht genügend Fragen vorhanden (mind. 5).")
            return

        registration_view = RegistrationView(self)
        
        embed = discord.Embed(
            title="🎯 Party-Quiz Anmeldung geöffnet!",
            description=f"Drücke den **'Mitspielen!'**-Button, um am Quiz teilzunehmen.\nDie Anmeldung schließt in **{self.REGISTRATION_TIME} Sekunden**.",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed, view=registration_view)
        
        registration_successful = await registration_view.wait()

        allowed_player_ids = registration_view.players
        
        if len(allowed_player_ids) < self.MIN_PLAYERS:
            await ctx.send(f"❌ Das Quiz wurde abgebrochen. Es wurden nicht genügend Spieler (mind. {self.MIN_PLAYERS}) gefunden.")
            return

        selected_questions = random.sample(questions, k=min(20, len(questions)))
        game = QuizGame(ctx, selected_questions, allowed_player_ids)
        self.active_games[guild_id] = game
        
        player_mentions = ", ".join(f"<@{p_id}>" for p_id in allowed_player_ids)
        await ctx.send(f"🎉 **Anmeldung beendet!** Das Quiz startet mit {len(allowed_player_ids)} Spielern: {player_mentions}")
        await game.next_question()
        
        if guild_id in self.active_games:
            del self.active_games[guild_id]

# --- UI für die Spieler-Registrierung ---

class RegistrationView(View):
    def __init__(self, cog: PartyQuiz):
        super().__init__(timeout=cog.REGISTRATION_TIME)
        self.players = set()
        self.cog = cog
        
        self.add_item(RegistrationButton(self))

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            
            new_embed = self.message.embeds[0]
            new_embed.title = "🎯 Anmeldung geschlossen!"
            new_embed.description = f"**{len(self.players)}** Spieler haben sich angemeldet."
            new_embed.color = discord.Color.red()
            
            await self.message.edit(embed=new_embed, view=self)
            
        self.stop() 

class RegistrationButton(Button):
    def __init__(self, view: RegistrationView):
        super().__init__(label="Mitspielen!", style=discord.ButtonStyle.primary)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        if user_id in self.view_ref.players:
            await interaction.response.send_message("Du bist bereits angemeldet!", ephemeral=True)
            return

        self.view_ref.players.add(user_id)
        
        await interaction.response.send_message("✅ Du bist registriert! Das Quiz startet bald.", ephemeral=True)
        
        new_embed = self.view_ref.message.embeds[0]
        new_embed.description = f"Drücke den **'Mitspielen!'**-Button, um am Quiz teilzunehmen.\nAngemeldete Spieler: **{len(self.view_ref.players)}**\nDie Anmeldung schließt in Kürze."
        await self.view_ref.message.edit(embed=new_embed, view=self.view_ref)

# -------------------
#  QuizGame und Quiz-Buttons
# -------------------

class QuizGame:
    """Verwaltet ein einzelnes Party-Quiz"""
    
    TIME_PER_QUESTION = 15  

    def __init__(self, ctx: commands.Context, questions, allowed_players: list):
        self.ctx = ctx
        self.questions = questions
        self.scores = {}  
        self.current_index = 0
        self.message = None
        self.allowed_players = set(allowed_players) 

    async def next_question(self):
        if self.current_index >= len(self.questions):
            await self.finish()
            return

        question = self.questions[self.current_index]
        view = PartyQuizView(question["options"], question["answer"], self)
        
        embed = discord.Embed(
            title=f"🧠 Frage {self.current_index + 1}/{len(self.questions)} (Zeit: {self.TIME_PER_QUESTION}s)",
            description=f"**{question['question']}**",
            color=discord.Color.blurple()
        )
        
        self.message = await self.ctx.send(embed=embed, view=view)
        
        await asyncio.sleep(self.TIME_PER_QUESTION)

        for item in view.children:
            if isinstance(item, Button):
                item.disabled = True
                if item.label == question["answer"]:
                    item.style = discord.ButtonStyle.success 

        await self.message.edit(
            content=f"⏱️ Zeit abgelaufen! Die richtige Antwort war: **{question['answer']}**", 
            embed=embed, 
            view=view
        )
        
        self.current_index += 1
        await self.next_question()

    async def register_answer(self, user: discord.User, answer: str, correct_answer: str):
        """Registriert die Antwort eines Spielers und aktualisiert den Score."""
        if user.id not in self.scores:
            self.scores[user.id] = 0
            
        if answer == correct_answer:
            self.scores[user.id] += 1

    async def finish(self):
        if not self.scores:
            await self.ctx.send("⚠️ Niemand von den zugelassenen Spielern hat am Quiz teilgenommen.")
            return

        final_ranking_data = []
        for player_id in self.allowed_players:
            score = self.scores.get(player_id, 0)
            final_ranking_data.append((player_id, score))
            
        final_ranking_data.sort(key=lambda x: x[1], reverse=True)

        description = ""
        for idx, (user_id, score) in enumerate(final_ranking_data, start=1):
            member = self.ctx.guild.get_member(user_id)
            name = member.display_name if member else f"Unbekannter Spieler ({user_id})"
            
            if idx == 1: emoji = "🥇"
            elif idx == 2: emoji = "🥈"
            elif idx == 3: emoji = "🥉"
            else: emoji = f"{idx}."
                
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
        super().__init__(timeout=game.TIME_PER_QUESTION)
        self.correct_answer = correct_answer
        self.game = game
        self.already_answered = set() 
        
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
        user_id = interaction.user.id
        
        if user_id not in self.game.allowed_players:
            await interaction.response.send_message("❌ Du bist nicht als Teilnehmer dieses Quiz zugelassen. Die Anmeldung ist beendet.", ephemeral=True)
            return
        
        if user_id in self.view_ref.already_answered:
            await interaction.response.send_message("❌ Du hast diese Frage bereits beantwortet.", ephemeral=True)
            return

        self.view_ref.already_answered.add(user_id)
        
        is_correct = self.label == self.correct_answer
        await self.game.register_answer(interaction.user, self.label, self.correct_answer)
        
        result_text = "richtig" if is_correct else "falsch"
        emoji = "✅" if is_correct else "❌"
        
        await interaction.response.send_message(
            f"{emoji} Deine Antwort **{self.label}** wurde registriert. Das war **{result_text}**! Warte auf die nächste Frage.", 
            ephemeral=True
        )

# --- Setup des Cogs ---

async def setup(bot: commands.Bot):
    await bot.add_cog(PartyQuiz(bot))
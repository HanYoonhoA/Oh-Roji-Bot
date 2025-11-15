import discord
import random
import asyncio
import os
import threading
from collections import defaultdict
from discord.ext import commands
from discord import app_commands
from media_links import gifs

# load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

# ⚠️ Token from environment (much safer than hardcoding)
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ---- Import question banks ----
from Question_Banks.Theory_of_Flight import week1_questions as week1_theory
from Question_Banks.Theory_of_Flight import week2_questions as week2_theory
from Question_Banks.Theory_of_Flight import week3_questions as week3_theory
from Question_Banks.Theory_of_Flight import week4_questions as week4_theory
from Question_Banks.Theory_of_Flight import week5_questions as week5_theory
from Question_Banks.Intro_to_CARs import week1_questions as week1_cars
from Question_Banks.Intro_to_CARs import week2_questions as week2_cars
from Question_Banks.Intro_to_CARs import week3_questions as week3_cars
from Question_Banks.Intro_to_CARs import week4_questions as week4_cars
from Question_Banks.Intro_to_CARs import week5_questions as week5_cars
from Question_Banks.Metallurgy import week1_questions as week1_met
from Question_Banks.Metallurgy import week2_questions as week2_met
from Question_Banks.Metallurgy import week3_questions as week3_met
from Question_Banks.Metallurgy import week4_questions as week4_met
from Question_Banks.Metallurgy import week5_questions as week5_met

# ------------ Review Notes Links ------------
review_links = {
    "Theory of Flight": {
        "week1": "https://docs.google.com/document/d/1usirzzuqvw3YF7DdT2ud-cZZnyyUz4yRZDngFhVew4g/edit?usp=sharing",
        "week2": "https://docs.google.com/document/d/1tgK5yVfs-bWmoGRpytdWvoVq3YUSWyda6Ot2-j28b2Q/edit?usp=sharing",
        "week3": "https://docs.google.com/document/d/1Y9lHSetcbGQutvdwFuIC5tFijOmnUHApiT0iCIXfHzE/edit?usp=sharing",
        "all_weeks": "https://docs.google.com/document/d/1wJrZvJtR9IiUTSKOPZlsE6eK50hJTuctivMQ90iJKBM/edit?usp=sharing",
        "week4": "https://docs.google.com/document/d/19xED-MX0qboM8W6AHsU9N37ufteFZiuDaRTJqZoyIks/edit?usp=sharing",
        "week5": "https://docs.google.com/document/d/1sJwQpJVW4vc-7Wh1sW8lHtp7UkDOHc5zWNpOOdgrQz0/edit?usp=sharing",
    },
    "Metallurgy": {
        "week1": "https://docs.google.com/document/d/1l9xySamiWW_aoemBrdJ4VTD2emN3Q_3WaNvnS_U8SQE/edit?usp=sharing",
        "week2": "https://docs.google.com/document/d/178S_BtXE3QGxhpfmDv_HVlvB8v2sd6IhodtglTkfB4c/edit?usp=sharing",
        "week3": "https://docs.google.com/document/d/1hIgxVswQjXGYo4hFDgaYa6vC8t5NA5CJjAVAvIIccZk/edit?usp=sharing",
        "week5": "https://docs.google.com/document/d/10oSQF0fNUUvh_9vo1LJHnjHzgegr7vMWOe7JaRxgX4E/edit?usp=sharing",
    },
    "Intro to CARs": {
        "week1": "https://docs.google.com/document/d/1yvkjvgEU5-jvz3J39osdNuBGSLt759aWBDJW8YDa3Rc/edit?usp=sharing",
        "week2": "https://docs.google.com/document/d/1CT_W0p2s16qU51PDok42YORWKhi-KSBfRNVsg2F_egM/edit?usp=sharing",
        "week3": "https://docs.google.com/document/d/1SKVaNWXe2qUny9wKqRf-RbDsXPpfvqGwYWzC07kk2tk/edit?usp=sharing",
        "all_weeks": "https://docs.google.com/document/d/1W2u7Y_6YOAWmYXs6OfBLIbJKG6RsnV8HLA-JDsZKxtE/edit?usp=sharing"
    }
}

review_note = (
    "⚠️ Please be respectful. These notes were created by fellow students and are intended for their own understanding. "
    "Do not modify or add inappropriate content. However, you’re welcome to suggest corrections or improvements if you spot any errors. "
    "I’m borrowing these notes purely for study purposes."
)

# ------------ Bot Setup ------------
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

# Active timers per user {user_id: question_index}
active_timers = {}

# Active sessions
active_sessions = 0
class_sessions = {
    "Theory of Flight": 0,
    "Intro to CARs": 0,
    "Metallurgy": 0
}

# Track active channels where quizzes are running
active_channels = set()
channel_sessions = defaultdict(int)  # channel_id -> active quiz count

# ------------ Global error handler ------------
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Unknown command. Try `/help`.")
    else:
        print(f"⚠️ Error: {error}")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    await interaction.response.send_message("⚠️ An error occurred while processing your request.", ephemeral=True)
    print(f"⚠️ Slash Command Error: {error}")


# ------------ /start command ------------
@bot.tree.command(name="start", description="Begin studying with the bot!")
async def start(interaction: discord.Interaction):
    embed = discord.Embed(
        title="👋 Welcome to Oh Roji!",
        description=(
            "I’m your study buddy. Here’s how to use me:\n"
            "1️⃣ `/start` → Begin\n"
            "2️⃣ Choose a study mode\n"
            "3️⃣ Pick a class/week\n"
            "4️⃣ Answer questions and track your score!"
        ),
        color=discord.Color.blurple()
    )
    view = discord.ui.View(timeout=None)
    view.add_item(StudyModeButton("Mid Term (30%)", "midterm", True))
    view.add_item(StudyModeButton("Quiz (5%)", "quiz", True))
    view.add_item(StudyModeButton("Final Exam (50%)", "final", True))
    await interaction.response.send_message(embed=embed, view=view)

# ------------ Info & Help ------------
@bot.tree.command(name="info", description="Learn more about Oh Roji")
async def info_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ℹ️ About Oh Roji",
        description=(
            "I’m **Oh Roji**, your reluctant but loyal study bot. 🤖\n\n"
            "📚 I cover **Theory of Flight**, **Intro to CARs**, and **Metallurgy**.\n"
            "All questions are pulled straight from your review sheets. Most of them were contributed by fellow students, so if anything feels off, you can use `/improve` to send feedback.\n\n"
            "Please be respectful of the notes attached to each question. They’re not mine, but generously shared by other students. I just keep the bot running."
        ),
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="help", description="How to use the bot")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Help Guide",
        description=(
            "`/start` → Begin studying\n"
            "`/help` → Show help\n"
            "`/info` → Learn about me\n\n"
            "Once started, use the buttons to navigate modes and classes."
        ),
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ------------ Status command ------------
@bot.tree.command(name="status", description="Show current active quizzes")
async def status(interaction: discord.Interaction):
    desc = f"📊 Total active quizzes: **{active_sessions}**\n\n"
    for cls, count in class_sessions.items():
        desc += f"• {cls}: {count}\n"
    desc += f"\n📝 Active channels: {len(active_channels)}"
    await interaction.response.send_message(desc, ephemeral=True)

# ------------ Welcome ------------
@bot.event
async def on_member_join(member):
    try:
        await member.send(
            f"👋 Welcome to **{member.guild.name}**, {member.mention}!\n"
            "I’m **Oh Roji Bot**, here to help you study.\nType `/start` to begin!"
        )
    except discord.Forbidden:
        print(f"⚠️ Couldn’t DM {member.name} (DMs disabled).")

# ------------ Buttons ------------
class StudyModeButton(discord.ui.Button):
    def __init__(self, label, mode, available):
        style = discord.ButtonStyle.primary if available else discord.ButtonStyle.secondary
        super().__init__(label=label, style=style, disabled=not available)
        self.mode = mode

    async def callback(self, interaction: discord.Interaction):
        view = discord.ui.View(timeout=None)

        if self.mode == "midterm":
            view.add_item(ClassButton("Theory of Flight", "midterm_theory"))
            view.add_item(ClassButton("Intro to CARs", "midterm_cars"))
            view.add_item(ClassButton("Metallurgy", "midterm_met"))

        elif self.mode == "quiz":
            view.add_item(ClassButton("Theory of Flight", "quiz_theory"))
            view.add_item(ClassButton("Intro to CARs", "quiz_cars"))
            view.add_item(ClassButton("Metallurgy", "quiz_met"))

        elif self.mode == "final":
            view.add_item(ClassButton("Theory of Flight", "final_theory"))
            view.add_item(ClassButton("Intro to CARs", "final_cars"))
            view.add_item(ClassButton("Metallurgy", "final_met"))

        await interaction.response.edit_message(
            embed=discord.Embed(
                title=f"🎯 {self.label}",
                description="Choose your class:",
                color=discord.Color.blurple()
            ),
            view=view
        )

class ClassButton(discord.ui.Button):
    def __init__(self, label, mode):
        super().__init__(label=label, style=discord.ButtonStyle.success)
        self.mode = mode

    async def callback(self, interaction: discord.Interaction):

        # ---------------- MIDTERM ----------------
        if self.mode == "midterm_theory":
            qs = week1_theory[:6] + week2_theory[:12] + week3_theory[:12]
        elif self.mode == "midterm_cars":
            qs = week1_cars[:18] + week2_cars[:5] + week3_cars[:7]
        elif self.mode == "midterm_met":
            qs = week1_met[:10] + week2_met[:10] + week3_met[:10]

            # assign class tag
        elif self.mode.startswith("midterm_"):
            qs = []

        # ---------------- QUIZ ----------------
        elif self.mode == "quiz_theory":
            view = discord.ui.View(timeout=None)
            view.add_item(WeekButton("Week 1", week1_theory, "Theory of Flight"))
            view.add_item(WeekButton("Week 2", week2_theory, "Theory of Flight"))
            view.add_item(WeekButton("Week 3", week3_theory, "Theory of Flight"))
            view.add_item(WeekButton("Week 4", week4_theory, "Theory of Flight"))
            view.add_item(WeekButton("Week 5", week5_theory, "Theory of Flight"))
            return await interaction.response.edit_message(
                embed=discord.Embed(
                    title="📝 Quiz (5%) — Theory of Flight",
                    description="Pick a week (5 random questions)",
                    color=discord.Color.blue()
                ),
                view=view
            )

        elif self.mode == "quiz_cars":
            view = discord.ui.View(timeout=None)
            view.add_item(WeekButton("Week 1", week1_cars, "Intro to CARs"))
            view.add_item(WeekButton("Week 2", week2_cars, "Intro to CARs"))
            view.add_item(WeekButton("Week 3", week3_cars, "Intro to CARs"))
            view.add_item(WeekButton("Week 4", week4_cars, "Intro to CARs"))
            view.add_item(WeekButton("Week 5", week5_cars, "Intro to CARs"))
            return await interaction.response.edit_message(
                embed=discord.Embed(
                    title="📝 Quiz (5%) — Intro to CARs",
                    description="Pick a week (5 random questions)",
                    color=discord.Color.blue()
                ),
                view=view
            )

        elif self.mode == "quiz_met":
            view = discord.ui.View(timeout=None)
            view.add_item(WeekButton("Week 1", week1_met, "Metallurgy"))
            view.add_item(WeekButton("Week 2", week2_met, "Metallurgy"))
            view.add_item(WeekButton("Week 3", week3_met, "Metallurgy"))
            view.add_item(WeekButton("Week 4", week4_met, "Metallurgy"))
            view.add_item(WeekButton("Week 5", week5_met, "Metallurgy"))
            return await interaction.response.edit_message(
                embed=discord.Embed(
                    title="📝 Quiz (5%) — Metallurgy",
                    description="Pick a week (5 random questions)",
                    color=discord.Color.blue()
                ),
                view=view
            )

        # ---------------- FINAL ----------------
        elif self.mode == "final_theory":
            qs = []
            qs += random.sample(week1_theory, min(2, len(week1_theory)))
            qs += random.sample(week2_theory, min(7, len(week2_theory)))
            qs += random.sample(week3_theory, min(14, len(week3_theory)))
            qs += random.sample(week4_theory, min(10, len(week4_theory)))
            qs += random.sample(week5_theory, min(17, len(week5_theory)))

        elif self.mode == "final_cars":
            qs = []
            qs += random.sample(week1_cars, min(10, len(week1_cars)))
            qs += random.sample(week2_cars, min(10, len(week2_cars)))
            qs += random.sample(week3_cars, min(10, len(week3_cars)))
            qs += random.sample(week4_cars, min(10, len(week4_cars)))
            qs += random.sample(week5_cars, min(10, len(week5_cars)))

        elif self.mode == "final_met":
            qs = []
            qs += random.sample(week1_met, min(10, len(week1_met)))
            qs += random.sample(week2_met, min(10, len(week2_met)))
            qs += random.sample(week3_met, min(10, len(week3_met)))
            qs += random.sample(week5_met, min(20, len(week5_met)))

        else:
            qs = []

        if qs:  # start quiz immediately (midterm/final only)
            for q in qs:
                q["class"] = self.label

            embed = discord.Embed(
                title=f"📚 {self.label} — {self.mode.split('_')[0].capitalize()}",
                description=f"{len(qs)} questions incoming for {interaction.user.mention}!",
                color=discord.Color.gold()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            await start_quiz(interaction, qs)



class WeekButton(discord.ui.Button):
    def __init__(self, label, questions, class_label):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.questions = questions
        self.class_label = class_label

    async def callback(self, interaction: discord.Interaction):
        qs = random.sample(self.questions, min(15, len(self.questions)))
        for q in qs:                # Change to 5 in the future
            q["class"] = self.class_label

        embed = discord.Embed(
            title=f"📚 {self.class_label} — {self.label} Quiz",
            description=f"5 questions incoming for {interaction.user.mention}!",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await start_quiz(interaction, qs)

# ------------ Quiz System ------------
class QuizView(discord.ui.View):
    def __init__(self, question, q_index, score, user, questions, wrongs, streak):
        super().__init__(timeout=None)
        self.question = question
        self.q_index = q_index
        self.score = score
        self.user = user
        self.questions = questions
        self.wrongs = wrongs
        self.streak = streak

        for idx, choice in enumerate(question["choices"]):
            self.add_item(AnswerButton(idx, choice, question["answerIndex"], self))

class AnswerButton(discord.ui.Button):
    def __init__(self, idx, label, correct_idx, parent_view):
        super().__init__(label=f"{chr(65+idx)}", style=discord.ButtonStyle.primary)
        self.idx = idx
        self.label_text = label
        self.correct_idx = correct_idx
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.parent_view.user:
            return await interaction.response.send_message("🚫 Not your quiz!", ephemeral=True)

        active_timers.pop(interaction.user.id, None)

        if self.idx == self.correct_idx:
            self.parent_view.score += 1
            feedback = discord.Embed(
                title="✅ Correct!",
                description=f"Nice one, {interaction.user.mention}!",
                color=discord.Color.green()
            )
        else:
            self.parent_view.wrongs.append({
                "q": self.parent_view.question["q"],
                "your": self.label_text,
                "correct": self.parent_view.question["choices"][self.correct_idx]
            })
            feedback = discord.Embed(
                title="❌ Incorrect",
                description=(
                    f"**Q:** {self.parent_view.question['q']}\n"
                    f"👉 Your Answer: {self.label_text}\n"
                    f"✅ Correct: {self.parent_view.question['choices'][self.correct_idx]}"
                ),
                color=discord.Color.red()
            )

        await interaction.response.edit_message(embed=feedback, view=None)
        await next_question(
            interaction,
            self.parent_view.q_index + 1,
            self.parent_view.score,
            self.parent_view.questions,
            self.parent_view.wrongs,
            0
        )

# ------------ Feedback Command ------------
@bot.tree.command(name="improve", description="Submit feedback or suggestions for the bot")
@app_commands.describe(feedback="Write your suggestion or report confusing questions with details")
async def improve(interaction: discord.Interaction, feedback: str):
    user_mention = f"<@{interaction.user.id}>"
    line = f"{user_mention} < {feedback} >\n"
    with open("improvements.txt", "a", encoding="utf-8") as f:
        f.write(line)

    embed = discord.Embed(
        title="✅ Feedback Received",
        description=f"Thanks {interaction.user.mention}! Your suggestion has been logged.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ------------ Quiz Flow ------------
async def question_timer(interaction, q_index, score, questions, wrongs, user, streak):
    await asyncio.sleep(60)
    if active_timers.get(user.id) == q_index:
        wrongs.append({
            "q": questions[q_index]["q"],
            "your": "⏱ No Answer",
            "correct": questions[q_index]["choices"][questions[q_index]["answerIndex"]]
        })
        embed = discord.Embed(
            title="⏱ Time’s Up!",
            description=f"{user.mention} Q{q_index+1} skipped.",
            color=discord.Color.dark_grey()
        )
        await interaction.followup.send(embed=embed)
        await next_question(interaction, q_index+1, score, questions, wrongs, streak+1)

async def start_quiz(interaction, questions):
    global active_sessions
    if not questions:
        return await interaction.followup.send("⚠️ No questions available.", ephemeral=True)

    active_sessions += 1
    class_name = questions[0].get("class", None)
    if class_name in class_sessions:
        class_sessions[class_name] += 1

    # Track the channel properly
    channel_id = getattr(interaction.channel, "id", None)
    if channel_id is not None:
        channel_sessions[channel_id] += 1
        active_channels.add(channel_id)

    print(f"📊 Active quizzes: {active_sessions}")
    for cls, count in class_sessions.items():
        print(f"   └ {cls}: {count}")

    randomized = random.sample(questions, len(questions))
    await next_question(interaction, 0, 0, randomized, [], 0)

async def next_question(interaction, q_index, score, questions, wrongs, streak):
    if q_index >= len(questions):
        return await end_quiz(interaction, score, questions, wrongs)
    if streak >= 3:
        return await end_quiz(interaction, score, questions, wrongs, True)

    q = questions[q_index]
    view = QuizView(q, q_index, score, interaction.user, questions, wrongs, streak)
    embed = discord.Embed(
        title=f"🎯 {interaction.user.mention} — Question {q_index+1}/{len(questions)}",
        description=q["q"],
        color=discord.Color.blurple()
    )
    for idx, choice in enumerate(q["choices"]):
        embed.add_field(name=chr(65+idx), value=choice, inline=False)

    active_timers[interaction.user.id] = q_index
    asyncio.create_task(question_timer(interaction, q_index, score, questions, wrongs, interaction.user, streak))

    await interaction.followup.send(embed=embed, view=view)

# ------------ End Quiz (FIXED SECTION) ------------
async def end_quiz(interaction, score, questions, wrongs, ended_by_streak=False):
    global active_sessions
    if active_sessions > 0:
        active_sessions -= 1

    class_name = questions[0].get("class", None) if questions else None
    if class_name in class_sessions and class_sessions[class_name] > 0:
        class_sessions[class_name] -= 1

    # Decrement channel-specific session count and remove channel if it reaches 0
    channel_id = getattr(interaction.channel, "id", None)
    if channel_id is not None:
        channel_sessions[channel_id] = channel_sessions.get(channel_id, 0) - 1
        if channel_sessions[channel_id] <= 0:
            channel_sessions.pop(channel_id, None)
            active_channels.discard(channel_id)

    print(f"📊 Active quizzes: {active_sessions}")
    for cls, count in class_sessions.items():
        print(f"   └ {cls}: {count}")

    desc = f"🏆 {interaction.user.mention}, you scored **{score}/{len(questions)}**!"
    if ended_by_streak:
        desc += "\n⚠️ Quiz ended after 3 missed questions."

    embed = discord.Embed(title="🎉 Quiz Complete", description=desc, color=discord.Color.gold())

    if gifs:
        embed.set_image(url=random.choice(gifs))

    if questions and class_name in review_links:
        links_text = ""
        for week, link in review_links[class_name].items():
            links_text += f"**{week.capitalize()}**: [Click Here]({link})\n"
        links_text += f"\n{review_note}"

        # ✅ FIX: split embed fields into 1024-character chunks
        chunks = [links_text[i:i+1024] for i in range(0, len(links_text), 1024)]
        for i, chunk in enumerate(chunks):
            field_name = f"📄 {class_name} Notes (Part {i+1})" if len(chunks) > 1 else f"📄 {class_name} Notes"
            embed.add_field(name=field_name, value=chunk, inline=False)

    view = None
    if wrongs:
        view = discord.ui.View(timeout=None)
        view.add_item(ReviewButton(wrongs))

    if view is not None:
        await interaction.followup.send(embed=embed, view=view)
    else:
        await interaction.followup.send(embed=embed)

# ------------ ReviewButton (FIXED) ------------
class ReviewButton(discord.ui.Button):
    def __init__(self, wrongs):
        super().__init__(label="📖 Review Mistakes", style=discord.ButtonStyle.danger)
        self.wrongs = wrongs

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="❌ Mistakes Review", color=discord.Color.red())
        for wa in self.wrongs:
            text_value = f"👉 Your: {wa['your']}\n✅ Correct: {wa['correct']}"
            # ✅ Fix: truncate if longer than 1024 chars
            if len(text_value) > 1024:
                text_value = text_value[:1021] + "..."
            embed.add_field(name=wa["q"][:256], value=text_value, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ------------ Startup ------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("✨ Use /start in Discord to begin!")
    print("💬 Type into this terminal with `> your message` to send to active quiz channels")

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Missing DISCORD_BOT_TOKEN environment variable")

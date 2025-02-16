import discord
from discord.ext import commands
from discord import app_commands  # For application commands
from openai import OpenAI
import aiohttp

# Bot setup with necessary permissions
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Zukijourney API setup
client = OpenAI(base_url="https://api.zukijourney.com/v1", api_key="zu-14cbdc74fc6e5cdcbc2336b96fda2680")

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # Register application commands once the bot is ready
    await bot.tree.sync()

# Slash Command: AI interaction
@bot.tree.command(name="ai", description="Interact with the AI to check math solutions")
async def ai_interaction(interaction: discord.Interaction, question_and_answer: str):
    # Sending request to AI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Check if the user's math solution is correct. If incorrect, suggest a corrected LaTeX version."},
            {"role": "user", "content": f"Check this math working out:\n{question_and_answer}"}
        ]
    )

    evaluation = response.choices[0].message.content

    # Send back AI evaluation
    await interaction.response.send_message(f"Math check result:\n```latex\n{evaluation}\n```")

    # React to correctness
    if "incorrect" in evaluation.lower():
        await interaction.message.add_reaction("❌")
    else:
        await interaction.message.add_reaction("✅")

# Run the bot
bot.run("MTM0MDI2NzE0ODcyMjgzMTQzMA.G5sJ2G.6sbWHqneSAgpvDTaUWfHnssLlRX0SkwrZQEtSw")

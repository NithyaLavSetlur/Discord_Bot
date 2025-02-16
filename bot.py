import discord
from discord.ext import commands
from discord import app_commands
from openai import OpenAI
import aiohttp
import pytesseract
from PIL import Image
import io

# Bot setup with necessary permissions
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.reactions = True
intents.members = True  # If you need to track member updates

bot = commands.Bot(command_prefix="!", intents=intents)

# Zukijourney API setup
client = OpenAI(base_url="https://api.zukijourney.com/v1", api_key="zu-14cbdc74fc6e5cdcbc2336b96fda2680")

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # Register application commands once the bot is ready
    await bot.tree.sync()

# Function to process OCR on images
async def process_image(image_url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            img_data = await resp.read()
            img = Image.open(io.BytesIO(img_data))
            text = pytesseract.image_to_string(img)
            return text

# Slash Command: AI interaction
@bot.tree.command(name="ai", description="Interact with the AI to check math solutions")
async def ai_interaction(interaction: discord.Interaction, question_and_answer: str):
    # Sending request to AI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Answer the user's math question if they haven't provided a solution."},
            {"role": "system", "content": "If the user has provided a question and solution, check if the user's math solution is correct. If incorrect, suggest a corrected LaTeX version."},
            {"role": "user", "content": f"Check this math working out/question:\n{question_and_answer}"}
        ]
    )

    evaluation = response.choices[0].message.content

    # Send back AI evaluation without a code block (as a normal message)
    await interaction.response.send_message(f"Math check result:\n{evaluation}")

    # React to correctness
    if "incorrect" in evaluation.lower():
        await interaction.message.add_reaction("❌")
    else:
        await interaction.message.add_reaction("✅")

# Event to handle images in messages
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type.startswith("image"):
                # Process the image using OCR
                image_text = await process_image(attachment.url)
                if image_text.strip():
                    # Send extracted text to the AI for evaluation
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Answer the user's math question if they haven't provided a solution."},
                            {"role": "system", "content": "If the user has provided a question and solution, check if the user's math solution is correct. If incorrect, suggest a corrected LaTeX version."},
                            {"role": "user", "content": f"Check this math working out/question:\n{image_text}"}
                        ]
                    )

                    evaluation = response.choices[0].message.content
                    await message.channel.send(f"Math check result for image:\n{evaluation}")

                    # React to correctness
                    if "incorrect" in evaluation.lower():
                        await message.add_reaction("❌")
                    else:
                        await message.add_reaction("✅")
                else:
                    await message.channel.send("No readable text found in the image.")

    # Allow commands to be processed by the bot
    await bot.process_commands(message)

# Run the bot
bot.run("MTM0MDI2NzE0ODcyMjgzMTQzMA.G5sJ2G.6sbWHqneSAgpvDTaUWfHnssLlRX0SkwrZQEtSw")

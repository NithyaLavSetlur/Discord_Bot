import discord
from discord.ext import commands
from discord import app_commands
from openai import OpenAI
import aiohttp
import pytesseract
from PIL import Image
import io
import asyncio
import os
import sys
from asyncio import WindowsSelectorEventLoopPolicy
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Protect against Windows event loop error
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

# === CONFIG ===
COMMAND_PREFIX = "!"
TARGET_GUILD_ID = 1340605014523117620  # Replace with your actual test guild/server ID
TARGET_IMAGE_CHANNEL_ID = 123456789012345678  # Replace with the channel ID where images are allowed

# === BOT SETUP ===
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.reactions = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
client = OpenAI(
    base_url="https://api.zukijourney.com/v1",
    api_key=os.getenv("OPENAI_API_KEY")
)

# === ON READY ===
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        guild = discord.Object(id=TARGET_GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ Synced {len(synced)} slash command(s) to test guild.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# === IMAGE PROCESSING FUNCTION ===
async def process_image(image_url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            img_data = await resp.read()
            img = Image.open(io.BytesIO(img_data))
            text = pytesseract.image_to_string(img)
            return text

# === SLASH COMMAND: /ai ===
@bot.tree.command(name="ai", description="Check your math solution with AI")
@app_commands.describe(question_and_answer="Your question and/or solution")
async def ai(interaction: discord.Interaction, question_and_answer: str):
    await interaction.response.defer()  # Acknowledge immediately to avoid timeout

    print("🧠 Received /ai interaction")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": (
                "If a question is provided without a solution, solve it using LaTeX. "
                "If a full solution is provided, verify it. If incorrect, give a corrected version using LaTeX."
            )},
            {"role": "user", "content": question_and_answer}
        ]
    )

    evaluation = response.choices[0].message.content

    await interaction.followup.send(f"📊 Math Check Result:\n```latex\n{evaluation}\n```")

    # React based on evaluation
    if "incorrect" in evaluation.lower():
        await interaction.channel.send("❌ Your solution appears incorrect.")
    else:
        await interaction.channel.send("✅ Correct!")

# === COMMAND: !check (text message based) ===
@bot.command()
async def check(ctx, *, question_and_answer):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Check the solution for correctness. If incorrect, suggest a corrected LaTeX version."},
            {"role": "user", "content": question_and_answer}
        ]
    )

    evaluation = response.choices[0].message.content
    await ctx.send(f"📊 Math Check Result:\n```latex\n{evaluation}\n```")

    # React
    if "incorrect" in evaluation.lower():
        await ctx.message.add_reaction("❌")
    else:
        await ctx.message.add_reaction("✅")

# === IMAGE OCR & EVALUATION ===
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Only handle image processing in specific channel
    if message.channel.id == TARGET_IMAGE_CHANNEL_ID and message.attachments:
        for attachment in message.attachments:
            if attachment.filename.lower().endswith(("png", "jpg", "jpeg")):
                await message.channel.send("🔍 Processing image...")
                extracted_text = await process_image(attachment.url)

                if not extracted_text.strip():
                    await message.channel.send("❌ Could not extract any text.")
                    return

                await message.channel.send(f"📤 Extracted Text:\n```latex\n{extracted_text}\n```")

                # Evaluate the OCR text
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Check the extracted math solution for correctness. Use LaTeX formatting."},
                        {"role": "user", "content": extracted_text}
                    ]
                )
                evaluation = response.choices[0].message.content

                await message.channel.send(f"📊 Math Check Result:\n```latex\n{evaluation}\n```")

                if "incorrect" in evaluation.lower():
                    await message.add_reaction("❌")
                else:
                    await message.add_reaction("✅")

    await bot.process_commands(message)

# === RUN THE BOT ===
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    if not TOKEN:
        raise Exception("❌ DISCORD_BOT_TOKEN environment variable not set.")
    bot.run(TOKEN)

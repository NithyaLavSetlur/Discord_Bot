import discord
from discord.ext import commands
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

bot = commands.Bot(command_prefix="!", intents=intents)

# Zukijourney API setup
client = OpenAI(base_url="https://api.zukijourney.com/v1", api_key="zu-14cbdc74fc6e5cdcbc2336b96fda2680")

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Command to check math answers (text-based)
@bot.command()
async def check(ctx, *, question_and_answer):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Check if the user's math solution is correct. If incorrect, suggest a corrected LaTeX version."},
            {"role": "user", "content": f"Check this math working out:\n{question_and_answer}"}
        ]
    )

    evaluation = response.choices[0].message.content
    await ctx.send(f"Math check result:\n```latex\n{evaluation}\n```")

    # React to correctness
    if "incorrect" in evaluation.lower():
        await ctx.message.add_reaction("❌")
    else:
        await ctx.message.add_reaction("✅")

# Event: Detect images, extract math, and check correctness
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Ignore bot's own messages

    if message.attachments:  # If message contains an image
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ["png", "jpg", "jpeg"]):
                await message.channel.send("Processing image... ⏳")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as response:
                        image_data = await response.read()

                # Convert image to text using OCR
                image = Image.open(io.BytesIO(image_data))
                extracted_text = pytesseract.image_to_string(image)

                if not extracted_text.strip():
                    await message.channel.send("❌ Could not extract text from the image.")
                    return

                await message.channel.send(f"Extracted LaTeX from image:\n```latex\n{extracted_text}\n```")

                # Check extracted math solution
                api_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Check if the user's math solution is correct. If incorrect, suggest a corrected LaTeX version."},
                        {"role": "user", "content": f"Check this math working out:\n{extracted_text}"}
                    ]
                )

                evaluation = api_response.choices[0].message.content
                await message.channel.send(f"Math check result:\n```latex\n{evaluation}\n```")

                # React to correctness
                if "incorrect" in evaluation.lower():
                    await message.add_reaction("❌")
                else:
                    await message.add_reaction("✅")

    await bot.process_commands(message)  # Process commands

# Run the bot
bot.run("MTM0MDI2NzE0ODcyMjgzMTQzMA.GyvruB.zIxe6m6Lu1As3_Y7l-mJIINDYapGrzYGL4cds0")

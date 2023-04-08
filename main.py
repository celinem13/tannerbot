import os
import json
import random
import aiohttp
import asyncpraw
import asyncio
import youtube_dl
import discord
from discord.ext import commands

from discord import voice_client
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

client_id = os.environ['reddit_client_id']
password = os.environ['your_reddit_password']
client_secret = os.environ['reddit_client_secret']
user_agent = os.environ['reddit_user_agent']

reddit = asyncpraw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    username="tannerbot227",
    password=password,
    user_agent=user_agent
)

sad_words = [
    "sad", "SAD", "Sad", "SAd", "sAD", "sAd", "saD", "SaD", "depressed",
    "unhappy", "angry", "anger", "miserable"
]

starter_encouragements = [
    "Cheer up!", "Hang in there.", "You are a great person!", "We love you",
    "I'm here for you", "I love you", "Let me give you a hug, friend"
]

encouragements = []

if "responding" not in os.environ:
    os.environ["responding"] = "True"

responding_lock = asyncio.Lock()
responding = os.getenv("responding").lower() in ["true", "yes", "1"]

if "encouragements" in os.environ:
    encouragements_str = os.environ["encouragements"]
    encouragements = json.loads(encouragements_str)
else:
    encouragements = starter_encouragements

encouragements_lock = asyncio.Lock()


async def get_quote():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://zenquotes.io/api/random") as response:
            json_data = await response.json()
            quote = json_data[0]["q"] + " -" + json_data[0]["a"]
            return quote


async def update_encouragements(encouraging_message):
    encouragements.append(encouraging_message)
    os.environ["encouragements"] = json.dumps(encouragements)


async def delete_encouragement(index):
    async with encouragements_lock:
        if len(encouragements) > index:
            del encouragements[index]
            os.environ["encouragements"] = json.dumps(encouragements)


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


@bot.command()
async def inspire(ctx):
    quote = await get_quote()
    await ctx.send(quote)


@bot.command()
async def add_encouragement(ctx, encouraging_message):
    await update_encouragements(encouraging_message)
    await ctx.send(f"New encouraging message added: {encouraging_message}")


@bot.command()
async def delete_encouragement(ctx, index):
    index = int(index)
    await delete_encouragement(index)
    await ctx.send(f"Encouragement message at index {index} deleted.")


@bot.command()
async def list_encouragements(ctx):
    encouragements_str = "\n- ".join(encouragements)
    await ctx.send(f"List of encouraging messages:\n- {encouragements_str}")


@bot.command()
async def toggle_responding(ctx):
    global responding
    async with responding_lock:
        responding = not responding
        os.environ["responding"] = str(responding)
        if responding:
            await ctx.send("Responding to sad words has been enabled.")
        else:
            await ctx.send("Responding to sad words has been disabled.")


queue = []


@bot.command()
async def play(ctx, *url):
    voice_channel = ctx.author.voice.channel
    if not voice_channel:
        await ctx.send("You need to be in a voice channel to use this command.")
        return

    song_info = youtube_dl.YoutubeDL().extract_info(url=url, download=False)
    song_title = song_info['title']

    queue.append({"title": song_title, "url": url})

    if len(queue) == 1:
        await play_song(ctx)


@bot.command()
async def skip(ctx):
    if len(queue) == 0:
        await ctx.send("There are no songs in the queue.")
        return

    voice_client = ctx.voice_client
    if voice_client.is_playing():
        voice_client.stop()

    queue.pop(0)

    if len(queue) > 0:
        await play_song(ctx)


@bot.command()
async def stop(ctx):
    queue.clear()

    voice_client = ctx.voice_client
    if voice_client.is_playing():
        voice_client.stop()

    await voice_client.disconnect()


async def play_song(ctx):
    voice_channel = ctx.author.voice.channel
    voice_client = await voice_channel.connect()

    song = queue[0]
    url = song["url"]
    song_title = song["title"]

    embed = discord.Embed(title="Now playing", description=song_title, color=discord.Color.green())
    await ctx.send(embed=embed)

    voice_client.play(discord.FFmpegPCMAudio(url, options="-vn"))

    while voice_client.is_playing():
        await asyncio.sleep(1)

    queue.pop(0)

    if len(queue) > 0:
        await play_song(ctx)
    else:
        await voice_client.disconnect()


bot.run(os.environ['DISCORD_TOKEN'])

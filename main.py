from discord import voice_client
from dotenv import load_dotenv

load_dotenv()

import os
import json
import random
import aiohttp
import asyncpraw
import asyncio
import youtube_dl
import discord
from discord.ext import commands

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

async def play_song(ctx, url):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel.")
        return
    else:
        channel = ctx.message.author.voice.channel

    if not queue:
        await channel.connect()

    server = ctx.message.guild
    voice_channel = server.voice_client

    try:
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=bot.loop)
            voice_channel.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
            await ctx.send(f"Playing: {player.title}")
    except Exception as e:
        print(e)
        await ctx.send("An error occurred while trying to play the song.")

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL().extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else youtube_dl.YoutubeDL().prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename), data=data)

@bot.command()
async def play(ctx, *, url):
    queue.append(url)
    await play_song(ctx, queue[0])

@bot.command()
async def skip(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client
    voice_channel.stop()

    if len(queue) > 0:
        queue.pop(0)

    if len(queue) > 0:
        await play_song(ctx, queue[0])
    else:
        await voice_channel.disconnect()

@bot.command()
async def stop(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client
    voice_channel.stop()
    queue.clear()
    await voice_channel.disconnect()

@bot.command()
async def queue(ctx):
    if not voice_client == ctx.guild.voice_client:
        return await ctx.send("I'm not connected to a voice channel.")
    if not (player := voice_client.source):
        return await ctx.send("There's no music playing at the moment.")

    queue = player.queue

    if not queue:
        return await ctx.send("The queue is empty.")

    embed = discord.Embed(title="Music queue", color=discord.Color.blue())
    for index, song in enumerate(queue, start=1):
        embed.add_field(name=f"{index}. {song.title}", value=song.url, inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def leave(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client:
        await voice_client.disconnect()
        await ctx.send("Disconnected from voice channel.")
    else:
        await ctx.send("I am not currently in a voice channel.")

bot.run(os.environ['DISCORD_TOKEN'])

import discord
import os
import json
import random
import aiohttp
import asyncpraw
import asyncio
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

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

executor = ThreadPoolExecutor(max_workers=10)


async def get_quote():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://zenquotes.io/api/random") as response:
            json_data = await response.json()
            quote = json_data[0]["q"] + " -" + json_data[0]["a"]
            return quote


async def update_encouragements(encouraging_message):
    async with encouragements_lock:
        encouragements.append(encouraging_message)
        os.environ["encouragements"] = json.dumps(encouragements)


async def delete_encouragement(index):
    async with encouragements_lock:
        if len(encouragements) > index:
            del encouragements[index]
            os.environ["encouragements"] = json.dumps(encouragements)


async def send_encouragement_message(message):
    async with responding_lock:
        if responding:
            if any(word in message.content for word in sad_words):
                await message.channel.send(random.choice(encouragements))


async def send_meme_message(message):
    async with responding_lock:
        async with aiohttp.ClientSession() as session:
            subreddit = await reddit.subreddit('memes')
            async for post in subreddit.hot(limit=50):
                random_post_number = random.randint(1, 50)
                if post.stickied:
                    continue
                data = {"title": post.title, "url": post.url}
                if data["url"].endswith(('.jpg', '.jpeg', '.png')):
                    title = data['title']
                    image_url = data['url']
                    embed = discord.Embed(title=title)
                    embed.set_image(url=image_url)
                    await message.channel.send(embed=embed)
                    break


async def handle_message(message):
    if message.author == client.user:
        return

    msg = message.content

    if msg.startswith("$inspire"):
        quote = await get_quote()
        await message.channel.send(quote)

    async with responding_lock:
        if responding:
            if any(word in msg for word in sad_words):
                await message.channel.send(random.choice(encouragements))

    if msg.startswith("$new"):
        encouraging_message = msg.split("$new ", 1)[1]
        async with responding_lock:
            await update_encouragements(encouraging_message)
        await message.channel.send("New encouraging message added.")

    if msg.startswith("$del"):
        index = int(msg.split("$del", 1)[1])
        async with responding_lock:
            await delete_encouragement(index)
        await message.channel.send("Encouraging message deleted.")

    if msg.startswith("$list"):
        async with responding_lock:
            encouragements_list = "\n".join(encouragements)
        await message.channel.send(encouragements_list)

    if msg.startswith("$responding"):
        value = msg.split("$responding ", 1)[1].lower()

        async with responding_lock:
            if value in ["true", "yes", "1"]:
                os.environ["responding"] = "True"
                responding = True
                await message.channel.send("Responding is on.")
            else:
                os.environ["responding"] = "False"
                responding = False
                await message.channel.send("Responding is off.")

    if msg.startswith('$meme'):
        async with aiohttp.ClientSession() as session:
            async with responding_lock:
                subreddit = await reddit.subreddit('memes')
                async for post in subreddit.hot(limit=50):
                    random_post_number = random.randint(1, 50)
                    if post.stickied:
                        continue
                    data = {"title": post.title, "url": post.url}
                    if data["url"].endswith(('.jpg', '.jpeg', '.png')):
                        title = data['title']
                        image_url = data['url']
                        embed = discord.Embed(title=title)
                        embed.set_image(url=image_url)
                        await message.channel.send(embed=embed)
                        break

    @client.event
    async def on_ready():
        print("We have logged in as {0.user}".format(client))

    @client.event
    async def on_message(message):
        loop = asyncio.get_running_loop()
        asyncio.ensure_future(handle_message(message), loop=loop)
        asyncio.ensure_future(executor.submit(handle_message, message), loop=loop)

    client.run(os.getenv("TOKEN"))

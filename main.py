import time
import discord
import os
import json
import random
import aiohttp
import asyncpraw
from dotenv import load_dotenv

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

responding = os.getenv("responding").lower() in ["true", "yes", "1"]

if "encouragements" in os.environ:
    encouragements_str = os.environ["encouragements"]
    encouragements = json.loads(encouragements_str)
else:
    encouragements = starter_encouragements


async def get_quote():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://zenquotes.io/api/random") as response:
            json_data = await response.json()
            quote = json_data[0]["q"] + " -" + json_data[0]["a"]
            return quote


def update_encouragements(encouraging_message):
    encouragements.append(encouraging_message)
    os.environ["encouragements"] = json.dumps(encouragements)


def delete_encouragement(index):
    if len(encouragements) > index:
        del encouragements[index]
        os.environ["encouragements"] = json.dumps(encouragements)


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    msg = message.content

    if msg.startswith("$inspire"):
        quote = get_quote()
        await message.channel.send(quote)

    if responding:
        if any(word in msg for word in sad_words):
            await message.channel.send(random.choice(encouragements))

    if msg.startswith("$new"):
        encouraging_message = msg.split("$new ", 1)[1]
        update_encouragements(encouraging_message)
        await message.channel.send("New encouraging message added.")

    if msg.startswith("$del"):
        index = int(msg.split("$del", 1)[1])
        delete_encouragement(index)
        await message.channel.send("Encouraging message deleted.")

    if msg.startswith("$list"):
        encouragements_list = "\n".join(encouragements)
        await message.channel.send(encouragements_list)

    if msg.startswith("$responding"):
        value = msg.split("$responding ", 1)[1].lower()

        if value in ["true", "yes", "1"]:
            os.environ["responding"] = "True"
            await message.channel.send("Responding is on.")
        else:
            os.environ["responding"] = "False"
            await message.channel.send("Responding is off.")

    if msg.startswith('$meme'):
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

    if msg.startswith('$joke'):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://official-joke-api.appspot.com/random_joke") as response:
                data = await response.json()
                setup = data["setup"]
                punchline = data["punchline"]
                await message.channel.send(setup)
                await asyncio.sleep(3)
                await message.channel.send(punchline)


client.run(os.getenv("TOKEN"))

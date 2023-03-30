import discord
import os
import requests
import json
import random
import praw
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

client_id = os.getenv('REDDIT_CLIENT_ID')
password = os.getenv('YOUR_REDDIT_PASSWORD')
client_secret = os.getenv('REDDIT_CLIENT_SECRET')
user_agent = os.getenv('REDDIT_USER_AGENT')

reddit = praw.Reddit(client_id=client_id,
                  client_secret=client_secret,
                  username="tannerbot227",
                  password=password,
                  user_agent=user_agent)

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

def get_quote():
  response = requests.get("https://zenquotes.io/api/random")
  json_data = json.loads(response.text)
  quote = json_data[0]["q"] + " -" + json_data[0]["a"]
  return (quote)

def update_encouragements(encouraging_message):
  if "encouragements" in os.environ:
    encouragements = os.environ["encouragements"].split(",")
    encouragements.append(encouraging_message)
    os.environ["encouragements"] = ",".join(encouragements)
  else:
    os.environ["encouragements"] = encouraging_message

def delete_encouragment(index):
  encouragements = os.environ["encouragements"].split(",")
  if len(encouragements) > index:
    del encouragements[index]
  os.environ["encouragements"] = ",".join(encouragements)

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

  if os.getenv("responding").lower() == "true":
    options = starter_encouragements
    if "encouragements" in os.environ:
      options += os.environ["encouragements"].split(",")

    if any(word in msg for word in sad_words):
      await message.channel.send(random.choice(options))

  if msg.startswith("$new"):
    encouraging_message = msg.split("$new ", 1)[1]
    update_encouragements(encouraging_message)
    await message.channel.send("New encouraging message added.")

  if msg.startswith("$del"):
    encouragements = []
    if "encouragements" in os.environ:
      index = int(msg.split("$del", 1)[1])
      delete_encouragment(index)
      encouragements = os.environ["encouragements"].split(",")
    await message.channel.send(encouragements)

  if msg.startswith("$list"):
    encouragements = []
    if "encouragements" in os.environ:
      encouragements = os.environ["encouragements"].split(",")
    await message.channel.send(encouragements)

if msg.startswith("$responding"):
    value = msg.split("$responding ", 1)[1]

    if value.lower() == "true":
        db["responding"] = True
        await message.channel.send("Responding is on.")
    else:
        db["responding"] = False
        await message.channel.send("Responding is off.")

  @client.command(name='meme')
  async def send_meme(ctx):
      subreddit = reddit.subreddit('memes')
      posts = subreddit.hot(limit=20)
      random_post_number = random.randint(1, 50)
      for i, post in enumerate(posts):
          if i == random_post_number:
              title = post.title
              image_url = post.url
              embed = discord.Embed(title=title)
              embed.set_image(url=image_url)
              await ctx.send(embed=embed)
              break

client.run(os.getenv("TOKEN"))

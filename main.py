import discord
import os

import requests
import json
import random
import praw
from replit import db

from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

client_id = os.environ['reddit_client_id']
password = os.environ['your_reddit_password']
client_secret = os.environ['reddit_client_secret']
user_agent = os.environ['reddit_user_agent']

reddit = praw.Reddit(client_id=client_id,
                  client_secret=client_secret,
                  username="tannerbot227",
                  password=password,
                  user_agent=user_agent)

keep_alive()

sad_words = [
  "sad", "SAD", "Sad", "SAd", "sAD", "sAd", "saD", "SaD", "depressed",
  "unhappy", "angry", "anger", "miserable"
]

starter_encouragements = [
  "Cheer up!", "Hang in there.", "You are a great person!", "We love you",
  "I'm here for you", "I love you", "Let me give you a hug, friend"
]

if "responding" not in db.keys():
  db["responding"] = True


def get_quote():
  response = requests.get("https://zenquotes.io/api/random")
  json_data = json.loads(response.text)
  quote = json_data[0]["q"] + " -" + json_data[0]["a"]
  return (quote)


def update_encouragements(encouraging_message):
  if "encouragements" in db.keys():
    encouragements = db["encouragements"]
    encouragements.append(encouraging_message)
    db["encouragements"] = encouragements
  else:
    db["encouragements"] = [encouraging_message]


def delete_encouragment(index):
  encouragements = db["encouragements"]
  if len(encouragements) > index:
    del encouragements[index]
  db["encouragements"] = encouragements


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

  if db["responding"]:
    options = starter_encouragements
    if "encouragements" in db.keys():
      options = options + db["encouragements"]

    if any(word in msg for word in sad_words):
      await message.channel.send(random.choice(options))

  if msg.startswith("$new"):
    encouraging_message = msg.split("$new ", 1)[1]
    update_encouragements(encouraging_message)
    await message.channel.send("New encouraging message added.")

  if msg.startswith("$del"):
    encouragements = []
    if "encouragements" in db.keys():
      index = int(msg.split("$del", 1)[1])
      delete_encouragment(index)
      encouragements = db["encouragements"]
    await message.channel.send(encouragements)

  if msg.startswith("$list"):
    encouragements = []
    if "encouragements" in db.keys():
      encouragements = db["encouragements"]
    await message.channel.send(encouragements)

  if msg.startswith("$responding"):
    value = msg.split("$responding ", 1)[1]

    if value.lower() == "true":
      db["responding"] = True
      await message.channel.send("Responding is on.")
    else:
      db["responding"] = False
      await message.channel.send("Responding is off.")

  if message.content.startswith('$meme'):
    subreddit = reddit.subreddit('memes')
    posts = subreddit.hot(limit=20)
    random_post_number = random.randint(1, 50)
    for i, post in enumerate(posts):
      if i == random_post_number:
        title = post.title
        image_url = post.url
        embed = discord.Embed(title=title)
        embed.set_image(url=image_url)
        await message.channel.send(embed=embed)
        break

client.run(os.getenv("TOKEN"))

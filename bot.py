import discord
from discord.ext import commands
import json
import random
import datetime

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="p!", intents=intents)

DATABASE = "database.json"

def load_data():
    with open(DATABASE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATABASE, "w") as f:
        json.dump(data, f, indent=4)

def random_spice():
    return random.uniform(-0.6, 0.6)

def calculate_score(level, has_feat):
    ranges = {
        "A": (6.0, 9.2),
        "B": (4.5, 9.0),
        "C": (2.5, 9.2),
        "D": (1.0, 9.2),
        "E.": (8.0, 10.0)  # Hidden rare tier
    }

    base = round(random.uniform(*ranges[level]), 1)
    
    if has_feat and random.choice([True, False]):
        base += 0.4

    base += random_spice()

    # Perfect 10 chance (1 in 70)
    if random.randrange(1, 71) == 1:
        base = 10.0

    return round(min(base, 10.0), 1)


def can_register(user_id, artist, project_type):
    data = load_data()
    current_time = datetime.datetime.now()
    count = 0

    for p in data["projects"]:
        if p["artist"] == artist and p["type"] == project_type:
            time = datetime.datetime.fromisoformat(p["timestamp"])
            if (current_time - time).seconds < 86400:
                count += 1

    return count < 2


@bot.event
async def on_ready():
    print(f"✅ BOT CONNECTED AS {bot.user}")


# ----------------- REGISTER ARTIST -----------------

@bot.command(name="register_artist")
async def register_artist(ctx, name: str, gender: str):
    data = load_data()

    if name in data["artists"]:
        await ctx.send("Artist already exists.")
        return

    data["artists"][name] = {
        "gender": gender,
        "albums": [],
        "singles": [],
        "average_score": 0
    }

    save_data(data)
    await ctx.send(f"✅ Artist `{name}` registered successfully.")

# ----------------- REGISTER PROJECT -----------------

@bot.command(name="register_project")
async def register_project(ctx, artist: str, title: str, project_type: str, genre: str, label: str, year: int, duration: str, tracks: int, explicit: str, level: str, has_feat: str, description: str):

    data = load_data()

    if artist not in data["artists"]:
        await ctx.send("Artist not found.")
        return

    if not can_register(ctx.author.id, artist, project_type):
        await ctx.send("❌ This artist reached the 24h limit (2 max).")
        return

    score = calculate_score(level, has_feat.lower() == "yes")

    project = {
        "artist": artist,
        "title": title,
        "type": project_type,
        "genre": genre,
        "label": label,
        "year": year,
        "duration": duration,
        "tracks": tracks,
        "explicit": explicit,
        "score": score,
        "description": description,
        "timestamp": str(datetime.datetime.now())
    }

    data["projects"].append(project)

    if label not in data["labels"]:
        data["labels"][label] = []

    data["labels"][label].append(project)

    data["artists"][artist][project_type + "s"].append(project)

    save_data(data)

    embed = discord.Embed(title=f"{title}", description=description, color=0x2f3136)
    embed.add_field(name="Artist", value=artist)
    embed.add_field(name="Type", value=project_type.capitalize())
    embed.add_field(name="Genre", value=genre)
    embed.add_field(name="Label", value=label)
    embed.add_field(name="Year", value=str(year))
    embed.add_field(name="Duration", value=duration)
    embed.add_field(name="Tracks", value=str(tracks))
    embed.add_field(name="Explicit", value=explicit)
    embed.add_field(name="Score", value=f"**{score}/10**", inline=False)
    embed.set_footer(text="© METACRITIC, A FANDOM COMPANY. ALL RIGHTS RESERVED.")

    await ctx.send(embed=embed)


# ----------------- SCORE LOOKUP -----------------

@bot.command(name="score")
async def score(ctx, title: str):
    data = load_data()

    for p in data["projects"]:
        if p["title"].lower() == title.lower():
            embed = discord.Embed(title=f"{p['title']}", description=p['description'], color=0x2f3136)
            embed.add_field(name="Artist", value=p["artist"])
            embed.add_field(name="Genre", value=p["genre"])
            embed.add_field(name="Label", value=p["label"])
            embed.add_field(name="Year", value=p["year"])
            embed.add_field(name="Score", value=f"**{p['score']}/10**", inline=False)
            embed.set_footer(text="© METACRITIC, A FANDOM COMPANY. ALL RIGHTS RESERVED.")

            await ctx.send(embed=embed)
            return

    await ctx.send("❌ Project not found.")


# ----------------- LEADERBOARD -----------------

@bot.command(name="leaderboard")
async def leaderboard(ctx, mode="top"):
    data = load_data()
    sorted_projects = sorted(data["projects"], key=lambda x: x["score"], reverse=(mode=="top"))

    embed = discord.Embed(title="Metacritic Leaderboard", color=0x000000)

    for p in sorted_projects[:10]:
        embed.add_field(name=p["title"], value=f"{p['artist']} — {p['score']}/10", inline=False)

    embed.set_footer(text="© METACRITIC, A FANDOM COMPANY. ALL RIGHTS RESERVED.")
    await ctx.send(embed=embed)


bot.run(MTQ0NjMwNDY1MzExMjUxMjY5Mg.GMu5Iv.5O7LHZjWk4GJd22KHAIeBHWKeOFJt4mPzX2Cr4)

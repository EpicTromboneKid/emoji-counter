import discord
from discord import app_commands
from discord.ext import commands
import re
import emoji
import collections
import json
import os
import random
from lines import flirts, moody

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
HELLO_FILE = 'hello_tracker.json'

bot = commands.Bot(command_prefix="$", intents=intents)
custom_emoji_pattern = re.compile(r"<(a?):\w+:(\d+)>")

def choose_response():
    if random.random() < 0.7:
        response = random.choice(flirts)
    else:
        response = random.choice(moody)
    return response

def load_data():
    if not os.path.exists('storage.json'):
        return {}
    with open('storage.json', 'r') as f:
        return json.load(f)

def save_data(data):
    with open('storage.json', 'w') as f:
        json.dump(data, f)
        

def load_hello_data():
    if not os.path.exists(HELLO_FILE):
        return {}
    with open(HELLO_FILE, 'r') as f:
        return json.load(f)

def save_hello_data(data):
    with open(HELLO_FILE, 'w') as f:
        json.dump(data, f)

def update_hello_counter(guild_id, user_id):
    data = load_hello_data()
    if guild_id not in data:
        data[guild_id] = {}
    
    # Track the count per user
    user_counts = data[guild_id]
    user_counts[user_id] = user_counts.get(user_id, 0) + 1
    
    save_hello_data(data)

def update_counter(guild_id, emoji_str):
    data = load_data()
    if guild_id not in data:
        data[guild_id] = {}
    counts = collections.Counter(data[guild_id])
    counts[emoji_str] += 1
    data[guild_id] = dict(counts)
    save_data(data)

def generate_top_25_embed(guild_id, guild_name):
    data = load_data()
    total = 0
    if guild_id not in data:
        return None
    counter = collections.Counter(data[guild_id])
    embed = discord.Embed(title=f"{guild_name}'s top emojis", color=0x985f50)
    n = 1
    for emoji_char, count in counter.most_common(25):
        if emoji_char.isdigit():
            emoji_string = f'<:rizz:{emoji_char}>'
        else:
            emoji_string = emoji_char
        embed.add_field(name=f"#{n}", value=f"{emoji_string}: {count}", inline=False)
        total += count
        n += 1
    embed.set_footer(text=f"total emojis counted: {total}")
    return embed

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user}')

@bot.tree.command(name="top", description="Shows the top 25 emojis in this server")
async def top25(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = generate_top_25_embed(str(interaction.guild.id), interaction.guild.name)
    if embed:
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("No emojis tracked yet!")

@bot.command(name="t")
async def t25(ctx):
    embed = generate_top_25_embed(str(ctx.guild.id), ctx.guild.name)
    if embed:
        await ctx.send(embed=embed)
    else:
        await ctx.send("No emojis tracked yet!")


@bot.tree.command(name="hello_top", description="Shows the top greeters in this server")
async def hello_top(interaction: discord.Interaction):
    data = load_hello_data()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in data or not data[guild_id]:
        await interaction.response.send_message("No hello greetings tracked yet!")
        return

    counts = data[guild_id]
    sorted_users = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    
    embed = discord.Embed(title=f"Top Greeters in {interaction.guild.name}", color=0x985f50)
    
    for i, (user_id, count) in enumerate(sorted_users[:10], start=1):
        mention = f"<@{user_id}>"
        embed.add_field(name=f"Rank #{i}", value=f"{mention}: **{count}** hello(s)", inline=False)
        
    await interaction.response.send_message(embed=embed)

@bot.command(name="htop")
async def hello_top_prefix(ctx):
    if not ctx.guild:
        await ctx.send("This command can only be used in a server!")
        return
    data = load_hello_data()
    guild_id = str(ctx.guild.id)
    if guild_id not in data or not data[guild_id]:
        await ctx.send("No hello greetings tracked yet!")
        return
    counts = data[guild_id]
    sorted_users = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    embed = discord.Embed(title=f"Top Greeters in {ctx.guild.name}", color=0x985f50)
    for i, (user_id, count) in enumerate(sorted_users[:10], start=1):
        mention = f"<@{user_id}>"
        embed.add_field(name=f"Rank #{i}", value=f"{mention}: **{count}** hello(s)", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user:
        return
    try:
        update_counter(str(reaction.message.guild.id), str(reaction.emoji.id))
    except:
        update_counter(str(reaction.message.guild.id), str(reaction.emoji))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    custom = custom_emoji_pattern.findall(message.content)
    unicode_emojis = [item['emoji'] for item in emoji.emoji_list(message.content)]

    for animated, emoji_id in custom:
        prefix = "a" if animated else ""
        update_counter(str(message.guild.id), f"{emoji_id}")
            
    for uni in unicode_emojis:
        update_counter(str(message.guild.id), uni)

    await bot.process_commands(message)
    
@bot.tree.command(name="hello", description="hi")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=True, users=True)
async def hello(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id) if interaction.guild else "DM"
    update_hello_counter(guild_id, str(interaction.user.id))
    response = choose_response()
    try:
        await interaction.channel.send(response)
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("\u200b", ephemeral=True)
    except:
        await interaction.response.send_message(response)
    
    
@bot.command(name="hello")
async def hello(ctx):
    guild_id = str(ctx.guild.id) if ctx.guild else "DM"
    update_hello_counter(guild_id, str(ctx.author.id))
    response = choose_response()
    
    await ctx.send(response)

x = open('hi.txt').read().strip()
bot.run(x)

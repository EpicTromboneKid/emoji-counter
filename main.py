import discord
from discord import app_commands
from discord.ext import commands
import re
import emoji
import collections
import json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="$", intents=intents)
custom_emoji_pattern = re.compile(r"<(a?):\w+:(\d+)>")

def load_data():
    if not os.path.exists('storage.json'):
        return {}
    with open('storage.json', 'r') as f:
        return json.load(f)

def save_data(data):
    with open('storage.json', 'w') as f:
        json.dump(data, f)

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
    embed = generate_top_25_embed(str(interaction.guild.id), interaction.guild.name)
    await interaction.response.defer(ephemeral=False)
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
        
@bot.tree.command(name="hello", description="hi")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=True, users=True)
async def hello(interaction: discord.Interaction):
    try:
        await interaction.channel.send('heyyyyyyyyyyyy :smiling_face_with_3_hearts: :kissing_heart: :heart:')
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("\u200b", ephemeral=True)
    except:
        await interaction.response.send_message('heyyyyyyyyyyyy :smiling_face_with_3_hearts: :kissing_heart: :heart:')
    
    
@bot.command(name="hello")
async def hello(ctx):
    await ctx.send('heyyyyyyyyyyyy :smiling_face_with_3_hearts: :kissing_heart: :heart:')

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

x = open('hi.txt').read().strip()
bot.run(x)

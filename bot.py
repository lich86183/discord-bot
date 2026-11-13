import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import requests
import asyncio

# Load the token from .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Define Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await bot.change_presence(activity=discord.Game(name="!help for commands"))
    print('------')

# --- Welcome Event ---
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="general")
    if channel:
        await channel.send(f"Welcome to the server, {member.mention}! Hope you have a great time!")

# --- Utility & Fun Commands ---

@bot.command()
async def ping(ctx):
    """Check if the bot is alive and show latency."""
    await ctx.send(f'Pong! Latency: {round(bot.latency * 1000)}ms')

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    """Get info about a user."""
    member = member or ctx.author
    embed = discord.Embed(title=f"User Info - {member.name}", color=discord.Color.blue())
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Joined at", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Roles", value=", ".join([role.name for role in member.roles if role.name != "@everyone"]), inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def joke(ctx):
    """Get a random joke."""
    headers = {"Accept": "application/json"}
    response = requests.get("https://icanhazdadjoke.com/", headers=headers)
    if response.status_code == 200:
        data = response.json()
        await ctx.send(data['joke'])
    else:
        await ctx.send("Could not fetch a joke right now.")

# --- New: Create a Poll ---
@bot.command()
async def poll(ctx, *, question: str):
    """Create a quick yes/no poll."""
    await ctx.message.delete()
    embed = discord.Embed(title="📊 Community Poll", description=question, color=discord.Color.gold())
    embed.set_footer(text=f"Poll created by {ctx.author.name}")

    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")

# --- New: Create an Event Announcement ---
@bot.command()
async def event(ctx, *, details: str):
    """Announce a community event."""
    await ctx.message.delete()
    embed = discord.Embed(title="🎉 Upcoming Event!", description=details, color=discord.Color.purple())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send("@everyone", embed=embed)


# --- Moderation Commands ---

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    """Clear a number of messages."""
    if amount < 1:
        await ctx.send("Please specify a number greater than 0.")
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'Deleted {len(deleted) - 1} messages.', delete_after=5)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    """Kick a member."""
    await member.kick(reason=reason)
    await ctx.send(f'Kicked {member.name}.')

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    """Ban a member from the server."""
    await member.ban(reason=reason)
    await ctx.send(f'Banned {member.name} from the server.')

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, minutes: int, *, reason=None):
    """Temporarily mute a user for X minutes."""
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        try:
            role = await ctx.guild.create_role(name="Muted", reason="For temporary mutes")
            for channel in ctx.guild.channels:
                await channel.set_permissions(role, send_messages=False, speak=False)
        except Exception as e:
            await ctx.send("Could not create 'Muted' role. Please make sure I have permission.")
            return

    await member.add_roles(role, reason=reason)
    await ctx.send(f'{member.mention} has been muted for {minutes} minutes.')

    await asyncio.sleep(minutes * 60)

    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f'{member.mention} has been unmuted.')

bot.run(TOKEN)

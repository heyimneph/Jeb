import os
import discord
import logging

from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv
from discord.ext.commands import is_owner, Context

# Load environment variables
load_dotenv("config.env.txt")

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_PREFIX = "%"

# Other External Keys
LAUNCH_TIME = datetime.utcnow()

# Intents configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.messages = True

# Ensure the necessary directories exist
os.makedirs('data', exist_ok=True)
os.makedirs('data/logs', exist_ok=True)
os.makedirs('data/databases', exist_ok=True)

# Logging Configuration
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger('discord')
handler = logging.FileHandler(filename='data/logs/discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Create bot client with updated intents
client = commands.Bot(
    command_prefix=DISCORD_PREFIX,
    intents=intents,
    help_command=None,
    activity=discord.Activity(type=discord.ActivityType.playing, name="music -- /help")
)

async def perform_sync():
    synced = await client.tree.sync()
    return len(synced)

@client.command()
@is_owner()
async def sync(ctx: Context) -> None:
    synced = await client.tree.sync()
    await ctx.reply("{} commands synced".format(len(synced)))

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)

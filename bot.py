import discord
import aiosqlite
import asyncio
import os
from datetime import datetime, timezone
from config import client, DISCORD_TOKEN, perform_sync

# ---------------------------------------------------------------------------------------------------------------------
# Database Configuration
# ---------------------------------------------------------------------------------------------------------------------
db_path = './data/databases/jeb.db'

# ---------------------------------------------------------------------------------------------------------------------
# Customisation Functions
# ---------------------------------------------------------------------------------------------------------------------

async def get_embed_colour(conn):
    async with conn.execute('SELECT value FROM customisation WHERE type = ?', ("embed_color",)) as cursor:
        row = await cursor.fetchone()
        if row:
            return int(row[0], 16)  # Assuming the color is stored as a hex string
        return 0x3498db

async def get_bio_settings(conn):
    async with conn.execute('SELECT value FROM customisation WHERE type = ?', ("activity_type",)) as cursor:
        activity_type_doc = await cursor.fetchone()
    async with conn.execute('SELECT value FROM customisation WHERE type = ?', ("bio",)) as cursor:
        bio_doc = await cursor.fetchone()
    if activity_type_doc and bio_doc:
        return activity_type_doc[0], bio_doc[0]
    return None, None

# ---------------------------------------------------------------------------------------------------------------------
# Event Handlers
# ---------------------------------------------------------------------------------------------------------------------

@client.event
async def on_ready():
    print(f'Bot is logged in as {client.user.name} ({client.user.id})')
    synced_count = await perform_sync()
    print(f"{synced_count} commands synced")

    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute('SELECT value FROM customisation WHERE type = ?', ("activity_type",)) as cursor:
            activity_type_doc = await cursor.fetchone()
        async with conn.execute('SELECT value FROM customisation WHERE type = ?', ("bio",)) as cursor:
            bio_doc = await cursor.fetchone()

    if activity_type_doc and bio_doc:
        activity_type = activity_type_doc[0]
        bio = bio_doc[0]

        if activity_type.lower() == "playing":
            activity = discord.Game(name=bio)
        elif activity_type.lower() == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=bio)
        elif activity_type.lower() == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=bio)
        else:
            print("Invalid activity type in database")
            return

        await client.change_presence(activity=activity)
    else:
        print("No bio settings found in database")

# ---------------------------------------------------------------------------------------------------------------------
# Main Function
# ---------------------------------------------------------------------------------------------------------------------

async def main():
    try:
        await client.load_extension("core.initialisation")

        for filename in os.listdir('cogs'):
            if filename.endswith('.py'):
                await client.load_extension(f'cogs.{filename[:-3]}')
                print(f"Loading {filename[:-3]}...")

        print("Starting Bot...")

        await client.start(DISCORD_TOKEN)

    except KeyboardInterrupt:
        print("Bot is shutting down...")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    finally:
        await client.close()
        print("Bot has been closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot terminated by user.")
    except Exception as e:
        print(f"An unexpected error occurred during bot execution: {e}")

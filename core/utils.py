import discord
import os
import logging
import aiosqlite

# Ensure the database directory exists
os.makedirs('./data/databases', exist_ok=True)

# Path to the SQLite database
db_path = './data/databases/jeb.db'

# ---------------------------------------------------------------------------------------------------------------------
# Command Logging
# ---------------------------------------------------------------------------------------------------------------------
async def log_command_usage(bot, interaction):
    try:
        command_options = ""
        if 'options' in interaction.data:
            for option in interaction.data['options']:
                command_options += f"{option['name']}: {option.get('value', 'Not provided')}\n"

        log_channel = None

        async with aiosqlite.connect(db_path) as conn:
            logging.info(f"Connected to the database at {db_path}")
            async with conn.execute(
                'SELECT log_channel_id FROM config WHERE guild_id = ?', (interaction.guild.id,)
            ) as cursor:
                row = await cursor.fetchone()

                if row:
                    log_channel_id = row[0]
                    log_channel = bot.get_channel(int(log_channel_id))

                if not log_channel:
                    logging.info(f"No log_channel_id found in the database for guild_id: {interaction.guild.id}, checking for 'misu_logs' channel.")
                    log_channel = discord.utils.get(interaction.guild.text_channels, name='misu_logs')

        if log_channel:
            embed = discord.Embed(
                description=f"Command: `{interaction.command.name}`",
                color=discord.Color.blue()
            )
            embed.add_field(name="User", value=interaction.user.mention, inline=True)
            embed.add_field(name="Guild ID", value=interaction.guild.id, inline=True)
            embed.add_field(name="Channel", value=interaction.channel.mention, inline=True)
            if command_options:
                embed.add_field(name="Command Options", value=command_options.strip(), inline=False)
            embed.set_footer(text=f"User ID: {interaction.user.id}")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await log_channel.send(embed=embed)
        else:
            logging.error(f"Log channel not found for guild_id: {interaction.guild.id}")

    except aiosqlite.Error as e:
        logging.error(f"Error logging command usage: {e}")
    except Exception as e:
        logging.error(f"Unexpected error logging command usage: {e}")



async def check_permissions(interaction):
    if interaction.user.id == 111941993629806592:
        return True

    if interaction.user.guild_permissions.administrator:
        return True

    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute('''
            SELECT can_use_commands FROM permissions WHERE guild_id = ? AND user_id = ?
        ''', (interaction.guild_id, interaction.user.id))
        permission = await cursor.fetchone()
        return permission and permission[0]


import aiosqlite
import os

# Ensure the database directory exists
os.makedirs('./data/databases', exist_ok=True)

# Path to the SQLite database
db_path = './data/databases/jeb.db'


async def is_shitty_friend(user_id: int) -> (bool, str):
    """
    Check if a user is banned from using commands.

    :param user_id: The ID of the user to check.
    :return: (bool, str) - A tuple where the first element indicates if the user is banned,
             and the second element is the reason if they are banned.
    """
    # Predefined "banned" user ID for now
    banned_users = {
        238293702630572032: "Shitty Friend"
    }

    # Check if the user ID is in the hardcoded list
    if user_id in banned_users:
        return True, banned_users[user_id]

    # Optionally, you can query the database to check if they are banned dynamically
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute("SELECT reason FROM banned_users WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        if result:
            return True, result[0]

    return False, ""






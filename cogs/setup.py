import discord
import aiosqlite
import os
import logging

from discord import app_commands
from discord.ext import commands

from core.utils import log_command_usage, check_permissions

# ---------------------------------------------------------------------------------------------------------------------
# Database Configuration
# ---------------------------------------------------------------------------------------------------------------------
db_path = './data/databases/jeb.db'

# ---------------------------------------------------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------------------------------------------------
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------------------------------------------------
# Setup Class
# ---------------------------------------------------------------------------------------------------------------------
class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = './data/databases/jeb.db'

    async def owner_check(self, interaction: discord.Interaction):
        owner_id = 111941993629806592
        return interaction.user.id == owner_id

    # ---------------------------------------------------------------------------------------------------------------------
    # Setup Commands
    # ---------------------------------------------------------------------------------------------------------------------

    @app_commands.command(description="Admin: Run the setup for Jeb.")
    async def setup(self, interaction: discord.Interaction):
        if not await check_permissions(interaction):
            await interaction.response.send_message("You do not have permission to use this command. "
                                                    "An Admin needs to `/authorise` you!",
                                                    ephemeral=True)
            return

        try:
            guild = interaction.guild

            # Permission overwrites for the log channel
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                # Default role cannot see the channel
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                # Bot can see and send messages
            }

            # Allow all administrator roles to view the channel
            for role in guild.roles:
                if role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True)

            # Check if a 'logs' channel exists, if not create it
            log_channel = discord.utils.get(guild.text_channels, name='logs')
            if log_channel is None:
                log_channel = await guild.create_text_channel('logs', overwrites=overwrites)

            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute('''
                    INSERT INTO config (guild_id, log_channel_id)
                    VALUES (?, ?)
                    ON CONFLICT(guild_id) DO UPDATE SET
                        log_channel_id = excluded.log_channel_id
                ''', (guild.id, log_channel.id))
                await conn.commit()

            await interaction.response.send_message('Setup completed! Channels created and configurations saved.',
                                                    ephemeral=True)
        except Exception as e:
            logger.error(f"Error with setup command: {e}")
            await interaction.response.send_message(f"An unexpected error occurred: {e}", ephemeral=True)
        finally:
            await log_command_usage(self.bot, interaction)


# ---------------------------------------------------------------------------------------------------------------------
# Setup Function
# ---------------------------------------------------------------------------------------------------------------------
async def setup(bot):
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS config (
                guild_id INTEGER PRIMARY KEY,
                log_channel_id TEXT
            )
        ''')
        await conn.commit()
    await bot.add_cog(SetupCog(bot))

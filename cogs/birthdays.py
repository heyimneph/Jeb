import discord
import aiosqlite
import os
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta

from core.utils import check_permissions, log_command_usage, is_shitty_friend

# Ensure the database directory exists
os.makedirs('./data/databases', exist_ok=True)

# Path to the SQLite database
db_path = './data/databases/jeb.db'

#  ---------------------------------------------------------------------------------------------------------------------
#  Birthday Class
#  ---------------------------------------------------------------------------------------------------------------------
class BirthdayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminder_loop.start()

    @tasks.loop(hours=24)
    async def reminder_loop(self):
        await self.send_birthday_reminders()

    async def send_birthday_reminders(self):
        today = datetime.utcnow()
        tomorrow = today + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%d/%m")

        async with aiosqlite.connect(db_path) as conn:
            # Fetch all users whose birthday is tomorrow
            cursor = await conn.execute("SELECT * FROM birthdays WHERE birthday = ?", (tomorrow_str,))
            rows = await cursor.fetchall()

            for row in rows:
                guild = self.bot.get_guild(row[1])  # Use index as the row is a tuple
                if guild:
                    birthday_message = f"🎉 Tomorrow is {row[2]}'s birthday! 🎂"

                    # Fetch subscribers for the guild
                    sub_cursor = await conn.execute(
                        "SELECT user_id FROM birthday_subscriptions WHERE guild_id = ?", (row[1],)
                    )
                    subscribers = await sub_cursor.fetchall()

                    # Send the reminder to each subscriber via DM
                    for subscriber in subscribers:
                        user = self.bot.get_user(subscriber[0])
                        if user:
                            try:
                                await user.send(birthday_message)
                            except discord.Forbidden:
                                continue


#  ---------------------------------------------------------------------------------------------------------------------
#  Birthday Commands
#  ---------------------------------------------------------------------------------------------------------------------

    @app_commands.command(name="birthday_add", description="Add your birthday (DD/MM)")
    @app_commands.describe(date="Your birthday: DD/MM")
    async def birthday_add(self, interaction: discord.Interaction, date: str):


        try:
            # Validate the date format (day and month only)
            birthday = datetime.strptime(date, "%d/%m").strftime("%d/%m")
            async with aiosqlite.connect(db_path) as conn:
                await conn.execute(
                    "INSERT INTO birthdays (user_id, guild_id, user_name, birthday) VALUES (?, ?, ?, ?) "
                    "ON CONFLICT(user_id, guild_id) DO UPDATE SET birthday = excluded.birthday",
                    (interaction.user.id, interaction.guild_id, interaction.user.name, birthday)
                )
                await conn.commit()
            await interaction.response.send_message("Your birthday has been saved!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Invalid date format. Please use DD/MM format.", ephemeral=True)
        finally:
            await log_command_usage(self.bot, interaction)

    @app_commands.command(name="birthday_remove", description="Remove your birthday")
    async def birthday_remove(self, interaction: discord.Interaction):
        try:
            async with aiosqlite.connect(db_path) as conn:
                await conn.execute("DELETE FROM birthdays WHERE user_id = ? AND guild_id = ?",
                                   (interaction.user.id, interaction.guild_id))
                await conn.commit()
            await interaction.response.send_message("Your birthday has been removed.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("An error occurred while removing your birthday.",
                                                    ephemeral=True)
        finally:
            await log_command_usage(self.bot, interaction)

    @app_commands.command(name="birthday_subscribe", description="Subscribe to birthday reminders")
    async def birthday_subscribe(self, interaction: discord.Interaction):
        try:
            async with aiosqlite.connect(db_path) as conn:
                await conn.execute(
                    "INSERT INTO birthday_subscriptions (user_id, guild_id) VALUES (?, ?) "
                    "ON CONFLICT(user_id, guild_id) DO NOTHING",
                    (interaction.user.id, interaction.guild_id)
                )
                await conn.commit()
            await interaction.response.send_message("You have been subscribed to birthday reminders!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("An error occurred while subscribing to birthday reminders.",
                                                    ephemeral=True)
        finally:
            await log_command_usage(self.bot, interaction)

    @app_commands.command(name="birthday_unsubscribe", description="Unsubscribe from birthday reminders")
    async def birthday_unsubscribe(self, interaction: discord.Interaction):
        try:
            async with aiosqlite.connect(db_path) as conn:
                await conn.execute("DELETE FROM birthday_subscriptions WHERE user_id = ? AND guild_id = ?",
                                   (interaction.user.id, interaction.guild_id))
                await conn.commit()
            await interaction.response.send_message("You have been unsubscribed from birthday reminders.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("An error occurred while unsubscribing from birthday reminders.",
                                                    ephemeral=True)
        finally:
            await log_command_usage(self.bot, interaction)

#  ---------------------------------------------------------------------------------------------------------------------
#  Setup Function
#  ---------------------------------------------------------------------------------------------------------------------
async def setup(bot):
    async with aiosqlite.connect(db_path) as conn:
        # Create the birthdays table if it does not exist
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS birthdays (
            user_id INTEGER,
            guild_id INTEGER,
            user_name TEXT,
            birthday TEXT,  -- Only stores day and month as DD/MM
            PRIMARY KEY (user_id, guild_id)
        )
        ''')
        # Create the birthday_subscriptions table if it does not exist
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS birthday_subscriptions (
            user_id INTEGER,
            guild_id INTEGER,
            PRIMARY KEY (user_id, guild_id)
        )
        ''')
        await conn.commit()
    await bot.add_cog(BirthdayCog(bot))

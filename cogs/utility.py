import discord
import logging
import aiosqlite
import os
import inspect

from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from datetime import datetime

from core.utils import check_permissions, log_command_usage, is_shitty_friend
from cogs.customisation import get_embed_colour

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
# Pagination for Help Command
# ---------------------------------------------------------------------------------------------------------------------
class HelpPaginator(View):
    def __init__(self, bot, pages):
        super().__init__(timeout=180)
        self.bot = bot
        self.pages = pages
        self.current_page = 0

        self.prev_button = Button(label="Prev", style=discord.ButtonStyle.primary)
        self.prev_button.callback = self.prev_page
        self.add_item(self.prev_button)

        self.home_button = Button(label="Home", style=discord.ButtonStyle.green)
        self.home_button.callback = self.go_home
        self.add_item(self.home_button)

        self.next_button = Button(label="Next", style=discord.ButtonStyle.primary)
        self.next_button.callback = self.next_page
        self.add_item(self.next_button)

    async def next_page(self, interaction: discord.Interaction):
        self.current_page += 1
        if self.current_page >= len(self.pages):
            self.current_page = 0
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    async def prev_page(self, interaction: discord.Interaction):
        self.current_page -= 1
        if self.current_page < 0:
            self.current_page = len(self.pages) - 1
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    async def go_home(self, interaction: discord.Interaction):
        self.current_page = 0
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    async def start(self, interaction: discord.Interaction):
        for page in self.pages:
            page.set_thumbnail(url=self.bot.user.display_avatar.url)
            page.set_footer(text="Bot created by heyimneph")
            page.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=self.pages[self.current_page], view=self, ephemeral=True)

# ---------------------------------------------------------------------------------------------------------------------
# Utility Cog Class
# ---------------------------------------------------------------------------------------------------------------------
class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_start_time = datetime.utcnow()

    async def has_required_permissions(self, interaction, command):
        try:
            async with aiosqlite.connect(db_path) as conn:
                cursor = await conn.execute('''
                    SELECT can_use_commands FROM permissions WHERE guild_id = ? AND user_id = ?
                ''', (interaction.guild.id, interaction.user.id))

                permission = await cursor.fetchone()

                if permission and permission[0]:
                    return True

            if "Admin" in command.description or "Owner" in command.description:
                return False

            for check in command.checks:
                try:
                    if inspect.iscoroutinefunction(check):
                        result = await check(interaction)
                    else:
                        result = check(interaction)
                    if not result:
                        return False
                except Exception as e:
                    return False

            return True
        except Exception as e:
            print(f"Error in has_required_permissions: {e}")
            raise

    async def owner_check(self, interaction: discord.Interaction):
        owner_id = 111941993629806592
        return interaction.user.id == owner_id



    # ---------------------------------------------------------------------------------------------------------------------

    @app_commands.command(name="help", description="Display help information for all commands.")
    async def help(self, interaction: discord.Interaction):
        try:
            pages = []
            colour = await get_embed_colour(interaction.guild.id)

            help_intro = discord.Embed(
                title="About Waabit",
                description="*Hello, I am Waabit! I am a Discord APP capable of creating and "
                            "managing your music playing needs! I have many commands for "
                            "configuring and customising playlists! \n\n"
                            "You may navigate the pages of Commands simply by pressing the "
                            "buttons below.* \n\n",
                color=colour
            )


            pages.append(help_intro)

            for cog_name, cog in self.bot.cogs.items():
                if cog_name == "Core" or cog_name == "TheMachineBotCore" or cog_name == "AdminCog":
                    continue
                embed = discord.Embed(title=f"{cog_name.replace('Cog', '')} Commands", description="", color=colour)

                for cmd in cog.get_app_commands():
                    if "Owner" in cmd.description and not await self.owner_check(interaction):
                        continue
                    if not await self.has_required_permissions(interaction, cmd):
                        continue
                    embed.add_field(name=f"/{cmd.name}", value=f"```{cmd.description}```", inline=False)

                if len(embed.fields) > 0:
                    pages.append(embed)

            paginator = HelpPaginator(self.bot, pages=pages)
            await paginator.start(interaction)

        except Exception as e:
            logger.error(f"Error with Help command: {e}")
            await interaction.response.send_message("Failed to fetch help information.", ephemeral=True)
        finally:
            await log_command_usage(self.bot, interaction)

    # ---------------------------------------------------------------------------------------------------------------------

    @app_commands.command(description="Admin: Authorize a user to use the bot.")
    @app_commands.describe(user="The user to authorize")
    @app_commands.checks.has_permissions(administrator=True)
    async def authorise(self, interaction: discord.Interaction, user: discord.User):
        try:
            async with aiosqlite.connect(db_path) as conn:
                await conn.execute('''
                    INSERT INTO permissions (guild_id, user_id, can_use_commands) VALUES (?, ?, 1)
                    ON CONFLICT(guild_id, user_id) DO UPDATE SET can_use_commands = 1
                ''', (interaction.guild.id, user.id))
                await conn.commit()
            await interaction.response.send_message(f"{user.display_name} has been authorized.", ephemeral=True)

        except Exception as e:
            logger.error(f"Failed to authorise user: {e}")
            await interaction.response.send_message(f"Failed to authorise user: {e}",
                                                    ephemeral=True)


        finally:
            await log_command_usage(self.bot, interaction)

    @app_commands.command(description="Admin: Revoke a user's authorization to use the bot.")
    @app_commands.describe(user="The user to unauthorize")
    @app_commands.checks.has_permissions(administrator=True)
    async def unauthorise(self, interaction: discord.Interaction, user: discord.User):
        try:
            async with aiosqlite.connect(db_path) as conn:
                await conn.execute('''
                    UPDATE permissions SET can_use_commands = 0 WHERE guild_id = ? AND user_id = ?
                ''', (interaction.guild.id, user.id))
                await conn.commit()
            await interaction.response.send_message(f"{user.display_name} has been unauthorized.", ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to unauthorise user: {e}")
            await interaction.response.send_message(f"Failed to unauthorise user: {e}",
                                                    ephemeral=True)
        finally:
            await log_command_usage(self.bot, interaction)


    @app_commands.command(description="Owner: DM invite links for all servers the bot is in.")
    async def generate_invites(self, interaction: discord.Interaction):
        if not await self.owner_check(interaction):
            await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
            return

        try:
            await interaction.response.send_message("Generating invites and sending them to your DMs...", ephemeral=True)

            owner = await self.bot.fetch_user(111941993629806592)
            invite_messages = []

            for guild in self.bot.guilds:
                invite_link = None
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).create_instant_invite:
                        try:
                            invite = await channel.create_invite(max_age=0, max_uses=0, reason="Owner invite dump")
                            invite_link = invite.url
                            break
                        except Exception:
                            continue

                if invite_link:
                    invite_messages.append(f"**{guild.name}**: {invite_link}")
                else:
                    invite_messages.append(f"**{guild.name}**: ❌ Could not generate invite (no permissions).")

            # Chunk the messages if needed (Discord DM message length limit: 2000 chars)
            chunk = ""
            for line in invite_messages:
                if len(chunk) + len(line) + 1 > 2000:
                    await owner.send(chunk)
                    chunk = ""
                chunk += line + "\n"
            if chunk:
                await owner.send(chunk)

        except discord.Forbidden:
            await interaction.response.send_message("I couldn't send you a DM. Please make sure your DMs are open.", ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to generate invites: {e}")
            await interaction.response.send_message("Something went wrong while generating invites.", ephemeral=True)


# ---------------------------------------------------------------------------------------------------------------------
# Setup Function
# ---------------------------------------------------------------------------------------------------------------------
async def setup(bot):
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute('''
                CREATE TABLE IF NOT EXISTS permissions (
                    guild_id INTEGER,
                    user_id INTEGER,
                    can_use_commands BOOLEAN DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                )
            ''')

        await conn.commit()
    await bot.add_cog(UtilityCog(bot))




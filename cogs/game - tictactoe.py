import random
import discord
import aiosqlite
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

from core.utils import check_permissions, log_command_usage, is_shitty_friend
# ---------------------------------------------------------------------------------------------------------------------
# Database Configuration
# ---------------------------------------------------------------------------------------------------------------------
db_path = './data/databases/jeb.db'

#  ---------------------------------------------------------------------------------------------------------------------
#  Challenge View
#  ---------------------------------------------------------------------------------------------------------------------
class ChallengeView(View):
    def __init__(self, opponent: discord.Member, challenger: discord.User, challenge_interaction: discord.Interaction):
        super().__init__()
        self.opponent = opponent
        self.challenger = challenger
        self.challenge_interaction = challenge_interaction

    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.secondary, disabled=True)
    async def blank1(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("You are not the one being challenged!", ephemeral=True)
        else:
            game_view = GameView(self.opponent, self.challenger, interaction)
            game_view.create_board()
            await interaction.response.edit_message(content=f"Game started! It's {self.challenger.mention}'s turn",
                                                    embed=None, view=game_view)

    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.secondary, disabled=True)
    async def blank2(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("You are not the one being challenged!", ephemeral=True)
        else:
            embed = discord.Embed(
                title="᲼᲼᲼Challenge Rejected!",
                description=f"{interaction.user.display_name} has rejected the challenge",
                color=discord.Color.from_str("#8e4cd0")
            )
            await self.challenge_interaction.edit_original_response(content="",
                                                                    embed=embed,
                                                                    view=None)
            await interaction.response.send_message("You have rejected the challenge.", ephemeral=True)

    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.secondary, disabled=True)
    async def blank3(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

#  ---------------------------------------------------------------------------------------------------------------------
#  Game View
#  ---------------------------------------------------------------------------------------------------------------------
class GameView(View):
    def __init__(self, opponent: discord.Member, challenger: discord.User, original_interaction: discord.Interaction):
        super().__init__()
        self.opponent = opponent
        self.challenger = challenger
        self.original_interaction = original_interaction
        self.board = [[" " for _ in range(3)] for _ in range(3)]
        self.game_over = False

        players = [self.challenger, self.opponent]
        random.shuffle(players)
        self.current_player = players[0]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.opponent or interaction.user == self.challenger

    async def update_leaderboard(self, guild_id, winner_id, loser_id, draw=False):
        game_name = "TicTacToe"
        async with aiosqlite.connect(db_path) as db:
            if draw:
                await db.execute(
                    "INSERT INTO leaderboards (guild_id, game, user_id, draws) VALUES (?, ?, ?, 1) "
                    "ON CONFLICT(guild_id, game, user_id) DO UPDATE SET draws = draws + 1",
                    (guild_id, game_name, winner_id)
                )
                await db.execute(
                    "INSERT INTO leaderboards (guild_id, game, user_id, draws) VALUES (?, ?, ?, 1) "
                    "ON CONFLICT(guild_id, game, user_id) DO UPDATE SET draws = draws + 1",
                    (guild_id, game_name, loser_id)
                )
            else:
                await db.execute(
                    "INSERT INTO leaderboards (guild_id, game, user_id, wins) VALUES (?, ?, ?, 1) "
                    "ON CONFLICT(guild_id, game, user_id) DO UPDATE SET wins = wins + 1",
                    (guild_id, game_name, winner_id)
                )
                await db.execute(
                    "INSERT INTO leaderboards (guild_id, game, user_id, losses) VALUES (?, ?, ?, 1) "
                    "ON CONFLICT(guild_id, game, user_id) DO UPDATE SET losses = losses + 1",
                    (guild_id, game_name, loser_id)
                )
            await db.commit()

    def create_board(self):
        self.clear_items()  # Clear any existing buttons
        for i in range(3):
            for j in range(3):
                button = Button(label="\u200b",
                                style=discord.ButtonStyle.secondary,
                                custom_id=f"cell_{i}_{j}", row=i)
                button.callback = self.make_move
                self.add_item(button)

    async def make_move(self, interaction: discord.Interaction):
        if interaction.user != self.current_player or self.game_over:
            await interaction.response.defer()
            return

        custom_id = interaction.data['custom_id']
        row, col = map(int, custom_id.split('_')[1:])

        if self.board[row][col] != " ":
            await interaction.response.defer()
            return

        self.board[row][col] = "X" if self.current_player == self.challenger else "O"

        button = discord.utils.get(self.children, custom_id=custom_id)
        button.label = self.board[row][col]
        button.disabled = True
        button.style = discord.ButtonStyle.primary if self.board[row][col] == "X" else discord.ButtonStyle.danger

        winner, winning_line = self.check_winner()
        if winner:
            for win_button_custom_id in winning_line:
                win_button = discord.utils.get(self.children, custom_id='_'.join(map(str, win_button_custom_id)))
                win_button.style = discord.ButtonStyle.success
            self.game_over = True
            content = f"{self.current_player.mention} wins!"
            self.disable_all_buttons()

            await self.update_leaderboard(interaction.guild_id, self.current_player.id,
                                          self.opponent.id if self.current_player == self.challenger else self.challenger.id)

        elif all(self.board[i][j] != " " for i in range(3) for j in range(3)):
            self.game_over = True
            content = "It's a draw!"
            self.disable_all_buttons()

            await self.update_leaderboard(interaction.guild_id, self.challenger.id, self.opponent.id, draw=True)

        else:
            self.current_player = self.opponent if self.current_player == self.challenger else self.challenger
            content = f"It's {self.current_player.mention}'s turn"

        await interaction.response.edit_message(content=content, view=self)

    def check_winner(self):
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != " ":
                return True, [('cell', i, j) for j in range(3)]
            if self.board[0][i] == self.board[1][i] == self.board[2][i] != " ":
                return True, [('cell', j, i) for j in range(3)]

        if self.board[0][0] == self.board[1][1] == self.board[2][2] != " ":
            return True, [('cell', i, i) for i in range(3)]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != " ":
            return True, [('cell', i, 2 - i) for i in range(3)]

        return False, None

    def disable_all_buttons(self):
        for item in self.children:
            if isinstance(item, Button):
                item.disabled = True

#  ---------------------------------------------------------------------------------------------------------------------
#  TicTacToe Cog
#  ---------------------------------------------------------------------------------------------------------------------
class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Play a game of TicTacToe")
    async def ttt(self, interaction: discord.Interaction, opponent: discord.Member):
        await interaction.response.defer()

        embed = discord.Embed(
            title=f"᲼᲼᲼᲼᲼᲼᲼᲼᲼᲼᲼᲼TicTacToe Challenge!",
            description=f"{opponent.mention}, you have been challenged by {interaction.user.mention}.",
            color=discord.Color.from_str("#8e4cd0")
        )
        embed.set_footer(text="᲼᲼᲼᲼Click a button below to accept or reject the challenge")

        view = ChallengeView(opponent, interaction.user, interaction)
        await interaction.followup.send(content=f"{interaction.user.mention} has challenged {opponent.mention}!",
                                        embed=embed, view=view)


        await log_command_usage(self.bot, interaction)


#  ---------------------------------------------------------------------------------------------------------------------
#  Setup Function
#  ---------------------------------------------------------------------------------------------------------------------
async def setup(bot):
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS leaderboards (
                guild_id INTEGER,
                game TEXT,
                user_id INTEGER,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                draws INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, game, user_id)
            )
        ''')
        await conn.commit()
    await bot.add_cog(TicTacToe(bot))

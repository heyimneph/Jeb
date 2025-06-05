import importlib.util
from pathlib import Path
import sys
import types

# Create a minimal mock of the discord package
mock_discord = types.ModuleType("discord")

class DummyView:
    def __init__(self, *args, **kwargs):
        self.children = []
    def add_item(self, item):
        self.children.append(item)
    def clear_items(self):
        self.children.clear()

class DummyButton:
    pass

class DummyButtonStyle:
    secondary = 'secondary'
    success = 'success'
    danger = 'danger'
    primary = 'primary'

def dummy_button(*args, **kwargs):
    def decorator(func):
        return func
    return decorator

mock_ui = types.ModuleType("discord.ui")
mock_ui.Button = DummyButton
mock_ui.View = DummyView
mock_ui.button = dummy_button

mock_discord.ui = mock_ui
mock_discord.ButtonStyle = DummyButtonStyle
mock_discord.Member = object
mock_discord.User = object
mock_discord.Interaction = object
mock_discord.utils = types.SimpleNamespace(get=lambda children, custom_id: None)

mock_app_commands = types.ModuleType("discord.app_commands")
mock_app_commands.command = lambda *args, **kwargs: (lambda f: f)
mock_discord.app_commands = mock_app_commands

mock_ext_commands = types.ModuleType("discord.ext.commands")
mock_ext_commands.Cog = object
mock_ext = types.ModuleType("discord.ext")
mock_ext.commands = mock_ext_commands
mock_discord.ext = mock_ext

sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = mock_ui
sys.modules["discord.app_commands"] = mock_app_commands
sys.modules["discord.ext"] = mock_ext
sys.modules["discord.ext.commands"] = mock_ext_commands

# Load the module containing GameView
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
module_path = REPO_ROOT / "cogs" / "game - tictactoe.py"
spec = importlib.util.spec_from_file_location("tictactoe_module", module_path)
tictactoe_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tictactoe_module)
GameView = tictactoe_module.GameView


def test_check_winner_horizontal():
    gv = GameView(None, None, None)
    gv.board = [
        ["X", "X", "X"],
        ["O", " ", "O"],
        [" ", " ", " "]
    ]
    result, line = gv.check_winner()
    assert result is True
    assert line == [("cell", 0, 0), ("cell", 0, 1), ("cell", 0, 2)]


def test_check_winner_vertical():
    gv = GameView(None, None, None)
    gv.board = [
        ["X", "O", " "],
        ["X", "O", " "],
        ["X", " ", " "]
    ]
    result, line = gv.check_winner()
    assert result is True
    assert line == [("cell", 0, 0), ("cell", 1, 0), ("cell", 2, 0)]


def test_check_winner_diagonal():
    gv = GameView(None, None, None)
    gv.board = [
        ["X", "O", " "],
        ["O", "X", " "],
        [" ", " ", "X"]
    ]
    result, line = gv.check_winner()
    assert result is True
    assert line == [("cell", 0, 0), ("cell", 1, 1), ("cell", 2, 2)]


def test_check_winner_no_win():
    gv = GameView(None, None, None)
    gv.board = [
        ["X", "O", "X"],
        ["O", "X", "O"],
        ["O", "X", "O"]
    ]
    result, line = gv.check_winner()
    assert result is False
    assert line is None

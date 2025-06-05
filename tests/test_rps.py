import importlib.util
from pathlib import Path
import sys

# Load the module containing GameView
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

module_path = REPO_ROOT / "cogs" / "game - rps.py"
spec = importlib.util.spec_from_file_location("rps_module", module_path)
rps_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rps_module)
GameView = rps_module.GameView


def test_determine_winner_tie():
    result, winner, loser = GameView.determine_winner(None, [1, 2], ['🪨', '🪨'])
    assert result == "It's a tie!"
    assert winner is None
    assert loser is None


def test_determine_winner_player1_win():
    result, winner, loser = GameView.determine_winner(None, [1, 2], ['🪨', '✂️'])
    assert result == "Winner determined"
    assert winner == 1
    assert loser == 2


def test_determine_winner_player2_win():
    result, winner, loser = GameView.determine_winner(None, [1, 2], ['📜', '✂️'])
    assert result == "Winner determined"
    assert winner == 2
    assert loser == 1

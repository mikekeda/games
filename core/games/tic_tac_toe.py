"""Tic-tac-toe."""

from core.games.base import LineUpGame
from core.games.bots import NegamaxBot
from core.games.registry import register


class TicTacToeBot(NegamaxBot):
    """Searches the whole game tree -- 3x3 is small enough to solve exactly."""

    max_depth = 9


@register
class TicTacToe(LineUpGame):
    slug = "TicTacToe"
    title = "Tic-tac-toe"
    description = (
        "Tic-tac-toe (also known as noughts and crosses or Xs and Os) is a "
        "paper-and-pencil game for two players, X and O, who take turns "
        "marking the spaces in a 3x3 grid. The player who succeeds in placing "
        "three of their marks in a horizontal, vertical, or diagonal row wins "
        "the game."
    )

    rows = 3
    cols = 3
    need_in_line = 3
    tokens = ("X", "O")
    render_map = {"*": "", "X": "\u2715", "O": "\u25ef"}
    cell_size = 150
    bot = TicTacToeBot

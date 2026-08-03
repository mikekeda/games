"""
Games package.

Game classes live in their own module and register themselves with the
:mod:`core.games.registry`. Nothing here needs editing to add a game.
"""

from core.games.base import (
    EMPTY,
    Game,
    GameState,
    GridGame,
    InvalidMove,
    LineUpGame,
    Move,
    MoveStyle,
    Outcome,
)
from core.games.registry import (
    all_games,
    autodiscover,
    game_choices,
    games_info,
    get_game,
    register,
)

__all__ = [
    "EMPTY",
    "Game",
    "GameState",
    "GridGame",
    "InvalidMove",
    "LineUpGame",
    "Move",
    "MoveStyle",
    "Outcome",
    "all_games",
    "autodiscover",
    "game_choices",
    "games_info",
    "get_game",
    "register",
]

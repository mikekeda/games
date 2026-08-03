"""
Computer opponents.

Bots are generic: they drive a game purely through the :class:`~core.games.base.Game`
interface, so any new game gets a working opponent for free as long as it
implements ``legal_moves``, ``apply``, ``outcome`` and (optionally)
``heuristic``.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod

from core.games.base import Game, GameState, Move

#: Score used for a forced win; larger than any heuristic can produce.
WIN_SCORE = 1e9


class Bot(ABC):
    """Chooses a move for a computer-controlled player."""

    @classmethod
    @abstractmethod
    def choose(cls, game: type[Game], state: GameState, player: int) -> Move | None:
        """Return a move, or ``None`` when the bot has nothing to play."""


class RandomBot(Bot):
    """Plays a uniformly random legal move. A useful baseline for new games."""

    @classmethod
    def choose(cls, game, state, player):
        moves = list(game.legal_moves(state))
        return random.choice(moves) if moves else None


class NegamaxBot(Bot):
    """Depth-limited negamax with alpha-beta pruning.

    Works for any two-player, zero-sum, perfect-information game. Set
    ``max_depth`` high enough to search a small game to the end (tic-tac-toe),
    or low enough to stay responsive on a larger one (connect four).
    """

    max_depth: int = 4

    @classmethod
    def order_moves(cls, game, state, moves: list[Move]) -> list[Move]:
        """Decide which moves to search first.

        Alpha-beta prunes far more when good moves come first, so a subclass
        that knows something about the game can make the search much cheaper.
        """
        return moves

    @classmethod
    def choose(cls, game, state, player):
        moves = list(game.legal_moves(state))
        if not moves:
            return None

        best_score = -float("inf")
        best_moves: list[Move] = []

        for move in cls.order_moves(game, state, moves):
            score = -cls._search(
                game,
                game.apply(state, player, move),
                cls.max_depth - 1,
                -float("inf"),
                float("inf"),
            )
            if score > best_score:
                best_score, best_moves = score, [move]
            elif score == best_score:
                best_moves.append(move)

        # Tie-break randomly so repeated games against the bot differ.
        return random.choice(best_moves)

    @classmethod
    def _search(
        cls,
        game: type[Game],
        state: GameState,
        depth: int,
        alpha: float,
        beta: float,
    ) -> float:
        """Score ``state`` from the point of view of the player to move."""
        mover = state.turn

        outcome = game.outcome(state)
        if outcome is not None:
            if outcome.is_draw:
                return 0.0
            # Prefer quick wins and slow losses so the bot finishes games off.
            return (
                (WIN_SCORE + depth) if outcome.winner == mover else -(WIN_SCORE + depth)
            )

        if depth <= 0:
            return game.heuristic(state, mover)

        moves = cls.order_moves(game, state, list(game.legal_moves(state)))
        if not moves:
            return game.heuristic(state, mover)

        best = -float("inf")
        for move in moves:
            score = -cls._search(
                game, game.apply(state, mover, move), depth - 1, -beta, -alpha
            )
            best = max(best, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        return best


class CenterFirstNegamaxBot(NegamaxBot):
    """Negamax that examines central columns first.

    In games with gravity the centre is where most lines cross, so searching it
    first produces much earlier cutoffs.
    """

    @classmethod
    def order_moves(cls, game, state, moves):
        centre = (game.cols - 1) / 2
        return sorted(moves, key=lambda move: abs(move.to_col - centre))

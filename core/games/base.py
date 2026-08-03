"""
Core game engine.

This module is deliberately free of Django imports: game rules are plain
Python and can be exercised without a database or settings module.

The engine is built around three ideas:

* :class:`GameState` carries everything needed to continue a game -- the
  board, whose turn it is, and a free-form ``extra`` dict for rules that do
  not fit in the grid (castling rights, en passant target, ...).
* :class:`Move` can express both "drop a token on a square" and
  "move the piece on square A to square B", so games with travelling pieces
  are representable.
* :class:`Game` subclasses are stateless: every method takes a state and
  returns a new one. Nothing is mutated in place.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Iterator

EMPTY = "*"

#: Direction vectors used when scanning for a line of tokens. Only four are
#: needed because each line is found from whichever end comes first in the scan.
DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


class InvalidMove(ValueError):
    """Raised when a move cannot be parsed or is not legal in the position."""


class MoveStyle:
    """How the client should collect a move from the player."""

    #: Click an empty square to place a token there.
    PLACE = "place"
    #: Click one of your pieces, then click its destination.
    SELECT = "select"


@dataclass(frozen=True)
class Move:
    """A single move.

    Placement games (tic-tac-toe, connect four, gomoku) only use
    ``to_row``/``to_col``. Games with travelling pieces (chess, checkers) also
    set ``from_row``/``from_col``.
    """

    to_row: int
    to_col: int
    from_row: int | None = None
    from_col: int | None = None
    promotion: str | None = None

    @property
    def is_relocation(self) -> bool:
        """True when the move takes a piece from one square to another."""
        return self.from_row is not None and self.from_col is not None

    @property
    def origin(self) -> tuple[int, int] | None:
        return (self.from_row, self.from_col) if self.is_relocation else None

    @property
    def target(self) -> tuple[int, int]:
        return self.to_row, self.to_col

    @classmethod
    def parse(cls, raw: Any) -> "Move":
        """Build a move from an untrusted client payload.

        Accepts the structured form ``{"to": [r, c], "from": [r, c]}`` as well
        as the legacy ``"row-col"`` string. Anything else raises
        :class:`InvalidMove` so callers never see a bare ``ValueError`` or
        ``IndexError`` escaping from the network layer.
        """
        if isinstance(raw, Move):
            return raw

        if isinstance(raw, str):
            parts = raw.split("-")
            if len(parts) != 2:
                raise InvalidMove(f"Cannot parse move {raw!r}")
            return cls(*cls._coords(parts))

        if isinstance(raw, dict):
            target = cls._coords(raw.get("to"))
            origin = raw.get("from")
            promotion = raw.get("promotion")
            if promotion is not None and not isinstance(promotion, str):
                raise InvalidMove("Invalid promotion")
            if origin is None:
                return cls(*target, promotion=promotion)
            return cls(*target, *cls._coords(origin), promotion=promotion)

        raise InvalidMove(f"Cannot parse move {raw!r}")

    @staticmethod
    def _coords(value: Any) -> tuple[int, int]:
        """Coerce a two element sequence into a pair of ints."""
        if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
            raise InvalidMove(f"Invalid coordinates {value!r}")
        if len(value) != 2:
            raise InvalidMove(f"Invalid coordinates {value!r}")
        try:
            return int(value[0]), int(value[1])
        except (TypeError, ValueError) as exc:
            raise InvalidMove(f"Invalid coordinates {value!r}") from exc

    def serialize(self) -> dict:
        """Representation suitable for JSON storage and websocket payloads."""
        data: dict[str, Any] = {"to": [self.to_row, self.to_col]}
        if self.is_relocation:
            data["from"] = [self.from_row, self.from_col]
        if self.promotion:
            data["promotion"] = self.promotion
        return data


@dataclass(frozen=True)
class Outcome:
    """The result of a finished game.

    ``winner`` is a player index, or ``None`` for a draw. An unfinished game is
    represented by the absence of an ``Outcome`` (``None``) rather than by a
    sentinel value.
    """

    winner: int | None = None
    reason: str = ""
    #: Squares that caused the result, so the UI can highlight them.
    cells: tuple[tuple[int, int], ...] = ()

    @property
    def is_draw(self) -> bool:
        return self.winner is None


@dataclass
class GameState:
    """Everything needed to resume a game."""

    board: list[list[str]]
    turn: int = 0
    extra: dict = field(default_factory=dict)

    def copy(self) -> "GameState":
        return GameState(
            board=[list(row) for row in self.board],
            turn=self.turn,
            extra=deepcopy(self.extra),
        )


class Game(ABC):
    """Interface every game implements.

    Subclasses are never instantiated; all methods are classmethods operating
    on an explicit :class:`GameState`.
    """

    #: Stable public identifier. Used in URLs and stored in the database, so it
    #: must not change once a game has shipped.
    slug: str = ""
    title: str = ""
    description: str = ""

    rows: int = 0
    cols: int = 0
    player_count: int = 2

    empty: str = EMPTY
    #: One token per player, indexed by player number.
    tokens: tuple[str, ...] = ()
    #: Maps stored cell values to what the player sees.
    render_map: dict[str, str] = {}

    #: Render row 0 at the bottom (games where pieces stack upwards).
    flip_board: bool = False
    move_style: str = MoveStyle.PLACE
    #: Square size in pixels. The board stylesheet reads this, so a new game
    #: needs no CSS of its own.
    cell_size: int = 75

    #: Bot used when a player is the built-in opponent.
    bot: "type | None" = None

    @classmethod
    @abstractmethod
    def initial_state(cls) -> GameState:
        """Return the opening position."""

    @classmethod
    @abstractmethod
    def legal_moves(cls, state: GameState) -> Iterator[Move]:
        """Yield every move the player to move may make."""

    @classmethod
    @abstractmethod
    def apply(cls, state: GameState, player: int, move: Move) -> GameState:
        """Return a new state with ``move`` played. Never mutates ``state``."""

    @classmethod
    @abstractmethod
    def outcome(cls, state: GameState) -> Outcome | None:
        """Return the result, or ``None`` while the game is still running."""

    @classmethod
    @abstractmethod
    def validate(cls, state: GameState) -> tuple[bool, str | None]:
        """Check a state is reachable. Used by the admin and by fixtures."""

    @classmethod
    @abstractmethod
    def render(cls, state: GameState) -> list[list[str]]:
        """Return a display-ready board. Never mutates ``state``."""

    @classmethod
    def is_legal(cls, state: GameState, player: int, move: Move) -> bool:
        """Whether ``player`` may play ``move`` right now.

        Turn order is checked explicitly here rather than being inferred from
        the contents of the board, so it keeps working for games where pieces
        are captured or a player may move more than once.
        """
        if player != state.turn:
            return False
        return any(move == legal for legal in cls.legal_moves(state))

    @classmethod
    def next_turn(cls, state: GameState, player: int) -> int:
        """Index of the player to move after ``player``."""
        return (player + 1) % cls.player_count

    @classmethod
    def heuristic(cls, state: GameState, player: int) -> float:
        """Score a non-terminal position from ``player``'s point of view.

        Used by search bots when they run out of depth. The default treats
        every unfinished position as equal.
        """
        return 0.0

    @classmethod
    def info(cls) -> dict:
        """Metadata for listing pages."""
        return {
            "slug": cls.slug,
            "title": cls.title,
            "description": cls.description,
            "rows": cls.rows,
            "cols": cls.cols,
            "players": cls.player_count,
            "cell_size": cls.cell_size,
        }


class GridGame(Game):
    """A game played on a rectangular grid of single tokens.

    Supplies the board bookkeeping that every grid game needs: building a
    fresh board, bounds checks, rendering and scanning for lines.
    """

    @classmethod
    def initial_board(cls) -> list[list[str]]:
        # Each row is built separately; a multiplied list would alias one row
        # object across the whole board.
        return [[cls.empty] * cls.cols for _ in range(cls.rows)]

    @classmethod
    def initial_extra(cls) -> dict:
        return {}

    @classmethod
    def initial_state(cls) -> GameState:
        return GameState(board=cls.initial_board(), turn=0, extra=cls.initial_extra())

    @classmethod
    def in_bounds(cls, row: int, col: int) -> bool:
        return 0 <= row < cls.rows and 0 <= col < cls.cols

    @classmethod
    def cells(cls) -> Iterator[tuple[int, int]]:
        for row in range(cls.rows):
            for col in range(cls.cols):
                yield row, col

    @classmethod
    def empty_cells(cls, board: list[list[str]]) -> Iterator[tuple[int, int]]:
        for row, col in cls.cells():
            if board[row][col] == cls.empty:
                yield row, col

    @classmethod
    def is_full(cls, board: list[list[str]]) -> bool:
        return all(board[row][col] != cls.empty for row, col in cls.cells())

    @classmethod
    def allowed_values(cls) -> set[str]:
        return {cls.empty, *cls.tokens}

    @classmethod
    def validate(cls, state: GameState) -> tuple[bool, str | None]:
        board = state.board
        if len(board) != cls.rows or any(len(row) != cls.cols for row in board):
            return False, f"Board must be {cls.rows}x{cls.cols}"

        allowed = cls.allowed_values()
        used = {cell for row in board for cell in row}
        if used - allowed:
            return False, f"Only {', '.join(sorted(allowed))} are allowed"

        if not 0 <= state.turn < cls.player_count:
            return False, "Invalid turn"

        return True, None

    @classmethod
    def render(cls, state: GameState) -> list[list[str]]:
        return [[cls.render_map.get(cell, cell) for cell in row] for row in state.board]

    @classmethod
    def find_line(
        cls, board: list[list[str]], length: int
    ) -> tuple[str, tuple[tuple[int, int], ...]] | None:
        """Find ``length`` identical non-empty tokens in a row.

        Returns the token and the squares making up the line, or ``None``.
        """
        for row, col in cls.cells():
            token = board[row][col]
            if token == cls.empty:
                continue

            for delta_row, delta_col in DIRECTIONS:
                end_row = row + delta_row * (length - 1)
                end_col = col + delta_col * (length - 1)
                if not cls.in_bounds(end_row, end_col):
                    continue

                line = tuple(
                    (row + delta_row * step, col + delta_col * step)
                    for step in range(length)
                )
                if all(board[r][c] == token for r, c in line):
                    return token, line

        return None

    @classmethod
    def windows(cls, length: int) -> Iterator[tuple[tuple[int, int], ...]]:
        """Yield every straight run of ``length`` squares on the board."""
        for row, col in cls.cells():
            for delta_row, delta_col in DIRECTIONS:
                end_row = row + delta_row * (length - 1)
                end_col = col + delta_col * (length - 1)
                if not cls.in_bounds(end_row, end_col):
                    continue
                yield tuple(
                    (row + delta_row * step, col + delta_col * step)
                    for step in range(length)
                )


class LineUpGame(GridGame):
    """Grid games won by lining up ``need_in_line`` tokens.

    Covers tic-tac-toe, connect four, gomoku and friends. A subclass normally
    only needs to declare its dimensions, tokens and ``need_in_line``; connect
    four additionally restricts :meth:`legal_moves` to enforce gravity.
    """

    need_in_line: int = 3

    @classmethod
    def outcome(cls, state: GameState) -> Outcome | None:
        found = cls.find_line(state.board, cls.need_in_line)
        if found is not None:
            token, line = found
            return Outcome(winner=cls.tokens.index(token), reason="line", cells=line)

        if cls.is_full(state.board):
            return Outcome(winner=None, reason="board full")

        return None

    @classmethod
    def legal_moves(cls, state: GameState) -> Iterator[Move]:
        if cls.outcome(state) is not None:
            return
        for row, col in cls.empty_cells(state.board):
            yield Move(row, col)

    @classmethod
    def apply(cls, state: GameState, player: int, move: Move) -> GameState:
        if not cls.is_legal(state, player, move):
            raise InvalidMove(f"{move} is not legal in this position")

        new_state = state.copy()
        new_state.board[move.to_row][move.to_col] = cls.tokens[player]
        new_state.turn = cls.next_turn(state, player)
        return new_state

    @classmethod
    def heuristic(cls, state: GameState, player: int) -> float:
        """Reward windows the player could still complete, penalise the opponent's.

        Each straight run of ``need_in_line`` squares is worth something only
        while a single player occupies it; a window containing both players'
        tokens can never be completed and scores zero.
        """
        board = state.board
        mine = cls.tokens[player]
        score = 0.0

        for window in cls.windows(cls.need_in_line):
            values = [board[row][col] for row, col in window]
            occupied = [value for value in values if value != cls.empty]
            if not occupied:
                continue
            if len(set(occupied)) > 1:
                continue

            # Nearly complete windows are worth far more than sparse ones.
            weight = 10.0 ** (len(occupied) - 1)
            score += weight if occupied[0] == mine else -weight

        return score

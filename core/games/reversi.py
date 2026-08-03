"""Reversi, also sold as Othello."""

from core.games.base import GameState, GridGame, InvalidMove, Move, Outcome
from core.games.bots import NegamaxBot
from core.games.registry import register

#: The eight directions a captured line can run in. Unlike the four in
#: ``base``, these are not folded in half: a line is only captured when it is
#: closed at the far end, so each direction has to be walked on its own.
RAYS = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)

#: What holding each square is worth. Corners can never be flipped, so they
#: are worth far more than anything else; the squares touching a corner are
#: penalised because playing them is usually what hands the corner over.
SQUARE_VALUES = (
    (120, -20, 20, 5, 5, 20, -20, 120),
    (-20, -40, -5, -5, -5, -5, -40, -20),
    (20, -5, 15, 3, 3, 15, -5, 20),
    (5, -5, 3, 3, 3, 3, -5, 5),
    (5, -5, 3, 3, 3, 3, -5, 5),
    (20, -5, 15, 3, 3, 15, -5, 20),
    (-20, -40, -5, -5, -5, -5, -40, -20),
    (120, -20, 20, 5, 5, 20, -20, 120),
)

#: Roughly how many points a spare move is worth, for the mobility term.
MOBILITY_WEIGHT = 10


class ReversiBot(NegamaxBot):
    """Searches three plies, examining corners first.

    Three rather than four on measurement, not principle: over eight games the
    two were level (4-3 with a draw), but three plies takes 0.06s a move
    against 0.44s, with a worst case of 0.18s against 1.9s. Since the bot runs
    inside the websocket handler, holding that thread for two seconds is worse
    than anything the extra ply buys. An odd depth also scores every leaf just
    after the bot has moved, which keeps the positional term consistent.
    """

    max_depth = 3

    @classmethod
    def order_moves(cls, game, state, moves):
        return sorted(moves, key=lambda move: -SQUARE_VALUES[move.to_row][move.to_col])


@register
class Reversi(GridGame):
    slug = "Reversi"
    title = "Reversi"
    description = (
        "Reversi (sold as Othello) is a two-player game on an 8x8 board. A "
        "move must trap a straight line of the opponent's discs between the "
        "disc you place and one of your own, and every disc in that line is "
        "flipped to your colour. Whoever has the most discs when neither "
        "player can move wins."
    )

    rows = 8
    cols = 8
    tokens = ("X", "O")
    render_map = {"*": "", "X": "\u26ab", "O": "\u26aa"}
    cell_size = 56
    show_legal_moves = True
    bot = ReversiBot

    @classmethod
    def initial_state(cls) -> GameState:
        """The four discs the game opens with, crossed in the middle."""
        board = cls.initial_board()
        board[3][3] = board[4][4] = cls.tokens[1]
        board[3][4] = board[4][3] = cls.tokens[0]
        return GameState(board=board, turn=0)

    @classmethod
    def opponent_of(cls, player: int) -> int:
        """The other player.

        Not :meth:`next_turn`, which is about whose turn it is next and has to
        account for passing.
        """
        return (player + 1) % cls.player_count

    @classmethod
    def captures(cls, board: list[list[str]], row: int, col: int, token: str) -> list:
        """Discs that playing ``token`` on ``(row, col)`` would flip.

        Empty when the move is not legal, since a move that captures nothing
        is exactly what the rules forbid.
        """
        if not cls.in_bounds(row, col) or board[row][col] != cls.empty:
            return []

        captured = []
        for delta_row, delta_col in RAYS:
            line = []
            scan_row, scan_col = row + delta_row, col + delta_col
            while (
                cls.in_bounds(scan_row, scan_col)
                and board[scan_row][scan_col] != cls.empty
                and board[scan_row][scan_col] != token
            ):
                line.append((scan_row, scan_col))
                scan_row, scan_col = scan_row + delta_row, scan_col + delta_col

            # Only a run closed off by one of your own discs is captured; one
            # that runs off the board or into a gap is not.
            if (
                line
                and cls.in_bounds(scan_row, scan_col)
                and board[scan_row][scan_col] == token
            ):
                captured.extend(line)

        return captured

    @classmethod
    def moves_for(cls, board: list[list[str]], player: int) -> list[Move]:
        """Every move ``player`` could make on ``board``."""
        token = cls.tokens[player]
        return [
            Move(row, col)
            for row, col in cls.empty_cells(board)
            if cls.captures(board, row, col, token)
        ]

    @classmethod
    def has_moves(cls, board: list[list[str]], player: int) -> bool:
        """Whether ``player`` can move at all. Stops at the first one it finds."""
        token = cls.tokens[player]
        return any(
            cls.captures(board, row, col, token) for row, col in cls.empty_cells(board)
        )

    @classmethod
    def legal_moves(cls, state: GameState):
        # Deliberately does not consult outcome(): the game being over is
        # defined as neither player having a move, so that would recurse.
        yield from cls.moves_for(state.board, state.turn)

    @classmethod
    def next_turn(cls, state: GameState, player: int) -> int:
        """Whose turn it is after ``player`` has moved.

        A player with nothing to play passes, which is part of the rules
        rather than an error, so the turn can come straight back. ``state``
        must already have the move applied.
        """
        opponent = cls.opponent_of(player)
        if cls.has_moves(state.board, opponent):
            return opponent
        if cls.has_moves(state.board, player):
            return player

        # Neither side can move, so the game is over and the turn stops
        # mattering. Handing it back keeps the alternation tidy.
        return opponent

    @classmethod
    def apply(cls, state: GameState, player: int, move: Move) -> GameState:
        if player != state.turn:
            raise InvalidMove("It is not your turn")

        token = cls.tokens[player]
        captured = cls.captures(state.board, move.to_row, move.to_col, token)
        if not captured:
            raise InvalidMove(f"{move} captures nothing, so it is not legal")

        new_state = state.copy()
        new_state.board[move.to_row][move.to_col] = token
        for row, col in captured:
            new_state.board[row][col] = token

        new_state.turn = cls.next_turn(new_state, player)
        return new_state

    @classmethod
    def counts(cls, board: list[list[str]]) -> list[int]:
        """How many discs each player has."""
        return [sum(row.count(token) for row in board) for token in cls.tokens]

    @classmethod
    def outcome(cls, state: GameState) -> Outcome | None:
        board = state.board

        # Usually the player to move has something, which settles it in one
        # scan. The board filling up is covered too: nobody can move then.
        if cls.has_moves(board, state.turn) or cls.has_moves(
            board, cls.opponent_of(state.turn)
        ):
            return None

        counts = cls.counts(board)
        best = max(counts)
        if counts.count(best) > 1:
            return Outcome(winner=None, reason="equal discs")

        return Outcome(winner=counts.index(best), reason="most discs")

    @classmethod
    def heuristic(cls, state: GameState, player: int) -> float:
        """Score a position by where the discs are, not how many there are.

        Disc count is a poor guide until the very end -- a big lead in the
        midgame usually just means more discs for the opponent to flip. What
        lasts is holding corners, staying off the squares beside them, and
        having more moves available than the opponent.
        """
        board = state.board
        opponent = cls.opponent_of(player)
        mine, theirs = cls.tokens[player], cls.tokens[opponent]

        score = 0
        for row, col in cls.cells():
            if board[row][col] == mine:
                score += SQUARE_VALUES[row][col]
            elif board[row][col] == theirs:
                score -= SQUARE_VALUES[row][col]

        mobility = len(cls.moves_for(board, player)) - len(
            cls.moves_for(board, opponent)
        )

        return score + MOBILITY_WEIGHT * mobility

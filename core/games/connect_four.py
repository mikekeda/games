"""Connect four."""

from core.games.base import GameState, LineUpGame, Move
from core.games.bots import CenterFirstNegamaxBot
from core.games.registry import register


class ConnectFourBot(CenterFirstNegamaxBot):
    """Shallow search -- the branching factor is only seven, but Python is slow.

    Four plies is enough to take an immediate win, block an immediate threat
    and avoid handing the opponent one, while staying well under a second.
    """

    max_depth = 4


@register
class ConnectFour(LineUpGame):
    slug = "ConnectFour"
    title = "Connect four"
    description = (
        "Connect Four (also known as Captain's Mistress, Four Up, Plot Four, "
        "Find Four, Four in a Row, Four in a Line) is a two-player connection "
        "game in which the players first choose a color and then take turns "
        "dropping one colored disc from the top into a seven-column, six-row "
        "vertically suspended grid."
    )

    rows = 6
    cols = 7
    need_in_line = 4
    tokens = ("X", "O")
    render_map = {"*": "", "X": "\U0001f535", "O": "\U0001f534"}

    # Row 0 is the bottom of the grid, so it has to be drawn last.
    flip_board = True
    bot = ConnectFourBot

    @classmethod
    def legal_moves(cls, state: GameState):
        """Only the lowest empty square in each column can be played."""
        if cls.outcome(state) is not None:
            return

        for col in range(cls.cols):
            for row in range(cls.rows):
                if state.board[row][col] == cls.empty:
                    yield Move(row, col)
                    break

    @classmethod
    def validate(cls, state: GameState) -> tuple[bool, str | None]:
        valid, error = super().validate(state)
        if not valid:
            return valid, error

        # A disc can never float: every filled square must sit on a filled one.
        for col in range(cls.cols):
            seen_empty = False
            for row in range(cls.rows):
                if state.board[row][col] == cls.empty:
                    seen_empty = True
                elif seen_empty:
                    return False, "Discs cannot float above an empty square"

        return True, None

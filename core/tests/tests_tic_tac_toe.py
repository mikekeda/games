from django.test import SimpleTestCase

from core.games.base import GameState, InvalidMove, Move
from core.games.tic_tac_toe import TicTacToe


def state(rows, turn=0):
    """Build a state from three strings, e.g. "XOX"."""
    return GameState(board=[list(row) for row in rows], turn=turn)


class TicTacToeTest(SimpleTestCase):
    def test_opening_position(self):
        opening = TicTacToe.initial_state()

        self.assertEqual(opening.board, [["*"] * 3] * 3)
        self.assertEqual(opening.turn, 0)
        self.assertEqual(len(list(TicTacToe.legal_moves(opening))), 9)

    def test_row_wins(self):
        outcome = TicTacToe.outcome(state(["XXX", "OO*", "***"]))
        self.assertEqual(outcome.winner, 0)
        self.assertEqual(outcome.cells, ((0, 0), (0, 1), (0, 2)))

    def test_column_wins(self):
        outcome = TicTacToe.outcome(state(["OX*", "OX*", "*X*"]))
        self.assertEqual(outcome.winner, 0)

    def test_leading_diagonal_wins(self):
        outcome = TicTacToe.outcome(state(["O**", "*O*", "X*O"]))
        self.assertEqual(outcome.winner, 1)
        self.assertEqual(outcome.cells, ((0, 0), (1, 1), (2, 2)))

    def test_anti_diagonal_wins(self):
        outcome = TicTacToe.outcome(state(["**X", "*X*", "X**"]))
        self.assertEqual(outcome.winner, 0)

    def test_full_board_is_a_draw(self):
        outcome = TicTacToe.outcome(state(["XOX", "XOO", "OXX"]))
        self.assertTrue(outcome.is_draw)
        self.assertEqual(outcome.reason, "board full")

    def test_unfinished_game_has_no_outcome(self):
        self.assertIsNone(TicTacToe.outcome(state(["XO*", "***", "***"])))

    def test_playing_a_move(self):
        after = TicTacToe.apply(TicTacToe.initial_state(), 0, Move(1, 1))

        self.assertEqual(after.board[1][1], "X")
        self.assertEqual(after.turn, 1)

    def test_cannot_move_after_the_game_is_won(self):
        won = state(["XXX", "OO*", "***"], turn=1)
        with self.assertRaises(InvalidMove):
            TicTacToe.apply(won, 1, Move(1, 2))

    def test_render_maps_tokens_to_glyphs(self):
        rendered = TicTacToe.render(state(["XO*", "***", "***"]))
        self.assertEqual(rendered[0], ["\u2715", "\u25ef", ""])

    def test_metadata_used_by_the_ui(self):
        self.assertEqual(TicTacToe.slug, "TicTacToe")
        self.assertFalse(TicTacToe.flip_board)
        self.assertEqual(TicTacToe.player_count, 2)

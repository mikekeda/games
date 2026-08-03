from django.test import SimpleTestCase

from core.games.base import GameState, InvalidMove, Move
from core.games.connect_four import ConnectFour


def state(rows, turn=0):
    """Build a state from bottom row first, e.g. ["XO*****", ...]."""
    return GameState(board=[list(row) for row in rows], turn=turn)


EMPTY_ROW = "*" * 7


def board(*bottom_rows):
    """Pad the given rows out to a full six-row board."""
    rows = list(bottom_rows)
    rows += [EMPTY_ROW] * (6 - len(rows))
    return rows


class ConnectFourTest(SimpleTestCase):
    def test_opening_position(self):
        opening = ConnectFour.initial_state()

        self.assertEqual(len(opening.board), 6)
        self.assertEqual(len(opening.board[0]), 7)
        self.assertTrue(ConnectFour.flip_board)

    def test_only_the_lowest_empty_square_per_column_is_legal(self):
        position = state(board("X******", "*******"))
        targets = sorted(move.target for move in ConnectFour.legal_moves(position))

        self.assertEqual(
            targets, [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 0)]
        )

    def test_full_column_offers_no_move(self):
        column = ["X******" if row % 2 == 0 else "O******" for row in range(6)]
        targets = [move.target for move in ConnectFour.legal_moves(state(column))]

        self.assertNotIn(0, [col for _, col in targets])

    def test_horizontal_win(self):
        outcome = ConnectFour.outcome(state(board("XXXX***", "OOO****")))
        self.assertEqual(outcome.winner, 0)

    def test_vertical_win(self):
        outcome = ConnectFour.outcome(
            state(board("O******", "O******", "O******", "O******"))
        )
        self.assertEqual(outcome.winner, 1)

    def test_diagonal_win(self):
        outcome = ConnectFour.outcome(
            state(
                board(
                    "XOOO***",
                    "*XOO***",
                    "**XO***",
                    "***X***",
                )
            )
        )
        self.assertEqual(outcome.winner, 0)

    def test_anti_diagonal_win(self):
        outcome = ConnectFour.outcome(
            state(
                board(
                    "***X***",
                    "**XO***",
                    "*XOO***",
                    "XOOO***",
                )
            )
        )
        self.assertEqual(outcome.winner, 0)

    def test_three_in_a_row_is_not_a_win(self):
        self.assertIsNone(ConnectFour.outcome(state(board("XXX****"))))

    def test_playing_drops_to_the_bottom(self):
        after = ConnectFour.apply(ConnectFour.initial_state(), 0, Move(0, 3))

        self.assertEqual(after.board[0][3], "X")
        self.assertEqual(after.board[1][3], "*")
        self.assertEqual(after.turn, 1)

    def test_cannot_place_a_floating_disc(self):
        with self.assertRaises(InvalidMove):
            ConnectFour.apply(ConnectFour.initial_state(), 0, Move(3, 3))

    def test_validate_rejects_floating_discs(self):
        valid, error = ConnectFour.validate(state(board("*******", "X******")))

        self.assertFalse(valid)
        self.assertIn("float", error)

    def test_validate_accepts_a_stacked_column(self):
        valid, error = ConnectFour.validate(state(board("X******", "O******")))

        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_render_maps_tokens_to_discs(self):
        rendered = ConnectFour.render(state(board("XO*****")))
        self.assertEqual(rendered[0][:3], ["\U0001f535", "\U0001f534", ""])

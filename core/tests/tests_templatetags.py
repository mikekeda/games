from django.test import SimpleTestCase

from core.templatetags.core_tags import board_rows


class BoardRowsTest(SimpleTestCase):
    def test_pairs_cells_with_their_coordinates(self):
        self.assertEqual(
            board_rows([["a", "b"], ["c", "d"]]),
            [
                (0, [(0, "a"), (1, "b")]),
                (1, [(0, "c"), (1, "d")]),
            ],
        )

    def test_flip_reverses_rows_but_keeps_their_indexes(self):
        self.assertEqual(
            board_rows([["a", "b"], ["c", "d"]], flip=True),
            [
                (1, [(0, "c"), (1, "d")]),
                (0, [(0, "a"), (1, "b")]),
            ],
        )

    def test_empty_board(self):
        self.assertEqual(board_rows([]), [])

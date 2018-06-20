from django.test import TestCase

from .games import TicTacToe


class GamesGameTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_is_board_valid(self):
        self.assertTupleEqual(TicTacToe.is_board_valid([
            ['*', '*', '*'],
            ['*', '*', '*'],
            ['*', '*', '*'],
        ]), (True, None))

        self.assertTupleEqual(TicTacToe.is_board_valid([
            ['*', 'X', '*'],
            ['O', '*', '*'],
            ['*', '*', '*'],
        ]), (True, None))

        self.assertTupleEqual(TicTacToe.is_board_valid([
            ['*', 'X', 'O'],
            ['O', 'X', '*'],
            ['*', 'X', '*'],
        ]), (True, None))

        self.assertFalse(TicTacToe.is_board_valid([
            ['*', 'X', '*'],
            ['O', 'D', '*'],
            ['*', '*', '*'],
        ])[0])

        self.assertFalse(TicTacToe.is_board_valid([
            ['*', 'X', '*'],
            ['O', 'X', 'X'],
            ['*', '*', '*'],
        ])[0])

    def test_is_valid_move(self):
        self.assertTrue(TicTacToe.is_valid_move([
            ['*', '*', '*'],
            ['*', '*', '*'],
            ['*', '*', '*'],
        ], 0, 0, 0))

        self.assertFalse(TicTacToe.is_valid_move([
            ['*', '*', '*'],
            ['*', '*', '*'],
            ['*', '*', '*'],
        ], 1, 0, 0))

        self.assertFalse(TicTacToe.is_valid_move([
            ['*', '*', '*'],
            ['*', '*', '*'],
            ['*', '*', '*'],
        ], 0, 3, 1))

        self.assertFalse(TicTacToe.is_valid_move([
            ['*', '*', '*'],
            ['*', '*', '*'],
            ['*', 'X', '*'],
        ], 1, 2, 1))

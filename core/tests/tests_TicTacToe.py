from django.test import TestCase

from core.games.TicTacToe import TicTacToe


class TicTacToeTest(TestCase):
    def test_is_board_valid(self):
        self.assertTupleEqual(
            TicTacToe.is_board_valid(
                [
                    ["*", "*", "*"],
                    ["*", "*", "*"],
                    ["*", "*", "*"],
                ]
            ),
            (True, None),
        )

        self.assertTupleEqual(
            TicTacToe.is_board_valid(
                [
                    ["*", "X", "*"],
                    ["O", "*", "*"],
                    ["*", "*", "*"],
                ]
            ),
            (True, None),
        )

        self.assertTupleEqual(
            TicTacToe.is_board_valid(
                [
                    ["*", "X", "O"],
                    ["O", "X", "*"],
                    ["*", "X", "*"],
                ]
            ),
            (True, None),
        )

        self.assertFalse(
            TicTacToe.is_board_valid(
                [
                    ["*", "X", "*"],
                    ["O", "D", "*"],
                    ["*", "*", "*"],
                ]
            )[0]
        )

        self.assertFalse(
            TicTacToe.is_board_valid(
                [
                    ["*", "X", "*"],
                    ["O", "X", "X"],
                    ["*", "*", "*"],
                ]
            )[0]
        )

    def test_is_valid_move(self):
        self.assertTrue(
            TicTacToe.is_valid_move(
                [
                    ["*", "*", "*"],
                    ["*", "*", "*"],
                    ["*", "*", "*"],
                ],
                0,
                0,
                0,
            )
        )

        self.assertFalse(
            TicTacToe.is_valid_move(
                [
                    ["*", "*", "*"],
                    ["*", "*", "*"],
                    ["*", "*", "*"],
                ],
                1,
                0,
                0,
            )
        )

        self.assertFalse(
            TicTacToe.is_valid_move(
                [
                    ["*", "*", "*"],
                    ["*", "*", "*"],
                    ["*", "*", "*"],
                ],
                0,
                3,
                1,
            )
        )

        self.assertFalse(
            TicTacToe.is_valid_move(
                [
                    ["*", "*", "*"],
                    ["*", "*", "*"],
                    ["*", "X", "*"],
                ],
                1,
                2,
                1,
            )
        )

    def test_who_is_winner(self):
        self.assertIsNone(
            TicTacToe.who_is_winner(
                [
                    ["*", "*", "*"],
                    ["*", "*", "*"],
                    ["*", "*", "*"],
                ]
            )
        )

        self.assertIsNone(
            TicTacToe.who_is_winner(
                [
                    ["X", "*", "O"],
                    ["*", "O", "*"],
                    ["X", "*", "*"],
                ]
            )
        )

        self.assertEqual(
            TicTacToe.who_is_winner(
                [
                    ["*", "*", "O"],
                    ["*", "O", "*"],
                    ["X", "X", "X"],
                ]
            ),
            0,
        )

        self.assertEqual(
            TicTacToe.who_is_winner(
                [
                    ["X", "*", "O"],
                    ["X", "O", "*"],
                    ["X", "*", "*"],
                ]
            ),
            0,
        )

        self.assertEqual(
            TicTacToe.who_is_winner(
                [
                    ["X", "X", "O"],
                    ["*", "O", "*"],
                    ["O", "X", "X"],
                ]
            ),
            1,
        )

        self.assertEqual(
            TicTacToe.who_is_winner(
                [
                    ["O", "X", "X"],
                    ["*", "O", "*"],
                    ["X", "X", "O"],
                ]
            ),
            1,
        )

        self.assertEqual(
            TicTacToe.who_is_winner(
                [
                    ["X", "X", "O"],
                    ["O", "O", "X"],
                    ["X", "X", "O"],
                ]
            ),
            -1,
        )

    def test_who_is_going_to_move(self):
        self.assertEqual(
            TicTacToe.who_is_going_to_move(
                [
                    ["*", "*", "*"],
                    ["*", "*", "*"],
                    ["*", "*", "*"],
                ]
            ),
            0,
        )

        self.assertEqual(
            TicTacToe.who_is_going_to_move(
                [
                    ["*", "*", "*"],
                    ["*", "X", "*"],
                    ["*", "*", "*"],
                ]
            ),
            1,
        )

    def test_move(self):
        self.assertListEqual(
            TicTacToe.move(
                [
                    ["*", "*", "*"],
                    ["*", "*", "*"],
                    ["*", "*", "*"],
                ],
                0,
                1,
                1,
            ),
            [
                ["*", "*", "*"],
                ["*", "X", "*"],
                ["*", "*", "*"],
            ],
        )

        self.assertListEqual(
            TicTacToe.move(
                [
                    ["*", "*", "O"],
                    ["*", "X", "*"],
                    ["*", "*", "*"],
                ],
                1,
                0,
                0,
            ),
            [
                ["*", "*", "O"],
                ["*", "X", "*"],
                ["*", "*", "*"],
            ],
        )

        self.assertListEqual(
            TicTacToe.move(
                [
                    ["*", "*", "*"],
                    ["*", "X", "*"],
                    ["*", "*", "*"],
                ],
                0,
                1,
                1,
            ),
            [
                ["*", "*", "*"],
                ["*", "X", "*"],
                ["*", "*", "*"],
            ],
        )

    def test_available_moves(self):
        self.assertSetEqual(
            set(
                TicTacToe.available_moves(
                    [
                        ["*", "O", "*"],
                        ["X", "X", "O"],
                        ["*", "*", "*"],
                    ]
                )
            ),
            {(0, 0), (0, 2), (2, 0), (2, 1), (2, 2)},
        )

    def test_render_board(self):
        self.assertListEqual(
            TicTacToe.render_board(
                [
                    ["*", "O", "*"],
                    ["X", "X", "O"],
                    ["*", "*", "*"],
                ]
            ),
            [
                ["", "◯", ""],
                ["✕", "✕", "◯"],
                ["", "", ""],
            ],
        )

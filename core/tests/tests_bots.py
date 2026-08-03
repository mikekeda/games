from django.test import SimpleTestCase

from core.games.base import GameState, Move
from core.games.bots import RandomBot
from core.games.connect_four import ConnectFour
from core.games.tic_tac_toe import TicTacToe


def ttt(rows, turn=0):
    return GameState(board=[list(row) for row in rows], turn=turn)


def c4(rows, turn=0):
    padded = list(rows) + ["*" * 7] * (6 - len(rows))
    return GameState(board=[list(row) for row in padded], turn=turn)


class RandomBotTest(SimpleTestCase):
    def test_plays_a_legal_move(self):
        state = TicTacToe.initial_state()
        move = RandomBot.choose(TicTacToe, state, 0)

        self.assertTrue(TicTacToe.is_legal(state, 0, move))

    def test_returns_nothing_when_the_game_is_over(self):
        state = ttt(["XXX", "OO*", "***"], turn=1)
        self.assertIsNone(RandomBot.choose(TicTacToe, state, 1))


class TicTacToeBotTest(SimpleTestCase):
    """The old bot just took the first empty square."""

    def test_takes_an_immediate_win(self):
        state = ttt(["XX*", "OO*", "***"], turn=0)
        move = TicTacToe.bot.choose(TicTacToe, state, 0)

        self.assertEqual(move, Move(0, 2))

    def test_blocks_an_immediate_threat(self):
        state = ttt(["OO*", "X**", "X**"], turn=1)
        move = TicTacToe.bot.choose(TicTacToe, state, 1)

        self.assertEqual(move, Move(0, 2))

    def test_perfect_play_always_draws(self):
        for _ in range(5):
            state = TicTacToe.initial_state()
            while TicTacToe.outcome(state) is None:
                move = TicTacToe.bot.choose(TicTacToe, state, state.turn)
                state = TicTacToe.apply(state, state.turn, move)

            self.assertTrue(TicTacToe.outcome(state).is_draw)


class ConnectFourBotTest(SimpleTestCase):
    """The old ConnectFour bot was a no-op, which deadlocked every bot game."""

    def test_actually_returns_a_move(self):
        state = ConnectFour.initial_state()
        move = ConnectFour.bot.choose(ConnectFour, state, 0)

        self.assertIsNotNone(move)
        self.assertTrue(ConnectFour.is_legal(state, 0, move))

    def test_takes_an_immediate_win(self):
        state = c4(["XXX*OOO"], turn=0)
        move = ConnectFour.bot.choose(ConnectFour, state, 0)

        self.assertEqual(move, Move(0, 3))

    def test_blocks_an_immediate_threat(self):
        state = c4(["XXX****", "O*O****"], turn=1)
        move = ConnectFour.bot.choose(ConnectFour, state, 1)

        self.assertEqual(move, Move(0, 3))

    def test_a_full_bot_game_terminates(self):
        state = ConnectFour.initial_state()
        for _ in range(ConnectFour.rows * ConnectFour.cols):
            if ConnectFour.outcome(state) is not None:
                break
            move = ConnectFour.bot.choose(ConnectFour, state, state.turn)
            self.assertIsNotNone(move)
            state = ConnectFour.apply(state, state.turn, move)

        self.assertIsNotNone(ConnectFour.outcome(state))

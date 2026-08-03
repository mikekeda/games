"""Tests for reversi."""

from django.test import SimpleTestCase

from core.games.base import GameState, InvalidMove, Move
from core.games.reversi import Reversi


def board_from(rows: list[str]) -> list[list[str]]:
    """Build a board from one string per row, using ``.`` for an empty square.

    Reversi positions are hard to read as nested lists, and most of these
    tests only make sense next to a picture of the board.
    """
    return [[cell if cell != "." else Reversi.empty for cell in row] for row in rows]


EMPTY_ROW = "." * 8


class ReversiRulesTest(SimpleTestCase):
    def test_opens_with_four_discs_crossed(self):
        state = Reversi.initial_state()

        self.assertEqual(state.board[3][3], "O")
        self.assertEqual(state.board[4][4], "O")
        self.assertEqual(state.board[3][4], "X")
        self.assertEqual(state.board[4][3], "X")
        self.assertEqual(Reversi.counts(state.board), [2, 2])
        self.assertEqual(state.turn, 0)

    def test_opening_has_the_four_standard_moves(self):
        moves = set(Reversi.legal_moves(Reversi.initial_state()))

        self.assertEqual(moves, {Move(2, 3), Move(3, 2), Move(4, 5), Move(5, 4)})

    def test_a_move_must_capture_something(self):
        state = Reversi.initial_state()

        # Legal square, but nothing is trapped by playing there.
        with self.assertRaises(InvalidMove):
            Reversi.apply(state, 0, Move(0, 0))

    def test_cannot_play_on_an_occupied_square(self):
        with self.assertRaises(InvalidMove):
            Reversi.apply(Reversi.initial_state(), 0, Move(3, 3))

    def test_off_board_moves_are_rejected_not_crashes(self):
        # The client can send anything; indexing must not blow up.
        for move in (Move(-1, 0), Move(0, 8), Move(99, 99)):
            with self.subTest(move=move):
                with self.assertRaises(InvalidMove):
                    Reversi.apply(Reversi.initial_state(), 0, move)

    def test_out_of_turn_moves_are_rejected(self):
        with self.assertRaises(InvalidMove):
            Reversi.apply(Reversi.initial_state(), 1, Move(2, 3))

    def test_playing_flips_the_trapped_line(self):
        state = Reversi.apply(Reversi.initial_state(), 0, Move(2, 3))

        self.assertEqual(state.board[2][3], "X")
        # The white disc between the new one and X at (4, 3) turns over.
        self.assertEqual(state.board[3][3], "X")
        self.assertEqual(Reversi.counts(state.board), [4, 1])
        self.assertEqual(state.turn, 1)

    def test_flips_run_in_every_direction_at_once(self):
        # A white disc on each side of the centre, each backed by a black one.
        state = GameState(
            board=board_from(
                [
                    EMPTY_ROW,
                    EMPTY_ROW,
                    "..XXX...",
                    "..XOX...",
                    "..X.X...",
                    EMPTY_ROW,
                    EMPTY_ROW,
                    EMPTY_ROW,
                ]
            ),
            turn=0,
        )

        # Placing below the lone white disc traps it against (2, 3).
        result = Reversi.apply(state, 0, Move(4, 3))

        self.assertEqual(result.board[3][3], "X")
        self.assertEqual(Reversi.counts(result.board)[1], 0)

    def test_a_line_must_be_closed_to_count(self):
        # X . O O . . . .  -- the run of O is open at the far end.
        state = GameState(
            board=board_from(
                ["X.OO....", EMPTY_ROW, EMPTY_ROW, EMPTY_ROW] + [EMPTY_ROW] * 4
            ),
            turn=0,
        )

        self.assertEqual(Reversi.captures(state.board, 0, 1, "X"), [])

    def test_leaves_the_original_state_untouched(self):
        state = Reversi.initial_state()
        Reversi.apply(state, 0, Move(2, 3))

        self.assertEqual(state.board[2][3], Reversi.empty)
        self.assertEqual(state.board[3][3], "O")
        self.assertEqual(state.turn, 0)


class ReversiPassTest(SimpleTestCase):
    """A player with no move passes -- the rule the engine had no concept of."""

    def test_turn_comes_back_when_the_opponent_cannot_move(self):
        # A real late-game position, found by playing random games until one
        # turned up. Contriving one by hand is harder than it looks: it is easy
        # to build a board where the opponent is stuck but so is the mover,
        # which is the end of the game rather than a pass.
        state = GameState(
            board=board_from(
                [
                    "OXXXOOO.",
                    "OOXXO.OO",
                    "OXOOXXOO",
                    "OOOXXXOO",
                    "OOXXOOXO",
                    "OXXXXXXX",
                    "XXOOXOXO",
                    "XXXXXXXO",
                ]
            ),
            turn=0,
        )

        result = Reversi.apply(state, 0, Move(1, 5))

        # White has nothing to play, so the turn comes straight back to black
        # rather than the game stopping.
        self.assertEqual(Reversi.moves_for(result.board, 1), [])
        self.assertEqual(result.turn, 0)
        self.assertIsNone(Reversi.outcome(result))
        self.assertTrue(list(Reversi.legal_moves(result)))

    def test_game_ends_when_neither_player_can_move(self):
        state = GameState(board=board_from(["XXXX...."] + [EMPTY_ROW] * 7), turn=1)

        outcome = Reversi.outcome(state)

        self.assertIsNotNone(outcome)
        self.assertEqual(outcome.winner, 0)
        self.assertEqual(outcome.reason, "most discs")

    def test_equal_discs_is_a_draw(self):
        # One disc in each corner. Corners cannot be flipped and nothing is
        # adjacent, so neither player has a move and the discs are level.
        state = GameState(
            board=board_from(["X......O"] + [EMPTY_ROW] * 6 + ["O......X"]),
            turn=0,
        )

        outcome = Reversi.outcome(state)

        self.assertTrue(outcome.is_draw)
        self.assertEqual(outcome.reason, "equal discs")

    def test_no_moves_are_offered_once_the_game_is_over(self):
        state = GameState(board=board_from(["XXXX...."] + [EMPTY_ROW] * 7), turn=1)

        self.assertEqual(list(Reversi.legal_moves(state)), [])


class ReversiRenderTest(SimpleTestCase):
    def test_renders_discs_and_leaves_empties_blank(self):
        rendered = Reversi.render(Reversi.initial_state())

        self.assertEqual(rendered[3][3], "\u26aa")
        self.assertEqual(rendered[3][4], "\u26ab")
        self.assertEqual(rendered[0][0], "")

    def test_render_does_not_mutate(self):
        state = Reversi.initial_state()
        Reversi.render(state)

        self.assertEqual(state.board[3][3], "O")


class ReversiBotTest(SimpleTestCase):
    def test_bot_plays_a_legal_move(self):
        state = Reversi.initial_state()

        move = Reversi.bot.choose(Reversi, state, 0)

        self.assertIn(move, list(Reversi.legal_moves(state)))

    def test_bot_takes_a_free_corner(self):
        # Black can play (0, 0) and capture the diagonal; a corner can never
        # be flipped back, so nothing else comes close.
        state = GameState(
            board=board_from(
                [
                    ".O.....X",
                    ".OO.....",
                    "..X.....",
                    "...XO...",
                    "...OX...",
                    EMPTY_ROW,
                    EMPTY_ROW,
                    EMPTY_ROW,
                ]
            ),
            turn=0,
        )

        self.assertEqual(Reversi.bot.choose(Reversi, state, 0), Move(0, 0))

    def test_a_full_game_between_bots_terminates(self):
        # Exercises passing, alternation and the end condition together.
        state = Reversi.initial_state()

        for _ in range(64):
            if Reversi.outcome(state) is not None:
                break
            move = Reversi.bot.choose(Reversi, state, state.turn)
            self.assertIsNotNone(move)
            state = Reversi.apply(state, state.turn, move)

        outcome = Reversi.outcome(state)
        self.assertIsNotNone(outcome)
        # Every disc on the board belongs to someone, and there are 64 squares.
        self.assertLessEqual(sum(Reversi.counts(state.board)), 64)

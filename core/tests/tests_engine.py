"""Tests for the shared engine: moves, registry and the grid bases."""

from django.test import SimpleTestCase

from core.games import all_games, game_choices, get_game, register
from core.games.base import (
    GameState,
    GridGame,
    InvalidMove,
    LineUpGame,
    Move,
    MoveStyle,
    Outcome,
)
from core.games.bots import NegamaxBot


class MoveTest(SimpleTestCase):
    def test_parses_structured_placement(self):
        move = Move.parse({"to": [1, 2]})
        self.assertEqual(move, Move(1, 2))
        self.assertFalse(move.is_relocation)

    def test_parses_structured_relocation(self):
        move = Move.parse({"from": [1, 4], "to": [3, 4], "promotion": "Q"})
        self.assertEqual(move.origin, (1, 4))
        self.assertEqual(move.target, (3, 4))
        self.assertEqual(move.promotion, "Q")
        self.assertTrue(move.is_relocation)

    def test_parses_legacy_string(self):
        self.assertEqual(Move.parse("2-1"), Move(2, 1))

    def test_round_trips_through_serialize(self):
        for move in (Move(0, 0), Move(3, 4, 1, 4, "Q")):
            self.assertEqual(Move.parse(move.serialize()), move)

    def test_rejects_malformed_input(self):
        # These all used to crash the websocket consumer with ValueError or
        # IndexError rather than being reported to the client.
        for raw in (
            "abc",
            "1",
            "1-2-3",
            "-1-1",
            "a-b",
            {},
            {"to": [1]},
            {"to": "12"},
            {"to": [1, "x"]},
            {"to": [1, 2], "from": None, "promotion": 5},
            None,
            42,
            [1, 2],
        ):
            with self.subTest(raw=raw):
                with self.assertRaises(InvalidMove):
                    Move.parse(raw)


class RegistryTest(SimpleTestCase):
    def test_finds_the_shipped_games(self):
        slugs = {game.slug for game in all_games()}
        self.assertIn("TicTacToe", slugs)
        self.assertIn("ConnectFour", slugs)

    def test_unknown_slug_returns_none(self):
        self.assertIsNone(get_game("NoSuchGame"))

    def test_choices_are_a_reusable_sequence(self):
        # The old GAMES was a generator and was empty on any second read.
        choices = game_choices()
        self.assertEqual(list(choices), list(choices))
        self.assertIn(("TicTacToe", "Tic-tac-toe"), choices)

    def test_rejects_a_game_without_a_slug(self):
        class Nameless(LineUpGame):
            pass

        with self.assertRaises(ValueError):
            register(Nameless)

    def test_rejects_a_duplicate_slug(self):
        class Clash(LineUpGame):
            slug = "TicTacToe"

        with self.assertRaises(ValueError):
            register(Clash)


class TinyGame(LineUpGame):
    """A 2x2 board needing two in a row. Small enough to reason about."""

    slug = "TinyGame"
    title = "Tiny"
    rows = 2
    cols = 2
    need_in_line = 2
    tokens = ("X", "O")
    render_map = {"*": ".", "X": "x", "O": "o"}


class GridGameTest(SimpleTestCase):
    def test_initial_board_rows_are_independent(self):
        # The old board was `[[empty] * cols] * rows`, which aliased one row
        # object across the board, and deepcopy preserved the aliasing.
        state = TinyGame.initial_state()
        self.assertIsNot(state.board[0], state.board[1])

        state.board[0][0] = "X"
        self.assertEqual(state.board[1][0], TinyGame.empty)

    def test_copy_is_deep(self):
        state = TinyGame.initial_state()
        clone = state.copy()
        clone.board[0][0] = "X"
        clone.extra["a"] = 1

        self.assertEqual(state.board[0][0], TinyGame.empty)
        self.assertEqual(state.extra, {})

    def test_render_does_not_mutate(self):
        # ConnectFour.render_board used to rewrite the board in place, leaving
        # display glyphs where tokens should be.
        state = TinyGame.initial_state()
        state.board[0][0] = "X"

        rendered = TinyGame.render(state)

        self.assertEqual(rendered[0][0], "x")
        self.assertEqual(state.board[0][0], "X")
        self.assertIsNot(rendered, state.board)

    def test_validate_rejects_unknown_values(self):
        state = GameState(board=[["Z", "*"], ["*", "*"]])
        valid, error = TinyGame.validate(state)
        self.assertFalse(valid)
        self.assertIn("allowed", error)

    def test_validate_rejects_wrong_shape(self):
        valid, error = TinyGame.validate(GameState(board=[["*", "*"]]))
        self.assertFalse(valid)
        self.assertIn("2x2", error)

    def test_validate_rejects_impossible_turn(self):
        state = TinyGame.initial_state()
        state.turn = 7
        valid, error = TinyGame.validate(state)
        self.assertFalse(valid)
        self.assertEqual(error, "Invalid turn")

    def test_find_line_reports_the_winning_squares(self):
        state = TinyGame.initial_state()
        state.board = [["X", "X"], ["*", "*"]]

        token, cells = TinyGame.find_line(state.board, 2)

        self.assertEqual(token, "X")
        self.assertEqual(cells, ((0, 0), (0, 1)))


class TurnOrderTest(SimpleTestCase):
    """Turn order is now checked explicitly instead of being inferred."""

    def test_second_player_cannot_open(self):
        state = TinyGame.initial_state()
        self.assertFalse(TinyGame.is_legal(state, 1, Move(0, 0)))
        self.assertTrue(TinyGame.is_legal(state, 0, Move(0, 0)))

    def test_apply_advances_the_turn(self):
        state = TinyGame.apply(TinyGame.initial_state(), 0, Move(0, 0))
        self.assertEqual(state.turn, 1)

    def test_apply_refuses_an_out_of_turn_move(self):
        with self.assertRaises(InvalidMove):
            TinyGame.apply(TinyGame.initial_state(), 1, Move(0, 0))

    def test_apply_refuses_an_occupied_square(self):
        state = TinyGame.apply(TinyGame.initial_state(), 0, Move(0, 0))
        with self.assertRaises(InvalidMove):
            TinyGame.apply(state, 1, Move(0, 0))

    def test_apply_refuses_an_off_board_square(self):
        with self.assertRaises(InvalidMove):
            TinyGame.apply(TinyGame.initial_state(), 0, Move(9, 9))

    def test_apply_leaves_the_original_state_untouched(self):
        state = TinyGame.initial_state()
        TinyGame.apply(state, 0, Move(0, 0))

        self.assertEqual(state.board[0][0], TinyGame.empty)
        self.assertEqual(state.turn, 0)


class OutcomeTest(SimpleTestCase):
    def test_running_game_has_no_outcome(self):
        self.assertIsNone(TinyGame.outcome(TinyGame.initial_state()))

    def test_line_wins(self):
        state = GameState(board=[["X", "X"], ["*", "*"]])
        outcome = TinyGame.outcome(state)

        self.assertEqual(outcome.winner, 0)
        self.assertEqual(outcome.reason, "line")
        self.assertFalse(outcome.is_draw)

    def test_full_board_without_a_line_is_a_draw(self):
        # Unwinnable needs a board too small to ever hold a line, so a full
        # board is unambiguously a draw.
        class Unwinnable(TinyGame):
            slug = "Unwinnable"
            need_in_line = 3

        outcome = Unwinnable.outcome(GameState(board=[["X", "O"], ["O", "X"]]))

        self.assertTrue(outcome.is_draw)
        self.assertIsNone(outcome.winner)
        self.assertEqual(outcome.reason, "board full")

    def test_no_moves_are_offered_once_the_game_is_over(self):
        state = GameState(board=[["X", "X"], ["*", "*"]], turn=1)
        self.assertEqual(list(TinyGame.legal_moves(state)), [])


class Hunt(GridGame):
    """A minimal travelling-piece game: catch the opponent's piece to win.

    Deliberately not registered -- it is not a game anyone would want to play.
    It exists so the suite exercises the things a game like chess needs and
    that neither shipped game does: pieces that move from one square to
    another, a win condition that is not a line of tokens, and a rule carried
    in ``extra`` rather than on the board.
    """

    slug = "Hunt"
    title = "Hunt"
    rows = 3
    cols = 3
    tokens = ("A", "B")
    move_style = MoveStyle.SELECT

    #: Nobody caught by this many plies is a draw, which also bounds the game.
    ply_limit = 12

    @classmethod
    def initial_state(cls):
        board = cls.initial_board()
        board[0][0] = "A"
        board[2][2] = "B"
        return GameState(board=board, turn=0, extra={"plies": 0})

    @classmethod
    def square_of(cls, board, token):
        """Where ``token`` stands, or ``None`` once it has been captured."""
        return next((rc for rc in cls.cells() if board[rc[0]][rc[1]] == token), None)

    @classmethod
    def legal_moves(cls, state):
        if cls.outcome(state) is not None:
            return

        origin = cls.square_of(state.board, cls.tokens[state.turn])
        if origin is None:
            return

        row, col = origin
        for delta_row in (-1, 0, 1):
            for delta_col in (-1, 0, 1):
                if (delta_row, delta_col) == (0, 0):
                    continue
                if cls.in_bounds(row + delta_row, col + delta_col):
                    yield Move(row + delta_row, col + delta_col, row, col)

    @classmethod
    def apply(cls, state, player, move):
        if not cls.is_legal(state, player, move):
            raise InvalidMove(f"{move} is not legal in this position")

        new_state = state.copy()
        new_state.board[move.from_row][move.from_col] = cls.empty
        new_state.board[move.to_row][move.to_col] = cls.tokens[player]
        new_state.extra["plies"] = new_state.extra.get("plies", 0) + 1
        new_state.turn = cls.next_turn(state, player)
        return new_state

    @classmethod
    def outcome(cls, state):
        for player, token in enumerate(cls.tokens):
            if cls.square_of(state.board, token) is None:
                return Outcome(winner=cls.next_turn(state, player), reason="captured")

        if state.extra.get("plies", 0) >= cls.ply_limit:
            return Outcome(winner=None, reason="ply limit")

        return None


class RelocationGameTest(SimpleTestCase):
    """The engine must support pieces that travel, not just tokens dropped on a square."""

    def test_opening_moves_all_carry_an_origin(self):
        moves = list(Hunt.legal_moves(Hunt.initial_state()))

        # The piece on a corner of a 3x3 board has three neighbours.
        self.assertEqual(len(moves), 3)
        for move in moves:
            self.assertTrue(move.is_relocation)
            self.assertEqual(move.origin, (0, 0))

    def test_applying_a_move_empties_the_origin(self):
        state = Hunt.apply(Hunt.initial_state(), 0, Move(0, 1, 0, 0))

        self.assertEqual(state.board[0][0], Hunt.empty)
        self.assertEqual(state.board[0][1], "A")

    def test_a_move_cannot_start_from_the_opponents_piece(self):
        with self.assertRaises(InvalidMove):
            Hunt.apply(Hunt.initial_state(), 0, Move(1, 1, 2, 2))

    def test_capturing_wins(self):
        state = GameState(board=[["A", "B", "*"], ["*"] * 3, ["*"] * 3], turn=0)

        outcome = Hunt.outcome(Hunt.apply(state, 0, Move(0, 1, 0, 0)))

        self.assertEqual(outcome.winner, 0)
        self.assertEqual(outcome.reason, "captured")

    def test_extra_carries_state_the_board_cannot(self):
        state = Hunt.initial_state()
        self.assertEqual(state.extra["plies"], 0)

        state = Hunt.apply(state, 0, Move(0, 1, 0, 0))

        self.assertEqual(state.extra["plies"], 1)

    def test_a_rule_held_in_extra_can_end_the_game(self):
        state = Hunt.initial_state()
        state.extra["plies"] = Hunt.ply_limit

        outcome = Hunt.outcome(state)

        self.assertTrue(outcome.is_draw)
        self.assertEqual(outcome.reason, "ply limit")
        self.assertEqual(list(Hunt.legal_moves(state)), [])

    def test_the_generic_bot_can_play_it_to_a_finish(self):
        # A bot written for placement games has to drive a relocation game too,
        # purely through the Game interface.
        class HuntBot(NegamaxBot):
            max_depth = 3

        state = Hunt.initial_state()
        while Hunt.outcome(state) is None:
            move = HuntBot.choose(Hunt, state, state.turn)
            self.assertIsNotNone(move)
            state = Hunt.apply(state, state.turn, move)

        self.assertIsNotNone(Hunt.outcome(state))

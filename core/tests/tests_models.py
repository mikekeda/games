from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from core.games.base import InvalidMove, Move
from core.models import Game, GameMove, GamePlayers

User = get_user_model()

IN_MEMORY_LAYER = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
}


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYER)
class GameModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username="alice", password="pw")
        cls.bob = User.objects.create_user(username="bob", password="pw")
        cls.bot = User.objects.create_user(username="bot", password="pw")

    def make_game(self, slug="TicTacToe", opponent=None):
        game = Game(game=slug)
        game.save()
        GamePlayers(game=game, user=self.alice, order=0).save()
        GamePlayers(game=game, user=opponent or self.bob, order=1).save()
        return game

    def test_new_game_starts_from_the_opening_position(self):
        game = self.make_game()

        self.assertEqual(game.board, [["*"] * 3] * 3)
        self.assertEqual(game.current_turn, 0)
        self.assertIsNone(game.completed)
        self.assertIsNone(game.winner)

    def test_boards_of_separate_games_do_not_share_rows(self):
        first = self.make_game()
        second = self.make_game()

        first.play(0, Move(0, 0))
        second.refresh_from_db()

        self.assertEqual(second.board, [["*"] * 3] * 3)

    def test_play_advances_the_turn_and_records_history(self):
        game = self.make_game()
        game.play(0, Move(1, 1))

        game.refresh_from_db()
        self.assertEqual(game.board[1][1], "X")
        self.assertEqual(game.current_turn, 1)
        self.assertEqual(
            list(game.moves.values_list("player", "move")),
            [(0, {"to": [1, 1]})],
        )

    def test_play_refuses_a_move_out_of_turn(self):
        game = self.make_game()

        with self.assertRaises(InvalidMove):
            game.play(1, Move(0, 0))

        game.refresh_from_db()
        self.assertEqual(game.board, [["*"] * 3] * 3)
        self.assertEqual(GameMove.objects.count(), 0)

    def test_play_refuses_an_occupied_square(self):
        game = self.make_game()
        game.play(0, Move(0, 0))

        with self.assertRaises(InvalidMove):
            game.play(1, Move(0, 0))

    def test_winning_completes_the_game(self):
        game = self.make_game()
        for move in (Move(0, 0), Move(1, 0), Move(0, 1), Move(1, 1), Move(0, 2)):
            game.play(game.current_turn, move)

        game.refresh_from_db()
        self.assertEqual(game.winner, 0)
        self.assertIsNotNone(game.completed)
        self.assertEqual(list(game.rules.legal_moves(game.state)), [])

    def test_no_moves_accepted_after_the_game_is_over(self):
        game = self.make_game()
        for move in (Move(0, 0), Move(1, 0), Move(0, 1), Move(1, 1), Move(0, 2)):
            game.play(game.current_turn, move)

        with self.assertRaises(InvalidMove):
            game.play(game.current_turn, Move(2, 2))

    def test_bot_replies_immediately(self):
        game = self.make_game(opponent=self.bot)
        game.play(0, Move(1, 1))

        game.refresh_from_db()
        filled = [cell for row in game.board for cell in row if cell != "*"]

        self.assertEqual(len(filled), 2)
        self.assertEqual(game.current_turn, 0)
        self.assertEqual(game.moves.count(), 2)

    def test_connect_four_bot_replies(self):
        # This is the deadlock that made ConnectFour unplayable: the old bot
        # returned the board untouched and the turn never came back.
        game = self.make_game(slug="ConnectFour", opponent=self.bot)
        game.play(0, Move(0, 3))

        game.refresh_from_db()
        filled = [cell for row in game.board for cell in row if cell != "*"]

        self.assertEqual(len(filled), 2)
        self.assertEqual(game.current_turn, 0)

    def test_payload_describes_the_position(self):
        game = self.make_game()
        payload = game.payload()

        self.assertEqual(payload["pk"], game.pk)
        self.assertEqual(payload["turn"], 0)
        self.assertIsNone(payload["winner"])
        self.assertEqual(len(payload["moves"]), 9)
        self.assertEqual(payload["board"][0], ["", "", ""])

    def test_payload_reports_a_draw_as_minus_one(self):
        game = self.make_game()
        for move in (
            Move(0, 0),
            Move(0, 1),
            Move(0, 2),
            Move(1, 1),
            Move(1, 0),
            Move(1, 2),
            Move(2, 1),
            Move(2, 0),
            Move(2, 2),
        ):
            game.play(game.current_turn, move)

        self.assertEqual(game.payload()["winner"], -1)

    def test_broadcast_reaches_the_group(self):
        game = self.make_game()
        layer = get_channel_layer()

        async_to_sync(layer.group_add)(f"game-{game.pk}", "test-channel")
        game.play(0, Move(0, 0))

        message = async_to_sync(layer.receive)("test-channel")
        self.assertEqual(message["type"], "game.update")
        self.assertEqual(message["content"]["pk"], game.pk)

    def test_unknown_game_is_rejected(self):
        with self.assertRaises(ValueError):
            Game(game="NoSuchGame").save()

    def test_clean_rejects_an_impossible_board(self):
        game = self.make_game()
        game.board = [["Z", "*", "*"], ["*", "*", "*"], ["*", "*", "*"]]

        with self.assertRaises(ValidationError):
            game.clean()

    def test_extra_survives_a_round_trip(self):
        # Games like chess keep castling rights and the en passant target here,
        # so it has to come back out of the database unchanged.
        game = self.make_game()
        game.extra = {"castling": ["K", "q"], "en_passant": [2, 4]}
        game.save()

        game.refresh_from_db()

        self.assertEqual(game.extra, {"castling": ["K", "q"], "en_passant": [2, 4]})
        self.assertEqual(game.state.extra["en_passant"], [2, 4])

    def test_state_hands_out_a_private_copy(self):
        # board was already copied but extra was not, so a game that wrote to
        # the state it was given could silently corrupt the row in memory.
        game = self.make_game()
        game.extra = {"castling": ["K"]}

        state = game.state
        state.board[0][0] = "X"
        state.extra["castling"] = []

        self.assertEqual(game.board[0][0], "*")
        self.assertEqual(game.extra, {"castling": ["K"]})


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYER)
class GamePlayersTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username="alice", password="pw")
        cls.bob = User.objects.create_user(username="bob", password="pw")
        cls.carol = User.objects.create_user(username="carol", password="pw")

    def test_rejects_more_players_than_seats(self):
        game = Game(game="TicTacToe")
        game.save()
        GamePlayers(game=game, user=self.alice, order=0).save()
        GamePlayers(game=game, user=self.bob, order=1).save()

        with self.assertRaises(ValidationError):
            GamePlayers(game=game, user=self.carol, order=2).save()

    def test_players_come_back_in_seat_order(self):
        game = Game(game="TicTacToe")
        game.save()
        GamePlayers(game=game, user=self.bob, order=1).save()
        GamePlayers(game=game, user=self.alice, order=0).save()

        self.assertEqual(game.ordered_players(), [self.alice, self.bob])

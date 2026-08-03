"""Tests for the game websocket, which previously had no coverage at all."""

from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TransactionTestCase, override_settings

from core.consumers import WsGame
from core.models import Game, GamePlayers

User = get_user_model()

IN_MEMORY_LAYER = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
}


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYER)
class WsGameTest(TransactionTestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pw")
        self.bob = User.objects.create_user(username="bob", password="pw")
        self.game = Game(game="TicTacToe")
        self.game.save()
        GamePlayers(game=self.game, user=self.alice, order=0).save()
        GamePlayers(game=self.game, user=self.bob, order=1).save()

    def communicator(self, user):
        communicator = WebsocketCommunicator(
            WsGame.as_asgi(), f"/ws/game/{self.game.pk}"
        )
        communicator.scope["url_route"] = {"kwargs": {"game_id": str(self.game.pk)}}
        communicator.scope["user"] = user
        return communicator

    async def connect(self, user):
        communicator = self.communicator(user)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        return communicator

    async def test_sends_the_position_on_connect(self):
        communicator = await self.connect(self.alice)

        payload = await communicator.receive_json_from()
        self.assertEqual(payload["pk"], self.game.pk)
        self.assertEqual(payload["turn"], 0)
        self.assertEqual(len(payload["moves"]), 9)

        await communicator.disconnect()

    async def test_a_move_is_broadcast_to_both_players(self):
        alice = await self.connect(self.alice)
        bob = await self.connect(self.bob)
        await alice.receive_json_from()
        await bob.receive_json_from()

        await alice.send_json_to({"move": {"to": [1, 1]}})

        for communicator in (alice, bob):
            payload = await communicator.receive_json_from()
            self.assertEqual(payload["board"][1][1], "\u2715")
            self.assertEqual(payload["turn"], 1)

        await alice.disconnect()
        await bob.disconnect()

    async def test_legacy_string_move_still_works(self):
        alice = await self.connect(self.alice)
        await alice.receive_json_from()

        await alice.send_json_to({"move": "0-0"})
        payload = await alice.receive_json_from()

        self.assertEqual(payload["board"][0][0], "\u2715")
        await alice.disconnect()

    async def test_a_move_out_of_turn_is_rejected(self):
        bob = await self.connect(self.bob)
        await bob.receive_json_from()

        await bob.send_json_to({"move": {"to": [0, 0]}})
        payload = await bob.receive_json_from()

        # The authoritative position is resent, unchanged.
        self.assertEqual(payload["board"][0][0], "")
        self.assertEqual(payload["turn"], 0)

        board = await database_sync_to_async(
            lambda: Game.objects.get(pk=self.game.pk).board
        )()
        self.assertEqual(board, [["*"] * 3] * 3)

        await bob.disconnect()

    async def test_malformed_move_reports_an_error_instead_of_crashing(self):
        alice = await self.connect(self.alice)
        await alice.receive_json_from()

        for raw in ("garbage", "1-2-3", {"to": [1]}, None, 7):
            with self.subTest(raw=raw):
                await alice.send_json_to({"move": raw})
                payload = await alice.receive_json_from()
                self.assertIn("error", payload)

        self.assertTrue(await alice.receive_nothing())
        await alice.disconnect()

    async def test_payload_without_a_move_is_ignored(self):
        alice = await self.connect(self.alice)
        await alice.receive_json_from()

        await alice.send_json_to({"hello": "world"})

        self.assertTrue(await alice.receive_nothing())
        await alice.disconnect()

    async def test_a_stranger_cannot_move(self):
        mallory = await database_sync_to_async(User.objects.create_user)(
            username="mallory", password="pw"
        )
        communicator = await self.connect(mallory)

        # Not a player, so no position is pushed on connect.
        self.assertTrue(await communicator.receive_nothing())

        await communicator.send_json_to({"move": {"to": [0, 0]}})
        payload = await communicator.receive_json_from()
        self.assertIn("error", payload)

        board = await database_sync_to_async(
            lambda: Game.objects.get(pk=self.game.pk).board
        )()
        self.assertEqual(board, [["*"] * 3] * 3)

        await communicator.disconnect()

    async def test_anonymous_user_cannot_move(self):
        communicator = await self.connect(AnonymousUser())

        await communicator.send_json_to({"move": {"to": [0, 0]}})
        payload = await communicator.receive_json_from()

        self.assertIn("error", payload)
        await communicator.disconnect()

    async def test_non_numeric_game_id_closes_the_socket(self):
        communicator = WebsocketCommunicator(WsGame.as_asgi(), "/ws/game/abc")
        communicator.scope["url_route"] = {"kwargs": {"game_id": "abc"}}
        communicator.scope["user"] = self.alice

        connected, _ = await communicator.connect()

        self.assertFalse(connected)
        await communicator.disconnect()

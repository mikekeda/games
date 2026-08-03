import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer

from core.games import InvalidMove, Move
from core.models import Game

log = logging.getLogger(__name__)


class WsGame(JsonWebsocketConsumer):
    """Websocket for a single game."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_id = None
        self.group_name = None

    def connect(self):
        """Join the group for this game and send the current position."""
        try:
            self.game_id = int(self.scope["url_route"]["kwargs"]["game_id"])
        except (KeyError, TypeError, ValueError):
            self.close()
            return

        self.group_name = f"game-{self.game_id}"
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        super().connect()

        game = self.get_game()
        if game is not None:
            self.send_json(game.payload())

    def disconnect(self, code):
        """Leave the group. Channels closes the socket itself."""
        if self.group_name:
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name, self.channel_name
            )

    def get_game(self) -> Game | None:
        """The game this socket is watching, if the user is a player in it."""
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            return None

        return (
            Game.objects.filter(pk=self.game_id, players=user)
            .prefetch_related("players")
            .first()
        )

    def receive_json(self, content, **kwargs):
        if not isinstance(content, dict) or "move" not in content:
            return

        game = self.get_game()
        if game is None:
            self.send_json({"error": "You are not a player in this game."})
            return

        try:
            move = Move.parse(content["move"])
        except InvalidMove:
            self.send_json({"error": "Could not read that move."})
            return

        players = game.ordered_players()
        try:
            player = players.index(self.scope["user"])
        except ValueError:
            self.send_json({"error": "You are not a player in this game."})
            return

        try:
            game.play(player, move)
        except InvalidMove:
            # Re-send the authoritative position so a client that guessed wrong
            # snaps back into sync.
            self.send_json(game.payload())
        # Last line of defence: a bug in a game must not take the socket down.
        except Exception:  # pylint: disable=broad-exception-caught
            log.exception("Failed to play move %s in game %s", move, self.game_id)
            self.send_json({"error": "Something went wrong playing that move."})

    def game_update(self, message):
        """Fan-out handler for `game.update` group messages."""
        self.send_json(message["content"])

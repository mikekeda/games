from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from django.shortcuts import get_object_or_404

from .models import Game


class WsGame(JsonWebsocketConsumer):
    """ WebsocketConsumer related to specific game. """
    game_id = None

    def connect(self):
        """ Adds to specific 'game' group. """
        self.game_id = int(self.scope['url_route']['kwargs'].get('game_id'))

        async_to_sync(self.channel_layer.group_add)(
            'game-{}'.format(str(self.game_id)),
            self.channel_name
        )
        super().connect()

    def disconnect(self, code):
        """ Remove from specific 'game' group and close the webSocket. """
        async_to_sync(self.channel_layer.group_discard)(
            'game-{}'.format(str(self.game_id)),
            self.channel_name
        )
        self.close()

    def receive_json(self, content, **kwargs):
        if 'move' in content:
            user = self.scope.get('user')
            game = get_object_or_404(Game.objects.prefetch_related('players'),
                                     pk=self.game_id, players=user)
            players = list(game.players.all())
            player_index = players.index(user)
            move = content.get('move').split('-')
            game.board = game.rules.move(game.board, player_index,
                                         int(move[0]), int(move[1]))
            game.save()

    def game_update(self, message):
        """ Message binding. """
        self.send_json(message['content'])

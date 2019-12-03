from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from django.shortcuts import get_object_or_404

from core.models import Game


class WsGame(JsonWebsocketConsumer):
    """ WebsocketConsumer related to specific game. """
    game_id = None

    def connect(self):
        """ Adds to specific 'game' group. """
        self.game_id = int(self.scope['url_route']['kwargs'].get('game_id'))

        async_to_sync(self.channel_layer.group_add)(
            f'game-{str(self.game_id)}',
            self.channel_name
        )
        super().connect()

    def disconnect(self, code):
        """ Remove from specific 'game' group and close the webSocket. """
        async_to_sync(self.channel_layer.group_discard)(
            f'game-{str(self.game_id)}',
            self.channel_name
        )
        self.close()

    def receive_json(self, content, **kwargs):
        if 'move' in content:
            user = self.scope.get('user')
            game = get_object_or_404(Game.objects.prefetch_related('players'),
                                     pk=self.game_id, players=user)
            players = list(game.players.order_by('gameplayers__order'))
            player_index = players.index(user)
            move = content.get('move').split('-')
            game.board = game.rules.move(game.board, player_index,
                                         int(move[0]), int(move[1]))

            bot_index = None
            for i, player in enumerate(players):
                if player.username == 'bot':
                    bot_index = i
                    break

            # If bot in the game - make it move.
            if bot_index is not None:
                game.board = game.rules.bot_move(game.board, bot_index)

            game.save()

    def game_update(self, message):
        """ Message binding. """
        self.send_json(message['content'])

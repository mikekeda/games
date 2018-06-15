from copy import deepcopy
from datetime import datetime

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import m2m_changed
from django.forms import Textarea

import core.games

channel_layer = get_channel_layer()
User = get_user_model()


class BoardField(ArrayField):
    """ Board field. """

    def formfield(self, **kwargs):
        kwargs['widget'] = Textarea
        if self.blank:
            kwargs['delimiter'] = '\n'
        else:
            kwargs['delimiter'] = '|'

        return super().formfield(**kwargs)


class Game(models.Model):
    """ Game model. """
    players = models.ManyToManyField(User)
    board = BoardField(
        BoardField(
            models.CharField(max_length=3, null=True, blank=True),
        ),
        null=True,
        blank=True

    )
    game = models.CharField(max_length=16, choices=core.games.GAMES)
    current_turn = models.PositiveSmallIntegerField(default=0)

    completed = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rules = None
        if self.game:
            self.rules = getattr(core.games, self.game)
            self.board = self.board or deepcopy(self.rules.board)

    def clean(self):
        super().clean()
        if self.board:
            board_check = self.rules.is_board_valid(self.board)
            if not board_check[0]:
                raise ValidationError(board_check[1])

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.pk:
            self.rules = getattr(core.games, self.game)
            self.board = deepcopy(self.rules.board)

        self.current_turn = self.rules.who_is_going_to_move(self.board)

        winner = self.rules.who_is_winner(self.board)
        if winner is not None:
            self.completed = datetime.now()

        super().save(force_insert, force_update, using, update_fields)

        # Update the game board via websockets.
        async_to_sync(channel_layer.group_send)(
            'game-{}'.format(str(self.pk)),
            {
                'type': 'game.update',
                'content': {
                    'board': self.rules.render_board(self.board),
                    'turn': self.current_turn,
                    'winner': winner,
                    'pk': self.pk
                }
            }
        )

    def __str__(self):
        return '{}: {}'.format(self.pk, self.game)


def players_changed(sender, **kwargs):
    # Validate amount of players.
    if kwargs['action'] == 'pre_add' and kwargs['instance'].players.count() + \
            len(kwargs['pk_set']) != kwargs['instance'].rules.need_players:
        raise ValidationError(
            "You need {} players to play this game".format(
                kwargs['instance'].rules.need_players
            )
        )


m2m_changed.connect(players_changed, sender=Game.players.through)

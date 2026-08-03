from copy import deepcopy
from functools import cached_property

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from django.forms import Textarea
from django.utils import timezone

from core.games import GameState, Move, game_choices, get_game

User = get_user_model()

#: Seats held by this user are played by the game's :attr:`~core.games.base.Game.bot`.
BOT_USERNAME = "bot"


class BoardField(ArrayField):
    """Board field."""

    def formfield(self, **kwargs):
        kwargs["widget"] = Textarea
        if self.blank:
            kwargs["delimiter"] = "\n"
        else:
            kwargs["delimiter"] = "|"

        # ArrayField does define formfield; pylint-django cannot see it.
        return super().formfield(**kwargs)  # pylint: disable=no-member


class Game(models.Model):
    """A single match between players."""

    players = models.ManyToManyField(User, through="GamePlayers")
    board = BoardField(
        BoardField(
            models.CharField(max_length=3, null=True, blank=True),
        ),
        null=True,
        blank=True,
    )
    # Choices are a callable so the registry is consulted lazily, and so that
    # adding a game does not generate a migration.
    game = models.CharField(max_length=32, choices=game_choices)
    current_turn = models.PositiveSmallIntegerField(default=0)
    # Rules that do not fit on the grid: castling rights, en passant target...
    extra = models.JSONField(default=dict, blank=True)

    winner = models.SmallIntegerField(
        null=True,
        blank=True,
        help_text="Index of the winning player. Null on a draw or unfinished game.",
    )
    completed = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Moves made in memory, written to GameMove on the next save.
        self._pending_moves = []

    @cached_property
    def rules(self):
        """The game class backing this match."""
        rules = get_game(self.game)
        if rules is None:
            raise ValueError(f"Unknown game {self.game!r}")
        return rules

    @property
    def state(self) -> GameState:
        """Engine view of this row.

        Both the board and ``extra`` are copied, so a game that mutates the
        state it is handed cannot reach back into this instance.
        """
        return GameState(
            board=[list(row) for row in self.board],
            turn=self.current_turn,
            extra=deepcopy(self.extra) if self.extra else {},
        )

    @state.setter
    def state(self, value: GameState) -> None:
        self.board = value.board
        self.current_turn = value.turn
        self.extra = value.extra

    def ordered_players(self) -> list:
        """Players in seating order."""
        return list(self.players.order_by("gameplayers__order"))

    def play(self, player: int, move: Move) -> GameState:
        """Apply a player's move, then let any bot opponents reply.

        Raises :class:`~core.games.base.InvalidMove` if the move is not legal,
        which includes it not being ``player``'s turn.
        """
        state = self.rules.apply(self.state, player, move)
        self.record_move(player, move)

        state = self._play_bots(state)

        self.state = state
        self.save()
        return state

    def _play_bots(self, state: GameState) -> GameState:
        """Let bot-controlled seats move until it is a human's turn again."""
        bot_seats = {
            index
            for index, user in enumerate(self.ordered_players())
            if user.username == BOT_USERNAME
        }
        if not bot_seats or self.rules.bot is None:
            return state

        # Bounded so a misbehaving bot cannot spin forever.
        for _ in range(self.rules.rows * self.rules.cols):
            if state.turn not in bot_seats or self.rules.outcome(state) is not None:
                break

            move = self.rules.bot.choose(self.rules, state, state.turn)
            if move is None:
                break

            self.record_move(state.turn, move)
            state = self.rules.apply(state, state.turn, move)

        return state

    def record_move(self, player: int, move: Move) -> None:
        """Queue a move for the history table, written on the next save."""
        self._pending_moves.append((player, move))

    def clean(self):
        super().clean()
        if self.board:
            valid, error = self.rules.validate(self.state)
            if not valid:
                raise ValidationError(error)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.state = self.rules.initial_state()

        outcome = self.rules.outcome(self.state)
        if outcome is not None:
            self.winner = outcome.winner
            self.completed = self.completed or timezone.now()

        super().save(*args, **kwargs)
        self._flush_moves()
        self.broadcast(outcome)

    def _flush_moves(self) -> None:
        pending = self._pending_moves
        if not pending:
            return

        # Numbering continues from the highest move on record rather than from
        # a count, so a deleted move cannot make a later one collide.
        last = GameMove.objects.filter(game=self).aggregate(last=Max("number"))["last"]
        start = 0 if last is None else last + 1
        GameMove.objects.bulk_create(
            GameMove(
                game=self, player=player, number=start + offset, move=move.serialize()
            )
            for offset, (player, move) in enumerate(pending)
        )
        self._pending_moves = []

    def broadcast(self, outcome=None) -> None:
        """Push the current position to everyone watching this game."""
        async_to_sync(get_channel_layer().group_send)(
            f"game-{self.pk}",
            {"type": "game.update", "content": self.payload(outcome)},
        )

    def payload(self, outcome=None) -> dict:
        """The websocket message describing the current position."""
        state = self.state
        if outcome is None:
            outcome = self.rules.outcome(state)

        return {
            "pk": self.pk,
            "board": self.rules.render(state),
            "turn": self.current_turn,
            # -1 means a draw; null means the game is still running. Kept for
            # compatibility with the existing client.
            "winner": (
                None if outcome is None else (-1 if outcome.is_draw else outcome.winner)
            ),
            "reason": outcome.reason if outcome else "",
            "highlight": [list(cell) for cell in outcome.cells] if outcome else [],
            "moves": [move.serialize() for move in self.rules.legal_moves(state)],
        }

    def __str__(self):
        return f"{self.pk}: {self.game}"


class GamePlayers(models.Model):
    """A seat at a game."""

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("order",)
        unique_together = (("game", "order"),)

    def clean(self):
        super().clean()
        seats = self.game.rules.player_count
        if not 0 <= self.order < seats:
            raise ValidationError(f"This game only has {seats} seats")

    def save(self, *args, **kwargs):
        """Refuse to seat more players than the game supports."""
        taken = type(self).objects.filter(game=self.game)
        if self.pk:
            taken = taken.exclude(pk=self.pk)

        if taken.count() >= self.game.rules.player_count:
            raise ValidationError(
                f"You need {self.game.rules.player_count} players to play this game"
            )

        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} ({self.order})"


class GameMove(models.Model):
    """One move in a game's history.

    Needed for replay and undo, and for rules that depend on the sequence of
    play rather than the current position (threefold repetition, the fifty-move
    rule, en passant).
    """

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="moves")
    player = models.PositiveSmallIntegerField()
    number = models.PositiveIntegerField()
    move = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("number",)
        unique_together = (("game", "number"),)

    def __str__(self):
        return f"{self.game_id} #{self.number}: {self.move}"

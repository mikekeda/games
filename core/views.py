from django.conf import settings
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import select_template
from django.views import View
from django.urls import reverse

from core.games import games_info, get_game
from core.models import BOT_USERNAME, Game, GamePlayers

User = get_user_model()


def opponents_for(user):
    """Users that ``user`` can start a game against, bot first."""
    if not user.is_authenticated:
        return []

    return sorted(
        User.objects.exclude(pk=user.pk)
        .filter(is_active=True)
        .values_list("username", "pk", named=True),
        key=lambda candidate: (
            candidate.username != BOT_USERNAME,
            candidate.username.lower(),
        ),
    )


def board_template(rules):
    """The board partial for a game, falling back to the generic grid.

    A game only needs its own template if the generic one cannot draw it.
    """
    return select_template(
        [f"games/{rules.slug}.html", "games/board.html"]
    ).template.name


class HomeView(View):
    # noinspection PyMethodMayBeStatic
    def get(self, request):
        """Home page."""
        return render(
            request,
            "homepage.html",
            {"games": games_info(), "users": opponents_for(request.user)},
        )


class GamesView(LoginRequiredMixin, View):
    # noinspection PyMethodMayBeStatic
    def get(self, request, name):
        """Game page."""
        rules = get_game(name)
        if rules is None:
            raise Http404

        return render(
            request,
            "homepage.html",
            {"games": [rules.info()], "users": opponents_for(request.user)},
        )

    # noinspection PyMethodMayBeStatic
    def post(self, request, name):
        """New game."""
        rules = get_game(name)
        if rules is None:
            raise Http404

        try:
            opponent_id = int(request.POST.get("opponent", ""))
        except (TypeError, ValueError) as exc:
            raise Http404("Pick an opponent to play against.") from exc

        opponent = User.objects.filter(pk=opponent_id, is_active=True).first()
        if opponent is None or opponent == request.user:
            raise Http404("Pick an opponent to play against.")

        # A game with empty seats is unplayable, so the row and both seats are
        # written together or not at all.
        with transaction.atomic():
            game = Game(game=name)
            game.save()
            GamePlayers(game=game, user=request.user, order=0).save()
            GamePlayers(game=game, user=opponent, order=1).save()

        return redirect(reverse("core:game", args=(game.game, game.pk)))


class GameView(LoginRequiredMixin, View):
    # noinspection PyMethodMayBeStatic
    def get(self, request, name, pk):
        """Game page."""
        rules = get_game(name)
        if rules is None:
            raise Http404

        game = get_object_or_404(
            Game.objects.prefetch_related("players"), pk=pk, game=name
        )
        players = [user.username for user in game.ordered_players()]
        outcome = game.rules.outcome(game.state)

        if outcome is None:
            winner = None
        elif outcome.is_draw:
            winner = -1
        else:
            winner = players[outcome.winner]

        return render(
            request,
            "game.html",
            {
                "game": game,
                "rules": rules,
                "rows": game.rules.render(game.state),
                "board_template": board_template(rules),
                "players": players,
                "seat": (
                    players.index(request.user.username)
                    if request.user.username in players
                    else None
                ),
                "user_turn": players[game.current_turn],
                "winner": winner,
            },
        )


@login_required
def my_games(request, name=None):
    games = (
        Game.objects.filter(players=request.user)
        .prefetch_related("players")
        .order_by("-id")
    )
    if name:
        if get_game(name) is None:
            raise Http404
        games = games.filter(game=name)

    boards = [
        {
            "game": game,
            "rules": game.rules,
            "rows": game.rules.render(game.state),
            "board_template": board_template(game.rules),
        }
        for game in games
    ]

    return render(request, "games.html", {"boards": boards})


def about_page(request):
    """About page."""
    return render(request, "about.html")


def terms(request):
    """Terms of service page."""
    return render(request, "terms.html")


def log_in(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    form = AuthenticationForm()
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(reverse(settings.LOGIN_REDIRECT_URL))

    return render(request, "login.html", {"form": form})


@login_required
def log_out(request):
    logout(request)
    return redirect(reverse(settings.LOGIN_URL))


def sign_up(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    form = UserCreationForm()
    if request.method == "POST":
        form = UserCreationForm(data=request.POST)
        if form.is_valid():
            form.save()
            user = authenticate(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password1"],
            )
            login(request, user)

            return redirect(reverse(settings.LOGIN_REDIRECT_URL))

    return render(request, "signup.html", {"form": form})

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.urls import reverse

import core.games

from .models import Game

User = get_user_model()


class HomeView(View):
    def get(self, request):
        """ Home page. """
        users = User.objects.exclude(id=request.user.pk) \
            .values_list('username', 'pk', named=True)

        return render(request, "homepage.html",
                      {'games': core.games.GAMES_INFO, 'users': users})


class GamesView(LoginRequiredMixin, View):
    def get(self, request, name):
        """ Game page. """
        game_class = getattr(core.games, name, None)
        if game_class is None:
            raise Http404

        return render(request, "homepage.html",
                      {'games': core.games.GAMES_INFO})

    def post(self, request, name):
        """ New game. """
        game_class = getattr(core.games, name, None)
        if game_class is None:
            raise Http404

        post_object = request.POST.copy()
        opponent = post_object.pop('opponent', [None])[0]
        game = Game(game=name)
        game.save()
        game.players.set([request.user, opponent])

        return redirect(reverse('core:game', args=(game.game, game.pk)))


class GameView(LoginRequiredMixin, View):
    def get(self, request, name, pk):
        """ Game page. """
        game_class = getattr(core.games, name, None)
        if game_class is None:
            raise Http404

        game = get_object_or_404(Game, pk=pk)
        players = [user.username for user in game.players.all()]
        user_turn = players[game.rules.who_is_going_to_move(game.board)]
        winner = game.rules.who_is_winner(game.board)
        game.board = game.rules.render_board(game.board)

        return render(request, "game.html", {
            'game': game,
            'players': players,
            'user_turn': user_turn,
            'winner': players[winner] if winner not in (None, -1) else winner
        })


@login_required
def my_games(request, name=None):
    games = Game.objects.filter(players=request.user)
    if name:
        games = games.filter(game=name)

    for game in games:
        game.board = game.rules.render_board(game.board)

    return render(request, "games.html", {'games': games})


def about_page(request):
    """ About page. """
    return render(request, 'about.html')


def log_in(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(reverse(settings.LOGIN_REDIRECT_URL))

    return render(request, 'login.html', {'form': form})


@login_required
def log_out(request):
    logout(request)
    return redirect(reverse(settings.LOGIN_URL))


def sign_up(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(data=request.POST)
        if form.is_valid():
            form.save()
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            login(request, user)

            return redirect(reverse(settings.LOGIN_REDIRECT_URL))

    return render(request, 'signup.html', {'form': form})

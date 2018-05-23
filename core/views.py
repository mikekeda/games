from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
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

        game = get_object_or_404(Game.objects.prefetch_related('players'),
                                 pk=pk)
        game.board = game.rules.render_board(game.board)

        return render(request, "game.html", {'game': game})


@login_required
def my_games(request, name=None):
    games = Game.objects.filter(players=request.user)
    if name:
        games = games.filter(game=name)
    games = list(games)

    return render(request, "games.html", {'games': games})

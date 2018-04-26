from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.views import View

import core.games

from .models import Game


class HomeView(View):
    def get(self, request):
        """ Home page. """

        return render(request, "homepage.html",
                      {'games': core.games.GAMES_INFO})


class GamesView(LoginRequiredMixin, View):
    def get(self, request, name):
        """ Game page. """
        game_class = getattr(core.games, name, None)
        if game_class is None:
            raise Http404

        return render(request, "homepage.html".format(name),
                      {'games': core.games.GAMES_INFO})


class GameView(LoginRequiredMixin, View):
    def get(self, request, name, pk):
        """ Game page. """
        game_class = getattr(core.games, name, None)
        if game_class is None:
            raise Http404

        game = get_object_or_404(Game, pk=pk)
        game.board = game.rules.render_board(game.board)

        return render(request, "game.html".format(name), {'game': game})


@login_required
def my_games(request, name=None):
    games = Game.objects.filter(players=request.user)
    if name:
        games = games.filter(game=name)
    games = list(games)

    return render(request, "games.html", {'games': games})

"""
Core URL Configuration
"""
from django.urls import path

from core.views import (HomeView, GameView, GamesView, my_games, about_page,
                        log_in, log_out, sign_up, terms)

app_name = "Core"

urlpatterns = [
    path('', HomeView.as_view(), name='homepage'),
    path('about', about_page, name='about'),
    path('terms', terms, name='terms'),
    path('login', log_in, name='login'),
    path('logout', log_out, name='logout'),
    path('signup', sign_up, name='signup'),
    path('game/<str:name>', GamesView.as_view(), name='new_game'),
    path('games', my_games, name='my_games'),
    path('games/<str:name>', my_games, name='my_specific_games'),
    path('game/<str:name>/<int:pk>', GameView.as_view(), name='game'),
]

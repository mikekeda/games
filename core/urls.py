"""
Core URL Configuration
"""
from django.urls import path

from .views import HomeView, GameView, GamesView, my_games

app_name = "Core"

urlpatterns = [
    path('', HomeView.as_view(), name='homepage'),
    path('game/<str:name>', GamesView.as_view(), name='new_game'),
    path('games', my_games, name='my_games'),
    path('games/<str:name>', my_games, name='my_specific_games'),
    path('game/<str:name>/<int:pk>', GameView.as_view(), name='game'),
]

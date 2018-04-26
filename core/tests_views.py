from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .games import GAMES_INFO
from .models import Game


class GamesViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(GamesViewTest, cls).setUpClass()

        # Create usual user.
        cls.test_user = User.objects.create_user(username='testuser',
                                                 password='12345')

        # Create admin user.
        cls.test_admin = User.objects.create_user(username='testadmin',
                                                  password='12345')

        cls.test_game = Game(game='TicTacToe')
        cls.test_game.save()
        cls.test_game.players.set([cls.test_user, cls.test_admin])

    # Pages available for anonymous.
    def test_views_home(self):
        resp = self.client.get(reverse('core:homepage'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'homepage.html')

    # Pages available only for registered users.
    def test_views_new_game(self):
        for game in GAMES_INFO:
            resp = self.client.get(reverse('core:new_game',
                                           kwargs={'name': game['classname']}))
            self.assertEqual(resp.status_code, 302)

        self.client.login(username='testuser', password='12345')
        for game in GAMES_INFO:
            resp = self.client.get(reverse('core:new_game',
                                   kwargs={'name': game['classname']}))
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateUsed(resp, 'homepage.html')

    def test_views_my_games(self):
        resp = self.client.get(reverse('core:my_games'))
        self.assertEqual(resp.status_code, 302)
        self.client.login(username='testuser', password='12345')
        resp = self.client.get(reverse('core:my_games'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'games.html')

    def test_views_game(self):
        resp = self.client.get(reverse('core:game', kwargs={
            'name': self.test_game.game, 'pk': self.test_game.pk}))
        self.assertEqual(resp.status_code, 302)
        self.client.login(username='testuser', password='12345')
        resp = self.client.get(reverse('core:game', kwargs={
            'name': self.test_game.game, 'pk': self.test_game.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'game.html')

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from core.games import all_games
from core.models import Game, GamePlayers

User = get_user_model()

IN_MEMORY_LAYER = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
}


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYER)
class GamesViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = "testpass"
        cls.test_user = User.objects.create_user(
            username="testuser", password=cls.password
        )
        cls.test_admin = User.objects.create_user(
            username="testadmin", password=cls.password
        )

        cls.test_game = Game(game="TicTacToe")
        cls.test_game.save()
        GamePlayers(game=cls.test_game, user=cls.test_user, order=0).save()
        GamePlayers(game=cls.test_game, user=cls.test_admin, order=1).save()

    def login(self):
        self.client.login(username="testuser", password=self.password)

    # Pages available for anonymous.
    def test_views_home(self):
        resp = self.client.get(reverse("core:homepage"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "homepage.html")

    def test_home_does_not_leak_usernames_to_anonymous_visitors(self):
        resp = self.client.get(reverse("core:homepage"))

        self.assertEqual(list(resp.context["users"]), [])
        self.assertNotContains(resp, "testadmin")

    def test_home_offers_opponents_once_logged_in(self):
        self.login()
        resp = self.client.get(reverse("core:homepage"))

        usernames = [user.username for user in resp.context["users"]]
        self.assertIn("testadmin", usernames)
        self.assertNotIn("testuser", usernames)

    def test_views_about(self):
        resp = self.client.get(reverse("core:about"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "about.html")

    def test_views_terms(self):
        resp = self.client.get(reverse("core:terms"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "terms.html")

    def test_views_login(self):
        resp = self.client.get(reverse("core:login"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "login.html")

        self.login()
        resp = self.client.get(reverse("core:login"))
        self.assertRedirects(resp, reverse(settings.LOGIN_REDIRECT_URL))

    def test_views_signup(self):
        resp = self.client.get(reverse("core:signup"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "signup.html")

        self.login()
        resp = self.client.get(reverse("core:signup"))
        self.assertRedirects(resp, reverse(settings.LOGIN_REDIRECT_URL))

    def test_views_logout(self):
        resp = self.client.get(reverse("core:logout"))
        self.assertRedirects(resp, "/login?next=/logout")

        self.login()
        resp = self.client.get(reverse("core:logout"))
        self.assertRedirects(resp, reverse("core:login"))

    # Pages available only for registered users.
    def test_views_new_game(self):
        for rules in all_games():
            resp = self.client.get(
                reverse("core:new_game", kwargs={"name": rules.slug})
            )
            self.assertEqual(resp.status_code, 302)

        self.login()
        for rules in all_games():
            resp = self.client.get(
                reverse("core:new_game", kwargs={"name": rules.slug})
            )
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateUsed(resp, "homepage.html")

    def test_new_game_for_unknown_slug_is_404(self):
        self.login()
        resp = self.client.get(reverse("core:new_game", kwargs={"name": "Nope"}))
        self.assertEqual(resp.status_code, 404)

    def test_starting_a_game_seats_both_players(self):
        self.login()
        resp = self.client.post(
            reverse("core:new_game", kwargs={"name": "TicTacToe"}),
            {"opponent": self.test_admin.pk},
        )

        game = Game.objects.latest("id")
        self.assertRedirects(
            resp, reverse("core:game", kwargs={"name": "TicTacToe", "pk": game.pk})
        )
        self.assertEqual(game.ordered_players(), [self.test_user, self.test_admin])

    def test_starting_a_game_needs_a_real_opponent(self):
        self.login()
        before = Game.objects.count()

        for opponent in ("", "999999", str(self.test_user.pk), "abc"):
            with self.subTest(opponent=opponent):
                resp = self.client.post(
                    reverse("core:new_game", kwargs={"name": "TicTacToe"}),
                    {"opponent": opponent},
                )
                self.assertEqual(resp.status_code, 404)

        self.assertEqual(Game.objects.count(), before)

    def test_views_my_games(self):
        resp = self.client.get(reverse("core:my_games"))
        self.assertEqual(resp.status_code, 302)

        self.login()
        resp = self.client.get(reverse("core:my_games"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "games.html")
        self.assertEqual(len(resp.context["boards"]), 1)

    def test_my_games_filtered_by_game(self):
        self.login()
        resp = self.client.get(
            reverse("core:my_specific_games", kwargs={"name": "ConnectFour"})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["boards"], [])

    def test_my_games_for_unknown_slug_is_404(self):
        self.login()
        resp = self.client.get(
            reverse("core:my_specific_games", kwargs={"name": "dummy"})
        )
        self.assertEqual(resp.status_code, 404)

    def test_views_game(self):
        url = reverse(
            "core:game", kwargs={"name": self.test_game.game, "pk": self.test_game.pk}
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        self.login()

        resp = self.client.get(
            reverse("core:game", kwargs={"name": "not-exists", "pk": self.test_game.pk})
        )
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "game.html")
        self.assertTemplateUsed(resp, "games/board.html")
        self.assertEqual(resp.context["seat"], 0)

    def test_game_url_must_match_the_game(self):
        self.login()
        resp = self.client.get(
            reverse(
                "core:game", kwargs={"name": "ConnectFour", "pk": self.test_game.pk}
            )
        )
        self.assertEqual(resp.status_code, 404)

    def test_board_renders_addressable_cells(self):
        self.login()
        resp = self.client.get(
            reverse(
                "core:game",
                kwargs={"name": self.test_game.game, "pk": self.test_game.pk},
            )
        )

        self.assertContains(resp, 'data-row="0" data-col="0"')
        self.assertContains(resp, 'data-row="2" data-col="2"')
        self.assertContains(resp, "--cell-size: 150px")

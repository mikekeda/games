from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class ToolAdminTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create admin user.
        cls.password = User.objects.make_random_password()
        cls.test_admin = User.objects.create_superuser(
            username="testadmin",
            email="myemail@test.com",
            password=cls.password,
            first_name="Bob",
            last_name="Smit",
        )
        cls.test_admin.save()

    def test_admin_game(self):
        self.client.login(username="testadmin", password=self.password)
        resp = self.client.get("/admin/core/game/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "admin/base.html")

        resp = self.client.get("/admin/core/game/add/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "admin/change_form.html")

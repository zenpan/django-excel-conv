from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AccountViewTests(TestCase):
    def test_register_requires_login(self):
        response = self.client.get(reverse("register"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_logout_requires_post(self):
        user = User.objects.create_user(username="tester", password="password")
        self.client.force_login(user)

        response = self.client.get(reverse("logout"))

        self.assertEqual(response.status_code, 405)

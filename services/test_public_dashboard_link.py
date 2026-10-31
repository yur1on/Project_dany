from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse


class PublicDashboardLinkTests(TestCase):
    def setUp(self):
        self.url = reverse("home")
        self.link = f'href="{reverse("dashboard_home")}"'
        self.staff = get_user_model().objects.create_user(
            username="staff", password="test-password-123", is_staff=True
        )
        self.staff.user_permissions.add(Permission.objects.get(codename="view_service"))

    def test_anonymous_and_unprivileged_users_do_not_see_link(self):
        self.assertNotContains(self.client.get(self.url), self.link)
        self.client.force_login(get_user_model().objects.create_user(username="visitor"))
        self.assertNotContains(self.client.get(self.url), self.link)
        self.assertEqual(self.client.get(reverse("dashboard_home")).status_code, 403)

    def test_staff_and_superuser_see_link_and_can_access_dashboard(self):
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(self.url), self.link)
        self.assertEqual(self.client.get(reverse("dashboard_home")).status_code, 200)
        admin = get_user_model().objects.create_superuser(username="admin", password="test-password-123")
        self.client.force_login(admin)
        self.assertContains(self.client.get(self.url), self.link)
        self.assertEqual(self.client.get(reverse("dashboard_home")).status_code, 200)

    def test_admin_login_session_and_post_logout(self):
        response = self.client.post(reverse("admin:login"), {
            "username": "staff", "password": "test-password-123", "next": reverse("admin:index"),
        })
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.client.get(self.url), self.link)
        self.assertEqual(self.client.get(reverse("dashboard_logout")).status_code, 405)
        self.client.post(reverse("dashboard_logout"))
        self.assertNotContains(self.client.get(self.url), self.link)

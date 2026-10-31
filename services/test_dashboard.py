from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse

from .models import Appointment


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.admin = users.objects.create_superuser("dashboard-admin", password="password")
        cls.regular = users.objects.create_user("regular", password="password")
        cls.staff = users.objects.create_user("staff", password="password", is_staff=True)
        cls.staff.user_permissions.add(Permission.objects.get(codename="view_appointment"))
        cls.appointment = Appointment.objects.create(
            name="Иван", phone="+375291234567", comment="Перезвоните", status=Appointment.Status.CONFIRMED,
            car_make="Skoda", car_model="Octavia", service_type=Appointment.ServiceType.ENGINE,
        )

    def test_anonymous_is_redirected_and_login_page_is_available(self):
        for url in [reverse("dashboard_home"), reverse("dashboard_appointments")]:
            response = self.client.get(url)
            self.assertRedirects(response, f"{reverse('dashboard_login')}?next={url}")
        self.assertEqual(self.client.get(reverse("dashboard_login")).status_code, 200)

    def test_non_staff_and_staff_without_permissions_are_forbidden(self):
        self.client.force_login(self.regular)
        self.assertEqual(self.client.get(reverse("dashboard_home")).status_code, 403)
        user = get_user_model().objects.create_user("no-permissions", password="password", is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("dashboard_appointments")).status_code, 403)

    def test_admin_can_see_overview_and_requests(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard_home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Иван")
        self.assertEqual(response.context["new_count"], 1)
        response = self.client.get(reverse("dashboard_appointments"))
        self.assertContains(response, "+375291234567")
        self.assertContains(response, "Перезвоните")
        self.assertContains(response, 'href="tel:+375291234567"')
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_readonly_staff_cannot_change(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("dashboard_home")).status_code, 200)
        url = reverse("dashboard_mark_processed", args=[self.appointment.pk])
        self.assertEqual(self.client.post(url).status_code, 403)
        self.appointment.refresh_from_db()
        self.assertFalse(self.appointment.is_processed)

    def test_mark_processed_preserves_history_and_is_post_only(self):
        self.client.force_login(self.admin)
        url = reverse("dashboard_mark_processed", args=[self.appointment.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.appointment.refresh_from_db()
        self.assertFalse(self.appointment.is_processed)
        self.assertRedirects(self.client.post(url), reverse("dashboard_appointments"))
        self.appointment.refresh_from_db()
        self.assertTrue(self.appointment.is_processed)
        self.assertEqual(self.appointment.status, Appointment.Status.CONFIRMED)
        self.assertEqual(self.appointment.car_make, "Skoda")
        self.assertEqual(self.appointment.service_type, Appointment.ServiceType.ENGINE)

    def test_processing_and_logout_require_csrf_and_logout_is_post_only(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(reverse("dashboard_mark_processed", args=[self.appointment.pk])).status_code, 403)
        self.assertEqual(client.get(reverse("dashboard_logout")).status_code, 405)
        self.assertEqual(client.post(reverse("dashboard_logout")).status_code, 403)
        response = client.get(reverse("dashboard_home"))
        token = response.cookies["csrftoken"].value
        self.assertRedirects(client.post(reverse("dashboard_logout"), {"csrfmiddlewaretoken": token}), reverse("dashboard_login"))

    def test_filters_and_pagination(self):
        self.client.force_login(self.admin)
        Appointment.objects.bulk_create([
            Appointment(name=f"Клиент {i}", phone="+375291234567", is_processed=i % 2 == 0)
            for i in range(42)
        ])
        url = reverse("dashboard_appointments")
        all_page = self.client.get(url)
        self.assertEqual(all_page.context["page"].paginator.count, 43)
        self.assertEqual(len(all_page.context["page"].object_list), 20)
        self.assertEqual(self.client.get(url, {"page": 3}).context["page"].number, 3)
        new_page = self.client.get(url, {"status": "new"})
        self.assertEqual(new_page.context["page"].paginator.count, 22)
        processed = self.client.get(url, {"status": "processed"})
        self.assertEqual(processed.context["page"].paginator.count, 21)

    def test_login_uses_existing_account_and_redirects_to_dashboard(self):
        response = self.client.post(reverse("dashboard_login"), {"username": "dashboard-admin", "password": "password"})
        self.assertRedirects(response, reverse("dashboard_home"))

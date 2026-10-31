from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse

from .models import Appointment, Service, ServicePhoto, SiteSettings


class SiteSettingsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser("settings-admin", password="password")
        cls.reader = get_user_model().objects.create_user("settings-reader", is_staff=True)
        cls.reader.user_permissions.add(Permission.objects.get(codename="view_sitesettings"))
        cls.ordinary = get_user_model().objects.create_user("settings-ordinary")

    def valid_data(self):
        return {"name": "Авто Центр", "hero_title": "Поможем автомобилю", "description": "Наш сервис", "about": "О нашей мастерской", "phone": "+375 33 111-22-33", "extra_phone": "80291234567", "address": "Новый адрес, 10", "hours": "Ежедневно 10:00-19:00", "telegram_url": "https://t.me/example", "messenger_url": "https://wa.me/375291234567", "map_url": "https://example.com/map"}

    def test_initial_settings_and_singleton(self):
        settings = SiteSettings.objects.get(pk=1)
        self.assertEqual(settings.phone, "+375 29 532-57-52")
        self.assertEqual(settings.address, "ул. Чонгарской дивизии, 5/1")
        self.assertEqual(SiteSettings.objects.count(), 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            SiteSettings.objects.bulk_create([SiteSettings(pk=2)])

    def test_permissions_and_csrf(self):
        url = reverse("dashboard_settings")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.ordinary)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.reader)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.post(url, self.valid_data()).status_code, 403)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(url, self.valid_data()).status_code, 403)
        self.assertEqual(SiteSettings.objects.get().name, "AVTOMOD")

    def test_edit_updates_all_public_pages_and_preserves_data(self):
        self.client.force_login(self.admin)
        service = Service.objects.create(title="Сервис для теста")
        appointment = Appointment.objects.create(name="Иван", phone="+375291234567")
        before_photos = ServicePhoto.objects.count()
        response = self.client.post(reverse("dashboard_settings"), self.valid_data())
        self.assertRedirects(response, reverse("dashboard_settings"))
        for path in ["/", "/services/", "/gallery/", "/contacts/", "/appointment/"]:
            with self.subTest(path=path):
                page = self.client.get(path)
                self.assertContains(page, "Авто Центр")
                self.assertContains(page, "+375 33 111-22-33")
                self.assertContains(page, 'href="tel:+375331112233"')
                self.assertContains(page, "Новый адрес, 10")
                self.assertNotContains(page, "ул. Чонгарской дивизии, 5/1")
                self.assertNotContains(page, "30.987500")
        self.assertContains(self.client.get("/"), "Поможем автомобилю")
        self.assertEqual(SiteSettings.objects.get().about, "О нашей мастерской")
        self.assertNotContains(self.client.get("/contacts/"), "О нашей мастерской")
        self.assertContains(self.client.get("/contacts/"), 'href="tel:+375291234567"')
        self.assertContains(self.client.get("/contacts/"), "https://t.me/example")
        self.assertTrue(Service.objects.filter(pk=service.pk).exists())
        self.assertTrue(Appointment.objects.filter(pk=appointment.pk).exists())
        self.assertEqual(ServicePhoto.objects.count(), before_photos)

    def test_address_change_clears_unchanged_map(self):
        self.client.force_login(self.admin)
        data = self.valid_data()
        data["map_url"] = SiteSettings.objects.get().map_url
        response = self.client.post(reverse("dashboard_settings"), data, follow=True)
        self.assertEqual(SiteSettings.objects.get().map_url, "")
        self.assertContains(response, "прежняя ссылка на карту удалена")
        self.assertNotContains(self.client.get("/contacts/"), "CPhCbWPu")

    def test_contacts_omit_unconfigured_optional_links(self):
        self.client.force_login(self.admin)
        data = {**self.valid_data(), "extra_phone": "", "telegram_url": "", "messenger_url": "", "map_url": ""}
        self.client.post(reverse("dashboard_settings"), data)
        page = self.client.get(reverse("contacts"))
        self.assertContains(page, 'href="tel:+375331112233"')
        self.assertNotContains(page, "contact-tile--messengers")
        self.assertNotContains(page, "Построить маршрут")
        self.assertNotContains(page, 'href="tel:+375291234567"')

    def test_invalid_phone_and_javascript_url_rejected(self):
        self.client.force_login(self.admin)
        url = reverse("dashboard_settings")
        for change, field in [({"phone": "abc"}, "phone"), ({"extra_phone": "12"}, "extra_phone"), ({"telegram_url": "javascript:alert(1)"}, "telegram_url"), ({"map_url": "ftp://example.com/map"}, "map_url")]:
            with self.subTest(field=field):
                response = self.client.post(url, {**self.valid_data(), **change})
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
        self.assertEqual(SiteSettings.objects.get().name, "AVTOMOD")

    def test_text_is_escaped_on_public_pages(self):
        self.client.force_login(self.admin)
        data = {**self.valid_data(), "hero_title": "<script>alert(1)</script>"}
        self.client.post(reverse("dashboard_settings"), data)
        page = self.client.get("/")
        self.assertNotContains(page, "<script>alert(1)</script>")
        self.assertContains(page, "&lt;script&gt;alert(1)&lt;/script&gt;", html=False)

    def test_admin_edits_same_record_and_cannot_add_or_delete(self):
        self.client.force_login(self.admin)
        url = reverse("admin:services_sitesettings_change", args=[1])
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, {**self.valid_data(), "_save": "Сохранить"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SiteSettings.objects.get().phone, "+375 33 111-22-33")
        self.assertContains(self.client.get("/"), "+375 33 111-22-33")
        self.assertEqual(self.client.get(reverse("admin:services_sitesettings_add")).status_code, 403)
        self.assertEqual(self.client.post(reverse("admin:services_sitesettings_delete", args=[1]), {"post": "yes"}).status_code, 403)

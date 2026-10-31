from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Appointment, Service, ServicePhoto


def image_upload(name="test.png"):
    data = BytesIO()
    Image.new("RGB", (8, 8), "red").save(data, "PNG")
    return SimpleUploadedFile(name, data.getvalue(), content_type="image/png")


class DashboardContentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser("content-admin", password="password")
        cls.staff = get_user_model().objects.create_user("reader", is_staff=True)
        cls.staff.user_permissions.add(Permission.objects.get(codename="view_service"))
        cls.service = Service.objects.create(title="Уникальная услуга", description="Описание")

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.temp.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.client.force_login(self.admin)

    def test_add_and_edit_service_with_photo(self):
        response = self.client.post(reverse("dashboard_service_add"), {"title": "Сцепление", "description": "Замена", "is_visible": "on", "photo": image_upload()})
        self.assertRedirects(response, reverse("dashboard_services"))
        service = Service.objects.get(title="Сцепление")
        photo = service.photos.get()
        self.assertTrue(photo.image.name.endswith(".webp"))
        response = self.client.post(reverse("dashboard_service_edit", args=[service.pk]), {"title": "Сцепление новое", "description": "Новое описание"})
        self.assertRedirects(response, reverse("dashboard_services"))
        service.refresh_from_db()
        self.assertFalse(service.is_visible)
        self.assertEqual(service.description, "Новое описание")
        self.assertNotContains(self.client.get(reverse("service_list")), "Сцепление новое")

    def test_no_fallback_when_all_services_hidden(self):
        Service.objects.update(is_visible=False)
        response = self.client.get(reverse("service_list"))
        self.assertNotContains(response, "Уникальная услуга")
        self.assertContains(response, "Список услуг пока обновляется.")
        self.assertNotContains(response, "Сезонная замена шин")

    def test_service_without_illustration(self):
        response = self.client.post(reverse("dashboard_service_add"), {"title": "Новая услуга", "is_visible": "on"})
        self.assertRedirects(response, reverse("dashboard_services"))
        service = Service.objects.get(title="Новая услуга")
        self.assertEqual(service.illustration, "")
        self.assertIsNone(service.illustration_photo_id)
        self.assertContains(self.client.get(reverse("service_list")), service.title)
        self.assertNotContains(self.client.get(reverse("service_list")), "service-row__illustration")
        self.assertNotIn("illustration", self.client.get(reverse("dashboard_service_add")).context["form"].fields)

    def test_edit_preserves_existing_illustration_and_photo(self):
        service = self.service
        photo = ServicePhoto.objects.create(service=service, image=image_upload())
        Service.objects.filter(pk=service.pk).update(illustration="photo", illustration_photo=photo)
        response = self.client.post(reverse("dashboard_service_edit", args=[service.pk]), {"title": service.title, "is_visible": "on", "illustration": ""})
        self.assertRedirects(response, reverse("dashboard_services"))
        service.refresh_from_db()
        self.assertEqual(service.illustration, "photo")
        self.assertEqual(service.illustration_photo_id, photo.pk)
        self.assertTrue(ServicePhoto.objects.filter(pk=photo.pk).exists())
        self.assertContains(self.client.get(reverse("gallery")), photo.image.url)
        self.assertNotIn("illustration", self.client.get(reverse("dashboard_service_edit", args=[service.pk])).context["form"].fields)
        admin_form = self.client.get(reverse("admin:services_service_change", args=[service.pk])).context["adminform"].form
        self.assertIn("illustration", admin_form.fields)
        self.assertIn("illustration_photo", admin_form.fields)

    def test_service_photo_rejects_bad_upload(self):
        url = reverse("dashboard_service_add")
        for upload in (SimpleUploadedFile("fake.svg", b"<svg></svg>", content_type="image/svg+xml"), SimpleUploadedFile("bad.png", b"broken", content_type="image/png"), SimpleUploadedFile("huge.png", b"x" * (10 * 1024 * 1024 + 1))):
            response = self.client.post(url, {"title": "Недопустимый файл", "photo": upload})
            self.assertEqual(response.status_code, 200)
            self.assertIn("photo", response.context["form"].errors)
        self.assertFalse(Service.objects.filter(title="Недопустимый файл").exists())

    def test_public_pages_display_only_visible_services_and_photos(self):
        Service.objects.update(is_visible=False)
        visible = Service.objects.create(title="Актуальная услуга", description="Доступна")
        hidden = Service.objects.create(title="Скрытая услуга", is_visible=False)
        photo = ServicePhoto.objects.create(service=visible, image=image_upload(), caption="Фото видимой услуги")
        hidden_photo = ServicePhoto.objects.create(service=hidden, image=image_upload(), caption="Фото скрытой услуги")
        page = self.client.get(reverse("service_list"))
        self.assertContains(page, visible.title)
        self.assertNotContains(page, hidden.title)
        gallery = self.client.get(reverse("gallery"))
        self.assertContains(gallery, "Фото видимой услуги")
        self.assertContains(gallery, "Актуальная услуга")
        self.assertNotContains(gallery, "Фото скрытой услуги")
        home = self.client.get(reverse("home"))
        self.assertContains(home, "services/img/avtomod-engineering-car.webp")
        self.assertNotContains(home, photo.image.url)
        self.assertNotContains(home, hidden_photo.image.url)

    def test_gallery_empty_state(self):
        ServicePhoto.objects.all().delete()
        self.assertContains(self.client.get(reverse("gallery")), "Фотографии работ скоро появятся")

    def test_add_photo_validation_and_public_visibility(self):
        url = reverse("dashboard_photo_add")
        response = self.client.post(url, {"image": image_upload(), "caption": "Ремонт", "order": 3})
        self.assertRedirects(response, reverse("dashboard_gallery"))
        photo = ServicePhoto.objects.get(caption="Ремонт")
        self.assertTrue(photo.image.name.endswith(".webp"))
        self.assertIsNone(photo.service)
        self.assertContains(self.client.get(reverse("gallery")), "Ремонт")
        response = self.client.post(url, {"image": SimpleUploadedFile("fake.webp", b"not image"), "order": 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn("image", response.context["form"].errors)
        response = self.client.post(url, {"image": SimpleUploadedFile("huge.png", b"x" * (10 * 1024 * 1024 + 1)), "order": 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn("image", response.context["form"].errors)
        self.assertEqual(ServicePhoto.objects.count(), 1)

    def test_edit_and_delete_photo(self):
        photo = ServicePhoto.objects.create(service=self.service, image=image_upload())
        path = photo.image.path
        response = self.client.post(reverse("dashboard_photo_edit", args=[photo.pk]), {"caption": "Новая подпись", "order": 2, "service": self.service.pk})
        self.assertRedirects(response, reverse("dashboard_gallery"))
        photo.refresh_from_db()
        self.assertEqual(photo.caption, "Новая подпись")
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("dashboard_photo_delete", args=[photo.pk]))
        self.assertRedirects(response, reverse("dashboard_gallery"))
        self.assertFalse(ServicePhoto.objects.filter(pk=photo.pk).exists())
        import os
        self.assertFalse(os.path.exists(path))

    def test_delete_service_preserves_photos_and_appointment_history(self):
        photo = ServicePhoto.objects.create(service=self.service, image=image_upload())
        appointment = Appointment.objects.create(name="Иван", phone="+375291234567", service="Уникальная услуга")
        response = self.client.post(reverse("dashboard_service_delete", args=[self.service.pk]))
        self.assertRedirects(response, reverse("dashboard_services"))
        self.service.refresh_from_db()
        self.assertTrue(self.service.is_deleted)
        self.assertFalse(self.service.is_visible)
        self.assertTrue(ServicePhoto.objects.filter(pk=photo.pk).exists())
        self.assertEqual(Appointment.objects.get(pk=appointment.pk).service, "Уникальная услуга")
        self.assertNotContains(self.client.get(reverse("gallery")), photo.image.url)

    def test_permissions_and_csrf(self):
        url = reverse("dashboard_services")
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get(reverse("dashboard_service_add")).status_code, 403)
        self.assertEqual(self.client.get(reverse("dashboard_gallery")).status_code, 403)
        self.assertEqual(self.client.post(reverse("dashboard_service_delete", args=[self.service.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("dashboard_appointments")).status_code, 403)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.admin)
        self.assertEqual(csrf_client.post(reverse("dashboard_service_delete", args=[self.service.pk])).status_code, 403)
        self.assertEqual(csrf_client.get(reverse("dashboard_service_delete", args=[self.service.pk])).status_code, 405)

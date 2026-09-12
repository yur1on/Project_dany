from io import BytesIO
from tempfile import TemporaryDirectory
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from unittest.mock import patch

from PIL import Image

from .models import Appointment, Service, ServicePhoto
from .notifications import format_appointment_message


class PublicPagesTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AVTOMOD")

    def test_appointment_can_be_created(self):
        with patch("services.notifications.request.urlopen") as urlopen:
            response = self.client.post(
                reverse("appointment_create"),
                {
                    "name": "Иван",
                    "phone": "+375291112233",
                    "car_make": "Skoda",
                    "car_model": "Octavia",
                    "car_year": "2018",
                    "service_type": "diagnostics",
                    "comment": "Посторонний звук спереди",
                },
            )
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(Appointment.objects.count(), 1)
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.car, "Skoda Octavia 2018")
        self.assertEqual(appointment.service, "Диагностика")
        urlopen.assert_not_called()

    def test_appointment_requires_car_make_and_model(self):
        response = self.client.post(
            reverse("appointment_create"),
            {
                "name": "Иван",
                "phone": "+375291112233",
                "service_type": "diagnostics",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Обязательное поле")
        self.assertEqual(Appointment.objects.count(), 0)

    def test_appointment_message_contains_request_details(self):
        appointment = Appointment.objects.create(
            name="Иван",
            phone="+375291112233",
            car_make="Skoda",
            car_model="Octavia",
            car_year=2018,
            service_type=Appointment.ServiceType.DIAGNOSTICS,
            comment="Посторонний звук спереди",
        )

        message = format_appointment_message(appointment)

        self.assertIn("Новая заявка AVTOMOD", message)
        self.assertIn("Иван", message)
        self.assertIn("+375291112233", message)
        self.assertIn("Skoda Octavia 2018", message)
        self.assertIn("Диагностика", message)
        self.assertIn("Посторонний звук спереди", message)

    @patch("services.notifications.request.urlopen")
    def test_telegram_notification_is_sent_when_configured(self, urlopen):
        urlopen.return_value.__enter__.return_value = object()

        with self.settings(TELEGRAM_BOT_TOKEN="token", TELEGRAM_CHAT_ID="123"):
            response = self.client.post(
                reverse("appointment_create"),
                {
                    "name": "Иван",
                    "phone": "+375291112233",
                    "car_make": "Skoda",
                    "car_model": "Octavia",
                    "car_year": "2018",
                    "service_type": "diagnostics",
                    "comment": "Посторонний звук спереди",
                },
            )

        self.assertRedirects(response, reverse("home"))
        urlopen.assert_called_once()

    def test_service_photo_upload_is_converted_to_webp(self):
        service = Service.objects.create(title="Тест", description="")
        source = BytesIO()
        Image.new("RGB", (12, 12), "red").save(source, format="PNG")
        upload = SimpleUploadedFile("engine.png", source.getvalue(), content_type="image/png")

        with TemporaryDirectory() as media_root, self.settings(MEDIA_ROOT=media_root):
            photo = ServicePhoto.objects.create(service=service, image=upload)

            self.assertTrue(photo.image.name.endswith(".webp"))
            with photo.image.open("rb") as converted:
                self.assertEqual(converted.read(4), b"RIFF")

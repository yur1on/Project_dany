from io import BytesIO
from tempfile import TemporaryDirectory
from django.test import SimpleTestCase, TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from unittest.mock import patch
from uuid import uuid4
from datetime import timedelta
from urllib.error import HTTPError, URLError

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone

from PIL import Image

from .models import Appointment, Service, ServicePhoto
from .notifications import format_appointment_message
from .templatetags.service_art import service_illustration


class ServiceIllustrationTests(SimpleTestCase):
    def test_known_service_uses_assigned_illustration(self):
        self.assertTrue(service_illustration(Service(pk=7, title="Диагностика", illustration="diagnostics")).endswith("services/img/service-art/diagnostics.svg"))

    def test_unknown_or_mismatched_service_uses_generic_illustration(self):
        for service in (Service(pk=999, title="Диагностика"), Service(pk=7, title="Другая услуга", illustration="invalid")):
            self.assertTrue(service_illustration(service).endswith("services/img/service-art/generic.svg"))


@override_settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID="")
class PublicPagesTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AVTOMOD")

    def test_confirmation_appears_only_after_successful_submission(self):
        self.assertNotContains(self.client.get(reverse("home")), "appointment-confirmation__icon")
        with patch("services.views.notify_appointment_created"):
            response = self.client.post(reverse("appointment_create"), {"name": "Иван", "phone": "+375291112233", "submission_id": str(uuid4())}, follow=True)
        self.assertEqual(response.redirect_chain, [(reverse("home"), 302)])
        self.assertContains(response, "appointment-confirmation__icon")
        self.assertContains(response, "Заявка отправлена")
        self.assertContains(response, 'href="/">На главную')

    def test_public_navigation_uses_separate_pages_and_marks_active_page(self):
        for name in ("home", "service_list", "gallery", "contacts"):
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, f'href="{reverse(name)}" aria-current="page"')
                self.assertNotContains(response, "#process")
                self.assertNotContains(response, 'href="/about/"')

    def test_home_is_a_short_navigation_page(self):
        service = Service.objects.create(title="Уникальный тест услуги", description="Описание")
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, service.title)
        self.assertNotContains(response, 'href="/about/"')
        self.assertContains(self.client.get(reverse("service_list")), service.title)

    def test_old_about_url_redirects_once_to_contacts(self):
        response = self.client.get(reverse("about"))
        self.assertRedirects(response, reverse("contacts"), status_code=301, target_status_code=200)
        self.assertEqual(self.client.get(reverse("about"), follow=True).redirect_chain, [(reverse("contacts"), 301)])

    def test_design_previews_are_local_only(self):
        with override_settings(DEBUG=True):
            for variant in ("a", "b", "c"):
                self.assertEqual(self.client.get(reverse("home_design_preview", args=[variant])).status_code, 200)
            self.assertEqual(self.client.get(reverse("home_design_preview", args=["unknown"])).status_code, 404)
        with override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"]):
            self.assertEqual(self.client.get(reverse("home_design_preview", args=["a"])).status_code, 404)

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
                    "submission_id": str(uuid4()),
                },
            )
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(Appointment.objects.count(), 1)
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.car, "")
        self.assertEqual(appointment.service_type, "")
        self.assertEqual(appointment.service, "")
        urlopen.assert_not_called()

    def test_appointment_requires_name(self):
        response = self.client.post(
            reverse("appointment_create"),
            {
                "name": "",
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
        self.assertNotIn("Skoda Octavia", message)
        self.assertNotIn("Диагностика", message)
        self.assertIn("Время:", message)
        self.assertIn("Посторонний звук спереди", message)

    @patch("services.notifications.request.urlopen")
    def test_telegram_notification_is_sent_when_configured(self, urlopen):
        urlopen.return_value.__enter__.return_value.read.return_value = b'{"ok": true}'

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
                    "submission_id": str(uuid4()),
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


@override_settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID="")
class AppointmentSafetyTests(TestCase):
    def setUp(self):
        self.data = {"name": "Иван", "phone": "+375 29 123-45-67", "comment": "Перезвоните", "submission_id": str(uuid4())}

    def test_common_belarusian_phone_formats(self):
        from .forms import AppointmentForm
        for phone in ["+375 29 123-45-67", "375291234567", "8 (029) 123-45-67", "80291234567", "0291234567", "+375 17 123-45-67"]:
            with self.subTest(phone=phone):
                form = AppointmentForm({**self.data, "phone": phone})
                self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_phone_is_rejected(self):
        from .forms import AppointmentForm
        for phone in ["abc", "12345", "+7 999 123-45-67", "+375 99 123-45-67", "+37529abc1234567", "+375290000000"]:
            with self.subTest(phone=phone):
                form = AppointmentForm({**self.data, "phone": phone})
                self.assertFalse(form.is_valid())
                self.assertIn("phone", form.errors)

    def test_form_only_has_callback_fields_and_csrf(self):
        response = self.client.get(reverse("appointment_create"), {"service": "123"})
        self.assertEqual(set(response.context["form"].fields), {"name", "phone", "comment", "submission_id"})
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertNotContains(response, 'name="car_make"')
        self.assertNotContains(response, 'name="service_type"')

    def test_callback_is_editable_in_admin_without_service(self):
        appointment = Appointment.objects.create(name="Иван", phone="+375291234567")
        user = get_user_model().objects.create_superuser(username="admin", password="password")
        self.client.force_login(user)
        url = reverse("admin:services_appointment_change", args=[appointment.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        form = response.context["adminform"].form
        self.assertFalse(form.fields["service_type"].required)

    def test_csrf_rejects_unprotected_submission(self):
        from django.test import Client
        response = Client(enforce_csrf_checks=True).post(reverse("appointment_create"), self.data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Appointment.objects.count(), 0)

    @patch("services.views.notify_appointment_created")
    def test_replay_notifies_once_but_fresh_form_can_submit(self, notify):
        url = reverse("appointment_create")
        for _ in range(2):
            self.assertRedirects(self.client.post(url, self.data), reverse("home"))
        self.assertEqual(Appointment.objects.count(), 1)
        notify.assert_called_once()
        self.assertRedirects(self.client.post(url, {**self.data, "submission_id": str(uuid4())}), reverse("home"))
        self.assertEqual(Appointment.objects.count(), 2)
        self.assertEqual(notify.call_count, 2)

    def test_fresh_form_has_unique_submission_id(self):
        url = reverse("appointment_create")
        first = self.client.get(url).context["form"]["submission_id"].value()
        second = self.client.get(url).context["form"]["submission_id"].value()
        self.assertNotEqual(first, second)

    def test_missing_submission_id_cannot_create_appointment(self):
        data = {key: value for key, value in self.data.items() if key != "submission_id"}
        response = self.client.post(reverse("appointment_create"), data)
        self.assertIn("submission_id", response.context["form"].errors)
        self.assertEqual(Appointment.objects.count(), 0)


@override_settings(TELEGRAM_BOT_TOKEN="test-token", TELEGRAM_CHAT_ID="test-chat")
class TelegramDeliveryTests(TestCase):
    def setUp(self):
        self.appointment = Appointment.objects.create(name="Иван", phone="+375291234567")

    def send(self, **kwargs):
        from .notifications import notify_appointment_created
        result = notify_appointment_created(self.appointment, **kwargs)
        self.appointment.refresh_from_db()
        return result

    @patch("services.notifications.request.urlopen")
    def test_success_records_sent_and_does_not_send_again(self, urlopen):
        urlopen.return_value.__enter__.return_value.read.return_value = b'{"ok": true}'
        self.assertTrue(self.send())
        self.assertEqual(self.appointment.telegram_status, Appointment.TelegramStatus.SENT)
        self.assertIsNotNone(self.appointment.telegram_last_attempt)
        self.assertFalse(self.send())
        urlopen.assert_called_once()

    @override_settings(TELEGRAM_BOT_TOKEN="")
    @patch("services.notifications.request.urlopen")
    def test_missing_configuration_records_error(self, urlopen):
        self.assertFalse(self.send())
        self.assertEqual(self.appointment.telegram_status, Appointment.TelegramStatus.ERROR)
        self.assertIn("не настроен", self.appointment.telegram_error)
        urlopen.assert_not_called()

    @patch("services.notifications.request.urlopen")
    def test_api_error_records_safe_error(self, urlopen):
        urlopen.return_value.__enter__.return_value.read.return_value = b'{"ok": false, "description": "secret test-token"}'
        with self.assertLogs("services.notifications", level="WARNING") as logs:
            self.assertFalse(self.send())
        self.assertEqual(self.appointment.telegram_status, Appointment.TelegramStatus.ERROR)
        self.assertNotIn("test-token", self.appointment.telegram_error + " ".join(logs.output))

    @patch("services.notifications.request.urlopen")
    def test_http_error_does_not_log_url_with_token(self, urlopen):
        urlopen.side_effect = HTTPError("https://api.telegram.org/bottest-token/sendMessage", 401, "secret", {}, None)
        with self.assertLogs("services.notifications", level="WARNING") as logs:
            self.assertFalse(self.send())
        self.assertEqual(self.appointment.telegram_status, Appointment.TelegramStatus.ERROR)
        self.assertNotIn("test-token", " ".join(logs.output))

    @patch("services.notifications.request.urlopen")
    def test_timeout_marks_uncertain_and_requires_explicit_retry(self, urlopen):
        urlopen.side_effect = TimeoutError("test-token")
        self.assertFalse(self.send())
        self.assertEqual(self.appointment.telegram_status, Appointment.TelegramStatus.UNCERTAIN)
        self.assertFalse(self.send())
        self.assertEqual(urlopen.call_count, 1)
        urlopen.side_effect = None
        urlopen.return_value.__enter__.return_value.read.return_value = b'{"ok": true}'
        self.assertTrue(self.send(retry_uncertain=True))
        self.assertEqual(Appointment.objects.count(), 1)

    @patch("services.notifications.request.urlopen", side_effect=URLError("network failure"))
    def test_network_error_marks_uncertain(self, urlopen):
        self.assertFalse(self.send())
        self.assertEqual(self.appointment.telegram_status, Appointment.TelegramStatus.UNCERTAIN)
        urlopen.assert_called_once()

    @patch("services.notifications.format_appointment_message", side_effect=RuntimeError("test-token"))
    def test_unexpected_failure_keeps_request_and_never_logs_secret(self, format_message):
        data = {"name": "Иван", "phone": "+375291234567", "car_make": "VW", "car_model": "Golf", "service_type": "diagnostics", "submission_id": str(uuid4())}
        with self.assertLogs("services.views", level="ERROR") as logs:
            self.assertRedirects(self.client.post(reverse("appointment_create"), data), reverse("home"))
        appointment = Appointment.objects.get(submission_id=data["submission_id"])
        self.assertEqual(appointment.telegram_status, Appointment.TelegramStatus.SENDING)
        self.assertNotIn("test-token", " ".join(logs.output))

    @patch("services.notifications.request.urlopen")
    def test_retry_error_without_new_appointment(self, urlopen):
        urlopen.return_value.__enter__.return_value.read.side_effect = [b'{"ok": false}', b'{"ok": true}']
        self.assertFalse(self.send())
        self.assertTrue(self.send())
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(urlopen.call_count, 2)

    @patch("services.notifications.request.urlopen")
    def test_claim_blocks_concurrent_attempt_and_stale_attempt_needs_explicit_retry(self, urlopen):
        self.appointment.telegram_status = Appointment.TelegramStatus.SENDING
        self.appointment.telegram_last_attempt = timezone.now()
        self.appointment.save()
        self.assertFalse(self.send(retry_uncertain=True))
        urlopen.assert_not_called()
        Appointment.objects.filter(pk=self.appointment.pk).update(telegram_last_attempt=timezone.now() - timedelta(minutes=6))
        self.assertFalse(self.send())
        urlopen.return_value.__enter__.return_value.read.return_value = b'{"ok": true}'
        self.assertTrue(self.send(retry_uncertain=True))
        urlopen.assert_called_once()

    @patch("services.notifications.request.urlopen")
    def test_repeated_post_creates_one_appointment_and_sends_once(self, urlopen):
        urlopen.return_value.__enter__.return_value.read.return_value = b'{"ok": true}'
        data = {"name": "Иван", "phone": "+375291234567", "car_make": "VW", "car_model": "Golf", "service_type": "diagnostics", "submission_id": str(uuid4())}
        for _ in range(2):
            self.assertRedirects(self.client.post(reverse("appointment_create"), data), reverse("home"))
        self.assertEqual(Appointment.objects.count(), 2)
        urlopen.assert_called_once()

    @patch("services.notifications.request.urlopen", side_effect=TimeoutError("test-token"))
    def test_timeout_does_not_break_client_submission(self, urlopen):
        data = {"name": "Иван", "phone": "+375291234567", "car_make": "VW", "car_model": "Golf", "service_type": "diagnostics", "submission_id": str(uuid4())}
        self.assertRedirects(self.client.post(reverse("appointment_create"), data), reverse("home"))
        self.assertEqual(Appointment.objects.get(submission_id=data["submission_id"]).telegram_status, Appointment.TelegramStatus.UNCERTAIN)

    @patch("services.notifications.request.urlopen")
    def test_admin_displays_and_retries_error(self, urlopen):
        self.appointment.telegram_status = Appointment.TelegramStatus.ERROR
        self.appointment.telegram_last_attempt = timezone.now()
        self.appointment.telegram_error = "Telegram не настроен"
        self.appointment.save()
        user = get_user_model().objects.create_superuser(username="admin", password="password")
        self.client.force_login(user)
        url = reverse("admin:services_appointment_changelist")
        response = self.client.get(url)
        self.assertContains(response, "Ошибка отправки")
        response = self.client.get(reverse("admin:services_appointment_change", args=[self.appointment.pk]))
        self.assertContains(response, "Последняя попытка Telegram")
        self.assertContains(response, "Telegram не настроен")
        urlopen.return_value.__enter__.return_value.read.return_value = b'{"ok": true}'
        self.client.post(url, {"action": "retry_telegram", "_selected_action": [str(self.appointment.pk)]})
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.telegram_status, Appointment.TelegramStatus.SENT)
        self.assertEqual(Appointment.objects.count(), 1)

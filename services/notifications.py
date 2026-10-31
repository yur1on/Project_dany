import json
import logging
import socket
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib import request

from django.conf import settings
from django.utils import timezone

from .models import Appointment

logger = logging.getLogger(__name__)


def format_appointment_message(appointment):
    lines = [
        "Новая заявка AVTOMOD",
        "",
        f"Имя: {appointment.name}",
        f"Телефон: {appointment.phone}",
        f"Время: {timezone.localtime(appointment.created_at).strftime('%d.%m.%Y %H:%M')}",
    ]

    if appointment.comment:
        lines.extend(["", f"Комментарий: {appointment.comment}"])

    return "\n".join(lines)


def send_telegram_message(text):
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        return Appointment.TelegramStatus.ERROR, "Telegram не настроен: отсутствует токен или ID чата."

    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }
    ).encode("utf-8")
    telegram_request = request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(telegram_request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
        if isinstance(result, dict) and result.get("ok") is True:
            return Appointment.TelegramStatus.SENT, ""
        if isinstance(result, dict) and result.get("ok") is False:
            return Appointment.TelegramStatus.ERROR, "Telegram отклонил сообщение. Проверьте настройки бота и чата."
        return Appointment.TelegramStatus.UNCERTAIN, "Некорректный ответ Telegram; проверьте чат перед повтором."
    except HTTPError as exc:
        if 400 <= exc.code < 500:
            return Appointment.TelegramStatus.ERROR, f"Telegram отклонил запрос (HTTP {exc.code})."
        return Appointment.TelegramStatus.UNCERTAIN, "Ошибка сервера Telegram; проверьте чат перед повтором."
    except (TimeoutError, socket.timeout, URLError, OSError, ValueError, UnicodeError):
        return Appointment.TelegramStatus.UNCERTAIN, "Ошибка соединения или ответа; проверьте чат перед повтором."
    except Exception:
        return Appointment.TelegramStatus.UNCERTAIN, "Не удалось определить результат; проверьте чат перед повтором."


def notify_appointment_created(appointment, *, retry_uncertain=False):
    statuses = [Appointment.TelegramStatus.PENDING, Appointment.TelegramStatus.ERROR]
    queryset = Appointment.objects.filter(pk=appointment.pk)
    if retry_uncertain:
        from django.db.models import Q

        claimable = Q(telegram_status=Appointment.TelegramStatus.UNCERTAIN) | Q(
            telegram_status=Appointment.TelegramStatus.SENDING,
            telegram_last_attempt__lt=timezone.now() - timedelta(minutes=5),
        )
        queryset = queryset.filter(claimable)
    else:
        queryset = queryset.filter(telegram_status__in=statuses)

    attempt = timezone.now()
    if not queryset.update(telegram_status=Appointment.TelegramStatus.SENDING, telegram_last_attempt=attempt, telegram_error=""):
        return False

    status, detail = send_telegram_message(format_appointment_message(appointment))
    updated = Appointment.objects.filter(pk=appointment.pk, telegram_status=Appointment.TelegramStatus.SENDING, telegram_last_attempt=attempt).update(
        telegram_status=status, telegram_error=detail,
    )
    if status != Appointment.TelegramStatus.SENT:
        logger.warning("Telegram notification for appointment %s: %s", appointment.pk, detail)
    return bool(updated) and status == Appointment.TelegramStatus.SENT

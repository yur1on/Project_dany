import json
import logging
from urllib import request

from django.conf import settings

logger = logging.getLogger(__name__)


def format_appointment_message(appointment):
    lines = [
        "Новая заявка AVTOMOD",
        "",
        f"Имя: {appointment.name}",
        f"Телефон: {appointment.phone}",
        f"Автомобиль: {appointment.car_display or 'не указан'}",
        f"Тип работ: {appointment.service_display}",
    ]

    if appointment.comment:
        lines.extend(["", f"Комментарий: {appointment.comment}"])

    return "\n".join(lines)


def send_telegram_message(text):
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        return False

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
        with request.urlopen(telegram_request, timeout=5):
            return True
    except Exception:
        logger.exception("Could not send Telegram notification")
        return False


def notify_appointment_created(appointment):
    return send_telegram_message(format_appointment_message(appointment))

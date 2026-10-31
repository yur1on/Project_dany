import re

from django.core.exceptions import ValidationError


def normalize_belarusian_phone(value):
    phone = value.strip()
    if not re.fullmatch(r"\+?[0-9 ()-]+", phone):
        raise ValidationError("Укажите корректный белорусский номер телефона.")
    digits = re.sub(r"[^0-9]", "", phone)
    if phone.startswith("+") and not digits.startswith("375"):
        raise ValidationError("Укажите номер с кодом Беларуси +375.")
    if digits.startswith("375"):
        digits = digits[3:]
    elif digits.startswith("80"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = digits[1:]
    if len(digits) != 9 or digits[:2] not in {"15", "16", "17", "21", "22", "23", "24", "25", "29", "33", "44"} or digits[2:] == "0000000":
        raise ValidationError("Укажите корректный белорусский номер, например +375 29 123-45-67.")
    return "+375" + digits

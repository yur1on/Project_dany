from io import BytesIO
from pathlib import Path
import warnings

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import URLValidator
from django.db import models
from PIL import Image, UnidentifiedImageError

from .validators import normalize_belarusian_phone


class SiteSettings(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    name = models.CharField("Название мастерской", max_length=120, default="AVTOMOD")
    hero_title = models.CharField("Заголовок главной страницы", max_length=180, default="Вернем автомобилю уверенность на дороге")
    description = models.TextField("Краткое описание", default="Диагностика, обслуживание и ремонт. От замены масла до ремонта двигателя.")
    about = models.TextField("О нас", blank=True)
    phone = models.CharField("Основной телефон", max_length=30, default="+375 29 532-57-52", validators=[normalize_belarusian_phone])
    extra_phone = models.CharField("Дополнительный телефон", max_length=30, blank=True, validators=[normalize_belarusian_phone])
    address = models.CharField("Адрес", max_length=200, default="ул. Чонгарской дивизии, 5/1")
    hours = models.CharField("График работы", max_length=160, default="Пн-Пт: 09:00-18:00")
    telegram_url = models.URLField("Ссылка на Telegram", blank=True, validators=[URLValidator(schemes=["http", "https"])], help_text="Полная ссылка, например https://t.me/имя")
    messenger_url = models.URLField("Ссылка на Viber или WhatsApp", blank=True, validators=[URLValidator(schemes=["http", "https"])], help_text="Полная ссылка, начинающаяся с https://")
    map_url = models.URLField("Ссылка на карту или маршрут", blank=True, default="https://yandex.ru/maps/-/CPhCbWPu", validators=[URLValidator(schemes=["http", "https"])], help_text="При изменении адреса укажите новую ссылку на карту.")

    class Meta:
        verbose_name = "настройки сайта"
        verbose_name_plural = "настройки сайта"
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name="single_site_settings")]

    def __str__(self):
        return self.name

    @property
    def phone_href(self):
        return normalize_belarusian_phone(self.phone)

    @property
    def extra_phone_href(self):
        return normalize_belarusian_phone(self.extra_phone) if self.extra_phone else ""

    def save(self, *args, **kwargs):
        if self.pk != 1:
            raise ValidationError("Допустим только один набор настроек сайта.")
        previous = type(self).objects.filter(pk=1).values("address", "map_url").first()
        if previous and previous["address"] != self.address and previous["map_url"] == self.map_url:
            self.map_url = ""
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = set(kwargs["update_fields"]) | {"map_url"}
        super().save(*args, **kwargs)


def validate_photo(upload):
    if upload.size > 10 * 1024 * 1024:
        raise ValidationError("Размер фотографии не должен превышать 10 МБ.")
    try:
        upload.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(upload) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValidationError("Поддерживаются только JPEG, PNG и WebP.")
                if image.width * image.height > 40000000:
                    raise ValidationError("Изображение слишком большое.")
                image.verify()
            upload.seek(0)
            with Image.open(upload) as image:
                image.load()
    except (UnidentifiedImageError, OSError, EOFError, SyntaxError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValidationError("Не удалось открыть изображение. Проверьте файл.")
    finally:
        upload.seek(0)


class Service(models.Model):
    class Illustration(models.TextChoices):
        GENERIC = "", "Универсальная"
        DIAGNOSTICS = "diagnostics", "Диагностический прибор"
        TIMING = "timing", "Ремень ГРМ"
        EXHAUST = "exhaust", "Выхлопная система"
        ENGINE = "engine", "Двигатель"
        SUSPENSION = "suspension", "Подвеска"
        STEERING = "steering", "Рулевое управление"
        BRAKES = "brakes", "Тормоза"
        WHEEL = "wheel", "Колесо"
        PHOTO = "photo", "Своя фотография"

    title = models.CharField("Название", max_length=120)
    description = models.TextField("Описание", blank=True)
    is_popular = models.BooleanField("Популярная услуга", default=False)
    is_visible = models.BooleanField("Показывать на сайте", default=True)
    is_deleted = models.BooleanField("Удалена", default=False)
    illustration = models.CharField("Иллюстрация", max_length=20, choices=Illustration.choices, blank=True, default="")
    illustration_photo = models.ForeignKey("ServicePhoto", verbose_name="Фотография иллюстрации", null=True, blank=True, on_delete=models.SET_NULL, related_name="illustrated_services")

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = ["title"]

    def __str__(self):
        return self.title


class ServiceDescriptionItem(models.Model):
    service = models.ForeignKey(Service, verbose_name="Услуга", related_name="description_items", on_delete=models.CASCADE)
    text = models.CharField("Строка описания", max_length=220)
    order = models.PositiveSmallIntegerField("Порядок", default=1)

    class Meta:
        verbose_name = "строка описания"
        verbose_name_plural = "строки описания"
        ordering = ["order", "id"]

    def __str__(self):
        return self.text


class ServicePhoto(models.Model):
    service = models.ForeignKey(Service, verbose_name="Услуга", related_name="photos", on_delete=models.SET_NULL, null=True, blank=True)
    image = models.FileField("Фото", upload_to="service_photos/", validators=[validate_photo])
    caption = models.CharField("Подпись", max_length=140, blank=True)
    order = models.PositiveSmallIntegerField("Порядок", default=1)

    class Meta:
        verbose_name = "фото услуги"
        verbose_name_plural = "фотографии услуги"
        ordering = ["order", "id"]

    def __str__(self):
        return self.caption or f"Фото: {self.service}"

    def save(self, *args, **kwargs):
        if self.image and not self.image._committed:
            validate_photo(self.image)
            with Image.open(self.image) as image:
                image_format = image.format
            self.image.seek(0)
            if image_format != "WEBP" or not self.image.name.lower().endswith(".webp"):
                self.image = self._convert_image_to_webp(self.image)
        super().save(*args, **kwargs)

    def _convert_image_to_webp(self, uploaded_file):
        from PIL import Image, UnidentifiedImageError

        try:
            uploaded_file.seek(0)
            image = Image.open(uploaded_file)
        except (UnidentifiedImageError, OSError):
            return uploaded_file

        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGBA")
            background = Image.new("RGBA", image.size, (255, 255, 255, 255))
            background.alpha_composite(image)
            image = background.convert("RGB")
        else:
            image = image.convert("RGB")

        output = BytesIO()
        image.save(output, format="WEBP", quality=82, method=6)
        output.seek(0)

        original_name = Path(uploaded_file.name).stem or "service-photo"
        return ContentFile(output.read(), name=f"{original_name}.webp")


class Appointment(models.Model):
    class TelegramStatus(models.TextChoices):
        PENDING = "pending", "Ожидает отправки"
        SENDING = "sending", "Отправляется"
        SENT = "sent", "Отправлено"
        ERROR = "error", "Ошибка отправки"
        UNCERTAIN = "uncertain", "Результат неизвестен"
        UNKNOWN = "unknown", "Старая заявка: статус неизвестен"

    class Status(models.TextChoices):
        NEW = "new", "Новая"
        CONFIRMED = "confirmed", "Подтверждена"
        DONE = "done", "Выполнена"
        CANCELED = "canceled", "Отменена"

    class ServiceType(models.TextChoices):
        DIAGNOSTICS = "diagnostics", "Диагностика"
        TIRES = "tires", "Шиномонтаж"
        EXHAUST = "exhaust", "Выхлопная система"
        SUSPENSION = "suspension", "Ходовая"
        BRAKES = "brakes", "Тормозная система"
        STEERING = "steering", "Рулевое управление"
        TIMING = "timing", "Замена ГРМ"
        ENGINE = "engine", "Двигатель"
        GASKET = "gasket", "Прокладка ГБЦ"
        VALVE_SEALS = "valve_seals", "Маслосъемные колпачки"
        OTHER = "other", "Другое"

    name = models.CharField("Имя", max_length=100)
    submission_id = models.UUIDField("Идентификатор отправки", unique=True, null=True, blank=True, editable=False)
    phone = models.CharField("Телефон", max_length=30)
    car_make = models.CharField("Марка", max_length=80, blank=True)
    car_model = models.CharField("Модель", max_length=80, blank=True)
    car_year = models.PositiveSmallIntegerField("Год выпуска", null=True, blank=True)
    car = models.CharField("Автомобиль", max_length=120, blank=True)
    service_type = models.CharField("Тип работ", max_length=30, choices=ServiceType.choices, blank=True, default="")
    service = models.CharField("Что нужно сделать", max_length=160, blank=True)
    comment = models.TextField("Комментарий", blank=True)
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.NEW)
    is_processed = models.BooleanField("Обработана", default=False)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    telegram_status = models.CharField("Telegram", max_length=16, choices=TelegramStatus.choices, default=TelegramStatus.PENDING)
    telegram_last_attempt = models.DateTimeField("Последняя попытка Telegram", null=True, blank=True)
    telegram_error = models.CharField("Информация о доставке Telegram", max_length=255, blank=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.car_display}"

    @property
    def car_display(self):
        parts = [self.car_make, self.car_model, str(self.car_year or "")]
        value = " ".join(part for part in parts if part).strip()
        return value or self.car

    @property
    def service_display(self):
        if self.service_type == self.ServiceType.OTHER and self.service:
            return self.service
        return self.get_service_type_display() if self.service_type else self.service

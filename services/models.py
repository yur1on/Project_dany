from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.db import models


class Service(models.Model):
    title = models.CharField("Название", max_length=120)
    description = models.TextField("Описание", blank=True)
    is_popular = models.BooleanField("Популярная услуга", default=False)

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
    service = models.ForeignKey(Service, verbose_name="Услуга", related_name="photos", on_delete=models.CASCADE)
    image = models.FileField("Фото", upload_to="service_photos/")
    caption = models.CharField("Подпись", max_length=140, blank=True)
    order = models.PositiveSmallIntegerField("Порядок", default=1)

    class Meta:
        verbose_name = "фото услуги"
        verbose_name_plural = "фотографии услуги"
        ordering = ["order", "id"]

    def __str__(self):
        return self.caption or f"Фото: {self.service}"

    def save(self, *args, **kwargs):
        if self.image and not self.image.name.lower().endswith(".webp"):
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
    phone = models.CharField("Телефон", max_length=30)
    car_make = models.CharField("Марка", max_length=80, blank=True)
    car_model = models.CharField("Модель", max_length=80, blank=True)
    car_year = models.PositiveSmallIntegerField("Год выпуска", null=True, blank=True)
    car = models.CharField("Автомобиль", max_length=120, blank=True)
    service_type = models.CharField("Тип работ", max_length=30, choices=ServiceType.choices, default=ServiceType.DIAGNOSTICS)
    service = models.CharField("Что нужно сделать", max_length=160, blank=True)
    comment = models.TextField("Комментарий", blank=True)
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField("Создана", auto_now_add=True)

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
        return self.get_service_type_display() if self.service_type else self.service

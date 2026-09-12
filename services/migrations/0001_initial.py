from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Appointment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="Имя")),
                ("phone", models.CharField(max_length=30, verbose_name="Телефон")),
                ("car", models.CharField(max_length=120, verbose_name="Автомобиль")),
                ("service", models.CharField(max_length=160, verbose_name="Что нужно сделать")),
                ("preferred_date", models.DateField(blank=True, null=True, verbose_name="Желаемая дата")),
                ("comment", models.TextField(blank=True, verbose_name="Комментарий")),
                (
                    "status",
                    models.CharField(
                        choices=[("new", "Новая"), ("confirmed", "Подтверждена"), ("done", "Выполнена")],
                        default="new",
                        max_length=20,
                        verbose_name="Статус",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
            ],
            options={
                "verbose_name": "Заявка",
                "verbose_name_plural": "Заявки",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("author", models.CharField(max_length=100, verbose_name="Автор")),
                ("car", models.CharField(max_length=120, verbose_name="Автомобиль")),
                ("text", models.TextField(verbose_name="Текст")),
                ("rating", models.PositiveSmallIntegerField(default=5, verbose_name="Оценка")),
                ("is_published", models.BooleanField(default=True, verbose_name="Опубликован")),
            ],
            options={
                "verbose_name": "Отзыв",
                "verbose_name_plural": "Отзывы",
                "ordering": ["-id"],
            },
        ),
        migrations.CreateModel(
            name="Service",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120, verbose_name="Название")),
                ("description", models.TextField(verbose_name="Описание")),
                ("price_from", models.PositiveIntegerField(verbose_name="Цена от")),
                ("duration", models.CharField(max_length=80, verbose_name="Срок выполнения")),
                ("is_popular", models.BooleanField(default=False, verbose_name="Популярная услуга")),
            ],
            options={
                "verbose_name": "Услуга",
                "verbose_name_plural": "Услуги",
                "ordering": ["title"],
            },
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0006_remove_service_duration"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="service",
            name="price_from",
        ),
        migrations.AlterField(
            model_name="appointment",
            name="service_type",
            field=models.CharField(
                choices=[
                    ("diagnostics", "Диагностика"),
                    ("tires", "Шиномонтаж"),
                    ("exhaust", "Выхлопная система"),
                    ("suspension", "Ходовая"),
                    ("brakes", "Тормозная система"),
                    ("steering", "Рулевое управление"),
                    ("timing", "Замена ГРМ"),
                    ("engine", "Двигатель"),
                    ("gasket", "Прокладка ГБЦ"),
                    ("valve_seals", "Маслосъемные колпачки"),
                    ("other", "Другое"),
                ],
                default="diagnostics",
                max_length=30,
                verbose_name="Тип работ",
            ),
        ),
    ]

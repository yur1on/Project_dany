from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0002_delete_review"),
    ]

    operations = [
        migrations.AddField(
            model_name="appointment",
            name="car_make",
            field=models.CharField(blank=True, max_length=80, verbose_name="Марка"),
        ),
        migrations.AddField(
            model_name="appointment",
            name="car_model",
            field=models.CharField(blank=True, max_length=80, verbose_name="Модель"),
        ),
        migrations.AddField(
            model_name="appointment",
            name="car_year",
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Год выпуска"),
        ),
        migrations.AddField(
            model_name="appointment",
            name="license_plate",
            field=models.CharField(blank=True, max_length=20, verbose_name="Госномер"),
        ),
        migrations.AddField(
            model_name="appointment",
            name="preferred_time",
            field=models.TimeField(blank=True, null=True, verbose_name="Желаемое время"),
        ),
        migrations.AddField(
            model_name="appointment",
            name="service_type",
            field=models.CharField(
                choices=[
                    ("diagnostics", "Диагностика"),
                    ("suspension", "Ходовая"),
                    ("brakes", "Тормозная система"),
                    ("maintenance", "Плановое ТО"),
                    ("engine", "Двигатель"),
                    ("electrics", "Электрика"),
                    ("other", "Другое"),
                ],
                default="diagnostics",
                max_length=30,
                verbose_name="Тип работ",
            ),
        ),
        migrations.AlterField(
            model_name="appointment",
            name="car",
            field=models.CharField(blank=True, max_length=120, verbose_name="Автомобиль"),
        ),
        migrations.AlterField(
            model_name="appointment",
            name="service",
            field=models.CharField(blank=True, max_length=160, verbose_name="Что нужно сделать"),
        ),
        migrations.AlterField(
            model_name="appointment",
            name="status",
            field=models.CharField(
                choices=[
                    ("new", "Новая"),
                    ("confirmed", "Подтверждена"),
                    ("done", "Выполнена"),
                    ("canceled", "Отменена"),
                ],
                default="new",
                max_length=20,
                verbose_name="Статус",
            ),
        ),
    ]

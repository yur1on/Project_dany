from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0004_remove_appointment_license_plate"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="appointment",
            name="preferred_date",
        ),
        migrations.RemoveField(
            model_name="appointment",
            name="preferred_time",
        ),
    ]

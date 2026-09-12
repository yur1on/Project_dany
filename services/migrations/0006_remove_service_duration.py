from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0005_remove_appointment_preferred_date_and_time"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="service",
            name="duration",
        ),
    ]

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0003_improve_appointments"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="appointment",
            name="license_plate",
        ),
    ]

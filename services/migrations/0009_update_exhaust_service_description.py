from django.db import migrations


def update_exhaust_description(apps, schema_editor):
    Service = apps.get_model("services", "Service")
    Service.objects.filter(title="Ремонт выхлопной системы").update(
        description="Диагностика и ремонт элементов выхлопной системы."
    )


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0008_seed_auto_mod_services"),
    ]

    operations = [
        migrations.RunPython(update_exhaust_description, migrations.RunPython.noop),
    ]

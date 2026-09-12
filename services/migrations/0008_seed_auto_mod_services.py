from django.db import migrations


AUTO_MOD_SERVICES = [
    {
        "title": "Шиномонтаж",
        "description": "Сезонная замена шин, балансировка и обслуживание колес.",
        "is_popular": True,
    },
    {
        "title": "Ремонт выхлопной системы",
        "description": "Диагностика и ремонт элементов выхлопной системы.",
        "is_popular": False,
    },
    {
        "title": "Ремонт подвески",
        "description": "Диагностика и ремонт ходовой части: рычаги, сайлентблоки, амортизаторы и другие узлы.",
        "is_popular": True,
    },
    {
        "title": "Ремонт тормозов",
        "description": "Обслуживание тормозной системы, замена колодок, дисков и ремонт суппортов.",
        "is_popular": False,
    },
    {
        "title": "Ремонт рулевого управления",
        "description": "Проверка и ремонт узлов рулевого управления.",
        "is_popular": False,
    },
    {
        "title": "Диагностика",
        "description": "Поиск неисправностей перед ремонтом и оценка состояния автомобиля.",
        "is_popular": True,
    },
    {
        "title": "Замена ГРМ",
        "description": "Замена ремня или комплекта ГРМ с учетом требований конкретного двигателя.",
        "is_popular": False,
    },
    {
        "title": "Ремонт двигателя",
        "description": "Ремонт двигателя, замена прокладки ГБЦ и маслосъемных колпачков.",
        "is_popular": False,
    },
]


def seed_services(apps, schema_editor):
    Service = apps.get_model("services", "Service")
    Service.objects.all().delete()
    Service.objects.bulk_create(Service(**service) for service in AUTO_MOD_SERVICES)


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0007_remove_service_price_from_update_appointments"),
    ]

    operations = [
        migrations.RunPython(seed_services, migrations.RunPython.noop),
    ]

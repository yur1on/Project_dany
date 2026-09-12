from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import AppointmentForm
from .models import Service
from .notifications import notify_appointment_created


DEFAULT_SERVICES = [
    {
        "title": "Шиномонтаж",
        "description": "Сезонная замена шин, балансировка и обслуживание колес.",
        "is_popular": True,
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
        "title": "Ремонт выхлопной системы",
        "description": "Диагностика и ремонт элементов выхлопной системы.",
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

def get_services():
    services = list(Service.objects.prefetch_related("description_items", "photos"))
    return services or DEFAULT_SERVICES


def home(request):
    return render(
        request,
        "services/home.html",
    )


def service_list(request):
    return render(request, "services/service_list.html", {"services": get_services()})


def appointment_create(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save()
            notify_appointment_created(appointment)
            messages.success(request, "Заявка отправлена. Мы перезвоним и подтвердим время.")
            return redirect("home")
    else:
        form = AppointmentForm()
    return render(request, "services/appointment.html", {"form": form})


def contacts(request):
    return render(request, "services/contacts.html")

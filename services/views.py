import logging

from django.contrib import messages
from django.conf import settings
from django.http import Http404
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import redirect, render

from .forms import AppointmentForm
from .models import Appointment, Service, ServicePhoto
from .notifications import notify_appointment_created

logger = logging.getLogger(__name__)



def get_services():
    return Service.objects.filter(is_visible=True, is_deleted=False).select_related("illustration_photo").prefetch_related("description_items", "photos")


def home(request):
    return render(
        request,
        "services/home.html",
        {"featured_services": get_services()[:4], "featured_photos": ServicePhoto.objects.filter(Q(service__isnull=True) | Q(service__is_visible=True, service__is_deleted=False))[:3]},
    )


def service_list(request):
    return render(request, "services/service_list.html", {"services": get_services()})


def gallery(request):
    photos = ServicePhoto.objects.filter(Q(service__isnull=True) | Q(service__is_visible=True, service__is_deleted=False)).select_related("service")
    return render(request, "services/gallery.html", {"photos": photos})


def appointment_create(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    appointment = form.save()
            except IntegrityError:
                if Appointment.objects.filter(submission_id=form.cleaned_data["submission_id"]).exists():
                    return redirect("home")
                raise
            try:
                notify_appointment_created(appointment)
            except Exception:
                logger.error("Could not update Telegram delivery for appointment %s", appointment.pk)
            messages.success(request, "Заявка отправлена. Мы перезвоним вам.")
            return redirect("home")
    else:
        form = AppointmentForm()
    return render(request, "services/appointment.html", {"form": form})


def contacts(request):
    return render(request, "services/contacts.html")


def about(request):
    return redirect("contacts", permanent=True)


def home_design_preview(request, variant):
    if not settings.DEBUG or variant not in ("a", "b", "c"):
        raise Http404
    photo = ServicePhoto.objects.filter(Q(service__isnull=True) | Q(service__is_visible=True, service__is_deleted=False)).first()
    return render(request, f"services/preview/home_{variant}.html", {"photo": photo})

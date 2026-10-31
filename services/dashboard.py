from functools import wraps

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .models import Appointment, Service, ServicePhoto, SiteSettings
from .dashboard_forms import ServiceForm, PhotoForm, SiteSettingsForm


class DashboardLoginView(LoginView):
    template_name = "services/dashboard/login.html"
    redirect_authenticated_user = False

    def get_default_redirect_url(self):
        return reverse_lazy("dashboard_home")


DASHBOARD_PERMISSIONS = ("view_appointment", "change_appointment", "view_service", "change_service", "add_service", "delete_service", "view_servicephoto", "change_servicephoto", "add_servicephoto", "delete_servicephoto", "view_sitesettings", "change_sitesettings")


def can_access_dashboard(user):
    return user.is_authenticated and user.is_active and user.is_staff and any(
        user.has_perm(f"services.{permission}") for permission in DASHBOARD_PERMISSIONS
    )


def dashboard_access(view):
    @never_cache
    @login_required(login_url="dashboard_login")
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not can_access_dashboard(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


@dashboard_access
def overview(request):
    if not (request.user.has_perm("services.view_appointment") or request.user.has_perm("services.change_appointment")):
        return render(request, "services/dashboard/overview.html", {"can_view_appointments": False})
    appointments = Appointment.objects.all()
    return render(request, "services/dashboard/overview.html", {
        "can_view_appointments": True,
        "new_count": appointments.filter(is_processed=False).count(),
        "total_count": appointments.count(),
        "appointments": appointments.order_by("-created_at", "-pk")[:5],
    })


@dashboard_access
def appointments(request):
    if not (request.user.has_perm("services.view_appointment") or request.user.has_perm("services.change_appointment")):
        raise PermissionDenied
    selected = request.GET.get("status", "all")
    if selected not in ("all", "new", "processed"):
        selected = "all"
    items = Appointment.objects.order_by("-created_at", "-pk")
    if selected != "all":
        items = items.filter(is_processed=selected == "processed")
    page = Paginator(items, 20).get_page(request.GET.get("page"))
    return render(request, "services/dashboard/appointments.html", {"page": page, "selected": selected})


@dashboard_access
@require_POST
def mark_processed(request, pk):
    if not request.user.has_perm("services.change_appointment"):
        raise PermissionDenied
    appointment = get_object_or_404(Appointment, pk=pk)
    if not appointment.is_processed:
        Appointment.objects.filter(pk=pk, is_processed=False).update(is_processed=True)
        messages.success(request, "Заявка отмечена как обработанная.")
    return redirect("dashboard_appointments")


@never_cache
@login_required(login_url="dashboard_login")
@require_POST
def dashboard_logout(request):
    logout(request)
    return redirect("dashboard_login")


def content_access(*permissions):
    def decorate(view):
        @never_cache
        @login_required(login_url="dashboard_login")
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_active or not request.user.is_staff or not any(request.user.has_perm(p) for p in permissions):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapped
    return decorate


@content_access("services.view_service", "services.change_service")
def service_list(request):
    return render(request, "services/dashboard/services.html", {"services": Service.objects.filter(is_deleted=False).prefetch_related("photos")})


def _service_form(request, instance=None):
    form = ServiceForm(request.POST if request.method == "POST" else None, request.FILES if request.method == "POST" else None, instance=instance)
    if request.method == "POST" and form.is_valid():
        photo = form.cleaned_data.get("photo")
        if photo and not request.user.has_perm("services.add_servicephoto"):
            raise PermissionDenied
        with transaction.atomic():
            service = form.save(commit=False)
            service.save()
            if photo:
                ServicePhoto.objects.create(service=service, image=photo)
        messages.success(request, "Услуга сохранена.")
        return redirect("dashboard_services")
    return render(request, "services/dashboard/content_form.html", {"form": form, "heading": "Изменить услугу" if instance else "Добавить услугу", "back": "dashboard_services", "service": instance})


@content_access("services.add_service")
def service_add(request):
    return _service_form(request)


@content_access("services.change_service")
def service_edit(request, pk):
    return _service_form(request, get_object_or_404(Service, pk=pk, is_deleted=False))


@content_access("services.delete_service")
@require_POST
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk, is_deleted=False)
    service.is_deleted = True
    service.is_visible = False
    service.save(update_fields=["is_deleted", "is_visible"])
    messages.success(request, "Услуга удалена из каталога.")
    return redirect("dashboard_services")


@content_access("services.view_servicephoto", "services.change_servicephoto")
def photo_list(request):
    return render(request, "services/dashboard/gallery.html", {"photos": ServicePhoto.objects.select_related("service")})


def _photo_form(request, instance=None):
    form = PhotoForm(request.POST if request.method == "POST" else None, request.FILES if request.method == "POST" else None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Фотография сохранена.")
        return redirect("dashboard_gallery")
    return render(request, "services/dashboard/content_form.html", {"form": form, "heading": "Изменить фотографию" if instance else "Добавить фотографию", "back": "dashboard_gallery", "photo": instance})


@content_access("services.add_servicephoto")
def photo_add(request):
    return _photo_form(request)


@content_access("services.change_servicephoto")
def photo_edit(request, pk):
    return _photo_form(request, get_object_or_404(ServicePhoto, pk=pk))


@content_access("services.delete_servicephoto")
@require_POST
def photo_delete(request, pk):
    photo = get_object_or_404(ServicePhoto, pk=pk)
    name, storage = photo.image.name, photo.image.storage
    photo.delete()
    def remove_unreferenced_file():
        if name and not ServicePhoto.objects.filter(image=name).exists():
            storage.delete(name)
    transaction.on_commit(remove_unreferenced_file)
    messages.success(request, "Фотография удалена из галереи.")
    return redirect("dashboard_gallery")


@content_access("services.view_sitesettings", "services.change_sitesettings")
def site_settings_view(request):
    instance = get_object_or_404(SiteSettings, pk=1)
    old_address, old_map = instance.address, instance.map_url
    can_edit = request.user.has_perm("services.change_sitesettings")
    if request.method == "POST" and not can_edit:
        raise PermissionDenied
    form = SiteSettingsForm(request.POST if request.method == "POST" else None, instance=instance)
    if not can_edit:
        for field in form.fields.values():
            field.disabled = True
    if request.method == "POST" and form.is_valid():
        new_address, new_map = form.cleaned_data["address"], form.cleaned_data["map_url"]
        form.save()
        if old_address != new_address and old_map and old_map == new_map:
            messages.warning(request, "Адрес изменен: прежняя ссылка на карту удалена. Добавьте новую ссылку.")
        else:
            messages.success(request, "Настройки сайта сохранены.")
        return redirect("dashboard_settings")
    return render(request, "services/dashboard/site_settings.html", {"form": form, "can_edit": can_edit})

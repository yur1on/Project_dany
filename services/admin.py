from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from .models import Appointment, Service, ServiceDescriptionItem, ServicePhoto, SiteSettings
from .dashboard_forms import SiteSettingsForm
from .notifications import notify_appointment_created


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    form = SiteSettingsForm

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists() and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


class ServiceDescriptionItemInline(admin.TabularInline):
    model = ServiceDescriptionItem
    extra = 1
    fields = ("text",)


class ServicePhotoInline(admin.TabularInline):
    model = ServicePhoto
    extra = 1
    fields = ("image", "caption")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "is_popular")
    list_filter = ("is_popular",)
    search_fields = ("title", "description", "description_items__text", "photos__caption")
    exclude = ("is_deleted",)
    inlines = (ServiceDescriptionItemInline, ServicePhotoInline)

    def save_formset(self, request, form, formset, change):
        if formset.model not in (ServiceDescriptionItem, ServicePhoto):
            return super().save_formset(request, form, formset, change)

        formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()

        items = []
        for inline_form in formset.forms:
            if not inline_form.cleaned_data or inline_form.cleaned_data.get("DELETE"):
                continue
            item = inline_form.save(commit=False)
            if getattr(item, "text", None) or getattr(item, "image", None):
                items.append(item)

        for order, item in enumerate(items, start=1):
            item.service = form.instance
            item.order = order
            item.save()

        formset.save_m2m()


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "car_info", "service_info", "status", "telegram_delivery", "telegram_last_attempt", "created_at")
    list_filter = ("status", "service_type", "telegram_status", "created_at")
    search_fields = ("name", "phone", "car_make", "car_model", "car", "service")
    readonly_fields = ("created_at", "telegram_delivery", "telegram_last_attempt", "telegram_error")
    actions = ("retry_telegram", "retry_uncertain_telegram")
    fieldsets = (
        ("Клиент", {"fields": ("name", "phone")}),
        ("Автомобиль", {"fields": ("car_make", "car_model", "car_year", "car")}),
        ("Ремонт", {"fields": ("service_type", "service", "comment")}),
        ("Запись", {"fields": ("status", "created_at")}),
        ("Уведомление Telegram", {"fields": ("telegram_delivery", "telegram_last_attempt", "telegram_error")}),
    )

    @admin.display(description="Автомобиль")
    def car_info(self, obj):
        return obj.car_display

    @admin.display(description="Работы")
    def service_info(self, obj):
        return obj.service_display

    @admin.display(description="Telegram")
    def telegram_delivery(self, obj):
        if obj.telegram_status == Appointment.TelegramStatus.SENDING and obj.telegram_last_attempt and obj.telegram_last_attempt < timezone.now() - timedelta(minutes=5):
            return "Результат неизвестен: проверьте чат перед повтором"
        return obj.get_telegram_status_display()

    @admin.action(description="Повторить неудачные уведомления Telegram")
    def retry_telegram(self, request, queryset):
        self._retry_notifications(request, queryset, retry_uncertain=False)

    @admin.action(description="Повторить с неизвестным результатом (возможен дубль)")
    def retry_uncertain_telegram(self, request, queryset):
        self._retry_notifications(request, queryset, retry_uncertain=True)

    def _retry_notifications(self, request, queryset, *, retry_uncertain):
        sent = 0
        for appointment in queryset:
            try:
                sent += bool(notify_appointment_created(appointment, retry_uncertain=retry_uncertain))
            except Exception:
                messages.error(request, "Не удалось обработать одну из попыток. Проверьте статус заявки.")
        self.message_user(request, f"Отправлено уведомлений: {sent}. Проверьте статусы остальных выбранных заявок.")

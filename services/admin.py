from django.contrib import admin

from .models import Appointment, Service, ServiceDescriptionItem, ServicePhoto


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
    exclude = ("description",)
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
    list_display = ("name", "phone", "car_info", "service_info", "status", "created_at")
    list_filter = ("status", "service_type", "created_at")
    search_fields = ("name", "phone", "car_make", "car_model", "car", "service")
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Клиент", {"fields": ("name", "phone")}),
        ("Автомобиль", {"fields": ("car_make", "car_model", "car_year", "car")}),
        ("Ремонт", {"fields": ("service_type", "service", "comment")}),
        ("Запись", {"fields": ("status", "created_at")}),
    )

    @admin.display(description="Автомобиль")
    def car_info(self, obj):
        return obj.car_display

    @admin.display(description="Работы")
    def service_info(self, obj):
        return obj.service_display

from django import template
from django.templatetags.static import static

from services.models import Service

register = template.Library()

@register.simple_tag
def service_illustration(service):
    if service.illustration == Service.Illustration.PHOTO and service.illustration_photo_id:
        photo = service.illustration_photo
        if photo.service_id == service.pk and photo.image:
            return photo.image.url
    allowed = {value for value, _ in Service.Illustration.choices} - {"", Service.Illustration.PHOTO}
    name = service.illustration if service.illustration in allowed else "generic"
    return static(f"services/img/service-art/{name}.svg")

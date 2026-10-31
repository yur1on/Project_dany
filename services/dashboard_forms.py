from django import forms

from .models import Service, ServicePhoto, SiteSettings, validate_photo


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ("name", "hero_title", "description", "about", "phone", "extra_phone", "address", "hours", "telegram_url", "messenger_url", "map_url")
        widgets = {"description": forms.Textarea(attrs={"rows": 3}), "about": forms.Textarea(attrs={"rows": 4})}


class ServiceForm(forms.ModelForm):
    photo = forms.FileField(label="Фотография услуги", required=False, validators=[validate_photo], help_text="JPEG, PNG или WebP до 10 МБ. Фотография появится в галерее.", widget=forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp", "data-photo-input": ""}))

    class Meta:
        model = Service
        fields = ("title", "description", "is_visible")
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

class PhotoForm(forms.ModelForm):
    class Meta:
        model = ServicePhoto
        fields = ("image", "caption", "service", "order")
        widgets = {"image": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp", "data-photo-input": ""})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(is_deleted=False)
        self.fields["service"].empty_label = "Общая галерея"

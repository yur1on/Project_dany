from django import forms

from .models import Appointment


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            "name",
            "phone",
            "car_make",
            "car_model",
            "car_year",
            "service_type",
            "comment",
        ]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Опишите симптомы: стук, вибрация, ошибка на панели, когда проявляется проблема."}),
            "car_year": forms.NumberInput(attrs={"min": 1980, "max": 2030}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "name": "Ваше имя",
            "phone": "+375 29 532-57-52",
            "car_make": "Например, Volkswagen",
            "car_model": "Например, Passat",
            "car_year": "2018",
        }
        for field_name, placeholder in placeholders.items():
            self.fields[field_name].widget.attrs.setdefault("placeholder", placeholder)
        self.fields["car_make"].required = True
        self.fields["car_model"].required = True

    def save(self, commit=True):
        appointment = super().save(commit=False)
        appointment.car = appointment.car_display
        appointment.service = appointment.service_display
        if commit:
            appointment.save()
            self.save_m2m()
        return appointment

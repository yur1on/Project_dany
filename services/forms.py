from uuid import uuid4

from django import forms
from .models import Appointment
from .validators import normalize_belarusian_phone


class AppointmentForm(forms.ModelForm):
    submission_id = forms.UUIDField(widget=forms.HiddenInput, initial=uuid4)

    class Meta:
        model = Appointment
        fields = ["name", "phone", "comment"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ваше имя"}),
            "phone": forms.TextInput(attrs={"placeholder": "+375 29 123-45-67", "type": "tel"}),
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Расскажите, по какому вопросу вам перезвонить"}),
        }

    def clean_phone(self):
        return normalize_belarusian_phone(self.cleaned_data["phone"])

    def save(self, commit=True):
        appointment = super().save(commit=False)
        appointment.submission_id = self.cleaned_data["submission_id"]
        appointment.service_type = ""
        if commit:
            appointment.save()
            self.save_m2m()
        return appointment

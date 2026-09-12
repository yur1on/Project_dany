from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("services/", views.service_list, name="service_list"),
    path("appointment/", views.appointment_create, name="appointment_create"),
    path("contacts/", views.contacts, name="contacts"),
]

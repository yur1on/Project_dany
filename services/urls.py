from django.urls import path

from . import views
from . import dashboard

urlpatterns = [
    path("", views.home, name="home"),
    path("services/", views.service_list, name="service_list"),
    path("appointment/", views.appointment_create, name="appointment_create"),
    path("contacts/", views.contacts, name="contacts"),
    path("gallery/", views.gallery, name="gallery"),
    path("about/", views.about, name="about"),
    path("_preview/home-<str:variant>/", views.home_design_preview, name="home_design_preview"),
    path("dashboard/services/", dashboard.service_list, name="dashboard_services"),
    path("dashboard/services/add/", dashboard.service_add, name="dashboard_service_add"),
    path("dashboard/services/<int:pk>/edit/", dashboard.service_edit, name="dashboard_service_edit"),
    path("dashboard/services/<int:pk>/delete/", dashboard.service_delete, name="dashboard_service_delete"),
    path("dashboard/gallery/", dashboard.photo_list, name="dashboard_gallery"),
    path("dashboard/gallery/add/", dashboard.photo_add, name="dashboard_photo_add"),
    path("dashboard/gallery/<int:pk>/edit/", dashboard.photo_edit, name="dashboard_photo_edit"),
    path("dashboard/gallery/<int:pk>/delete/", dashboard.photo_delete, name="dashboard_photo_delete"),
    path("dashboard/login/", dashboard.DashboardLoginView.as_view(), name="dashboard_login"),
    path("dashboard/settings/", dashboard.site_settings_view, name="dashboard_settings"),
    path("dashboard/logout/", dashboard.dashboard_logout, name="dashboard_logout"),
    path("dashboard/", dashboard.overview, name="dashboard_home"),
    path("dashboard/appointments/", dashboard.appointments, name="dashboard_appointments"),
    path("dashboard/appointments/<int:pk>/processed/", dashboard.mark_processed, name="dashboard_mark_processed"),
]

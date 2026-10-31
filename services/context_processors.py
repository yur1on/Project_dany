from .models import SiteSettings
from .dashboard import can_access_dashboard


def site_settings(request):
    return {"site_settings": SiteSettings.objects.filter(pk=1).first(), "can_access_dashboard": can_access_dashboard(request.user)}

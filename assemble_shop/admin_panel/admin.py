from django.contrib import admin

from .utils import get_extra_context


class CustomAdminPanelSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        extra_context = get_extra_context(request, extra_context)
        return super().index(request, extra_context)

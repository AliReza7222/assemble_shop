from django.contrib.admin.apps import AdminConfig


class CustomAdminPanelConfig(AdminConfig):
    default_site = "assemble_shop.admin_panel.admin.CustomAdminPanelSite"

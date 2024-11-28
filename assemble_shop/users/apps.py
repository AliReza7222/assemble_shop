import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "assemble_shop.users"
    verbose_name = _("Users")

    def ready(self):
        with contextlib.suppress(ImportError):
            import assemble_shop.users.signals  # noqa: F401

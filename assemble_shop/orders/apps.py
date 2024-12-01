from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "assemble_shop.orders"

    def ready(self):
        try:
            import assemble_shop.orders.signals  # noqa F401
        except ImportError:
            pass

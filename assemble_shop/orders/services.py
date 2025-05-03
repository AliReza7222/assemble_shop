from django.db.models import Sum

from assemble_shop.orders.models import OrderItem


class OrderService:
    @staticmethod
    def get_top_selling():
        return (
            OrderItem.objects.values("product_id")
            .annotate(total_quantity=Sum("quantity"))
            .order_by("-total_quantity")[:6]
        )

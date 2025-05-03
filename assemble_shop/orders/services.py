from dateutil.relativedelta import relativedelta  # type: ignore
from django.db.models import Sum
from django.utils import timezone

from assemble_shop.orders.enums import OrderStatusEnum
from assemble_shop.orders.models import Order, OrderItem


class OrderService:
    @staticmethod
    def get_top_selling():
        return (
            OrderItem.objects.values("product_id")
            .annotate(total_quantity=Sum("quantity"))
            .order_by("-total_quantity")[:6]
        )

    def get_monthly_income(self):
        past_month = timezone.now() - relativedelta(months=1)
        query_income_path_month = (
            Order.objects.filter(
                created_at__gte=past_month,
                status=OrderStatusEnum.COMPLETED.name,
            )
            .values("created_by_id")
            .annotate(month_income=Sum("total_price"))
            .order_by("-month_income")
        )
        sum_income_orders_path_month = query_income_path_month.aggregate(
            total_income=Sum("total_price")
        )["total_income"]
        top_five_customers = query_income_path_month[:5]
        return {
            "income_path_month": sum_income_orders_path_month,
            "top_five_customers": top_five_customers,
        }

    def get_customers_orders(self):
        pass

    def get_top_rated_products(self):
        pass

    def recent_orders(self):
        pass

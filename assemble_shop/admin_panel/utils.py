from dateutil.relativedelta import relativedelta  # type: ignore
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from assemble_shop.orders.enums import OrderStatusEnum
from assemble_shop.orders.models import Order, Product


def get_past_date(month):
    now_month = timezone.now().replace(day=1)
    return now_month - relativedelta(months=month)


def get_label_months():
    date = get_past_date(month=5)
    month_names = []
    for i in range(5):
        date = date + relativedelta(months=1)
        month_names.append(date.strftime("%B"))
    return month_names


def get_order_data():
    orders = Order.objects.filter(
        created_at__gte=get_past_date(month=4),
        status=OrderStatusEnum.COMPLETED.name,
    )
    monthly_income = (
        orders.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total_price=Sum("total_price"))
        .annotate(count=Count("id"))
        .order_by("month")
    )
    data = {}
    for order in monthly_income:
        month_name = order.get("month").strftime("%B")  # type: ignore
        data[month_name] = {
            "total_price": float(order.get("total_price", 0)),
            "count": order.get("count", 0),
        }
    return data


def top_products():
    return Product.objects.filter(
        rating__isnull=False, inventory__gte=0
    ).order_by("-rating")[:5]


def top_customers():
    return (
        Order.objects.filter(
            created_at__gte=get_past_date(month=0),
            status=OrderStatusEnum.COMPLETED.name,
        )
        .values("created_by__email")
        .annotate(total_cost=Sum("total_price"))
        .order_by("-total_cost")
    )[:5]


def get_extra_context(request, extra_context=None):
    extra_context = extra_context or {}
    month_labels = get_label_months()
    order_data = get_order_data()
    total_price_orders = []
    count_orders = []

    for month in month_labels:
        if data := order_data.get(month):
            total_price, count = data.values()
            total_price_orders.append(total_price)
            count_orders.append(count)
        else:
            total_price_orders.append(0)
            count_orders.append(0)

    extra_context["chart_data"] = {
        "total_price": total_price_orders,
        "count_orders": count_orders,
    }
    extra_context["month_labels"] = month_labels
    extra_context["is_superior_group"] = request.user.is_superior_group
    extra_context["top_products"] = top_products()
    extra_context["top_customers"] = top_customers()

    return extra_context

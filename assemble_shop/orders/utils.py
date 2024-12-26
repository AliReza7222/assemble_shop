from decimal import Decimal

from django.db.models import Case, DecimalField, ExpressionWrapper, F, Sum, When
from django.utils import timezone


def get_items_with_price_based_quantity(order):
    return order.items.annotate(
        effective_price=Case(
            When(
                product__discounts__start_date__lte=timezone.now(),
                product__discounts__end_date__gte=timezone.now(),
                product__discounts__is_active=True,
                then=F("product__price")
                * (1 - F("product__discounts__discount_percentage") / 100),
            ),
            default=F("product__price"),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )
    ).annotate(
        total_item_price=ExpressionWrapper(
            F("quantity") * F("effective_price"),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )
    )


def get_total_price_order(order):
    items = get_items_with_price_based_quantity(order)
    total = items.aggregate(total=Sum("total_item_price"))["total"]
    return total.quantize(Decimal("0.01")) if total else Decimal("0.00")

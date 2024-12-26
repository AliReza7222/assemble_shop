from decimal import Decimal

from django.db.models import (
    Case,
    DecimalField,
    ExpressionWrapper,
    F,
    QuerySet,
    Sum,
    When,
)
from django.utils import timezone

from assemble_shop.orders.models import Order


def get_items_with_price_based_quantity(order: Order) -> QuerySet:
    """
    Annotates each order item with its effective price after applying any active discount
    and calculates the total item price based on quantity. The calculation is done at the
    database level using `Case`, `When`, and `F` expressions to optimize performance.
    """
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


def get_total_price_order(order: Order) -> Decimal:
    """
    Calculates the total price of an order by summing up the total price of each item,
    considering quantity and any discount at the database.
    """
    items = get_items_with_price_based_quantity(order)
    total = items.aggregate(total=Sum("total_item_price"))["total"]
    return total.quantize(Decimal("0.01")) if total else Decimal("0.00")

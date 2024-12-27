from decimal import Decimal

from django.db.models import (
    Case,
    DecimalField,
    ExpressionWrapper,
    F,
    OuterRef,
    QuerySet,
    Subquery,
    Sum,
    When,
)
from django.utils import timezone

from assemble_shop.orders.enums import OrderStatusEnum
from assemble_shop.orders.models import Discount, Order, OrderItem, Product


def _get_active_discount_subquery():
    """
    Returns a subquery to fetch the active discount percentage for a product.
    This subquery ensures that only active discounts within the current time range are considered.
    """
    return Discount.objects.filter(
        product=OuterRef("product_id"),
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now(),
    ).values("discount_percentage")[:1]


def _get_items_price_based_on_quantity(order: Order) -> QuerySet:
    """
    Annotates each order item with its effective price after applying any active discount
    and calculates the total item price based on quantity.
    """
    discount_subquery = _get_active_discount_subquery()

    return order.items.annotate(
        discount_percentage_now=Subquery(discount_subquery),
        total_item_price=ExpressionWrapper(
            F("quantity")
            * Case(
                When(
                    discount_percentage_now__isnull=False,
                    then=F("product__price")
                    * (1 - F("discount_percentage_now") / 100),
                ),
                default=F("product__price"),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            ),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        ),
    )


def get_total_price_order(order: Order) -> Decimal:
    """
    Calculates the total price of an order by summing up the total price of each item,
    considering quantity and any discount at the database.
    """
    items = _get_items_price_based_on_quantity(order)
    total = items.aggregate(total=Sum("total_item_price"))["total"]
    return total.quantize(Decimal("0.01")) if total else Decimal("0.00")


def update_total_price_for_orders_pending(product: Product, data: dict) -> None:
    """
    Updates the pending order items and recalculates total prices for affected orders.
    """
    order_items = OrderItem.objects.filter(
        order__status=OrderStatusEnum.PENDING.name, product=product
    ).select_related("order", "product")

    order_items.update(**data)
    affected_orders = Order.objects.filter(
        id__in=order_items.values_list("order", flat=True)
    )

    for order in affected_orders:
        order.total_price = get_total_price_order(order)

    Order.objects.bulk_update(affected_orders, ["total_price"])

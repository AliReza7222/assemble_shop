from django.db.models import (
    Case,
    DecimalField,
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
from assemble_shop.users.models import User


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


def update_order_total_price(order_ids: list[int]) -> None:
    """
    Updates the total price for orders given a list of order IDs.
    """
    order_subquery = Order.objects.filter(
        pk=OuterRef("pk"), id__in=order_ids
    ).annotate(
        total_price_updated=Sum(
            F("items__quantity")
            * Case(
                When(
                    items__discount_percentage__isnull=False,
                    then=F("items__price")
                    * (1 - F("items__discount_percentage") / 100),
                ),
                default=F("items__price"),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            )
        )
    )

    Order.objects.filter(id__in=order_ids).update(
        total_price=Subquery(order_subquery.values("total_price_updated")[:1])
    )


def update_orders_pending(product: Product, data: dict) -> None:
    """
    Updates the pending order items and recalculates total prices for affected orders.
    """
    order_items = OrderItem.objects.filter(
        order__status=OrderStatusEnum.PENDING.name, product=product
    ).select_related("order", "product")

    order_items.update(**data)
    if order_ids := order_items.values_list("order", flat=True):
        update_order_total_price(order_ids=order_ids)  # type: ignore


def get_order_items(order_id: int) -> QuerySet:
    """
    Retrieves the order items for a specific order, including the discount now for each product.
    """
    discount_subquery = _get_active_discount_subquery()

    return (
        OrderItem.objects.filter(order__id=order_id)
        .select_related("product", "order")
        .annotate(
            active_discount=Subquery(
                discount_subquery, output_field=DecimalField()
            )
        )
        .values(
            "product",
            "quantity",
            "product__price",
            "active_discount",
        )
    )


def regenerate_order(order_id: int, user: User) -> Order:
    """
    Regenerates an order by creating a new order and copying the items from an existing order.
    """
    items = get_order_items(order_id)

    new_order = Order.objects.create(created_by=user, updated_by=user)

    new_items_order = [
        OrderItem(
            order=new_order,
            product_id=item["product"],
            quantity=item["quantity"],
            price=item["product__price"],
            discount_percentage=item["active_discount"],
        )
        for item in items
    ]
    OrderItem.objects.bulk_create(new_items_order)
    update_order_total_price(order_ids=[new_order.id])
    return new_order


def confirmed_order(order: Order) -> tuple:
    """
    Verifies and updates the inventory of the products in an order.
    Returns products updated and error messages if any.
    """
    items = order.items.select_related("product")
    products_updated: list = []
    error_messages: list = []

    if not items.exists():
        error_messages.append("You can't Confirmed without item.")
        return products_updated, error_messages

    for item in items:
        if item.product.inventory < item.quantity:
            error_messages.append(
                f"The stock of {item.product} is less than the quantity selected."
            )
        else:
            item.product.inventory -= item.quantity
            products_updated.append(item.product)

    return products_updated, error_messages


def get_extra_context_order(extra_context: dict | None, user: User) -> dict:
    """
    Updating extra_context of change_view admin order.
    """
    extra_context = extra_context or {}
    extra_context.update(
        {
            "pend_status": OrderStatusEnum.PENDING.name,
            "canceled_status": OrderStatusEnum.CANCELED.name,
            "confirmed_status": OrderStatusEnum.CONFIRMED.name,
            "completed_status": OrderStatusEnum.COMPLETED.name,
            "is_superior_group": user.is_superior_group,
        }
    )
    return extra_context

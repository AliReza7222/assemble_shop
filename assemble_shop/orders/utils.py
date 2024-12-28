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
    new_order.total_price = get_total_price_order(new_order)
    new_order.save(update_fields=["total_price"])
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

from django.db import connection
from django.db.models import DecimalField, OuterRef, QuerySet, Subquery
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


def update_order_total_price(order_ids: list[int]):
    """Updates total price for orders using raw SQL with CTE."""
    order_ids_str = ",".join(map(str, order_ids))
    query = f"""
    WITH order_totals AS (
        SELECT
            orders.id AS order_id,
            SUM(
                items.quantity *
                CASE
                    WHEN items.discount_percentage IS NOT NULL
                    THEN items.price * (1 - items.discount_percentage / 100)
                    ELSE items.price
                END
            ) AS total_price_updated
        FROM orders
        LEFT JOIN order_items AS items ON orders.id = items.order_id
        WHERE orders.id IN ({order_ids_str})
        GROUP BY orders.id
    )
    UPDATE orders
    SET total_price = order_totals.total_price_updated
    FROM order_totals
    WHERE orders.id = order_totals.order_id;
    """
    with connection.cursor() as cursor:
        cursor.execute(query)


def update_orders_pending(
    product: Product, data: dict, order_ids: list[int]
) -> None:
    """
    Updates the pending order items and recalculates total prices for affected orders.
    """
    order_items = OrderItem.objects.filter(
        order__status=OrderStatusEnum.PENDING.name, product=product
    ).select_related("order", "product")

    order_items.update(**data)
    update_order_total_price(order_ids=order_ids)


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

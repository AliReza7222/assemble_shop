from django.db import connection, transaction
from django.db.models import FilteredRelation, Q
from django.utils import timezone

from assemble_shop.orders.enums import OrderStatusEnum
from assemble_shop.orders.models import Order, OrderItem, Product
from assemble_shop.users.models import User


def get_pending_order_ids_for_product(product: Product):
    """
    Retrieve the IDs of all pending orders for the given product.
    """
    return product.orders.filter(
        status=OrderStatusEnum.PENDING.name
    ).values_list("id", flat=True)


def update_order_total_price(order_ids: list[int]):
    """Updates total price for orders using raw SQL with CTE."""

    query = """
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
        WHERE orders.id = ANY(%s)
        GROUP BY orders.id
    )
    UPDATE orders
    SET total_price = order_totals.total_price_updated
    FROM order_totals
    WHERE orders.id = order_totals.order_id;
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [list(order_ids)])


@transaction.atomic
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


def order_item_values(order_id: int):
    """
    Retrieves the order items for a specific order using left join with condition.
    """
    return (
        OrderItem.objects.filter(order_id=order_id)
        .select_related("product", "order")
        .annotate(
            active_discount=FilteredRelation(
                "product__discounts",
                condition=(
                    Q(product__discounts__is_active=True)
                    & Q(product__discounts__start_date__lte=timezone.now())
                    & Q(product__discounts__end_date__gte=timezone.now())
                ),
            )
        )
        .values(
            "product",
            "product__price",
            "quantity",
            "active_discount__discount_percentage",
        )
    )


@transaction.atomic
def regenerate_order(order_id: int, user: User) -> Order:
    """
    Regenerates an order by creating a new order and copying the items from an existing order.
    """
    items = order_item_values(order_id)

    new_order = Order.objects.create(created_by=user, updated_by=user)

    new_items_order = [
        OrderItem(
            order=new_order,
            product_id=item["product"],
            quantity=item["quantity"],
            price=item["product__price"],
            discount_percentage=item["active_discount__discount_percentage"],
        )
        for item in items
    ]
    OrderItem.objects.bulk_create(new_items_order)
    update_order_total_price(order_ids=[new_order.id])
    return new_order


@transaction.atomic
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

from decimal import Decimal

from django.db.models import Avg
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from assemble_shop.orders.enums import OrderStatusEnum
from assemble_shop.orders.models import (
    Discount,
    Order,
    OrderItem,
    Product,
    Review,
)


@receiver(post_save, sender=Review)
def update_product_rating(sender, instance, **kwargs):
    """
    Updates the product's average rating after a review is saved.
    """
    product = instance.product
    avg_rating = Review.objects.filter(product=product).aggregate(
        avg_rating=Avg("rating")
    )
    if avg_result := avg_rating.get("avg_rating"):
        product.rating = Decimal(avg_result).quantize(Decimal("0.01"))
        product.save(update_fields=["rating"])


@receiver(pre_save, sender=OrderItem)
def update_price_and_discount_for_order_item(sender, instance, **kwargs):
    """
    Updates the price and discount percentage of an order item before saving.
    """
    instance.price = instance.product.price
    if discount := instance.product.discount_now:
        instance.discount_percentage = discount.discount_percentage


@receiver(post_save, sender=Discount)
def update_pending_orders_after_discount_change(sender, instance, **kwargs):
    """
    Updates the discount percentage for pending order items
    when a discount is changed or created, and recalculates total prices.
    """
    update_pending_orders_discount_products(
        instance.product, discount_percentage=instance.discount_percentage
    )


@receiver(post_delete, sender=Discount)
def update_pending_orders_after_discount_deleted(sender, instance, **kwargs):
    """
    Updates the discount percentage for pending order items
    when a discount is deleted.
    """
    update_pending_orders_discount_products(
        instance.product, discount_percentage=None
    )


@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def update_total_price_after_order_item_change(sender, instance, **kwargs):
    """
    Recalculates the total price of an order when an order item
    is created, updated, or deleted.
    """
    order = instance.order
    total_price = sum(item.get_product_price for item in order.items.all())
    order.total_price = total_price
    order.save(update_fields=["total_price"])


@receiver(post_save, sender=Product)
def update_orders_after_product_change(sender, instance, **kwargs):
    """
    Updates the price in pending order items when a product's price changes
    and recalculates total prices of affected orders.
    """
    order_items = OrderItem.objects.filter(
        product=instance, order__status=OrderStatusEnum.PENDING.name
    ).select_related("order")
    for item in order_items:
        item.price = instance.price
    OrderItem.objects.bulk_update(order_items, ["price"])

    affected_orders = [item.order for item in order_items]
    update_total_price_for_orders(affected_orders)


def update_total_price_for_orders(orders):
    """
    Updates the total price for the given orders.
    """
    for order in orders:
        order.total_price = sum(
            item.get_product_price for item in order.items.all()
        )

    Order.objects.bulk_update(orders, ["total_price"])


def update_pending_orders_discount_products(product, discount_percentage=None):
    """
    Updates the discount percentage for pending order items
    and recalculates total prices for affected orders.
    """
    order_items = OrderItem.objects.filter(
        order__status=OrderStatusEnum.PENDING.name, product=product
    ).select_related("order")

    order_items.update(discount_percentage=discount_percentage)

    affected_orders = [item.order for item in order_items]
    update_total_price_for_orders(affected_orders)

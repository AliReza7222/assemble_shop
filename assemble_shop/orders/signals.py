from decimal import Decimal

from django.db.models import Avg
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .enums import OrderStatusEnum
from .models import *


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


@receiver(post_save, sender=Discount)
def update_pending_orders_after_discount_change(sender, instance, **kwargs):
    """
    Updates the discount percentage for pending order items
    when a discount is changed or created, and recalculates total prices.
    """
    discount_percentage = None
    if (
        instance.is_active
        and instance.start_date <= timezone.now() <= instance.end_date
    ):
        discount_percentage = instance.discount_percentage

    update_total_price_for_orders_pending(
        product=instance.product,
        data={"discount_percentage": discount_percentage},
    )


@receiver(post_delete, sender=Discount)
def update_pending_orders_after_discount_deleted(sender, instance, **kwargs):
    """
    Updates the discount percentage for pending order items
    when a discount is deleted.
    """
    update_total_price_for_orders_pending(
        product=instance.product, data={"discount_percentage": None}
    )


@receiver(post_save, sender=Product)
def update_orders_after_product_change(sender, instance, **kwargs):
    """
    Updates the price in pending order items when a product's price changes
    and recalculates total prices of affected orders.
    """
    if instance.order_items.exists():
        update_total_price_for_orders_pending(
            product=instance, data={"price": instance.price}
        )


def update_total_price_for_orders_pending(product, data):
    """
    Updates the pending order items and recalculates total prices for affected orders.
    """
    order_items = (
        OrderItem.objects.filter(
            order__status=OrderStatusEnum.PENDING.name, product=product
        )
        .select_related("order")
        .select_related("product")
    )

    order_items.update(**data)
    affected_orders = [item.order for item in order_items]

    for order in affected_orders:
        order.total_price = sum(
            item.get_product_price for item in order.items.all()
        )

    Order.objects.bulk_update(affected_orders, ["total_price"])

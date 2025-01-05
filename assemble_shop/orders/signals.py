from decimal import Decimal

from django.db.models import Avg
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import *
from .utils import update_order_total_price, update_orders_pending


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
    update_order_total_price(order_ids=[instance.order.id])


@receiver(post_save, sender=Discount)
def update_pending_orders_after_discount_change(sender, instance, **kwargs):
    """
    Updates the discount percentage for pending order items
    when a discount is changed or created, and recalculates total prices.
    """
    order_ids = instance.product.orders.filter(
        status=OrderStatusEnum.PENDING.name
    ).values_list("id", flat=True)

    if order_ids:
        discount_active = instance.product.discount_now
        update_orders_pending(
            order_ids=order_ids,
            product=instance.product,
            data={
                "discount_percentage": discount_active.discount_percentage
                if discount_active
                else None
            },
        )


@receiver(post_delete, sender=Discount)
def update_pending_orders_after_discount_deleted(sender, instance, **kwargs):
    """
    Updates the discount percentage for pending order items
    when a discount is deleted.
    """
    order_ids = instance.product.orders.filter(
        status=OrderStatusEnum.PENDING.name
    ).values_list("id", flat=True)

    if order_ids:
        update_orders_pending(
            product=instance.product,
            data={"discount_percentage": None},
            order_ids=order_ids,
        )


@receiver(pre_save, sender=Product)
def capture_old_product_instance(sender, instance, **kwargs):
    """
    Captures the current the Product instance from the database
    before saving any changes.
    """
    instance._old_instance = Product.objects.filter(pk=instance.pk).first()


@receiver(post_save, sender=Product)
def update_orders_after_product_change(sender, instance, **kwargs):
    """
    Updates the price in pending order items when a product's price changes
    and recalculates total prices of affected orders.
    """
    order_ids = instance.orders.filter(
        status=OrderStatusEnum.PENDING.name
    ).values_list("id", flat=True)

    if old_instance := getattr(instance, "_old_instance", None):
        if order_ids and old_instance.price != instance.price:
            update_orders_pending(
                product=instance,
                data={"price": instance.price},
                order_ids=order_ids,
            )

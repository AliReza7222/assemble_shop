from decimal import Decimal

from django.db.models import Avg
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from assemble_shop.orders.enums import OrderStatusEnum
from assemble_shop.orders.models import Discount, Order, OrderItem, Review


@receiver(post_save, sender=Review)
def update_product_rating(sender, instance, **kwargs):
    product = instance.product
    avg_rating = Review.objects.filter(product=product).aggregate(
        avg_rating=Avg("rating")
    )
    if avg_result := avg_rating.get("avg_rating"):
        product.rating = Decimal(avg_result).quantize(Decimal("0.01"))
        product.save(update_fields=["rating"])


@receiver(pre_save, sender=OrderItem)
def update_price_and_discount(sender, instance, **kwargs):
    instance.price = instance.product.price
    if discount := instance.product.discount_now:
        instance.discount_percentage = discount.discount_percentage


@receiver(post_save, sender=Discount)
def update_orders_pending(sender, instance, **kwargs):
    order_items = OrderItem.objects.filter(
        order__status=OrderStatusEnum.PENDING.name, product__discounts=instance
    )
    order_items.update(discount_percentage=instance.discount_percentage)

    affected_orders = Order.objects.filter(
        items__product__discounts=instance,
        status=OrderStatusEnum.PENDING.name,
    )

    for order in affected_orders:
        order.total_price = sum(
            item.get_product_price for item in order.items.all()
        )

    Order.objects.bulk_update(affected_orders, ["total_price"])

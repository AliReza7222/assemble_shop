from django.db.models import Count, Sum
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from assemble_shop.orders.models import Order, Review


@receiver(post_save, sender=Review)
def update_rating_product(sender, instance, **kwargs):
    instance.product.update_rating()


@receiver(m2m_changed, sender=Order.products.through)
def set_total_price_and_quantity_order(sender, instance, action, **kwargs):
    if action in ("post_add", "post_remove", "post_clear"):
        result = instance.products.aggregate(
            total_price=Sum("price"), quantity=Count("id")
        )
        instance.quantity = result.get("quantity")
        instance.total_price = result.get("total_price")
        instance.save()

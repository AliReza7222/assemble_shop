from django.db.models.signals import post_save
from django.dispatch import receiver

from assemble_shop.orders.models import Review


@receiver(post_save, sender=Review)
def update_rating_product(sender, instance, **kwargs):
    instance.product.update_rating()

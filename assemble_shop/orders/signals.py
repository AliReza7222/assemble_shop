from decimal import Decimal

from django.db.models import Avg
from django.db.models.signals import post_save
from django.dispatch import receiver

from assemble_shop.orders.models import Review


@receiver(post_save, sender=Review)
def update_product_rating(sender, instance, **kwargs):
    product = instance.product
    avg_rating = Review.objects.filter(product=product).aggregate(
        avg_rating=Avg("rating")
    )
    if avg_result := avg_rating.get("avg_rating"):
        product.rating = Decimal(avg_result).quantize(Decimal("0.01"))
        product.save(update_fields=["rating"])

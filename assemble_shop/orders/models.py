import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from assemble_shop.base.models import BaseModel
from assemble_shop.orders.enums import DiscountFieldsEnum, OrderStatusEnum

User = get_user_model()


class Product(BaseModel):
    name = models.CharField(
        verbose_name=_("Product Name"), max_length=225, unique=True
    )
    price = models.DecimalField(
        verbose_name=_("Price"), max_digits=10, decimal_places=2
    )
    description = models.TextField(verbose_name=_("Description"), blank=True)
    inventory = models.PositiveIntegerField(
        verbose_name=_("Inventory Of Product"), default=0
    )
    rating = models.DecimalField(
        verbose_name=_("Rating"),
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True,
    )

    @property
    def discount_now(self):
        time_now = timezone.now()
        return self.discounts.filter(
            start_date__lte=time_now, end_date__gte=time_now, is_active=True
        ).first()

    @property
    def discounted_price(self):
        discount = self.discount_now
        if discount:
            discounted_price = self.price - (
                self.price * (discount.discount_percentage / 100)
            )
            return Decimal(discounted_price).quantize(Decimal("0.01"))
        return

    def get_attribute_discount(self, attribute):
        return getattr(self.discount_now, attribute)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "products"
        indexes = [models.Index(fields=["name"], name="product_name_idx")]


# ‌  set attributes discounts for Products
def make_getattr(field):
    def getattr(self):
        return self.get_attribute_discount(field)

    getattr.short_description = field.replace("_", " ").title()  # type: ignore
    return getattr


for field in DiscountFieldsEnum.GENERAL_FIELDS.value[1:]:
    setattr(Product, f"get_{field}", make_getattr(field))


class Order(BaseModel):
    products = models.ManyToManyField(  # type: ignore
        Product,
        verbose_name=_("Products"),
        related_name="orders",
        through="OrderItem",
    )
    status = models.CharField(
        verbose_name=_("Status"),
        max_length=50,
        choices=OrderStatusEnum.choices(),
        default=OrderStatusEnum.PENDING.name,
    )
    total_price = models.DecimalField(
        verbose_name=_("Total Price"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    tracking_code = models.UUIDField(
        verbose_name=_("Tracking Code"),
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    @property
    def is_pending_status(self):
        return self.status == OrderStatusEnum.PENDING.name

    def __str__(self):
        return str(self.tracking_code)

    class Meta:
        db_table = "orders"
        indexes = [
            models.Index(
                fields=["tracking_code"], name="order_tracking_code_idx"
            )
        ]


class OrderItem(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name=_("Product"),
        related_name="order_items",
        on_delete=models.DO_NOTHING,
    )
    order = models.ForeignKey(
        Order,
        verbose_name=_("Order"),
        related_name="items",
        on_delete=models.DO_NOTHING,
    )
    quantity = models.PositiveIntegerField(
        default=1, verbose_name=_("Quantity")
    )
    discount_percentage = models.DecimalField(
        verbose_name=_("Discount Percentage"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    price = models.DecimalField(
        verbose_name=_("Porduct Price"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def get_product_price(self):
        discount_product = self.product.discounted_price
        return (
            self.price * self.quantity  # type:ignore
            if not discount_product
            else discount_product * self.quantity
        )

    def __str__(self):
        return f"{self.order} | {self.product}"

    class Meta:
        db_table = "order_items"
        unique_together = ("order", "product")


class Review(BaseModel):
    product = models.ForeignKey(
        Product,
        verbose_name=_("Product"),
        related_name="reviews",
        on_delete=models.CASCADE,
    )
    rating = models.PositiveIntegerField(
        default=1, validators=[MaxValueValidator(5), MinValueValidator(1)]
    )
    comment = models.TextField()

    def __str__(self):
        return f"{self.product} Rating {self.rating}"

    class Meta:
        db_table = "reviews"


class Discount(BaseModel):
    product = models.ForeignKey(
        Product,
        verbose_name=_("Product"),
        related_name="discounts",
        on_delete=models.CASCADE,
    )
    discount_percentage = models.DecimalField(
        verbose_name=_("Discount Percentage"), max_digits=10, decimal_places=2
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product} - off {self.discount_percentage} %"

    class Meta:
        db_table = "discounts"

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from assemble_shop.base.models import BaseModel
from assemble_shop.orders.enums import OrderStatusEnum

User = get_user_model()


class Product(BaseModel):
    name = models.CharField(verbose_name=_("Product Name"), max_length=225)
    price = models.DecimalField(
        verbose_name=_("Price"), max_digits=10, decimal_places=2
    )
    description = models.TextField(verbose_name=_("Description"), blank=True)
    inventory = models.PositiveIntegerField(
        verbose_name=_("Inventory of product"), default=0
    )
    rating = models.DecimalField(
        verbose_name=_("Rating"), max_digits=2, decimal_places=2
    )

    def update_rating(self):
        pass

    @property
    def discounted_price(self):
        pass

    class Meta:
        db_table = "products"


class Order(BaseModel):
    customer = models.ForeignKey(
        User,
        verbose_name=_("Customer"),
        related_name="customer",
        on_delete=models.DO_NOTHING,
    )
    products = models.ManyToManyField(
        Product, verbose_name=_("Products"), related_name="orders"
    )
    quantity = models.PositiveIntegerField(
        verbose_name=_("Quantity"), default=1
    )
    status = models.CharField(
        verbose_name=_("Status"),
        max_length=50,
        choices=OrderStatusEnum.choices(),
        default=OrderStatusEnum.PENDING.value,
    )

    class Meta:
        db_table = "orders"


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
        verbose_name=_("Discount of Product"), max_digits=2, decimal_places=2
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    def set_is_active(self):
        pass

    class Meta:
        db_table = "discounts"

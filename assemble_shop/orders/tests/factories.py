import random

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from assemble_shop.base.factories import BaseFactory
from assemble_shop.orders.models import (
    Discount,
    Order,
    OrderItem,
    Product,
    Review,
)


class ProductFactory(BaseFactory):
    name = factory.Faker("word")
    price = factory.Faker(
        "pydecimal",
        left_digits=3,
        right_digits=2,
        positive=True,
    )
    inventory = factory.Faker("random_int", min=0, max=100)

    class Meta:
        model = Product


class ReviewFactory(BaseFactory):
    product = factory.SubFactory(ProductFactory)
    rating = factory.Faker("random_int", min=1, max=5)
    comment = factory.Faker("text")

    class Meta:
        model = Review


class DiscountFactory(BaseFactory):
    product = factory.SubFactory(ProductFactory)
    discount_percentage = factory.Faker(
        "pydecimal", left_digits=2, right_digits=2, positive=True, max_value=100
    )
    start_date = factory.LazyFunction(timezone.now)
    end_date = factory.LazyAttribute(
        lambda obj: obj.start_date
        + timezone.timedelta(days=random.randint(1, 30))  # type:ignore
    )

    class Meta:
        model = Discount


class OrderFactory(BaseFactory):
    class Meta:
        model = Order


class OrderItemFactory(DjangoModelFactory):
    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    price = factory.SelfAttribute("product.price")

    class Meta:
        model = OrderItem


class OrderWithMultipleOrderItem(OrderFactory):
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        products = kwargs.pop("products", [])
        order = super()._create(model_class, *args, **kwargs)

        for i, product in enumerate(products):
            OrderItemFactory(order=order, product=product)

        return order

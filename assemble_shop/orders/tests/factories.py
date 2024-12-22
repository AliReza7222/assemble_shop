import decimal
import random

from factory import Faker, LazyFunction, SubFactory

from assemble_shop.base.factories import BaseFactory
from assemble_shop.orders.models import Discount, Product, Review


class ProductFactory(BaseFactory):
    name = Faker("word")
    price = LazyFunction(
        lambda: decimal.Decimal(random.randint(100, 10000)) / 100
    )
    inventory = Faker("random_int", min=0, max=100)

    class Meta:
        model = Product


class ReviewFactory(BaseFactory):
    product = SubFactory(ProductFactory)
    rating = Faker("random_int", min=1, max=5)
    comment = Faker("text")

    class Meta:
        model = Review


class DiscountFactory(BaseFactory):
    product = SubFactory(ProductFactory)
    discount_percentage = LazyFunction(
        lambda: decimal.Decimal(random.randint(0, 100))
    )
    start_date = Faker("date_time_this_year")
    end_date = Faker("date_time_this_year", after_now=True)

    class Meta:
        model = Discount

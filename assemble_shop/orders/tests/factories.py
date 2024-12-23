from factory import Faker, SubFactory

from assemble_shop.base.factories import BaseFactory
from assemble_shop.orders.models import Discount, Product, Review


class ProductFactory(BaseFactory):
    name = Faker("word")
    price = Faker(
        "pydecimal",
        left_digits=3,
        right_digits=2,
        positive=True,
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
    discount_percentage = Faker(
        "pydecimal", left_digits=2, right_digits=2, positive=True, max_value=100
    )
    start_date = Faker("date_time_this_year")
    end_date = Faker("date_time_this_year", after_now=True)

    class Meta:
        model = Discount

from decimal import Decimal

import pytest
from django.utils import timezone


class TestProductModel:
    def test_no_discount(self, create_product):
        product = create_product(name="P1")

        assert product.discount_now is None
        assert product.discounted_price is None

    def test_active_discount(self, create_product, create_discount):
        product = create_product(name="P1", price=Decimal("100"))
        discount_now = create_discount(
            product=product,
            discount_percentage=Decimal("10"),
            start_date=timezone.now() - timezone.timedelta(days=1),  # type: ignore
            end_date=timezone.now() + timezone.timedelta(days=1),  # type: ignore
            is_active=True,
        )

        assert product.discount_now == discount_now
        assert product.discounted_price == Decimal("90")

    def test_expired_discount(self, create_product, create_discount):
        product = create_product(name="P1", price=Decimal("100"))
        create_discount(
            product=product,
            discount_percentage=Decimal("10"),
            start_date=timezone.now() - timezone.timedelta(days=2),  # type: ignore
            end_date=timezone.now() - timezone.timedelta(days=1),  # type: ignore
            is_active=True,
        )

        assert product.discount_now is None
        assert product.discounted_price is None

    def test_multiple_discounts(self, create_product, create_discount):
        product = create_product(name="P1", price=Decimal("100"))

        discount_now = create_discount(
            product=product,
            discount_percentage=Decimal("20"),
            start_date=timezone.now() - timezone.timedelta(days=1),  # type: ignore
            end_date=timezone.now() + timezone.timedelta(days=1),  # type: ignore
            is_active=True,
        )

        create_discount(
            product=product,
            discount_percentage=Decimal("10"),
            start_date=timezone.now() + timezone.timedelta(days=2),  # type: ignore
            end_date=timezone.now() + timezone.timedelta(days=7),  # type: ignore
            is_active=True,
        )

        assert product.discount_now == discount_now
        assert product.discounted_price == Decimal("80")


class TestOrderModel:
    def test_total_price_without_discount(
        self, create_order_with_items, create_product
    ):
        """
        Test that the total price of an order is correctly calculated
        when no discounts are applied to the products.
        """
        product1 = create_product(name="Product1", price=Decimal("150.83"))
        product2 = create_product(name="Product2", price=Decimal("173.49"))
        order = create_order_with_items(products=[product1, product2])

        assert order.total_price == pytest.approx(
            product1.price + product2.price
        )
        assert order.items.count() == 2

    def test_total_price_with_discount(
        self, create_order_with_items, create_product, product_with_discount
    ):
        """
        Test that the total price of an order is correctly calculated
        when one or more products have discounts applied.
        """
        product = create_product(name="Product", price=Decimal("150.83"))
        order = create_order_with_items(
            products=[product, product_with_discount]
        )

        assert order.total_price == pytest.approx(
            product.price + product_with_discount.discounted_price
        )
        assert order.items.count() == 2

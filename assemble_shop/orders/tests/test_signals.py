from decimal import Decimal

import pytest

from assemble_shop.orders.enums import OrderStatusEnum


class TestProductSignal:
    def test_no_reviews(self, create_product):
        product = create_product()

        assert product.rating is None

    def test_multiple_ratings(self, faker, create_product, create_review):
        expected_rating = Decimal("0")
        num_review = 5
        faker.seed_instance(42)
        product = create_product()

        for _ in range(num_review):
            rating = faker.random_int(min=1, max=5)
            create_review(product=product, rating=rating)
            expected_rating += rating

        expected_rating = (expected_rating / num_review).quantize(
            Decimal("0.01")
        )

        assert product.rating == expected_rating


class TestOrderSignal:
    def test_total_price_without_discount(self, create_order, create_product):
        """
        Test that the total price of an order is correctly calculated
        when no discounts are applied to the products.
        """
        product1 = create_product(name="Product1", price=Decimal("150.83"))
        product2 = create_product(name="Product2", price=Decimal("173.49"))
        order = create_order(products=[product1, product2])

        assert order.total_price == pytest.approx(
            product1.price + product2.price
        )
        assert order.items.count() == 2

    def test_total_price_with_discount(
        self, create_order, create_product, product_with_discount
    ):
        """
        Test that the total price of an order is correctly calculated
        when one or more products have discounts applied.
        """
        product = create_product(name="Product", price=Decimal("150.83"))
        order = create_order(products=[product, product_with_discount])

        assert order.total_price == pytest.approx(
            product.price + product_with_discount.discounted_price
        )
        assert order.items.count() == 2

    def test_create_and_delete_discount_in_status_pending(
        self, create_product, create_discount, create_order
    ):
        """
        Verifies that the total price updates correctly after applying and removing the discount.
        """
        product1 = create_product(name="Product1", price=Decimal("150.83"))
        product2 = create_product(name="Product2", price=Decimal("173.49"))
        order = create_order(products=[product1, product2])

        discount_product2 = create_discount(
            product=product2,
            discount_percentage=Decimal("50.50"),
            is_active=True,
        )
        order.refresh_from_db()
        assert order.total_price == pytest.approx(
            product1.price + product2.discounted_price
        )

        discount_product2.delete()
        order.refresh_from_db()
        assert order.total_price == pytest.approx(
            product1.price + product2.price
        )

    def test_update_product_in_status_pending(
        self, create_product, create_order
    ):
        """
        Verifies that the order's total price reflects the updated product price.
        """
        product = create_product(name="Product", price=Decimal("150.83"))
        order = create_order(products=[product])

        product.price = Decimal("199.99")
        product.save()
        order.refresh_from_db()

        assert order.total_price == product.price

    def test_update_product_when_is_not_status_pending(
        self, create_product, create_order, create_discount
    ):
        """
        Verifies that the items and values of an order do not change when the order
        is not in 'PENDING' status and  when a product's price is updated or a discount is applied.
        """
        product1 = create_product(name="Product1", price=Decimal("150.83"))
        product2 = create_product(name="Product2", price=Decimal("200"))
        order = create_order(
            products=[product1, product2], status=OrderStatusEnum.CONFIRMED.name
        )
        old_total_price = order.total_price

        product1.price = Decimal("199.99")
        create_discount(
            product=product2, discount_percentage=Decimal("50"), is_active=True
        )
        product1.save()
        order.refresh_from_db()

        assert order.total_price == old_total_price
        assert order.items.filter(
            product__name="Product1", price=Decimal("150.83")
        ).exists()
        assert order.items.filter(
            product__name="Product2", discount_percentage__isnull=True
        ).exists()

from decimal import Decimal

import pytest

from assemble_shop.orders.enums import OrderStatusEnum


class TestProductSignal:
    def test_multiple_ratings(self, create_product, create_review):
        """
        This test ensures that the average rating is calculated correctly when
        several reviews with different ratings are added.
        """
        product = create_product()
        create_review(product=product, rating=3)
        create_review(product=product, rating=5)
        create_review(product=product, rating=1)
        expected_rating = Decimal((3 + 5 + 1) / 3).quantize(Decimal("0.01"))

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
        order.refresh_from_db()

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
        order.refresh_from_db()

        assert order.total_price == pytest.approx(
            product.price + product_with_discount.discounted_price
        )
        assert order.items.count() == 2

    def test_updated_discount_in_status_pending(
        self, create_product, create_order, create_discount
    ):
        product1 = create_product(name="Product1", price=Decimal("150.83"))
        product2 = create_product(name="Product2", price=Decimal("500"))
        order = create_order(products=[product1, product2])
        old_total_price = order.total_price

        create_discount(
            product=product2, discount_percentage=Decimal("50"), is_active=True
        )
        order.refresh_from_db()

        assert order.total_price != old_total_price
        assert order.total_price == pytest.approx(
            Decimal("250") + Decimal("150.83")
        )

    def test_updated_discount_not_in_status_pending(
        self, create_product, create_order, create_discount
    ):
        product1 = create_product(name="Product1", price=Decimal("150.83"))
        product2 = create_product(name="Product2", price=Decimal("500"))
        order = create_order(
            products=[product1, product2], status=OrderStatusEnum.CONFIRMED.name
        )
        order.refresh_from_db()
        old_total_price = order.total_price

        create_discount(
            product=product2, discount_percentage=Decimal("50"), is_active=True
        )

        assert order.total_price == old_total_price

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
        ), f"Expected total price with discount to be {product1.price + product2.discounted_price},\
             but got {order.total_price}"

        discount_product2.delete()
        order.refresh_from_db()
        assert order.total_price == pytest.approx(
            product1.price + product2.price
        ), f"Expected total price when deleted discount to be {product1.price + product2.price}, \
             but got {order.total_price}"

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
        order.refresh_from_db()
        old_total_price = order.total_price

        product1.price = Decimal("199.99")
        create_discount(
            product=product2, discount_percentage=Decimal("50"), is_active=True
        )
        product1.save()

        assert order.total_price == old_total_price
        assert order.items.filter(
            product__name="Product1", price=Decimal("150.83")
        ).exists()
        assert order.items.filter(
            product__name="Product2", discount_percentage__isnull=True
        ).exists()

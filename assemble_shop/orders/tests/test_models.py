from decimal import Decimal

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

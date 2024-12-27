from decimal import Decimal

from django.utils import timezone

from assemble_shop.orders.forms import DiscountForm


class TestProductForm:
    def test_date_invalid(self, user, create_product):
        """
        Test that DiscountForm raises a validation error when the start_date
        is later than the end_date.
        """
        product = create_product()
        discount_data = {
            "created_by": user.pk,
            "product": product.pk,
            "discount_percentage": Decimal("99.99"),
            "start_date": timezone.now(),
            "end_date": (timezone.now() - timezone.timedelta(days=1)),  # type: ignore
        }
        discount_form = DiscountForm(data=discount_data)
        errors = discount_form.non_field_errors()

        assert not discount_form.is_valid()
        assert len(errors) == 1
        assert (
            str(errors[0])
            == "The start date cannot be later than the end date."
        )

    def test_overlapping_discounts(
        self, user, product_with_discount, create_discount
    ):
        """
        Test that DiscountForm raises a validation error when there is an overlapping discount
        for the same product.
        """
        discount_data = {
            "created_by": user.pk,
            "product": product_with_discount.pk,
            "discount_percentage": Decimal("99.99"),
            "start_date": timezone.now(),
            "end_date": (timezone.now() + timezone.timedelta(days=3)),  # type: ignore
        }
        discount_form = DiscountForm(data=discount_data)
        errors = discount_form.non_field_errors()

        assert not discount_form.is_valid()
        assert len(errors) == 1
        assert (
            str(errors[0])
            == "This product already has an overlapping discount."
        )

    def test_data_valid(self, user, product_with_discount):
        """
        Test that DiscountForm is valid when the discount data is correct.
        """
        discount_data = {
            "created_by": user.pk,
            "product": product_with_discount.pk,
            "discount_percentage": Decimal("99.99"),
            "start_date": (timezone.now() + timezone.timedelta(days=10)),  # type: ignore
            "end_date": (timezone.now() + timezone.timedelta(days=12)),  # type: ignore
        }
        discount_form = DiscountForm(data=discount_data)
        errors = discount_form.errors

        assert discount_form.is_valid()
        assert len(errors) == 0

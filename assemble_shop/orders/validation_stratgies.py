from abc import ABC, abstractmethod

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class ValidationStrategy(ABC):
    @abstractmethod
    def validate(self, data):
        pass


class ProductRequiredValidation(ValidationStrategy):
    def validate(self, data):
        if not data.get("product"):
            raise ValidationError(_("Field Product is required."))


class QuantityValidation(ValidationStrategy):
    def validate(self, data):
        if data.get("quantity", 0) < 1:
            raise ValidationError(
                _(
                    f"Quantity must be at least 1 for product {data.get('product')}."
                )
            )


class StockValidation(ValidationStrategy):
    def validate(self, data):
        product = data.get("product")
        if product and product.inventory < data.get("quantity", 0):
            raise ValidationError(
                _(
                    f"Insufficient stock for the selected product {product} quantity."
                )
            )

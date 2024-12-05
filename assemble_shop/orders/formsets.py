from django.forms import ValidationError
from django.forms.models import BaseInlineFormSet
from django.utils.translation import gettext_lazy as _

from assemble_shop.orders.validation_stratgies import (
    ProductRequiredValidation,
    QuantityValidation,
    StockValidation,
)


class OrderItemFormset(BaseInlineFormSet):
    def clean(self):
        super().clean()

        if not self.forms:
            raise ValidationError(
                _("You must add at least one product to your order.")
            )

        validations = [
            ProductRequiredValidation(),
            QuantityValidation(),
            StockValidation(),
        ]
        for form in self.forms:
            for validation_strategy in validations:
                validation_strategy.validate(data=form.cleaned_data)

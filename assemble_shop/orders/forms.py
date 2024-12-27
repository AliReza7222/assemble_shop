from django import forms

from assemble_shop.orders.models import Discount
from assemble_shop.orders.validation_stratgies import (
    ValidateNoOverlappingDiscounts,
    ValidateStartDateBeforeEndDate,
    ValidateStartDateNotInPast,
)


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data.update({"instance": self.instance})  # type: ignore
        validations = (
            ValidateStartDateNotInPast(),
            ValidateStartDateBeforeEndDate(),
            ValidateNoOverlappingDiscounts(),
        )
        for validation in validations:
            validation.validate(data=cleaned_data)

        del cleaned_data["instance"]  # type: ignore
        return cleaned_data

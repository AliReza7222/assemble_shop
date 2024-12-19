from django import forms
from django.utils.translation import gettext_lazy as _

from assemble_shop.orders.models import Discount


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("start_date") > cleaned_data.get("end_date"):  # type: ignore
            raise forms.ValidationError(
                _("The start date cannot be later than the end date.")
            )

        product = cleaned_data.get("product")  # type: ignore

        latest_discount = product.discounts.filter(  # type: ignore
            start_date__lte=cleaned_data.get("end_date"),  # type: ignore
            end_date__gte=cleaned_data.get("start_date"),  # type: ignore
        ).exclude(id=self.instance.id)

        if latest_discount.exists():
            raise forms.ValidationError(
                _("This product already has an overlapping discount.")
            )

        return cleaned_data

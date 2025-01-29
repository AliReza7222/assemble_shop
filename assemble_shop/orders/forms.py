from django import forms

from assemble_shop.orders.models import Discount
from assemble_shop.orders.validation_stratgies import (
    ValidateFileFormatExcel,
    ValidateFileSizeExcel,
    ValidateNoOverlappingDiscounts,
    ValidateStartDateBeforeEndDate,
)


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        if self.errors:
            raise forms.ValidationError("Please enter the correct data.")

        cleaned_data.update({"instance": self.instance})  # type: ignore
        validations = (
            ValidateStartDateBeforeEndDate(),
            ValidateNoOverlappingDiscounts(),
        )
        for validation in validations:
            validation.validate(data=cleaned_data)

        del cleaned_data["instance"]  # type: ignore
        return cleaned_data


class UploadFileForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"accept": ".xls,.xlsx"}),
        help_text=(
            "Please upload an Excel file (.xls or .xlsx) containing the required data.<br>"
            "The file should include the following headers in the exact order:<br>"
            "<ol>"
            "  <li><strong>name</strong></li>"
            "  <li><strong>price</strong></li>"
            "  <li><strong>description</strong></li>"
            "  <li><strong>inventory</strong></li>"
            "</ol>"
            "Ensure that the first row of the file contains these headers and subsequent rows "
            "contain the corresponding data. Files not following this format will be rejected."
        ),
    )

    def clean(self):
        data = self.cleaned_data

        validations = (
            ValidateFileFormatExcel(),
            ValidateFileSizeExcel(),
        )
        for validation in validations:
            validation.validate(data=data)

        return data

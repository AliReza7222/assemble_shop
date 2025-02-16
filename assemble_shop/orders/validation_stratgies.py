import mimetypes
import os
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
        quantity = data.get("quantity")
        if quantity is not None and quantity < 1:
            raise ValidationError(_("Quantity must be at least 1 for product."))


class StockValidation(ValidationStrategy):
    def validate(self, data):
        product = data.get("product")
        if product and product.inventory < data.get("quantity", 0):
            raise ValidationError(
                _(
                    f"Insufficient stock for the selected product {product} quantity."
                )
            )


class ValidateStartDateBeforeEndDate(ValidationStrategy):
    def validate(self, data):
        if data.get("start_date") > data.get("end_date"):
            raise ValidationError(
                _("The start date cannot be later than the end date.")
            )


class ValidateNoOverlappingDiscounts(ValidationStrategy):
    def validate(self, data):
        product = data.get("product")
        instance = data.get("instance")

        latest_discount = product.discounts.filter(
            start_date__lte=data.get("end_date"),
            end_date__gte=data.get("start_date"),
        ).exclude(id=instance.id)

        if latest_discount.exists():
            raise ValidationError(
                _("This product already has an overlapping discount.")
            )


class ValidateFileFormatExcel(ValidationStrategy):
    def validate(self, data):
        content_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        content_type_file, info = mimetypes.guess_type(data.name)
        name, file_format = os.path.splitext(data.name)

        if file_format.lower() != ".xlsx" or content_type != content_type_file:
            raise ValidationError(
                _("Invalid file format. Please upload an Excel file (.xlsx).")
            )


class ValidateFileSizeExcel(ValidationStrategy):
    def validate(self, data):
        max_size = 5 * 1024 * 1024
        if data.size > max_size:
            raise ValidationError(_("File size should not exceed 5MB."))

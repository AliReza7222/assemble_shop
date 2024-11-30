from django.contrib import admin

from assemble_shop.base.admin import BaseAdmin
from assemble_shop.base.enums import BaseFieldsEnum, BaseTitleEnum
from assemble_shop.orders.enums import *
from assemble_shop.orders.models import *


@admin.register(Product)
class ProductAdmin(BaseAdmin):
    list_display = ProductFieldsEnum.LIST_DISPLAY_FIELDS.value

    def get_readonly_fields(self, request, obj=None):
        return ProductFieldsEnum.READONLY_FIELDS.value + tuple(
            self.readonly_fields
        )

    def get_fieldsets(self, request, obj=None):
        return (
            (
                BaseTitleEnum.GENERAL.value,
                {"fields": ProductFieldsEnum.GENERAL_FIELDS.value},
            ),
            (BaseTitleEnum.INFO.value, {"fields": BaseFieldsEnum.BASE.value}),
        )


@admin.register(Order)
class OrderAdmin(BaseAdmin):
    list_display = OrderFieldsEnum.LIST_DISPLAY_FIELDS.value
    filter_horizontal = OrderFieldsEnum.FILTER_HORIZONTAL.value

    def get_readonly_fields(self, request, obj=None):
        return OrderFieldsEnum.READONLY_FIELDS.value + tuple(
            self.readonly_fields
        )

    def get_fieldsets(self, request, obj=None):
        return (
            (
                BaseTitleEnum.GENERAL.value,
                {"fields": OrderFieldsEnum.GENERAL_FIELDS.value},
            ),
            (
                OrderTitleEnum.TRACKING_CODE.value,
                {"fields": OrderFieldsEnum.TRACKING_FIELDS.value},
            ),
            (BaseTitleEnum.INFO.value, {"fields": BaseFieldsEnum.BASE.value}),
        )


@admin.register(Review)
class ReviewAdmin(BaseAdmin):
    list_display = ReviewFieldsEnum.LIST_DISPLAY_FIELDS.value

    def get_fieldsets(self, request, obj=None):
        return (
            (
                BaseTitleEnum.GENERAL.value,
                {"fields": ReviewFieldsEnum.GENERAL_FIELDS.value},
            ),
            (BaseTitleEnum.INFO.value, {"fields": BaseFieldsEnum.BASE.value}),
        )


@admin.register(Discount)
class DiscountAdmin(BaseAdmin):
    list_display = DiscountFieldsEnum.LIST_DISPLAY_FIELDS.value

    def get_fieldsets(self, request, obj=None):
        return (
            (
                BaseTitleEnum.GENERAL.value,
                {"fields": DiscountFieldsEnum.GENERAL_FIELDS.value},
            ),
            (BaseTitleEnum.INFO.value, {"fields": BaseFieldsEnum.BASE.value}),
        )

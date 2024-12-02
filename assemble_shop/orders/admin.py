from django.contrib import admin

from assemble_shop.base.admin import BaseAdmin
from assemble_shop.base.enums import BaseFieldsEnum, BaseTitleEnum
from assemble_shop.orders.enums import *
from assemble_shop.orders.forms import DiscountForm
from assemble_shop.orders.models import *


@admin.register(Product)
class ProductAdmin(BaseAdmin):
    list_display = ProductFieldsEnum.LIST_DISPLAY_FIELDS.value
    search_fields = ProductFieldsEnum.LIST_SEARCH_FIELDS.value

    def get_readonly_fields(self, request, obj=None):
        return ProductFieldsEnum.READONLY_FIELDS.value + tuple(
            self.readonly_fields
        )

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (
                BaseTitleEnum.GENERAL.value,
                {"fields": ProductFieldsEnum.GENERAL_FIELDS.value},
            ),
        )
        if obj.discount_now:
            fieldsets += (  # type: ignore
                (
                    ProductTitleEnum.DISCOUNT_INFO.value,
                    {"fields": ProductFieldsEnum.DISCOUNT_NOW_FIELDS.value},
                ),
            )
        fieldsets += (  # type: ignore
            (BaseTitleEnum.INFO.value, {"fields": BaseFieldsEnum.BASE.value}),
        )
        return fieldsets


@admin.register(Order)
class OrderAdmin(BaseAdmin):
    list_display = OrderFieldsEnum.LIST_DISPLAY_FIELDS.value
    filter_horizontal = OrderFieldsEnum.FILTER_HORIZONTAL.value
    search_fields = OrderFieldsEnum.LIST_SEARCH_FIELDS.value
    list_filter = OrderFieldsEnum.LIST_FILTER_FIELDS.value

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = OrderFieldsEnum.READONLY_FIELDS.value + tuple(
            self.readonly_fields
        )
        if request.user.is_customer:
            readonly_fields += ("status",)

        return readonly_fields

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_customer:
            return queryset.filter(created_by=request.user)
        return queryset

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (
                BaseTitleEnum.GENERAL.value,
                {
                    "fields": (
                        OrderFieldsEnum.GENERAL_FIELDS.value
                        if obj
                        else (OrderFieldsEnum.GENERAL_FIELDS.value[0],)
                    )
                },
            ),
        )
        if obj:
            fieldsets += (  # type: ignore
                (
                    OrderTitleEnum.TRACKING_CODE.value,
                    {"fields": OrderFieldsEnum.TRACKING_FIELDS.value},
                ),
                (
                    BaseTitleEnum.INFO.value,
                    {"fields": BaseFieldsEnum.BASE.value},
                ),
            )
        return fieldsets


@admin.register(Review)
class ReviewAdmin(BaseAdmin):
    list_display = ReviewFieldsEnum.LIST_DISPLAY_FIELDS.value
    search_fields = ReviewFieldsEnum.LIST_SEARCH_FIELDS.value

    def get_fieldsets(self, request, obj=None):
        return (
            (
                BaseTitleEnum.GENERAL.value,
                {"fields": ReviewFieldsEnum.GENERAL_FIELDS.value},
            ),
            (BaseTitleEnum.INFO.value, {"fields": BaseFieldsEnum.BASE.value}),
        )

    def has_change_permission(self, request, obj=None):
        if obj:
            return request.user == obj.created_by or request.user.is_superuser
        super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj:
            return request.user == obj.created_by or request.user.is_superuser
        super().has_delete_permission(request, obj)


@admin.register(Discount)
class DiscountAdmin(BaseAdmin):
    list_display = DiscountFieldsEnum.LIST_DISPLAY_FIELDS.value
    search_fields = DiscountFieldsEnum.LIST_SEARCH_FIELDS.value
    list_filter = DiscountFieldsEnum.LIST_FILTER_FIELDS.value
    form = DiscountForm

    def get_fieldsets(self, request, obj=None):
        return (
            (
                BaseTitleEnum.GENERAL.value,
                {"fields": DiscountFieldsEnum.GENERAL_FIELDS.value},
            ),
            (BaseTitleEnum.INFO.value, {"fields": BaseFieldsEnum.BASE.value}),
        )

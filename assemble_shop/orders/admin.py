from django.contrib import admin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from assemble_shop.base.admin import BaseAdmin
from assemble_shop.base.enums import BaseFieldsEnum, BaseTitleEnum
from assemble_shop.orders.enums import *
from assemble_shop.orders.forms import DiscountForm
from assemble_shop.orders.formsets import OrderItemFormset
from assemble_shop.orders.models import *


@admin.register(Product)
class ProductAdmin(BaseAdmin):
    list_display = ProductFieldsEnum.LIST_DISPLAY_FIELDS.value
    search_fields = ProductFieldsEnum.LIST_SEARCH_FIELDS.value

    def get_readonly_fields(self, request, obj=None):
        return ProductFieldsEnum.READONLY_FIELDS.value + self.readonly_fields

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (
                BaseTitleEnum.GENERAL.value,
                {"fields": ProductFieldsEnum.GENERAL_FIELDS.value},
            ),
        )
        if obj and obj.discount_now:
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


class OrderItemInline(admin.StackedInline):
    model = Order.products.through
    formset = OrderItemFormset
    readonly_fields = OrderItemFieldsEnum.TAGS.value
    autocomplete_fields = ("product",)
    extra = 0

    def get_fields(self, request, obj=None):
        return (
            OrderItemFieldsEnum.GENERAL_FIELDS.value
            + OrderItemFieldsEnum.TAGS.value
        )

    def has_change_permission(self, request, obj=None):
        return obj.is_pending_status if obj else True

    def has_add_permission(self, request, obj=None):
        return obj.is_pending_status if obj else True

    def has_delete_permission(self, request, obj=None):
        return obj.is_pending_status if obj else True

    @admin.display(description="Product Price")
    def product_price(self, obj):
        return obj.product.price

    @admin.display(description="Discounted Price")
    def product_discount(self, obj):
        return obj.product.discounted_price

    @admin.display(description="Discount Percentage")
    def discount_percentage(self, obj):
        discount_now = obj.product.discount_now
        return f"{discount_now.discount_percentage} %" if discount_now else None


@admin.register(Order)
class OrderAdmin(BaseAdmin):
    list_display = OrderFieldsEnum.LIST_DISPLAY_FIELDS.value
    search_fields = OrderFieldsEnum.LIST_SEARCH_FIELDS.value
    list_filter = OrderFieldsEnum.LIST_FILTER_FIELDS.value
    inlines = (OrderItemInline,)

    def has_delete_permission(self, request, obj=None):
        return obj.is_pending_status if obj else True

    def has_change_permission(self, request, obj=None):
        return obj.is_pending_status if obj else True

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = (
            OrderFieldsEnum.READONLY_FIELDS.value + self.readonly_fields
        )

        if request.user.is_customer:
            readonly_fields += ("status",)  # type: ignore

        return readonly_fields

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_customer:
            return queryset.filter(created_by=request.user)
        return queryset

    def changed_status_order(self, order, status):
        order.status = status
        order.save(update_fields=["status"])

    def regenerate_order_view(self, request, order_id):
        old_order = self.get_object(request, order_id)
        total_price = 0
        for item in old_order.items.all():  # type: ignore
            total_price += (
                item.product.price * item.quantity
                if not item.product.discounted_price
                else item.product.discounted_price * item.quantity
            )
        data = {
            "created_by": request.user,
            "updated_by": request.user,
            "total_price": total_price,
        }
        new_order = Order.objects.create(**data)
        new_order.products.set(old_order.products.all())  # type: ignore
        self.message_user(
            request, "Your order was successfully regenerated.", level="success"
        )
        return HttpResponseRedirect(
            reverse("admin:orders_order_change", args=(new_order.id,))
        )

    def completed_status_order_view(self, request, order_id):
        order = self.get_object(request, order_id)
        self.changed_status_order(order, OrderStatusEnum.COMPLETED.name)
        self.message_user(
            request, "Your order was successfully completed.", level="success"
        )
        return HttpResponseRedirect(request.headers.get("referer"))

    @transaction.atomic
    def confirimed_order_view(self, request, order_id):
        order = self.get_object(request, order_id)
        products_updated = []

        for item in order.items.select_related("product"):  # type: ignore
            if item.product.inventory < item.quantity:
                self.message_user(
                    request,
                    f"The stock of a {item.product} product is less than the quantity you selected.",
                    level="error",
                )
                return HttpResponseRedirect(request.headers.get("referer"))
            item.product.inventory -= item.quantity
            products_updated.append(item.product)
        Product.objects.bulk_update(products_updated, ["inventory"])

        self.changed_status_order(order, OrderStatusEnum.CONFIRMED.name)
        self.message_user(
            request, "Your order was successfully confirmed.", level="success"
        )
        return HttpResponseRedirect(request.headers.get("referer"))

    @transaction.atomic
    def canceled_order_view(self, request, order_id):
        order = self.get_object(request, order_id)
        products_updated = []

        for item in order.items.select_related("product"):  # type: ignore
            item.product.inventory += item.quantity
            products_updated.append(item.product)
        Product.objects.bulk_update(products_updated, ["inventory"])

        self.changed_status_order(order, OrderStatusEnum.CANCELED.name)
        self.message_user(
            request, "Your order was successfully canceled.", level="success"
        )
        return HttpResponseRedirect(request.headers.get("referer"))

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "<int:order_id>/finalize_order/",
                self.admin_site.admin_view(self.confirimed_order_view),
                name="orders_order_confirimed_order",
            ),
            path(
                "<int:order_id>/cancel_order/",
                self.admin_site.admin_view(self.canceled_order_view),
                name="orders_order_cancel_order",
            ),
            path(
                "<int:order_id>/complete_order/",
                self.admin_site.admin_view(self.completed_status_order_view),
                name="orders_order_complete_order",
            ),
            path(
                "<int:order_id>/regenerate_order/",
                self.admin_site.admin_view(self.regenerate_order_view),
                name="orders_order_regenerate_order",
            ),
        ]
        return custom_urls + urls

    def get_fieldsets(self, request, obj=None):
        fieldsets = ()
        if obj:
            fieldsets += (  # type: ignore
                (
                    BaseTitleEnum.GENERAL.value,
                    {"fields": OrderFieldsEnum.GENERAL_FIELDS.value},
                ),
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

    def save_model(self, request, obj, form, change):
        if obj.status != OrderStatusEnum.CONFIRMED.name:
            msg = f'Your products have only been selected , \
                    Please complete the order "{obj}" items to confirimed the order.'
            self.message_user(request, msg, level="warning")
        super().save_model(request, obj, form, change)

    def update_total_price_order(self, order, order_items_formset):
        total_price = 0
        for form in order_items_formset.forms:
            product = form.cleaned_data.get("product")
            quantity = form.cleaned_data.get("quantity")
            total_price += (
                product.price * quantity
                if not product.discounted_price
                else product.discounted_price * quantity
            )
        order.total_price = total_price
        order.save(update_fields=["total_price"])

    def save_related(self, request, form, formsets, change):
        form.save_m2m()
        order = form.instance
        for formset in formsets:
            if order.is_pending_status and isinstance(
                formset, OrderItemFormset
            ):
                self.update_total_price_order(formset.instance, formset)
            self.save_formset(request, form, formset, change=change)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["pend_status"] = OrderStatusEnum.PENDING.name
        extra_context.update(
            {
                "canceled_status": OrderStatusEnum.CANCELED.name,
                "confirmed_status": OrderStatusEnum.CONFIRMED.name,
                "completed_status": OrderStatusEnum.COMPLETED.name,
                "is_superior_group": request.user.is_superior_group,
            }
        )
        return super().change_view(request, object_id, form_url, extra_context)


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
            return (
                request.user == obj.created_by or request.user.is_superior_group
            )
        return True

    def has_delete_permission(self, request, obj=None):
        if obj:
            return (
                request.user == obj.created_by or request.user.is_superior_group
            )
        return True


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

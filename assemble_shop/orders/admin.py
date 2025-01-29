from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from assemble_shop.base.admin import BaseAdmin
from assemble_shop.base.enums import BaseFieldsEnum, BaseTitleEnum
from assemble_shop.orders.enums import *
from assemble_shop.orders.forms import DiscountForm, UploadFileForm
from assemble_shop.orders.formsets import OrderItemFormset
from assemble_shop.orders.models import *
from assemble_shop.orders.utils import (
    confirmed_order,
    get_extra_context_order,
    regenerate_order,
)
from assemble_shop.utils import excel_file


@admin.register(Product)
class ProductAdmin(BaseAdmin):
    list_display = ProductFieldsEnum.LIST_DISPLAY_FIELDS.value
    search_fields = ProductFieldsEnum.LIST_SEARCH_FIELDS.value

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + ProductFieldsEnum.READONLY_FIELDS.value

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (
                BaseTitleEnum.GENERAL.value,
                {"fields": ProductFieldsEnum.GENERAL_FIELDS.value},
            ),
        )
        if obj:
            if obj.discount_now:
                fieldsets += (  # type: ignore
                    (
                        ProductTitleEnum.DISCOUNT_INFO.value,
                        {"fields": ProductFieldsEnum.DISCOUNT_NOW_FIELDS.value},
                    ),
                )
            fieldsets += (  # type: ignore
                (
                    BaseTitleEnum.INFO.value,
                    {"fields": BaseFieldsEnum.BASE.value},
                ),
            )
        return fieldsets

    def save_products(self, products):
        Product.objects.bulk_create(products)

    def upload_file_to_storage(self, file, user):
        file_name = f"import_data_product/{user}/{timezone.now().strftime('%Y-%m-%d')}/{file.name}"
        default_storage.save(file_name, file)

    def process_uploaded_file(self, file, user):
        headers, rows = excel_file.get_data(file=file)
        expected_headers = ["name", "price", "description", "inventory"]

        if headers != expected_headers:
            raise ValidationError(
                _(
                    "Headers in the uploaded file are incorrect. "
                    f"Expected headers are: {', '.join(expected_headers)}. "
                    "Please ensure the file includes these headers in the exact order."
                )
            )

        for row in rows:
            yield Product(
                created_by=user,
                name=row[0],
                price=row[1],
                description=row[2] if row[2] else "",
                inventory=row[3],
            )

    def import_file_view(self, request):
        """
        Handles file upload and data import for products.
        """
        if request.method == "POST":
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                file = form.cleaned_data.get("file")
                try:
                    self.save_products(
                        products=list(
                            self.process_uploaded_file(file, request.user)
                        )
                    )
                    self.upload_file_to_storage(file, request.user)
                    self.message_user(
                        request,
                        "File imported successfully!",
                        level=messages.SUCCESS,
                    )

                except ValidationError as e:
                    form.add_error("file", e.message)

                except IntegrityError as e:
                    form.add_error("file", f"Database error: {str(e)}")

                except Exception:
                    form.add_error(
                        "file",
                        "An error occurred: Please select correct file.",
                    )
        else:
            form = UploadFileForm()

        admin_form = admin.helpers.AdminForm(  # type: ignore
            form,
            [("ImportFile", {"fields": ("file",)})],
            {},
            model_admin=self,
        )
        extra_context = {
            "adminform": admin_form,
            "show_save_and_continue": False,
            "errors": admin.helpers.AdminErrorList(form, []),  # type: ignore
        }
        return super().changeform_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "upload-file/",
                self.admin_site.admin_view(self.import_file_view),
                name="import_file_add_view",
            )
        ]

        return custom_urls + urls


class OrderItemInline(admin.StackedInline):
    model = Order.products.through
    formset = OrderItemFormset
    readonly_fields = OrderItemFieldsEnum.READONLY_FIELDS.value
    autocomplete_fields = ("product",)
    extra = 0

    def get_fields(self, request, obj=None):
        return (
            OrderItemFieldsEnum.GENERAL_FIELDS.value
            + OrderItemFieldsEnum.READONLY_FIELDS.value
        )

    def has_change_permission(self, request, obj=None):
        return obj.is_pending_status if obj else True

    def has_add_permission(self, request, obj=None):
        return obj.is_pending_status if obj else True

    def has_delete_permission(self, request, obj=None):
        return obj.is_pending_status if obj else True


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

    def _changed_status_order(self, request, order_id, status):
        order = self.get_object(request, order_id)
        order.status = status  # type: ignore
        order.save(update_fields=["status"])  # type: ignore
        self.message_user(
            request,
            f"Your order was successfully {status.title()}.",
            level="success",
        )
        return HttpResponseRedirect(request.headers.get("referer"))

    @transaction.atomic
    def regenerate_order_view(self, request, order_id):
        new_order = regenerate_order(order_id, request.user)

        self.message_user(
            request, "Your order was successfully regenerated.", level="success"
        )
        return HttpResponseRedirect(
            reverse("admin:orders_order_change", args=(new_order.id,))
        )

    def completed_status_order_view(self, request, order_id):
        return self._changed_status_order(
            request, order_id, OrderStatusEnum.COMPLETED.name
        )

    @transaction.atomic
    def confirmed_order_view(self, request, order_id):
        order = self.get_object(request, order_id)
        products_updated, error_messages = confirmed_order(order)  # type: ignore

        if error_messages:
            for msg in error_messages:
                self.message_user(request, msg, level="error")
            return HttpResponseRedirect(request.headers.get("referer"))

        Product.objects.bulk_update(products_updated, ["inventory"])

        return self._changed_status_order(
            request, order_id, OrderStatusEnum.CONFIRMED.name
        )

    @transaction.atomic
    def canceled_order_view(self, request, order_id):
        order = self.get_object(request, order_id)
        products_updated = []

        for item in order.items.select_related("product"):  # type: ignore
            item.product.inventory += item.quantity
            products_updated.append(item.product)
        Product.objects.bulk_update(products_updated, ["inventory"])

        return self._changed_status_order(
            request, order_id, OrderStatusEnum.CANCELED.name
        )

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "<int:order_id>/confirime_order/",
                self.admin_site.admin_view(self.confirmed_order_view),
                name="orders_order_confirmed_order",
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
        if obj.is_pending_status:
            msg = f'Your products have only been selected , \
                    Please complete the order "{obj}" items to confirimed the order.'
            self.message_user(request, msg, level="warning")
        super().save_model(request, obj, form, change)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = get_extra_context_order(extra_context, request.user)
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(Review)
class ReviewAdmin(BaseAdmin):
    list_display = ReviewFieldsEnum.LIST_DISPLAY_FIELDS.value
    search_fields = ReviewFieldsEnum.LIST_SEARCH_FIELDS.value
    autocomplete_fields = ("product",)

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (
                BaseTitleEnum.GENERAL.value,
                {"fields": ReviewFieldsEnum.GENERAL_FIELDS.value},
            ),
        )
        if obj:
            fieldsets += (  # type:ignore
                (
                    BaseTitleEnum.INFO.value,
                    {"fields": BaseFieldsEnum.BASE.value},
                ),
            )
        return fieldsets

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
    autocomplete_fields = ("product",)
    form = DiscountForm

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (
                BaseTitleEnum.GENERAL.value,
                {"fields": DiscountFieldsEnum.GENERAL_FIELDS.value},
            ),
        )
        if obj:
            fieldsets += (  # type: ignore
                (
                    BaseTitleEnum.INFO.value,
                    {"fields": BaseFieldsEnum.BASE.value},
                ),
            )
        return fieldsets

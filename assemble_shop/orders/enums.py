from assemble_shop.base.enums import BaseEnum
from assemble_shop.orders.fields import *


class OrderStatusEnum(BaseEnum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    CANCELED = "Canceled"


class OrderFieldsEnum(BaseEnum):
    GENERAL_FIELDS = ORDER_FIELDS
    LIST_DISPLAY_FIELDS = ORDER_LIST_DISPLAY_FIELDS
    FILTER_HORIZONTAL = ORDER_FILTER_HORIZONTAL
    TRACKING_FIELDS = ORDER_TRACKING_FIELDS
    READONLY_FIELDS = ORDER_READONLY_FIELDS


class OrderTitleEnum(BaseEnum):
    TRACKING_CODE = "Tracking Code"


class ProductTitleEnum(BaseEnum):
    pass


class ProductFieldsEnum(BaseEnum):
    GENERAL_FIELDS = PRODUCT_FIELDS
    LIST_DISPLAY_FIELDS = PRODUCT_LIST_DISPLAY_FIELDS
    READONLY_FIELDS = PRODUCT_READONLY_FIELDS


class ReviewFieldsEnum(BaseEnum):
    GENERAL_FIELDS = REVIEW_FIELDS
    LIST_DISPLAY_FIELDS = REVIEW_LIST_DISPLAY_FIELDS


class DiscountFieldsEnum(BaseEnum):
    GENERAL_FIELDS = DISCOUNT_FIELDS
    LIST_DISPLAY_FIELDS = DISCOUNT_LIST_DISPLAY_FIELDS

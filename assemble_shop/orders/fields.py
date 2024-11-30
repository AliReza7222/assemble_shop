# Product Fields
# ------------------------------------------------------------------------------
PRODUCT_FIELDS = (
    "name",
    "price",
    "inventory",
    "rating",
    "description",
)
PRODUCT_LIST_DISPLAY_FIELDS = (
    "name",
    "price",
    "inventory",
    "rating",
)
PRODUCT_READONLY_FIELDS = ("rating",)
# Order Fields
# ------------------------------------------------------------------------------
ORDER_FIELDS = (
    "customer",
    "products",
    "quantity",
    "status",
    "total_price",
)
ORDER_LIST_DISPLAY_FIELDS = ("customer", "quantity", "status", "total_price")
ORDER_FILTER_HORIZONTAL = ("products",)
ORDER_TRACKING_FIELDS = ("tracking_code",)
ORDER_READONLY_FIELDS = (
    "total_price",
    "quantity",
    "tracking_code",
)
# Review Fields
# ------------------------------------------------------------------------------
REVIEW_FIELDS = (
    "product",
    "rating",
    "comment",
)
REVIEW_LIST_DISPLAY_FIELDS = (
    "created_by",
    "product",
    "rating",
)
# Discount Fields
# ------------------------------------------------------------------------------
DISCOUNT_FIELDS = (
    "product",
    "discount_percentage",
    "start_date",
    "end_date",
    "is_active",
)
DISCOUNT_LIST_DISPLAY_FIELDS = (
    "product",
    "discount_percentage",
    "start_date",
    "end_date",
    "is_active",
)

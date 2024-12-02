# Product Fields
# ------------------------------------------------------------------------------
PRODUCT_FIELDS = (
    "name",
    "price",
    "discounted_price",
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
PRODUCT_TAGS = ("discounted_price",)
PRODUCT_LIST_SEARCH_FIELDS = ("name",)
PRODUCT_DISCOUNT_NOW_FIELDS = (
    "get_discount_percentage",
    "get_start_date",
    "get_end_date",
    "get_is_active",
)
PRODUCT_READONLY_FIELDS = ("rating",)
# Order Fields
# ------------------------------------------------------------------------------
ORDER_FIELDS = (
    "products",
    "quantity",
    "status",
    "total_price",
)
ORDER_LIST_DISPLAY_FIELDS = (
    "created_by",
    "total_price",
    "status",
    "quantity",
)
ORDER_FILTER_HORIZONTAL = ("products",)
ORDER_TRACKING_FIELDS = ("tracking_code",)
ORDER_LIST_SEARCH_FIELDS = ("created_by__email", "tracking_code")
ORDER_LIST_FILTER_FIELDS = ("status",)
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
REVIEW_LIST_SEARCH_FIELDS = ("product__name", "rating")
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
DISCOUNT_LIST_SEARCH_FIELDS = ("product__name",)
DISCOUNT_LIST_FILTER_FIELDS = ("is_active",)

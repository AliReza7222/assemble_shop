ADMIN = "Admin"
STOREMANAGER = "Store_Manager"
CUSTOMER = "Customer"

PERMISIONS = {
    ADMIN: [
        # Product
        "add_product",
        "view_product",
        "delete_product",
        "change_product",
        # Order
        "add_order",
        "view_order",
        "delete_order",
        "change_order",
        # Review
        "add_review",
        "view_review",
        "delete_review",
        "change_review",
        # Discount
        "add_discount",
        "view_discount",
        "delete_discount",
        "change_discount",
    ],
    STOREMANAGER: [
        # Product
        "add_product",
        "view_product",
        # Order
        "add_order",
        "view_order",
        # Review
        "add_review",
        "view_review",
        "change_review",
        "delete_review",
        # Discount
        "add_discount",
        "view_discount",
        "delete_discount",
        "change_discount",
    ],
    CUSTOMER: [
        # Product
        "view_product",
        # Order
        "add_order",
        "view_order",
        "change_order",
        # Review
        "add_review",
        "view_review",
        "delete_review",
        "change_review",
    ],
}

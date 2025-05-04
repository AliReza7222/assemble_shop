from django.urls import path

from assemble_shop.orders.api.views import (
    GetCustomersOrders,
    GetMonthlyIncome,
    GetTopRatedProducts,
    GetTopSelling,
)

app_name = "orders"
urlpatterns = [
    path("info-top-selling/", GetTopSelling.as_view(), name="info_top_selling"),
    path(
        "info-monthly-income/",
        GetMonthlyIncome.as_view(),
        name="info_monthly_income",
    ),
    path(
        "info-history-customers-orders/",
        GetCustomersOrders.as_view(),
        name="info_history_customers_orders",
    ),
    path(
        "info-top-rated-products/",
        GetTopRatedProducts.as_view(),
        name="info_top_products",
    ),
]

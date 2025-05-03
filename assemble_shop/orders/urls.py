from django.urls import path

from assemble_shop.orders.api.views import GetMonthlyIncome, GetTopSelling

app_name = "orders"
urlpatterns = [
    path("get_top_selling/", GetTopSelling.as_view(), name="get_top_selling"),
    path(
        "get_monthly_income/",
        GetMonthlyIncome.as_view(),
        name="get_monthly_income",
    ),
]

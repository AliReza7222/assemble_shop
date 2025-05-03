from django.urls import path

from assemble_shop.orders.api.views import GetTopSelling

app_name = "orders"
urlpatterns = [
    path("get_top_selling/", GetTopSelling.as_view(), name="get_top_selling"),
]

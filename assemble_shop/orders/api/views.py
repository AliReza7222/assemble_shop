from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from assemble_shop.base.pagination import BasePagination
from assemble_shop.orders.api.serializers import OrderSerializer
from assemble_shop.orders.services import OrderService

order_service = OrderService()


class GetTopSelling(GenericAPIView):
    http_method_names = ("get",)

    def get(self, request):
        return Response(
            order_service.get_top_selling(), status=status.HTTP_200_OK
        )


class GetMonthlyIncome(GenericAPIView):
    http_method_names = ("get",)

    def get(self, request):
        return Response(
            order_service.get_monthly_income(), status=status.HTTP_200_OK
        )


class GetCustomersOrders(ListAPIView):
    http_method_names = ("get",)
    permission_classes = (IsAuthenticated,)
    pagination_class = BasePagination
    serializer_class = OrderSerializer

    def get_queryset(self):
        return order_service.get_customers_orders(
            customer_id=self.request.user.id
        )

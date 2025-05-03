from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

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

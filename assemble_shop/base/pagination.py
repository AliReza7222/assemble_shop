from rest_framework import pagination
from rest_framework.response import Response


class BasePagination(pagination.PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 10

    def get_paginated_response(self, data):
        return Response(
            {
                "links": {
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
                "count": self.page.paginator.count,  # type: ignore
                "page": self.page.number,  # type: ignore
                "page_size": self.get_page_size(self.request),  # type: ignore
                "results": data,
            }
        )

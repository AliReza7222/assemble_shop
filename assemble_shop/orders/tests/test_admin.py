from decimal import Decimal

from django.urls import reverse
from rest_framework import status

from assemble_shop.orders.models import Product


class TestProductAdmin:
    def data_product(self):
        return {"name": "Product1", "price": Decimal("100"), "inventory": 10}

    def assert_post_request_permission(
        self, client, url, data, result_http_status, product_id=None
    ):
        url = reverse(url, args=(product_id,)) if product_id else reverse(url)
        response = client.post(url, data=data)

        assert response.status_code == result_http_status

    def test_admin_group_permissions(self, client, user_admin):
        client.force_login(user_admin)

        # Test permssion add for admin user
        product_count_before = Product.objects.count()
        self.assert_post_request_permission(
            client,
            url="admin:orders_product_add",
            data=self.data_product(),
            result_http_status=status.HTTP_302_FOUND,
        )
        assert Product.objects.count() == product_count_before + 1

        # Test permssion delete for admin user
        product_count_before = Product.objects.count()
        product = Product.objects.first()
        self.assert_post_request_permission(
            client,
            url="admin:orders_product_delete",
            data={"post": "yes"},
            result_http_status=status.HTTP_302_FOUND,
            product_id=product.id,  # type: ignore
        )
        assert Product.objects.count() == product_count_before - 1

    def test_storemanager_group_permissions(
        self, client, user_storemanager, create_product
    ):
        client.force_login(user_storemanager)

        # Test permssion add for admin user
        product_count_before = Product.objects.count()
        self.assert_post_request_permission(
            client,
            url="admin:orders_product_add",
            data=self.data_product(),
            result_http_status=status.HTTP_302_FOUND,
        )
        assert Product.objects.count() == product_count_before + 1

        # Test permssion delete for admin user
        product = create_product()
        self.assert_post_request_permission(
            client,
            url="admin:orders_product_delete",
            data={"post": "yes"},
            result_http_status=status.HTTP_403_FORBIDDEN,
            product_id=product.id,
        )
        assert Product.objects.filter(name=product.name).exists()

    def test_customer_group_permissions(
        self, client, user_customer, create_product
    ):
        client.force_login(user_customer)

        # Test permssion add for admin user
        self.assert_post_request_permission(
            client,
            url="admin:orders_product_add",
            data=self.data_product(),
            result_http_status=status.HTTP_403_FORBIDDEN,
        )

        # Test permssion delete for admin user
        product = create_product()
        self.assert_post_request_permission(
            client,
            url="admin:orders_product_delete",
            data={"post": "yes"},
            result_http_status=status.HTTP_403_FORBIDDEN,
            product_id=product.id,
        )
        assert Product.objects.filter(name=product.name).exists()

from http import HTTPStatus
from io import BytesIO

import openpyxl
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from assemble_shop.orders.enums import OrderStatusEnum
from assemble_shop.orders.models import Order, Product, Review


class TestReviewAdmin:
    def request_change(self, client, review, data):
        url = reverse("admin:orders_review_change", args=(review.id,))
        return client.post(url, data=data)

    def request_delete(self, client, review):
        url = reverse("admin:orders_review_delete", args=(review.id,))
        return client.post(url, data={"post": "yes"})

    def test_change_and_delete_non_owner(
        self, client, create_user, create_product, create_review
    ):
        """
        Test that a non-owner user cannot change or delete another user's review.
        """
        user1 = create_user(is_staff=True)
        user2 = create_user(is_staff=True)

        client.force_login(user1)

        # Test change review
        product = create_product()
        review = create_review(product=product, created_by=user2, rating=4)
        response = self.request_change(client, review, data={"rating": 1})
        assert response.status_code == HTTPStatus.FORBIDDEN

        # Test delete review
        review_count_before = Review.objects.count()
        response = self.request_delete(client, review)
        assert response.status_code == HTTPStatus.FORBIDDEN
        assert Review.objects.count() == review_count_before

    def test_change_and_delete_for_owner(
        self, client, create_user, create_product, create_review
    ):
        """
        Test that the owner of the review can change and delete their own review.
        """
        user = create_user(is_staff=True)
        client.force_login(user)

        # Test change review
        product = create_product()
        review = create_review(product=product, created_by=user, rating=4)
        response = self.request_change(client, review, data={"rating": 1})
        assert response.status_code == HTTPStatus.OK

        # Test delete review
        review_count_before = Review.objects.count()
        response = self.request_delete(client, review)
        assert response.status_code == HTTPStatus.FOUND
        assert Review.objects.count() == review_count_before - 1

    def test_change_and_delete_for_superior_user(
        self, client, create_user, user_admin, create_product, create_review
    ):
        """
        Test that a superior user can change and delete any review.
        Superior Users are in group Admin and superuser.
        """
        user = create_user(is_staff=True)
        client.force_login(user_admin)

        # Test change review
        product = create_product()
        review = create_review(product=product, created_by=user, rating=4)
        response = self.request_change(client, review, data={"rating": 1})
        assert response.status_code == HTTPStatus.OK

        # Test delete review
        review_count_before = Review.objects.count()
        response = self.request_delete(client, review)
        assert response.status_code == HTTPStatus.FOUND
        assert Review.objects.count() == review_count_before - 1


class TestOrderItemInlineAdmin:
    def test_add_items_in_pending(
        self, client_authenticated, data_orderitem_inline
    ):
        """
        Test that items can be added to an order when the order status is PENDING.
        """
        product, order, data = data_orderitem_inline()
        url = reverse("admin:orders_order_change", args=(order.pk,))

        response = client_authenticated.post(url, data=data)

        assert response.status_code == HTTPStatus.FOUND
        assert order.items.filter(product=product).exists()

    def test_add_items_not_in_pending(
        self, client_authenticated, data_orderitem_inline
    ):
        """
        Test that items cannot be added to an order when the order status is not PENDING.
        """
        product, order, data = data_orderitem_inline(
            status=OrderStatusEnum.CONFIRMED.name
        )
        url = reverse("admin:orders_order_change", args=(order.pk,))

        response = client_authenticated.post(url, data=data)

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert not order.items.filter(product=product).exists()

    def test_change_items_in_pending(
        self, client_authenticated, data_orderitem_inline
    ):
        """
        Test that items can be updated in an order when the order status is PENDING.
        """
        product, order, data = data_orderitem_inline(has_items=True)
        item = order.items.get(product=product)
        url = reverse("admin:orders_order_change", args=(order.pk,))
        data.update(
            {
                "items-INITIAL_FORMS": "1",
                "items-0-id": item.id,
                "items-0-quantity": 7,
            }
        )

        response = client_authenticated.post(url, data=data)

        assert response.status_code == HTTPStatus.FOUND
        assert order.items.filter(product__id=product.id, quantity=7).exists()

    def test_change_items_not_in_pending(
        self, client_authenticated, data_orderitem_inline
    ):
        """
        Test that items cannot be updated in an order when the order status is not PENDING.
        """
        product, order, data = data_orderitem_inline(
            status=OrderStatusEnum.CONFIRMED.name, has_items=True
        )
        item = order.items.get(product=product)
        url = reverse("admin:orders_order_change", args=(order.pk,))
        data.update(
            {
                "items-INITIAL_FORMS": "1",
                "items-0-id": item.id,
                "items-0-quantity": 7,
            }
        )

        response = client_authenticated.post(url, data=data)

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert not order.items.filter(
            product__id=product.id, quantity=7
        ).exists()

    def test_delete_items_in_pending(
        self, client_authenticated, data_orderitem_inline
    ):
        """
        Test that items can be deleted from an order when the order status is PENDING.
        """
        product, order, data = data_orderitem_inline(has_items=True)
        item = order.items.get(product=product)
        url = reverse("admin:orders_order_change", args=(order.pk,))
        data.update(
            {
                "items-INITIAL_FORMS": "1",
                "items-0-id": item.id,
                "items-0-DELETE": "on",
            }
        )

        response = client_authenticated.post(url, data=data)

        assert response.status_code == HTTPStatus.FOUND
        assert not order.items.filter(product__id=product.id).exists()

    def test_delete_items_not_in_pending(
        self, client_authenticated, data_orderitem_inline
    ):
        """
        Test that items cannot be deleted from an order when the order status is not PENDING.
        """
        product, order, data = data_orderitem_inline(
            status=OrderStatusEnum.CONFIRMED.name, has_items=True
        )
        item = order.items.get(product=product)
        url = reverse("admin:orders_order_change", args=(order.pk,))
        data.update(
            {
                "items-INITIAL_FORMS": "1",
                "items-0-id": item.id,
                "items-0-DELETE": "on",
            }
        )

        response = client_authenticated.post(url, data=data)

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert order.items.filter(product__id=product.id).exists()


class TestOrderViewsAdmin:
    def refresh_database(self, instances: list) -> None:
        for instance in instances:
            instance.refresh_from_db()

    def test_confirm_and_cancel_view(
        self, client_authenticated, create_order, create_product
    ):
        """
        Test the behavior of confirming and canceling an order.
        Verifies that order status changes correctly and inventory is updated.
        """
        product1 = create_product(name="ProductTest1", inventory=2)
        product2 = create_product(name="ProductTest2", inventory=1)
        order = create_order(products=[product1, product2])
        confirm_url = reverse(
            "admin:orders_order_confirmed_order", args=(order.id,)
        )

        # Confirm order
        confirm_response = client_authenticated.get(confirm_url)
        self.refresh_database(instances=[order, product1, product2])

        assert (
            confirm_response.status_code == HTTPStatus.FOUND
        ), f"Expected 302 Found for confirmation, got {confirm_response.status_code}."
        assert (
            order.status == OrderStatusEnum.CONFIRMED.name
        ), "Order status not updated to CONFIRMED."
        assert (
            product1.inventory == 1
        ), "Product1 inventory not reduced correctly after confirmation."
        assert (
            product2.inventory == 0
        ), "Product2 inventory not reduced correctly after confirmation."

        # Cancel order
        cancel_url = reverse(
            "admin:orders_order_cancel_order", args=(order.id,)
        )
        cancel_response = client_authenticated.get(cancel_url)
        self.refresh_database(instances=[order, product1, product2])

        assert (
            cancel_response.status_code == HTTPStatus.FOUND
        ), f"Expected 302 Found for cancellation, got {cancel_response.status_code}."
        assert (
            order.status == OrderStatusEnum.CANCELED.name
        ), "Order status not updated to CANCELED."
        assert (
            product1.inventory == 2
        ), "Product1 inventory not restored correctly after cancellation."
        assert (
            product2.inventory == 1
        ), "Product2 inventory not restored correctly after cancellation."

    def test_completed_view(self, client_authenticated, create_order):
        """
        Test completing an order via the admin view.
        Ensures the order status updates to 'COMPLETED'.
        """
        order = create_order()
        url = reverse("admin:orders_order_complete_order", args=(order.id,))

        response = client_authenticated.get(url)
        self.refresh_database(instances=[order])

        assert (
            response.status_code == HTTPStatus.FOUND
        ), f"Expected 302 Found, got {response.status_code}."
        assert (
            order.status == OrderStatusEnum.COMPLETED.name
        ), "Order status not updated to COMPLETED."

    def test_regenerate_view(
        self, client_authenticated, create_order, create_product
    ):
        """
        Test regenerating an order through the admin view.
        Confirms that a new order is created with identical items and 'PENDING' status.
        """
        product1 = create_product(name="ProductTest1", inventory=2)
        product2 = create_product(name="ProductTest2", inventory=1)
        old_order = create_order(
            products=[product1, product2], status=OrderStatusEnum.COMPLETED
        )
        url = reverse(
            "admin:orders_order_regenerate_order", args=(old_order.id,)
        )

        response = client_authenticated.get(url)
        self.refresh_database(instances=[old_order])

        # Ensure a new order is created with the same items
        new_order = Order.objects.exclude(id=old_order.id).get()
        old_items = list(old_order.items.values("product", "quantity"))
        new_items = list(new_order.items.values("product", "quantity"))

        assert (
            response.status_code == HTTPStatus.FOUND
        ), f"Expected 302 Found, got {response.status_code}."
        assert (
            Order.objects.count() == 2
        ), "Expected a new order to be created, but the count didn't increase."
        assert (
            new_order.status == OrderStatusEnum.PENDING.name
        ), "New order status not set to PENDING."
        assert (
            new_items == old_items
        ), "Items in the new order do not match the original order."


@pytest.mark.django_db
class TestProductAdmin:
    def create_file_excel(self, headers, rows):
        """
        Creates an in-memory Excel file with the given headers and rows.
        """
        output = BytesIO()
        wb = openpyxl.Workbook()
        ws = wb.active

        ws.append(headers)

        for row in rows:
            ws.append(row)

        wb.save(output)
        output.seek(0)

        return output

    def test_successful_import_file(self, client, user_admin):
        """
        Tests that a valid Excel file successfully imports products into the database.
        """
        client.force_login(user_admin)

        headers = ["name", "price", "description", "inventory"]
        rows = [
            ["Product A", 10.5, "Description A", 100],
            ["Product B", 20.0, "Description B", 50],
        ]
        excel_file = self.create_file_excel(headers, rows)
        uploaded_file = SimpleUploadedFile(
            "products.xlsx",
            excel_file.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        url = reverse("admin:import_file_add_view")
        client.post(url, {"file": uploaded_file}, follow=True)

        assert Product.objects.count() == 2
        assert Product.objects.filter(name="Product A").exists()
        assert Product.objects.filter(name="Product B").exists()

    def test_invalid_headers(self, client, user_admin):
        """
        Tests that an Excel file with incorrect headers does not import any products.
        """
        client.force_login(user_admin)

        headers = [
            "wrong_name",
            "wrong_price",
            "wrong_description",
            "wrong_inventory",
        ]
        rows = [
            ["Product A", 10.5, "Description A", 100],
            ["Product B", 20.0, "Description B", 50],
        ]
        excel_file = self.create_file_excel(headers, rows)
        uploaded_file = SimpleUploadedFile(
            "products.xlsx",
            excel_file.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        url = reverse("admin:import_file_add_view")
        client.post(url, {"file": uploaded_file}, follow=True)

        assert Product.objects.count() == 0

    def test_invalid_arrange_headers(self, client, user_admin):
        """
        Tests that an Excel file with invalid arrange headers does not import any products.
        """
        client.force_login(user_admin)

        headers = ["price", "name", "inventory", "description"]
        rows = [
            [10.5, "Product A", 100, "Description A"],
            [20.0, "Product B", 50, "Description B"],
        ]
        excel_file = self.create_file_excel(headers, rows)
        uploaded_file = SimpleUploadedFile(
            "products.xlsx",
            excel_file.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        url = reverse("admin:import_file_add_view")
        client.post(url, {"file": uploaded_file}, follow=True)

        assert Product.objects.count() == 0

    def test_empty_file(self, client, user_admin):
        """
        Tests that an empty Excel file does not import any products.
        """
        client.force_login(user_admin)

        uploaded_file = SimpleUploadedFile(
            "products.xlsx",
            b"",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        url = reverse("admin:import_file_add_view")
        client.post(url, {"file": uploaded_file}, follow=True)

        assert Product.objects.count() == 0

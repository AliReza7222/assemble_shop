from http import HTTPStatus

from django.urls import reverse

from assemble_shop.orders.models import Review


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

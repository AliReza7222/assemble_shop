from decimal import Decimal


class TestProductSignal:
    def test_no_reviews(self, create_product):
        product = create_product()

        assert product.rating is None

    def test_multiple_ratings(self, faker, create_product, create_review):
        expected_rating = Decimal("0")
        num_review = 5
        faker.seed_instance(42)
        product = create_product()

        for _ in range(num_review):
            rating = faker.random_int(min=1, max=5)
            create_review(product=product, rating=rating)
            expected_rating += rating

        expected_rating = (expected_rating / num_review).quantize(
            Decimal("0.01")
        )

        assert product.rating == expected_rating

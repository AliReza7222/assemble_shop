class TestOrderItemFormset:
    def test_without_items_validation(self, orderitem_inline_formset):
        """
        Test that the formset raises an error when no items are added to the order.
        """
        formset = orderitem_inline_formset(data={})
        msg_error = "You must add at least one product to your order."
        assert not formset.is_valid()
        assert msg_error in str(formset.non_form_errors())

    def test_stock_validation(self, orderitem_inline_formset, create_product):
        """
        Test that the formset raises an error if the quantity exceeds available stock.
        """
        product = create_product(inventory=5)
        data = {
            "items-TOTAL_FORMS": "1",
            "items-INITIAL_FORMS": "0",
            "items-0-product": product.pk,
            "items-0-quantity": 10,
        }
        formset = orderitem_inline_formset(data=data)
        msg_error = (
            f"Insufficient stock for the selected product {product} quantity."
        )

        assert not formset.is_valid()
        assert msg_error in str(formset.errors[0].get("__all__", []))

    def test_quantity_validation(
        self, orderitem_inline_formset, create_product
    ):
        """
        Test that the formset raises an error if the quantity is less than 1.
        """
        product = create_product()
        data = {
            "items-TOTAL_FORMS": "1",
            "items-INITIAL_FORMS": "0",
            "items-0-product": product.pk,
            "items-0-quantity": 0,
        }
        formset = orderitem_inline_formset(data=data)
        msg_error = f"Quantity must be at least 1 for product {product.name}."

        assert not formset.is_valid()
        assert msg_error in str(formset.errors[0].get("__all__", []))

    def test_exists_product_validation(self, orderitem_inline_formset):
        """
        Test that the formset raises an error if a product is not selected.
        """
        data = {
            "items-TOTAL_FORMS": "1",
            "items-INITIAL_FORMS": "0",
            "items-0-quantity": 1,
        }
        formset = orderitem_inline_formset(data=data)
        msg_error = "Field Product is required."

        assert not formset.is_valid()
        assert msg_error in str(formset.errors[0].get("__all__", []))

    def test_create_valid_items(self, orderitem_inline_formset, create_product):
        """
        Test that the formset successfully creates valid order items.
        """
        product1 = create_product(name="ProductTest1", inventory=10)
        product2 = create_product(name="ProductTest2", inventory=10)
        data = {
            "items-TOTAL_FORMS": "2",
            "items-INITIAL_FORMS": "0",
            "items-0-product": product1.pk,
            "items-0-quantity": 1,
            "items-1-product": product2.pk,
            "items-1-quantity": 1,
        }
        formset = orderitem_inline_formset(data=data)
        order = formset.instance

        assert formset.is_valid()
        formset.save()
        assert order.items.count() == 2

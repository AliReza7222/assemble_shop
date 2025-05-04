from rest_framework import serializers

from assemble_shop.orders.models import Order, OrderItem, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "price",
            "inventory",
            "description",
            "rating",
            "image",
        )


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product",
            "order_id",
            "discount_percentage",
            "quantity",
            "price",
            "created_at",
        )


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "created_by_id",
            "created_at",
            "total_price",
            "tracking_code",
            "status",
            "items",
        )

from rest_framework import serializers

from .models import DiscountCode, Invoice, Order, OrderItem

class CartAddSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)


class CartUpdateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=0)


class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)


class CheckoutSerializer(serializers.Serializer):
    discount_code = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
    )


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )
    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "quantity",
            "unit_price",
            "subtotal",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user_id",
            "total_amount",
            "discount_amount",
            "final_amount",
            "status",
            "created_at",
            "items",
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "user_id",
            "created_at",
            "order",
        ]

class DiscountCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountCode
        fields = [
            "id",
            "code",
            "discount_percent",
            "max_uses",
            "used_count",
            "expires_at",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "used_count",
            "created_at",
            "updated_at",
        ]
from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product


class OrderItemSerializer(serializers.Serializer):
    """
    Handles a single line item in an order.
    Used for INPUT only — validates product exists and has enough stock.
    """
    product_id = serializers.IntegerField()
    quantity   = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(pk=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError(
                f"Product with id {value} does not exist."
            )
        return value

    def validate(self, data):
        product  = Product.objects.get(pk=data['product_id'])
        quantity = data['quantity']

        if product.stock < quantity:
            raise serializers.ValidationError({
                'quantity': (
                    f"Not enough stock for '{product.name}'. "
                    f"Available: {product.stock}, Requested: {quantity}."
                )
            })
        return data


class OrderItemDetailSerializer(serializers.ModelSerializer):
    """
    Used for OUTPUT only — shows full item detail in order response.
    Nested inside OrderDetailSerializer.
    """
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model  = OrderItem
        fields = [
            'id',
            'product',
            'product_name',
            'quantity',
            'unit_price',
            'subtotal'
        ]


class OrderSerializer(serializers.Serializer):
    """
    INPUT serializer — accepts a list of items to create an order.

    Expected request body:
    {
        "items": [
            { "product_id": 1, "quantity": 2 },
            { "product_id": 3, "quantity": 1 }
        ]
    }
    """
    items = OrderItemSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                "Order must contain at least one item."
            )

        # Check for duplicate product_ids in same order
        product_ids = [item['product_id'] for item in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError(
                "Duplicate products found. Adjust quantity instead."
            )
        return value


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    OUTPUT serializer — shapes the full order response including nested items.
    """
    items       = OrderItemDetailSerializer(many=True, read_only=True)
    user_email  = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model  = Order
        fields = [
            'id',
            'user_email',
            'status',
            'total_price',
            'payment_reference',
            'items',
            'created_at',
            'updated_at',
        ]
# apps/cart/serializers.py

from rest_framework import serializers
from .models import Cart, CartItem, SavedCart
from menu.serializers import FoodListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items."""
    
    food = FoodListSerializer(read_only=True)
    food_id = serializers.IntegerField(write_only=True)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = (
            'id', 'food', 'food_id', 'quantity', 'unit_price', 'total_price',
            'price_snapshot', 'selected_variant', 'selected_addons', 'notes',
            'added_at', 'updated_at'
        )
        read_only_fields = ('id', 'price_snapshot', 'added_at', 'updated_at')
    
    def validate_quantity(self, value):
        """Validate quantity is positive."""
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value
    
    def validate_food_id(self, value):
        """Validate food exists and is available."""
        from menu.models import Food
        
        try:
            food = Food.objects.get(id=value)
            if not food.is_available:
                raise serializers.ValidationError("This food item is currently unavailable.")
        except Food.DoesNotExist:
            raise serializers.ValidationError("Food item does not exist.")
        
        return value


class CartSerializer(serializers.ModelSerializer):
    """Serializer for cart."""
    
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = (
            'id', 'user', 'is_active', 'items', 'total_items',
            'subtotal', 'total', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart."""
    
    food_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(default=1, min_value=1)
    selected_variant = serializers.CharField(required=False, allow_blank=True)
    selected_addons = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_food_id(self, value):
        """Validate food exists and is available."""
        from menu.models import Food
        
        try:
            food = Food.objects.get(id=value)
            if not food.is_available:
                raise serializers.ValidationError("This food item is currently unavailable.")
        except Food.DoesNotExist:
            raise serializers.ValidationError("Food item does not exist.")
        
        return value


class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart items."""
    
    quantity = serializers.IntegerField(required=False, min_value=1)
    selected_variant = serializers.CharField(required=False, allow_blank=True)
    selected_addons = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class SavedCartSerializer(serializers.ModelSerializer):
    """Serializer for saved carts."""
    
    items = CartItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = SavedCart
        fields = ('id', 'user', 'name', 'items', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class MergeCartSerializer(serializers.Serializer):
    """Serializer for merging anonymous cart with user cart."""
    
    anonymous_items = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
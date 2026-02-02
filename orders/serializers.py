# apps/orders/serializers.py

from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory
from menu.serializers import FoodListSerializer
from reviews.models import Review


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""
    
    food = FoodListSerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    # 1. Add the field definition
    has_reviewed = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = (
            'id', 'food', 'food_name', 'food_price', 'quantity',
            'selected_variant', 'selected_addons', 'notes', 'total_price',
            'has_reviewed'  # 2. Add to fields list
        )
        read_only_fields = ('id', 'food_name', 'food_price')

    def get_has_reviewed(self, obj):
        """Check if the user has already reviewed this item in this order."""
        try:
            # We need the request context to know WHO is asking
            request = self.context.get('request')
            if not request or not request.user.is_authenticated:
                return False
            
            user = request.user
            
            # Check if a review exists for this specific order + food + user combo
            return Review.objects.filter(
                order=obj.order, 
                food=obj.food, 
                user=user
            ).exists()
            
        except (AttributeError, KeyError):
            # Fallback for safety if context is missing
            return False


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for order status history."""

    changed_by_email = serializers.EmailField(
        source='changed_by.email', 
        read_only=True, 
        allow_null=True
    )
    
    class Meta:
        model = OrderStatusHistory
        fields = ('id', 'old_status', 'new_status', 'changed_by_email', 'notes', 'created_at')
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders."""
    
    items = OrderItemSerializer(many=True, read_only=True)
    
    status_history = OrderStatusHistorySerializer(
        many=True, 
        read_only=True
    )

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.first_name', read_only=True)
    
    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'user', 'user_email', 'user_name',
            'delivery_address', 'phone_number', 'delivery_notes',
            'status', 'payment_status', 'payment_reference',
            'total_amount', 'paid_amount', 'is_paid',
            'items_count', 'items', 'status_history',
            'admin_notes', 'created_at', 'updated_at',
            'paid_at', 'shipped_at', 'completed_at'
        )
        read_only_fields = (
            'id', 'order_number', 'user', 'total_amount', 'items_count',
            'is_paid', 'created_at', 'updated_at', 'paid_at',
            'shipped_at', 'completed_at', 'status_history'
        )

class CreateOrderSerializer(serializers.ModelSerializer):
    """Serializer for creating orders from cart."""
    
    # Add 'note' as a write-only field to accept what the frontend sends
    note = serializers.CharField(required=False, write_only=True, allow_blank=True)

    class Meta:
        model = Order
        fields = ('delivery_address', 'phone_number', 'delivery_notes', 'note')
    
    def validate(self, attrs):
        """Validate order data."""
        if not attrs.get('delivery_address'):
            raise serializers.ValidationError({"delivery_address": "Delivery address is required."})
        
        if not attrs.get('phone_number'):
            raise serializers.ValidationError({"phone_number": "Phone number is required for delivery."})
        
        return attrs
    
    def create(self, validated_data):
        """Create order from user's cart."""
        request = self.context.get('request')
        user = request.user
        
        # 1. HANDLE NOTES LOGIC (The Fix)
        # Check 'delivery_notes' first, fallback to 'note', default to empty string
        delivery_instruction = validated_data.get('delivery_notes') or validated_data.get('note') or ''

        # Get user's active cart
        from cart.models import Cart
        try:
            cart = Cart.objects.get(user=user, is_active=True)
        except Cart.DoesNotExist:
            raise serializers.ValidationError({"cart": "No active cart found."})
        
        if cart.items.count() == 0:
            raise serializers.ValidationError({"cart": "Cart is empty."})
        
        # Calculate total amount
        total_amount = cart.total
        
        # Create order
        order = Order.objects.create(
            user=user,
            delivery_address=validated_data['delivery_address'],
            phone_number=validated_data['phone_number'],
            delivery_notes=delivery_instruction,
            total_amount=total_amount,
            items_count=cart.total_items
        )
        
        # Create order items (Bulk Create for speed)
        order_items = []
        for cart_item in cart.items.all():
            order_items.append(OrderItem(
                order=order,
                food=cart_item.food,
                food_name=cart_item.food.name,
                food_price=cart_item.food.current_price,
                quantity=cart_item.quantity,
                selected_variant=cart_item.selected_variant,
                selected_addons=cart_item.selected_addons,
                notes=cart_item.notes
            ))
        
        if order_items:
            OrderItem.objects.bulk_create(order_items)
        
        # Clear the cart
        cart.items.all().delete()
        
        return order


class UpdateOrderStatusSerializer(serializers.Serializer):
    """Serializer for updating order status (admin only)."""
    
    status = serializers.ChoiceField(choices=Order.ORDER_STATUS)
    admin_notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_status(self, value):
        """Validate status transition."""
        order = self.context.get('order')
        
        if order.status == 'completed':
            raise serializers.ValidationError("Cannot change status of a completed order.")
        
        if order.status == 'cancelled':
            raise serializers.ValidationError("Cannot change status of a cancelled order.")
        
        return value


class PaymentInitSerializer(serializers.Serializer):
    """Serializer for payment initialization."""
    
    order_id = serializers.IntegerField(required=True)
    
    def validate_order_id(self, value):
        """Validate order exists and can be paid."""
        try:
            order = Order.objects.get(id=value)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")
        
        if order.is_paid:
            raise serializers.ValidationError("Order is already paid.")
        
        if order.status == 'cancelled':
            raise serializers.ValidationError("Cannot pay for a cancelled order.")
        
        return value


class PaystackWebhookSerializer(serializers.Serializer):
    """Serializer for Paystack webhook data."""
    
    event = serializers.CharField()
    data = serializers.DictField()
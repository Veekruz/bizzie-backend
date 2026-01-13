# apps/payments/serializers.py
from rest_framework import serializers
from .models import Payment
from orders.models import Order


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Payment
        fields = (
            'payment_id', 'reference', 'order', 'order_number', 
            'user', 'user_email', 'amount', 'currency', 'status',
            'paystack_authorization_url', 'created_at', 'paid_at',
            'is_successful'
        )
        read_only_fields = fields


class InitializePaymentSerializer(serializers.Serializer):
    """Serializer for initializing payment."""
    
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


class VerifyPaymentSerializer(serializers.Serializer):
    """Serializer for verifying payment."""
    
    reference = serializers.CharField(required=True)
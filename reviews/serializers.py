# apps/reviews/serializers.py
from rest_framework import serializers
from .models import Review
from orders.serializers import OrderSerializer
from menu.serializers import FoodListSerializer


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model."""
    
    order_details = OrderSerializer(source='order', read_only=True)
    food_details = FoodListSerializer(source='food', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.first_name', read_only=True)
    
    class Meta:
        model = Review
        fields = (
            'id', 'order', 'order_details', 'user', 'user_email', 'user_name',
            'food', 'food_details', 'rating', 'comment', 'is_approved',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class CreateReviewSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews."""
    
    class Meta:
        model = Review
        fields = ('order', 'food', 'rating', 'comment')
    
    def validate(self, attrs):
        order = attrs['order']
        user = self.context['request'].user
        
        # Validate order belongs to user
        if order.user != user:
            raise serializers.ValidationError({
                'order': 'You can only review your own orders.'
            })
        
        # Validate order is completed
        if order.status != 'completed':
            raise serializers.ValidationError({
                'order': 'You can only review completed orders.'
            })
        
        # Validate food is in the order
        if not order.items.filter(food=attrs['food']).exists():
            raise serializers.ValidationError({
                'food': 'This food item is not in your order.'
            })
        
        # Check if review already exists for this food in this order
        if Review.objects.filter(order=order, food=attrs['food'], user=user).exists():
            raise serializers.ValidationError({
                'review': 'You have already reviewed this food item from this order.'
            })
        
        return attrs
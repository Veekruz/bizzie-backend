# apps/menu/serializers.py

from rest_framework import serializers
from .models import Category, Food, FoodVariant, FoodAddon
from django.utils.text import Truncator


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    
    food_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'image', 'display_order', 
                 'is_active', 'food_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at', 'food_count')
    
    def get_food_count(self, obj):
        return obj.foods.filter(is_available=True).count()


class FoodVariantSerializer(serializers.ModelSerializer):
    """Serializer for FoodVariant model."""
    
    class Meta:
        model = FoodVariant
        fields = ('id', 'name', 'price_adjustment', 'is_available')
        read_only_fields = ('id',)


class FoodAddonSerializer(serializers.ModelSerializer):
    """Serializer for FoodAddon model."""
    
    class Meta:
        model = FoodAddon
        fields = ('id', 'name', 'price', 'is_available')
        read_only_fields = ('id',)


class FoodListSerializer(serializers.ModelSerializer):
    """Serializer for listing food items (limited fields)."""
    
    category = CategorySerializer(read_only=True)
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_on_sale = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    short_description = serializers.SerializerMethodField()
    
    class Meta:
        model = Food
        fields = ('id', 'name', 'short_description', 'current_price', 'discount_price',
                 'is_on_sale', 'discount_percentage', 'image', 'category', 
                 'preparation_time', 'is_available', 'popularity_score')
        read_only_fields = fields
    
    def get_short_description(self, obj):
        return Truncator(obj.description).chars(100)


class FoodDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed food view."""
    
    category = CategorySerializer(read_only=True)
    created_by = serializers.StringRelatedField()
    updated_by = serializers.StringRelatedField()
    variants = FoodVariantSerializer(many=True, read_only=True)
    addons = FoodAddonSerializer(many=True, read_only=True)
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_on_sale = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Food
        fields = (
            'id', 'name', 'description', 'price', 'discount_price', 'current_price',
            'is_on_sale', 'discount_percentage', 'category', 'image', 'image_2', 'image_3',
            'created_by', 'updated_by', 'preparation_time', 'calories', 'is_vegetarian',
            'is_spicy', 'is_available', 'stock_quantity', 'variants', 'addons',
            'popularity_score', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'current_price',
                           'is_on_sale', 'discount_percentage', 'created_by')


class FoodCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating food items (admin only)."""
    
    class Meta:
        model = Food
        fields = (
            'name', 'description', 'price', 'discount_price', 'category',
            'image', 'image_2', 'image_3', 'preparation_time', 'calories',
            'is_vegetarian', 'is_spicy', 'is_available', 'stock_quantity',
            'display_order'
        )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields optional for updates
        if self.instance:  # This is an update
            for field in self.fields:
                self.fields[field].required = False
    
    def create(self, validated_data):
        # Set the created_by field to current user (admin)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Set the updated_by field to current user (admin)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)
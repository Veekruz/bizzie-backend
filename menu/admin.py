# apps/menu/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Food, FoodVariant, FoodAddon


class FoodVariantInline(admin.TabularInline):
    """Inline admin for FoodVariant."""
    
    model = FoodVariant
    extra = 1
    fields = ('name', 'price_adjustment', 'is_available')


class FoodAddonInline(admin.TabularInline):
    """Inline admin for FoodAddon."""
    
    model = FoodAddon
    extra = 1
    fields = ('name', 'price', 'is_available')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model."""
    
    list_display = ('name', 'display_order', 'is_active', 'food_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('display_order', 'is_active')
    prepopulated_fields = {'name': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'food_count')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'image', 'display_order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def food_count(self, obj):
        return obj.foods.count()
    food_count.short_description = 'Food Items'


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    """Admin interface for Food model."""
    
    list_display = ('name', 'category', 'current_price', 'is_available', 
                   'stock_quantity', 'created_by', 'created_at')
    list_filter = ('is_available', 'category', 'is_vegetarian', 'is_spicy', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_available', 'stock_quantity')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by',
                      'current_price', 'is_on_sale', 'discount_percentage', 'popularity_score')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'image', 'image_2', 'image_3')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price', 'current_price', 'is_on_sale', 'discount_percentage')
        }),
        ('Details', {
            'fields': ('preparation_time', 'calories', 'is_vegetarian', 'is_spicy')
        }),
        ('Inventory', {
            'fields': ('is_available', 'stock_quantity', 'display_order', 'popularity_score')
        }),
        ('Admin', {
            'fields': ('created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [FoodVariantInline, FoodAddonInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new
            obj.created_by = request.user
        else:  # If updating
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image Preview'


@admin.register(FoodVariant)
class FoodVariantAdmin(admin.ModelAdmin):
    """Admin interface for FoodVariant model."""
    
    list_display = ('food', 'name', 'price_adjustment', 'is_available')
    list_filter = ('is_available', 'food__category')
    search_fields = ('food__name', 'name')
    list_editable = ('is_available', 'price_adjustment')


@admin.register(FoodAddon)
class FoodAddonAdmin(admin.ModelAdmin):
    """Admin interface for FoodAddon model."""
    
    list_display = ('food', 'name', 'price', 'is_available')
    list_filter = ('is_available', 'food__category')
    search_fields = ('food__name', 'name')
    list_editable = ('is_available', 'price')
# apps/cart/admin.py

from django.contrib import admin
from .models import Cart, CartItem, SavedCart


class CartItemInline(admin.TabularInline):
    """Inline admin for CartItem."""
    
    model = CartItem
    extra = 0
    readonly_fields = ('price_snapshot', 'added_at', 'updated_at')
    fields = ('food', 'quantity', 'price_snapshot', 'selected_variant', 'notes')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin interface for Cart model."""
    
    list_display = ('id', 'user', 'is_active', 'total_items', 'subtotal', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'user__first_name')
    readonly_fields = ('created_at', 'updated_at', 'total_items', 'subtotal', 'total')
    inlines = [CartItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'is_active')
        }),
        ('Cart Summary', {
            'fields': ('total_items', 'subtotal', 'total'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Admin interface for CartItem model."""
    
    list_display = ('id', 'cart', 'food', 'quantity', 'unit_price', 'total_price', 'added_at')
    list_filter = ('added_at', 'cart__user')
    search_fields = ('food__name', 'cart__user__email', 'notes')
    readonly_fields = ('price_snapshot', 'added_at', 'updated_at', 'unit_price', 'total_price')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('cart', 'food', 'quantity')
        }),
        ('Pricing', {
            'fields': ('price_snapshot', 'unit_price', 'total_price')
        }),
        ('Options', {
            'fields': ('selected_variant', 'selected_addons', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('added_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SavedCart)
class SavedCartAdmin(admin.ModelAdmin):
    """Admin interface for SavedCart model."""
    
    list_display = ('id', 'user', 'name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'name')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('items',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name')
        }),
        ('Items', {
            'fields': ('items',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
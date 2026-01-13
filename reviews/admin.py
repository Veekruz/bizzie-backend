# apps/reviews/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin interface for Review model."""
    
    list_display = ('id', 'user_email', 'food_name', 'rating_stars', 'is_approved_badge', 'created_at', 'order_number')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('user__email', 'food__name', 'comment', 'order__order_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Review Information', {
            'fields': ('order', 'user', 'food', 'rating', 'comment', 'is_approved')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def food_name(self, obj):
        return obj.food.name
    food_name.short_description = 'Food'
    
    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = 'Order #'
    
    def rating_stars(self, obj):
        stars = '⭐' * obj.rating
        return format_html('<span style="color: gold;">{}</span>', stars)
    rating_stars.short_description = 'Rating'
    
    def is_approved_badge(self, obj):
        if obj.is_approved:
            return format_html(
                '<span style="background-color: green; color: white; padding: 2px 8px; border-radius: 10px;">Approved</span>'
            )
        return format_html(
            '<span style="background-color: orange; color: white; padding: 2px 8px; border-radius: 10px;">Pending</span>'
        )
    is_approved_badge.short_description = 'Status'
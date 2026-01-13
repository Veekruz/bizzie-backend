# apps/payments/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model."""
    
    list_display = (
        'reference', 'order_number', 'user_email', 
        'amount_display', 'status_badge', 'created_at', 'paid_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('reference', 'order__order_number', 'user__email')
    readonly_fields = ('payment_id', 'reference', 'created_at', 'updated_at', 'paid_at')
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_id', 'reference', 'order', 'user', 'amount', 'currency', 'status')
        }),
        ('Paystack Data', {
            'fields': ('paystack_authorization_url', 'paystack_access_code'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = 'Order #'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Customer'
    
    def amount_display(self, obj):
        return f"₦{obj.amount}"
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'successful': 'green',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 10px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
# apps/orders/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    """Inline admin for OrderItem."""
    
    model = OrderItem
    extra = 0
    readonly_fields = ('food_name', 'food_price', 'total_price')
    fields = ('food', 'food_name', 'food_price', 'quantity', 'total_price', 'notes')
    
    def total_price(self, obj):
        return f"₦{obj.total_price}"
    total_price.short_description = 'Total'


class OrderStatusHistoryInline(admin.TabularInline):
    """Inline admin for OrderStatusHistory."""
    
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('changed_by', 'created_at')
    fields = ('old_status', 'new_status', 'changed_by', 'notes', 'created_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for Order model."""
    
    list_display = ('order_number', 'user_email', 'status_badge', 'payment_status_badge', 
                   'total_amount', 'created_at', 'action_buttons')
    list_filter = ('status', 'payment_status', 'created_at', 'is_paid')
    search_fields = ('order_number', 'user__email', 'user__first_name', 'delivery_address')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'paid_at', 
                      'shipped_at', 'completed_at', 'total_amount', 'items_count')
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status', 'is_paid')
        }),
        ('Delivery Information', {
            'fields': ('delivery_address', 'phone_number', 'delivery_notes')
        }),
        ('Payment Information', {
            'fields': ('total_amount', 'paid_amount', 'payment_reference', 'payment_method')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'shipped_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Customer Email'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'shipped': 'blue',
            'completed': 'green',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 10px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def payment_status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'paid': 'green',
            'failed': 'red',
            'refunded': 'gray',
        }
        color = colors.get(obj.payment_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 10px;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Payment'
    
    def action_buttons(self, obj):
        buttons = []
        if obj.status == 'pending':
            buttons.append(f'<a href="/admin/orders/order/{obj.id}/change/?status=shipped" class="button">Mark as Shipped</a>')
        elif obj.status == 'shipped':
            buttons.append(f'<a href="/admin/orders/order/{obj.id}/change/?status=completed" class="button">Mark as Completed</a>')
        return format_html(' '.join(buttons))
    action_buttons.short_description = 'Actions'
    
    def changelist_view(self, request, extra_context=None):
        # Add statistics to admin list view
        if extra_context is None:
            extra_context = {}
        
        from django.db.models import Count, Sum
        from django.utils import timezone
        from datetime import timedelta
        
        # Order statistics
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        today = timezone.now().date()
        today_orders = Order.objects.filter(created_at__date=today).count()
        
        # Revenue statistics
        paid_orders = Order.objects.filter(is_paid=True)
        total_revenue = paid_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        extra_context.update({
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'today_orders': today_orders,
            'total_revenue': total_revenue,
        })
        
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin interface for OrderItem model."""
    
    list_display = ('id', 'order_number', 'food_name', 'quantity', 'food_price', 'total_price', 'order_status')
    list_filter = ('order__status',)
    search_fields = ('order__order_number', 'food_name', 'order__user__email')
    readonly_fields = ('food_name', 'food_price', 'total_price')
    
    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = 'Order #'
    
    def order_status(self, obj):
        return obj.order.get_status_display()
    order_status.short_description = 'Order Status'
    
    def total_price(self, obj):
        return f"₦{obj.total_price}"
    total_price.short_description = 'Total'


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """Admin interface for OrderStatusHistory model."""
    
    list_display = ('order_number', 'old_status', 'new_status', 'changed_by_email', 'created_at')
    list_filter = ('created_at', 'new_status')
    search_fields = ('order__order_number', 'changed_by__email', 'notes')
    readonly_fields = ('order', 'old_status', 'new_status', 'changed_by', 'created_at')
    
    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = 'Order #'
    
    def changed_by_email(self, obj):
        return obj.changed_by.email if obj.changed_by else 'System'
    changed_by_email.short_description = 'Changed By'
# apps/users/admin_dashboard.py (optional)

from django.contrib import admin
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import User


class UserDashboardAdmin(admin.ModelAdmin):
    """Custom admin dashboard for user analytics."""
    
    def changelist_view(self, request, extra_context=None):
        # Get default response
        response = super().changelist_view(request, extra_context=extra_context)
        
        # Add custom statistics to context
        if extra_context is None:
            extra_context = {}
        
        # User statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        staff_users = User.objects.filter(is_staff=True).count()
        
        # New users in last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        new_users_week = User.objects.filter(created_at__gte=week_ago).count()
        
        # Add statistics to context
        extra_context.update({
            'total_users': total_users,
            'active_users': active_users,
            'staff_users': staff_users,
            'new_users_week': new_users_week,
        })
        
        # Update response context
        response.context_data.update(extra_context)
        return response
    
    # Add this to the list_display
    list_display = ('email', 'first_name', 'phone_number', 'is_staff', 'is_active', 'created_at', 'user_orders_count')
    
    def user_orders_count(self, obj):
        # This will show order count for each user (we'll implement this later)
        return 0
    user_orders_count.short_description = 'Orders Count'
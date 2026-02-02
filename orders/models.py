# apps/orders/models.py

import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from menu.models import Food
from cart.models import Cart, CartItem


class Order(models.Model):
    """Order model for food orders."""
    
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    # Order identification
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    
    # Delivery information (entered at checkout)
    delivery_address = models.TextField()
    phone_number = models.CharField(max_length=15)
    delivery_notes = models.TextField(blank=True, null=True)
    
    # Order status
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Payment information
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, default='paystack')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Order details
    items_count = models.PositiveIntegerField(default=0)
    is_paid = models.BooleanField(default=False)
    
    # Admin notes
    admin_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        """Generate order number if not set."""
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Generate unique order number."""
        import random
        import string
        prefix = "ORD"
        timestamp = self.created_at.strftime('%Y%m%d') if self.created_at else '00000000'
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}{timestamp}{random_str}"
    
    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled."""
        return self.status == 'pending' and not self.is_paid
    
    @property
    def is_delivered(self):
        """Check if order is delivered."""
        return self.status == 'completed'
    
    def mark_as_paid(self, payment_reference=None):
        """Mark order as paid."""
        from django.utils import timezone
        
        self.payment_status = 'paid'
        self.is_paid = True
        self.paid_amount = self.total_amount
        self.paid_at = timezone.now()
        
        if payment_reference:
            self.payment_reference = payment_reference
        
        self.save()
    
    def update_status(self, new_status, admin_notes=None):
        """Update order status with timestamp."""
        from django.utils import timezone
        
        old_status = self.status
        self.status = new_status
        
        if new_status == 'shipped' and old_status != 'shipped':
            self.shipped_at = timezone.now()
        elif new_status == 'completed' and old_status != 'completed':
            self.completed_at = timezone.now()
        
        if admin_notes:
            self.admin_notes = admin_notes
        
        self.save()
        
        return True


class OrderItem(models.Model):
    """Individual items in an order."""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    food = models.ForeignKey(
        Food,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )
    
    food_name = models.CharField(max_length=200)  # Snapshot of food name
    food_price = models.DecimalField(max_digits=10, decimal_places=2)  # Snapshot of price
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    # Variants and addons
    selected_variant = models.CharField(max_length=100, blank=True, null=True)
    selected_addons = models.JSONField(default=list, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.quantity}x {self.food_name} in Order #{self.order.order_number}"
    
    @property
    def total_price(self):
        """Calculate total price for this item."""
        return self.quantity * float(self.food_price)


class OrderStatusHistory(models.Model):
    """Track order status changes."""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    
    # Who changed the status
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Order Status History'
    
    def __str__(self):
        return f"Order #{self.order.order_number}: {self.old_status} → {self.new_status}"
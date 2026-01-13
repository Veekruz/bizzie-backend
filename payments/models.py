# apps/payments/models.py
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from orders.models import Order


class Payment(models.Model):
    """Payment model to track payment transactions."""
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    )
    
    # Payment identification
    payment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    reference = models.CharField(max_length=100, unique=True)  # Paystack reference
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='NGN')
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    # Paystack data
    paystack_authorization_url = models.URLField(max_length=500, blank=True, null=True)
    paystack_access_code = models.CharField(max_length=100, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['order']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Payment {self.reference} - {self.status}"
    
    @property
    def is_successful(self):
        return self.status == 'successful'
    
    def mark_as_successful(self, metadata=None):
        """Mark payment as successful."""
        self.status = 'successful'
        self.paid_at = timezone.now()
        self.save()
        
        # Also update the order
        self.order.mark_as_paid(self.reference)
    
    def mark_as_failed(self, reason=""):
        """Mark payment as failed."""
        self.status = 'failed'
        self.save()
# apps/reviews/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from orders.models import Order
from menu.models import Food


class Review(models.Model):
    """Review model for completed orders."""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='review'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    food = models.ForeignKey(
        Food,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    comment = models.TextField()
    is_approved = models.BooleanField(default=True)  # Admin can moderate
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['order', 'user', 'food']  # One review per food per order
    
    def __str__(self):
        return f"Review by {self.user.email} - {self.rating} stars"
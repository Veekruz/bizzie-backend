# apps/cart/models.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from menu.models import Food


class Cart(models.Model):
    """Main cart model for users."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts'
    )
    
    # Cart status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'is_active']
    
    def __str__(self):
        return f"Cart #{self.id} - {self.user.email}"
    
    @property
    def total_items(self):
        """Return total number of items in cart."""
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0
    
    @property
    def subtotal(self):
        """Calculate subtotal of all items in cart."""
        total = 0
        for item in self.items.all():
            total += item.total_price
        return total
    
    @property
    def total(self):
        """Calculate total price (subtotal + tax + delivery - discounts)."""
        # For now, just return subtotal. Can add tax/delivery/discounts later.
        return self.subtotal


class CartItem(models.Model):
    """Individual items in the cart."""
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    food = models.ForeignKey(
        Food,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    
    # Price at time of adding to cart (snapshot)
    price_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price of the food when added to cart"
    )
    
    # Optional: Selected variant and addons
    selected_variant = models.CharField(max_length=100, blank=True, null=True)
    selected_addons = models.JSONField(default=list, blank=True)
    
    # Notes from customer
    notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-added_at']
        unique_together = ['cart', 'food']  # One food type per cart
    
    def __str__(self):
        return f"{self.quantity}x {self.food.name} in Cart #{self.cart.id}"
    
    @property
    def unit_price(self):
        """Return current unit price (discounted if available)."""
        return self.food.current_price
    
    @property
    def total_price(self):
        """Calculate total price for this item (quantity * unit price)."""
        return self.quantity * float(self.unit_price)
    
    def save(self, *args, **kwargs):
        """Save price snapshot when adding to cart."""
        if not self.price_snapshot:
            self.price_snapshot = self.food.current_price
        super().save(*args, **kwargs)


class SavedCart(models.Model):
    """Saved carts for later (wishlist/quick reorder)."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_carts'
    )
    
    name = models.CharField(max_length=200, default="My Saved Cart")
    
    items = models.ManyToManyField(
        CartItem,
        related_name='saved_in_carts',
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Saved Cart: {self.name} - {self.user.email}"
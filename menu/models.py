# apps/menu/models.py

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """Food category model (e.g., Pizza, Burgers, Drinks)."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    
    # Ordering field for display priority
    display_order = models.PositiveIntegerField(default=0)
    
    # Active status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self):
        return self.name


class Food(models.Model):
    """Food item model."""
    
    # Food basic info
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Discounted price if any"
    )
    
    # Category
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='foods'
    )
    
    # Images
    image = models.ImageField(upload_to='food_images/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='food_images/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='food_images/', blank=True, null=True)
    
    # Admin who created/updated the food
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_foods',
        limit_choices_to={'is_staff': True}  # Only staff can create foods
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_foods',
        limit_choices_to={'is_staff': True}
    )
    
    # Food details
    preparation_time = models.PositiveIntegerField(
        default=15,
        help_text="Preparation time in minutes"
    )
    calories = models.PositiveIntegerField(blank=True, null=True)
    is_vegetarian = models.BooleanField(default=False)
    is_spicy = models.BooleanField(default=False)
    
    # Availability
    is_available = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=100)
    
    # Ordering and popularity
    display_order = models.PositiveIntegerField(default=0)
    popularity_score = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-popularity_score', 'name']
        verbose_name = _('food')
        verbose_name_plural = _('foods')
        indexes = [
            models.Index(fields=['is_available', 'category']),
            models.Index(fields=['price']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.name
    
    @property
    def current_price(self):
        """Return discounted price if available, else regular price."""
        return self.discount_price if self.discount_price else self.price
    
    @property
    def is_on_sale(self):
        """Check if food is on discount."""
        return self.discount_price is not None and self.discount_price < self.price
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage if on sale."""
        if self.is_on_sale:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0


class FoodVariant(models.Model):
    """Variants for food items (e.g., size, spice level)."""
    
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100)  # e.g., "Small", "Medium", "Extra Spicy"
    price_adjustment = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Additional price for this variant"
    )
    is_available = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['food', 'name']
    
    def __str__(self):
        return f"{self.food.name} - {self.name}"


class FoodAddon(models.Model):
    """Addons for food items (e.g., extra cheese, extra sauce)."""
    
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='addons')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['food', 'name']
    
    def __str__(self):
        return f"{self.food.name} - {self.name}"
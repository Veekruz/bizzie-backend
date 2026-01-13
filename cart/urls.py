# apps/cart/urls.py

from django.urls import path
from .views import (
    CartView,
    AddToCartView,
    UpdateCartItemView,
    RemoveCartItemView,
    ClearCartView,
    SaveCartView,
    LoadSavedCartView,
    SavedCartListView,
    SavedCartDetailView,
    CartSummaryView,
)

urlpatterns = [
    # Main cart endpoints
    path('', CartView.as_view(), name='cart'),
    path('add/', AddToCartView.as_view(), name='add-to-cart'),
    path('summary/', CartSummaryView.as_view(), name='cart-summary'),
    path('clear/', ClearCartView.as_view(), name='clear-cart'),
    
    # Cart item management
    path('items/<int:item_id>/update/', UpdateCartItemView.as_view(), name='update-cart-item'),
    path('items/<int:item_id>/remove/', RemoveCartItemView.as_view(), name='remove-cart-item'),
    
    # Saved carts
    path('save/', SaveCartView.as_view(), name='save-cart'),
    path('saved/', SavedCartListView.as_view(), name='saved-carts'),
    path('saved/<int:saved_cart_id>/load/', LoadSavedCartView.as_view(), name='load-saved-cart'),
    path('saved/<int:id>/', SavedCartDetailView.as_view(), name='saved-cart-detail'),
]
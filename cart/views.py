# apps/cart/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, ValidationError

from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Cart, CartItem, SavedCart
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
    SavedCartSerializer
)
from menu.models import Food


class CartView(generics.RetrieveAPIView):
    """View to get user's active cart."""
    
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Get or create user's active cart."""
        cart, created = Cart.objects.get_or_create(
            user=self.request.user,
            is_active=True
        )
        return cart


class AddToCartView(APIView):
    """View to add items to cart."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        
        if serializer.is_valid():
            food_id = serializer.validated_data['food_id']
            quantity = serializer.validated_data['quantity']
            selected_variant = serializer.validated_data.get('selected_variant', '')
            selected_addons = serializer.validated_data.get('selected_addons', [])
            notes = serializer.validated_data.get('notes', '')
            
            # Get or create user's active cart
            cart, created = Cart.objects.get_or_create(
                user=request.user,
                is_active=True
            )
            
            # Get the food item
            food = Food.objects.get(id=food_id)
            
            # Check if item already exists in cart
            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                food=food,
                defaults={
                    'quantity': quantity,
                    'selected_variant': selected_variant,
                    'selected_addons': selected_addons,
                    'notes': notes
                }
            )
            
            if not item_created:
                # Update quantity if item already exists
                cart_item.quantity += quantity
                cart_item.selected_variant = selected_variant or cart_item.selected_variant
                cart_item.selected_addons = selected_addons or cart_item.selected_addons
                cart_item.notes = notes or cart_item.notes
                cart_item.save()
            
            cart_serializer = CartSerializer(cart)
            
            message = "Added to cart" if item_created else "Cart updated"
            return Response({
                'message': message,
                'cart': cart_serializer.data,
                'item': CartItemSerializer(cart_item).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateCartItemView(APIView):
    """View to update cart item quantity or details."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, item_id):
        cart = get_object_or_404(Cart, user=request.user, is_active=True)
        
        try:
            cart_item = cart.items.get(id=item_id)
        except CartItem.DoesNotExist:
            raise NotFound("Cart item not found.")
        
        serializer = UpdateCartItemSerializer(data=request.data, partial=True)
        
        if serializer.is_valid():
            quantity = serializer.validated_data.get('quantity')
            selected_variant = serializer.validated_data.get('selected_variant')
            selected_addons = serializer.validated_data.get('selected_addons')
            notes = serializer.validated_data.get('notes')
            
            if quantity is not None:
                cart_item.quantity = quantity
            
            if selected_variant is not None:
                cart_item.selected_variant = selected_variant
            
            if selected_addons is not None:
                cart_item.selected_addons = selected_addons
            
            if notes is not None:
                cart_item.notes = notes
            
            cart_item.save()
            
            cart_serializer = CartSerializer(cart)
            return Response({
                'message': 'Cart item updated',
                'cart': cart_serializer.data,
                'item': CartItemSerializer(cart_item).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RemoveCartItemView(APIView):
    """View to remove item from cart."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, item_id):
        cart = get_object_or_404(Cart, user=request.user, is_active=True)
        
        try:
            cart_item = cart.items.get(id=item_id)
        except CartItem.DoesNotExist:
            raise NotFound("Cart item not found.")
        
        item_name = cart_item.food.name
        cart_item.delete()
        
        cart_serializer = CartSerializer(cart)
        return Response({
            'message': f'{item_name} removed from cart',
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)


class ClearCartView(APIView):
    """View to clear all items from cart."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request):
        cart = get_object_or_404(Cart, user=request.user, is_active=True)
        
        item_count = cart.items.count()
        cart.items.all().delete()
        
        cart_serializer = CartSerializer(cart)
        return Response({
            'message': f'Cart cleared ({item_count} items removed)',
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)


class SaveCartView(APIView):
    """View to save current cart for later."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user, is_active=True)
        
        if cart.items.count() == 0:
            return Response({
                'error': 'Cannot save an empty cart'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        name = request.data.get('name', 'My Saved Cart')
        
        # Create saved cart
        saved_cart = SavedCart.objects.create(
            user=request.user,
            name=name
        )
        
        # Create new cart items for the saved cart (not just references)
        for item in cart.items.all():
            # Create a new cart item for the saved cart
            new_item = CartItem.objects.create(
                cart=cart,  # This creates a reference, but that's okay
                food=item.food,
                quantity=item.quantity,
                selected_variant=item.selected_variant,
                selected_addons=item.selected_addons,
                notes=item.notes,
                price_snapshot=item.price_snapshot
            )
            saved_cart.items.add(new_item)
        
        serializer = SavedCartSerializer(saved_cart)
        return Response({
            'message': 'Cart saved successfully',
            'saved_cart': serializer.data
        }, status=status.HTTP_201_CREATED)


class LoadSavedCartView(APIView):
    """View to load a saved cart into active cart."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, saved_cart_id):
        saved_cart = get_object_or_404(
            SavedCart,
            id=saved_cart_id,
            user=request.user
        )
        
        cart, created = Cart.objects.get_or_create(
            user=request.user,
            is_active=True
        )
        
        # Clear current cart
        cart.items.all().delete()
        
        # Add items from saved cart
        added_items = []
        for saved_item in saved_cart.items.all():
            # Check if food still exists and is available
            if saved_item.food and saved_item.food.is_available:
                # Create new cart item from saved item
                cart_item = CartItem.objects.create(
                    cart=cart,
                    food=saved_item.food,
                    quantity=saved_item.quantity,
                    selected_variant=saved_item.selected_variant,
                    selected_addons=saved_item.selected_addons,
                    notes=saved_item.notes,
                    price_snapshot=saved_item.food.current_price
                )
                added_items.append(cart_item)
        
        cart_serializer = CartSerializer(cart)
        return Response({
            'message': f'Saved cart "{saved_cart.name}" loaded successfully',
            'cart': cart_serializer.data,
            'items_added': len(added_items)
        }, status=status.HTTP_200_OK)
    

class SavedCartListView(generics.ListAPIView):
    """View to list user's saved carts."""
    
    serializer_class = SavedCartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SavedCart.objects.filter(user=self.request.user)



class SavedCartDetailView(generics.RetrieveDestroyAPIView):
    """View to retrieve or delete a saved cart."""
    
    serializer_class = SavedCartSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        return SavedCart.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            'message': 'Saved cart deleted successfully'
        }, status=status.HTTP_200_OK)


class CartSummaryView(APIView):
    """View to get cart summary (totals, item count)."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        cart, created = Cart.objects.get_or_create(
            user=request.user,
            is_active=True
        )
        
        return Response({
            'total_items': cart.total_items,
            'subtotal': float(cart.subtotal),
            'total': float(cart.total),
            'item_count': cart.items.count()
        }, status=status.HTTP_200_OK)
# apps/menu/views.py

from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Category, Food
from .serializers import (
    CategorySerializer, 
    FoodListSerializer, 
    FoodDetailSerializer,
    FoodCreateUpdateSerializer
)


class CategoryListView(generics.ListAPIView):
    """View to list all active categories."""
    
    queryset = Category.objects.filter(is_active=True).order_by('display_order')
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # No pagination for categories


class FoodListView(generics.ListAPIView):
    """View to list all available food items."""
    
    serializer_class = FoodListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Food.objects.filter(is_available=True)
        
        # Manual filtering without django-filter
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        # Order by display_order and popularity
        queryset = queryset.order_by('display_order', '-popularity_score')
        
        return queryset.select_related('category')


class FoodDetailView(generics.RetrieveAPIView):
    """View to get detailed information about a food item."""
    
    queryset = Food.objects.all()
    serializer_class = FoodDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Increment popularity score on view
        instance.popularity_score += 1
        instance.save(update_fields=['popularity_score'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class FoodSearchView(APIView):
    """View for searching food items."""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '')
        
        if not query or len(query) < 2:
            return Response({
                'results': [],
                'count': 0,
                'query': query
            })
        
        # Search in name, description, and category
        foods = Food.objects.filter(
            Q(is_available=True) &
            (Q(name__icontains=query) | 
             Q(description__icontains=query) |
             Q(category__name__icontains=query))
        ).select_related('category').order_by('-popularity_score')[:20]
        
        serializer = FoodListSerializer(foods, many=True)
        
        return Response({
            'results': serializer.data,
            'count': len(foods),
            'query': query
        })


class FoodCreateView(generics.CreateAPIView):
    """View for creating new food items (admin only)."""
    
    queryset = Food.objects.all()
    serializer_class = FoodCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]


class FoodUpdateView(generics.UpdateAPIView):
    """View for updating food items (admin only)."""
    
    queryset = Food.objects.all()
    serializer_class = FoodCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    lookup_field = 'id'


class FoodDeleteView(generics.DestroyAPIView):
    """View for deleting food items (admin only)."""
    
    queryset = Food.objects.all()
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    lookup_field = 'id'
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Soft delete by marking as unavailable instead of actual deletion
        instance.is_available = False
        instance.save()
        
        return Response({
            'message': f'Food item "{instance.name}" has been marked as unavailable.'
        }, status=status.HTTP_200_OK)


class FeaturedFoodsView(generics.ListAPIView):
    """View to get featured/popular food items."""
    
    serializer_class = FoodListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        # Get top 8 popular food items
        return Food.objects.filter(
            is_available=True
        ).order_by('-popularity_score')[:8]


class OnSaleFoodsView(generics.ListAPIView):
    """View to get food items on sale."""
    
    serializer_class = FoodListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        # Get all available foods with discount_price
        foods_with_discount = Food.objects.filter(
            is_available=True,
            discount_price__isnull=False
        )
        
        # Filter in Python to check if discount_price < price
        on_sale_ids = []
        for food in foods_with_discount:
            if food.discount_price < food.price:
                on_sale_ids.append(food.id)
        
        # Return queryset filtered by the valid IDs
        return Food.objects.filter(id__in=on_sale_ids).order_by('-popularity_score')


class AdminFoodListView(generics.ListAPIView):
    """View for admin to see all food items (including unavailable)."""
    
    serializer_class = FoodListSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_available', 'category', 'created_by']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        return Food.objects.all().select_related('category', 'created_by')
    
    
class CategoryCreateView(generics.CreateAPIView):
    """View for creating categories (admin only)."""
    
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]


class CategoryUpdateView(generics.UpdateAPIView):
    """View for updating categories (admin only)."""
    
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    lookup_field = 'id'


class CategoryDeleteView(generics.DestroyAPIView):
    """View for deleting categories (admin only)."""
    
    queryset = Category.objects.all()
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    lookup_field = 'id'
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Soft delete by marking as inactive instead of actual deletion
        instance.is_active = False
        instance.save()
        
        return Response({
            'message': f'Category "{instance.name}" has been marked as inactive.'
        }, status=status.HTTP_200_OK)

# apps/menu/urls.py

from django.urls import path
from .views import (
    CategoryListView,
    CategoryCreateView,
    CategoryUpdateView,
    CategoryDeleteView,
    FoodListView,
    FoodDetailView,
    FoodSearchView,
    FoodCreateView,
    FoodUpdateView,
    FoodDeleteView,
    FeaturedFoodsView,
    OnSaleFoodsView,
    AdminFoodListView,
)

urlpatterns = [
    # Public endpoints (no authentication required)
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('foods/', FoodListView.as_view(), name='food-list'),
    path('foods/<int:id>/', FoodDetailView.as_view(), name='food-detail'),
    path('foods/search/', FoodSearchView.as_view(), name='food-search'),
    path('foods/featured/', FeaturedFoodsView.as_view(), name='featured-foods'),
    path('foods/on-sale/', OnSaleFoodsView.as_view(), name='on-sale-foods'),
    
    # Admin endpoints for categories
    path('admin/categories/create/', CategoryCreateView.as_view(), name='category-create'),
    path('admin/categories/<int:id>/update/', CategoryUpdateView.as_view(), name='category-update'),
    path('admin/categories/<int:id>/delete/', CategoryDeleteView.as_view(), name='category-delete'),
    
    # Admin endpoints for foods
    path('admin/foods/', AdminFoodListView.as_view(), name='admin-food-list'),
    path('admin/foods/create/', FoodCreateView.as_view(), name='food-create'),
    path('admin/foods/<int:id>/update/', FoodUpdateView.as_view(), name='food-update'),
    path('admin/foods/<int:id>/delete/', FoodDeleteView.as_view(), name='food-delete'),
]
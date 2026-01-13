# apps/reviews/urls.py
from django.urls import path
from .views import (
    CreateReviewView,
    UserReviewsListView,
    FoodReviewsListView,
    UpdateReviewView,
    DeleteReviewView,
    AdminReviewListView,
    ToggleReviewApprovalView,
)

urlpatterns = [
    # User endpoints
    path('create/', CreateReviewView.as_view(), name='create-review'),
    path('my-reviews/', UserReviewsListView.as_view(), name='user-reviews'),
    path('food/<int:food_id>/', FoodReviewsListView.as_view(), name='food-reviews'),
    path('update/<int:pk>/', UpdateReviewView.as_view(), name='update-review'),
    path('delete/<int:pk>/', DeleteReviewView.as_view(), name='delete-review'),
    
    # Admin endpoints
    path('admin/all/', AdminReviewListView.as_view(), name='admin-reviews'),
    path('admin/toggle-approval/<int:review_id>/', ToggleReviewApprovalView.as_view(), name='toggle-review-approval'),
]
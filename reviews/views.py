# apps/reviews/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.shortcuts import get_object_or_404
from .models import Review
from .serializers import ReviewSerializer, CreateReviewSerializer


class CreateReviewView(APIView):
    """View for creating reviews for completed orders."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CreateReviewSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Add user to review
            review = serializer.save(user=request.user)
            
            return Response({
                'success': True,
                'message': 'Review submitted successfully!',
                'review': ReviewSerializer(review).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserReviewsListView(generics.ListAPIView):
    """View to list user's reviews."""
    
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)


class FoodReviewsListView(generics.ListAPIView):
    """View to list reviews for a specific food item."""
    
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        food_id = self.kwargs['food_id']
        return Review.objects.filter(food_id=food_id, is_approved=True)


class UpdateReviewView(generics.UpdateAPIView):
    """View to update a review (only by owner)."""
    
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)


class DeleteReviewView(generics.DestroyAPIView):
    """View to delete a review (only by owner or admin)."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Review.objects.all()
        return Review.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'message': 'Review deleted successfully!'
        }, status=status.HTTP_200_OK)


class AdminReviewListView(generics.ListAPIView):
    """View for admin to see all reviews."""
    
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get_queryset(self):
        return Review.objects.all()


class ToggleReviewApprovalView(APIView):
    """View for admin to approve/unapprove reviews."""
    
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def patch(self, request, review_id):
        review = get_object_or_404(Review, id=review_id)
        
        review.is_approved = not review.is_approved
        review.save()
        
        action = 'approved' if review.is_approved else 'unapproved'
        
        return Response({
            'success': True,
            'message': f'Review {action} successfully!',
            'review': ReviewSerializer(review).data
        }, status=status.HTTP_200_OK)
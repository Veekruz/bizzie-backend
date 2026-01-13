# apps/users/views.py

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    AdminUserSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

User = get_user_model()


class UserRegistrationView(APIView):
    """View for user registration."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'User registered successfully!',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'phone_number': user.phone_number,
                    'is_admin': user.is_staff,  # False for regular users
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(TokenObtainPairView):
    """View for user login with email/password."""
    
    serializer_class = UserLoginSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({
                'error': 'Invalid credentials',
                'details': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Login successful!',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'phone_number': user.phone_number,
                'is_admin': user.is_staff,  # True for admin users
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating user profile."""
    
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class AdminProfileView(generics.RetrieveAPIView):
    """View for retrieving admin user details (admin only)."""
    
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """View for changing user password."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            
            # Check old password
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({
                    'error': 'Current password is incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Password changed successfully!'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """Password reset view - accepts email, new_password, confirm_password."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        # Validate all fields are present
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not new_password or not confirm_password:
            return Response({
                'error': 'Both new_password and confirm_password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate passwords match
        if new_password != confirm_password:
            return Response({
                'error': 'Passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate password length
        if len(new_password) < 6:
            return Response({
                'error': 'Password must be at least 6 characters'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find user by email
            user = User.objects.get(email=email)
            
            # Update password immediately
            user.set_password(new_password)
            user.save()
            
            return Response({
                'success': True,
                'message': 'Password updated successfully! You can now login with your new password.'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            # For security, return same message whether user exists or not
            return Response({
                'success': True,
                'message': 'If your email is registered, your password has been updated.'
            }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """View for user logout (blacklist refresh token)."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response({
                    'error': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'message': 'Logout successful!'
            }, status=status.HTTP_205_RESET_CONTENT)
            
        except Exception as e:
            return Response({
                'error': 'Invalid token or token not provided'
            }, status=status.HTTP_400_BAD_REQUEST)


class DeleteAccountView(APIView):
    """View for deleting user account."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request):
        user = request.user
        user_email = user.email
        
        user.delete()
        
        return Response({
            'message': f'Account {user_email} deleted successfully!'
        }, status=status.HTTP_204_NO_CONTENT)
# apps/users/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
    AdminProfileView,
    ChangePasswordView,
    PasswordResetRequestView,
    LogoutView,
    DeleteAccountView,
)

urlpatterns = [
    # Authentication endpoints
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile management
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('admin-profile/', AdminProfileView.as_view(), name='admin_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    
    # Password reset
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
]
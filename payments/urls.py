# apps/payments/urls.py
from django.urls import path
from .views import (
    InitializePaymentView,
    VerifyPaymentView,
    UserPaymentsListView,
    PaymentDetailView,
    CheckPaymentStatusView,
)

urlpatterns = [
    # Payment endpoints
    path('initialize/', InitializePaymentView.as_view(), name='initialize-payment'),
    path('verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('check/<str:reference>/', CheckPaymentStatusView.as_view(), name='check-payment'),
    
    # Payment history
    path('history/', UserPaymentsListView.as_view(), name='payment-history'),
    path('<uuid:payment_id>/', PaymentDetailView.as_view(), name='payment-detail'),
]
# apps/orders/urls.py

from django.urls import path
from .views import (
    OrderListView,
    OrderDetailView,
    CreateOrderView,
    InitiatePaymentView,
    PaystackWebhookView,
    UpdateOrderStatusView,
    CancelOrderView,
    AdminOrderListView,
    OrderStatsView,
)

urlpatterns = [
    # User order endpoints
    path('', OrderListView.as_view(), name='order-list'),
    path('create/', CreateOrderView.as_view(), name='create-order'),
    path('stats/', OrderStatsView.as_view(), name='order-stats'),
    path('<int:id>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/cancel/', CancelOrderView.as_view(), name='cancel-order'),
    
    # Payment endpoints
    path('payment/initiate/', InitiatePaymentView.as_view(), name='initiate-payment'),
    path('webhook/paystack/', PaystackWebhookView.as_view(), name='paystack-webhook'),
    
    # Admin endpoints
    path('admin/all/', AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/<int:order_id>/update-status/', UpdateOrderStatusView.as_view(), name='update-order-status'),
]
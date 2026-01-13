# apps/orders/views.py

import json
import hashlib
import hmac
from django.conf import settings
from django.http import HttpResponse

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, PermissionDenied

from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Order, OrderItem, OrderStatusHistory
from django.db.models import Sum, Count
from .serializers import (
    OrderSerializer,
    CreateOrderSerializer,
    UpdateOrderStatusSerializer,
    PaymentInitSerializer,
)


class OrderListView(generics.ListAPIView):
    """View to list user's orders."""
    
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderDetailView(generics.RetrieveAPIView):
    """View to get order details."""
    
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        # Users can only see their own orders
        return Order.objects.filter(user=self.request.user)


class CreateOrderView(APIView):
    """View to create order from cart."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CreateOrderSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            order = serializer.save()
            
            # Serialize the created order
            order_serializer = OrderSerializer(order)
            
            return Response({
                'message': 'Order created successfully!',
                'order': order_serializer.data,
                'next_step': 'Proceed to payment'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InitiatePaymentView(APIView):
    """View to initiate Paystack payment."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PaymentInitSerializer(data=request.data)
        
        if serializer.is_valid():
            order_id = serializer.validated_data['order_id']
            order = get_object_or_404(Order, id=order_id, user=request.user)
            
            # Check if order is already paid
            if order.is_paid:
                return Response({
                    'error': 'Order is already paid'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate payment reference (for Paystack)
            import random
            import string
            payment_ref = 'PAY' + ''.join(random.choices(string.digits, k=10))
            
            # Update order with payment reference
            order.payment_reference = payment_ref
            order.save()
            
            # In a real implementation, you would:
            # 1. Call Paystack API to initialize transaction
            # 2. Get payment URL from Paystack
            # 3. Return the URL to frontend
            
            # For now, return mock payment data
            return Response({
                'message': 'Payment initialized',
                'order_id': order.id,
                'order_number': order.order_number,
                'amount': float(order.total_amount),
                'payment_reference': payment_ref,
                'payment_url': f'https://paystack.com/pay/{payment_ref}',  # Mock URL
                'public_key': settings.PAYSTACK_PUBLIC_KEY if hasattr(settings, 'PAYSTACK_PUBLIC_KEY') else 'test_key'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaystackWebhookView(APIView):
    """View to handle Paystack webhook."""
    
    permission_classes = []  # No authentication for webhook
    authentication_classes = []  # No authentication for webhook
    
    def post(self, request):
        # Verify webhook signature
        signature = request.headers.get('x-paystack-signature')
        
        if not self.verify_signature(request.body, signature):
            return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
        
        data = json.loads(request.body)
        event = data.get('event')
        
        if event == 'charge.success':
            return self.handle_successful_payment(data)
        elif event == 'charge.failed':
            return self.handle_failed_payment(data)
        
        return Response({'message': 'Webhook received'}, status=status.HTTP_200_OK)
    
    def verify_signature(self, payload, signature):
        """Verify Paystack webhook signature."""
        if not hasattr(settings, 'PAYSTACK_WEBHOOK_SECRET'):
            return True  # Skip verification in development
        
        secret = settings.PAYSTACK_WEBHOOK_SECRET.encode('utf-8')
        expected_signature = hmac.new(secret, payload, hashlib.sha512).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    def handle_successful_payment(self, data):
        """Handle successful payment webhook."""
        payment_data = data.get('data', {})
        reference = payment_data.get('reference')
        amount = payment_data.get('amount') / 100  # Convert from kobo to naira
        
        try:
            order = Order.objects.get(payment_reference=reference)
            
            # Mark order as paid
            order.mark_as_paid(payment_reference=reference)
            
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                old_status=order.status,
                new_status=order.status,
                notes=f'Payment successful via Paystack. Amount: ₦{amount}'
            )
            
            return Response({'message': 'Payment processed successfully'}, status=status.HTTP_200_OK)
            
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def handle_failed_payment(self, data):
        """Handle failed payment webhook."""
        payment_data = data.get('data', {})
        reference = payment_data.get('reference')
        
        try:
            order = Order.objects.get(payment_reference=reference)
            
            # Update payment status
            order.payment_status = 'failed'
            order.save()
            
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                old_status=order.status,
                new_status=order.status,
                notes='Payment failed via Paystack'
            )
            
            return Response({'message': 'Payment failure recorded'}, status=status.HTTP_200_OK)
            
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


class UpdateOrderStatusView(APIView):
    """View for admin to update order status."""
    
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def patch(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        
        serializer = UpdateOrderStatusSerializer(
            data=request.data,
            context={'order': order}
        )
        
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            admin_notes = serializer.validated_data.get('admin_notes', '')
            
            # Create status history before updating
            OrderStatusHistory.objects.create(
                order=order,
                old_status=order.status,
                new_status=new_status,
                changed_by=request.user,
                notes=admin_notes
            )
            
            # Update order status
            order.update_status(new_status, admin_notes)
            
            order_serializer = OrderSerializer(order)
            return Response({
                'message': f'Order status updated to {new_status}',
                'order': order_serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CancelOrderView(APIView):
    """View for users to cancel their order."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Check if order can be cancelled
        if not order.can_be_cancelled:
            return Response({
                'error': 'This order cannot be cancelled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            old_status=order.status,
            new_status='cancelled',
            changed_by=request.user,
            notes='Cancelled by customer'
        )
        
        # Update order status
        order.update_status('cancelled', 'Cancelled by customer')
        
        order_serializer = OrderSerializer(order)
        return Response({
            'message': 'Order cancelled successfully',
            'order': order_serializer.data
        }, status=status.HTTP_200_OK)


class AdminOrderListView(generics.ListAPIView):
    """View for admin to see all orders."""
    
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get_queryset(self):
        # Admin can see all orders
        return Order.objects.all()


class OrderStatsView(APIView):
    """View to get order statistics."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Add imports locally or at top
        from django.db.models import Sum
        
        if user.is_staff:
            # Admin sees all stats
            total_orders = Order.objects.count()
            pending_orders = Order.objects.filter(status='pending').count()
            completed_orders = Order.objects.filter(status='completed').count()
            total_revenue = Order.objects.filter(is_paid=True).aggregate(
                total=Sum('total_amount')
            )['total'] or 0
        else:
            # Regular user sees their own stats
            total_orders = Order.objects.filter(user=user).count()
            pending_orders = Order.objects.filter(user=user, status='pending').count()
            completed_orders = Order.objects.filter(user=user, status='completed').count()
            total_revenue = 0  # Users don't see revenue
        
        return Response({
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'total_revenue': float(total_revenue)
        }, status=status.HTTP_200_OK)
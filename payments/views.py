# apps/payments/views.py
import random
import string
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment
from orders.models import Order
from .serializers import (
    PaymentSerializer,
    InitializePaymentSerializer,
    VerifyPaymentSerializer,
)
from .services import PaystackService


class InitializePaymentView(APIView):
    """
    Initialize Paystack payment and get payment URL.
    
    Flow:
    1. User provides order_id
    2. Backend creates payment record with unique reference
    3. Backend calls Paystack to get payment URL
    4. Frontend redirects user to Paystack URL
    5. User pays on Paystack
    6. Paystack redirects back to frontend
    7. Frontend calls verify endpoint with reference
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = InitializePaymentSerializer(data=request.data)
        
        if serializer.is_valid():
            order_id = serializer.validated_data['order_id']
            
            # Get the order
            order = get_object_or_404(
                Order,
                id=order_id,
                user=request.user
            )
            
            # Check if already paid
            if order.is_paid:
                return Response({
                    'success': False,
                    'error': 'Order is already paid'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate unique reference
            reference = self.generate_reference()
            
            # Check if reference is unique
            while Payment.objects.filter(reference=reference).exists():
                reference = self.generate_reference()
            
            # Create payment record
            payment = Payment.objects.create(
                reference=reference,
                order=order,
                user=request.user,
                amount=order.total_amount,
                currency='NGN',
                status='pending'
            )
            
            try:
                # Initialize Paystack transaction
                paystack_service = PaystackService()
                
                # Create callback URL for redirect
                callback_url = self.get_callback_url(request, reference)
                
                # Call Paystack API
                result = paystack_service.initialize_transaction(
                    email=request.user.email,
                    amount=float(order.total_amount),
                    reference=reference,
                    callback_url=callback_url
                )
                
                if result['success']:
                    # Save Paystack data
                    payment.paystack_authorization_url = result['authorization_url']
                    payment.paystack_access_code = result['access_code']
                    payment.save()
                    
                    return Response({
                        'success': True,
                        'message': 'Payment link generated successfully',
                        'data': {
                            'payment_url': result['authorization_url'],
                            'reference': reference,
                            'order_id': order.id,
                            'order_number': order.order_number,
                            'amount': float(order.total_amount),
                            'public_key': getattr(settings, 'PAYSTACK_PUBLIC_KEY', ''),
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    # Mark payment as failed
                    payment.mark_as_failed(result.get('message', 'Payment initialization failed'))
                    
                    return Response({
                        'success': False,
                        'error': 'Failed to create payment link',
                        'details': result.get('message', 'Unknown error')
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception as e:
                # Mark payment as failed
                payment.mark_as_failed(f"Server error: {str(e)}")
                
                return Response({
                    'success': False,
                    'error': 'Payment initialization failed',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def generate_reference(self):
        """Generate unique payment reference."""
        timestamp = str(int(timezone.now().timestamp()))[-8:]
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"PAY{timestamp}{random_str}"
    
    def get_callback_url(self, request, reference):
        """Get the callback URL for Paystack redirect."""
        # You can customize this based on your frontend URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return f"{frontend_url}/payment/verify/{reference}/"


class VerifyPaymentView(APIView):
    """
    Verify payment after user returns from Paystack.
    
    This endpoint should be called by frontend after Paystack redirect.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reference = serializer.validated_data['reference']
        
        try:
            # Get payment (user can only verify their own payments)
            payment = Payment.objects.get(reference=reference, user=request.user)
            
            # Check if already verified
            if payment.is_successful:
                return Response({
                    'success': True,
                    'message': 'Payment already verified',
                    'data': {
                        'payment': PaymentSerializer(payment).data,
                        'order': {
                            'id': payment.order.id,
                            'order_number': payment.order.order_number,
                            'status': payment.order.status,
                        }
                    }
                }, status=status.HTTP_200_OK)
            
            # Verify with Paystack
            paystack_service = PaystackService()
            result = paystack_service.verify_transaction(reference)
            
            if result['success']:
                # Mark payment as successful
                payment.mark_as_successful()
                
                return Response({
                    'success': True,
                    'message': 'Payment verified successfully!',
                    'data': {
                        'payment': PaymentSerializer(payment).data,
                        'order': {
                            'id': payment.order.id,
                            'order_number': payment.order.order_number,
                            'status': payment.order.status,
                        }
                    }
                }, status=status.HTTP_200_OK)
            else:
                # Mark payment as failed
                payment.mark_as_failed(result.get('message', 'Verification failed'))
                
                return Response({
                    'success': False,
                    'error': 'Payment verification failed',
                    'details': result.get('message', 'Unknown error'),
                    'data': {
                        'payment': PaymentSerializer(payment).data
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Payment.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Verification failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserPaymentsListView(generics.ListAPIView):
    """List all payments for the authenticated user."""
    
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


class PaymentDetailView(generics.RetrieveAPIView):
    """Get payment details."""
    
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'payment_id'
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


class CheckPaymentStatusView(APIView):
    """Quick check if payment is successful."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, reference):
        try:
            payment = Payment.objects.get(reference=reference, user=request.user)
            
            return Response({
                'success': True,
                'data': {
                    'reference': payment.reference,
                    'status': payment.status,
                    'is_successful': payment.is_successful,
                    'order_id': payment.order.id,
                    'order_number': payment.order.order_number,
                }
            })
            
        except Payment.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
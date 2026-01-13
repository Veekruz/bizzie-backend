# apps/payments/services.py
import requests
import json
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from urllib.parse import urljoin


class PaystackService:
    """Service class for Paystack payment integration."""
    
    BASE_URL = "https://api.paystack.co"
    
    def __init__(self):
        self.secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
        
        if not self.secret_key:
            raise ImproperlyConfigured("PAYSTACK_SECRET_KEY is not set in settings.py")
        
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
    
    def initialize_transaction(self, email, amount, reference, callback_url=None):
        """
        Initialize a Paystack transaction.
        
        Args:
            email: Customer email
            amount: Amount in Naira (will be converted to kobo)
            reference: Unique transaction reference
            callback_url: Where Paystack redirects after payment
            
        Returns:
            Dictionary with success status and data
        """
        url = urljoin(self.BASE_URL, "/transaction/initialize")
        
        payload = {
            "email": email,
            "amount": int(amount * 100),  # Convert to kobo
            "reference": reference,
        }
        
        # Add callback URL for redirect after payment
        if callback_url:
            payload["callback_url"] = callback_url
        
        try:
            response = requests.post(url, headers=self.headers, data=json.dumps(payload), timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status"):
                return {
                    "success": True,
                    "authorization_url": data["data"]["authorization_url"],
                    "access_code": data["data"]["access_code"],
                    "reference": data["data"]["reference"],
                }
            else:
                return {
                    "success": False,
                    "message": data.get("message", "Failed to initialize transaction"),
                    "data": data
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Network error: {str(e)}",
            }
    
    def verify_transaction(self, reference):
        """
        Verify a Paystack transaction.
        
        Args:
            reference: Paystack transaction reference
            
        Returns:
            Dictionary with verification status
        """
        url = urljoin(self.BASE_URL, f"/transaction/verify/{reference}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") and data["data"]["status"] == "success":
                return {
                    "success": True,
                    "data": data["data"],
                    "message": "Transaction verified successfully",
                }
            else:
                return {
                    "success": False,
                    "message": data.get("message", "Transaction verification failed"),
                    "data": data
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Network error: {str(e)}",
            }
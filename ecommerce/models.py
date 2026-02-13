from django.db import models
from django.db.models import Sum
from django.conf import settings
from services.models import Plan
from quotes.models import QuoteRequest
import os

def transaction_proof_path(instance, filename):

    order_id = getattr(instance, 'order_id', None) or getattr(getattr(instance, 'order', None), 'id', 'unknown')
    transaction_id = getattr(instance, 'id', None) or 'temp'
    return f"transactions/{order_id}/{transaction_id}/{filename}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        AWAITING_PAYMENT = 'AWAITING_PAYMENT', 'Awaiting Payment'
        PAID = 'PAID', 'Paid'
        ACTIVE = 'ACTIVE', 'Active'
        CANCELLED = 'CANCELLED', 'Cancelled'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    quote_request = models.OneToOneField(QuoteRequest, on_delete=models.SET_NULL, null=True, blank=True)
    negotiated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.email}"

    def update_status_based_on_milestones(self):
        if not self.milestones.exists():
            return

        has_pending_milestones = self.milestones.filter(status='PENDING').exists()

        if not has_pending_milestones:
            self.status = self.Status.ACTIVE
        else:
            if self.status != self.Status.PENDING:
                self.status = self.Status.AWAITING_PAYMENT
        
        self.save()

    @property
    def final_price(self):
        if self.negotiated_price is not None:
            return self.negotiated_price
        if self.plan:
            return self.plan.price
        return 0.00

class Transaction(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'   
        VERIFYING = 'VERIFYING', 'Verifying Proof'
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='transactions')
    milestone = models.ForeignKey('billing.Milestone', on_delete=models.SET_NULL, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    provider_name = models.CharField(max_length=50, blank=True, null=True, default="RiskPay") 
    gateway_address_in = models.TextField(blank=True, null=True)
    gateway_polygon_address_in = models.CharField(max_length=255, blank=True, null=True)
    gateway_ipn_token = models.TextField(unique=True, blank=True, null=True) 
    gateway_txid_out = models.CharField(max_length=255, blank=True, null=True) 
    gateway_coin_type = models.CharField(max_length=50, blank=True, null=True) 
    gateway_value_in_coin = models.CharField(max_length=50, blank=True, null=True) 
    proof_screenshot = models.ImageField(upload_to=transaction_proof_path, null=True, blank=True)
    proof_reference_number = models.CharField(max_length=100, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.id} for Order #{self.order.id} - {self.status}"

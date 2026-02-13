
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import requests
from decimal import Decimal
import urllib.parse
from .models import Milestone
from .serializers import MilestoneSerializer
from users.permissions import IsEmployeeOrOwner
from ecommerce.models import Transaction, Order
from payments.models import PaymentProvider

class MilestoneViewSet(viewsets.ModelViewSet):
    """
    Handles full CRUD for Milestones.
    - EMPLOYEES/OWNERS: Create, update, delete milestones.
    - CUSTOMERS: List/Retrieve own milestones, Initiate Payments.
    """
    serializer_class = MilestoneSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in [user.Role.EMPLOYEE, user.Role.OWNER]:
            return Milestone.objects.all()
        return Milestone.objects.filter(order__user=user)

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'initiate_payment']:
            return [IsAuthenticated()]
        return [IsEmployeeOrOwner()]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            order_id = response.data.get('order')
            try:
                order = Order.objects.get(id=order_id)
                if order.status in [Order.Status.ACTIVE, Order.Status.PAID]:
                    order.status = Order.Status.AWAITING_PAYMENT
                    order.save()
            except Order.DoesNotExist:
                pass
        return response

    @action(detail=True, methods=['post'])
    def initiate_payment(self, request, pk=None):
        milestone = self.get_object()

        if milestone.order.user != request.user and request.user.role == 'CUSTOMER':
            return Response({"error": "You do not have permission to pay for this milestone."}, status=status.HTTP_403_FORBIDDEN)
        
        if milestone.status == Milestone.Status.PAID:
            return Response({"error": "This milestone has already been paid."}, status=status.HTTP_400_BAD_REQUEST)

        provider_code = request.data.get('provider_code')
        if not provider_code:
            return Response({"error": "A 'provider_code' must be selected."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            provider = PaymentProvider.objects.get(provider_name_code=provider_code, is_active=True)
        except PaymentProvider.DoesNotExist:
            return Response({"error": "The selected payment provider is not valid or active."}, status=status.HTTP_404_NOT_FOUND)

        custom_amount_str = request.data.get('custom_amount')
        payment_amount = milestone.amount 

        if custom_amount_str:
            try:
                custom_amount = Decimal(custom_amount_str)
            except:
                return Response({"error": "Invalid custom amount format."}, status=status.HTTP_400_BAD_REQUEST)

            if custom_amount <= 0:
                return Response({"error": "Payment amount must be greater than 0."}, status=status.HTTP_400_BAD_REQUEST)
            
            if custom_amount > milestone.amount:
                return Response({"error": "You cannot pay more than the milestone amount."}, status=status.HTTP_400_BAD_REQUEST)

            if custom_amount < milestone.amount:
                remaining_amount = milestone.amount - custom_amount
                original_title = milestone.title
                
                milestone.amount = custom_amount
                milestone.title = f"{original_title} (Partial Payment)"
                milestone.save()
                
                Milestone.objects.create(
                    order=milestone.order,
                    title=f"Remaining Balance: {original_title}",
                    amount=remaining_amount,
                    status=Milestone.Status.PENDING
                )
                payment_amount = custom_amount

        if payment_amount < provider.min_amount:
            return Response({"error": f"Payment amount ${payment_amount} is below the minimum of ${provider.min_amount} for this provider."}, status=status.HTTP_400_BAD_REQUEST)
        if payment_amount > provider.max_amount:
            return Response({"error": f"Payment amount ${payment_amount} exceeds the maximum of ${provider.max_amount} for this provider."}, status=status.HTTP_400_BAD_REQUEST)

        fee_percentage = provider.processing_fee_percentage / Decimal('100')
        processing_fee = payment_amount * fee_percentage
        final_charge_amount = payment_amount + processing_fee
        
        existing_transaction = Transaction.objects.filter(
            milestone=milestone, 
            status=Transaction.Status.PENDING
        ).first()

        if existing_transaction:
            transaction = existing_transaction
            transaction.amount = final_charge_amount
            transaction.provider_name = provider.title
            transaction.save()
        else:
            transaction = Transaction.objects.create(
                order=milestone.order,
                milestone=milestone,
                amount=final_charge_amount,
                status=Transaction.Status.PENDING,
                provider_name=provider.title 
            )

        if provider.type == PaymentProvider.ProviderType.BANK_TRANSFER:
            return Response({
                'payment_type': 'MANUAL',
                'transaction_id': transaction.id,
                'bank_details': provider.bank_details, 
                'milestone_amount': payment_amount,
                'processing_fee': processing_fee,
                'final_charge_amount': final_charge_amount,
                'message': "Please transfer the amount manually using the provided bank details."
            }, status=status.HTTP_200_OK)
        
        callback_url_with_id = f"{settings.RISKPAY_CALLBACK_URL}?transaction_id={transaction.id}"
        params = {'address': settings.RISKPAY_MERCHANT_WALLET_ADDRESS, 'callback': callback_url_with_id}
        
        try:
            response = requests.get(settings.RISKPAY_API_WALLET_URL, params=params)
            response.raise_for_status() 
            riskpay_data = response.json()
        except Exception as e:
            transaction.status = Transaction.Status.FAILED
            transaction.save()
            return Response({"error": f"Could not connect to payment gateway: {str(e)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        transaction.gateway_address_in = riskpay_data.get('address_in')
        transaction.gateway_polygon_address_in = riskpay_data.get('polygon_address_in')
        transaction.gateway_ipn_token = riskpay_data.get('ipn_token')
        transaction.save()

        payment_url_params = {
            'amount': str(final_charge_amount),
            'provider': provider.provider_name_code,
            'email': request.user.email,
            'currency': 'USD'
        }
        
        query_string = urllib.parse.urlencode(payment_url_params)
        payment_url = f"{settings.RISKPAY_PAYMENT_PROCESSING_URL}?address={transaction.gateway_address_in}&{query_string}"
        
        print("--- Generated Payment URL ---")
        print(payment_url)
        print("---------------------------")

        return Response({
            'payment_type': 'GATEWAY',
            'payment_url': payment_url, 
            'milestone_amount': payment_amount,
            'processing_fee': processing_fee,
            'final_charge_amount': final_charge_amount
        }, status=status.HTTP_200_OK)
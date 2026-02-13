from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status , viewsets
from rest_framework.permissions import AllowAny
from ecommerce.models import Transaction, Order
from billing.models import Milestone
from users.models import User
from users.permissions import IsOwner
from .models import PaymentProvider
from .serializers import PaymentProviderSerializer

class RiskPayIPNView(APIView):

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        ipn_data = request.data
        
        ipn_token = ipn_data.get('ipn_token')
        payment_status = ipn_data.get('status') 

        if not ipn_token:
            return Response(
                {"error": "Required 'ipn_token' not found in IPN data."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            transaction = Transaction.objects.get(gateway_ipn_token=ipn_token)
        except Transaction.DoesNotExist:
            print(f"Warning: Received an IPN with an unknown token: {ipn_token}")
            return Response(
                {"error": "Transaction not found for the provided IPN token."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        transaction.gateway_txid_out = ipn_data.get('txid_out')
        transaction.gateway_coin_type = ipn_data.get('coin')
        transaction.gateway_value_in_coin = ipn_data.get('value_coin')

        if payment_status and payment_status.upper() == 'ACCEPT':
            transaction.status = Transaction.Status.SUCCESS
            transaction.save()
            if transaction.milestone:
                transaction.milestone.status = Milestone.Status.PAID
                transaction.milestone.save() 
        else:
            transaction.status = Transaction.Status.FAILED
            transaction.save()
        return Response({"status": "IPN received and processed successfully."}, status=status.HTTP_200_OK)
    
class PaymentProviderViewSet(viewsets.ModelViewSet): 

    serializer_class = PaymentProviderSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        
        return [IsOwner()]

    def get_queryset(self):

        user = self.request.user
        if user.is_authenticated and user.role == User.Role.OWNER:
            return PaymentProvider.objects.all().order_by('id')

        return PaymentProvider.objects.filter(is_active=True).order_by('id')
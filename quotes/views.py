from rest_framework import viewsets, mixins
from .models import QuoteRequest
from .serializers import QuoteRequestSerializer
from ecommerce.models import Order
from ecommerce.serializers import OrderDetailSerializer
from users.permissions import IsEmployeeOrOwner 
from rest_framework.views import APIView
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.decorators import action 
from rest_framework.permissions import AllowAny, IsAuthenticated

class QuoteRequestViewSet(viewsets.ModelViewSet):
    serializer_class = QuoteRequestSerializer
    
    def get_queryset(self):

        user = self.request.user
        if user.is_authenticated:
            if user.role in [user.Role.EMPLOYEE, user.Role.OWNER]:
                return QuoteRequest.objects.all().order_by('-created_at')
            return QuoteRequest.objects.filter(user=user).order_by('-created_at')
        return QuoteRequest.objects.none() 

    def get_permissions(self):

        if self.action == 'create':
            permission_classes = [AllowAny]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsEmployeeOrOwner]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["patch"], permission_classes=[IsEmployeeOrOwner])
    def update_status(self, request, pk=None):
        quote = self.get_object()
        new_status = request.data.get("status")
        valid_statuses = [choice[0] for choice in QuoteRequest.Status.choices]

        if new_status not in valid_statuses:
            return Response({"error": f"Invalid status. Valid choices: {valid_statuses}"}, status=status.HTTP_400_BAD_REQUEST)
        
        quote.status = new_status
        quote.save()
        return Response({"message": f"Quote status updated to {quote.status}"}, status=status.HTTP_200_OK)

class ConvertQuoteToOrderView(APIView):
    permission_classes = [IsEmployeeOrOwner]
    def post(self, request, quote_id, *args, **kwargs):
        try:
            quote = QuoteRequest.objects.get(id=quote_id)
        except QuoteRequest.DoesNotExist:
            return Response({"error": "Quote request not found."}, status=status.HTTP_404_NOT_FOUND)
        if Order.objects.filter(quote_request=quote).exists():
             return Response({"error": "An order has already been created for this quote."}, status=status.HTTP_400_BAD_REQUEST)
        order = Order.objects.create(
            user=quote.user,
            plan=quote.plan,
            quote_request=quote 
        )
        quote.status = QuoteRequest.Status.CONVERTED
        quote.save()
        serializer = OrderDetailSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

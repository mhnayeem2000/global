from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Order, Transaction
from .serializers import OrderListSerializer, OrderDetailSerializer, TransactionSerializer
from users.permissions import IsEmployeeOrOwner
from billing.models import Milestone 

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        user = self.request.user
        if user.role in [user.Role.EMPLOYEE, user.Role.OWNER]:
            return Order.objects.all().order_by("-created_at")
        return Order.objects.filter(user=user).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderListSerializer

    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)
        plan = order.plan
        
        if plan:
            Milestone.objects.create(
                order=order,
                title=f"Initial payment for {plan.name}",
                amount=plan.price,
                status=Milestone.Status.PENDING
            )

    @action(detail=True, methods=["patch"], permission_classes=[IsEmployeeOrOwner])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get("status")
        valid_statuses = [choice[0] for choice in Order.Status.choices]
        if new_status not in valid_statuses:
            return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
        order.status = new_status
        order.save()
        return Response({"message": f"Order status updated to {order.status}"}, status=status.HTTP_200_OK)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if user.role in [user.Role.EMPLOYEE, user.Role.OWNER]:
            return Transaction.objects.all().order_by('-timestamp')
        
        return Transaction.objects.filter(order__user=user).order_by('-timestamp')
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit_proof(self, request, pk=None):
        transaction = self.get_object()
        if transaction.order.user != request.user:
            return Response({"error": "You do not have permission to access this transaction."}, status=status.HTTP_403_FORBIDDEN)
        if transaction.status not in [Transaction.Status.PENDING, Transaction.Status.FAILED]:
            return Response({"error": "Cannot submit proof for this transaction status."}, status=status.HTTP_400_BAD_REQUEST)

        proof_ref = request.data.get('proof_reference_number')
        proof_img = request.FILES.get('proof_screenshot')

        if not proof_ref and not proof_img:
            return Response({"error": "You must provide either a reference number or a screenshot."}, status=status.HTTP_400_BAD_REQUEST)

        if proof_ref:
            transaction.proof_reference_number = proof_ref
        if proof_img:
            transaction.proof_screenshot = proof_img
        if hasattr(Transaction.Status, 'VERIFYING'):
            transaction.status = Transaction.Status.VERIFYING
        
        transaction.save()

        serializer = self.get_serializer(transaction)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsEmployeeOrOwner])
    def approve_transfer(self, request, pk=None):
        transaction = self.get_object()
        
        if transaction.status == Transaction.Status.SUCCESS:
            return Response({"error": "Transaction is already successful."}, status=status.HTTP_400_BAD_REQUEST)
        transaction.status = Transaction.Status.SUCCESS
        transaction.save()
        if transaction.milestone:
            transaction.milestone.status = Milestone.Status.PAID
            transaction.milestone.save()

        serializer = self.get_serializer(transaction)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsEmployeeOrOwner])
    def reject_transfer(self, request, pk=None):

        transaction = self.get_object()
        if transaction.status == Transaction.Status.SUCCESS:
            return Response({"error": "Cannot reject a successful transaction."}, status=status.HTTP_400_BAD_REQUEST)
        transaction.status = Transaction.Status.FAILED
        transaction.save()
        return Response({"message": "Transaction rejected."}, status=status.HTTP_200_OK)
    

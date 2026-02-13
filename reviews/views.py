from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Review
from .serializers import ReviewSerializer
from ecommerce.models import Order

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        order = serializer.validated_data.get('order')

        if self.request.user != order.user:
            raise serializers.ValidationError("You do not have permission to review this order.")
        if hasattr(order, 'review'):
            raise serializers.ValidationError("This order has already been reviewed.")

        serializer.save(user=self.request.user, plan=order.plan)
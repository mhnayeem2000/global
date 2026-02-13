from rest_framework import viewsets
from .models import Service, Plan, Feature
from .serializers import ServiceSerializer, PlanSerializer, FeatureSerializer
from users.permissions import IsOwnerOrReadOnly

class ServiceViewSet(viewsets.ModelViewSet): 
    queryset = Service.objects.all() 
    serializer_class = ServiceSerializer
    lookup_field = 'slug'
    permission_classes = [IsOwnerOrReadOnly]

class FeatureViewSet(viewsets.ModelViewSet): 
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    permission_classes = [IsOwnerOrReadOnly]

class PlanViewSet(viewsets.ModelViewSet): 
    queryset = Plan.objects.prefetch_related('features', 'reviews__user__profile', 'faqs').all()
    serializer_class = PlanSerializer
    lookup_field = 'slug'
    permission_classes = [IsOwnerOrReadOnly] 
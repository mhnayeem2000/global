from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, PlanViewSet , FeatureViewSet

router = DefaultRouter()
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'plans', PlanViewSet, basename='plan')
router.register(r'features', FeatureViewSet, basename='feature')

urlpatterns = [
    path('', include(router.urls)),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RiskPayIPNView, PaymentProviderViewSet

router = DefaultRouter()
router.register(r'payment-providers', PaymentProviderViewSet, basename='payment-provider')

urlpatterns = [
    path('', include(router.urls)),
    path('ipn/riskpay/', RiskPayIPNView.as_view(), name='riskpay-ipn'),
]
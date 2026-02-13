from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuoteRequestViewSet , ConvertQuoteToOrderView

router = DefaultRouter()
router.register(r'quotes', QuoteRequestViewSet, basename='quote')

urlpatterns = [
    path('', include(router.urls)),
    path('quotes/<int:quote_id>/convert-to-order/', ConvertQuoteToOrderView.as_view(), name='convert-quote-to-order'),

]
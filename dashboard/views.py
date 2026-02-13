from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from dashboard.models import SiteSettings
from dashboard.serializers import SiteSettingsSerializer
from ecommerce.serializers import OrderDetailSerializer
from quotes.models import QuoteRequest
from quotes.serializers import QuoteRequestSerializer
from users.models import User
from ecommerce.models import Order, Transaction
from quotes.models import QuoteRequest
from services.models import Service
from users.permissions import IsOwner
from django.db.models import Sum, Count, Q
from users.permissions import IsOwnerOrReadOnly # <-- Import the permission
from rest_framework import generics



class CustomerDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        
        orders = user.orders.all()
        order_serializer = OrderDetailSerializer(orders, many=True)
        quotes = QuoteRequest.objects.filter(user=user)
        quote_serializer = QuoteRequestSerializer(quotes, many=True)

        dashboard_data = {
            'user_info': {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'orders': order_serializer.data,
            'quote_requests': quote_serializer.data,
        }
        return Response(dashboard_data)



class AdminDashboardView(APIView):

    permission_classes = [IsOwner] 

    def get(self, request, *args, **kwargs):
        user_counts = User.objects.aggregate(
            total_customers=Count('id', filter=Q(role=User.Role.CUSTOMER)),
            total_employees=Count('id', filter=Q(role=User.Role.EMPLOYEE))
        )
        running_orders_count = Order.objects.filter(
            status__in=[Order.Status.ACTIVE, Order.Status.AWAITING_PAYMENT]
        ).count()
        pending_quotes_count = QuoteRequest.objects.filter(status=QuoteRequest.Status.PENDING).count()
        pending_orders_count = Order.objects.filter(status=Order.Status.PENDING).count()
        total_services_count = Service.objects.count()
        total_earnings = Transaction.objects.filter(status=Transaction.Status.SUCCESS).aggregate(
            total=Sum('amount')
        )['total'] or 0.00 

        dashboard_stats = {
            "user_stats": {
                "total_customers": user_counts['total_customers'],
                "total_employees": user_counts['total_employees'],
            },
            "service_stats": {
                "total_services_offered": total_services_count,
                "running_orders": running_orders_count,
                "pending_quotes_for_approval": pending_quotes_count,
                "pending_direct_purchase_orders": pending_orders_count,
            },
            "financial_stats": {
                "total_earnings": total_earnings,
            }
        }
        
        return Response(dashboard_stats)



class SiteSettingsView(generics.RetrieveUpdateAPIView):

    serializer_class = SiteSettingsSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_object(self):
        settings_obj = SiteSettings.objects.first()
        
        if not settings_obj:
            settings_obj = SiteSettings.objects.create(
                site_email="admin@example.com",
                site_phone="+123456789",
                site_location="123 Main Street"
            )
        
        return settings_obj
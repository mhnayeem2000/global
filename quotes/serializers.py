from rest_framework import serializers
from .models import QuoteRequest
from users.models import User
from ecommerce.models import Order
from billing.models import Milestone
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from rest_framework_simplejwt.tokens import RefreshToken

class QuoteRequestSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = QuoteRequest
        fields = ['id', 'plan', 'name', 'email', 'company_name', 'custom_requirements', 'token']
        read_only_fields = ['id', 'token']

    def get_token(self, obj):
        if hasattr(obj, 'created_user'):
            user = obj.created_user
            refresh = RefreshToken.for_user(user)
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        return None

    def create(self, validated_data):
        email = validated_data['email']
        plan = validated_data.get('plan')

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': validated_data.get('name', '').split(' ')[0],
                'last_name': ' '.join(validated_data.get('name', '').split(' ')[1:]),
                'role': User.Role.CUSTOMER,
            }
        )

        if created:
            temp_password = get_random_string(length=10)
            user.set_password(temp_password)
            user.save()

            subject = "Welcome to Global Financial World - Your Account is Ready"
            message = f"""
                Hi {user.first_name},

                Thank you for your request! Your account has been created and you are now logged in.

                For future logins, please use the credentials below. We recommend changing your password from your dashboard.

                Email: {user.email}
                Temporary Password: {temp_password}

                Thanks,
                The Global Financial World Team
                """
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
            )

        quote_request = QuoteRequest.objects.create(user=user, **validated_data)
        quote_request.created_user = user
        order = Order.objects.create(user=user, plan=plan, quote_request=quote_request, status=Order.Status.PENDING)
        if plan:
            Milestone.objects.create(order=order, title=f"Initial payment for {plan.name}", amount=plan.price, status=Milestone.Status.PENDING)
        
        return quote_request
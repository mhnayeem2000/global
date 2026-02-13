from rest_framework import serializers
from .models import User, Profile
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.db.models import Sum, Count


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['company_name', 'phone_number']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'profile']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value
    

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        user_serializer = UserSerializer(self.user)
        data['user'] = user_serializer.data
        
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, required=True, min_length=8)
    role = serializers.ChoiceField(choices=[User.Role.CUSTOMER, User.Role.EMPLOYEE])
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name', 'role', 'token')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def get_token(self, user):
        if user.is_active:
            tokens = RefreshToken.for_user(user)
            return {
                'refresh': str(tokens),
                'access': str(tokens.access_token)
            }
        return None

    def create(self, validated_data):
        email = validated_data['email']
        role = validated_data['role']

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        is_active = False
        if role == User.Role.CUSTOMER:
            is_active = True
        
        user = User.objects.create(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=role,
            is_active=is_active
        )
        user.set_password(validated_data['password'])
        user.save()

        return user

class EmployeeManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']


class UserManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'role',
            'is_active', 
            'date_joined',
        ]
        read_only_fields = ['email', 'date_joined']

class MyProfileSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='profile.company_name', allow_blank=True, required=False)
    phone_number = serializers.CharField(source='profile.phone_number', allow_blank=True, required=False)
    order_stats = serializers.SerializerMethodField()
    financial_stats = serializers.SerializerMethodField()
    transaction_history = serializers.SerializerMethodField()
    schedule_stats = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role',
            'company_name', 'phone_number',
            'order_stats',     
            'financial_stats',  
            'transaction_history' ,
            'schedule_stats',
        ]
        read_only_fields = ['email', 'role', 'id', 'order_stats', 'financial_stats', 'transaction_history']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        profile, created = Profile.objects.get_or_create(user=instance)
        
        instance = super().update(instance, validated_data)

        if profile_data:
            profile.company_name = profile_data.get('company_name', profile.company_name)
            profile.phone_number = profile_data.get('phone_number', profile.phone_number)
            profile.save()
        return instance


    def get_order_stats(self, obj):
        from ecommerce.models import Order
        user_orders = Order.objects.filter(user=obj)
        
        return {
            "total_orders": user_orders.count(),
            "active_running": user_orders.filter(status=Order.Status.ACTIVE).count(),
            "awaiting_payment": user_orders.filter(status=Order.Status.AWAITING_PAYMENT).count(),
            "completed": user_orders.filter(status=Order.Status.PAID).count(),
            "cancelled_rejected": user_orders.filter(status=Order.Status.CANCELLED).count(),
        }

    def get_financial_stats(self, obj):
        from ecommerce.models import Transaction
        from billing.models import Milestone
        from django.db.models import Sum

        total_spent = Transaction.objects.filter(
            order__user=obj, 
            status=Transaction.Status.SUCCESS
        ).aggregate(total=Sum('amount'))['total'] or 0.00
        total_pending = Milestone.objects.filter(
            order__user=obj,
            status='PENDING' 
        ).aggregate(total=Sum('amount'))['total'] or 0.00
        
        return {
            "total_spend_money": total_spent,
            "total_pending_money": total_pending 
        }

    def get_transaction_history(self, obj):

        from ecommerce.models import Transaction
        from ecommerce.serializers import TransactionSerializer 
        transactions = Transaction.objects.filter(order__user=obj).order_by('-timestamp')
        return TransactionSerializer(transactions, many=True).data

    def get_schedule_stats(self, obj):
            from scheduling.models import Appointment
            my_schedules = Appointment.objects.filter(employee=obj)
            
            return {
                "total_schedules_handled": my_schedules.count(),
                "pending_requests": my_schedules.filter(status=Appointment.Status.PENDING).count(),
                "active_upcoming": my_schedules.filter(status=Appointment.Status.CONFIRMED).count(),
                "completed_schedules": my_schedules.filter(status=Appointment.Status.COMPLETED).count(),
                "cancelled_schedules": my_schedules.filter(status=Appointment.Status.CANCELLED).count(),
            }

class RequestPasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)

    class Meta:
        fields = ['email']

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value

    def send_password_reset_email(self, email):
        user = User.objects.get(email=email)
        
        token_generator = PasswordResetTokenGenerator()
        uidb64 = urlsafe_base64_encode(smart_bytes(user.pk))
        token = token_generator.make_token(user)
        
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uidb64}/{token}/"
        
        subject = "Password Reset Request for Your Global Financial World Account"
        message = f"""
                Hi {user.first_name},

                We received a request to reset your password. Please click the link below to set a new password:

                {reset_url}

                If you did not request a password reset, you can safely ignore this email.

                Thanks,
                The Global Financial World Team
                """
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False
        )


class SetNewPasswordSerializer(serializers.Serializer):

    password = serializers.CharField(min_length=8, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True)

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)
            
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise serializers.ValidationError('The reset link is invalid or has expired.', code='authorization')

            user.set_password(password)
            user.save()
            
            return user
        except (ValueError, TypeError, OverflowError, User.DoesNotExist, UnicodeDecodeError) as e:
            raise serializers.ValidationError('The reset link is invalid or has expired.', code='authorization')



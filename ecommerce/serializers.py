from rest_framework import serializers
from django.db import models
from services.models import Plan
from .models import Order, Transaction
from decimal import Decimal



try:
    from billing.serializers import MilestoneSerializer
    from communications.serializers import WorkUpdateSerializer, ChatMessageSerializer
    from reviews.serializers import ReviewSerializer
except ImportError:
    MilestoneSerializer = serializers.Serializer()
    WorkUpdateSerializer = serializers.Serializer()
    ChatMessageSerializer = serializers.Serializer()
    ReviewSerializer = serializers.Serializer()

class TransactionSerializer(serializers.ModelSerializer):
    customer_email = serializers.EmailField(source='order.user.email', read_only=True)
    plan_name = serializers.CharField(source='order.plan.name', read_only=True)
    milestone_title = serializers.CharField(source='milestone.title', read_only=True)
    user_id = serializers.IntegerField(source='order.user.id', read_only=True)
    user_name = serializers.CharField(source='order.user.get_full_name', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id',
            'order',        
            'milestone',      
            'customer_email', 
            'plan_name',      
            'milestone_title',
            'amount',         
            'status',        
            'timestamp',     
            'provider_name',  
            'gateway_txid_out', 
            'gateway_coin_type', 
            'gateway_value_in_coin', 
            'proof_screenshot',
            'proof_reference_number',
            'user_id',
            'user_name',
        ]
        read_only_fields = ['status', 'amount', 'order', 'milestone', 'provider_name']

class OrderListSerializer(serializers.ModelSerializer):

    plan_details = serializers.StringRelatedField(source='plan')
    plan_price = serializers.DecimalField(source='plan.price', read_only=True, max_digits=10, decimal_places=2)
    plan = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all())  

    class Meta:
        model = Order
        fields = ['id', 'plan', 'plan_details', 'plan_price', 'status', 'created_at']





class OrderDetailSerializer(serializers.ModelSerializer):

    plan_details = serializers.StringRelatedField(source='plan')
    plan_price = serializers.DecimalField(source='plan.price', read_only=True, max_digits=10, decimal_places=2)
    transactions = TransactionSerializer(many=True, read_only=True)
    milestones = MilestoneSerializer(many=True, read_only=True)
    work_updates = WorkUpdateSerializer(many=True, read_only=True)
    chat_messages = ChatMessageSerializer(many=True, read_only=True)
    review = ReviewSerializer(read_only=True)

    total_budget = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    remaining_balance = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'plan', 'plan_details', 'plan_price', 'status', 'created_at', 'user',
            'total_budget', 'total_paid', 'remaining_balance',
            'transactions', 
            'milestones',
            'work_updates',
            'chat_messages',
            'review',
            'quote_request'
        ]

    def get_total_budget(self, obj):
        return obj.milestones.aggregate(total=models.Sum('amount'))['total'] or 0.00
    
    def get_total_paid(self, obj):
        return obj.milestones.filter(status='PAID').aggregate(total=models.Sum('amount'))['total'] or 0.00

    def get_remaining_balance(self, obj):
        return Decimal(self.get_total_budget(obj)) - Decimal(self.get_total_paid(obj))

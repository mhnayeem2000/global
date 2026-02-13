from rest_framework import serializers
from .models import PaymentProvider

class PaymentProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentProvider
        fields = [
            'id', 'title', 'provider_name_code', 'logo', 'description', 
            'processing_fee_percentage', 'type', 'min_amount', 'max_amount'
        ]
class PaymentProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentProvider
        fields = '__all__'        
from rest_framework import serializers
from .models import Service, Plan, Feature
from reviews.serializers import ReviewSerializer, FAQSerializer

class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['id', 'description']

class PlanSerializer(serializers.ModelSerializer):
    features = FeatureSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True) 
    faqs = FAQSerializer(many=True, read_only=True)

    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'slug', 'description','service',
            'price', 'billing_cycle', 'features', 'reviews', 'faqs'
        ] 

class ServiceSerializer(serializers.ModelSerializer):
    plans = PlanSerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = ['id', 'name', 'slug', 'description', 'is_product', 'plans']

class SimplePlanSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = Plan
        fields = ['id', 'name', 'service_name']

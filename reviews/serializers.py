# reviews/serializers.py
from rest_framework import serializers
from .models import Review, FAQ
from users.serializers import UserSerializer

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'order', 'plan', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ('user', 'plan')

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'plan', 'question', 'answer']
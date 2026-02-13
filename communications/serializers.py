from rest_framework import serializers
from .models import WorkUpdate, ChatMessage
from users.serializers import UserSerializer
from services.serializers import SimplePlanSerializer

class WorkUpdateSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = WorkUpdate
        fields = ['id', 'order', 'author', 'title', 'description', 'attachment', 'link', 'created_at']
        read_only_fields = ['author']


class ChatMessageSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    plan = SimplePlanSerializer(source='order.plan', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'order','plan', 'author', 'message', 'timestamp']
        read_only_fields = ['author']
from rest_framework import viewsets
from .models import WorkUpdate, ChatMessage
from .serializers import WorkUpdateSerializer, ChatMessageSerializer
from users.permissions import IsEmployeeOrOwner
from rest_framework.permissions import IsAuthenticated

class WorkUpdateViewSet(viewsets.ModelViewSet):
    queryset = WorkUpdate.objects.all()
    serializer_class = WorkUpdateSerializer
    permission_classes = [IsEmployeeOrOwner] 

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class ChatMessageViewSet(viewsets.ModelViewSet):
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
from rest_framework.routers import DefaultRouter
from .views import WorkUpdateViewSet, ChatMessageViewSet

router = DefaultRouter()

router.register(r'work-updates', WorkUpdateViewSet)
router.register(r'chat-messages', ChatMessageViewSet)
urlpatterns = router.urls
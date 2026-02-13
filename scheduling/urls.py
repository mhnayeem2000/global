from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeAvailabilityViewSet, AppointmentViewSet, PublicEmployeeListView, SchedulingView

router = DefaultRouter()
router.register(r'availabilities', EmployeeAvailabilityViewSet, basename='employee-availability')
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('', include(router.urls)),
    path('available-slots/', SchedulingView.as_view(), name='available-slots'),
    path('public-employees/', PublicEmployeeListView.as_view(), name='public-employees'),

]
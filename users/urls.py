from django.urls import path, include
from .views import MyProfileViewSet, RequestPasswordResetEmailView, SetNewPasswordView , UserManagementViewSet,  ApproveEmployeeView, PendingEmployeeListView, ChangePasswordView , UserRegistrationView
from rest_framework.routers import DefaultRouter 


router = DefaultRouter()
router.register(r'management', UserManagementViewSet, basename='user-management')

my_profile_view = MyProfileViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update'
})


urlpatterns = [

    path('', include(router.urls)),

    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('pending-employees/', PendingEmployeeListView.as_view(), name='pending-employees'),
    path('approve-employee/<int:user_id>/', ApproveEmployeeView.as_view(), name='approve-employee'),
    path('me/', my_profile_view, name='my-profile'),
    path('request-reset-password/', RequestPasswordResetEmailView.as_view(), name='request-reset-password'),
    path('reset-password-confirm/', SetNewPasswordView.as_view(), name='reset-password-confirm'),

]

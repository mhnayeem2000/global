from django.urls import path
from .views import AdminDashboardView, CustomerDashboardView, SiteSettingsView

urlpatterns = [
    path('dashboard/customer', CustomerDashboardView.as_view(), name='customer-dashboard'),
    path('dashboard/admin/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('site-settings/', SiteSettingsView.as_view(), name='site-settings'),

]
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from users.views import MyTokenObtainPairView



urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/', include('services.urls')),
    path('api/', include('quotes.urls')),
    path('api/', include('ecommerce.urls')),
    path('api/', include('dashboard.urls')),
    path('api/users/', include('users.urls')),
    path('api/', include('billing.urls')),
    path('api/', include('communications.urls')),
    path('api/', include('reviews.urls')),
    path('api/', include('payments.urls')),
    path('api/', include('scheduling.urls')), 

    
    #path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),

    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),  # JSON schema
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    
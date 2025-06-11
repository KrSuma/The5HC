"""
API URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)

from .views import (
    ClientViewSet, AssessmentViewSet, SessionPackageViewSet,
    SessionViewSet, PaymentViewSet, UserViewSet,
    CustomTokenObtainPairView
)

app_name = 'api'

# Create router
router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'assessments', AssessmentViewSet, basename='assessment')
router.register(r'packages', SessionPackageViewSet, basename='package')
router.register(r'sessions', SessionViewSet, basename='session')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
    
    # Router URLs
    path('', include(router.urls)),
]
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
    CustomTokenObtainPairView,
    QuestionCategoryViewSet, MultipleChoiceQuestionViewSet,
    MCQAssessmentAPIView, MCQAnalyticsViewSet
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

# MCQ endpoints
router.register(r'mcq/categories', QuestionCategoryViewSet, basename='mcq-category')
router.register(r'mcq/questions', MultipleChoiceQuestionViewSet, basename='mcq-question')
router.register(r'mcq/analytics', MCQAnalyticsViewSet, basename='mcq-analytics')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
    
    # MCQ Assessment endpoints (custom viewset)
    path('assessments/<int:pk>/mcq/', 
         MCQAssessmentAPIView.as_view({'get': 'get_mcq_status'}), 
         name='assessment-mcq-status'),
    path('assessments/<int:pk>/mcq/responses/', 
         MCQAssessmentAPIView.as_view({
             'post': 'submit_responses',
             'patch': 'update_responses',
             'delete': 'clear_responses'
         }), 
         name='assessment-mcq-responses'),
    
    # Router URLs
    path('', include(router.urls)),
]
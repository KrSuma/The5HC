from django.urls import path
from . import views

app_name = 'trainers'

urlpatterns = [
    # Trainer profile URLs
    path('', views.trainer_list_view, name='list'),
    path('<int:pk>/', views.trainer_detail_view, name='detail'),
    path('profile/edit/', views.trainer_profile_edit_view, name='profile_edit'),
    path('<int:pk>/edit/', views.trainer_profile_edit_view, name='edit'),
    path('<int:pk>/deactivate/', views.trainer_deactivate_view, name='deactivate'),
    path('analytics/', views.trainer_analytics_view, name='analytics'),
    path('<int:pk>/analytics/', views.trainer_analytics_view, name='trainer_analytics'),
    
    # Organization management
    path('organization/edit/', views.organization_edit_view, name='organization_edit'),
    path('organization/switch/', views.organization_switch_view, name='organization_switch'),
    path('organization/dashboard/', views.organization_dashboard_view, name='organization_dashboard'),
    
    # Invitation management
    path('invite/', views.trainer_invite_view, name='invite'),
    path('invitation/<int:pk>/cancel/', views.invitation_cancel_view, name='invitation_cancel'),
    
    # Notifications
    path('notifications/', views.notification_list_view, name='notifications'),
    path('notifications/<int:pk>/read/', views.notification_mark_read_view, name='notification_mark_read'),
    path('notifications/badge/', views.notification_badge_view, name='notification_badge'),
]
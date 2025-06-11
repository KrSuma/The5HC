from django.urls import path
from . import views

app_name = 'sessions'

urlpatterns = [
    # Session packages
    path('packages/', views.session_package_list_view, name='package_list'),
    path('packages/add/', views.session_package_add_view, name='package_add'),
    path('packages/<int:pk>/', views.session_package_detail_view, name='package_detail'),
    
    # Sessions
    path('', views.session_list_view, name='session_list'),
    path('add/', views.session_add_view, name='session_add'),
    path('<int:pk>/complete/', views.session_complete_view, name='session_complete'),
    path('calendar/', views.session_calendar_view, name='session_calendar'),
    
    # Payments
    path('payments/add/', views.payment_add_view, name='payment_add'),
    
    # AJAX endpoints
    path('ajax/get-client-packages/', views.get_client_packages_ajax, name='get_client_packages'),
    path('ajax/calculate-fees/', views.calculate_package_fees_ajax, name='calculate_fees'),
]
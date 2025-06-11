from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.client_list_view, name='list'),
    path('add/', views.client_add_view, name='add'),
    path('<int:pk>/', views.client_detail_view, name='detail'),
    path('<int:pk>/edit/', views.client_edit_view, name='edit'),
    path('<int:pk>/delete/', views.client_delete_view, name='delete'),
    path('export/', views.client_export_view, name='export'),
    
    # HTMX validation endpoints
    path('validate/name/', views.validate_client_name, name='validate_name'),
    path('validate/email/', views.validate_client_email, name='validate_email'),
    path('validate/phone/', views.validate_client_phone, name='validate_phone'),
]
"""
Test URLs for refactored client views.
These URLs allow testing the refactored views alongside the original ones.
"""
from django.urls import path
from . import views_refactored, views_with_mixins

app_name = 'clients_test'

urlpatterns = [
    # Function-based views with service layer
    path('refactored/', views_refactored.client_list_view_refactored, name='client_list_refactored'),
    path('refactored/<int:pk>/', views_refactored.client_detail_view_refactored, name='client_detail_refactored'),
    path('refactored/add/', views_refactored.client_add_view_refactored, name='client_add_refactored'),
    path('refactored/<int:pk>/edit/', views_refactored.client_edit_view_refactored, name='client_edit_refactored'),
    path('refactored/<int:pk>/delete/', views_refactored.client_delete_view_refactored, name='client_delete_refactored'),
    
    # Class-based views with mixins and service layer
    path('mixins/', views_with_mixins.ClientListViewWithMixins.as_view(), name='client_list_mixins'),
    path('mixins/<int:pk>/', views_with_mixins.ClientDetailViewWithMixins.as_view(), name='client_detail_mixins'),
    path('mixins/add/', views_with_mixins.ClientCreateViewWithMixins.as_view(), name='client_add_mixins'),
    path('mixins/<int:pk>/edit/', views_with_mixins.ClientUpdateViewWithMixins.as_view(), name='client_edit_mixins'),
    path('mixins/<int:pk>/delete/', views_with_mixins.ClientDeleteViewWithMixins.as_view(), name='client_delete_mixins'),
]
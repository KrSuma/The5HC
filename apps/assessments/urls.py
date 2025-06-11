from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    # List and search
    path('', views.assessment_list_view, name='list'),
    
    # CRUD operations
    path('add/', views.assessment_add_view, name='add'),
    path('<int:pk>/', views.assessment_detail_view, name='detail'),
    path('<int:pk>/delete/', views.assessment_delete_view, name='delete'),
    path('<int:pk>/report/', views.assessment_report_view, name='report'),
    
    # AJAX score calculations
    path('ajax/calculate-pushup-score/', views.calculate_push_up_score_ajax, name='calculate_pushup_score'),
    path('ajax/calculate-balance-score/', views.calculate_balance_score_ajax, name='calculate_balance_score'),
    path('ajax/calculate-toe-touch-score/', views.calculate_toe_touch_score_ajax, name='calculate_toe_touch_score'),
    path('ajax/calculate-farmer-score/', views.calculate_farmer_score_ajax, name='calculate_farmer_score'),
]
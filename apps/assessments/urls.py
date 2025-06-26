from django.urls import path
from . import views
from . import views_optimized

app_name = 'assessments'

urlpatterns = [
    # List and search
    path('', views.assessment_list_view, name='list'),
    
    # CRUD operations
    path('add/', views.assessment_add_view, name='add'),
    path('<int:pk>/', views.assessment_detail_view, name='detail'),
    path('<int:pk>/delete/', views.assessment_delete_view, name='delete'),
    
    # Refactored forms (demonstration)
    path('add-refactored/', views.assessment_add_refactored_view, name='add_refactored'),
    path('<int:pk>/edit-refactored/', views.assessment_edit_refactored_view, name='edit_refactored'),
    
    # Comparison
    path('compare/', views.assessment_compare_view, name='compare'),
    
    # MCQ Assessment
    path('<int:assessment_id>/mcq/', views.mcq_assessment_view, name='mcq'),
    path('<int:assessment_id>/mcq/save/', views.mcq_save_view, name='mcq_save'),
    path('<int:assessment_id>/mcq/quick/', views.mcq_quick_form_view, name='mcq_quick'),
    path('<int:assessment_id>/mcq/print/', views.mcq_print_view, name='mcq_print'),
    
    # AJAX score calculations
    path('ajax/calculate-pushup-score/', views.calculate_push_up_score_ajax, name='calculate_pushup_score'),
    path('ajax/calculate-balance-score/', views.calculate_balance_score_ajax, name='calculate_balance_score'),
    path('ajax/calculate-toe-touch-score/', views.calculate_toe_touch_score_ajax, name='calculate_toe_touch_score'),
    path('ajax/calculate-farmer-score/', views.calculate_farmer_score_ajax, name='calculate_farmer_score'),
    path('ajax/calculate-harvard-score/', views.calculate_harvard_score_ajax, name='calculate_harvard_score'),
    
    # Timer test page
    path('timer-test/', views.timer_test_view, name='timer_test'),
    path('timer-debug/', views.timer_debug_view, name='timer_debug'),
    path('timer-inline-test/', views.timer_inline_test_view, name='timer_inline_test'),
    
    # Optimized views with new model relationships
    path('optimized/', views_optimized.assessment_list_optimized_view, name='list_optimized'),
    path('optimized/<int:pk>/', views_optimized.assessment_detail_optimized_view, name='detail_optimized'),
    path('optimized/compare/', views_optimized.assessment_comparison_optimized_view, name='compare_optimized'),
]
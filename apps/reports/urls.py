from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # List views
    path('', views.report_list, name='list'),
    path('client/<int:client_id>/', views.client_reports, name='client_reports'),
    path('assessment/<int:assessment_id>/', views.assessment_reports, name='assessment_reports'),
    
    # Report generation
    path('generate/<int:assessment_id>/', views.generate_report, name='generate'),
    
    # Report actions
    path('<int:report_id>/download/', views.download_report, name='download'),
    path('<int:report_id>/view/', views.view_report, name='view'),
    path('<int:report_id>/delete/', views.delete_report, name='delete'),
]
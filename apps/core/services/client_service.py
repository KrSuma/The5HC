"""
Client service handling all business logic related to clients.
"""
from datetime import timedelta
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal

from django.db import transaction
from django.db.models import (
    Q, F, Count, Avg, Sum, Max, 
    ExpressionWrapper, FloatField, 
    Subquery, OuterRef, Exists
)
from django.db.models.query import QuerySet
from django.utils import timezone

from .base import BaseService
from apps.clients.models import Client
from apps.assessments.models import Assessment
from apps.sessions.models import SessionPackage, Session


class ClientService(BaseService):
    """
    Service class for client-related business logic.
    
    This service encapsulates all complex business logic related to clients,
    including search, filtering, statistics calculation, and data export.
    """
    
    model = Client
    
    def get_annotated_queryset(self) -> QuerySet:
        """
        Get queryset with all necessary annotations for client listing.
        
        Returns:
            QuerySet with calculated fields like BMI, latest score, activity status
        """
        queryset = self.get_queryset().select_related('trainer')
        
        # Calculate BMI
        queryset = queryset.annotate(
            calculated_bmi=ExpressionWrapper(
                F('weight') / (F('height') * F('height') / 10000),
                output_field=FloatField()
            )
        )
        
        # Get latest assessment score
        latest_assessment = Assessment.objects.filter(
            client=OuterRef('pk')
        ).order_by('-date').values('overall_score')[:1]
        
        queryset = queryset.annotate(
            latest_score=Subquery(latest_assessment)
        )
        
        # Check activity status (session or assessment in last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        recent_session = Session.objects.filter(
            client=OuterRef('pk'),
            session_date__gte=thirty_days_ago
        )
        
        recent_assessment = Assessment.objects.filter(
            client=OuterRef('pk'),
            date__gte=thirty_days_ago
        )
        
        queryset = queryset.annotate(
            has_recent_activity=Exists(recent_session) | Exists(recent_assessment)
        )
        
        return queryset
    
    def search_and_filter(self, filters: Dict[str, Any]) -> QuerySet:
        """
        Apply search and filter criteria to client queryset.
        
        Args:
            filters: Dictionary of filter criteria from search form
            
        Returns:
            Filtered QuerySet
        """
        queryset = self.get_annotated_queryset()
        
        # Text search
        search = filters.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        
        # Gender filter
        gender = filters.get('gender')
        if gender:
            queryset = queryset.filter(gender=gender)
        
        # Age range
        age_min = filters.get('age_min')
        if age_min:
            queryset = queryset.filter(age__gte=age_min)
        
        age_max = filters.get('age_max')
        if age_max:
            queryset = queryset.filter(age__lte=age_max)
        
        # BMI range filter
        bmi_range = filters.get('bmi_range')
        if bmi_range:
            bmi_filters = {
                'underweight': Q(calculated_bmi__lt=18.5),
                'normal': Q(calculated_bmi__gte=18.5, calculated_bmi__lt=23),
                'overweight': Q(calculated_bmi__gte=23, calculated_bmi__lt=25),
                'obese': Q(calculated_bmi__gte=25)
            }
            if bmi_range in bmi_filters:
                queryset = queryset.filter(bmi_filters[bmi_range])
        
        # Registration date range
        registration_start = filters.get('registration_start')
        if registration_start:
            queryset = queryset.filter(created_at__date__gte=registration_start)
        
        registration_end = filters.get('registration_end')
        if registration_end:
            queryset = queryset.filter(created_at__date__lte=registration_end)
        
        # Medical conditions
        has_medical = filters.get('has_medical_conditions')
        if has_medical == 'yes':
            queryset = queryset.exclude(medical_conditions='').exclude(medical_conditions__isnull=True)
        elif has_medical == 'no':
            queryset = queryset.filter(Q(medical_conditions='') | Q(medical_conditions__isnull=True))
        
        # Athletic background
        has_athletic = filters.get('has_athletic_background')
        if has_athletic == 'yes':
            queryset = queryset.exclude(athletic_background='').exclude(athletic_background__isnull=True)
        elif has_athletic == 'no':
            queryset = queryset.filter(Q(athletic_background='') | Q(athletic_background__isnull=True))
        
        # Activity status
        activity_status = filters.get('activity_status')
        if activity_status == 'active':
            queryset = queryset.filter(has_recent_activity=True)
        elif activity_status == 'inactive':
            queryset = queryset.filter(has_recent_activity=False)
        
        # Latest score range
        score_range = filters.get('latest_score_range')
        if score_range:
            score_filters = {
                '90-100': Q(latest_score__gte=90),
                '80-89': Q(latest_score__gte=80, latest_score__lt=90),
                '70-79': Q(latest_score__gte=70, latest_score__lt=80),
                '60-69': Q(latest_score__gte=60, latest_score__lt=70),
                '0-59': Q(latest_score__lt=60)
            }
            if score_range in score_filters:
                queryset = queryset.filter(score_filters[score_range])
        
        # Sorting
        sort_by = filters.get('sort_by', '-created_at')
        queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_client_statistics(self, client: Client) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics for a client.
        
        Args:
            client: Client instance
            
        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_assessments': client.assessments.count(),
            'total_sessions': client.sessions.count(),
            'active_packages': client.session_packages.filter(is_active=True).count(),
            'total_packages': client.session_packages.count(),
        }
        
        # Assessment statistics
        assessment_stats = client.assessments.aggregate(
            avg_score=Avg('overall_score'),
            max_score=Max('overall_score'),
            latest_date=Max('date')
        )
        stats.update(assessment_stats)
        
        # Session statistics
        session_stats = client.sessions.aggregate(
            total_sessions=Count('id'),
            completed_sessions=Count('id', filter=Q(status='completed')),
            cancelled_sessions=Count('id', filter=Q(status='cancelled'))
        )
        stats.update(session_stats)
        
        # Financial statistics
        financial_stats = client.session_packages.aggregate(
            total_revenue=Sum('net_amount'),
            total_gross=Sum('total_amount'),
            avg_package_value=Avg('total_amount')
        )
        stats.update(financial_stats)
        
        # Activity status
        thirty_days_ago = timezone.now() - timedelta(days=30)
        stats['is_active'] = (
            client.sessions.filter(session_date__gte=thirty_days_ago).exists() or
            client.assessments.filter(date__gte=thirty_days_ago).exists()
        )
        
        # Days since last activity
        last_session = client.sessions.order_by('-session_date').first()
        last_assessment = client.assessments.order_by('-date').first()
        
        last_activity_date = None
        if last_session and last_assessment:
            last_activity_date = max(last_session.session_date, last_assessment.date)
        elif last_session:
            last_activity_date = last_session.session_date
        elif last_assessment:
            last_activity_date = last_assessment.date
        
        if last_activity_date:
            stats['days_since_last_activity'] = (timezone.now().date() - last_activity_date).days
        else:
            stats['days_since_last_activity'] = None
        
        return stats
    
    def get_client_timeline(self, client: Client, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get combined timeline of client activities.
        
        Args:
            client: Client instance
            limit: Maximum number of items to return
            
        Returns:
            List of timeline events sorted by date
        """
        timeline = []
        
        # Add assessments
        for assessment in client.assessments.order_by('-date')[:limit]:
            timeline.append({
                'type': 'assessment',
                'date': assessment.date,
                'title': '체력 평가 완료',
                'description': f'종합 점수: {assessment.overall_score:.1f}점',
                'icon': '📊',
                'object': assessment
            })
        
        # Add sessions
        for session in client.sessions.order_by('-session_date')[:limit]:
            timeline.append({
                'type': 'session',
                'date': session.session_date,
                'title': '세션 진행',
                'description': f'상태: {session.get_status_display()}',
                'icon': '🏋️',
                'object': session
            })
        
        # Add package purchases
        for package in client.session_packages.order_by('-created_at')[:limit]:
            timeline.append({
                'type': 'package',
                'date': package.created_at.date(),
                'title': '패키지 구매',
                'description': f'{package.package_name} ({package.total_sessions}회)',
                'icon': '📦',
                'object': package
            })
        
        # Sort by date descending
        timeline.sort(key=lambda x: x['date'], reverse=True)
        
        return timeline[:limit]
    
    def create_client(self, data: Dict[str, Any]) -> Tuple[Optional[Client], bool]:
        """
        Create a new client with validation.
        
        Args:
            data: Client data dictionary
            
        Returns:
            Tuple of (client, success)
        """
        self.clear_errors()
        
        # Validate required fields
        required_fields = ['name', 'gender', 'age', 'height', 'weight']
        for field in required_fields:
            if not data.get(field):
                self.add_error(f"{field}는 필수 입력 항목입니다.")
        
        if self.has_errors:
            return None, False
        
        # Create client
        try:
            with transaction.atomic():
                client = Client(
                    trainer=self.user,
                    **data
                )
                
                if self.save_with_audit(client, action='create'):
                    return client, True
                else:
                    return None, False
                    
        except Exception as e:
            self.add_error(f"고객 생성 중 오류가 발생했습니다: {str(e)}")
            return None, False
    
    def update_client(self, client: Client, data: Dict[str, Any]) -> bool:
        """
        Update client information.
        
        Args:
            client: Client instance to update
            data: Updated data
            
        Returns:
            bool: True if successful
        """
        self.clear_errors()
        
        # Check permission
        if not self.check_permission(client, 'edit'):
            self.add_error("이 고객을 수정할 권한이 없습니다.")
            return False
        
        # Track changed fields for audit
        changed_fields = []
        for field, value in data.items():
            if hasattr(client, field) and getattr(client, field) != value:
                changed_fields.append(field)
                setattr(client, field, value)
        
        if not changed_fields:
            return True  # No changes
        
        # Save with audit
        return self.save_with_audit(
            client, 
            action='update',
            metadata={'changed_fields': changed_fields}
        )
    
    def export_clients_data(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Prepare client data for export.
        
        Args:
            queryset: Filtered queryset of clients
            
        Returns:
            List of dictionaries ready for CSV export
        """
        export_data = []
        
        for client in queryset:
            export_data.append({
                '이름': client.name,
                '성별': client.get_gender_display(),
                '나이': client.age,
                '키(cm)': client.height,
                '체중(kg)': client.weight,
                'BMI': f"{client.calculated_bmi:.1f}" if hasattr(client, 'calculated_bmi') else '',
                '이메일': client.email or '',
                '전화번호': client.phone or '',
                '최근 점수': f"{client.latest_score:.1f}점" if getattr(client, 'latest_score', None) else '-',
                '활동 상태': '활동중' if getattr(client, 'has_recent_activity', False) else '비활동',
                '등록일': client.created_at.strftime('%Y-%m-%d'),
                '의료 상태': '있음' if client.medical_conditions else '없음',
                '운동 경력': '있음' if client.athletic_background else '없음'
            })
        
        return export_data
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for dashboard display.
        
        Returns:
            Dictionary of dashboard metrics
        """
        queryset = self.get_queryset()
        
        # Basic counts
        total_clients = queryset.count()
        
        # Activity metrics
        thirty_days_ago = timezone.now() - timedelta(days=30)
        active_clients = queryset.filter(
            Q(sessions__session_date__gte=thirty_days_ago) |
            Q(assessments__date__gte=thirty_days_ago)
        ).distinct().count()
        
        # New clients this month
        month_start = timezone.now().replace(day=1)
        new_clients_this_month = queryset.filter(
            created_at__gte=month_start
        ).count()
        
        # Assessment metrics
        clients_with_assessments = queryset.filter(
            assessments__isnull=False
        ).distinct().count()
        
        # Average metrics
        avg_metrics = queryset.aggregate(
            avg_age=Avg('age'),
            avg_sessions_per_client=Avg('sessions__pk')
        )
        
        return {
            'total_clients': total_clients,
            'active_clients': active_clients,
            'inactive_clients': total_clients - active_clients,
            'new_clients_this_month': new_clients_this_month,
            'clients_with_assessments': clients_with_assessments,
            'assessment_completion_rate': (
                (clients_with_assessments / total_clients * 100) if total_clients > 0 else 0
            ),
            'avg_age': avg_metrics['avg_age'] or 0,
            'activity_rate': (
                (active_clients / total_clients * 100) if total_clients > 0 else 0
            )
        }
"""
API Views for The5HC
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum, Avg, F
from datetime import datetime, timedelta

from apps.clients.models import Client
from apps.assessments.models import Assessment
from apps.sessions.models import SessionPackage, Session, Payment
from .serializers import (
    UserSerializer, ClientSerializer, ClientListSerializer,
    AssessmentSerializer, AssessmentListSerializer,
    SessionPackageSerializer, SessionSerializer, PaymentSerializer,
    LoginSerializer, ChangePasswordSerializer
)


class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Client CRUD operations
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'phone_number', 'email']
    ordering_fields = ['name', 'created_at', 'age']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter clients by current trainer"""
        return Client.objects.filter(trainer=self.request.user)
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail views"""
        if self.action == 'list':
            return ClientListSerializer
        return ClientSerializer
    
    @action(detail=True, methods=['get'])
    def assessments(self, request, pk=None):
        """Get all assessments for a client"""
        client = self.get_object()
        assessments = Assessment.objects.filter(client=client).order_by('-date')
        serializer = AssessmentListSerializer(assessments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def packages(self, request, pk=None):
        """Get all session packages for a client"""
        client = self.get_object()
        packages = SessionPackage.objects.filter(client=client).order_by('-created_at')
        serializer = SessionPackageSerializer(packages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get client statistics"""
        client = self.get_object()
        
        # Calculate statistics
        stats = {
            'total_assessments': Assessment.objects.filter(client=client).count(),
            'total_packages': SessionPackage.objects.filter(client=client).count(),
            'active_packages': SessionPackage.objects.filter(
                client=client, status='active'
            ).count(),
            'total_sessions': Session.objects.filter(
                package__client=client
            ).count(),
            'completed_sessions': Session.objects.filter(
                package__client=client, attendance_status='present'
            ).count(),
            'latest_assessment': None,
            'average_score': None
        }
        
        # Get latest assessment
        latest_assessment = Assessment.objects.filter(client=client).order_by('-date').first()
        if latest_assessment:
            stats['latest_assessment'] = {
                'date': latest_assessment.date,
                'overall_score': latest_assessment.overall_score
            }
        
        # Calculate average score
        avg_score = Assessment.objects.filter(client=client).aggregate(
            avg_score=Avg('overall_score')
        )
        stats['average_score'] = avg_score['avg_score']
        
        return Response(stats)


class AssessmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Assessment CRUD operations
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['client__name', 'notes']
    ordering_fields = ['date', 'total_score', 'created_at']
    ordering = ['-date']
    
    def get_queryset(self):
        """Filter assessments by current trainer's clients"""
        from apps.trainers.models import Trainer
        trainer = Trainer.objects.get(user=self.request.user)
        queryset = Assessment.objects.filter(trainer=trainer)
        
        # Allow filtering by test variations
        push_up_type = self.request.query_params.get('push_up_type', None)
        if push_up_type:
            queryset = queryset.filter(push_up_type=push_up_type)
        
        test_environment = self.request.query_params.get('test_environment', None)
        if test_environment:
            queryset = queryset.filter(test_environment=test_environment)
        
        # Filter by has variations (assessments with any variation data)
        has_variations = self.request.query_params.get('has_variations', None)
        if has_variations is not None:
            if has_variations.lower() == 'true':
                queryset = queryset.exclude(
                    push_up_type='standard'
                ) | queryset.exclude(
                    farmer_carry_percentage__isnull=True
                ) | queryset.exclude(
                    test_environment='indoor'
                ) | queryset.exclude(
                    temperature__isnull=True
                )
        
        return queryset
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail views"""
        if self.action == 'list':
            return AssessmentListSerializer
        return AssessmentSerializer
    
    @action(detail=True, methods=['get'])
    def comparison(self, request, pk=None):
        """Compare with previous assessment"""
        current_assessment = self.get_object()
        previous_assessment = Assessment.objects.filter(
            client=current_assessment.client,
            date__lt=current_assessment.date
        ).order_by('-date').first()
        
        if not previous_assessment:
            return Response({
                'message': '이전 평가 기록이 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate differences
        comparison = {
            'current': AssessmentSerializer(current_assessment).data,
            'previous': AssessmentSerializer(previous_assessment).data,
            'improvements': {
                'overall_score': (current_assessment.overall_score or 0) - (previous_assessment.overall_score or 0),
                'strength_score': (current_assessment.strength_score or 0) - (previous_assessment.strength_score or 0),
                'mobility_score': (current_assessment.mobility_score or 0) - (previous_assessment.mobility_score or 0),
            }
        }
        
        return Response(comparison)


class SessionPackageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SessionPackage CRUD operations
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SessionPackageSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['client__name', 'package_name']
    ordering_fields = ['created_at', 'is_active']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter packages by current trainer"""
        queryset = SessionPackage.objects.filter(trainer=self.request.user)
        
        # Allow filtering by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Allow filtering by expiration (simplified for now)
        # TODO: Add proper expiration date logic based on actual model fields
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """Get all sessions for a package"""
        package = self.get_object()
        sessions = Session.objects.filter(package=package).order_by('-date')
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        """Get all payments for a package"""
        package = self.get_object()
        payments = Payment.objects.filter(package=package).order_by('-payment_date')
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete_session(self, request, pk=None):
        """Mark a session as completed"""
        package = self.get_object()
        
        # Check if package has remaining sessions
        if package.remaining_sessions <= 0:
            return Response({
                'error': '남은 세션이 없습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new session
        session_data = {
            'package': package.id,
            'session_date': request.data.get('date', datetime.now().date()),
            'session_time': request.data.get('time'),
            'session_duration': request.data.get('duration', 60),
            'session_cost': request.data.get('cost', package.session_price),
            'status': 'completed',
            'notes': request.data.get('notes', '')
        }
        
        serializer = SessionSerializer(data=session_data)
        if serializer.is_valid():
            session = serializer.save()
            # Update remaining sessions
            package.remaining_sessions -= 1
            package.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Session CRUD operations
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SessionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['package__client__name', 'notes']
    ordering_fields = ['session_date', 'created_at']
    ordering = ['-session_date']
    
    def get_queryset(self):
        """Filter sessions by current trainer"""
        queryset = Session.objects.filter(package__trainer=self.request.user)
        
        # Allow filtering by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(session_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(session_date__lte=end_date)
        
        # Allow filtering by attendance status
        attendance = self.request.query_params.get('attendance', None)
        if attendance:
            queryset = queryset.filter(attendance_status=attendance)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Get sessions in calendar format"""
        # Get month and year from query params
        month = int(request.query_params.get('month', datetime.now().month))
        year = int(request.query_params.get('year', datetime.now().year))
        
        # Get sessions for the month
        sessions = self.get_queryset().filter(
            session_date__year=year,
            session_date__month=month
        )
        
        # Group by date
        calendar_data = {}
        for session in sessions:
            date_str = session.session_date.isoformat()
            if date_str not in calendar_data:
                calendar_data[date_str] = []
            
            calendar_data[date_str].append({
                'id': session.id,
                'client_name': session.package.client.name,
                'time': session.session_time.strftime('%H:%M') if session.session_time else '00:00',
                'status': session.status,
                'duration': session.session_duration,
                'cost': str(session.session_cost)
            })
        
        return Response(calendar_data)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Payment CRUD operations
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['client__name', 'description']
    ordering_fields = ['payment_date', 'amount', 'created_at']
    ordering = ['-payment_date']
    
    def get_queryset(self):
        """Filter payments by current trainer"""
        queryset = Payment.objects.filter(trainer=self.request.user)
        
        # Allow filtering by payment method
        method = self.request.query_params.get('method', None)
        if method:
            queryset = queryset.filter(payment_method=method)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get payment summary statistics"""
        # Get date range from query params
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        
        queryset = self.get_queryset()
        
        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)
        
        # Calculate summary
        summary = queryset.aggregate(
            total_amount=Sum('amount'),
            total_payments=Count('id'),
            average_payment=Avg('amount')
        )
        
        # Group by payment method
        by_method = queryset.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        summary['by_method'] = list(by_method)
        
        return Response(summary)


# Authentication Views
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

class CustomTokenObtainPairView(APIView):
    """
    Custom login view that accepts email or username
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email_or_username = serializer.validated_data['email_or_username']
        password = serializer.validated_data['password']
        
        # Try to authenticate with username first, then email
        user = authenticate(request, username=email_or_username, password=password)
        if not user:
            # Try with email
            User = get_user_model()
            try:
                user_obj = User.objects.get(email=email_or_username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if not user:
            return Response({
                'error': '잘못된 인증 정보입니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user profile operations
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        """Only allow users to see their own profile"""
        return get_user_model().objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password"""
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'error': '현재 비밀번호가 올바르지 않습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': '비밀번호가 성공적으로 변경되었습니다.'
        })
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics for current user"""
        user = request.user
        
        # Get active client IDs
        active_client_ids = SessionPackage.objects.filter(
            trainer=user,
            is_active=True
        ).values_list('client_id', flat=True).distinct()
        
        stats = {
            'total_clients': Client.objects.filter(trainer=user).count(),
            'active_clients': Client.objects.filter(
                trainer=user,
                id__in=active_client_ids
            ).count(),
            'total_assessments': Assessment.objects.filter(
                client__trainer=user
            ).count(),
            'active_packages': SessionPackage.objects.filter(
                trainer=user,
                is_active=True
            ).count(),
            'sessions_this_month': Session.objects.filter(
                package__trainer=user,
                session_date__month=datetime.now().month,
                session_date__year=datetime.now().year
            ).count(),
            'revenue_this_month': Payment.objects.filter(
                trainer=user,
                payment_date__month=datetime.now().month,
                payment_date__year=datetime.now().year
            ).aggregate(total=Sum('amount'))['total'] or 0
        }
        
        return Response(stats)

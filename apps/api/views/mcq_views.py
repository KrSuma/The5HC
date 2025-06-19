"""
MCQ (Multiple Choice Questions) API views.

This module provides API endpoints for MCQ functionality including
listing questions, submitting responses, and retrieving results.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.assessments.models import (
    QuestionCategory, MultipleChoiceQuestion,
    QuestionChoice, QuestionResponse, Assessment
)
from apps.trainers.decorators import (
    requires_trainer, organization_member_required
)
from ..serializers.mcq_serializers import (
    QuestionCategorySerializer, MultipleChoiceQuestionSerializer,
    QuestionResponseSerializer, MCQResponseBulkSerializer,
    MCQAssessmentSerializer, QuestionValidationSerializer
)
from apps.api.permissions import IsOwnerOrReadOnly, BelongsToOrganization
from apps.api.filters import QuestionFilter


class MCQPagination(PageNumberPagination):
    """Custom pagination for MCQ endpoints."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema_view(
    list=extend_schema(
        summary="List MCQ categories",
        description="Get all active question categories with statistics",
        tags=["MCQ"]
    ),
    retrieve=extend_schema(
        summary="Get category details",
        description="Get details of a specific question category",
        tags=["MCQ"]
    )
)
class QuestionCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for question categories."""
    
    queryset = QuestionCategory.objects.filter(is_active=True)
    serializer_class = QuestionCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order', 'name']
    ordering = ['order']
    
    def get_queryset(self):
        """Filter by active categories and add annotations."""
        queryset = super().get_queryset()
        
        # Add question count annotation
        queryset = queryset.annotate(
            active_question_count=Count(
                'questions',
                filter=Q(questions__is_active=True)
            )
        )
        
        return queryset
    
    @extend_schema(
        summary="Get category questions",
        description="Get all active questions for a specific category",
        responses={200: MultipleChoiceQuestionSerializer(many=True)},
        tags=["MCQ"]
    )
    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """Get all questions for a specific category."""
        category = self.get_object()
        
        questions = MultipleChoiceQuestion.objects.filter(
            category=category,
            is_active=True
        ).select_related(
            'category', 'depends_on'
        ).prefetch_related(
            'choices'
        ).order_by('order')
        
        serializer = MultipleChoiceQuestionSerializer(
            questions, many=True
        )
        
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List MCQ questions",
        description="Get paginated list of all active questions with filtering and search",
        parameters=[
            OpenApiParameter(
                name='category',
                description='Filter by category slug',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='type',
                description='Filter by question type',
                required=False,
                type=str,
                enum=['single', 'multiple', 'scale', 'text']
            ),
            OpenApiParameter(
                name='required',
                description='Filter by required status',
                required=False,
                type=bool
            ),
            OpenApiParameter(
                name='search',
                description='Search in question text and help text',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='q',
                description='Alternative search parameter',
                required=False,
                type=str
            )
        ],
        tags=["MCQ"]
    ),
    retrieve=extend_schema(
        summary="Get question details",
        description="Get details of a specific question including choices",
        tags=["MCQ"]
    )
)
class MultipleChoiceQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for multiple choice questions."""
    
    queryset = MultipleChoiceQuestion.objects.filter(is_active=True)
    serializer_class = MultipleChoiceQuestionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MCQPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = QuestionFilter
    search_fields = ['question_text', 'question_text_ko', 'help_text', 'help_text_ko']
    ordering_fields = ['order', 'created_at']
    ordering = ['category__order', 'order']
    
    def get_queryset(self):
        """Optimize query with related data."""
        queryset = super().get_queryset()
        
        # Prefetch related data
        queryset = queryset.select_related(
            'category', 'depends_on'
        ).prefetch_related(
            'choices'
        )
        
        # Filter by search query if provided
        search_query = self.request.query_params.get('q', None)
        if search_query:
            queryset = queryset.filter(
                Q(question_text__icontains=search_query) |
                Q(question_text_ko__icontains=search_query) |
                Q(help_text__icontains=search_query) |
                Q(help_text_ko__icontains=search_query)
            )
        
        return queryset
    
    @extend_schema(
        summary="Validate question answer",
        description="Validate an answer and calculate points earned",
        request=QuestionValidationSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'valid': {'type': 'boolean'},
                    'points': {'type': 'number'},
                    'max_points': {'type': 'number'}
                }
            }
        },
        tags=["MCQ"]
    )
    @action(detail=False, methods=['post'])
    def validate(self, request):
        """Validate an answer for a question."""
        serializer = QuestionValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        question = serializer.validated_data['question']
        
        # Calculate points based on answer
        points = 0
        if question.question_type == 'text':
            # Text questions get full points if answered
            if serializer.validated_data.get('answer'):
                points = question.points
        else:
            # Calculate points from selected choices
            choice_ids = serializer.validated_data.get('selected_choices', [])
            choices = QuestionChoice.objects.filter(
                id__in=choice_ids,
                question=question
            )
            points = sum(choice.points for choice in choices)
        
        return Response({
            'valid': True,
            'points': points,
            'max_points': question.points
        })
    
    @extend_schema(
        summary="Get questions by IDs",
        description="Get multiple questions by providing a list of IDs",
        request={
            'type': 'object',
            'properties': {
                'question_ids': {
                    'type': 'array',
                    'items': {'type': 'integer'}
                }
            },
            'required': ['question_ids']
        },
        responses={200: MultipleChoiceQuestionSerializer(many=True)},
        tags=["MCQ"]
    )
    @action(detail=False, methods=['post'])
    def batch(self, request):
        """Get multiple questions by IDs."""
        question_ids = request.data.get('question_ids', [])
        
        if not question_ids:
            return Response(
                {'error': '질문 ID가 제공되지 않았습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        questions = self.get_queryset().filter(id__in=question_ids)
        serializer = self.get_serializer(questions, many=True)
        
        return Response(serializer.data)


class MCQAssessmentAPIView(viewsets.GenericViewSet):
    """API endpoints for MCQ assessment operations."""
    
    permission_classes = [IsAuthenticated, BelongsToOrganization]
    
    def get_assessment(self, assessment_id):
        """Get assessment and check permissions."""
        assessment = get_object_or_404(
            Assessment.objects.select_related('client', 'trainer'),
            id=assessment_id
        )
        
        # Check organization membership
        if assessment.trainer.organization != self.request.user.trainer.organization:
            self.permission_denied(
                self.request,
                message="이 평가에 접근할 권한이 없습니다."
            )
        
        return assessment
    
    @action(detail=True, methods=['get'], url_path='mcq')
    def get_mcq_status(self, request, pk=None):
        """Get MCQ status and results for an assessment."""
        assessment = self.get_assessment(pk)
        
        serializer = MCQAssessmentSerializer(assessment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='mcq/responses')
    def submit_responses(self, request, pk=None):
        """Submit MCQ responses for an assessment."""
        assessment = self.get_assessment(pk)
        
        # Check if user can modify this assessment
        if assessment.trainer != request.user.trainer:
            return Response(
                {'error': '이 평가를 수정할 권한이 없습니다.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MCQResponseBulkSerializer(
            data=request.data,
            context={'assessment': assessment}
        )
        serializer.is_valid(raise_exception=True)
        
        # Save responses
        result = serializer.save()
        
        # Update assessment MCQ scores
        assessment.calculate_mcq_scores()
        
        # Return updated MCQ status
        mcq_serializer = MCQAssessmentSerializer(assessment)
        return Response(
            mcq_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['patch'], url_path='mcq/responses')
    def update_responses(self, request, pk=None):
        """Update existing MCQ responses."""
        # Same as submit but with PATCH
        return self.submit_responses(request, pk)
    
    @action(detail=True, methods=['delete'], url_path='mcq/responses')
    def clear_responses(self, request, pk=None):
        """Clear all MCQ responses for an assessment."""
        assessment = self.get_assessment(pk)
        
        # Check if user can modify this assessment
        if assessment.trainer != request.user.trainer:
            return Response(
                {'error': '이 평가를 수정할 권한이 없습니다.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete all responses
        QuestionResponse.objects.filter(assessment=assessment).delete()
        
        # Clear MCQ scores
        assessment.knowledge_score = None
        assessment.lifestyle_score = None
        assessment.readiness_score = None
        assessment.comprehensive_score = None
        assessment.save()
        
        return Response(
            {'message': 'MCQ 응답이 삭제되었습니다.'},
            status=status.HTTP_204_NO_CONTENT
        )


class MCQAnalyticsViewSet(viewsets.ViewSet):
    """ViewSet for MCQ analytics endpoints."""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='category-scores')
    def category_scores(self, request):
        """Get average scores by category for the organization."""
        trainer = request.user.trainer
        organization = trainer.organization
        
        # Get all assessments for the organization
        assessments = Assessment.objects.filter(
            trainer__organization=organization
        ).exclude(
            comprehensive_score__isnull=True
        )
        
        # Calculate average scores by category
        category_scores = []
        
        categories = QuestionCategory.objects.filter(is_active=True)
        for category in categories:
            if category.slug == 'knowledge':
                avg_score = assessments.aggregate(
                    avg=Avg('knowledge_score')
                )['avg'] or 0
            elif category.slug == 'lifestyle':
                avg_score = assessments.aggregate(
                    avg=Avg('lifestyle_score')
                )['avg'] or 0
            elif category.slug == 'readiness':
                avg_score = assessments.aggregate(
                    avg=Avg('readiness_score')
                )['avg'] or 0
            else:
                avg_score = 0
            
            category_scores.append({
                'category': category.name_ko,
                'slug': category.slug,
                'average_score': round(avg_score, 1),
                'assessment_count': assessments.count()
            })
        
        return Response(category_scores)
    
    @action(detail=False, methods=['get'], url_path='risk-factors')
    def risk_factors(self, request):
        """Get most common risk factors from MCQ responses."""
        trainer = request.user.trainer
        organization = trainer.organization
        
        # Get all responses for the organization
        responses = QuestionResponse.objects.filter(
            assessment__trainer__organization=organization
        ).prefetch_related('selected_choices')
        
        # Count risk factors
        risk_factor_counts = {}
        
        for response in responses:
            for choice in response.selected_choices.all():
                if choice.risk_factor:
                    if choice.risk_factor not in risk_factor_counts:
                        risk_factor_counts[choice.risk_factor] = 0
                    risk_factor_counts[choice.risk_factor] += 1
        
        # Sort by count and return top 10
        sorted_factors = sorted(
            risk_factor_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        result = [
            {
                'risk_factor': factor,
                'count': count,
                'percentage': round(count / len(responses) * 100, 1) if responses else 0
            }
            for factor, count in sorted_factors
        ]
        
        return Response(result)
    
    @action(detail=False, methods=['get'], url_path='completion-rates')
    def completion_rates(self, request):
        """Get MCQ completion rates by category."""
        trainer = request.user.trainer
        organization = trainer.organization
        
        # Get all assessments for the organization
        assessments = Assessment.objects.filter(
            trainer__organization=organization
        ).prefetch_related(
            'question_responses__question__category'
        )
        
        # Calculate completion rates
        completion_data = []
        
        categories = QuestionCategory.objects.filter(is_active=True)
        for category in categories:
            total_questions = category.questions.filter(
                is_active=True
            ).count()
            
            if total_questions == 0:
                continue
            
            # Count assessments with complete responses for this category
            complete_count = 0
            
            for assessment in assessments:
                answered = assessment.question_responses.filter(
                    question__category=category
                ).count()
                
                if answered == total_questions:
                    complete_count += 1
            
            completion_data.append({
                'category': category.name_ko,
                'slug': category.slug,
                'total_questions': total_questions,
                'completion_rate': round(
                    complete_count / assessments.count() * 100, 1
                ) if assessments.count() > 0 else 0,
                'complete_count': complete_count,
                'total_assessments': assessments.count()
            })
        
        return Response(completion_data)
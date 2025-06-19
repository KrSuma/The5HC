"""
MCQ (Multiple Choice Questions) serializers for API endpoints.

This module provides serializers for all MCQ-related models including
questions, categories, choices, and responses. It handles validation,
nested relationships, and custom business logic for MCQ assessments.
"""

from rest_framework import serializers
from django.db import transaction
from django.db.models import Q, Count, Avg, F

from apps.assessments.models import (
    QuestionCategory, MultipleChoiceQuestion, 
    QuestionChoice, QuestionResponse, Assessment
)


class QuestionChoiceSerializer(serializers.ModelSerializer):
    """Serializer for question choices."""
    
    class Meta:
        model = QuestionChoice
        fields = [
            'id', 'choice_text', 'choice_text_ko', 'points', 
            'risk_factor', 'order', 'is_correct'
        ]
        read_only_fields = ['id']


class MultipleChoiceQuestionSerializer(serializers.ModelSerializer):
    """Serializer for multiple choice questions with nested choices."""
    
    choices = QuestionChoiceSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_name_ko = serializers.CharField(source='category.name_ko', read_only=True)
    depends_on_question = serializers.CharField(
        source='depends_on.question_text_ko', 
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = MultipleChoiceQuestion
        fields = [
            'id', 'category', 'category_name', 'category_name_ko',
            'question_text', 'question_text_ko', 'question_type',
            'is_required', 'points', 'help_text', 'help_text_ko',
            'depends_on', 'depends_on_question', 'depends_on_answer',
            'order', 'choices', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuestionCategorySerializer(serializers.ModelSerializer):
    """Serializer for question categories with statistics."""
    
    question_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    average_score = serializers.SerializerMethodField()
    
    class Meta:
        model = QuestionCategory
        fields = [
            'id', 'name', 'name_ko', 'slug', 'description', 
            'description_ko', 'weight', 'order', 'is_active',
            'question_count', 'completion_rate', 'average_score',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_question_count(self, obj):
        """Get count of active questions in category."""
        return obj.questions.filter(is_active=True).count()
    
    def get_completion_rate(self, obj):
        """Calculate completion rate for questions in this category."""
        # This would need access to assessment context
        # For now, return placeholder
        return 0.0
    
    def get_average_score(self, obj):
        """Calculate average score for this category across assessments."""
        # This would need more complex query
        # For now, return placeholder
        return 0.0


class QuestionResponseSerializer(serializers.ModelSerializer):
    """Serializer for question responses."""
    
    question_text = serializers.CharField(
        source='question.question_text_ko', 
        read_only=True
    )
    question_type = serializers.CharField(
        source='question.question_type',
        read_only=True
    )
    selected_choice_texts = serializers.SerializerMethodField()
    
    class Meta:
        model = QuestionResponse
        fields = [
            'id', 'question', 'question_text', 'question_type',
            'response_text', 'selected_choices', 'selected_choice_texts',
            'points_earned', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'points_earned', 'created_at', 'updated_at']
    
    def get_selected_choice_texts(self, obj):
        """Get text of selected choices in Korean."""
        return [choice.choice_text_ko for choice in obj.selected_choices.all()]
    
    def validate(self, data):
        """Validate response based on question type and requirements."""
        question = data.get('question')
        
        if not question:
            raise serializers.ValidationError("질문이 지정되지 않았습니다.")
        
        # Check if question is required
        if question.is_required:
            response_text = data.get('response_text')
            selected_choices = data.get('selected_choices', [])
            
            if question.question_type == 'text' and not response_text:
                raise serializers.ValidationError(
                    f"'{question.question_text_ko}'는 필수 질문입니다."
                )
            elif question.question_type in ['single', 'multiple', 'scale'] and not selected_choices:
                raise serializers.ValidationError(
                    f"'{question.question_text_ko}'는 필수 질문입니다."
                )
        
        # Validate choice count for single choice questions
        if question.question_type == 'single':
            selected_choices = data.get('selected_choices', [])
            if len(selected_choices) > 1:
                raise serializers.ValidationError(
                    "단일 선택 질문에는 하나의 답변만 선택할 수 있습니다."
                )
        
        return data


class MCQResponseBulkSerializer(serializers.Serializer):
    """Serializer for bulk MCQ response submission."""
    
    responses = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )
    
    def validate_responses(self, value):
        """Validate all responses in bulk submission."""
        if not value:
            raise serializers.ValidationError("응답이 없습니다.")
        
        # Check for required fields in each response
        for response in value:
            if 'question_id' not in response:
                raise serializers.ValidationError(
                    "각 응답에는 question_id가 필요합니다."
                )
        
        return value
    
    def create(self, validated_data):
        """Create multiple responses in a transaction."""
        responses_data = validated_data['responses']
        assessment = self.context['assessment']
        created_responses = []
        
        with transaction.atomic():
            # Delete existing responses for this assessment
            QuestionResponse.objects.filter(assessment=assessment).delete()
            
            for response_data in responses_data:
                question_id = response_data.pop('question_id')
                
                try:
                    question = MultipleChoiceQuestion.objects.get(
                        id=question_id,
                        is_active=True
                    )
                except MultipleChoiceQuestion.DoesNotExist:
                    raise serializers.ValidationError(
                        f"질문 ID {question_id}를 찾을 수 없습니다."
                    )
                
                # Create response
                response = QuestionResponse.objects.create(
                    assessment=assessment,
                    question=question,
                    response_text=response_data.get('response_text', '')
                )
                
                # Add selected choices
                choice_ids = response_data.get('selected_choices', [])
                if choice_ids:
                    choices = QuestionChoice.objects.filter(
                        id__in=choice_ids,
                        question=question
                    )
                    response.selected_choices.set(choices)
                    response.save()  # Trigger points calculation
                
                created_responses.append(response)
        
        return {'responses': created_responses}


class MCQAssessmentSerializer(serializers.Serializer):
    """Serializer for MCQ assessment summary."""
    
    knowledge_score = serializers.FloatField(read_only=True)
    lifestyle_score = serializers.FloatField(read_only=True)
    readiness_score = serializers.FloatField(read_only=True)
    comprehensive_score = serializers.FloatField(read_only=True)
    completion_status = serializers.DictField(read_only=True)
    risk_factors = serializers.ListField(read_only=True)
    insights = serializers.DictField(read_only=True)
    responses = QuestionResponseSerializer(many=True, read_only=True)
    
    def to_representation(self, instance):
        """Convert assessment instance to MCQ summary."""
        assessment = instance
        
        # Get MCQ scores
        data = {
            'knowledge_score': assessment.knowledge_score or 0.0,
            'lifestyle_score': assessment.lifestyle_score or 0.0,
            'readiness_score': assessment.readiness_score or 0.0,
            'comprehensive_score': assessment.comprehensive_score or 0.0,
        }
        
        # Get responses
        responses = assessment.question_responses.select_related(
            'question', 'question__category'
        ).prefetch_related('selected_choices')
        
        data['responses'] = QuestionResponseSerializer(
            responses, many=True
        ).data
        
        # Calculate completion status
        categories = QuestionCategory.objects.filter(is_active=True)
        completion_status = {}
        
        for category in categories:
            total_questions = category.questions.filter(
                is_active=True
            ).count()
            answered_questions = responses.filter(
                question__category=category
            ).count()
            
            completion_status[category.slug] = {
                'total': total_questions,
                'answered': answered_questions,
                'percentage': (answered_questions / total_questions * 100) if total_questions > 0 else 0
            }
        
        data['completion_status'] = completion_status
        
        # Get risk factors from MCQ responses
        risk_factors = []
        for response in responses:
            for choice in response.selected_choices.all():
                if choice.risk_factor:
                    risk_factors.append(choice.risk_factor)
        
        data['risk_factors'] = list(set(risk_factors))  # Unique risk factors
        
        # Get insights (would be generated by scoring engine)
        data['insights'] = {
            'knowledge': self._get_category_insight(assessment, 'knowledge'),
            'lifestyle': self._get_category_insight(assessment, 'lifestyle'),
            'readiness': self._get_category_insight(assessment, 'readiness')
        }
        
        return data
    
    def _get_category_insight(self, assessment, category_slug):
        """Generate insight for a category based on score."""
        score_map = {
            'knowledge': assessment.knowledge_score,
            'lifestyle': assessment.lifestyle_score,
            'readiness': assessment.readiness_score
        }
        
        score = score_map.get(category_slug, 0) or 0
        
        if score >= 80:
            level = "우수"
            message = "매우 좋은 수준입니다. 현재 상태를 유지하세요."
        elif score >= 60:
            level = "양호"
            message = "좋은 수준이지만 개선의 여지가 있습니다."
        elif score >= 40:
            level = "보통"
            message = "개선이 필요한 부분이 있습니다."
        else:
            level = "미흡"
            message = "전문가의 도움을 받아 개선 계획을 세우세요."
        
        return {
            'score': score,
            'level': level,
            'message': message
        }


class QuestionValidationSerializer(serializers.Serializer):
    """Serializer for validating question answers."""
    
    question_id = serializers.IntegerField()
    answer = serializers.CharField(required=False, allow_blank=True)
    selected_choices = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    
    def validate(self, data):
        """Validate the answer for a specific question."""
        try:
            question = MultipleChoiceQuestion.objects.get(
                id=data['question_id'],
                is_active=True
            )
        except MultipleChoiceQuestion.DoesNotExist:
            raise serializers.ValidationError("질문을 찾을 수 없습니다.")
        
        # Add question to validated data
        data['question'] = question
        
        # Validate based on question type
        if question.question_type == 'text':
            if not data.get('answer'):
                raise serializers.ValidationError("텍스트 답변이 필요합니다.")
        else:
            if not data.get('selected_choices'):
                raise serializers.ValidationError("선택 항목이 필요합니다.")
        
        return data
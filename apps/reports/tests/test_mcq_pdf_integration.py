"""
Tests for MCQ integration in PDF reports.

Tests the integration of MCQ results into PDF report generation.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth import get_user_model
from apps.assessments.factories import (
    AssessmentFactory, QuestionCategoryFactory,
    MultipleChoiceQuestionFactory, QuestionChoiceFactory,
    QuestionResponseFactory
)
from apps.trainers.factories import TrainerFactory, OrganizationFactory
from apps.clients.factories import ClientFactory
from apps.reports.services import ReportGenerator

User = get_user_model()


@pytest.mark.django_db
class TestMCQPDFIntegration:
    """Test MCQ integration in PDF reports."""
    
    def setup_method(self):
        """Set up test data."""
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        self.client_obj = ClientFactory(trainer=self.trainer)
        self.assessment = AssessmentFactory(
            client=self.client_obj,
            trainer=self.trainer,
            overall_score=75.0
        )
        
        # Create MCQ structure
        self.knowledge_cat = QuestionCategoryFactory(
            name="Knowledge",
            name_ko="지식 평가",
            weight=Decimal('0.15'),
            order=1
        )
        self.lifestyle_cat = QuestionCategoryFactory(
            name="Lifestyle",
            name_ko="생활습관",
            weight=Decimal('0.15'),
            order=2
        )
        self.readiness_cat = QuestionCategoryFactory(
            name="Readiness",
            name_ko="준비도",
            weight=Decimal('0.10'),
            order=3
        )
        
        # Create questions and responses
        self.create_mcq_data()
        
        self.report_generator = ReportGenerator()
    
    def create_mcq_data(self):
        """Create MCQ questions and responses."""
        # Knowledge question
        self.k_question = MultipleChoiceQuestionFactory(
            category=self.knowledge_cat,
            question_text="What is the primary benefit of strength training?",
            question_type='single',
            points=10
        )
        self.k_choice_correct = QuestionChoiceFactory(
            question=self.k_question,
            choice_text="Increased muscle mass",
            points=10,
            is_correct=True
        )
        self.k_choice_wrong = QuestionChoiceFactory(
            question=self.k_question,
            choice_text="Only weight loss",
            points=0,
            is_correct=False
        )
        
        # Create response (correct answer - 100% score)
        QuestionResponseFactory(
            assessment=self.assessment,
            question=self.k_question,
            points_earned=10,
            selected_choices=[self.k_choice_correct]
        )
        
        # Lifestyle question with risk factor
        self.l_question = MultipleChoiceQuestionFactory(
            category=self.lifestyle_cat,
            question_text="How many hours of sleep do you get?",
            question_type='single',
            points=10
        )
        self.l_choice_good = QuestionChoiceFactory(
            question=self.l_question,
            choice_text="7-8 hours",
            points=10,
            is_correct=True,
            contributes_to_risk=False,
            risk_weight=Decimal('0.0')
        )
        self.l_choice_risky = QuestionChoiceFactory(
            question=self.l_question,
            choice_text="Less than 5 hours",
            points=2,
            is_correct=False,
            contributes_to_risk=True,
            risk_weight=Decimal('0.8')
        )
        
        # Create response (risky choice - 20% score + risk factor)
        QuestionResponseFactory(
            assessment=self.assessment,
            question=self.l_question,
            points_earned=2,
            selected_choices=[self.l_choice_risky]
        )
        
        # Readiness question
        self.r_question = MultipleChoiceQuestionFactory(
            category=self.readiness_cat,
            question_text="Rate your energy level (1-5)",
            question_type='scale',
            points=10
        )
        self.r_choice = QuestionChoiceFactory(
            question=self.r_question,
            choice_text="4",
            points=8,
            order=4
        )
        
        # Create response (80% score)
        QuestionResponseFactory(
            assessment=self.assessment,
            question=self.r_question,
            points_earned=8,
            selected_choices=[self.r_choice]
        )
    
    def test_get_mcq_data_with_responses(self):
        """Test _get_mcq_data with MCQ responses."""
        mcq_data = self.report_generator._get_mcq_data(self.assessment)
        
        assert mcq_data['has_responses'] is True
        assert 'scores' in mcq_data
        assert 'insights' in mcq_data
        assert 'risk_factors' in mcq_data
        assert 'comprehensive_score' in mcq_data
        
        # Check scores
        scores = mcq_data['scores']
        assert scores['knowledge'] == 100.0  # 10/10 * 100
        assert scores['lifestyle'] == 20.0   # 2/10 * 100
        assert scores['readiness'] == 80.0   # 8/10 * 100
        
        # Check risk factors
        risk_factors = mcq_data['risk_factors']
        assert len(risk_factors) == 1
        assert risk_factors[0]['category'] == 'Lifestyle'
        assert risk_factors[0]['risk_weight'] == 0.8
        
        # Check comprehensive score calculation
        # Physical: 75 * 0.60 = 45
        # Knowledge: 100 * 0.15 = 15
        # Lifestyle: 20 * 0.15 = 3
        # Readiness: 80 * 0.10 = 8
        # Total: 45 + 15 + 3 + 8 = 71
        expected_comprehensive = 75*0.6 + 100*0.15 + 20*0.15 + 80*0.10
        assert abs(mcq_data['comprehensive_score'] - expected_comprehensive) < 0.1
    
    def test_get_mcq_data_without_responses(self):
        """Test _get_mcq_data without MCQ responses."""
        # Create assessment without MCQ responses
        empty_assessment = AssessmentFactory(
            client=self.client_obj,
            trainer=self.trainer,
            overall_score=80.0
        )
        
        mcq_data = self.report_generator._get_mcq_data(empty_assessment)
        
        assert mcq_data['has_responses'] is False
        assert mcq_data['scores'] == {'knowledge': 0, 'lifestyle': 0, 'readiness': 0}
        assert mcq_data['comprehensive_score'] == 80.0  # Falls back to overall_score
        assert mcq_data['insights'] == {}
        assert mcq_data['risk_factors'] == []
    
    def test_get_suggestions_with_mcq_data(self):
        """Test _get_suggestions includes MCQ-based recommendations."""
        physical_scores = {
            'strength': 2.5,  # Below 3, should get suggestions
            'mobility': 3.5,  # Above 3, no suggestions
            'balance': 3.0,   # Equal to 3, no suggestions
            'cardio': 2.0     # Below 3, should get suggestions
        }
        
        mcq_data = self.report_generator._get_mcq_data(self.assessment)
        suggestions = self.report_generator._get_suggestions(physical_scores, mcq_data)
        
        # Should have physical suggestions
        assert 'strength' in suggestions
        assert 'cardio' in suggestions
        assert 'mobility' not in suggestions  # Score above threshold
        
        # Should have MCQ-based suggestions
        assert 'knowledge' in suggestions
        assert 'lifestyle' in suggestions
        assert 'readiness' in suggestions
        
        # Check knowledge suggestions (score: 100%)
        knowledge_suggestions = suggestions['knowledge']
        assert len(knowledge_suggestions) >= 1
        assert any('훌륭한' in suggestion for suggestion in knowledge_suggestions)
        
        # Check lifestyle suggestions (score: 20%)
        lifestyle_suggestions = suggestions['lifestyle']
        assert len(lifestyle_suggestions) >= 1
        assert any('수면' in suggestion for suggestion in lifestyle_suggestions)
    
    def test_get_suggestions_without_mcq_data(self):
        """Test _get_suggestions works without MCQ data."""
        physical_scores = {
            'strength': 2.5,
            'mobility': 2.5,
            'balance': 2.5,
            'cardio': 2.5
        }
        
        suggestions = self.report_generator._get_suggestions(physical_scores, None)
        
        # Should only have physical suggestions
        assert 'strength' in suggestions
        assert 'mobility' in suggestions
        assert 'balance' in suggestions
        assert 'cardio' in suggestions
        
        # Should not have MCQ suggestions
        assert 'knowledge' not in suggestions
        assert 'lifestyle' not in suggestions
        assert 'readiness' not in suggestions
    
    @patch('apps.reports.services.WEASYPRINT_AVAILABLE', True)
    @patch('apps.reports.services.HTML')
    @patch('apps.reports.services.CSS')
    def test_generate_assessment_report_with_mcq(self, mock_css, mock_html):
        """Test generating PDF report with MCQ data."""
        # Mock HTML and CSS for PDF generation
        mock_html_instance = mock_html.return_value
        mock_html_instance.write_pdf.return_value = None
        
        # Mock the HTML to PDF conversion to avoid actual PDF generation
        with patch.object(self.report_generator, '_html_to_pdf') as mock_pdf:
            mock_pdf.return_value = type('MockPDF', (), {
                'getvalue': lambda: b'mock_pdf_content',
                'getbuffer': lambda: type('MockBuffer', (), {'nbytes': 1024})()
            })()
            
            report = self.report_generator.generate_assessment_report(
                assessment_id=self.assessment.id,
                user=self.trainer.user
            )
        
        assert report is not None
        assert report.assessment == self.assessment
        assert report.generated_by == self.trainer.user
        assert report.report_type == 'detailed'
        assert report.file_size == 1024
    
    def test_mcq_data_error_handling(self):
        """Test error handling in MCQ data retrieval."""
        # Test with assessment that doesn't exist
        with patch('apps.reports.services.logger') as mock_logger:
            # Create an assessment instance but don't save it
            fake_assessment = AssessmentFactory.build()
            fake_assessment.id = 99999  # Non-existent ID
            
            mcq_data = self.report_generator._get_mcq_data(fake_assessment)
            
            # Should return safe defaults
            assert mcq_data['has_responses'] is False
            assert mcq_data['comprehensive_score'] == 0  # No overall_score
    
    def test_mcq_template_context_integration(self):
        """Test that MCQ data is properly integrated into template context."""
        # Get MCQ data
        mcq_data = self.report_generator._get_mcq_data(self.assessment)
        
        # Simulate the context creation process
        context = {
            'mcq_data': mcq_data,
            'has_mcq_data': mcq_data['has_responses'],
            'mcq_scores': mcq_data['scores'],
            'mcq_insights': mcq_data['insights'],
            'mcq_risk_factors': mcq_data['risk_factors'],
            'comprehensive_score': mcq_data['comprehensive_score'],
        }
        
        # Verify context has all required MCQ data
        assert context['has_mcq_data'] is True
        assert context['mcq_scores']['knowledge'] == 100.0
        assert context['mcq_scores']['lifestyle'] == 20.0
        assert context['mcq_scores']['readiness'] == 80.0
        assert len(context['mcq_risk_factors']) == 1
        assert 'knowledge' in context['mcq_insights']
        assert 'lifestyle' in context['mcq_insights']
        assert 'readiness' in context['mcq_insights']
    
    def test_comprehensive_score_display_logic(self):
        """Test comprehensive score display logic."""
        mcq_data = self.report_generator._get_mcq_data(self.assessment)
        
        # With MCQ data, should use comprehensive score
        assert mcq_data['has_responses'] is True
        assert mcq_data['comprehensive_score'] != self.assessment.overall_score
        
        # Comprehensive score should be different from physical-only score
        # Physical: 75, Comprehensive: should be lower due to poor lifestyle score
        assert mcq_data['comprehensive_score'] < self.assessment.overall_score
    
    def test_mcq_score_percentages(self):
        """Test MCQ score percentage calculations for progress bars."""
        mcq_data = self.report_generator._get_mcq_data(self.assessment)
        
        percentages = mcq_data['mcq_score_percentages']
        
        # Scores are already percentages (0-100), so percentages should match scores
        assert percentages['knowledge_pct'] == 100.0
        assert percentages['lifestyle_pct'] == 20.0
        assert percentages['readiness_pct'] == 80.0
        
        # All percentages should be between 0 and 100
        for pct in percentages.values():
            assert 0 <= pct <= 100


@pytest.mark.django_db
class TestMCQPDFTemplateIntegration:
    """Test MCQ template integration specifically."""
    
    def setup_method(self):
        """Set up test data."""
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        self.client_obj = ClientFactory(trainer=self.trainer)
        self.assessment = AssessmentFactory(
            client=self.client_obj,
            trainer=self.trainer,
            overall_score=85.0
        )
    
    def test_template_context_without_mcq(self):
        """Test template context when no MCQ data exists."""
        report_generator = ReportGenerator()
        mcq_data = report_generator._get_mcq_data(self.assessment)
        
        assert mcq_data['has_responses'] is False
        
        # Template should handle missing MCQ data gracefully
        context = {
            'has_mcq_data': mcq_data['has_responses'],
            'mcq_data': mcq_data,
            'mcq_scores': mcq_data['scores'],
            'comprehensive_score': mcq_data['comprehensive_score']
        }
        
        # Should not show MCQ sections in template
        assert context['has_mcq_data'] is False
        assert context['comprehensive_score'] == 85.0  # Falls back to overall_score
        assert context['mcq_scores'] == {'knowledge': 0, 'lifestyle': 0, 'readiness': 0}
    
    def test_risk_factor_display_structure(self):
        """Test risk factor data structure for template display."""
        # Create assessment with risk factors
        category = QuestionCategoryFactory(name="Lifestyle")
        question = MultipleChoiceQuestionFactory(category=category)
        risky_choice = QuestionChoiceFactory(
            question=question,
            choice_text="Poor choice",
            contributes_to_risk=True,
            risk_weight=Decimal('0.7')
        )
        
        QuestionResponseFactory(
            assessment=self.assessment,
            question=question,
            selected_choices=[risky_choice]
        )
        
        report_generator = ReportGenerator()
        mcq_data = report_generator._get_mcq_data(self.assessment)
        
        risk_factors = mcq_data['risk_factors']
        assert len(risk_factors) == 1
        
        risk = risk_factors[0]
        # Check template-required fields
        assert 'category' in risk
        assert 'answer' in risk
        assert 'risk_weight' in risk
        assert risk['category'] == 'Lifestyle'
        assert risk['answer'] == 'Poor choice'
        assert risk['risk_weight'] == 0.7


@pytest.mark.django_db 
class TestMCQPDFPerformance:
    """Test performance aspects of MCQ PDF integration."""
    
    def setup_method(self):
        """Set up test data."""
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        self.client_obj = ClientFactory(trainer=self.trainer)
        self.report_generator = ReportGenerator()
    
    def test_large_mcq_dataset_performance(self):
        """Test PDF generation with large MCQ dataset."""
        assessment = AssessmentFactory(
            client=self.client_obj,
            trainer=self.trainer
        )
        
        # Create multiple categories and questions
        categories = []
        for i in range(3):
            category = QuestionCategoryFactory(
                name=f"Category{i}",
                weight=Decimal('0.05')
            )
            categories.append(category)
            
            # Create 10 questions per category
            for j in range(10):
                question = MultipleChoiceQuestionFactory(category=category)
                choice = QuestionChoiceFactory(question=question, points=5)
                QuestionResponseFactory(
                    assessment=assessment,
                    question=question,
                    points_earned=5,
                    selected_choices=[choice]
                )
        
        # Test MCQ data retrieval performance
        import time
        start_time = time.time()
        
        mcq_data = self.report_generator._get_mcq_data(assessment)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 30 questions quickly (under 1 second)
        assert processing_time < 1.0
        
        # Verify data integrity
        assert mcq_data['has_responses'] is True
        assert len(mcq_data['risk_factors']) >= 0  # May or may not have risk factors
    
    def test_mcq_data_caching_behavior(self):
        """Test that MCQ data calculation is efficient for repeated calls."""
        assessment = AssessmentFactory(
            client=self.client_obj,
            trainer=self.trainer
        )
        
        category = QuestionCategoryFactory(name="Knowledge")
        question = MultipleChoiceQuestionFactory(category=category)
        choice = QuestionChoiceFactory(question=question)
        QuestionResponseFactory(
            assessment=assessment,
            question=question,
            selected_choices=[choice]
        )
        
        # Multiple calls should be efficient
        import time
        start_time = time.time()
        
        for _ in range(5):
            mcq_data = self.report_generator._get_mcq_data(assessment)
            assert mcq_data['has_responses'] is True
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 5 calls should complete quickly
        assert total_time < 2.0
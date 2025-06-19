"""
Tests for MCQ management commands.

Tests all MCQ-related Django management commands created in Phase 7.
"""

import pytest
import tempfile
import json
import csv
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from apps.assessments.models import (
    QuestionCategory, MultipleChoiceQuestion,
    QuestionChoice, QuestionResponse
)
from apps.assessments.factories import (
    AssessmentFactory, QuestionCategoryFactory,
    MultipleChoiceQuestionFactory, QuestionChoiceFactory,
    QuestionResponseFactory
)


@pytest.mark.django_db
class TestLoadMCQQuestionsCommand:
    """Test cases for load_mcq_questions management command."""
    
    def test_load_questions_from_json(self):
        """Test loading questions from JSON file."""
        # Create test JSON data
        test_data = [
            {
                "category": {
                    "name": "Knowledge",
                    "name_ko": "지식 평가",
                    "weight": 0.15,
                    "order": 1
                },
                "question_text": "What is physical fitness?",
                "question_text_ko": "신체 건강이란 무엇입니까?",
                "question_type": "single",
                "points": 10,
                "is_required": True,
                "order": 1,
                "choices": [
                    {
                        "choice_text": "The ability to perform daily activities",
                        "choice_text_ko": "일상 활동을 수행하는 능력",
                        "points": 10,
                        "is_correct": True,
                        "order": 1,
                        "risk_factor": ""
                    },
                    {
                        "choice_text": "Only muscle strength",
                        "choice_text_ko": "근력만",
                        "points": 0,
                        "is_correct": False,
                        "order": 2,
                        "risk_factor": ""
                    }
                ]
            }
        ]
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_file_path = f.name
        
        try:
            # Run command
            call_command('load_mcq_questions', file=json_file_path, format='json')
            
            # Verify data was loaded
            category = QuestionCategory.objects.get(name="Knowledge")
            assert category.name_ko == "지식 평가"
            assert float(category.weight) == 0.15
            
            question = MultipleChoiceQuestion.objects.get(
                question_text="What is physical fitness?"
            )
            assert question.category == category
            assert question.question_type == 'single'
            assert question.points == 10
            assert question.is_required is True
            
            choices = question.choices.all()
            assert choices.count() == 2
            
            correct_choice = choices.filter(is_correct=True).first()
            assert correct_choice.points == 10
            assert correct_choice.choice_text == "The ability to perform daily activities"
            
        finally:
            # Clean up
            import os
            os.unlink(json_file_path)
    
    def test_load_questions_from_csv(self):
        """Test loading questions from CSV file."""
        # Create test CSV data
        csv_data = '''category,category_ko,category_weight,question_text,question_text_ko,question_type,points,is_required,choice_1_text,choice_1_text_ko,choice_1_points,choice_1_correct,choice_1_risk_factor,choice_2_text,choice_2_text_ko,choice_2_points,choice_2_correct,choice_2_risk_factor
Lifestyle,생활습관,0.15,How many hours do you sleep?,몇 시간 잠을 자십니까?,single,10,true,7-8 hours,7-8시간,10,true,,Less than 5 hours,5시간 미만,2,false,sleep_deprivation'''
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            csv_file_path = f.name
        
        try:
            # Run command
            call_command('load_mcq_questions', file=csv_file_path, format='csv')
            
            # Verify data was loaded
            category = QuestionCategory.objects.get(name="Lifestyle")
            assert category.name_ko == "생활습관"
            
            question = MultipleChoiceQuestion.objects.get(
                question_text="How many hours do you sleep?"
            )
            assert question.category == category
            
            # Check risk factor mapping
            risky_choice = question.choices.filter(choice_text="Less than 5 hours").first()
            assert risky_choice.contributes_to_risk is True
            assert risky_choice.risk_weight > 0
            
            safe_choice = question.choices.filter(choice_text="7-8 hours").first()
            assert safe_choice.contributes_to_risk is False
            assert safe_choice.risk_weight == 0
            
        finally:
            import os
            os.unlink(csv_file_path)
    
    def test_load_questions_dry_run(self):
        """Test dry run mode doesn't save data."""
        test_data = [{
            "category": {
                "name": "Test Category",
                "name_ko": "테스트",
                "weight": 0.10
            },
            "question_text": "Test question?",
            "question_type": "single",
            "points": 5,
            "choices": []
        }]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_file_path = f.name
        
        try:
            # Run command with dry-run
            call_command('load_mcq_questions', file=json_file_path, dry_run=True)
            
            # Verify no data was saved
            assert not QuestionCategory.objects.filter(name="Test Category").exists()
            assert not MultipleChoiceQuestion.objects.filter(
                question_text="Test question?"
            ).exists()
            
        finally:
            import os
            os.unlink(json_file_path)
    
    def test_load_questions_clear_existing(self):
        """Test clearing existing data before loading."""
        # Create existing data
        existing_category = QuestionCategoryFactory(name="Existing")
        existing_question = MultipleChoiceQuestionFactory(category=existing_category)
        
        test_data = [{
            "category": {
                "name": "New Category",
                "name_ko": "새로운",
                "weight": 0.10
            },
            "question_text": "New question?",
            "question_type": "single",
            "points": 5,
            "choices": []
        }]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_file_path = f.name
        
        try:
            # Run command with clear
            call_command('load_mcq_questions', file=json_file_path, clear=True)
            
            # Verify existing data was cleared
            assert not QuestionCategory.objects.filter(name="Existing").exists()
            assert not MultipleChoiceQuestion.objects.filter(id=existing_question.id).exists()
            
            # Verify new data was loaded
            assert QuestionCategory.objects.filter(name="New Category").exists()
            
        finally:
            import os
            os.unlink(json_file_path)
    
    def test_load_questions_invalid_file(self):
        """Test error handling for invalid files."""
        # Test with non-existent file
        with pytest.raises(CommandError):
            call_command('load_mcq_questions', file='non_existent.json')
        
        # Test with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json content')
            invalid_json_path = f.name
        
        try:
            with pytest.raises(CommandError):
                call_command('load_mcq_questions', file=invalid_json_path)
        finally:
            import os
            os.unlink(invalid_json_path)


@pytest.mark.django_db
class TestExportMCQQuestionsCommand:
    """Test cases for export_mcq_questions management command."""
    
    def setup_method(self):
        """Set up test data."""
        self.category = QuestionCategoryFactory(
            name="Knowledge",
            name_ko="지식",
            weight=0.15
        )
        self.question = MultipleChoiceQuestionFactory(
            category=self.category,
            question_text="What is fitness?",
            question_text_ko="피트니스란?",
            question_type='single',
            points=10
        )
        self.choice1 = QuestionChoiceFactory(
            question=self.question,
            choice_text="Physical ability",
            points=10,
            is_correct=True
        )
        self.choice2 = QuestionChoiceFactory(
            question=self.question,
            choice_text="Mental state",
            points=0,
            is_correct=False
        )
    
    def test_export_questions_json(self):
        """Test exporting questions to JSON format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            # Run export command
            call_command('export_mcq_questions', output=output_file, format='json')
            
            # Read and verify exported data
            with open(output_file, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            assert len(exported_data) == 1
            
            question_data = exported_data[0]
            assert question_data['question_text'] == "What is fitness?"
            assert question_data['question_text_ko'] == "피트니스란?"
            assert question_data['category']['name'] == "Knowledge"
            assert len(question_data['choices']) == 2
            
        finally:
            import os
            os.unlink(output_file)
    
    def test_export_questions_csv(self):
        """Test exporting questions to CSV format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name
        
        try:
            # Run export command
            call_command('export_mcq_questions', output=output_file, format='csv')
            
            # Read and verify exported data
            with open(output_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 1
            
            row = rows[0]
            assert row['question_text'] == "What is fitness?"
            assert row['category'] == "Knowledge"
            assert 'choice_1_text' in row
            assert 'choice_2_text' in row
            
        finally:
            import os
            os.unlink(output_file)
    
    def test_export_questions_yaml(self):
        """Test exporting questions to YAML format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            output_file = f.name
        
        try:
            # Run export command
            call_command('export_mcq_questions', output=output_file, format='yaml')
            
            # Read and verify exported data
            import yaml
            with open(output_file, 'r', encoding='utf-8') as f:
                exported_data = yaml.safe_load(f)
            
            assert len(exported_data) == 1
            
            question_data = exported_data[0]
            assert question_data['question_text'] == "What is fitness?"
            assert question_data['category']['name'] == "Knowledge"
            
        finally:
            import os
            os.unlink(output_file)
    
    def test_export_questions_filter_by_category(self):
        """Test exporting questions filtered by category."""
        # Create another category and question
        other_category = QuestionCategoryFactory(name="Lifestyle")
        other_question = MultipleChoiceQuestionFactory(category=other_category)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            # Export only Knowledge category
            call_command(
                'export_mcq_questions',
                output=output_file,
                category="Knowledge",
                format='json'
            )
            
            with open(output_file, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            # Should only export questions from Knowledge category
            assert len(exported_data) == 1
            assert exported_data[0]['category']['name'] == "Knowledge"
            
        finally:
            import os
            os.unlink(output_file)
    
    def test_export_questions_include_responses(self):
        """Test exporting questions with response statistics."""
        # Create some responses
        assessment = AssessmentFactory()
        QuestionResponseFactory(
            assessment=assessment,
            question=self.question,
            points_earned=10,
            selected_choices=[self.choice1]
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            call_command(
                'export_mcq_questions',
                output=output_file,
                include_responses=True,
                format='json'
            )
            
            with open(output_file, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            question_data = exported_data[0]
            # Should include response statistics
            assert 'response_count' in question_data
            assert question_data['response_count'] == 1
            
        finally:
            import os
            os.unlink(output_file)


@pytest.mark.django_db
class TestValidateMCQDataCommand:
    """Test cases for validate_mcq_data management command."""
    
    def setup_method(self):
        """Set up test data with some issues."""
        # Valid category
        self.valid_category = QuestionCategoryFactory(
            name="Valid Category",
            weight=0.15
        )
        
        # Invalid category (weight > 1)
        self.invalid_category = QuestionCategoryFactory(
            name="Invalid Category",
            weight=1.5  # Invalid
        )
        
        # Question without choices
        self.question_no_choices = MultipleChoiceQuestionFactory(
            category=self.valid_category,
            question_type='single'
        )
        
        # Question with choices
        self.question_with_choices = MultipleChoiceQuestionFactory(
            category=self.valid_category,
            question_type='single'
        )
        QuestionChoiceFactory.create_batch(3, question=self.question_with_choices)
    
    def test_validate_data_without_fix(self):
        """Test data validation without auto-fixing."""
        out = StringIO()
        call_command('validate_mcq_data', stdout=out)
        
        output = out.getvalue()
        
        # Should report validation issues
        assert "Invalid Category" in output
        assert "weight" in output.lower()
        assert "no choices" in output.lower()
    
    def test_validate_data_with_fix(self):
        """Test data validation with auto-fixing."""
        out = StringIO()
        call_command('validate_mcq_data', fix=True, stdout=out)
        
        output = out.getvalue()
        
        # Should report fixes applied
        assert "fixed" in output.lower() or "corrected" in output.lower()
        
        # Check that invalid category weight was fixed
        self.invalid_category.refresh_from_db()
        assert self.invalid_category.weight <= 1.0
    
    def test_validate_dependencies(self):
        """Test validation of question dependencies."""
        # Create circular dependency
        parent_q = MultipleChoiceQuestionFactory(category=self.valid_category)
        child_q = MultipleChoiceQuestionFactory(
            category=self.valid_category,
            depends_on=parent_q
        )
        
        # Create circular reference (not possible in model, but test handles it)
        # parent_q.depends_on = child_q
        # parent_q.save()
        
        out = StringIO()
        call_command('validate_mcq_data', check_dependencies=True, stdout=out)
        
        output = out.getvalue()
        # Should complete without errors
        assert "validation" in output.lower()
    
    def test_validate_verbose_output(self):
        """Test verbose validation output."""
        out = StringIO()
        call_command('validate_mcq_data', verbose=True, stdout=out)
        
        output = out.getvalue()
        
        # Should provide detailed information
        assert len(output) > 100  # Verbose output should be substantial
        assert "category" in output.lower()
        assert "question" in output.lower()


@pytest.mark.django_db
class TestMCQStatisticsCommand:
    """Test cases for mcq_statistics management command."""
    
    def setup_method(self):
        """Set up test data with responses."""
        self.category = QuestionCategoryFactory(name="Knowledge")
        self.question = MultipleChoiceQuestionFactory(
            category=self.category,
            question_text="Test question",
            points=10
        )
        self.choice1 = QuestionChoiceFactory(
            question=self.question,
            points=10,
            is_correct=True
        )
        self.choice2 = QuestionChoiceFactory(
            question=self.question,
            points=0,
            is_correct=False
        )
        
        # Create assessments with responses
        for i in range(5):
            assessment = AssessmentFactory(knowledge_score=80 + i * 2)
            QuestionResponseFactory(
                assessment=assessment,
                question=self.question,
                points_earned=8 + i,
                selected_choices=[self.choice1 if i % 2 == 0 else self.choice2]
            )
    
    def test_statistics_basic_output(self):
        """Test basic statistics output."""
        out = StringIO()
        call_command('mcq_statistics', stdout=out)
        
        output = out.getvalue()
        
        # Should contain overview statistics
        assert "MCQ STATISTICS" in output
        assert "Total Assessments" in output
        assert "Total MCQ Responses" in output
        assert "5" in output  # Should show 5 assessments
    
    def test_statistics_detailed_output(self):
        """Test detailed statistics output."""
        out = StringIO()
        call_command('mcq_statistics', detailed=True, stdout=out)
        
        output = out.getvalue()
        
        # Should contain detailed question-level stats
        assert "TOP QUESTIONS" in output
        assert "Test question" in output
        assert "Knowledge" in output
    
    def test_statistics_filter_by_category(self):
        """Test statistics filtered by category."""
        out = StringIO()
        call_command('mcq_statistics', category="Knowledge", stdout=out)
        
        output = out.getvalue()
        
        # Should focus on Knowledge category
        assert "Knowledge" in output
    
    def test_statistics_export_csv(self):
        """Test exporting statistics to CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name
        
        try:
            call_command('mcq_statistics', export=output_file)
            
            # Verify CSV file was created
            assert os.path.exists(output_file)
            
            with open(output_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Should have header and data rows
            assert len(rows) > 1
            assert "MCQ STATISTICS REPORT" in rows[0][0]
            
        finally:
            import os
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_statistics_date_filtering(self):
        """Test statistics with date filtering."""
        from datetime import date, timedelta
        
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')
        
        out = StringIO()
        call_command(
            'mcq_statistics',
            start_date=start_date,
            end_date=end_date,
            stdout=out
        )
        
        output = out.getvalue()
        
        # Should contain date range information
        assert start_date in output or "from" in output.lower()


@pytest.mark.django_db
class TestMCQCommandsIntegration:
    """Integration tests for MCQ management commands."""
    
    def test_export_then_import_workflow(self):
        """Test complete export -> import workflow."""
        # Create initial data
        category = QuestionCategoryFactory(name="Original")
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_text="Original question"
        )
        QuestionChoiceFactory.create_batch(2, question=question)
        
        # Export data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_file = f.name
        
        try:
            call_command('export_mcq_questions', output=export_file, format='json')
            
            # Clear existing data
            QuestionChoice.objects.all().delete()
            MultipleChoiceQuestion.objects.all().delete()
            QuestionCategory.objects.all().delete()
            
            # Import data back
            call_command('load_mcq_questions', file=export_file, format='json')
            
            # Verify data was restored
            restored_category = QuestionCategory.objects.get(name="Original")
            restored_question = MultipleChoiceQuestion.objects.get(
                question_text="Original question"
            )
            assert restored_question.category == restored_category
            assert restored_question.choices.count() == 2
            
        finally:
            import os
            os.unlink(export_file)
    
    def test_load_validate_statistics_workflow(self):
        """Test load -> validate -> statistics workflow."""
        # Load sample data
        test_data = [{
            "category": {
                "name": "Test Category",
                "weight": 0.20
            },
            "question_text": "Test question?",
            "question_type": "single",
            "points": 10,
            "choices": [
                {"choice_text": "A", "points": 10},
                {"choice_text": "B", "points": 0}
            ]
        }]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_file = f.name
        
        try:
            # Load data
            call_command('load_mcq_questions', file=json_file)
            
            # Validate data
            out = StringIO()
            call_command('validate_mcq_data', stdout=out)
            validation_output = out.getvalue()
            
            # Generate statistics
            out = StringIO()
            call_command('mcq_statistics', stdout=out)
            stats_output = out.getvalue()
            
            # Verify workflow completed
            assert "Test Category" in stats_output
            assert len(validation_output) > 0
            assert len(stats_output) > 0
            
        finally:
            import os
            os.unlink(json_file)
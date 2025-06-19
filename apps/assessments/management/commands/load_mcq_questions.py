"""
Load default MCQ questions from JSON/CSV files.

This command loads predefined Multiple Choice Questions into the database,
creating categories and questions with their choices.

Usage:
    python manage.py load_mcq_questions
    python manage.py load_mcq_questions --file questions.json
    python manage.py load_mcq_questions --file questions.csv --format csv
    python manage.py load_mcq_questions --clear  # Clear existing questions first
"""

import json
import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from apps.assessments.models import QuestionCategory, MultipleChoiceQuestion, QuestionChoice, QuestionResponse


class Command(BaseCommand):
    help = 'Load default MCQ questions from JSON or CSV file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='mcq_questions.json',
            help='Path to the questions file (default: mcq_questions.json)'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv'],
            default='json',
            help='File format (default: json)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing questions before loading'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making database changes'
        )
    
    def handle(self, *args, **options):
        file_path = options['file']
        file_format = options['format']
        clear_existing = options['clear']
        dry_run = options['dry_run']
        
        # Check if file path is absolute or relative
        if not os.path.isabs(file_path):
            # Look in common locations
            possible_paths = [
                os.path.join(settings.BASE_DIR, 'data', file_path),
                os.path.join(settings.BASE_DIR, 'fixtures', file_path),
                os.path.join(settings.BASE_DIR, 'apps', 'assessments', 'fixtures', file_path),
                file_path  # Try current directory as last resort
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    file_path = path
                    break
            else:
                raise CommandError(f"File not found: {file_path}")
        
        if not os.path.exists(file_path):
            raise CommandError(f"File not found: {file_path}")
        
        self.stdout.write(f"Loading questions from: {file_path}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be saved"))
        
        try:
            with transaction.atomic():
                if clear_existing and not dry_run:
                    self.clear_existing_questions()
                
                if file_format == 'json':
                    questions_data = self.load_json_file(file_path)
                else:
                    questions_data = self.load_csv_file(file_path)
                
                stats = self.process_questions(questions_data, dry_run)
                
                if dry_run:
                    transaction.set_rollback(True)
                
                self.display_summary(stats)
                
        except Exception as e:
            raise CommandError(f"Error loading questions: {str(e)}")
    
    def clear_existing_questions(self):
        """Clear all existing questions and categories."""
        self.stdout.write("Clearing existing questions...")
        
        # Delete in order to respect foreign key constraints
        QuestionResponse.objects.all().delete()
        QuestionChoice.objects.all().delete()
        MultipleChoiceQuestion.objects.all().delete()
        QuestionCategory.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS("Existing questions cleared"))
    
    def load_json_file(self, file_path):
        """Load questions from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise CommandError("JSON file must contain a list of questions")
        
        return data
    
    def load_csv_file(self, file_path):
        """Load questions from CSV file."""
        questions = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            current_question = None
            
            for row in reader:
                # Check if this is a new question or a choice for existing question
                if row.get('question_text'):
                    # Save previous question if exists
                    if current_question:
                        questions.append(current_question)
                    
                    # Start new question
                    current_question = {
                        'category': {
                            'name': row.get('category_name', 'General'),
                            'name_ko': row.get('category_name_ko', '일반'),
                            'weight': float(row.get('category_weight', 0.25)),
                            'order': int(row.get('category_order', 0))
                        },
                        'question_text': row['question_text'],
                        'question_text_ko': row.get('question_text_ko', row['question_text']),
                        'question_type': row.get('question_type', 'single'),
                        'is_required': row.get('is_required', 'True').lower() == 'true',
                        'points': int(row.get('points', 1)),
                        'help_text': row.get('help_text', ''),
                        'help_text_ko': row.get('help_text_ko', ''),
                        'order': int(row.get('order', 0)),
                        'is_active': row.get('is_active', 'True').lower() == 'true',
                        'choices': []
                    }
                
                # Add choices from numbered columns
                for i in range(1, 6):
                    choice_text = row.get(f'choice_{i}_text')
                    if choice_text:
                        # Handle risk factor conversion
                        risk_factor = row.get(f'choice_{i}_risk_factor', '')
                        contributes_to_risk = bool(risk_factor and risk_factor.strip())
                        risk_weight = 1.0 if contributes_to_risk else 0.0
                        
                        current_question['choices'].append({
                            'choice_text': choice_text,
                            'choice_text_ko': row.get(f'choice_{i}_text_ko', choice_text),
                            'points': int(row.get(f'choice_{i}_points', 0)),
                            'contributes_to_risk': contributes_to_risk,
                            'risk_weight': risk_weight,
                            'order': i,
                            'is_correct': row.get(f'choice_{i}_is_correct', 'False').lower() == 'true'
                        })
            
            # Don't forget the last question
            if current_question:
                questions.append(current_question)
        
        return questions
    
    def process_questions(self, questions_data, dry_run):
        """Process and create questions in the database."""
        stats = {
            'categories_created': 0,
            'categories_updated': 0,
            'questions_created': 0,
            'choices_created': 0,
            'errors': []
        }
        
        categories_cache = {}
        
        for idx, question_data in enumerate(questions_data):
            try:
                # Process category
                cat_data = question_data.get('category', {})
                cat_name = cat_data.get('name', 'General')
                
                if cat_name not in categories_cache:
                    category, created = QuestionCategory.objects.get_or_create(
                        name=cat_name,
                        defaults={
                            'name_ko': cat_data.get('name_ko', '일반'),
                            'weight': cat_data.get('weight', 0.25),
                            'order': cat_data.get('order', 0),
                            'description': cat_data.get('description', ''),
                            'description_ko': cat_data.get('description_ko', ''),
                            'is_active': cat_data.get('is_active', True)
                        }
                    )
                    
                    if created:
                        stats['categories_created'] += 1
                        self.stdout.write(f"Created category: {cat_name}")
                    else:
                        # Update existing category if needed
                        updated = False
                        for field in ['name_ko', 'weight', 'order', 'description', 'description_ko']:
                            if field in cat_data and getattr(category, field) != cat_data[field]:
                                setattr(category, field, cat_data[field])
                                updated = True
                        
                        if updated and not dry_run:
                            category.save()
                            stats['categories_updated'] += 1
                    
                    categories_cache[cat_name] = category
                else:
                    category = categories_cache[cat_name]
                
                # Create question
                question = MultipleChoiceQuestion(
                    category=category,
                    question_text=question_data['question_text'],
                    question_text_ko=question_data.get('question_text_ko', question_data['question_text']),
                    question_type=question_data.get('question_type', 'single'),
                    is_required=question_data.get('is_required', True),
                    points=question_data.get('points', 1),
                    help_text=question_data.get('help_text', ''),
                    help_text_ko=question_data.get('help_text_ko', ''),
                    order=question_data.get('order', 0),
                    is_active=question_data.get('is_active', True)
                )
                
                if not dry_run:
                    question.save()
                
                stats['questions_created'] += 1
                
                # Create choices
                for choice_data in question_data.get('choices', []):
                    # Handle risk factor conversion
                    risk_factor = choice_data.get('risk_factor', '')
                    contributes_to_risk = bool(risk_factor and risk_factor.strip())
                    risk_weight = 1.0 if contributes_to_risk else 0.0
                    
                    choice = QuestionChoice(
                        question=question,
                        choice_text=choice_data['choice_text'],
                        choice_text_ko=choice_data.get('choice_text_ko', choice_data['choice_text']),
                        points=choice_data.get('points', 0),
                        contributes_to_risk=contributes_to_risk,
                        risk_weight=risk_weight,
                        order=choice_data.get('order', 0),
                        is_correct=choice_data.get('is_correct', False)
                    )
                    
                    if not dry_run:
                        choice.save()
                    
                    stats['choices_created'] += 1
                
            except Exception as e:
                error_msg = f"Error processing question {idx + 1}: {str(e)}"
                stats['errors'].append(error_msg)
                self.stdout.write(self.style.ERROR(error_msg))
        
        return stats
    
    def display_summary(self, stats):
        """Display loading summary."""
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("LOADING SUMMARY"))
        self.stdout.write("="*50)
        
        self.stdout.write(f"Categories created: {stats['categories_created']}")
        self.stdout.write(f"Categories updated: {stats['categories_updated']}")
        self.stdout.write(f"Questions created: {stats['questions_created']}")
        self.stdout.write(f"Choices created: {stats['choices_created']}")
        
        if stats['errors']:
            self.stdout.write(self.style.ERROR(f"\nErrors encountered: {len(stats['errors'])}"))
            for error in stats['errors'][:5]:  # Show first 5 errors
                self.stdout.write(self.style.ERROR(f"  - {error}"))
            if len(stats['errors']) > 5:
                self.stdout.write(self.style.ERROR(f"  ... and {len(stats['errors']) - 5} more"))
        else:
            self.stdout.write(self.style.SUCCESS("\nNo errors encountered!"))
        
        self.stdout.write("="*50)
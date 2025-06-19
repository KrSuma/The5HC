"""
Export MCQ questions to various formats.

This command exports Multiple Choice Questions from the database to
JSON, CSV, or YAML format for backup, sharing, or version control.

Usage:
    python manage.py export_mcq_questions
    python manage.py export_mcq_questions --output questions_backup.json
    python manage.py export_mcq_questions --format csv --output questions.csv
    python manage.py export_mcq_questions --category "Knowledge Assessment"
    python manage.py export_mcq_questions --active-only
"""

import json
import csv
import yaml
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Prefetch
from apps.assessments.models import QuestionCategory, MultipleChoiceQuestion, QuestionChoice


class Command(BaseCommand):
    help = 'Export MCQ questions to JSON, CSV, or YAML format'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (default: mcq_export_YYYYMMDD_HHMMSS.[format])'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv', 'yaml'],
            default='json',
            help='Export format (default: json)'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Export only questions from specific category'
        )
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Export only active questions and categories'
        )
        parser.add_argument(
            '--include-responses',
            action='store_true',
            help='Include response statistics (JSON/YAML only)'
        )
        parser.add_argument(
            '--pretty',
            action='store_true',
            help='Pretty print JSON output'
        )
    
    def handle(self, *args, **options):
        output_file = options['output']
        export_format = options['format']
        category_filter = options['category']
        active_only = options['active_only']
        include_responses = options['include_responses']
        pretty = options['pretty']
        
        # Generate default filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'mcq_export_{timestamp}.{export_format}'
        
        # Ensure correct extension
        if not output_file.endswith(f'.{export_format}'):
            output_file = f'{output_file}.{export_format}'
        
        self.stdout.write(f"Exporting questions to: {output_file}")
        
        try:
            # Fetch questions with optimized query
            questions = self.fetch_questions(category_filter, active_only)
            
            if not questions:
                self.stdout.write(self.style.WARNING("No questions found matching the criteria"))
                return
            
            # Export based on format
            if export_format == 'json':
                self.export_json(questions, output_file, include_responses, pretty)
            elif export_format == 'csv':
                self.export_csv(questions, output_file)
            elif export_format == 'yaml':
                self.export_yaml(questions, output_file, include_responses)
            
            self.stdout.write(self.style.SUCCESS(f"Successfully exported {len(questions)} questions to {output_file}"))
            
        except Exception as e:
            raise CommandError(f"Error exporting questions: {str(e)}")
    
    def fetch_questions(self, category_filter, active_only):
        """Fetch questions with optimized query."""
        # Build queryset
        queryset = MultipleChoiceQuestion.objects.all()
        
        if active_only:
            queryset = queryset.filter(is_active=True, category__is_active=True)
        
        if category_filter:
            queryset = queryset.filter(category__name=category_filter)
        
        # Optimize with select_related and prefetch_related
        queryset = queryset.select_related('category').prefetch_related(
            Prefetch('choices', queryset=QuestionChoice.objects.order_by('order'))
        ).order_by('category__order', 'order')
        
        return list(queryset)
    
    def export_json(self, questions, output_file, include_responses, pretty):
        """Export questions to JSON format."""
        data = []
        categories_seen = set()
        
        for question in questions:
            # Build question data
            question_data = {
                'category': {
                    'name': question.category.name,
                    'name_ko': question.category.name_ko,
                    'weight': float(question.category.weight),
                    'order': question.category.order,
                    'description': question.category.description,
                    'description_ko': question.category.description_ko,
                    'is_active': question.category.is_active
                },
                'question_text': question.question_text,
                'question_text_ko': question.question_text_ko,
                'question_type': question.question_type,
                'is_required': question.is_required,
                'points': question.points,
                'help_text': question.help_text,
                'help_text_ko': question.help_text_ko,
                'order': question.order,
                'is_active': question.is_active,
                'choices': []
            }
            
            # Add choices
            for choice in question.choices.all():
                choice_data = {
                    'choice_text': choice.choice_text,
                    'choice_text_ko': choice.choice_text_ko,
                    'points': choice.points,
                    'risk_factor': choice.risk_factor,
                    'order': choice.order,
                    'is_correct': choice.is_correct
                }
                question_data['choices'].append(choice_data)
            
            # Add response statistics if requested
            if include_responses:
                stats = self.get_response_statistics(question)
                if stats:
                    question_data['response_stats'] = stats
            
            data.append(question_data)
            categories_seen.add(question.category.name)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                json.dump(data, f, ensure_ascii=False)
        
        self.stdout.write(f"Exported {len(questions)} questions from {len(categories_seen)} categories")
    
    def export_csv(self, questions, output_file):
        """Export questions to CSV format."""
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            # Define headers
            headers = [
                'category_name', 'category_name_ko', 'category_weight', 'category_order',
                'question_id', 'question_text', 'question_text_ko', 'question_type',
                'is_required', 'points', 'help_text', 'help_text_ko',
                'order', 'is_active'
            ]
            
            # Add choice headers (support up to 10 choices)
            for i in range(1, 11):
                headers.extend([
                    f'choice_{i}_text', f'choice_{i}_text_ko', 
                    f'choice_{i}_points', f'choice_{i}_risk_factor',
                    f'choice_{i}_is_correct'
                ])
            
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for question in questions:
                row = {
                    'category_name': question.category.name,
                    'category_name_ko': question.category.name_ko,
                    'category_weight': float(question.category.weight),
                    'category_order': question.category.order,
                    'question_id': question.id,
                    'question_text': question.question_text,
                    'question_text_ko': question.question_text_ko,
                    'question_type': question.question_type,
                    'is_required': question.is_required,
                    'points': question.points,
                    'help_text': question.help_text,
                    'help_text_ko': question.help_text_ko,
                    'order': question.order,
                    'is_active': question.is_active
                }
                
                # Add choices
                choices = list(question.choices.all())
                for i in range(10):
                    if i < len(choices):
                        choice = choices[i]
                        row[f'choice_{i+1}_text'] = choice.choice_text
                        row[f'choice_{i+1}_text_ko'] = choice.choice_text_ko
                        row[f'choice_{i+1}_points'] = choice.points
                        row[f'choice_{i+1}_risk_factor'] = choice.risk_factor
                        row[f'choice_{i+1}_is_correct'] = choice.is_correct
                    else:
                        # Empty choice slots
                        row[f'choice_{i+1}_text'] = ''
                        row[f'choice_{i+1}_text_ko'] = ''
                        row[f'choice_{i+1}_points'] = ''
                        row[f'choice_{i+1}_risk_factor'] = ''
                        row[f'choice_{i+1}_is_correct'] = ''
                
                writer.writerow(row)
        
        self.stdout.write(f"Exported {len(questions)} questions to CSV")
    
    def export_yaml(self, questions, output_file, include_responses):
        """Export questions to YAML format."""
        data = []
        
        for question in questions:
            question_data = {
                'category': {
                    'name': question.category.name,
                    'name_ko': question.category.name_ko,
                    'weight': float(question.category.weight),
                    'order': question.category.order
                },
                'question': {
                    'text': question.question_text,
                    'text_ko': question.question_text_ko,
                    'type': question.question_type,
                    'required': question.is_required,
                    'points': question.points,
                    'help_text': question.help_text,
                    'help_text_ko': question.help_text_ko,
                    'order': question.order,
                    'active': question.is_active
                },
                'choices': []
            }
            
            # Add choices
            for choice in question.choices.all():
                choice_data = {
                    'text': choice.choice_text,
                    'text_ko': choice.choice_text_ko,
                    'points': choice.points,
                    'risk_factor': choice.risk_factor or None,
                    'correct': choice.is_correct
                }
                question_data['choices'].append(choice_data)
            
            # Add response statistics if requested
            if include_responses:
                stats = self.get_response_statistics(question)
                if stats:
                    question_data['statistics'] = stats
            
            data.append(question_data)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        self.stdout.write(f"Exported {len(questions)} questions to YAML")
    
    def get_response_statistics(self, question):
        """Get response statistics for a question."""
        from django.db.models import Count
        
        try:
            total_responses = question.responses.count()
            
            if total_responses == 0:
                return None
            
            stats = {
                'total_responses': total_responses,
                'response_rate': f"{(total_responses / question.assessments.count() * 100):.1f}%" if question.assessments.exists() else "0%"
            }
            
            if question.question_type in ['single', 'multiple']:
                # Get choice distribution
                choice_counts = {}
                for choice in question.choices.all():
                    count = question.responses.filter(selected_choices=choice).count()
                    choice_counts[choice.choice_text] = {
                        'count': count,
                        'percentage': f"{(count / total_responses * 100):.1f}%"
                    }
                stats['choice_distribution'] = choice_counts
            
            return stats
            
        except Exception:
            return None
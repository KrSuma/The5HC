"""
Generate MCQ response statistics and insights.

This command analyzes MCQ responses to provide insights about question
effectiveness, response patterns, and assessment quality.

Usage:
    python manage.py mcq_statistics
    python manage.py mcq_statistics --category "Knowledge Assessment"
    python manage.py mcq_statistics --trainer 5
    python manage.py mcq_statistics --start-date 2025-01-01 --end-date 2025-12-31
    python manage.py mcq_statistics --export stats.csv
"""

import csv
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db.models import Count, Avg, Q, F, Sum, StdDev
from django.utils import timezone
from apps.assessments.models import (
    QuestionCategory, MultipleChoiceQuestion, 
    QuestionChoice, QuestionResponse, Assessment
)
from apps.trainers.models import Trainer


class Command(BaseCommand):
    help = 'Generate MCQ response statistics and insights'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            type=str,
            help='Filter by question category'
        )
        parser.add_argument(
            '--trainer',
            type=int,
            help='Filter by trainer ID'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--export',
            type=str,
            help='Export statistics to CSV file'
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed question-level statistics'
        )
    
    def handle(self, *args, **options):
        category_filter = options['category']
        trainer_id = options['trainer']
        start_date = options['start_date']
        end_date = options['end_date']
        export_file = options['export']
        detailed = options['detailed']
        
        # Parse dates
        if start_date:
            start_date = timezone.make_aware(
                datetime.strptime(start_date, '%Y-%m-%d')
            )
        else:
            start_date = timezone.now() - timedelta(days=365)
        
        if end_date:
            end_date = timezone.make_aware(
                datetime.strptime(end_date, '%Y-%m-%d').replace(
                    hour=23, minute=59, second=59
                )
            )
        else:
            end_date = timezone.now()
        
        self.stdout.write(f"Generating MCQ statistics from {start_date.date()} to {end_date.date()}")
        
        # Collect statistics
        stats = {
            'overview': self.get_overview_stats(start_date, end_date, trainer_id),
            'categories': self.get_category_stats(category_filter, start_date, end_date, trainer_id),
            'questions': self.get_question_stats(category_filter, start_date, end_date, trainer_id, detailed),
            'response_patterns': self.get_response_patterns(start_date, end_date, trainer_id),
            'quality_metrics': self.get_quality_metrics(start_date, end_date, trainer_id)
        }
        
        # Display or export statistics
        if export_file:
            self.export_statistics(stats, export_file)
        else:
            self.display_statistics(stats, detailed)
    
    def get_overview_stats(self, start_date, end_date, trainer_id):
        """Get general overview statistics."""
        # Filter assessments
        assessment_filter = Q(date__gte=start_date, date__lte=end_date)
        if trainer_id:
            assessment_filter &= Q(trainer_id=trainer_id)
        
        assessments = Assessment.objects.filter(assessment_filter)
        total_assessments = assessments.count()
        
        # MCQ completion stats
        assessments_with_mcq = assessments.filter(
            question_responses__isnull=False
        ).distinct().count()
        
        # Response stats
        response_filter = Q(assessment__date__gte=start_date, assessment__date__lte=end_date)
        if trainer_id:
            response_filter &= Q(assessment__trainer_id=trainer_id)
        
        total_responses = QuestionResponse.objects.filter(response_filter).count()
        
        # Score statistics
        mcq_scores = assessments.exclude(
            knowledge_score__isnull=True
        ).aggregate(
            avg_knowledge=Avg('knowledge_score'),
            avg_lifestyle=Avg('lifestyle_score'),
            avg_readiness=Avg('readiness_score'),
            avg_comprehensive=Avg('comprehensive_score')
        )
        
        return {
            'total_assessments': total_assessments,
            'assessments_with_mcq': assessments_with_mcq,
            'mcq_completion_rate': (assessments_with_mcq / total_assessments * 100) if total_assessments > 0 else 0,
            'total_responses': total_responses,
            'avg_responses_per_assessment': total_responses / assessments_with_mcq if assessments_with_mcq > 0 else 0,
            'score_averages': mcq_scores
        }
    
    def get_category_stats(self, category_filter, start_date, end_date, trainer_id):
        """Get statistics by category."""
        categories = QuestionCategory.objects.filter(is_active=True)
        if category_filter:
            categories = categories.filter(name=category_filter)
        
        category_stats = []
        
        for category in categories:
            # Get questions in category
            questions = category.multiplechoicequestion_set.filter(is_active=True)
            
            # Build response filter
            response_filter = Q(
                question__category=category,
                assessment__date__gte=start_date,
                assessment__date__lte=end_date
            )
            if trainer_id:
                response_filter &= Q(assessment__trainer_id=trainer_id)
            
            # Calculate stats
            responses = QuestionResponse.objects.filter(response_filter)
            response_count = responses.count()
            avg_points = responses.aggregate(avg=Avg('points_earned'))['avg'] or 0
            
            # Calculate response rate
            possible_responses = questions.count() * Assessment.objects.filter(
                date__gte=start_date, date__lte=end_date
            ).count()
            response_rate = (response_count / possible_responses * 100) if possible_responses > 0 else 0
            
            category_stats.append({
                'name': category.name_ko,
                'weight': float(category.weight),
                'active_questions': questions.count(),
                'total_responses': response_count,
                'response_rate': response_rate,
                'avg_points_earned': avg_points,
                'avg_score': (avg_points / questions.aggregate(avg=Avg('points'))['avg'] * 100) if questions.exists() else 0
            })
        
        return category_stats
    
    def get_question_stats(self, category_filter, start_date, end_date, trainer_id, detailed):
        """Get question-level statistics."""
        questions = MultipleChoiceQuestion.objects.filter(is_active=True)
        if category_filter:
            questions = questions.filter(category__name=category_filter)
        
        question_stats = []
        
        for question in questions.select_related('category'):
            # Build response filter
            response_filter = Q(
                question=question,
                assessment__date__gte=start_date,
                assessment__date__lte=end_date
            )
            if trainer_id:
                response_filter &= Q(assessment__trainer_id=trainer_id)
            
            responses = QuestionResponse.objects.filter(response_filter)
            response_count = responses.count()
            
            if response_count == 0:
                continue
            
            stats = {
                'id': question.id,
                'category': question.category.name_ko,
                'question': question.question_text_ko[:50] + '...',
                'type': question.get_question_type_display(),
                'response_count': response_count,
                'avg_points': responses.aggregate(avg=Avg('points_earned'))['avg'] or 0,
                'max_points': question.points
            }
            
            # Additional stats for choice questions
            if question.question_type in ['single', 'multiple']:
                # Choice distribution
                choice_stats = []
                for choice in question.choices.all():
                    selected_count = responses.filter(selected_choices=choice).count()
                    choice_stats.append({
                        'text': choice.choice_text_ko,
                        'count': selected_count,
                        'percentage': (selected_count / response_count * 100) if response_count > 0 else 0,
                        'points': choice.points
                    })
                
                stats['choices'] = sorted(choice_stats, key=lambda x: x['count'], reverse=True)
                
                # Calculate discrimination index (how well question differentiates high/low performers)
                if response_count >= 10:
                    # Get top and bottom 27% of assessments by comprehensive score
                    top_27_percent = int(response_count * 0.27)
                    
                    top_assessments = Assessment.objects.filter(
                        question_responses__question=question
                    ).order_by('-comprehensive_score')[:top_27_percent]
                    
                    bottom_assessments = Assessment.objects.filter(
                        question_responses__question=question
                    ).order_by('comprehensive_score')[:top_27_percent]
                    
                    top_correct = responses.filter(
                        assessment__in=top_assessments,
                        points_earned__gt=0
                    ).count()
                    
                    bottom_correct = responses.filter(
                        assessment__in=bottom_assessments,
                        points_earned__gt=0
                    ).count()
                    
                    discrimination_index = (top_correct - bottom_correct) / top_27_percent if top_27_percent > 0 else 0
                    stats['discrimination_index'] = discrimination_index
            
            question_stats.append(stats)
        
        return sorted(question_stats, key=lambda x: x['response_count'], reverse=True)
    
    def get_response_patterns(self, start_date, end_date, trainer_id):
        """Analyze response patterns and trends."""
        response_filter = Q(
            assessment__date__gte=start_date,
            assessment__date__lte=end_date
        )
        if trainer_id:
            response_filter &= Q(assessment__trainer_id=trainer_id)
        
        # Time to complete analysis (if timestamps available)
        assessments = Assessment.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            question_responses__isnull=False
        ).distinct()
        
        # Response completeness by question type
        completeness_by_type = {}
        for q_type in ['single', 'multiple', 'scale', 'text']:
            total_questions = MultipleChoiceQuestion.objects.filter(
                question_type=q_type,
                is_active=True
            ).count()
            
            if total_questions > 0:
                responses = QuestionResponse.objects.filter(
                    response_filter,
                    question__question_type=q_type
                ).values('assessment').annotate(
                    answered=Count('id')
                )
                
                avg_answered = responses.aggregate(avg=Avg('answered'))['avg'] or 0
                completeness_by_type[q_type] = {
                    'total_questions': total_questions,
                    'avg_answered': avg_answered,
                    'completion_rate': (avg_answered / total_questions * 100) if total_questions > 0 else 0
                }
        
        # Skip patterns (questions frequently left unanswered)
        all_questions = MultipleChoiceQuestion.objects.filter(is_active=True)
        skip_patterns = []
        
        for question in all_questions:
            possible_responses = assessments.count()
            actual_responses = QuestionResponse.objects.filter(
                response_filter,
                question=question
            ).count()
            
            skip_rate = ((possible_responses - actual_responses) / possible_responses * 100) if possible_responses > 0 else 0
            
            if skip_rate > 20:  # More than 20% skip rate
                skip_patterns.append({
                    'question': question.question_text_ko[:50] + '...',
                    'category': question.category.name_ko,
                    'skip_rate': skip_rate,
                    'is_required': question.is_required
                })
        
        return {
            'completeness_by_type': completeness_by_type,
            'high_skip_questions': sorted(skip_patterns, key=lambda x: x['skip_rate'], reverse=True)[:10]
        }
    
    def get_quality_metrics(self, start_date, end_date, trainer_id):
        """Calculate quality metrics for MCQ system."""
        response_filter = Q(
            assessment__date__gte=start_date,
            assessment__date__lte=end_date
        )
        if trainer_id:
            response_filter &= Q(assessment__trainer_id=trainer_id)
        
        # Internal consistency (category score correlations)
        assessments = Assessment.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            knowledge_score__isnull=False
        )
        
        if assessments.count() >= 10:
            # Calculate correlations between MCQ scores and physical scores
            score_data = assessments.values(
                'knowledge_score', 'lifestyle_score', 'readiness_score',
                'overall_score', 'comprehensive_score'
            )
            
            # Simple correlation indicator
            mcq_vs_physical = assessments.filter(
                comprehensive_score__gte=70,
                overall_score__gte=70
            ).count() / assessments.count() * 100 if assessments.count() > 0 else 0
        else:
            mcq_vs_physical = None
        
        # Question difficulty distribution
        difficulty_distribution = []
        for category in QuestionCategory.objects.filter(is_active=True):
            questions = category.multiplechoicequestion_set.filter(is_active=True)
            
            for question in questions:
                responses = QuestionResponse.objects.filter(
                    response_filter,
                    question=question
                )
                
                if responses.count() >= 5:
                    avg_score_rate = responses.aggregate(
                        avg=Avg(F('points_earned') * 100.0 / question.points)
                    )['avg'] or 0
                    
                    difficulty_distribution.append({
                        'question_id': question.id,
                        'difficulty': 100 - avg_score_rate  # Higher = more difficult
                    })
        
        # Categorize difficulty
        difficulty_categories = {
            'very_easy': 0,  # 0-20% difficulty
            'easy': 0,       # 20-40%
            'medium': 0,     # 40-60%
            'hard': 0,       # 60-80%
            'very_hard': 0   # 80-100%
        }
        
        for item in difficulty_distribution:
            diff = item['difficulty']
            if diff < 20:
                difficulty_categories['very_easy'] += 1
            elif diff < 40:
                difficulty_categories['easy'] += 1
            elif diff < 60:
                difficulty_categories['medium'] += 1
            elif diff < 80:
                difficulty_categories['hard'] += 1
            else:
                difficulty_categories['very_hard'] += 1
        
        return {
            'mcq_physical_alignment': mcq_vs_physical,
            'difficulty_distribution': difficulty_categories,
            'total_analyzed_questions': len(difficulty_distribution)
        }
    
    def display_statistics(self, stats, detailed):
        """Display statistics in console."""
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("MCQ STATISTICS REPORT"))
        self.stdout.write("="*70)
        
        # Overview
        overview = stats['overview']
        self.stdout.write("\n📊 OVERVIEW")
        self.stdout.write(f"  Total Assessments: {overview['total_assessments']}")
        self.stdout.write(f"  Assessments with MCQ: {overview['assessments_with_mcq']} ({overview['mcq_completion_rate']:.1f}%)")
        self.stdout.write(f"  Total MCQ Responses: {overview['total_responses']}")
        self.stdout.write(f"  Avg Responses per Assessment: {overview['avg_responses_per_assessment']:.1f}")
        
        if overview['score_averages']['avg_knowledge'] is not None:
            self.stdout.write("\n  Average Scores:")
            self.stdout.write(f"    Knowledge: {overview['score_averages']['avg_knowledge']:.1f}")
            self.stdout.write(f"    Lifestyle: {overview['score_averages']['avg_lifestyle']:.1f}")
            self.stdout.write(f"    Readiness: {overview['score_averages']['avg_readiness']:.1f}")
            self.stdout.write(f"    Comprehensive: {overview['score_averages']['avg_comprehensive']:.1f}")
        
        # Category Statistics
        self.stdout.write("\n\n📂 CATEGORY STATISTICS")
        for cat_stat in stats['categories']:
            self.stdout.write(f"\n  {cat_stat['name']} (Weight: {cat_stat['weight']:.0%})")
            self.stdout.write(f"    Active Questions: {cat_stat['active_questions']}")
            self.stdout.write(f"    Total Responses: {cat_stat['total_responses']}")
            self.stdout.write(f"    Response Rate: {cat_stat['response_rate']:.1f}%")
            self.stdout.write(f"    Average Score: {cat_stat['avg_score']:.1f}%")
        
        # Response Patterns
        patterns = stats['response_patterns']
        self.stdout.write("\n\n📈 RESPONSE PATTERNS")
        
        self.stdout.write("\n  Completion by Question Type:")
        for q_type, data in patterns['completeness_by_type'].items():
            self.stdout.write(f"    {q_type}: {data['completion_rate']:.1f}% ({data['avg_answered']:.1f}/{data['total_questions']} questions)")
        
        if patterns['high_skip_questions']:
            self.stdout.write("\n  Questions with High Skip Rates:")
            for skip in patterns['high_skip_questions'][:5]:
                required = "Required" if skip['is_required'] else "Optional"
                self.stdout.write(f"    - {skip['question']} ({skip['category']}) - {skip['skip_rate']:.1f}% skip rate [{required}]")
        
        # Quality Metrics
        quality = stats['quality_metrics']
        self.stdout.write("\n\n🎯 QUALITY METRICS")
        
        if quality['mcq_physical_alignment'] is not None:
            self.stdout.write(f"  MCQ-Physical Score Alignment: {quality['mcq_physical_alignment']:.1f}%")
        
        self.stdout.write(f"\n  Question Difficulty Distribution ({quality['total_analyzed_questions']} questions):")
        total_q = quality['total_analyzed_questions'] or 1
        for level, count in quality['difficulty_distribution'].items():
            percentage = (count / total_q * 100) if total_q > 0 else 0
            self.stdout.write(f"    {level.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        # Top Questions (if detailed)
        if detailed and stats['questions']:
            self.stdout.write("\n\n🔝 TOP QUESTIONS BY RESPONSES")
            for q_stat in stats['questions'][:10]:
                self.stdout.write(f"\n  {q_stat['question']}")
                self.stdout.write(f"    Category: {q_stat['category']} | Type: {q_stat['type']}")
                self.stdout.write(f"    Responses: {q_stat['response_count']} | Avg Points: {q_stat['avg_points']:.1f}/{q_stat['max_points']}")
                
                if 'discrimination_index' in q_stat:
                    quality = "Excellent" if q_stat['discrimination_index'] > 0.4 else "Good" if q_stat['discrimination_index'] > 0.3 else "Fair" if q_stat['discrimination_index'] > 0.2 else "Poor"
                    self.stdout.write(f"    Discrimination Index: {q_stat['discrimination_index']:.2f} ({quality})")
                
                if 'choices' in q_stat and q_stat['choices']:
                    self.stdout.write("    Top Choices:")
                    for choice in q_stat['choices'][:3]:
                        self.stdout.write(f"      - {choice['text']}: {choice['count']} ({choice['percentage']:.1f}%)")
        
        self.stdout.write("\n" + "="*70)
    
    def export_statistics(self, stats, filename):
        """Export statistics to CSV file."""
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            
            # Write overview
            writer.writerow(['MCQ STATISTICS REPORT'])
            writer.writerow([])
            writer.writerow(['OVERVIEW'])
            overview = stats['overview']
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Assessments', overview['total_assessments']])
            writer.writerow(['Assessments with MCQ', overview['assessments_with_mcq']])
            writer.writerow(['MCQ Completion Rate', f"{overview['mcq_completion_rate']:.1f}%"])
            writer.writerow(['Total Responses', overview['total_responses']])
            writer.writerow(['Avg Responses per Assessment', f"{overview['avg_responses_per_assessment']:.1f}"])
            
            # Write category stats
            writer.writerow([])
            writer.writerow(['CATEGORY STATISTICS'])
            writer.writerow(['Category', 'Weight', 'Active Questions', 'Total Responses', 'Response Rate', 'Average Score'])
            
            for cat in stats['categories']:
                writer.writerow([
                    cat['name'],
                    f"{cat['weight']:.0%}",
                    cat['active_questions'],
                    cat['total_responses'],
                    f"{cat['response_rate']:.1f}%",
                    f"{cat['avg_score']:.1f}%"
                ])
            
            # Write question stats
            if stats['questions']:
                writer.writerow([])
                writer.writerow(['QUESTION STATISTICS'])
                writer.writerow(['Question', 'Category', 'Type', 'Responses', 'Avg Points', 'Max Points'])
                
                for q in stats['questions']:
                    writer.writerow([
                        q['question'],
                        q['category'],
                        q['type'],
                        q['response_count'],
                        f"{q['avg_points']:.1f}",
                        q['max_points']
                    ])
        
        self.stdout.write(self.style.SUCCESS(f"Statistics exported to {filename}"))
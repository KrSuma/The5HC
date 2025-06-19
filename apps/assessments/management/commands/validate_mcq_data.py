"""
Validate MCQ data integrity and fix common issues.

This command checks for data integrity issues in MCQ questions and
can optionally fix common problems.

Usage:
    python manage.py validate_mcq_data
    python manage.py validate_mcq_data --fix
    python manage.py validate_mcq_data --check-dependencies
    python manage.py validate_mcq_data --category "Knowledge Assessment"
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Q, F, Sum
from django.db import transaction
from apps.assessments.models import (
    QuestionCategory, MultipleChoiceQuestion, 
    QuestionChoice, QuestionResponse
)


class Command(BaseCommand):
    help = 'Validate MCQ data integrity and fix common issues'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix found issues automatically'
        )
        parser.add_argument(
            '--check-dependencies',
            action='store_true',
            help='Check for broken question dependencies'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Validate only questions in specific category'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information about each issue'
        )
    
    def handle(self, *args, **options):
        fix_issues = options['fix']
        check_deps = options['check_dependencies']
        category_filter = options['category']
        verbose = options['verbose']
        
        self.stdout.write("Starting MCQ data validation...")
        
        issues = {
            'categories': [],
            'questions': [],
            'choices': [],
            'dependencies': [],
            'responses': []
        }
        
        # Run validation checks
        with transaction.atomic():
            self.validate_categories(issues, fix_issues, verbose)
            self.validate_questions(issues, fix_issues, category_filter, verbose)
            self.validate_choices(issues, fix_issues, verbose)
            
            if check_deps:
                self.validate_dependencies(issues, fix_issues, verbose)
            
            self.validate_responses(issues, fix_issues, verbose)
            
            # Display summary
            self.display_summary(issues)
            
            # Rollback if not fixing
            if not fix_issues and any(issues.values()):
                transaction.set_rollback(True)
    
    def validate_categories(self, issues, fix, verbose):
        """Validate category data."""
        self.stdout.write("\nValidating categories...")
        
        # Check for duplicate category names
        duplicates = QuestionCategory.objects.values('name').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        for dup in duplicates:
            issue = f"Duplicate category name: {dup['name']} ({dup['count']} occurrences)"
            issues['categories'].append(issue)
            if verbose:
                self.stdout.write(self.style.WARNING(f"  - {issue}"))
        
        # Check for invalid weights
        invalid_weights = QuestionCategory.objects.filter(
            Q(weight__lt=0) | Q(weight__gt=1)
        )
        
        for cat in invalid_weights:
            issue = f"Invalid weight for category '{cat.name}': {cat.weight}"
            issues['categories'].append(issue)
            if verbose:
                self.stdout.write(self.style.WARNING(f"  - {issue}"))
            
            if fix:
                cat.weight = max(0, min(1, cat.weight))
                cat.save()
                self.stdout.write(self.style.SUCCESS(f"    Fixed: Set weight to {cat.weight}"))
        
        # Check total weights
        total_weight = QuestionCategory.objects.filter(
            is_active=True
        ).aggregate(total=Sum('weight'))['total'] or 0
        
        if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
            issue = f"Total category weights do not sum to 1.0: {total_weight}"
            issues['categories'].append(issue)
            if verbose:
                self.stdout.write(self.style.WARNING(f"  - {issue}"))
            
            if fix and total_weight > 0:
                # Normalize weights
                categories = QuestionCategory.objects.filter(is_active=True)
                for cat in categories:
                    cat.weight = cat.weight / total_weight
                    cat.save()
                self.stdout.write(self.style.SUCCESS("    Fixed: Normalized category weights"))
    
    def validate_questions(self, issues, fix, category_filter, verbose):
        """Validate question data."""
        self.stdout.write("\nValidating questions...")
        
        queryset = MultipleChoiceQuestion.objects.all()
        if category_filter:
            queryset = queryset.filter(category__name=category_filter)
        
        # Check for questions without choices
        no_choices = []
        for question in queryset.annotate(choice_count=Count('choices')):
            if question.choice_count == 0 and question.question_type in ['single', 'multiple']:
                no_choices.append(question)
                issue = f"Question '{question.question_text_ko[:50]}...' has no choices"
                issues['questions'].append(issue)
                if verbose:
                    self.stdout.write(self.style.WARNING(f"  - {issue}"))
        
        # Check for invalid question types
        valid_types = ['single', 'multiple', 'scale', 'text']
        invalid_types = queryset.exclude(question_type__in=valid_types)
        
        for question in invalid_types:
            issue = f"Invalid question type '{question.question_type}' for question ID {question.id}"
            issues['questions'].append(issue)
            if verbose:
                self.stdout.write(self.style.WARNING(f"  - {issue}"))
            
            if fix:
                question.question_type = 'single'
                question.save()
                self.stdout.write(self.style.SUCCESS("    Fixed: Changed to 'single' type"))
        
        # Check for questions with invalid points
        invalid_points = queryset.filter(points__lt=0)
        
        for question in invalid_points:
            issue = f"Negative points ({question.points}) for question ID {question.id}"
            issues['questions'].append(issue)
            if verbose:
                self.stdout.write(self.style.WARNING(f"  - {issue}"))
            
            if fix:
                question.points = abs(question.points)
                question.save()
                self.stdout.write(self.style.SUCCESS(f"    Fixed: Set points to {question.points}"))
        
        # Check for duplicate orders within categories
        for category in QuestionCategory.objects.all():
            duplicates = MultipleChoiceQuestion.objects.filter(
                category=category
            ).values('order').annotate(
                count=Count('id')
            ).filter(count__gt=1)
            
            if duplicates:
                issue = f"Duplicate question orders in category '{category.name}'"
                issues['questions'].append(issue)
                if verbose:
                    self.stdout.write(self.style.WARNING(f"  - {issue}"))
                
                if fix:
                    # Reorder questions
                    questions = MultipleChoiceQuestion.objects.filter(
                        category=category
                    ).order_by('order', 'id')
                    
                    for idx, question in enumerate(questions):
                        question.order = idx
                        question.save()
                    
                    self.stdout.write(self.style.SUCCESS(f"    Fixed: Reordered questions in '{category.name}'"))
    
    def validate_choices(self, issues, fix, verbose):
        """Validate choice data."""
        self.stdout.write("\nValidating choices...")
        
        # Check for single-choice questions with multiple correct answers
        problematic_questions = []
        
        single_questions = MultipleChoiceQuestion.objects.filter(
            question_type='single'
        ).annotate(
            correct_count=Count('choices', filter=Q(choices__is_correct=True))
        ).filter(correct_count__gt=1)
        
        for question in single_questions:
            issue = f"Single-choice question has {question.correct_count} correct answers: '{question.question_text_ko[:30]}...'"
            issues['choices'].append(issue)
            problematic_questions.append(question)
            if verbose:
                self.stdout.write(self.style.WARNING(f"  - {issue}"))
        
        if fix and problematic_questions:
            for question in problematic_questions:
                # Keep only the first correct choice
                correct_choices = question.choices.filter(is_correct=True).order_by('order')
                for idx, choice in enumerate(correct_choices):
                    if idx > 0:
                        choice.is_correct = False
                        choice.save()
                
                self.stdout.write(self.style.SUCCESS(f"    Fixed: Question ID {question.id} now has only one correct answer"))
        
        # Check for choices with invalid points
        invalid_choices = QuestionChoice.objects.filter(points__lt=0)
        
        for choice in invalid_choices:
            issue = f"Negative points ({choice.points}) for choice in question ID {choice.question_id}"
            issues['choices'].append(issue)
            if verbose:
                self.stdout.write(self.style.WARNING(f"  - {issue}"))
            
            if fix:
                choice.points = 0
                choice.save()
                self.stdout.write(self.style.SUCCESS("    Fixed: Set negative points to 0"))
        
        # Check for duplicate choice orders within questions
        questions_with_dup_orders = MultipleChoiceQuestion.objects.annotate(
            dup_count=Count('choices__order')
        ).filter(dup_count__gt=Count('choices', distinct=True))
        
        for question in questions_with_dup_orders:
            issue = f"Duplicate choice orders in question ID {question.id}"
            issues['choices'].append(issue)
            if verbose:
                self.stdout.write(self.style.WARNING(f"  - {issue}"))
            
            if fix:
                choices = question.choices.order_by('order', 'id')
                for idx, choice in enumerate(choices):
                    choice.order = idx
                    choice.save()
                self.stdout.write(self.style.SUCCESS(f"    Fixed: Reordered choices for question ID {question.id}"))
    
    def validate_dependencies(self, issues, fix, verbose):
        """Validate question dependencies."""
        self.stdout.write("\nValidating question dependencies...")
        
        # Check for circular dependencies
        questions_with_deps = MultipleChoiceQuestion.objects.filter(
            depends_on__isnull=False
        ).select_related('depends_on')
        
        for question in questions_with_deps:
            # Simple check for direct circular dependency
            if question.depends_on.depends_on == question:
                issue = f"Circular dependency: Question ID {question.id} and {question.depends_on.id}"
                issues['dependencies'].append(issue)
                if verbose:
                    self.stdout.write(self.style.WARNING(f"  - {issue}"))
                
                if fix:
                    question.depends_on = None
                    question.depends_on_answer = None
                    question.save()
                    self.stdout.write(self.style.SUCCESS(f"    Fixed: Removed circular dependency"))
        
        # Check for broken dependencies (depends_on_answer not in choices)
        for question in questions_with_deps.filter(depends_on_answer__isnull=False):
            valid_answers = list(question.depends_on.choices.values_list('choice_text', flat=True))
            
            if question.depends_on_answer not in valid_answers:
                issue = f"Invalid dependency answer '{question.depends_on_answer}' for question ID {question.id}"
                issues['dependencies'].append(issue)
                if verbose:
                    self.stdout.write(self.style.WARNING(f"  - {issue}"))
                    self.stdout.write(f"      Valid answers: {', '.join(valid_answers[:3])}...")
                
                if fix:
                    question.depends_on_answer = None
                    question.save()
                    self.stdout.write(self.style.SUCCESS("    Fixed: Cleared invalid dependency answer"))
        
        # Check for dependencies across categories (warning only)
        cross_category_deps = questions_with_deps.filter(
            ~Q(category=F('depends_on__category'))
        )
        
        for question in cross_category_deps:
            issue = f"Cross-category dependency: Question ID {question.id} ('{question.category.name}') depends on question in '{question.depends_on.category.name}'"
            issues['dependencies'].append(issue)
            if verbose:
                self.stdout.write(self.style.WARNING(f"  - {issue} (WARNING: This may affect question flow)"))
    
    def validate_responses(self, issues, fix, verbose):
        """Validate response data."""
        self.stdout.write("\nValidating responses...")
        
        # Check for orphaned responses (question deleted)
        orphaned = QuestionResponse.objects.filter(question__isnull=True).count()
        if orphaned > 0:
            issue = f"Found {orphaned} orphaned responses (question deleted)"
            issues['responses'].append(issue)
            if verbose:
                self.stdout.write(self.style.WARNING(f"  - {issue}"))
            
            if fix:
                QuestionResponse.objects.filter(question__isnull=True).delete()
                self.stdout.write(self.style.SUCCESS(f"    Fixed: Deleted {orphaned} orphaned responses"))
        
        # Check for responses with invalid selected choices
        responses_with_choices = QuestionResponse.objects.filter(
            question__question_type__in=['single', 'multiple']
        ).prefetch_related('selected_choices', 'question__choices')
        
        invalid_responses = 0
        for response in responses_with_choices:
            valid_choice_ids = set(response.question.choices.values_list('id', flat=True))
            selected_ids = set(response.selected_choices.values_list('id', flat=True))
            
            if selected_ids and not selected_ids.issubset(valid_choice_ids):
                invalid_responses += 1
                if verbose and invalid_responses <= 5:  # Limit output
                    self.stdout.write(self.style.WARNING(
                        f"  - Response ID {response.id} has invalid choice selections"
                    ))
        
        if invalid_responses > 0:
            issue = f"Found {invalid_responses} responses with invalid choice selections"
            issues['responses'].append(issue)
            
            if fix:
                # This is complex to fix automatically, just report
                self.stdout.write(self.style.WARNING(
                    "    Cannot automatically fix invalid choice selections. Manual review required."
                ))
    
    def display_summary(self, issues):
        """Display validation summary."""
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("VALIDATION SUMMARY"))
        self.stdout.write("="*60)
        
        total_issues = sum(len(v) for v in issues.values())
        
        if total_issues == 0:
            self.stdout.write(self.style.SUCCESS("✓ No issues found! MCQ data is valid."))
        else:
            self.stdout.write(self.style.ERROR(f"✗ Found {total_issues} issues:"))
            
            for category, category_issues in issues.items():
                if category_issues:
                    self.stdout.write(f"\n{category.upper()}: {len(category_issues)} issues")
                    for issue in category_issues[:3]:  # Show first 3
                        self.stdout.write(f"  - {issue}")
                    if len(category_issues) > 3:
                        self.stdout.write(f"  ... and {len(category_issues) - 3} more")
        
        self.stdout.write("="*60)
        
        # Statistics
        self.stdout.write("\nDATABASE STATISTICS:")
        self.stdout.write(f"  Categories: {QuestionCategory.objects.count()}")
        self.stdout.write(f"  Questions: {MultipleChoiceQuestion.objects.count()}")
        self.stdout.write(f"  Choices: {QuestionChoice.objects.count()}")
        self.stdout.write(f"  Responses: {QuestionResponse.objects.count()}")
        
        active_stats = {
            'categories': QuestionCategory.objects.filter(is_active=True).count(),
            'questions': MultipleChoiceQuestion.objects.filter(is_active=True).count()
        }
        self.stdout.write(f"\n  Active Categories: {active_stats['categories']}")
        self.stdout.write(f"  Active Questions: {active_stats['questions']}")